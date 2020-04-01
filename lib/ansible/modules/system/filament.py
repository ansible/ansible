#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020, David Shrewsbury <dshrewsb@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: filament
version_added: '2.10'
short_description: Test module
description:
    - Just a test module.
author: "David Shrewsbury (@Shrews)"
options:
    num1:
        description: First number for adding
        type: int
        required: true
    num2:
        description: Second number for adding
        type: int
        required: true
'''

EXAMPLES = '''
    - name: Add numbers
      filament:
          num1: 6
          num2: 4
      register: result
'''

RETURN = '''
    result:
        description: The addition result value
        type: int
        returned: on success
        sample: 10
'''

from ansible.module_utils.basic import AnsibleModule


def do_add(num1, num2):
    return num1 + num2


def run_module():
    module_args = dict(
        num1=dict(type='int', required=True),
        num2=dict(type='int', required=True)
    )
    module = AnsibleModule(argument_spec=module_args)
    result = dict(changed=True)
    result['result'] = do_add(module.params['num1'], module.params['num2'])
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
