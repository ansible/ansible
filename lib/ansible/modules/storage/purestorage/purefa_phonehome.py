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
module: purefa_phonehome
version_added: '2.9'
short_description: Enable or Disable Pure Storage FlashArray Phonehome
description:
- Enable or Disable Phonehome for a Pure Storage FlashArray.
author:
- Pure Storage Ansible Team (@sdodsley) <pure-ansible-team@purestorage.com>
options:
  state:
    description:
    - Define state of phonehome
    type: str
    default: present
    choices: [ present, absent ]
extends_documentation_fragment:
- purestorage.fa
'''

EXAMPLES = r'''
- name: Enable Phonehome
  purefa_phonehome:
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Disable Phonehome
  purefa_phonehome:
    state: disable
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pure import get_system, purefa_argument_spec


def enable_ph(module, array):
    """Enable Remote Assist"""
    changed = False
    if array.get_phonehome()['phonehome'] != 'enabled':
        try:
            if not module.check_mode:
                array.enable_phonehome()
            changed = True
        except Exception:
            module.fail_json(msg='Enabling Phonehome failed')
    module.exit_json(changed=changed)


def disable_ph(module, array):
    """Disable Remote Assist"""
    changed = False
    if array.get_phonehome()['phonehome'] == 'enabled':
        try:
            if not module.check_mode:
                array.disable_phonehome()
            changed = True
        except Exception:
            module.fail_json(msg='Disabling Remote Assist failed')
    module.exit_json(changed=changed)


def main():
    argument_spec = purefa_argument_spec()
    argument_spec.update(dict(
        state=dict(type='str', default='present', choices=['present', 'absent']),
    ))

    module = AnsibleModule(argument_spec,
                           supports_check_mode=True)

    array = get_system(module)

    if module.params['state'] == 'present':
        enable_ph(module, array)
    else:
        disable_ph(module, array)
    module.exit_json(changed=False)


if __name__ == '__main__':
    main()
