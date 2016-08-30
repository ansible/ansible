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
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value. See U(http://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeRouteTables.html) for possible filters.
    required: false
    default: null
  DhcpOptionsIds:
    description:
      - Get details of specific DHCP Option ID
      - Provide this value as a list
    required: false
    default: None
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

import json

try:
    import botocore
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


def get_dhcp_options_info(dhcp_option):
    dhcp_option_info = {'DhcpOptionsId': dhcp_option['DhcpOptionsId'],
                       'DhcpConfigurations': dhcp_option['DhcpConfigurations'],
                       'Tags': dhcp_option['Tags']
               }
    return dhcp_option_info


def list_dhcp_options(client, module):
    dryrun = module.params.get("DryRun")
    all_dhcp_options_array = []
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

    if module.params.get("DhcpOptionsIds"):
        params['DhcpOptionsIds'] = module.params.get("DhcpOptionsIds")

    try:
        all_dhcp_options = client.describe_dhcp_options(**params)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=str(e))

    for dhcp_option in all_dhcp_options['DhcpOptions']:
        all_dhcp_options_array.append(get_dhcp_options_info(dhcp_option))

    snaked_dhcp_options_array = []
    for dhcp_option in all_dhcp_options_array:
         snaked_dhcp_options_array.append(camel_dict_to_snake_dict(dhcp_option))

    module.exit_json(dhcp_options=snaked_dhcp_options_array)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            filters = dict(type='dict', default=None, ),
            DryRun = dict(type='bool', default=False),
            DhcpOptionsIds = dict(type='list', default=None)
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
    results = list_dhcp_options(connection, module)

    module.exit_json(result=results)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
