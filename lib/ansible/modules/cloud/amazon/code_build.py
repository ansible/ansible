#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Shuang Wang <ooocamel@icloud.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: code_build
version_added: "2.8"
short_description: Represents AWS CodeBuild
description: Creates,deletes repository in AWS CodeBuild
author: Shuang Wang (@ptux)

requirements:
  - botocore
  - boto3
  - python >= 2.6

options:
  name:
    description:
      - name of build.
    required: true
  comment:
    description:
      - description or comment of build.
    required: false
  state:
    description:
      - Specifies the state of build.
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
# Create A new build
- code_build:
    name: build_name
    state: present
'''

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import camel_dict_to_snake_dict


class CodeBuild(object):
    def __init__(self, module=None):
        self._module = module
        self._client = self._module.client('codebuild')
        self._check_mode = self._module.check_mode

    def process(self):
        pass


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

    code_build = CodeBuild(module=ansible_aws_module)
    result = code_build.process()
    ansible_aws_module.exit_json(**camel_dict_to_snake_dict(result))


if __name__ == '__main__':
    main()
