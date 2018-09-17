import errno
import os
import time
import mock
import pytest

boto3 = pytest.importorskip("boto3")
botocore = pytest.importorskip("botocore")
placebo = pytest.importorskip("placebo")

"""
Using Placebo to test modules using boto3:

This is an example test, using the placeboify fixture to test that a module
will fail if resources it depends on don't exist.

> from placebo_fixtures import placeboify, scratch_vpc
>
> def test_create_with_nonexistent_launch_config(placeboify):
>     connection = placeboify.client('autoscaling')
>     module = FakeModule('test-asg-created', None, min_size=0, max_size=0, desired_capacity=0)
>     with pytest.raises(FailJSON) as excinfo:
>         asg_module.create_autoscaling_group(connection, module)
>     .... asserts based on module state/exceptions ....

In more advanced cases, use unrecorded resource fixtures to fill in ARNs/IDs of
things modules depend on, such as:

> def test_create_in_vpc(placeboify, scratch_vpc):
>     connection = placeboify.client('autoscaling')
>     module = FakeModule(name='test-asg-created',
>         min_size=0, max_size=0, desired_capacity=0,
>         availability_zones=[s['az'] for s in scratch_vpc['subnets']],
>         vpc_zone_identifier=[s['id'] for s in scratch_vpc['subnets']],
>     )
>     ..... so on and so forth ....
"""


@pytest.fixture
def placeboify(request, monkeypatch):
    """This fixture puts a recording/replaying harness around `boto3_conn`

    Placeboify patches the `boto3_conn` function in ec2 module_utils to return
    a boto3 session that in recording or replaying mode, depending on the
    PLACEBO_RECORD environment variable. Unset PLACEBO_RECORD (the common case
    for just running tests) will put placebo in replay mode, set PLACEBO_RECORD
    to any value to turn off replay & operate on real AWS resources.

    The recorded sessions are stored in the test file's directory, under the
    namespace `placebo_recordings/{testfile name}/{test function name}` to
    distinguish them.
    """
    session = boto3.Session(region_name='us-west-2')

    recordings_path = os.path.join(
        request.fspath.dirname,
        'placebo_recordings',
        request.fspath.basename.replace('.py', ''),
        request.function.__name__
        # remove the test_ prefix from the function & file name
    ).replace('test_', '')

    if not os.getenv('PLACEBO_RECORD'):
        if not os.path.isdir(recordings_path):
            raise NotImplementedError('Missing Placebo recordings in directory: %s' % recordings_path)
    else:
        try:
            # make sure the directory for placebo test recordings is available
            os.makedirs(recordings_path)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    pill = placebo.attach(session, data_path=recordings_path)
    if os.getenv('PLACEBO_RECORD'):
        pill.record()
    else:
        pill.playback()

    def boto3_middleman_connection(module, conn_type, resource, region='us-west-2', **kwargs):
        if conn_type != 'client':
            # TODO support resource-based connections
            raise ValueError('Mocker only supports client, not %s' % conn_type)
        return session.client(resource, region_name=region)

    import ansible.module_utils.ec2
    monkeypatch.setattr(
        ansible.module_utils.ec2,
        'boto3_conn',
        boto3_middleman_connection,
    )
    yield session

    # tear down
    pill.stop()


@pytest.fixture(scope='module')
def basic_launch_config():
    """Create an EC2 launch config whose creation *is not* recorded and return its name

    This fixture is module-scoped, since launch configs are immutable and this
    can be reused for many tests.
    """
    if not os.getenv('PLACEBO_RECORD'):
        yield 'pytest_basic_lc'
        return

    # use a *non recording* session to make the launch config
    # since that's a prereq of the ec2_asg module, and isn't what
    # we're testing.
    asg = boto3.client('autoscaling')
    asg.create_launch_configuration(
        LaunchConfigurationName='pytest_basic_lc',
        ImageId='ami-9be6f38c',  # Amazon Linux 2016.09 us-east-1 AMI, can be any valid AMI
        SecurityGroups=[],
        UserData='#!/bin/bash\necho hello world',
        InstanceType='t2.micro',
        InstanceMonitoring={'Enabled': False},
        AssociatePublicIpAddress=True
    )

    yield 'pytest_basic_lc'

    try:
        asg.delete_launch_configuration(LaunchConfigurationName='pytest_basic_lc')
    except botocore.exceptions.ClientError as e:
        if 'not found' in e.message:
            return
        raise


@pytest.fixture(scope='module')
def scratch_vpc():
    if not os.getenv('PLACEBO_RECORD'):
        yield {
            'vpc_id': 'vpc-123456',
            'cidr_range': '10.0.0.0/16',
            'subnets': [
                {
                    'id': 'subnet-123456',
                    'az': 'us-east-1d',
                },
                {
                    'id': 'subnet-654321',
                    'az': 'us-east-1e',
                },
            ]
        }
        return

    # use a *non recording* session to make the base VPC and subnets
    ec2 = boto3.client('ec2')
    vpc_resp = ec2.create_vpc(
        CidrBlock='10.0.0.0/16',
        AmazonProvidedIpv6CidrBlock=False,
    )
    subnets = (
        ec2.create_subnet(
            VpcId=vpc_resp['Vpc']['VpcId'],
            CidrBlock='10.0.0.0/24',
        ),
        ec2.create_subnet(
            VpcId=vpc_resp['Vpc']['VpcId'],
            CidrBlock='10.0.1.0/24',
        )
    )
    time.sleep(3)

    yield {
        'vpc_id': vpc_resp['Vpc']['VpcId'],
        'cidr_range': '10.0.0.0/16',
        'subnets': [
            {
                'id': s['Subnet']['SubnetId'],
                'az': s['Subnet']['AvailabilityZone'],
            } for s in subnets
        ]
    }

    try:
        for s in subnets:
            try:
                ec2.delete_subnet(SubnetId=s['Subnet']['SubnetId'])
            except botocore.exceptions.ClientError as e:
                if 'not found' in e.message:
                    continue
                raise
        ec2.delete_vpc(VpcId=vpc_resp['Vpc']['VpcId'])
    except botocore.exceptions.ClientError as e:
        if 'not found' in e.message:
            return
        raise


@pytest.fixture(scope='module')
def maybe_sleep():
    """If placebo is reading saved sessions, make sleep always take 0 seconds.

    AWS modules often perform polling or retries, but when using recorded
    sessions there's no reason to wait. We can still exercise retry and other
    code paths without waiting for wall-clock time to pass."""
    if not os.getenv('PLACEBO_RECORD'):
        p = mock.patch('time.sleep', return_value=None)
        p.start()
        yield
        p.stop()
    else:
        yield
