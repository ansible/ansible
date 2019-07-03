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
version_added: '2.9'
requirements: [ boto3 ]
options:
  state:
    description:
      - NOT IMPLEMENTED Create or delete API - currently we always create.
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
- name: Create DNS setup for API GW Rest API
  aws_api_gateway_domain:
    domain_name: api.foobar.com
    certificate_arn: 'arn:aws:acm:us-east-1:1231123123:certificate/8bd89412-abc123-xxxxx'
    endpoint_configuration: {}
    state: present

'''

RETURN = '''
output:
  description: the data returned by put_restapi in boto3
  returned: success
  type: dict
  sample:
    'data':
      {
          "id": "abc123321cba",
          "name": "MY REST API",
          "createdDate": 1484233401
      }
'''

import json

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
    try:
        res = get_domain_name(client, domain_name)
    except (botocore.exceptions.ClientError, botocore.exceptions.EndpointConnectionError) as e:
        module.fail_json_aws(e, msg="getting API domain")
    return res


def create_domain(module, client):
    args = module.params
    try:
        res = create_domain_name(client, args)
    except (botocore.exceptions.ClientError, botocore.exceptions.EndpointConnectionError) as e:
        module.fail_json_aws(e, msg="creating API domain")
    return res


def update_domain(module, client):
    args = module.params
    try:
        res = update_domain_name(client, args)
    except (botocore.exceptions.ClientError, botocore.exceptions.EndpointConnectionError) as e:
        module.fail_json_aws(e, msg="updating API domain")
    return res


def delete_domain(module, client):
    domain_name = module.params.get('domain_name')
    try:
        res = delete_domain_name(client, domain_name)
    except (botocore.exceptions.ClientError, botocore.exceptions.EndpointConnectionError) as e:
        module.fail_json_aws(e, msg="deleting API domain")
    return res


retry_params = {"tries": 10, "delay": 5, "backoff": 1.2}


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
        certificate_name=dict(type='str'),
        certificate_arn=dict(type='str'),
        security_policy=dict(type='str', default='TLS_1_2', choices=['TLS_1_0', 'TLS_1_2']),
        endpoint_type=dict(type='str', default='EDGE', choices=['EDGE', 'REGIONAL', 'PRIVATE']),
        state=dict(type='str', default='present', choices=['present', 'absent'])
    )

    mutually_exclusive = [['certificate_arn', 'certificate_name']]

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=False,
        mutually_exclusive=mutually_exclusive,
    )

    client = module.client('apigateway')

    state = module.params.get('state')
    changed = False

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
