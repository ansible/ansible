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

DOCUMENTATION = '''
module: ec2_vpc_peering_facts
short_description: Retrieves AWS VPC Peering details using AWS methods. Requires Boto3.
description:
  - Gets various details related to AWS VPC Peers
version_added: "2.1"
options:
  peer_connection_ids:
    description:
      - Get details of specific vpc peer IDs
    required: false
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        See U(http://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeVpcPeeringConnections.html)
        for possible filters.
  region:
    description:
      - VPC peers are region specific and a region must be provided.
    required: true
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

try:
    import json
    import botocore
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

import time


def date_handler(obj):
    return obj.isoformat() if hasattr(obj, 'isoformat') else obj


def get_vpc_peers(client, module):
    params = dict()
    if module.params.get('filters'):
        params['Filters'] = []
        for key, value in module.params.get('filters').iteritems():
            temp_dict = dict()
            temp_dict['Name'] = key
            if isinstance(value, basestring):
                temp_dict['Values'] = [value]
            else:
                temp_dict['Values'] = value
            params['Filters'].append(temp_dict)
    if module.params.get('peer_connection_ids'):
        params['VpcPeeringConnectionIds'] = module.params.get('peer_connection_ids')
    try:
        result = json.loads(json.dumps(client.describe_vpc_peering_connections(**params), default=date_handler))
    except Exception as e:
        module.fail_json(msg=str(e.message))

    return result['VpcPeeringConnections']


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        filters=dict(default=None, type='dict'),
        peer_connection_ids=dict(default=None, type='list'),
        region=dict(required=True),
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    # Validate Requirements
    if not HAS_BOTO3:
        module.fail_json(msg='json and botocore/boto3 is required.')

    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        ec2 = boto3_conn(module, conn_type='client', resource='ec2', region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except botocore.exceptions.NoCredentialsError, e:
        module.fail_json(msg="Can't authorize connection - "+str(e))

    results = get_vpc_peers(ec2, module)

    module.exit_json(result=results)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
