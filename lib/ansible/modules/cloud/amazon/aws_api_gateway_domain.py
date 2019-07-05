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
     - AWS API Gateway custom domain setups use CloudFront behind the scenenes.
       So you will get a CloudFront distribution as a result, configured to be aliased with your domain.
version_added: '2.9'
requirements: [ boto3 ]
author:
    - 'Stefan Horning (@stefanhorning)'
options:
  domain_name:
    description:
      - Domain name you want to use for your API GW deployment
    required: true
    type: str
  certificate_arn:
    description:
      - AWS Certificate Manger (ACM) TLS certificate ARN.
    type: str
  security_policy:
    description:
      - Set allowed TLS versions through AWS defined policies. Currently only TLS_1_0 and TLS_1_2 are available.
      - Can only be set with botocore 1.12.175 or newer. On older boto versions this flag will automatically be ignored
    default: TLS_1_2
    choices: ['TLS_1_0', 'TLS_1_2']
    type: str
  endpoint_type:
    description:
      - API endpoint configuration for domain. Use EDGE for edge-optimized endpoint, or use REGIONAL or PRIVATE
    default: EDGE
    choices: ['EDGE', 'REGIONAL', 'PRIVATE']
    type: str
  domain_mappings:
    description:
      - Map your domain base paths to your API GW REST APIs, you previously created. Use provide ID of the API setup and the release stage.
      - "domain_mappings should be a list of dictionaries containing three keys: base_path, rest_api_id and stage."
      - "Example: I([{ base_path: v1, rest_api_id: abc123, stage: production }])"
      - if you want base path to be just I(/) omit the param completely or set it to empty string.
    required: true
    type: list
  state:
    description:
      - Create or delete custom domain setup
    default: present
    choices: [ 'present', 'absent' ]
    type: str
extends_documentation_fragment:
    - aws
    - ec2
notes:
   - Does not create a DNS entry on Route53, for that use the route53 module.
   - Only supports TLS certificates from AWS ACM that can just be referenced by the ARN, while the AWS API still offers (deprecated)
     options to add own Certificates.
'''

EXAMPLES = '''
- name: Setup endpoint for a custom domain for your API Gateway HTTP API
  aws_api_gateway_domain:
    domain_name: myapi.foobar.com
    certificate_arn: 'arn:aws:acm:us-east-1:1231123123:certificate/8bd89412-abc123-xxxxx'
    security_policy: TLS_1_0
    endpoint_type: EDGE
    domain_mappings:
        - { rest_api_id: abc123, stage: production }
    state: present
  register: api_gw_domain_result

- name: Create a DNS record for your custom domain on route 53 (using route53 module)
  route53:
    record: myapi.foobar.com
    value: "{{ api_gw_domain_result.response.domain.distribution_domain_name }}"
    type: A
    alias: true
    zone: foobar.com
    alias_hosted_zone_id: "{{ api_gw_domain_result.response.domain.distribution_hosted_zone_id }}"
    command: create
'''

RETURN = '''
response:
  description: The data returned by create_domain_name (or update and delete) nad create_base_path_mapping methods in boto3
  returned: success
  type: dict
  sample:
    domain:
        {
            domain_name: mydomain.com,
            certificate_arn: 'arn:aws:acm:xxxxxx',
            distribution_domain_name: xxxx.cloudfront.net,
            distribution_hosted_zone_id: ABC123123,
            endpoint_configuration: { types: ['EDGE'] },
            domain_name_status: 'AVAILABLE',
            security_policy: TLS_1_2,
            tags: {}
        }
    path_mappings: [
        { base_path: '(empty)', rest_api_id: 'abcd123', stage: 'production' }
    ]
'''

try:
    import botocore
except ImportError:
    # HAS_BOTOCORE taken care of in AnsibleAWSModule
    pass

import copy
import traceback

from ansible.module_utils.aws.core import AnsibleAWSModule, is_boto3_error_code
from ansible.module_utils.ec2 import (AWSRetry, camel_dict_to_snake_dict, snake_dict_to_camel_dict)


def get_domain(module, client):
    domain_name = module.params.get('domain_name')
    result = {}
    try:
        result['domain'] = get_domain_name(client, domain_name)
        result['path_mappings'] = get_domain_mappings(client, domain_name)
    except is_boto3_error_code('NotFoundException'):
        return None
    except (botocore.exceptions.ClientError, botocore.exceptions.EndpointConnectionError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="getting API GW domain")
    return camel_dict_to_snake_dict(result)


def create_domain(module, client):
    path_mappings = module.params.get('domain_mappings', [])
    domain_name = module.params.get('domain_name')
    result = {'domain': {}, 'path_mappings': []}

    try:
        result['domain'] = create_domain_name(
            module,
            client,
            domain_name,
            module.params.get('certificate_arn'),
            module.params.get('endpoint_type'),
            module.params.get('security_policy')
        )

        for mapping in path_mappings:
            base_path = mapping.get('base_path', '')
            rest_api_id = mapping.get('rest_api_id')
            stage = mapping.get('stage')
            if rest_api_id is None or stage is None:
                module.fail_json('Every domain mapping needs a rest_api_id and stage name')

            result['path_mappings'].append(add_domain_mapping(client, domain_name, base_path, rest_api_id, stage))

    except (botocore.exceptions.ClientError, botocore.exceptions.EndpointConnectionError) as e:
        module.fail_json_aws(e, msg="creating API GW domain")
    return camel_dict_to_snake_dict(result)


def update_domain(module, client, existing_domain):
    domain_name = module.params.get('domain_name')
    result = existing_domain
    result['updated'] = False

    domain = existing_domain.get('domain')
    # Compare only relevant set of domain arguments.
    # As get_domain_name gathers all kind of state information that can't be set anyways.
    # Also this module doesn't support custom TLS cert setup params as they are kind of deprecated already and would increase complexity.
    existing_domain_settings = {
        'certificate_arn': domain.get('certificate_arn'),
        'security_policy': domain.get('security_policy'),
        'endpoint_type': domain.get('endpoint_configuration').get('types')[0]
    }
    specified_domain_settings = {
        'certificate_arn': module.params.get('certificate_arn'),
        'security_policy': module.params.get('security_policy'),
        'endpoint_type': module.params.get('endpoint_type')
    }

    if specified_domain_settings != existing_domain_settings:
        try:
            result['domain'] = update_domain_name(client, domain_name, **snake_dict_to_camel_dict(specified_domain_settings))
            result['updated'] = True
        except (botocore.exceptions.ClientError, botocore.exceptions.EndpointConnectionError) as e:
            module.fail_json_aws(e, msg="updating API GW domain")

    existing_mappings = copy.deepcopy(existing_domain.get('path_mappings', []))
    # Cleanout `base_path: "(none)"` elements from dicts as those won't match with specified mappings
    for mapping in existing_mappings:
        if mapping.get('base_path', 'missing') == '(none)':
            mapping.pop('base_path')

    specified_mappings = copy.deepcopy(module.params.get('domain_mappings', []))
    # Cleanout `base_path: ""` elements from dicts as those won't match with existing mappings
    for mapping in specified_mappings:
        if mapping.get('base_path', 'missing') == '':
            mapping.pop('base_path')

    if specified_mappings != existing_mappings:
        try:
            # When lists missmatch delete all existing mappings before adding new ones as specified
            for mapping in existing_domain.get('path_mappings', []):
                delete_domain_mapping(client, domain_name, mapping['base_path'])
            for mapping in module.params.get('domain_mappings', []):
                result['path_mappings'] = add_domain_mapping(
                    client, domain_name, mapping.get('base_path', ''), mapping.get('rest_api_id'), mapping.get('stage')
                )
                result['updated'] = True
        except (botocore.exceptions.ClientError, botocore.exceptions.EndpointConnectionError) as e:
            module.fail_json_aws(e, msg="updating API GW domain mapping")

    return camel_dict_to_snake_dict(result)


def delete_domain(module, client):
    domain_name = module.params.get('domain_name')
    try:
        result = delete_domain_name(client, domain_name)
    except (botocore.exceptions.ClientError, botocore.exceptions.EndpointConnectionError) as e:
        module.fail_json_aws(e, msg="deleting API GW domain")
    return camel_dict_to_snake_dict(result)


retry_params = {"tries": 10, "delay": 5, "backoff": 1.2}


@AWSRetry.backoff(**retry_params)
def get_domain_name(client, domain_name):
    return client.get_domain_name(domainName=domain_name)


@AWSRetry.backoff(**retry_params)
def get_domain_mappings(client, domain_name):
    return client.get_base_path_mappings(domainName=domain_name, limit=200).get('items', [])


@AWSRetry.backoff(**retry_params)
def create_domain_name(module, client, domain_name, certificate_arn, endpoint_type, security_policy):
    endpoint_configuration = {'types': [endpoint_type]}
    if module.botocore_at_least('1.12.175'):
        # The securityPolicy param was only added in botocore 1.12.175, hence we don't set it if older version is installed.
        # See diff at https://github.com/boto/botocore/compare/1.12.174...1.12.175
        return client.create_domain_name(
            domainName=domain_name,
            certificateArn=certificate_arn,
            endpointConfiguration=endpoint_configuration,
            securityPolicy=security_policy
        )
    else:
        return client.create_domain_name(domainName=domain_name, certificateArn=certificate_arn, endpointConfiguration=endpoint_configuration)


@AWSRetry.backoff(**retry_params)
def add_domain_mapping(client, domain_name, base_path, rest_api_id, stage):
    return client.create_base_path_mapping(domainName=domain_name, basePath=base_path, restApiId=rest_api_id, stage=stage)


@AWSRetry.backoff(**retry_params)
def update_domain_name(client, domain_name, **kwargs):
    patch_operations = []

    for key, value in kwargs.items():
        path = "/" + key
        if key == "endpointType":
            continue
        patch_operations.append({"op": "replace", "path": path, "value": value})

    return client.update_domain_name(domainName=domain_name, patchOperations=patch_operations)


@AWSRetry.backoff(**retry_params)
def delete_domain_name(client, domain_name):
    return client.delete_domain_name(domainName=domain_name)


@AWSRetry.backoff(**retry_params)
def delete_domain_mapping(client, domain_name, base_path):
    return client.delete_base_path_mapping(domainName=domain_name, basePath=base_path)


def main():
    argument_spec = dict(
        domain_name=dict(type='str', required=True),
        certificate_arn=dict(type='str', required=True),
        security_policy=dict(type='str', default='TLS_1_2', choices=['TLS_1_0', 'TLS_1_2']),
        endpoint_type=dict(type='str', default='EDGE', choices=['EDGE', 'REGIONAL', 'PRIVATE']),
        domain_mappings=dict(type='list', required=True),
        state=dict(type='str', default='present', choices=['present', 'absent'])
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=False
    )

    client = module.client('apigateway')

    state = module.params.get('state')
    changed = False

    if state == "present":
        existing_domain = get_domain(module, client)
        if existing_domain is not None:
            result = update_domain(module, client, existing_domain)
            changed = result['updated']
        else:
            result = create_domain(module, client)
            changed = True
    if state == "absent":
        result = delete_domain(module, client)
        changed = True

    exit_args = {"changed": changed}

    if result is not None:
        exit_args['response'] = result

    module.exit_json(**exit_args)


if __name__ == '__main__':
    main()
