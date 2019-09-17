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
module: purefa_user
version_added: '2.8'
short_description: Create, modify or delete FlashArray local user account
description:
- Create, modify or delete local users on a Pure Storage FlashArray.
author:
- Pure Storage Ansible Team (@sdodsley) <pure-ansible-team@purestorage.com>
options:
  state:
    description:
    - Create, delete or update local user account
    default: present
    type: str
    choices: [ absent, present ]
  name:
    description:
    - The name of the local user account
    type: str
  role:
    description:
    - Sets the local user's access level to the array
    type: str
    choices: [ readonly, storage_admin, array_admin ]
  password:
    description:
    - Password for the local user.
    type: str
  old_password:
    description:
    - If changing an existing password, you must provide the old password for security
    type: str
  api:
    description:
    - Define whether to create an API token for this user
    - Token can be exposed using the I(debug) module
    type: bool
    default: false
extends_documentation_fragment:
- purestorage.fa
'''

EXAMPLES = r'''
- name: Create new user ansible with API token
  purefa_user:
    name: ansible
    password: apassword
    role: storage_admin
    api: true
    fb_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

  debug:
    msg: "API Token: {{ ansible_facts['api_token'] }}"

- name: Change role type for existing user
  purefa_user:
    name: ansible
    role: array_admin
    state: update
    fb_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Change password type for existing user (NOT IDEMPOTENT)
  purefa_user:
    name: ansible
    password: anewpassword
    old_password: apassword
    fb_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Change API token for existing user
  purefa_user:
    name: ansible
    api: true
    state: update
    fb_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

  debug:
    msg: "API Token: {{ ansible_facts['user_api'] }}"
'''

RETURN = r'''
'''


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pure import get_system, purefa_argument_spec


def get_user(module, array):
    """Return Local User Account or None"""
    user = None
    users = array.list_admins()
    for acct in range(0, len(users)):
        if users[acct]['name'] == module.params['name']:
            user = users[acct]
    return user


def create_user(module, array):
    """Create or Update Local User Account"""
    changed = False
    user = get_user(module, array)
    role = module.params['role']
    api_changed = False
    role_changed = False
    passwd_changed = False
    user_token = {}
    if not user:
        try:
            if not role:
                role = 'readonly'
            array.create_admin(module.params['name'], role=role,
                               password=module.params['password'])
            if module.params['api']:
                try:
                    user_token['user_api'] = array.create_api_token(module.params['name'])['api_token']
                    # Added for 2.8.2: Not breaking user's playbooks in minor releases.
                    user_token['api_token'] = user_token['user_api']
                except Exception:
                    array.delete_user(module.params['name'])
                    module.fail_json(msg='Local User {0}: Creation failed'.format(module.params['name']))
            changed = True
        except Exception:
            module.fail_json(msg='Local User {0}: Creation failed'.format(module.params['name']))
    else:
        if module.params['password'] and not module.params['old_password']:
            changed = False
            module.exit_json(changed=changed)
        if module.params['password'] and module.params['old_password']:
            if module.params['old_password'] and (module.params['password'] != module.params['old_password']):
                try:
                    array.set_admin(module.params['name'], password=module.params['password'],
                                    old_password=module.params['old_password'])
                    passwd_changed = True
                except Exception:
                    module.fail_json(msg='Local User {0}: Password reset failed. '
                                     'Check old password.'.format(module.params['name']))
            else:
                module.fail_json(msg='Local User Account {0}: Password change failed - '
                                 'Check both old and new passwords'.format(module.params['name']))
        if module.params['api']:
            try:
                if not array.get_api_token(module.params['name'])['api_token'] is None:
                    array.delete_api_token(module.params['name'])
                user_token['user_api'] = array.create_api_token(module.params['name'])['api_token']
                # Added for 2.8.2: Not breaking user's playbooks in minor releases.
                user_token['api_token'] = user_token['user_api']
                api_changed = True
            except Exception:
                module.fail_json(msg='Local User {0}: API token change failed'.format(module.params['name']))
        if module.params['role'] != user['role']:
            try:
                array.set_admin(module.params['name'], role=module.params['role'])
                role_changed = True
            except Exception:
                module.fail_json(msg='Local User {0}: Role changed failed'.format(module.params['name']))
        if passwd_changed or role_changed or api_changed:
            changed = True
    module.exit_json(changed=changed, ansible_facts=user_token)


def delete_user(module, array):
    """Delete Local User Account"""
    changed = False
    if get_user(module, array):
        try:
            array.delete_admin(module.params['name'])
            changed = True
        except Exception:
            module.fail_json(msg='Object Store Account {0}: Deletion failed'.format(module.params['name']))
    module.exit_json(changed=changed)


def main():
    argument_spec = purefa_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True, type='str'),
        role=dict(type='str', choices=['readonly', 'storage_admin', 'array_admin']),
        state=dict(type='str', default='present', choices=['absent', 'present']),
        password=dict(type='str', no_log=True),
        old_password=dict(type='str', no_log=True),
        api=dict(type='bool', default=False),
    ))

    module = AnsibleModule(argument_spec,
                           supports_check_mode=False)

    state = module.params['state']
    array = get_system(module)

    if state == 'absent':
        delete_user(module, array)
    elif state == 'present':
        create_user(module, array)
    else:
        module.exit_json(changed=False)


if __name__ == '__main__':
    main()
