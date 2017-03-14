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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ec2_vpc_vgw_facts
short_description: Gather facts about virtual gateways in AWS
description:
    - Gather facts about virtual gateways in AWS.
version_added: "2.3"
requirements: [ boto3 ]
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value. See U(http://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeRouteTables.html) for possible filters.
    required: false
    default: None
  vpn_gateway_ids:
    description:
      - Get details of a specific Virtual Gateway ID. This value should be provided as a list.
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
        "tag:Name": "main-virt-gateway"
  register: vgw_facts

- name: Gather facts about a specific virtual gateway by VpnGatewayIds
  ec2_vpc_vgw_facts:
    region: ap-southeast-2
    profile: production
    vpn_gateway_ids: vgw-c432f6a7
  register: vgw_facts
'''

RETURN = '''
virtual_gateways:
    description: The virtual gateways for the account.
    returned: always
    type: list
    sample: [
        {
            "state": "available",
            "tags": [
                {
                    "key": "Name",
                    "value": "TEST-VGW"
                }
            ],
            "type": "ipsec.1",
            "vpc_attachments": [
                {
                    "state": "attached",
                    "vpc_id": "vpc-22a93c74"
                }
            ],
            "vpn_gateway_id": "vgw-23e3d64e"
        }
    ]

changed:
    description: True if listing the virtual gateways succeeds.
    returned: always
    type: bool
    sample: "false"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import ec2_argument_spec, get_aws_connection_info
from ansible.module_utils.ec2 import boto3_conn, camel_dict_to_snake_dict
from ansible.module_utils.ec2 import ansible_dict_to_boto3_filter_list, HAS_BOTO3

try:
    import botocore
except ImportError:
    pass  # will be captured by imported HAS_BOTO3


def get_virtual_gateway_info(virtual_gateway):
    virtual_gateway_info = {'VpnGatewayId': virtual_gateway['VpnGatewayId'],
                             'State': virtual_gateway['State'],
                             'Type': virtual_gateway['Type'],
                             'VpcAttachments': virtual_gateway['VpcAttachments'],
                             'Tags': virtual_gateway['Tags']}
    return virtual_gateway_info


def list_virtual_gateways(client, module):
    params = dict()

    params['Filters'] = ansible_dict_to_boto3_filter_list(module.params.get('filters'))
    params['DryRun'] = module.check_mode

    if module.params.get("vpn_gateway_ids"):
        params['VpnGatewayIds'] = module.params.get("vpn_gateway_ids")

    try:
        all_virtual_gateways = client.describe_vpn_gateways(**params)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=str(e),exception=traceback.format_exc())

    snaked_vgws = [camel_dict_to_snake_dict(get_virtual_gateway_info(vgw))
                                for vgw in all_virtual_gateways['VpnGateways']]

    module.exit_json(virtual_gateways=snaked_vgws)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            filters = dict(type='dict', default=dict()),
            vpn_gateway_ids = dict(type='list', default=None)
        )
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    # Validate Requirements
    if not HAS_BOTO3:
        module.fail_json(msg='json and boto3 is required.')

    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        connection = boto3_conn(module, conn_type='client', resource='ec2', region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except botocore.exceptions.NoCredentialsError as e:
        module.fail_json(msg="Can't authorize connection - "+str(e))

    # call your function here
    results = list_virtual_gateways(connection, module)

    module.exit_json(result=results)


if __name__ == '__main__':
    main()
