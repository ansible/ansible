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
module: ec2_vpc_igw_facts
short_description: Gather facts about internet gateways in AWS
description:
    - Gather facts about internet gateways in AWS.
version_added: "2.3"
author: "Nick Aslanidis (@naslanidis)"
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        See U(http://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeInternetGateways.html) for possible filters.
    required: false
    default: null
  internet_gateway_ids:
    description:
      - Get details of specific Internet Gateway ID. Provide this value as a list.
    required: false
    default: None
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# # Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Gather facts about all Internet Gateways for an account or profile
  ec2_vpc_igw_facts:
    region: ap-southeast-2
    profile: production
  register: igw_facts

- name: Gather facts about a filtered list of Internet Gateways
  ec2_vpc_igw_facts:
    region: ap-southeast-2
    profile: production
    filters:
        "tag:Name": "igw-123"
  register: igw_facts

- name: Gather facts about a specific internet gateway by InternetGatewayId
  ec2_vpc_igw_facts:
    region: ap-southeast-2
    profile: production
    internet_gateway_ids: igw-c1231234
  register: igw_facts
'''

RETURN = '''
internet_gateways:
    description: The internet gateways for the account.
    returned: always
    type: list
    sample: [
        {
            "attachments": [
                {
                    "state": "available",
                    "vpc_id": "vpc-02123b67"
                }
            ],
            "internet_gateway_id": "igw-2123634d",
            "tags": [
                {
                    "key": "Name",
                    "value": "test-vpc-20-igw"
                }
            ]
        }
    ]

changed:
    description: True if listing the internet gateways succeeds.
    type: bool
    returned: always
    sample: "false"
'''

# import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import ec2_argument_spec, get_aws_connection_info
from ansible.module_utils.ec2 import boto3_conn, camel_dict_to_snake_dict
from ansible.module_utils.ec2 import ansible_dict_to_boto3_filter_list, HAS_BOTO3

try:
    import botocore
except ImportError:
    pass  # will be captured by imported HAS_BOTO3


def get_internet_gateway_info(internet_gateway):
    internet_gateway_info = {'InternetGatewayId': internet_gateway['InternetGatewayId'],
                             'Attachments': internet_gateway['Attachments'],
                             'Tags': internet_gateway['Tags']}
    return internet_gateway_info


def list_internet_gateways(client, module):
    params = dict()

    params['Filters'] = ansible_dict_to_boto3_filter_list(module.params.get('filters'))

    if module.params.get("internet_gateway_ids"):
        params['InternetGatewayIds'] = module.params.get("internet_gateway_ids")

    try:
        all_internet_gateways = client.describe_internet_gateways(**params)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=str(e))

    snaked_internet_gateways = [camel_dict_to_snake_dict(get_internet_gateway_info(igw))
                                for igw in all_internet_gateways['InternetGateways']]

    module.exit_json(internet_gateways=snaked_internet_gateways)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            filters=dict(type='dict', default=dict()),
            internet_gateway_ids=dict(type='list', default=None)
        )
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    # Validate Requirements
    if not HAS_BOTO3:
        module.fail_json(msg='botocore and boto3 are required.')

    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        connection = boto3_conn(module, conn_type='client', resource='ec2', region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except botocore.exceptions.NoCredentialsError as e:
        module.fail_json(msg="Can't authorize connection - " + str(e))

    # call your function here
    results = list_internet_gateways(connection, module)

    module.exit_json(result=results)


if __name__ == '__main__':
    main()
