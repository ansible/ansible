#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ec2_vpc_igw_facts
short_description: Gather facts about internet gateways in AWS
description:
    - Gather facts about internet gateways in AWS.
version_added: "2.3"
requirements: [ boto3 ]
author: "Nick Aslanidis (@naslanidis)"
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        See U(http://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeInternetGateways.html) for possible filters.
  internet_gateway_ids:
    description:
      - Get details of specific Internet Gateway ID. Provide this value as a list.
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

try:
    import botocore
except ImportError:
    pass  # will be captured by imported HAS_BOTO3

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import (ec2_argument_spec, get_aws_connection_info, boto3_conn,
                                      camel_dict_to_snake_dict, ansible_dict_to_boto3_filter_list, HAS_BOTO3)


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

    return [camel_dict_to_snake_dict(get_internet_gateway_info(igw))
            for igw in all_internet_gateways['InternetGateways']]


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

    module.exit_json(internet_gateways=results)


if __name__ == '__main__':
    main()
