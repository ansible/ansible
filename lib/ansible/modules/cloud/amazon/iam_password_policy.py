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

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: iam_password_policy
short_description: Update an IAM Password Policy
description:
    - Module updates an IAM Password Policy on a given AWS account
version_added: "2.6"
requirements: [ 'botocore', 'boto3' ]
author:
    - "Aaron Smith (@slapula)"
options:
  state:
    description:
      - Specifies the overall state of the password policy.
    required: true
    choices: ['present', 'absent']
  min_pw_length:
    description:
      - Minimum password length.
    default: 6
  require_symbols:
    description:
      - Require symbols in password.
    default: false
    type: bool
  require_numbers:
    description:
      - Require numbers in password.
    default: false
    type: bool
  require_uppercase:
    description:
      - Require uppercase letters in password.
    default: false
    type: bool
  require_lowercase:
    description:
      - Require lowercase letters in password.
    default: false
    type: bool
  allow_pw_change:
    description:
      - Allow users to change their password.
    default: false
    type: bool
  pw_max_age:
    description:
      - Maximum age for a password in days.
    default: 0
  pw_reuse_prevent:
    description:
      - Prevent re-use of passwords.
    default: 0
  pw_expire:
    description:
      - Prevents users from change an expired password.
    default: false
    type: bool
extends_documentation_fragment:
  - aws
  - ec2
'''

EXAMPLES = '''
- name: Password policy for AWS account
  iam_password_policy:
    state: present
    min_pw_length: 8
    require_symbols: false
    require_numbers: true
    require_uppercase: true
    require_lowercase: true
    allow_pw_change: true
    pw_max_age: 60
    pw_reuse_prevent: 5
    pw_expire: false
'''

RETURN = ''' # '''

from collections import defaultdict

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import boto3_conn, get_aws_connection_info, ec2_argument_spec, AWSRetry
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, boto3_tag_list_to_ansible_dict


class IAMConnection(object):

    def __init__(self, module, region, **aws_connect_params):
        try:
            self.connection = boto3_conn(module, conn_type='resource',
                                         resource='iam', region=region,
                                         **aws_connect_params)
            self.module = module
        except Exception as e:
            module.fail_json(msg="Failed to connect to AWS: %s" % str(e))
        self.region = region

    def update_password_policy(self, module, policy):
        min_pw_length = module.params.get('min_pw_length')
        require_symbols = module.params.get('require_symbols')
        require_numbers = module.params.get('require_numbers')
        require_uppercase = module.params.get('require_uppercase')
        require_lowercase = module.params.get('require_lowercase')
        allow_pw_change = module.params.get('allow_pw_change')
        pw_max_age = module.params.get('pw_max_age')
        pw_reuse_prevent = module.params.get('pw_reuse_prevent')
        pw_expire = module.params.get('pw_expire')

        try:
            results = policy.update(
                MinimumPasswordLength=min_pw_length,
                RequireSymbols=require_symbols,
                RequireNumbers=require_numbers,
                RequireUppercaseCharacters=require_uppercase,
                RequireLowercaseCharacters=require_lowercase,
                AllowUsersToChangePassword=allow_pw_change,
                MaxPasswordAge=pw_max_age,
                PasswordReusePrevention=pw_reuse_prevent,
                HardExpiry=pw_expire
            )
            policy.reload()
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Couldn't update IAM Password Policy")
        return camel_dict_to_snake_dict(results)

    def delete_password_policy(self, policy):
        try:
            results = policy.delete()
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            if e.response['Error']['Code'] == 'NoSuchEntity':
                self.module.exit_json(changed=False, task_status={'IAM': "Couldn't find IAM Password Policy"})
            else:
                self.module.fail_json_aws(e, msg="Couldn't delete IAM Password Policy")
        return camel_dict_to_snake_dict(results)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        state=dict(choices=['present', 'absent'], required=True),
        min_pw_length=dict(type='int', default=6),
        require_symbols=dict(type='bool', default=False),
        require_numbers=dict(type='bool', default=False),
        require_uppercase=dict(type='bool', default=False),
        require_lowercase=dict(type='bool', default=False),
        allow_pw_change=dict(type='bool', default=False),
        pw_max_age=dict(type='int', default=0),
        pw_reuse_prevent=dict(type='int', default=0),
        pw_expire=dict(type='bool', default=False),
    ))

    module = AnsibleAWSModule(argument_spec=argument_spec,
                              supports_check_mode=True)

    region, dummy, aws_connect_params = get_aws_connection_info(module, boto3=True)
    resource = IAMConnection(module, region, **aws_connect_params)
    policy = resource.connection.AccountPasswordPolicy()

    state = module.params.get('state')

    if state == 'present':
        update_result = resource.update_password_policy(module, policy)
        module.exit_json(changed=True, task_status={'IAM': update_result})

    if state == 'absent':
        delete_result = resource.delete_password_policy(policy)
        module.exit_json(changed=True, task_status={'IAM': delete_result})


if __name__ == '__main__':
    main()
