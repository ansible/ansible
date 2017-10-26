#!/usr/bin/python
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''
---
module: ec2_lc

short_description: Create or delete AWS Autoscaling Launch Configurations

description:
  - Can create or delete AWS Autoscaling Configurations
  - Works with the ec2_asg module to manage Autoscaling Groups

notes:
  - Amazon ASG Autoscaling Launch Configurations are immutable once created, so modifying the configuration after it is changed will not modify the
    launch configuration on AWS. You must create a new config and assign it to the ASG instead.
  - encrypted volumes are supported on versions >= 2.4

version_added: "1.6"

author:
  - "Gareth Rushgrove (@garethr)"
  - "Willem van Ketwich (@wilvk)"

options:
  state:
    description:
      - Register or deregister the instance
    required: true
    choices: ['present', 'absent']
  name:
    description:
      - Unique name for configuration
    required: true
  instance_type:
    description:
      - Instance type to use for the instance
    required: true
    default: null
    aliases: []
  image_id:
    description:
      - The AMI unique identifier to be used for the group
  key_name:
    description:
      - The SSH key name to be used for access to managed instances
  security_groups:
    description:
      - A list of security groups to apply to the instances. Since version 2.4 you can specify either security group names or IDs or a mix.  Previous
        to 2.4, for VPC instances, specify security group IDs and for EC2-Classic, specify either security group names or IDs.
  volumes:
    description:
      - A list of volume dicts, each containing device name and optionally ephemeral id or snapshot id. Size and type (and number of iops for io
        device type) must be specified for a new volume or a root volume, and may be passed for a snapshot volume. For any volume, a volume size less
        than 1 will be interpreted as a request not to create the volume.
  user_data:
    description:
      - Opaque blob of data which is made available to the ec2 instance. Mutually exclusive with I(user_data_path).
  user_data_path:
    description:
      - Path to the file that contains userdata for the ec2 instances. Mutually exclusive with I(user_data).
    version_added: "2.3"
  kernel_id:
    description:
      - Kernel id for the EC2 instance
  spot_price:
    description:
      - The spot price you are bidding. Only applies for an autoscaling group with spot instances.
  instance_monitoring:
    description:
      - Specifies whether instances are launched with detailed monitoring.
    default: false
  assign_public_ip:
    description:
      - Used for Auto Scaling groups that launch instances into an Amazon Virtual Private Cloud. Specifies whether to assign a public IP address
        to each instance launched in a Amazon VPC.
    version_added: "1.8"
  ramdisk_id:
    description:
      - A RAM disk id for the instances.
    version_added: "1.8"
  instance_profile_name:
    description:
      - The name or the Amazon Resource Name (ARN) of the instance profile associated with the IAM role for the instances.
    version_added: "1.8"
  ebs_optimized:
    description:
      - Specifies whether the instance is optimized for EBS I/O (true) or not (false).
    default: false
    version_added: "1.8"
  classic_link_vpc_id:
    description:
      - Id of ClassicLink enabled VPC
    version_added: "2.0"
  classic_link_vpc_security_groups:
    description:
      - A list of security group IDs with which to associate the ClassicLink VPC instances.
    version_added: "2.0"
  vpc_id:
    description:
      - VPC ID, used when resolving security group names to IDs.
    version_added: "2.4"
  instance_id:
    description:
      - The Id of a running instance to use as a basis for a launch configuration. Can be used in place of image_id and instance_type.
    version_added: "2.4"
  placement_tenancy:
    description:
      - Determines whether the instance runs on single-tenant harware or not.
    default: 'default'
    version_added: "2.4"

extends_documentation_fragment:
    - aws
    - ec2

requirements:
    - boto3 >= 1.4.4

'''

EXAMPLES = '''

# create a launch configuration using an AMI image and instance type as a basis

- name: note that encrypted volumes are only supported in >= Ansible 2.4
  ec2_lc:
    name: special
    image_id: ami-XXX
    key_name: default
    security_groups: ['group', 'group2' ]
    instance_type: t1.micro
    volumes:
    - device_name: /dev/sda1
      volume_size: 100
      device_type: io1
      iops: 3000
      delete_on_termination: true
      encrypted: true
    - device_name: /dev/sdb
      ephemeral: ephemeral0

# create a launch configuration using a running instance id as a basis

- ec2_lc:
    name: special
    instance_id: i-00a48b207ec59e948
    key_name: default
    security_groups: ['launch-wizard-2' ]
    volumes:
    - device_name: /dev/sda1
      volume_size: 120
      device_type: io1
      iops: 3000
      delete_on_termination: true

'''

import traceback
from ansible.module_utils.ec2 import (get_aws_connection_info, ec2_argument_spec, ec2_connect, camel_dict_to_snake_dict, get_ec2_security_group_ids_from_names,
                                      boto3_conn, snake_dict_to_camel_dict, HAS_BOTO3)
from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule

try:
    import botocore
except ImportError:
    pass


def create_block_device_meta(module, volume):
    MAX_IOPS_TO_SIZE_RATIO = 30
    if 'snapshot' not in volume and 'ephemeral' not in volume:
        if 'volume_size' not in volume:
            module.fail_json(msg='Size must be specified when creating a new volume or modifying the root volume')
    if 'snapshot' in volume:
        if 'device_type' in volume and volume.get('device_type') == 'io1' and 'iops' not in volume:
            module.fail_json(msg='io1 volumes must have an iops value set')
    if 'ephemeral' in volume:
        if 'snapshot' in volume:
            module.fail_json(msg='Cannot set both ephemeral and snapshot')

    return_object = {}

    if 'ephemeral' in volume:
        return_object['VirtualName'] = volume.get('ephemeral')

    if 'device_name' in volume:
        return_object['DeviceName'] = volume.get('device_name')

    if 'no_device' is volume:
        return_object['NoDevice'] = volume.get('no_device')

    if any(key in volume for key in ['snapshot', 'volume_size', 'volume_type', 'delete_on_termination', 'ips', 'encrypted']):
        return_object['Ebs'] = {}

    if 'snapshot' in volume:
        return_object['Ebs']['SnapshotId'] = volume.get('snapshot')

    if 'volume_size' in volume:
        return_object['Ebs']['VolumeSize'] = volume.get('volume_size')

    if 'volume_type' in volume:
        return_object['Ebs']['VolumeType'] = volume.get('volume_type')

    if 'delete_on_termination' in volume:
        return_object['Ebs']['DeleteOnTermination'] = volume.get('delete_on_termination', False)

    if 'iops' in volume:
        return_object['Ebs']['Iops'] = volume.get('iops')

    if 'encrypted' in volume:
        return_object['Ebs']['Encrypted'] = volume.get('encrypted')

    return return_object


def create_launch_config(connection, module):
    name = module.params.get('name')
    vpc_id = module.params.get('vpc_id')
    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        ec2_connection = boto3_conn(module, 'client', 'ec2', region, ec2_url, **aws_connect_kwargs)
        security_groups = get_ec2_security_group_ids_from_names(module.params.get('security_groups'), ec2_connection, vpc_id=vpc_id, boto3=True)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Failed to get Security Group IDs", exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    except ValueError as e:
        module.fail_json(msg="Failed to get Security Group IDs", exception=traceback.format_exc())
    user_data = module.params.get('user_data')
    user_data_path = module.params.get('user_data_path')
    volumes = module.params['volumes']
    instance_monitoring = module.params.get('instance_monitoring')
    assign_public_ip = module.params.get('assign_public_ip')
    instance_profile_name = module.params.get('instance_profile_name')
    ebs_optimized = module.params.get('ebs_optimized')
    classic_link_vpc_id = module.params.get('classic_link_vpc_id')
    classic_link_vpc_security_groups = module.params.get('classic_link_vpc_security_groups')

    block_device_mapping = []

    convert_list = ['image_id', 'instance_type', 'instance_type', 'instance_id', 'placement_tenancy', 'key_name', 'kernel_id', 'ramdisk_id', 'spot_price']

    launch_config = (snake_dict_to_camel_dict(dict((k.capitalize(), str(v)) for k, v in module.params.items() if v is not None and k in convert_list)))

    if user_data_path:
        try:
            with open(user_data_path, 'r') as user_data_file:
                user_data = user_data_file.read()
        except IOError as e:
            module.fail_json(msg="Failed to open file for reading", exception=traceback.format_exc())

    if volumes:
        for volume in volumes:
            if 'device_name' not in volume:
                module.fail_json(msg='Device name must be set for volume')
            # Minimum volume size is 1GB. We'll use volume size explicitly set to 0 to be a signal not to create this volume
            if 'volume_size' not in volume or int(volume['volume_size']) > 0:
                block_device_mapping.append(create_block_device_meta(module, volume))

    try:
        launch_configs = connection.describe_launch_configurations(LaunchConfigurationNames=[name]).get('LaunchConfigurations')
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Failed to describe launch configuration by name", exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    changed = False
    result = {}

    launch_config['LaunchConfigurationName'] = name

    if security_groups is not None:
        launch_config['SecurityGroups'] = security_groups

    if classic_link_vpc_id is not None:
        launch_config['ClassicLinkVPCId'] = classic_link_vpc_id

    if instance_monitoring:
        launch_config['InstanceMonitoring'] = {'Enabled': instance_monitoring}

    if classic_link_vpc_security_groups is not None:
        launch_config['ClassicLinkVPCSecurityGroups'] = classic_link_vpc_security_groups

    if block_device_mapping:
        launch_config['BlockDeviceMappings'] = block_device_mapping

    if instance_profile_name is not None:
        launch_config['IamInstanceProfile'] = instance_profile_name

    if assign_public_ip is not None:
        launch_config['AssociatePublicIpAddress'] = assign_public_ip

    if user_data is not None:
        launch_config['UserData'] = user_data

    if ebs_optimized is not None:
        launch_config['EbsOptimized'] = ebs_optimized

    if len(launch_configs) == 0:
        try:
            connection.create_launch_configuration(**launch_config)
            launch_configs = connection.describe_launch_configurations(LaunchConfigurationNames=[name]).get('LaunchConfigurations')
            changed = True
            if launch_configs:
                launch_config = launch_configs[0]
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Failed to create launch configuration", exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    result = (dict((k, v) for k, v in launch_config.items()
              if k not in ['Connection', 'CreatedTime', 'InstanceMonitoring', 'BlockDeviceMappings']))

    result['CreatedTime'] = to_text(launch_config.get('CreatedTime'))

    try:
        result['InstanceMonitoring'] = module.boolean(launch_config.get('InstanceMonitoring').get('Enabled'))
    except AttributeError:
        result['InstanceMonitoring'] = False

    result['BlockDeviceMappings'] = []

    for block_device_mapping in launch_config.get('BlockDeviceMappings', []):
        result['BlockDeviceMappings'].append(dict(device_name=block_device_mapping.get('DeviceName'), virtual_name=block_device_mapping.get('VirtualName')))
        if block_device_mapping.get('Ebs') is not None:
            result['BlockDeviceMappings'][-1]['ebs'] = dict(
                snapshot_id=block_device_mapping.get('Ebs').get('SnapshotId'), volume_size=block_device_mapping.get('Ebs').get('VolumeSize'))

    if user_data_path:
        result['UserData'] = "hidden"  # Otherwise, we dump binary to the user's terminal

    return_object = {
        'Name': result.get('LaunchConfigurationName'),
        'CreatedTime': result.get('CreatedTime'),
        'ImageId': result.get('ImageId'),
        'Arn': result.get('LaunchConfigurationARN'),
        'SecurityGroups': result.get('SecurityGroups'),
        'InstanceType': result.get('InstanceType'),
        'Result': result
    }

    module.exit_json(changed=changed, **camel_dict_to_snake_dict(return_object))


def delete_launch_config(connection, module):
    try:
        name = module.params.get('name')
        launch_configs = connection.describe_launch_configurations(LaunchConfigurationNames=[name]).get('LaunchConfigurations')
        if launch_configs:
            connection.delete_launch_configuration(LaunchConfigurationName=launch_configs[0].get('LaunchConfigurationName'))
            module.exit_json(changed=True)
        else:
            module.exit_json(changed=False)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Failed to delete launch configuration", exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name=dict(required=True),
            image_id=dict(),
            instance_id=dict(),
            key_name=dict(),
            security_groups=dict(default=[], type='list'),
            user_data=dict(),
            user_data_path=dict(type='path'),
            kernel_id=dict(),
            volumes=dict(type='list'),
            instance_type=dict(),
            state=dict(default='present', choices=['present', 'absent']),
            spot_price=dict(type='float'),
            ramdisk_id=dict(),
            instance_profile_name=dict(),
            ebs_optimized=dict(default=False, type='bool'),
            associate_public_ip_address=dict(type='bool'),
            instance_monitoring=dict(default=False, type='bool'),
            assign_public_ip=dict(type='bool'),
            classic_link_vpc_security_groups=dict(type='list'),
            classic_link_vpc_id=dict(),
            vpc_id=dict(),
            placement_tenancy=dict(default='default', choices=['default', 'dedicated'])
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=[['user_data', 'user_data_path']]
    )

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        connection = boto3_conn(module, conn_type='client', resource='autoscaling', region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except botocore.exceptions.NoRegionError:
        module.fail_json(msg=("region must be specified as a parameter in AWS_DEFAULT_REGION environment variable or in boto configuration file"))
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="unable to establish connection - " + str(e), exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    state = module.params.get('state')

    if state == 'present':
        create_launch_config(connection, module)
    elif state == 'absent':
        delete_launch_config(connection, module)


if __name__ == '__main__':
    main()
