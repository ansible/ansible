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
module: ec2_vpc_endpoint_facts
short_description: Retrieves AWS VPC endpoints details using AWS methods.
description:
  - Gets various details related to AWS VPC Endpoints
version_added: "2.2"
requirements: [ boto3 ]
options:
  query:
    description:
      - Specifies the query action to take. Services returns the supported
        AWS services that can be specified when creating an endpoint.
    required: True
    choices: [
            'services',
            'endpoints'
            ]
  max_items:
    description:
      - Maximum number of items to return. AWS maximum of 1000
    required: false
  next_token:
    description:
      - If the result exceeds the max_items or the AWS maximum of 1000 you
        can specify the token to get the next set of results
    required: false
  vpc_endpoint_ids:
    description:
      - Get details of specific endpoint IDs
      - Provide this value as a list
    required: false
    default: None
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        See U(http://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeVpcEndpoints.html)
        for possible filters.
    required: false
    default: None
author: Karen Cheng(@Etherdaemon)
extends_documentation_fragment: aws
'''

EXAMPLES = '''
# Simple example of listing all support AWS services
  for VPC endpoints
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
      vpc-id: [vpc-12345678, vpc-87654321]
      vpc-endpoint-state: ['available','pending']
    max_items: 200
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
result:
  description: The result of the describe.
  returned: success
  type: dictionary or a list of dictionaries
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


def get_supported_services(client, module):
    params = dict()
    if module.params.get('max_items'):
        params['MaxResults'] = module.params.get('max_items')
    if module.params.get('next_token'):
        params['NextToken'] = module.params.get('next_token')

    result = client.describe_vpc_endpoint_services(**params)
    return result


def get_endpoints(client, module):
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
    if module.params.get('max_items'):
        params['MaxResults'] = module.params.get('max_items')
    if module.params.get('next_token'):
        params['NextToken'] = module.params.get('next_token')
    if module.params.get('vpc_endpoint_ids'):
        params['VpcEndpointIds'] = module.params.get('vpc_endpoint_ids')

    try:
        result = json.loads(json.dumps(client.describe_vpc_endpoints(**params), default=date_handler))
    except Exception as e:
        module.fail_json(msg=str(e.message))

    return result


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        query=dict(choices=[
            'services',
            'endpoints',
        ], required=True),
        max_items=dict(type='int'),
        next_token=dict(),
        filters=dict(default=None, type='dict'),
        vpc_endpoint_ids=dict(default=None, type='list'),
        )
    )

    module = AnsibleModule(argument_spec=argument_spec,)

    # Validate Requirements
    if not HAS_BOTO3:
        module.fail_json(msg='json and botocore/boto3 is required.')

    try:
        region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)
        if region:
            connection = boto3_conn(module, conn_type='client', resource='ec2', region=region, endpoint=ec2_url, **aws_connect_params)
        else:
            module.fail_json(msg="region must be specified")
    except botocore.exceptions.NoCredentialsError, e:
        module.fail_json(msg=str(e))

    invocations = {
        'services': get_supported_services,
        'endpoints': get_endpoints,
    }
    results = invocations[module.params.get('query')](ec2, module)

    module.exit_json(result=results)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
