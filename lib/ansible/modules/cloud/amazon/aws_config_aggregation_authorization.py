#!/usr/bin/python

# Copyright: (c) 2018, Aaron Smith <ajsmith10381@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: aws_config_aggregation_authorization
short_description: Manage cross-account AWS Config authorizations
description:
    - Module manages AWS Config resources
version_added: "2.6"
requirements: [ 'botocore', 'boto3' ]
author:
    - "Aaron Smith (@slapula)"
options:
  state:
    description:
    - Whether the Config rule should be present or absent.
    default: present
    choices: ['present', 'absent']
  authorized_account_id:
    description:
    - The 12-digit account ID of the account authorized to aggregate data.
  authorized_aws_region:
    description:
    - The region authorized to collect aggregated data.
extends_documentation_fragment:
  - aws
  - ec2
'''

EXAMPLES = r'''
- name: Get current account ID
  aws_caller_facts:
  register: whoami
- aws_config_aggregation_authorization:
    state: present
    authorized_account_id: '{{ whoami.account }}'
    authorzed_aws_region: us-east-1
'''

RETURN = r'''#'''


try:
    import botocore
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # handled by AnsibleAWSModule

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import boto3_conn, get_aws_connection_info, AWSRetry
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, boto3_tag_list_to_ansible_dict


def resource_exists(client, module, params):
    try:
        current_authorizations = client.describe_aggregation_authorizations()['AggregationAuthorizations']
        authorization_exists = next(
            (item for item in current_authorizations if item["AuthorizedAccountId"] == params['AuthorizedAccountId']),
            None
        )
        if authorization_exists:
            return True
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError):
        return False


def create_resource(client, module, params, result):
    try:
        response = client.put_aggregation_authorization(
            AuthorizedAccountId=params['AuthorizedAccountId'],
            AuthorizedAwsRegion=params['AuthorizedAwsRegion']
        )
        result['changed'] = True
        return result
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't create AWS Aggregation authorization")


def update_resource(client, module, params, result):
    current_authorizations = client.describe_aggregation_authorizations()['AggregationAuthorizations']
    current_params = next(
        (item for item in current_authorizations if item["AuthorizedAccountId"] == params['AuthorizedAccountId']),
        None
    )

    del current_params['AggregationAuthorizationArn']
    del current_params['CreationTime']

    if params != current_params:
        try:
            response = client.put_aggregation_authorization(
                AuthorizedAccountId=params['AuthorizedAccountId'],
                AuthorizedAwsRegion=params['AuthorizedAwsRegion']
            )
            result['changed'] = True
            return result
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't create AWS Aggregation authorization")


def delete_resource(client, module, params, result):
    try:
        response = client.delete_aggregation_authorization(
            AuthorizedAccountId=params['AuthorizedAccountId'],
            AuthorizedAwsRegion=params['AuthorizedAwsRegion']
        )
        result['changed'] = True
        return result
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't delete AWS Aggregation authorization")


def main():
    module = AnsibleAWSModule(
        argument_spec={
            'state': dict(type='str', choices=['present', 'absent'], default='present'),
            'authorized_account_id': dict(type='str', required=True),
            'authorized_aws_region': dict(type='str', required=True),
        },
        supports_check_mode=False,
    )

    result = {'changed': False}

    params = {
        'AuthorizedAccountId': module.params.get('authorized_account_id'),
        'AuthorizedAwsRegion': module.params.get('authorized_aws_region'),
    }

    client = module.client('config', retry_decorator=AWSRetry.jittered_backoff())
    resource_status = resource_exists(client, module, params)

    if module.params.get('state') == 'present':
        if not resource_status:
            create_resource(client, module, params, result)
        else:
            update_resource(client, module, params, result)

    if module.params.get('state') == 'absent':
        if resource_status:
            delete_resource(client, module, params, result)

    module.exit_json(changed=result['changed'])


if __name__ == '__main__':
    main()
