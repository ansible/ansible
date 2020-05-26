#!/usr/bin/python
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: redirected_module
short_description: a module that returns the option provided
version_added: "2.10"
description: a module that returns the option provided
options:
    option:
      description: an option to pass to the module
      default: default_value
'''

from ansible.module_utils.basic import AnsibleModule


def run_module():
    module = AnsibleModule(
        argument_spec={
            'option': {'type': 'str', 'default': 'default_value'}
        },
        supports_check_mode=True
    )

    module.exit_json(option=module.params['option'])


def main():
    run_module()


if __name__ == '__main__':
    main()
