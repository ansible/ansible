#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: ec2_customer_gateway_info
short_description: Gather information about customer gateways in AWS
description:
    - Gather information about customer gateways in AWS
    - This module was called C(ec2_customer_gateway_facts) before Ansible 2.9. The usage did not change.
version_added: "2.5"
requirements: [ boto3 ]
author: Madhura Naniwadekar (@Madhura-CSI)
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeCustomerGateways.html) for possible filters.
  customer_gateway_ids:
    description:
      - Get details of a specific customer gateways using customer gateway ID/IDs. This value should be provided as a list.
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# # Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Gather information about all customer gateways
  ec2_customer_gateway_info:

- name: Gather information about a filtered list of customer gateways, based on tags
  ec2_customer_gateway_info:
    region: ap-southeast-2
    filters:
      "tag:Name": test-customer-gateway
      "tag:AltName": test-customer-gateway-alt
  register: cust_gw_info

- name: Gather information about a specific customer gateway by specifying customer gateway ID
  ec2_customer_gateway_info:
    region: ap-southeast-2
    customer_gateway_ids:
      - 'cgw-48841a09'
      - 'cgw-fec021ce'
  register: cust_gw_info
'''

RETURN = '''
customer_gateways:
    description: List of one or more customer gateways.
    returned: always
    type: list
    sample: [
            {
                "bgp_asn": "65000",
                "customer_gateway_id": "cgw-fec844ce",
                "customer_gateway_name": "test-customer-gw",
                "ip_address": "110.112.113.120",
                "state": "available",
                "tags": [
                    {
                        "key": "Name",
                        "value": "test-customer-gw"
                    }
                ],
                "type": "ipsec.1"
            }
        ]
'''

import json
try:
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import (ansible_dict_to_boto3_filter_list,
                                      boto3_conn, boto3_tag_list_to_ansible_dict, camel_dict_to_snake_dict,
                                      ec2_argument_spec, get_aws_connection_info)


def date_handler(obj):
    return obj.isoformat() if hasattr(obj, 'isoformat') else obj


def list_customer_gateways(connection, module):
    params = dict()

    params['Filters'] = ansible_dict_to_boto3_filter_list(module.params.get('filters'))
    params['CustomerGatewayIds'] = module.params.get('customer_gateway_ids')

    try:
        result = json.loads(json.dumps(connection.describe_customer_gateways(**params), default=date_handler))
    except (ClientError, BotoCoreError) as e:
        module.fail_json_aws(e, msg="Could not describe customer gateways")
    snaked_customer_gateways = [camel_dict_to_snake_dict(gateway) for gateway in result['CustomerGateways']]
    if snaked_customer_gateways:
        for customer_gateway in snaked_customer_gateways:
            customer_gateway['tags'] = boto3_tag_list_to_ansible_dict(customer_gateway.get('tags', []))
            customer_gateway_name = customer_gateway['tags'].get('Name')
            if customer_gateway_name:
                customer_gateway['customer_gateway_name'] = customer_gateway_name
    module.exit_json(changed=False, customer_gateways=snaked_customer_gateways)


def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            customer_gateway_ids=dict(default=[], type='list'),
            filters=dict(default={}, type='dict')
        )
    )

    module = AnsibleAWSModule(argument_spec=argument_spec,
                              mutually_exclusive=[['customer_gateway_ids', 'filters']],
                              supports_check_mode=True)
    if module._module._name == 'ec2_customer_gateway_facts':
        module._module.deprecate("The 'ec2_customer_gateway_facts' module has been renamed to 'ec2_customer_gateway_info'", version='2.13')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)

    connection = boto3_conn(module, conn_type='client', resource='ec2', region=region, endpoint=ec2_url, **aws_connect_params)

    list_customer_gateways(connection, module)


if __name__ == '__main__':
    main()
