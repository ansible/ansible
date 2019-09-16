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
module: purefb_s3acc
version_added: '2.8'
short_description: Create or delete FlashBlade Object Store accounts
description:
- Create or delete object store accounts on a Pure Storage FlashBlade.
author:
- Pure Storage Ansible Team (@sdodsley) <pure-ansible-team@purestorage.com>
options:
  state:
    description:
    - Create or delete object store account
    default: present
    choices: [ absent, present ]
    type: str
  name:
    description:
    - The name of object store account
    type: str
extends_documentation_fragment:
- purestorage.fb
'''

EXAMPLES = r'''
- name: Create object store account foo
  purefb_s3acc:
    name: foo
    fb_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Delete object store account foo
  purefb_s3acc:
    name: foo
    state: absent
    fb_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592
'''

RETURN = r'''
'''


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pure import get_blade, purefb_argument_spec


MIN_REQUIRED_API_VERSION = '1.3'


def get_s3acc(module, blade):
    """Return Object Store Account or None"""
    s3acc = None
    accts = blade.object_store_accounts.list_object_store_accounts()
    for acct in range(0, len(accts.items)):
        if accts.items[acct].name == module.params['name']:
            s3acc = accts.items[acct]
    return s3acc


def update_s3acc(module, blade):
    """Update Object Store Account"""
    changed = False
    module.exit_json(changed=changed)


def create_s3acc(module, blade):
    """Create Object Store Account"""
    changed = False
    try:
        blade.object_store_accounts.create_object_store_accounts(names=[module.params['name']])
        changed = True
    except Exception:
        module.fail_json(msg='Object Store Account {0}: Creation failed'.format(module.params['name']))
    module.exit_json(changed=changed)


def delete_s3acc(module, blade):
    """Delete Object Store Account"""
    changed = False
    count = len(blade.object_store_users.list_object_store_users(filter='name=\'' + module.params['name'] + '/*\'').items)
    if count != 0:
        module.fail_json(msg='Remove all Users from Object Store Account {0} before deletion'.format(module.params['name']))
    else:
        try:
            blade.object_store_accounts.delete_object_store_accounts(names=[module.params['name']])
            changed = True
        except Exception:
            module.fail_json(msg='Object Store Account {0}: Deletion failed'.format(module.params['name']))
    module.exit_json(changed=changed)


def main():
    argument_spec = purefb_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True, type='str'),
        state=dict(default='present', choices=['present', 'absent']),
    ))

    module = AnsibleModule(argument_spec,
                           supports_check_mode=False)

    state = module.params['state']
    blade = get_blade(module)
    versions = blade.api_version.list_versions().versions

    if MIN_REQUIRED_API_VERSION not in versions:
        module.fail_json(msg='FlashBlade REST version not supported. Minimum version required: {0}'.format(MIN_REQUIRED_API_VERSION))

    s3acc = get_s3acc(module, blade)

    if state == 'absent' and s3acc:
        delete_s3acc(module, blade)
    elif state == 'present' and s3acc:
        update_s3acc(module, blade)
    elif not s3acc and state == 'present':
        create_s3acc(module, blade)
    else:
        module.exit_json(changed=False)


if __name__ == '__main__':
    main()
