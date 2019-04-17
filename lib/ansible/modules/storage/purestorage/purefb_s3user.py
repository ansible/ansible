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
module: purefb_s3user
version_added: '2.8'
short_description: Create or delete FlashBlade Object Store account users
description:
- Create or delete object store account users on a Pure Stoage FlashBlade.
author:
- Pure Storage Ansible Team (@sdodsley) <pure-ansible-team@purestorage.com>
options:
  state:
    description:
    - Create or delete object store account user
    default: present
    choices: [ absent, present ]
    type: str
  name:
    description:
    - The name of object store user
    type: str
  account:
    description:
    - The name of object store account associated with user
    type: str
  access_key:
    description:
    - Create secret access key.
    - Key can be exposed using the I(debug) module
    type: bool
    default: true
extends_documentation_fragment:
- purestorage.fb
'''

EXAMPLES = r'''
- name: Crrate object store user (with access ID and key) foo in account bar
  purefb_s3user:
    name: foo
    account: bar
    fb_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

  debug:
    var: ansible_facts.fb_s3user

- name: Delete object store user foo in account bar
  purefb_s3user:
    name: foo
    account: bar
    state: absent
    fb_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592
'''

RETURN = r'''
'''


HAS_PURITY_FB = True
try:
    from purity_fb import ObjectStoreAccessKey
except ImportError:
    HAS_PURITY_FB = False


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pure import get_blade, purefb_argument_spec


MIN_REQUIRED_API_VERSION = '1.3'


def get_s3acc(module, blade):
    """Return Object Store Account or None"""
    s3acc = None
    accts = blade.object_store_accounts.list_object_store_accounts()
    for acct in range(0, len(accts.items)):
        if accts.items[acct].name == module.params['account']:
            s3acc = accts.items[acct]
    return s3acc


def get_s3user(module, blade):
    """Return Object Store Account or None"""
    full_user = module.params['account'] + "/" + module.params['name']
    s3user = None
    s3users = blade.object_store_users.list_object_store_users()
    for user in range(0, len(s3users.items)):
        if s3users.items[user].name == full_user:
            s3user = s3users.items[user]
    return s3user


def update_s3user(module, blade):
    """Update Object Store User"""
    changed = False
    s3user_facts = {}
    user = module.params['account'] + "/" + module.params['name']
    if module.params['access_key']:
        try:
            result = blade.object_store_access_keys.create_object_store_access_keys(
                object_store_access_key=ObjectStoreAccessKey(user={'name': user}))
            s3user_facts['fb_s3user'] = {'user': user,
                                         'access_key': result.items[0].secret_access_key,
                                         'access_id': result.items[0].name}
        except Exception:
            delete_s3user(module, blade)
            module.fail_json(msg='Object Store User {0}: Creation failed'.format(user))
    changed = True
    module.exit_json(changed=changed, ansible_facts=s3user_facts)


def create_s3user(module, blade):
    """Create Object Store Account"""
    s3user_facts = {}
    changed = False
    user = module.params['account'] + "/" + module.params['name']
    try:
        blade.object_store_users.create_object_store_users(names=[user])
        if module.params['access_key']:
            try:
                result = blade.object_store_access_keys.create_object_store_access_keys(
                    object_store_access_key=ObjectStoreAccessKey(user={'name': user}))
                s3user_facts['fb_s3user'] = {'user': user,
                                             'access_key': result.items[0].secret_access_key,
                                             'access_id': result.items[0].name}
            except Exception:
                delete_s3user(module, blade)
                module.fail_json(msg='Object Store User {0}: Creation failed'.format(user))
        changed = True
    except Exception:
        module.fail_json(msg='Object Store User {0}: Creation failed'.format(user))
    module.exit_json(changed=changed, ansible_facts=s3user_facts)


def delete_s3user(module, blade):
    """Delete Object Store Account"""
    changed = False
    user = module.params['account'] + "/" + module.params['name']
    try:
        blade.object_store_users.delete_object_store_users(names=[user])
        changed = True
    except Exception:
        module.fail_json(msg='Object Store Account {0}: Deletion failed'.format(module.params['name']))
    module.exit_json(changed=changed)


def main():
    argument_spec = purefb_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True, type='str'),
        account=dict(required=True, type='str'),
        access_key=dict(default='true', type='bool'),
        state=dict(default='present', choices=['present', 'absent']),
    ))

    module = AnsibleModule(argument_spec,
                           supports_check_mode=False)

    if not HAS_PURITY_FB:
        module.fail_json(msg='purity_fb sdk is required for this module')

    state = module.params['state']
    blade = get_blade(module)
    versions = blade.api_version.list_versions().versions

    if MIN_REQUIRED_API_VERSION not in versions:
        module.fail_json(msg='FlashBlade REST version not supported. Minimum version required: {0}'.format(MIN_REQUIRED_API_VERSION))

    s3acc = get_s3acc(module, blade)
    if not s3acc:
        module.fail_json(msg='Object Store Account {0} does not exist'.format(module.params['account']))

    s3user = get_s3user(module, blade)

    if state == 'absent' and s3user:
        delete_s3user(module, blade)
    elif state == 'present' and s3user:
        update_s3user(module, blade)
    elif not s3user and state == 'present':
        create_s3user(module, blade)
    else:
        module.exit_json(changed=False)


if __name__ == '__main__':
    main()
