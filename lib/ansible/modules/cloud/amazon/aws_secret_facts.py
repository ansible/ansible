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
module: aws_secret_facts
short_description: Access facts for secrets stored in AWS Secrets Manager.
description:
    - Access facts for secrets stored in AWS Secrets Manager.
author: "Aaron Smith (@slapula)"
version_added: "2.8"
requirements: [ 'botocore>=1.10.0', 'boto3' ]
options:
  name:
    description:
    - Friendly name of the secret you are looking up.
  prefix:
    description:
    - Common string identifier that has been added to the beginning of a secret name.
  suffix:
    description:
    - Common string identifier that has been added to the end of a secret name.
  regex:
    description:
    - Regex pattern that can be used to identify a specific secret or set of secrets.
notes:
  - Each lookup option is mutually exclusive.
  - Leaving all parameters empty will cause the module to look up the information of all secrets stored
    in Secrets Manager.
extends_documentation_fragment:
    - ec2
    - aws
'''


EXAMPLES = r'''
- name: Get facts for all secrets
  aws_secret_facts:
  register: all_secrets

- name: Get facts for specific secret
  aws_secret_facts:
    name: 'example_secret'
  register: specific_secret

- name: Get facts for specific prefix of secrets
  aws_secret_facts:
    prefix: 'example_'
  register: specific_prefix_set
'''


RETURN = r'''
arn:
    description: The Amazon Resource Name (ARN) of the secret.
    returned: always
    type: string
name:
    description: The friendly name of the secret.
    returned: always
    type: string
description:
    description: The user-provided description of the secret.
    returned: always
    type: string
kms_key_id:
    description:
      - The ARN or alias of the AWS KMS customer master key (CMK) that's used to encrypt the SecretString and SecretBinary fields in each
        version of the secret.  If you don't provide a key, then Secrets Manager defaults to encrypting the secret fields with the default
        KMS CMK (the one named awssecretsmanager ) for this account.
    returned: always
    type: string
rotation_enabled:
    description: Indicated whether automatic, scheduled rotation is enabled for this secret.
    returned: always
    type: boolean
rotation_lambda_arn:
    description:
      - The ARN of an AWS Lambda function that's invoked by Secrets Manager to rotate and expire the secret either automatically per
        the schedule or manually by a call to RotateSecret .
    returned: always
    type: string
rotation_rules:
    description: A structure that defines the rotation configuration for the secret.
    returned: always
    type: dict
automatically_after_days:
    description: Specifies the number of days between automatic scheduled rotations of the secret.
    returned: always
    type: int
last_rotate_date:
    description: The last date and time that the rotation process for this secret was invoked.
    returned: always
    type: string
last_changed_date:
    description: The last date and time that this secret was modified in any way.
    returned: always
    type: string
last_access_date:
    description: The last date that this secret was accessed. This value is truncated to midnight of the date and therefore shows only the date, not the time.
    returned: always
    type: string
deleted_date:
    description:
      - The date and time on which this secret was deleted. Not present on active secrets. The secret can be recovered until the number of days
        in the recovery window has passed, as specified in the RecoveryWindowInDays parameter of the DeleteSecret operation.
    returned: always
    type: string
tags:
    description: The list of user-defined tags that are associated with the secret.
    returned: always
    type: list
secret_versions_to_stages:
    description: A list of all of the currently assigned SecretVersionStage staging labels and the SecretVersionId that each is attached to.
    returned: always
    type: dict
'''

import os
import re

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import camel_dict_to_snake_dict

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # handled by AnsibleAWSModule


def camel_list_to_snake_list(list):
    conv_list = []
    for i in list:
        conv_list.append(camel_dict_to_snake_dict(i))
    return conv_list


def main():
    module = AnsibleAWSModule(
        argument_spec={
            'name': dict(type='str'),
            'prefix': dict(type='str'),
            'suffix': dict(type='str'),
            'regex': dict(type='str'),
        },
        mutually_exclusive=[
            ['name', 'prefix', 'suffix', 'regex']
        ],
        supports_check_mode=True,
    )

    result = {
        'changed': False,
        'desired_secrets': []
    }

    client = module.client('secretsmanager')

    kwargs = {}
    all_secrets = []

    try:
        while True:
            response = client.list_secrets(**kwargs)
            for i in response['SecretList']:
                all_secrets.append(i)
            try:
                kwargs['nextToken'] = response['nextToken']
            except KeyError:
                break
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to look up secret data")

    if module.params.get('name'):
        for i in all_secrets:
            if i['Name'] == module.params.get('name'):
                result['desired_secrets'].append(camel_dict_to_snake_dict(i))
    elif module.params.get('prefix'):
        for i in all_secrets:
            if i['Name'].startswith(module.params.get('prefix')):
                result['desired_secrets'].append(camel_dict_to_snake_dict(i))
    elif module.params.get('suffix'):
        for i in all_secrets:
            if i['Name'].endswith(module.params.get('suffix')):
                result['desired_secrets'].append(camel_dict_to_snake_dict(i))
    elif module.params.get('regex'):
        for i in all_secrets:
            if re.match(module.params.get('regex'), i['Name']):
                result['desired_secrets'].append(camel_dict_to_snake_dict(i))
    else:
        result['desired_secrets'] = camel_list_to_snake_list(all_secrets)

    module.exit_json(changed=result['changed'], facts=result['desired_secrets'])


if __name__ == '__main__':
    main()
