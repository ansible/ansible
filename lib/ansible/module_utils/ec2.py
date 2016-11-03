# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c), Michael DeHaan <michael.dehaan@gmail.com>, 2012-2013
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os
import re
from time import sleep

from ansible.module_utils.cloud import CloudRetry

try:
    import boto
    import boto.ec2 #boto does weird import stuff
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

try:
    import boto3
    import botocore
    HAS_BOTO3 = True
except:
    HAS_BOTO3 = False

try:
    from distutils.version import LooseVersion
    HAS_LOOSE_VERSION = True
except:
    HAS_LOOSE_VERSION = False

from ansible.module_utils.six import string_types

class AnsibleAWSError(Exception):
    pass


def _botocore_exception_maybe():
    """
    Allow for boto3 not being installed when using these utils by wrapping
    botocore.exceptions instead of assigning from it directly.
    """
    if HAS_BOTO3:
        return botocore.exceptions.ClientError
    return type(None)


class AWSRetry(CloudRetry):
    base_class = _botocore_exception_maybe()

    @staticmethod
    def status_code_from_exception(error):
        return error.response['Error']['Code']

    @staticmethod
    def found(response_code):
        # This list of failures is based on this API Reference
        # http://docs.aws.amazon.com/AWSEC2/latest/APIReference/errors-overview.html
        retry_on = [
            'RequestLimitExceeded', 'Unavailable', 'ServiceUnavailable',
            'InternalFailure', 'InternalError'
        ]

        not_found = re.compile(r'^\w+.NotFound')
        if response_code in retry_on or not_found.search(response_code):
            return True
        else:
            return False


def boto3_conn(module, conn_type=None, resource=None, region=None, endpoint=None, **params):
    try:
        return _boto3_conn(conn_type=conn_type, resource=resource, region=region, endpoint=endpoint, **params)
    except ValueError:
        module.fail_json(msg='There is an issue in the code of the module. You must specify either both, resource or client to the conn_type parameter in the boto3_conn function call')

def _boto3_conn(conn_type=None, resource=None, region=None, endpoint=None, **params):
    profile = params.pop('profile_name', None)

    if conn_type not in ['both', 'resource', 'client']:
        raise ValueError('There is an issue in the calling code. You '
                         'must specify either both, resource, or client to '
                         'the conn_type parameter in the boto3_conn function '
                         'call')

    if conn_type == 'resource':
        resource = boto3.session.Session(profile_name=profile).resource(resource, region_name=region, endpoint_url=endpoint, **params)
        return resource
    elif conn_type == 'client':
        client = boto3.session.Session(profile_name=profile).client(resource, region_name=region, endpoint_url=endpoint, **params)
        return client
    else:
        resource = boto3.session.Session(profile_name=profile).resource(resource, region_name=region, endpoint_url=endpoint, **params)
        client = boto3.session.Session(profile_name=profile).client(resource, region_name=region, endpoint_url=endpoint, **params)
        return client, resource

boto3_inventory_conn = _boto3_conn

def aws_common_argument_spec():
    return dict(
        ec2_url=dict(),
        aws_secret_key=dict(aliases=['ec2_secret_key', 'secret_key'], no_log=True),
        aws_access_key=dict(aliases=['ec2_access_key', 'access_key']),
        validate_certs=dict(default=True, type='bool'),
        security_token=dict(aliases=['access_token'], no_log=True),
        profile=dict(),
    )


def ec2_argument_spec():
    spec = aws_common_argument_spec()
    spec.update(
        dict(
            region=dict(aliases=['aws_region', 'ec2_region']),
        )
    )
    return spec


def get_aws_connection_info(module, boto3=False):

    # Check module args for credentials, then check environment vars
    # access_key

    ec2_url = module.params.get('ec2_url')
    access_key = module.params.get('aws_access_key')
    secret_key = module.params.get('aws_secret_key')
    security_token = module.params.get('security_token')
    region = module.params.get('region')
    profile_name = module.params.get('profile')
    validate_certs = module.params.get('validate_certs')

    if not ec2_url:
        if 'AWS_URL' in os.environ:
            ec2_url = os.environ['AWS_URL']
        elif 'EC2_URL' in os.environ:
            ec2_url = os.environ['EC2_URL']

    if not access_key:
        if 'AWS_ACCESS_KEY_ID' in os.environ:
            access_key = os.environ['AWS_ACCESS_KEY_ID']
        elif 'AWS_ACCESS_KEY' in os.environ:
            access_key = os.environ['AWS_ACCESS_KEY']
        elif 'EC2_ACCESS_KEY' in os.environ:
            access_key = os.environ['EC2_ACCESS_KEY']
        else:
            # in case access_key came in as empty string
            access_key = None

    if not secret_key:
        if 'AWS_SECRET_ACCESS_KEY' in os.environ:
            secret_key = os.environ['AWS_SECRET_ACCESS_KEY']
        elif 'AWS_SECRET_KEY' in os.environ:
            secret_key = os.environ['AWS_SECRET_KEY']
        elif 'EC2_SECRET_KEY' in os.environ:
            secret_key = os.environ['EC2_SECRET_KEY']
        else:
            # in case secret_key came in as empty string
            secret_key = None

    if not region:
        if 'AWS_REGION' in os.environ:
            region = os.environ['AWS_REGION']
        elif 'AWS_DEFAULT_REGION' in os.environ:
            region = os.environ['AWS_DEFAULT_REGION']
        elif 'EC2_REGION' in os.environ:
            region = os.environ['EC2_REGION']
        else:
            if not boto3:
                # boto.config.get returns None if config not found
                region = boto.config.get('Boto', 'aws_region')
                if not region:
                    region = boto.config.get('Boto', 'ec2_region')
            elif HAS_BOTO3:
                # here we don't need to make an additional call, will default to 'us-east-1' if the below evaluates to None.
                region = botocore.session.get_session().get_config_variable('region')
            else:
                module.fail_json(msg="Boto3 is required for this module. Please install boto3 and try again")

    if not security_token:
        if 'AWS_SECURITY_TOKEN' in os.environ:
            security_token = os.environ['AWS_SECURITY_TOKEN']
        elif 'AWS_SESSION_TOKEN' in os.environ:
            security_token = os.environ['AWS_SESSION_TOKEN']
        elif 'EC2_SECURITY_TOKEN' in os.environ:
            security_token = os.environ['EC2_SECURITY_TOKEN']
        else:
            # in case security_token came in as empty string
            security_token = None

    if HAS_BOTO3 and boto3:
        boto_params = dict(aws_access_key_id=access_key,
                           aws_secret_access_key=secret_key,
                           aws_session_token=security_token)
        boto_params['verify'] = validate_certs

        if profile_name:
            boto_params['profile_name'] = profile_name

    else:
        boto_params = dict(aws_access_key_id=access_key,
                           aws_secret_access_key=secret_key,
                           security_token=security_token)

        # only set profile_name if passed as an argument
        if profile_name:
            boto_params['profile_name'] = profile_name

        boto_params['validate_certs'] = validate_certs

    for param, value in boto_params.items():
        if isinstance(value, str):
            boto_params[param] = unicode(value, 'utf-8', 'strict')

    return region, ec2_url, boto_params


def get_ec2_creds(module):
    ''' for compatibility mode with old modules that don't/can't yet
        use ec2_connect method '''
    region, ec2_url, boto_params = get_aws_connection_info(module)
    return ec2_url, boto_params['aws_access_key_id'], boto_params['aws_secret_access_key'], region


def boto_fix_security_token_in_profile(conn, profile_name):
    ''' monkey patch for boto issue boto/boto#2100 '''
    profile = 'profile ' + profile_name
    if boto.config.has_option(profile, 'aws_security_token'):
        conn.provider.set_security_token(boto.config.get(profile, 'aws_security_token'))
    return conn


def connect_to_aws(aws_module, region, **params):
    conn = aws_module.connect_to_region(region, **params)
    if not conn:
        if region not in [aws_module_region.name for aws_module_region in aws_module.regions()]:
            raise AnsibleAWSError("Region %s does not seem to be available for aws module %s. If the region definitely exists, you may need to upgrade boto or extend with endpoints_path" % (region, aws_module.__name__))
        else:
            raise AnsibleAWSError("Unknown problem connecting to region %s for aws module %s." % (region, aws_module.__name__))
    if params.get('profile_name'):
        conn = boto_fix_security_token_in_profile(conn, params['profile_name'])
    return conn


def ec2_connect(module):

    """ Return an ec2 connection"""

    region, ec2_url, boto_params = get_aws_connection_info(module)

    # If we have a region specified, connect to its endpoint.
    if region:
        try:
            ec2 = connect_to_aws(boto.ec2, region, **boto_params)
        except (boto.exception.NoAuthHandlerFound, AnsibleAWSError) as e:
            module.fail_json(msg=str(e))
    # Otherwise, no region so we fallback to the old connection method
    elif ec2_url:
        try:
            ec2 = boto.connect_ec2_endpoint(ec2_url, **boto_params)
        except (boto.exception.NoAuthHandlerFound, AnsibleAWSError) as e:
            module.fail_json(msg=str(e))
    else:
        module.fail_json(msg="Either region or ec2_url must be specified")

    return ec2

def paging(pause=0, marker_property='marker'):
    """ Adds paging to boto retrieval functions that support a 'marker'
        this is configurable as not all boto functions seem to use the
        same name.
    """
    def wrapper(f):
        def page(*args, **kwargs):
            results = []
            marker = None
            while True:
                try:
                    new = f(*args, marker=marker, **kwargs)
                    marker = getattr(new, marker_property)
                    results.extend(new)
                    if not marker:
                        break
                    elif pause:
                        sleep(pause)
                except TypeError:
                    # Older version of boto do not allow for marker param, just run normally
                    results = f(*args, **kwargs)
                    break
            return results
        return page
    return wrapper


def camel_dict_to_snake_dict(camel_dict):

    def camel_to_snake(name):

        import re

        first_cap_re = re.compile('(.)([A-Z][a-z]+)')
        all_cap_re = re.compile('([a-z0-9])([A-Z])')
        s1 = first_cap_re.sub(r'\1_\2', name)

        return all_cap_re.sub(r'\1_\2', s1).lower()


    def value_is_list(camel_list):

        checked_list = []
        for item in camel_list:
            if isinstance(item, dict):
                checked_list.append(camel_dict_to_snake_dict(item))
            elif isinstance(item, list):
                checked_list.append(value_is_list(item))
            else:
                checked_list.append(item)

        return checked_list


    snake_dict = {}
    for k, v in camel_dict.iteritems():
        if isinstance(v, dict):
            snake_dict[camel_to_snake(k)] = camel_dict_to_snake_dict(v)
        elif isinstance(v, list):
            snake_dict[camel_to_snake(k)] = value_is_list(v)
        else:
            snake_dict[camel_to_snake(k)] = v

    return snake_dict


def ansible_dict_to_boto3_filter_list(filters_dict):

    """ Convert an Ansible dict of filters to list of dicts that boto3 can use
    Args:
        filters_dict (dict): Dict of AWS filters.
    Basic Usage:
        >>> filters = {'some-aws-id', 'i-01234567'}
        >>> ansible_dict_to_boto3_filter_list(filters)
        {
            'some-aws-id': 'i-01234567'
        }
    Returns:
        List: List of AWS filters and their values
        [
            {
                'Name': 'some-aws-id',
                'Values': [
                    'i-01234567',
                ]
            }
        ]
    """

    filters_list = []
    for k,v in filters_dict.iteritems():
        filter_dict = {'Name': k}
        if isinstance(v, string_types):
            filter_dict['Values'] = [v]
        else:
            filter_dict['Values'] = v

        filters_list.append(filter_dict)

    return filters_list


def boto3_tag_list_to_ansible_dict(tags_list):

    """ Convert a boto3 list of resource tags to a flat dict of key:value pairs
    Args:
        tags_list (list): List of dicts representing AWS tags.
    Basic Usage:
        >>> tags_list = [{'Key': 'MyTagKey', 'Value': 'MyTagValue'}]
        >>> boto3_tag_list_to_ansible_dict(tags_list)
        [
            {
                'Key': 'MyTagKey',
                'Value': 'MyTagValue'
            }
        ]
    Returns:
        Dict: Dict of key:value pairs representing AWS tags
         {
            'MyTagKey': 'MyTagValue',
        }
    """

    tags_dict = {}
    for tag in tags_list:
        if 'key' in tag:
            tags_dict[tag['key']] = tag['value']
        elif 'Key' in tag:
            tags_dict[tag['Key']] = tag['Value']

    return tags_dict


def ansible_dict_to_boto3_tag_list(tags_dict):

    """ Convert a flat dict of key:value pairs representing AWS resource tags to a boto3 list of dicts
    Args:
        tags_dict (dict): Dict representing AWS resource tags.
    Basic Usage:
        >>> tags_dict = {'MyTagKey': 'MyTagValue'}
        >>> ansible_dict_to_boto3_tag_list(tags_dict)
        {
            'MyTagKey': 'MyTagValue'
        }
    Returns:
        List: List of dicts containing tag keys and values
        [
            {
                'Key': 'MyTagKey',
                'Value': 'MyTagValue'
            }
        ]
    """

    tags_list = []
    for k,v in tags_dict.iteritems():
        tags_list.append({'Key': k, 'Value': v})

    return tags_list


def get_ec2_security_group_ids_from_names(sec_group_list, ec2_connection, vpc_id=None, boto3=True):

    """ Return list of security group IDs from security group names. Note that security group names are not unique
     across VPCs.  If a name exists across multiple VPCs and no VPC ID is supplied, all matching IDs will be returned. This
     will probably lead to a boto exception if you attempt to assign both IDs to a resource so ensure you wrap the call in
     a try block
     """

    def get_sg_name(sg, boto3):

        if boto3:
            return sg['GroupName']
        else:
            return sg.name


    def get_sg_id(sg, boto3):

        if boto3:
            return sg['GroupId']
        else:
            return sg.id


    sec_group_id_list = []

    if isinstance(sec_group_list, string_types):
        sec_group_list = [sec_group_list]

    # Get all security groups
    if boto3:
        if vpc_id:
            filters = [
                {
                    'Name': 'vpc-id',
                    'Values': [
                        vpc_id,
                    ]
                }
            ]
            all_sec_groups = ec2_connection.describe_security_groups(Filters=filters)['SecurityGroups']
        else:
            all_sec_groups = ec2_connection.describe_security_groups()['SecurityGroups']
    else:
        if vpc_id:
            filters = { 'vpc-id': vpc_id }
            all_sec_groups = ec2_connection.get_all_security_groups(filters=filters)
        else:
            all_sec_groups = ec2_connection.get_all_security_groups()

    unmatched = set(sec_group_list).difference(str(get_sg_name(all_sg, boto3)) for all_sg in all_sec_groups)
    sec_group_name_list = list(set(sec_group_list) - set(unmatched))

    if len(unmatched) > 0:
        # If we have unmatched names that look like an ID, assume they are
        import re
        sec_group_id_list[:] = [sg for sg in unmatched if re.match('sg-[a-fA-F0-9]+$', sg)]
        still_unmatched = [sg for sg in unmatched if not re.match('sg-[a-fA-F0-9]+$', sg)]
        if len(still_unmatched) > 0:
            raise ValueError("The following group names are not valid: %s" % ', '.join(still_unmatched))

    sec_group_id_list += [ str(get_sg_id(all_sg, boto3)) for all_sg in all_sec_groups if str(get_sg_name(all_sg, boto3)) in sec_group_name_list ]

    return sec_group_id_list

