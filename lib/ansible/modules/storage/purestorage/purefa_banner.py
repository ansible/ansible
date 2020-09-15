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
module: purefa_banner
version_added: '2.9'
short_description: Configure Pure Storage FlashArray GUI and SSH MOTD message
description:
- Configure MOTD for Pure Storage FlashArrays.
- This will be shown during an SSH or GUI login to the array.
- Multiple line messages can be achieved using \\n.
author:
- Pure Storage Ansible Team (@sdodsley) <pure-ansible-team@purestorage.com>
options:
  state:
    description: Set ot delete the MOTD
    default: present
    type: str
    choices: [ present, absent ]
  banner:
    description: Banner text, or MOTD, to use
    type: str
    default: "Welcome to the machine..."
extends_documentation_fragment:
- purestorage.fa
'''

EXAMPLES = r'''
- name: Set new banner text
  purefa_banner:
    banner: "Banner over\ntwo lines"
    state: present
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Delete banner text
  purefa_banner:
    state: absent
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pure import get_system, purefa_argument_spec


def set_banner(module, array):
    """Set MOTD banner text"""
    changed = False

    try:
        if not module.params['banner']:
            module.fail_json(msg='Invalid MOTD banner given')

        if not module.check_mode:
            array.set(banner=module.params['banner'])
        changed = True
    except Exception:
        module.fail_json(msg='Failed to set MOTD banner text')

    module.exit_json(changed=changed)


def delete_banner(module, array):
    """Delete MOTD banner text"""
    changed = False
    try:
        array.set(banner="")
        changed = True
    except Exception:
        module.fail_json(msg='Failed to delete current MOTD banner text')
    module.exit_json(changed=changed)


def main():
    argument_spec = purefa_argument_spec()
    argument_spec.update(dict(
        banner=dict(type='str', default="Welcome to the machine..."),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    ))

    required_if = [('state', 'present', ['banner'])]

    module = AnsibleModule(argument_spec,
                           required_if=required_if,
                           supports_check_mode=False)

    state = module.params['state']
    array = get_system(module)
    current_banner = array.get(banner=True)['banner']
    # set banner if empty value or value differs
    if state == 'present' and (not current_banner or current_banner != module.params['banner']):
        set_banner(module, array)
    # clear banner if it has a value
    elif state == 'absent' and current_banner:
        delete_banner(module, array)

    module.exit_json(changed=False)


if __name__ == '__main__':
    main()
