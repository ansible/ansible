#!/usr/bin/python
# Copyright (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
module: boto3_facts
short_description: Get facts about boto3 and botocore versions
description:
    - Show python path and version and boto3 and botocore module versions
version_added: "2.7"

author: Will Thames (@willthames)
'''

EXAMPLES = '''
- name: show boto3 module information
  boto3_facts:
'''

RETURN = '''
python:
    description: path to python version used
    returned: always
    type: str
    sample: /usr/local/opt/python@2/bin/python2.7
python_version:
    description: version of python
    returned: always
    type: str
    sample: "2.7.15 (default, May  1 2018, 16:44:08)\n[GCC 4.2.1 Compatible Apple LLVM 9.1.0 (clang-902.0.39.1)]"
boto3_version:
    description: boto3 library version
    returned: if boto3 is installed
    type: str
    sample: "1.7.33"
botocore_version:
    description: botocore library version
    returned: if botocore is installed
    type: str
    sample: "1.10.33"
'''

import sys

from ansible.module_utils.aws.core import AnsibleAWSModule


def main():
    module = AnsibleAWSModule(argument_spec={},
                              supports_check_mode=True,
                              check_boto3=False,
                              default_args=False)
    module.exit_json(python=sys.executable, python_version=sys.version, **module._gather_versions())


if __name__ == '__main__':
    main()
