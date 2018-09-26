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
results:
    description: A complex type that contains information about results
    returned: changed
    type: dict

'''

EXAMPLES = '''
# Create new A repository
- code_commit:
    name: repo
    state: present
'''

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import (
    boto3_conn,
    boto_exception,
    ec2_argument_spec
)


class AWSRoute53Record(object):
    def __init__(self, module=None):
        self._module = module
        self._connection = self._module.client('codecommit')
        self._check_mode = self._module.check_mode

    def process(self):
        results = dict(changed=False)
        changed = False

        results = self._connection.create_repository(
        repositoryName=self._module['name'],
        repositoryDescription=self._module['description']
        )
        return changed, results

    def _exists(self):
        exists = False
        repositories = self._connection.list_repositories()['repositories']

        return exists

def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True),
        description=dict(default=''),
        state=dict(choices=['present', 'absent'], required=True)
    ))

    ansible_aws_module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )
    code_commit = CodeCommit(module=ansible_aws_module)
    changed, results = code_commit.process()
    ansible_aws_module.exit_json(changed=changed, results=results)


if __name__ == '__main__':
    main()