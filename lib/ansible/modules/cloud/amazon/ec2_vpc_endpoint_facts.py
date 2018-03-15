#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: ec2_vpc_endpoint_facts
short_description: Retrieves AWS VPC endpoints details using AWS methods.
description:
  - Gets various details related to AWS VPC Endpoints
version_added: "2.4"
requirements: [ boto3 ]
options:
  query:
    description:
      - Specifies the query action to take. Services returns the supported
        AWS services that can be specified when creating an endpoint.
    required: True
    choices:
      - services
      - endpoints
  vpc_endpoint_ids:
    description:
      - Get details of specific endpoint IDs
      - Provide this value as a list
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        See U(http://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeVpcEndpoints.html)
        for possible filters.
author: Karen Cheng(@Etherdaemon)
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Simple example of listing all support AWS services for VPC endpoints
- name: List supported AWS endpoint services
  ec2_vpc_endpoint_facts:
    query: services
    region: ap-southeast-2
  register: supported_endpoint_services

- name: Get all endpoints in ap-southeast-2 region
  ec2_vpc_endpoint_facts:
    query: endpoints
    region: ap-southeast-2
  register: existing_endpoints

- name: Get all endpoints with specific filters
  ec2_vpc_endpoint_facts:
    query: endpoints
    region: ap-southeast-2
    filters:
      vpc-id:
        - vpc-12345678
        - vpc-87654321
      vpc-endpoint-state:
        - available
        - pending
  register: existing_endpoints

- name: Get details on specific endpoint
  ec2_vpc_endpoint_facts:
    query: endpoints
    region: ap-southeast-2
    vpc_endpoint_ids:
      - vpce-12345678
  register: endpoint_details
'''

RETURN = '''
service_names:
  description: AWS VPC endpoint service names
  returned: I(query) is C(services)
  type: list
  sample:
    service_names:
    - com.amazonaws.ap-southeast-2.s3
vpc_endpoints:
  description:
    - A list of endpoints that match the query. Each endpoint has the keys creation_timestamp,
      policy_document, route_table_ids, service_name, state, vpc_endpoint_id, vpc_id.
  returned: I(query) is C(endpoints)
  type: list
  sample:
    vpc_endpoints:
    - creation_timestamp: "2017-02-16T11:06:48+00:00"
      policy_document: >
        "{\"Version\":\"2012-10-17\",\"Id\":\"Policy1450910922815\",
        \"Statement\":[{\"Sid\":\"Stmt1450910920641\",\"Effect\":\"Allow\",
        \"Principal\":\"*\",\"Action\":\"s3:*\",\"Resource\":[\"arn:aws:s3:::*/*\",\"arn:aws:s3:::*\"]}]}"
      route_table_ids:
      - rtb-abcd1234
      service_name: "com.amazonaws.ap-southeast-2.s3"
      state: "available"
      vpc_endpoint_id: "vpce-abbad0d0"
      vpc_id: "vpc-1111ffff"
'''

import json

try:
    import botocore
except ImportError:
    pass  # will be picked up from imported HAS_BOTO3

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import (ec2_argument_spec, boto3_conn, get_aws_connection_info,
                                      ansible_dict_to_boto3_filter_list, HAS_BOTO3, camel_dict_to_snake_dict, AWSRetry)


def date_handler(obj):
    return obj.isoformat() if hasattr(obj, 'isoformat') else obj


@AWSRetry.exponential_backoff()
def get_supported_services(client, module):
    results = list()
    params = dict()
    while True:
        response = client.describe_vpc_endpoint_services(**params)
        results.extend(response['ServiceNames'])
        if 'NextToken' in response:
            params['NextToken'] = response['NextToken']
        else:
            break
    return dict(service_names=results)


@AWSRetry.exponential_backoff()
def get_endpoints(client, module):
    results = list()
    params = dict()
    params['Filters'] = ansible_dict_to_boto3_filter_list(module.params.get('filters'))
    if module.params.get('vpc_endpoint_ids'):
        params['VpcEndpointIds'] = module.params.get('vpc_endpoint_ids')
    while True:
        response = client.describe_vpc_endpoints(**params)
        results.extend(response['VpcEndpoints'])
        if 'NextToken' in response:
            params['NextToken'] = response['NextToken']
        else:
            break
    try:
        results = json.loads(json.dumps(results, default=date_handler))
    except Exception as e:
        module.fail_json(msg=str(e.message))
    return dict(vpc_endpoints=[camel_dict_to_snake_dict(result) for result in results])


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            query=dict(choices=['services', 'endpoints'], required=True),
            filters=dict(default={}, type='dict'),
            vpc_endpoint_ids=dict(type='list'),
        )
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    # Validate Requirements
    if not HAS_BOTO3:
        module.fail_json(msg='botocore and boto3 are required.')

    try:
        region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)
        if region:
            connection = boto3_conn(module, conn_type='client', resource='ec2', region=region, endpoint=ec2_url, **aws_connect_params)
        else:
            module.fail_json(msg="region must be specified")
    except botocore.exceptions.NoCredentialsError as e:
        module.fail_json(msg=str(e))

    invocations = {
        'services': get_supported_services,
        'endpoints': get_endpoints,
    }
    results = invocations[module.params.get('query')](connection, module)

    module.exit_json(**results)


if __name__ == '__main__':
    main()
