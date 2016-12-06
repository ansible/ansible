#!/usr/bin/python
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

DOCUMENTATION = '''
---
module: ec2_vpc_vgw_facts
short_description: Gather facts about virtual gateways in AWS
description:
    - Gather facts about virtual gateways in AWS
version_added: "2.3"
requirements: [ boto3 ]
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value. See U(http://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeRouteTables.html) for possible filters.
    required: false
    default: None
  VpnGatewayIds:
    description:
      - Get details of specific Virtual Gateway ID
      - Provide this value as a list
    required: false
    default: None
author: "Nick Aslanidis (@naslanidis)"
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# # Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Gather facts about all virtual gateways for an account or profile
  ec2_vpc_vgw_facts:
    region: ap-southeast-2
    profile: production
  register: vgw_facts

- name: Gather facts about a filtered list of Virtual Gateways
  ec2_vpc_vgw_facts:
    region: ap-southeast-2
    profile: production
    filters:
        "tag:Name": "vgw-123"
  register: vgw_facts

- name: Gather facts about a specific virtual gateway by VpnGatewayIds
  ec2_vpc_vgw_facts:
    region: ap-southeast-2
    profile: production
    VpnGatewayIds: vgw-c432f6a7 
  register: vgw_facts
'''

RETURN = '''
virtual_gateways:
    description: The virtual gateways for the account
    returned: always
    type: list

changed:
    description: True if listing the virtual gateways succeeds
    type: bool
    returned: always
'''

import json

try:
    import botocore
    import boto3   
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


def get_virtual_gateway_info(virtual_gateway):
    virtual_gateway_info = {'VpnGatewayId': virtual_gateway['VpnGatewayId'],
                             'State': virtual_gateway['State'],
                             'Type': virtual_gateway['Type'],
                             'VpcAttachments': virtual_gateway['VpcAttachments'],
                             'Tags': virtual_gateway['Tags']                                                              
               }
    return virtual_gateway_info


def list_virtual_gateways(client, module):
    dryrun = module.params.get("DryRun")
    all_virtual_gateways_array = []
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

    if module.params.get("DryRun"):
        params['DryRun'] = module.params.get("DryRun")

    if module.params.get("VpnGatewayIds"):
        params['VpnGatewayIds'] = module.params.get("VpnGatewayIds")

    try:
        all_virtual_gateways = client.describe_vpn_gateways(**params)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=str(e))

    for virtual_gateway in all_virtual_gateways['VpnGateways']:
        all_virtual_gateways_array.append(get_virtual_gateway_info(virtual_gateway))

    #Turn the boto3 result in to ansible_friendly_snaked_names
    snaked_vgw_array = []
    for vgw in all_virtual_gateways_array:
        snaked_vgw_array.append(camel_dict_to_snake_dict(vgw))
    
    module.exit_json(virtual_gateways=snaked_vgw_array)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            filters = dict(type='dict', default=None, ),
            DryRun = dict(type='bool', default=False),
            VpnGatewayIds = dict(type='list', default=None)
        )
    )

    module = AnsibleModule(argument_spec=argument_spec)

     # Validate Requirements
    if not HAS_BOTO3:
        module.fail_json(msg='json and botocore/boto3 is required.')

    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        connection = boto3_conn(module, conn_type='client', resource='ec2', region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except botocore.exceptions.NoCredentialsError as e:
        module.fail_json(msg="Can't authorize connection - "+str(e))

    # call your function here
    results = list_virtual_gateways(connection, module)
    
    module.exit_json(result=results)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
