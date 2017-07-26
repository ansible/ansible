#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This Ansible library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ec2_lc_facts
short_description: Gather facts about AWS Autoscaling Launch Configurations
description:
    - Gather facts about AWS Autoscaling Launch Configurations
version_added: "2.3"
author: "Loïc Latreille (@psykotox)"
requirements: [ boto3 ]
options:
  name:
    description:
      - A name or a list of name to match.
    required: false
    default: []
  sort:
    description:
      - Optional attribute which with to sort the results.
    choices: ['launch_configuration_name', 'image_id', 'created_time', 'instance_type', 'kernel_id', 'ramdisk_id', 'key_name']
    default: null
    required: false
  sort_order:
    description:
      - Order in which to sort results.
      - Only used when the 'sort' parameter is specified.
    choices: ['ascending', 'descending']
    default: 'ascending'
    required: false
  sort_start:
    description:
      - Which result to start with (when sorting).
      - Corresponds to Python slice notation.
    default: null
    required: false
  sort_end:
    description:
      - Which result to end with (when sorting).
      - Corresponds to Python slice notation.
    default: null
    required: false
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Gather facts about all launch configurations
- ec2_lc_facts:

# Gather facts about launch configuration with name "example"
- ec2_lc_facts:
    name: example

# Gather facts sorted by created_time from most recent to least recent
- ec2_lc_facts:
    sort: created_time
    sort_order: descending
'''

RETURN = '''
block_device_mapping:
    description: Block device mapping for the instances of launch configuration
    type: list
    returned: always
    sample: "[{
        'device_name': '/dev/xvda':,
        'ebs': {
            'delete_on_termination': true,
            'volume_size': 8,
            'volume_type': 'gp2'
    }]"
classic_link_vpc_security_groups:
    description: IDs of one or more security groups for the VPC specified in classic_link_vpc_id
    type: string
    returned: always
    sample:
created_time:
    description: The creation date and time for the launch configuration
    type: string
    returned: always
    sample: "2016-05-27T13:47:44.216000+00:00"
ebs_optimized:
    description: EBS I/O optimized (true ) or not (false )
    type: bool
    returned: always
    sample: true,
image_id:
    description: ID of the Amazon Machine Image (AMI)
    type: string
    returned: always
    sample: "ami-12345678"
instance_monitoring:
    description: Launched with detailed monitoring or not
    type: dict
    returned: always
    sample: "{
        'enabled': true
    }"
instance_type:
    description: Instance type
    type: string
    returned: always
    sample: "t2.micro"
kernel_id:
    description: ID of the kernel associated with the AMI
    type: string
    returned: always
    sample:
key_name:
    description: Name of the key pair
    type: string
    returned: always
    sample: "user_app"
launch_configuration_arn:
    description: Amazon Resource Name (ARN) of the launch configuration
    type: string
    returned: always
    sample: "arn:aws:autoscaling:us-east-1:666612345678:launchConfiguration:ba785e3a-dd42-6f02-4585-ea1a2b458b3d:launchConfigurationName/lc-app"
launch_configuration_name:
    description: Name of the launch configuration
    type: string
    returned: always
    sample: "lc-app"
ramdisk_id:
    description: ID of the RAM disk associated with the AMI
    type: string
    returned: always
    sample:
security_groups:
    description: Security groups to associated
    type: list
    returned: always
    sample: "[
        'web'
    ]"
user_data:
    description: User data available
    type: string
    returned: always
    sample:
'''

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

from ansible.module_utils.ec2 import paging


def list_launch_configs(connection, module):

    launch_config_name = module.params.get("name")
    sort = module.params.get('sort')
    sort_order = module.params.get('sort_order')
    sort_start = module.params.get('sort_start')
    sort_end = module.params.get('sort_end')

    try:
        launch_configs = {'LaunchConfigurations': paging(pause=0, marker_property='NextToken', result_key='LaunchConfigurations')
                                                        (connection.describe_launch_configurations)(LaunchConfigurationNames=launch_config_name)}
    except ClientError as e:
        module.fail_json(msg=e.message)

    snaked_launch_configs = []
    for launch_config in launch_configs['LaunchConfigurations']:
        snaked_launch_configs.append(camel_dict_to_snake_dict(launch_config))

    for launch_config in snaked_launch_configs:
        if 'CreatedTime' in launch_config:
            launch_config['CreatedTime'] = str(launch_config['CreatedTime'])

    if sort:
        snaked_launch_configs.sort(key=lambda e: e[sort], reverse=(sort_order=='descending'))

    try:
        if sort and sort_start and sort_end:
            snaked_launch_configs = snaked_launch_configs[int(sort_start):int(sort_end)]
        elif sort and sort_start:
            snaked_launch_configs = snaked_launch_configs[int(sort_start):]
        elif sort and sort_end:
            snaked_launch_configs = snaked_launch_configs[:int(sort_end)]
    except TypeError:
        module.fail_json(msg="Please supply numeric values for sort_start and/or sort_end")

    module.exit_json(launch_configurations=snaked_launch_configs)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name = dict(required=False, default=[], type='list'),
            sort = dict(required=False, default=None,
                choices=['launch_configuration_name', 'image_id', 'created_time', 'instance_type', 'kernel_id', 'ramdisk_id', 'key_name']),
            sort_order = dict(required=False, default='ascending',
                choices=['ascending', 'descending']),
            sort_start = dict(required=False),
            sort_end = dict(required=False),
        )
    )

    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)

    if region:
        connection = boto3_conn(module, conn_type='client', resource='autoscaling', region=region, endpoint=ec2_url, **aws_connect_params)
    else:
        module.fail_json(msg="region must be specified")

    list_launch_configs(connection, module)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
