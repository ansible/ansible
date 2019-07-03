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
module: aws_api_gateway_domain
short_description: Manage AWS API Gateway custom domains
description:
     - Allows for the management of API Gateway custom domains. To have nice domain names for your API GW Rest APIs.
     - AWS API Gateway custom domain setups use CloudFront behind the scenenes. So you will get a CloudFront distribution as a result, configured to be aliased with your domain.
version_added: '2.9'
requirements: [ boto3 ]
options:
  domain_name:
    description:
      - Domain name you want to use for your API GW deployment
    required: true
  certificate_arn:
    description:
      - AWS Certificate Manger (ACM) TLS certificate ARN.
  security_policy:
    description:
      - Set allowed TLS versions through AWS defined policies. Currently only TLS_1_0 and TLS_1_2 are available.
    default: TLS_1_2
    choices: ['TLS_1_0', 'TLS_1_2']
  endpoint_type:
    description:
      - API endpoint configuration for domain. Use EDGE for edge-optimized endpoint, or use REGIONAL or PRIVATE
    default: EDGE
    choices: ['EDGE', 'REGIONAL', 'PRIVATE']
  state:
    description:
      - Create or delete custom domain setup
    default: present
    choices: [ 'present', 'absent' ]

author:
    - 'Stefan Horning (@stefanhorning)'
extends_documentation_fragment:
    - aws
    - ec2
notes:
   - Does not create a DNS entry on Route53, for that use the route53 module.
'''

EXAMPLES = '''
- name: Setup endpoint for a custom domain for your API Gateway HTTP API
  aws_api_gateway_domain:
    domain_name: myapi.foobar.com
    certificate_arn: 'arn:aws:acm:us-east-1:1231123123:certificate/8bd89412-abc123-xxxxx'
    security_policy: TLS_1_0
    endpoint_type: EDGE
    state: present
  register: api_gw_domain_result

- name: Create a DNS record for your custom domain on route 53 (using route53 module)
  route53
    record: myapi.foobar.com
    value: "{{ api_gw_domain_result.domain_name }}"
    type: A
    alias: true
    zone: foobar.com
    alias_hosted_zone_id: "{{ api_gw_domain_result.distribution_hosted_zone_id }}"
    command: create
'''

RETURN = '''
repsonse:
  description: The data returned by create_domain_name (or update and delete) method in boto3
  returned: success
  type: dict
  sample:
    {
        domain_name: mydomain.com,
        certificate_arn: 'arn:aws:acm:xxxxxx',
        distribution_domain_name: mydomain.com
        distribution_hosted_zone_id: abc123123,
        endpoint_configuration: { types: ['EDGE'] },
        domain_name_status: 'AVAILABLE',
        security_policy: TLS_1_2,
        tags: {}
    }
'''

try:
    import botocore
except ImportError:
    # HAS_BOTOCORE taken care of in AnsibleAWSModule
    pass

import traceback
from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import (AWSRetry, camel_dict_to_snake_dict)


def get_domain(module, client):
    domain_name = module.params.get('domain_name')
    result = {}
    try:
        result['domain_name']   = get_domain_name(client, domain_name)
        result['path_mapping']  = get_domain_mapping(client, domain_name)
    except (botocore.exceptions.ClientError, botocore.exceptions.EndpointConnectionError) as e:
        module.fail_json_aws(e, msg="getting API GW domain")

    return result


def create_domain(module, client):
    args = module.params
    try:
        res = create_domain_name(client, args)
    except (botocore.exceptions.ClientError, botocore.exceptions.EndpointConnectionError) as e:
        module.fail_json_aws(e, msg="creating API GW domain")
    return res


def update_domain(module, client):
    args = module.params
    try:
        res = update_domain_name(client, args)
    except (botocore.exceptions.ClientError, botocore.exceptions.EndpointConnectionError) as e:
        module.fail_json_aws(e, msg="updating API GW domain")
    return res


def delete_domain(module, client):
    domain_name = module.params.get('domain_name')
    try:
        res = delete_domain_name(client, domain_name)
    except (botocore.exceptions.ClientError, botocore.exceptions.EndpointConnectionError) as e:
        module.fail_json_aws(e, msg="deleting API GW domain")
    return res


retry_params = {"tries": 10, "delay": 5, "backoff": 1.2}


@AWSRetry.backoff(**retry_params)
def get_domain_name(client, domain_name):
    return client.get_domain_name(domainName=domain_name)


@AWSRetry.backoff(**retry_params)
def get_domain_mapping(client, domain_name):
    return client.get_base_path_mappings(domainName=domain_name, limit=200)


@AWSRetry.backoff(**retry_params)
def create_domain_name(client, **args):
    return client.create_domain_name(args)


@AWSRetry.backoff(**retry_params)
def update_domain_name(client, **args):
    return client.update_domain_name(args)


@AWSRetry.backoff(**retry_params)
def delete_domain_name(client, domain_name):
    return client.delete_domain_name(domainName=domain_name)


def main():
    argument_spec=dict(
        domain_name=dict(type='str', required=True),
        certificate_arn=dict(type='str', required=True),
        security_policy=dict(type='str', default='TLS_1_2', choices=['TLS_1_0', 'TLS_1_2']),
        endpoint_type=dict(type='str', default='EDGE', choices=['EDGE', 'REGIONAL', 'PRIVATE']),
        domain_mapping=dict(type='list', required=True)
        state=dict(type='str', default='present', choices=['present', 'absent'])
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=False,
    )

    client = module.client('apigateway')

    state = module.params.get('state')
    changed = False

    # TODO: add base path mapping creation/deletion
    if state == "present":
        existing_domain = get_domain(module, client)
        # if domain exists use update

        result = create_domain(module, client)
    if state == "absent":
        result = delete_domain(module, client)

    exit_args = { "changed": changed }

    if result is not None:
        exit_args['response'] = camel_dict_to_snake_dict(result)

    module.exit_json(**exit_args)


if __name__ == '__main__':
    main()
