#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, Simon Dodsley (simon@purestorage.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: purefa_arrayname
version_added: '2.9'
short_description: Configure Pure Storage FlashArray array name
description:
- Configure name of array for Pure Storage FlashArrays.
- Ideal for Day 0 initial configuration.
author:
- Pure Storage Ansible Team (@sdodsley) <pure-ansible-team@purestorage.com>
options:
  state:
    description: Set the array name
    type: str
    default: present
    choices: [ present ]
  name:
    description:
    - Name of the array. Must conform to correct naming schema.
    type: str
    required: true
extends_documentation_fragment:
- purestorage.fa
'''

EXAMPLES = r'''
- name: Set new array name
  purefa_arrayname:
    name: new-array-name
    state: present
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592
'''

RETURN = r'''
'''

import re
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pure import get_system, purefa_argument_spec


def update_name(module, array):
    """Change array name"""
    changed = False

    try:
        array.set(name=module.params['name'])
        changed = True
    except Exception:
        module.fail_json(msg='Failed to change array name to {0}'.format(module.params['name']))

    module.exit_json(changed=changed)


def main():
    argument_spec = purefa_argument_spec()
    argument_spec.update(dict(
        name=dict(type='str', required=True),
        state=dict(type='str', default='present', choices=['present']),
    ))

    module = AnsibleModule(argument_spec,
                           supports_check_mode=False)

    array = get_system(module)
    pattern = re.compile("^[a-zA-Z0-9]([a-zA-Z0-9-]{0,54}[a-zA-Z0-9])?$")
    if not pattern.match(module.params['name']):
        module.fail_json(msg='Array name {0} does not conform to array name rules. See documentation.'.format(module.params['name']))
    if module.params['name'] != array.get()['array_name']:
        update_name(module, array)

    module.exit_json(changed=False)


if __name__ == '__main__':
    main()
