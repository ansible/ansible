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
module: ec2_vpc_dhcp_options_facts
short_description: Gather facts about dhcp options sets in AWS
description:
    - Gather facts about dhcp options sets in AWS
version_added: "2.2"
requirements: [ boto3 ]
author: "Nick Aslanidis (@naslanidis)"
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        See U(http://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeRouteTables.html) for possible filters.
    required: false
    default: null
  dhcp_options_ids:
    description:
      - Get details of specific DHCP Option ID
      - Provide this value as a list
    required: false
    default: None
    aliases: ['DhcpOptionsIds']
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# # Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Gather facts about all DHCP Option sets for an account or profile
  ec2_vpc_dhcp_options_facts:
    region: ap-southeast-2
    profile: production
  register: dhcp_facts

- name: Gather facts about a filtered list of DHCP Option sets
  ec2_vpc_dhcp_options_facts:
    region: ap-southeast-2
    profile: production
    filters:
        "tag:Name": "abc-123"
  register: dhcp_facts

- name: Gather facts about a specific DHCP Option set by DhcpOptionId
  ec2_vpc_dhcp_options_facts:
    region: ap-southeast-2
    profile: production
    DhcpOptionsIds: dopt-123fece2
  register: dhcp_facts

'''

RETURN = '''
dhcp_options:
    description: The dhcp option sets for the account
    returned: always
    type: list

changed:
    description: True if listing the dhcp options succeeds
    type: bool
    returned: always
'''

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import ec2_argument_spec, boto3_conn, HAS_BOTO3
from ansible.module_utils.ec2 import ansible_dict_to_boto3_filter_list, get_aws_connection_info
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, boto3_tag_list_to_ansible_dict

try:
    import botocore
except ImportError:
    pass  # caught by imported HAS_BOTO3


def get_dhcp_options_info(dhcp_option):
    dhcp_option_info = {'DhcpOptionsId': dhcp_option['DhcpOptionsId'],
                        'DhcpConfigurations': dhcp_option['DhcpConfigurations'],
                        'Tags': boto3_tag_list_to_ansible_dict(dhcp_option.get('Tags', [{'Value': '', 'Key': 'Name'}]))}
    return dhcp_option_info


def list_dhcp_options(client, module):
    params = dict(Filters=ansible_dict_to_boto3_filter_list(module.params.get('filters')))

    if module.params.get("dry_run"):
        params['DryRun'] = True

    if module.params.get("dhcp_options_ids"):
        params['DhcpOptionsIds'] = module.params.get("dhcp_options_ids")

    try:
        all_dhcp_options = client.describe_dhcp_options(**params)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc(),
                         **camel_dict_to_snake_dict(e.response))

    results = [camel_dict_to_snake_dict(get_dhcp_options_info(option))
               for option in all_dhcp_options['DhcpOptions']]

    module.exit_json(dhcp_options=results)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            filters=dict(type='dict', default={}),
            dry_run=dict(type='bool', default=False, aliases=['DryRun']),
            dhcp_options_ids=dict(type='list', aliases=['DhcpOptionIds'])
        )
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    # Validate Requirements
    if not HAS_BOTO3:
        module.fail_json(msg='boto3 and botocore are required.')

    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        connection = boto3_conn(module, conn_type='client', resource='ec2', region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except botocore.exceptions.NoCredentialsError as e:
        module.fail_json(msg="Can't authorize connection - " + str(e))

    # call your function here
    results = list_dhcp_options(connection, module)

    module.exit_json(result=results)


if __name__ == '__main__':
    main()
