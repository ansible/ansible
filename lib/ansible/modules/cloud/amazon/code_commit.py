#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Shuang Wang <ooocamel@icloud.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: code_commit
version_added: "2.8"
short_description: Represents AWS CodeCommit
description: Creates,deletes repository in AWS CodeCommit
author: Shuang Wang (@ptux)

requirements:
  - botocore
  - boto3
  - python >= 2.6

options:
  name:
    description:
      - name of repository.
    required: true
  comment:
    description:
      - description or comment of repository.
    required: false
  state:
    description:
      - Specifies the state of repository.
    required: true
    choices: [ 'present', 'absent' ]

extends_documentation_fragment:
  - aws
  - ec2
'''

RETURN = '''
result:
    description: A complex type that contains information about result
    returned: changed
    type: dict

'''

EXAMPLES = '''
# Create A new repository
- code_commit:
    name: repo
    state: present
'''

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import camel_dict_to_snake_dict


class CodeCommit(object):
    def __init__(self, module=None):
        self._module = module
        self._client = self._module.client('codecommit')
        self._check_mode = self._module.check_mode

    def process(self):
        result = dict(changed=False)
        repository_exists = self._repository_exists()

        if self._module.params['state'] == 'present' and not repository_exists:
            result['changed'] = True
            if not self._module.check_mode:
                result = self._create_repository()
        if self._module.params['state'] == 'absent' and repository_exists:
            result['changed'] = True
            if not self._module.check_mode:
                result = self._delete_repository()
        return result

    def _repository_exists(self):
        try:
            repository_exists = False
            paginator = self._client.get_paginator('list_repositories')
            for page in paginator.paginate():
                repositories = page['repositories']
                for item in repositories:
                    if self._module.params['name'] in item.values():
                        repository_exists = True
                        return repository_exists
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self._module.fail_json_aws(e, msg="couldn't get repository")
        return repository_exists

    def _create_repository(self):
        result = dict(changed=False)
        try:
            result = self._client.create_repository(
                repositoryName=self._module.params['name'],
                repositoryDescription=self._module.params['comment']
            )
            result['changed'] = True
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self._module.fail_json_aws(e, msg="couldn't create repository")
        return result

    def _delete_repository(self):
        result = dict(changed=False)
        try:
            result = self._client.delete_repository(
                repositoryName=self._module.params['name']
            )
            result['changed'] = True
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self._module.fail_json_aws(e, msg="couldn't delete repository")
        return result


def main():
    argument_spec = dict(
        name=dict(required=True),
        state=dict(choices=['present', 'absent'], required=True),
        comment=dict(default='')
    )

    ansible_aws_module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    code_commit = CodeCommit(module=ansible_aws_module)
    result = code_commit.process()
    ansible_aws_module.exit_json(**camel_dict_to_snake_dict(result))


if __name__ == '__main__':
    main()
