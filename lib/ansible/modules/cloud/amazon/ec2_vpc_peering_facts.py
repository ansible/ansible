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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: ec2_vpc_peering_facts
short_description: Retrieves AWS VPC Peering details using AWS methods.
description:
  - Gets various details related to AWS VPC Peers
version_added: "2.4"
requirements: [ boto3 ]
options:
  peer_connection_ids:
    description:
      - Get details of specific vpc peer IDs
    required: false
    default: None
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        See U(http://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeVpcPeeringConnections.html)
        for possible filters.
    required: false
    default: None
author: Karen Cheng(@Etherdaemon)
extends_documentation_fragment: aws
'''

EXAMPLES = '''
# Simple example of listing all VPC Peers
- name: List all vpc peers
  ec2_vpc_peering_facts:
    region: ap-southeast-2
  register: all_vpc_peers

- name: Debugging the result
  debug:
    msg: "{{ all_vpc_peers.result }}"

- name: Get details on specific VPC peer
  ec2_vpc_peering_facts:
    peer_connection_ids:
      - pcx-12345678
      - pcx-87654321
    region: ap-southeast-2
  register: all_vpc_peers

- name: Get all vpc peers with specific filters
  ec2_vpc_peering_facts:
    region: ap-southeast-2
    filters:
      status-code: ['pending-acceptance']
  register: pending_vpc_peers
'''

RETURN = '''
result:
  description: The result of the describe.
  returned: success
  type: list
'''

import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import ec2_argument_spec, boto3_conn, get_aws_connection_info
from ansible.module_utils.ec2 import ansible_dict_to_boto3_filter_list, HAS_BOTO3
from ansible.module_utils.ec2 import camel_dict_to_snake_dict

try:
    import botocore
except ImportError:
    pass  # will be picked up by imported HAS_BOTO3


def date_handler(obj):
    return obj.isoformat() if hasattr(obj, 'isoformat') else obj


def get_vpc_peers(client, module):
    params = dict()
    params['Filters'] = ansible_dict_to_boto3_filter_list(module.params.get('filters'))
    if module.params.get('peer_connection_ids'):
        params['VpcPeeringConnectionIds'] = module.params.get('peer_connection_ids')
    try:
        result = json.loads(json.dumps(client.describe_vpc_peering_connections(**params), default=date_handler))
    except Exception as e:
        module.fail_json(msg=str(e.message))

    return result['VpcPeeringConnections']


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            filters=dict(default=dict(), type='dict'),
            peer_connection_ids=dict(default=None, type='list'),
        )
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    # Validate Requirements
    if not HAS_BOTO3:
        module.fail_json(msg='botocore and boto3 are required.')

    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    except NameError as e:
        # Getting around the get_aws_connection_info boto reliance for region
        if "global name 'boto' is not defined" in e.message:
            module.params['region'] = botocore.session.get_session().get_config_variable('region')
            if not module.params['region']:
                module.fail_json(msg="Error - no region provided")
        else:
            module.fail_json(msg="Can't retrieve connection information - " + str(e))

    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        ec2 = boto3_conn(module, conn_type='client', resource='ec2', region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except botocore.exceptions.NoCredentialsError as e:
        module.fail_json(msg=str(e))

    results = [camel_dict_to_snake_dict(peer) for peer in get_vpc_peers(ec2, module)]

    module.exit_json(result=results)


if __name__ == '__main__':
    main()
