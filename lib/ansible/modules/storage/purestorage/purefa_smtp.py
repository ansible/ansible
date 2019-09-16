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
module: purefa_smtp
version_added: '2.9'
author:
  - Pure Storage ansible Team (@sdodsley) <pure-ansible-team@purestorage.com>
short_description: Configure FlashArray SMTP settings
description:
- Set or erase configuration for the SMTP settings.
- If username/password are set this will always force a change as there is
  no way to see if the password is different from the current SMTP configuration.
- Pure Storage Ansible Team (@sdodsley) <pure-ansible-team@purestorage.com>
options:
  state:
    description:
    - Set or delete SMTP configuration
    default: present
    type: str
    choices: [ absent, present ]
  password:
    description:
    - The SMTP password.
    type: str
  user:
    description:
    - The SMTP username.
    type: str
  relay_host:
    description:
    - IPv4 or IPv6 address or FQDN. A port number may be appended.
    type: str
  sender_domain:
    description:
    - Domain name.
    type: str
extends_documentation_fragment:
- purestorage.fa
'''

EXAMPLES = r'''
- name: Delete existing SMTP settings
  purefa_smtp:
    state: absent
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Set SMTP settings
  purefa_smtp:
    sender_domain: purestorage.com
    password: account_password
    user: smtp_account
    relay_host: 10.2.56.78:2345
    fa_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pure import get_system, purefa_argument_spec


def delete_smtp(module, array):
    """Delete SMTP settings"""
    changed = True
    if not module.check_mode:
        try:
            array.set_smtp(sender_domain='', username='', password='', relay_host='')
        except Exception:
            module.fail_json(msg='Delete SMTP settings failed')
    module.exit_json(changed=changed)


def create_smtp(module, array):
    """Set SMTP settings"""
    changed = True
    current_smtp = array.get_smtp()
    if not module.check_mode:
        if module.params['sender_domain'] and current_smtp['sender_domain'] != module.params['sender_domain']:
            try:
                array.set_smtp(sender_domain=module.params['sender_domain'])
                changed_sender = True
            except Exception:
                module.fail_json(msg='Set SMTP sender domain failed.')
        else:
            changed_sender = False
        if module.params['relay_host'] and current_smtp['relay_host'] != module.params['relay_host']:
            try:
                array.set_smtp(relay_host=module.params['relay_host'])
                changed_relay = True
            except Exception:
                module.fail_json(msg='Set SMTP relay host failed.')
        else:
            changed_relay = False
        if module.params['user']:
            try:
                array.set_smtp(user_name=module.params['user'], password=module.params['password'])
                changed_creds = True
            except Exception:
                module.fail_json(msg='Set SMTP username/password failed.')
        else:
            changed_creds = False
        changed = bool(changed_sender or changed_relay or changed_creds)

    module.exit_json(changed=changed)


def main():
    argument_spec = purefa_argument_spec()
    argument_spec.update(dict(
        state=dict(type='str', default='present', choices=['absent', 'present']),
        sender_domain=dict(type='str'),
        password=dict(type='str', no_log=True),
        user=dict(type='str'),
        relay_host=dict(type='str'),
    ))

    required_together = [['user', 'password']]

    module = AnsibleModule(argument_spec,
                           required_together=required_together,
                           supports_check_mode=True)

    state = module.params['state']
    array = get_system(module)

    if state == 'absent':
        delete_smtp(module, array)
    elif state == 'present':
        create_smtp(module, array)
    else:
        module.exit_json(changed=False)


if __name__ == '__main__':
    main()
