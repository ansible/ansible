#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: aws_api_gateway_facts
version_added: '2.9.0'
short_description: Gather facts about API Gateways
description: Gather facts about API Gateways
author:
  - Nao Morikawa (@cahlchang)
requirements: [ boto3 ]

extends_documentation_fragment:
    - aws
    - ec2
options:
  api_id:
    description:
      - The Amazon API Gateway ID.
    required: false
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: gather facts about all API Gateway
  aws_api_gateway_facts:
    profile: YOUR_PROFILE

- name: gather facts about an API Gateway using apigateway-id.
  aws_api_gateway_facts:
    api_id: xxxxxxxxxx
'''

RETURN = '''
apis:
  description: a list of api-gateway
  returned: always
  type: complex
  contains:
    id:
      description: The API Gateway unique id.
      returned: always
      type: str
      sample: xxxxxxxxxx
    name:
      description: The API Gateway name.
      returned: always
      type: str
      sample: Name of the API Gateway you named.
    version:
      description: API Gateway version
      returned: always
      type: str
      sample: Versuib of the API Gateway.
    creation_date:
      description: The date and time the API Gateway was created.
      returned: always
      type: str
      sample: 2018-12-08T13:30:58Z

'''

import traceback

try:
    import boto3
    from botocore.exceptions import ClientError, BotoCoreError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False
from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import (boto3_conn, ec2_argument_spec, get_aws_connection_info, camel_dict_to_snake_dict)


def list_api_gateway(client, module, api_id):

    exit_args = {"changed": False}

    try:
        if api_id:
            result = client.get_rest_api(restApiId=api_id)
            del result['ResponseMetadata']
            api_result = {'items': [result]}
        else:
            api_result = client.get_rest_apis()
    except (ClientError, BotoCoreError) as err:
        module.fail_json(msg=err.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(err.response))

    apis = {}
    for api in api_result['items']:
        apis[api['id']] = api

    apis = camel_dict_to_snake_dict(apis)
    exit_args['apis'] = apis
    module.exit_json(**exit_args)


def main():
    argument_spec = dict(
        api_id=dict(type='str', required=False)
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    api_id = module.params.get('api_id')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)

    if region:
        client = boto3_conn(module, conn_type='client', resource='apigateway', region=region, endpoint=ec2_url, **aws_connect_params)
    else:
        module.fail_json(msg="region must be specified")

    list_api_gateway(client, module, api_id)


if __name__ == '__main__':
    main()
