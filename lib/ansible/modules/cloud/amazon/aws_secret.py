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
module: aws_secret
short_description: Manage secrets stored in AWS Secrets Manager.
description:
    - Create, update, and delete secrets stored in AWS Secrets Manager.
author: "Aaron Smith (@slapula)"
version_added: "2.6"
requirements: [ 'botocore>=1.10.0', 'boto3' ]
options:
  name:
    description:
    - Friendly name for the secret you are creating.
    required: true
  state:
    description:
    - Whether the secret should be exist or not.
    default: 'present'
    choices: ['present', 'absent']
  client_request_token:
    description:
    - UUID used to ensure idempotency.
    - This field is autopopulated if not provided.
  description:
    description:
    - Specifies a user-provided description of the secret.
  kms_key_id:
    description:
    - Specifies the ARN or alias of the AWS KMS customer master key (CMK) to be
      used to encrypt the `secret_string` or `secret_binary` values in the versions stored in this secret.
  secret_type:
    description:
    - Specifies the type of data that you want to encrypt.
    required: true
    choices: ['binary', 'string']
  secret:
    description:
    - Specifies string or binary data that you want to encrypt and store in the new version of the secret.
    required: true
  tags:
    description:
    - Specifies a list of user-defined tags that are attached to the secret.
  rotation_lambda:
    description:
    - Specifies the ARN of the Lambda function that can rotate the secret.
  rotation_interval:
    description:
    - Specifies the number of days between automatic scheduled rotations of the secret.
    default: 30
extends_documentation_fragment:
    - ec2
    - aws
'''


EXAMPLES = r'''
- name: Add string to AWS Secrets Manager
  aws_secret:
    name: 'test_secret_string'
    state: present
    secret_type: 'string'
    secret: "{{ super_secret_string }}"

- name: remove string from AWS Secrets Manager
  aws_secret:
    name: 'test_secret_string'
    state: absent
    secret_type: 'string'
    secret: "{{ super_secret_string }}"
'''


RETURN = r'''
secret_arn:
    description: The ARN of the secret you just created or updated.
    returned: always
    type: string
version_id:
    description: The unique identifier of the version of the secret you just created or updated.
    returned: always
    type: string
'''

import os

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import boto3_conn, get_aws_connection_info, AWSRetry
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, boto3_tag_list_to_ansible_dict

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # handled by AnsibleAWSModule


def secret_exists(client, module, result):
    if module.check_mode and module.params.get('state') == 'absent':
        return True

    try:
        response = client.list_secrets()
        while 'NextToken' in response:
            response = client.list_secrets(
                NextToken=response['NextToken']
            )
        for i in response['SecretList']:
            if i['Name'] == module.params.get('name'):
                result['secret_arn'] = i['ARN']
                return True
    except (ClientError, IndexError):
        return False

    return False


def create_secret(client, module, params, result):
    if module.check_mode:
        module.exit_json(changed=True)

    try:
        cs_response = client.create_secret(**params)
        result['secret_arn'] = cs_response['ARN']
        result['version_id'] = cs_response['VersionId']
        result['changed'] = True
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to create secret")

    if module.params.get('rotation_lambda'):
        try:
            rs_params = {}
            rs_params['SecretId'] = cs_response['ARN']
            rs_params['RotationLambdaARN'] = module.params.get('rotation_lambda')
            rs_params['RotationRules'] = {
                'AutomaticallyAfterDays': module.params.get('rotation_interval')
            }
            if module.params.get('client_request_token'):
                rs_params['ClientRequestToken'] = module.params.get('client_request_token')
            rs_response = client.rotate_secret(**rs_params)
            result['secret_arn'] = rs_response['ARN']
            result['version_id'] = rs_response['VersionId']
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Failed to add rotation policy to secret")

    return result


def update_secret(client, module, params, result):
    if module.check_mode:
        module.exit_json(changed=True)

    secret_details = client.describe_secret(
        SecretId=result['secret_arn']
    )

    secret_value = client.get_secret_value(
        SecretId=result['secret_arn']
    )

    params['SecretId'] = result['secret_arn']
    del params['Name']
    if 'Tags' in params:
        del params['Tags']

    changes_detected = []
    if 'ClientRequestToken' in params:
        if secret_details.get('ClientRequestToken') != params['ClientRequestToken']:
            changes_detected.append(True)
    if 'Description' in params:
        if secret_details.get('Description') != params['Description']:
            changes_detected.append(True)
    if 'KmsKeyId' in params:
        if secret_details.get('KmsKeyId') != params['KmsKeyId']:
            changes_detected.append(True)
    if 'SecretBinary' in params:
        if secret_value.get('SecretBinary') != params['SecretBinary']:
            changes_detected.append(True)
    if 'SecretString' in params:
        if secret_value.get('SecretString') != params['SecretString']:
            changes_detected.append(True)

    if any(changes_detected):
        try:
            response = client.update_secret(**params)
            result['VersionId'] = response['VersionId']
            result['changed'] = True
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Failed to update secret")

    rotation_updater(client, module, result, secret_details)
    tag_updater(client, module, result, secret_details)

    return result


def delete_secret(client, module, result):
    if module.check_mode:
        module.exit_json(changed=True)

    try:
        response = client.delete_secret(
            SecretId=result['secret_arn']
        )
        result['changed'] = True
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to delete secret")

    return result


def rotation_updater(client, module, result, secret_details):
    if module.params.get('rotation_lambda') and 'RotationLambdaARN' not in secret_details:
        rs_params = {}
        rs_params['SecretId'] = result['secret_arn']
        rs_params['RotationLambdaARN'] = module.params.get('rotation_lambda')
        rs_params['RotationRules'] = {
            'AutomaticallyAfterDays': module.params.get('rotation_interval')
        }
        if module.params.get('client_request_token'):
            rs_params['ClientRequestToken'] = module.params.get('client_request_token')

        try:
            rs_response = client.rotate_secret(**rs_params)
            result['secret_arn'] = rs_response['ARN']
            result['version_id'] = rs_response['VersionId']
            result['changed'] = True
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Failed to add rotation policy to secret")

    if module.params.get('rotation_lambda') and 'RotationLambdaARN' in secret_details:
        changes_detected = []
        if secret_details.get('RotationLambdaARN') != module.params.get('rotation_lambda'):
            changes_detected.append(True)
        if secret_details.get('RotationRules').get('AutomaticallyAfterDays') != module.params.get('rotation_interval'):
            changes_detected.append(True)

        if any(changes_detected):
            rs_params = {}
            rs_params['SecretId'] = result['secret_arn']
            rs_params['RotationLambdaARN'] = module.params.get('rotation_lambda')
            rs_params['RotationRules'] = {
                'AutomaticallyAfterDays': module.params.get('rotation_interval')
            }
            if module.params.get('client_request_token'):
                rs_params['ClientRequestToken'] = module.params.get('client_request_token')

            try:
                rs_response = client.rotate_secret(**rs_params)
                result['secret_arn'] = rs_response['ARN']
                result['version_id'] = rs_response['VersionId']
                result['changed'] = True
            except (BotoCoreError, ClientError) as e:
                module.fail_json_aws(e, msg="Failed to add rotation policy to secret")

    if not module.params.get('rotation_lambda') and 'RotationLambdaARN' in secret_details:
        try:
            rs_response = client.cancel_rotate_secret(
                SecretId=result['secret_arn']
            )
            result['changed'] = True
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Failed to remove rotation policy from secret")


def tag_updater(client, module, result, secret_details):
    if module.params.get('tags') and 'Tags' not in secret_details:
        tag_params = {}
        tag_params['SecretId'] = result['secret_arn']
        tag_params['Tags'] = module.params.get('tags')

        try:
            rs_response = client.tag_resource(**tag_params)
            result['changed'] = True
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Failed to add tag(s) to secret")

    if module.params.get('tags') and 'Tags' in secret_details:
        changes_detected = []
        if secret_details.get('Tags') != module.params.get('tags'):
            changes_detected.append(True)

        if any(changes_detected):
            tag_params = {}
            tag_params['SecretId'] = result['secret_arn']

            tags_to_add = list(set(module.params.get('tags').items()).difference(set(secret_details.get('Tags').items())))
            tags_to_remove = list(set(secret_details.get('Tags').items()).difference(set(module.params.get('tags').items())))

            if len(tags_to_add) > 0:
                tag_params['Tags'] = dict(tags_to_add)
                try:
                    tag_response = client.tag_resource(**tag_params)
                    result['changed'] = True
                except (BotoCoreError, ClientError) as e:
                    module.fail_json_aws(e, msg="Failed to add tag(s) to secret")

            if len(tags_to_remove) > 0:
                tag_params['Tags'] = dict(tags_to_remove)
                try:
                    tag_response = client.untag_resource(**tag_params)
                    result['changed'] = True
                except (BotoCoreError, ClientError) as e:
                    module.fail_json_aws(e, msg="Failed to remove tag(s) from secret")

    if not module.params.get('tags') and 'Tags' in secret_details:
        try:
            tag_response = client.untag_resource(
                SecretId=result['secret_arn'],
                TagKeys=list(set().union(*(d.keys() for d in list(secret_details['Tags']))))
            )
            result['changed'] = True
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Failed to remove tag(s) from secret")


def main():
    module = AnsibleAWSModule(
        argument_spec={
            'name': dict(type='str', required=True),
            'state': dict(type='str', choices=['present', 'absent'], default='present'),
            'client_request_token': dict(type='str'),
            'description': dict(type='str'),
            'kms_key_id': dict(type='str'),
            'secret_type': dict(type='str', choices=['binary', 'string'], required=True),
            'secret': dict(type='str', required=True),
            'tags': dict(type='list'),
            'rotation_lambda': dict(type='str'),
            'rotation_interval': dict(type='int', default=30),
        },
        supports_check_mode=True,
    )

    result = {
        'changed': False
    }

    desired_state = module.params.get('state')

    params = {}
    params['Name'] = module.params.get('name')
    if module.params.get('client_request_token'):
        params['ClientRequestToken'] = module.params.get('client_request_token')
    if module.params.get('description'):
        params['Description'] = module.params.get('description')
    if module.params.get('kms_key_id'):
        params['KmsKeyId'] = module.params.get('kms_key_id')
    if module.params.get('secret_type') == 'binary':
        params['SecretBinary'] = module.params.get('secret')
    if module.params.get('secret_type') == 'string':
        params['SecretString'] = module.params.get('secret')
    if module.params.get('tags'):
        params['Tags'] = module.params.get('tags')

    client = module.client('secretsmanager')

    secret_status = secret_exists(client, module, result)

    if desired_state == 'present':
        if not secret_status:
            create_secret(client, module, params, result)
        if secret_status:
            update_secret(client, module, params, result)

    if desired_state == 'absent':
        if secret_status:
            delete_secret(client, module, result)

    module.exit_json(changed=result['changed'], output=result)


if __name__ == '__main__':
    main()
