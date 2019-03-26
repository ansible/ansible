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
module: purefb_dsrole
version_added: '2.8'
short_description: Configure FlashBlade  Management Directory Service Roles
description:
- Set or erase directory services role configurations.
author:
- Pure Storage Ansible Team (@sdodsley) <pure-ansible-team@purestorage.com>
options:
  state:
    description:
    - Create or delete directory service role
    default: present
    type: str
    choices: [ absent, present ]
  role:
    description:
    - The directory service role to work on
    choices: [ array_admin, ops_admin, readonly, storage_admin ]
    type: str
  group_base:
    description:
    - Specifies where the configured group is located in the directory
      tree. This field consists of Organizational Units (OUs) that combine
      with the base DN attribute and the configured group CNs to complete
      the full Distinguished Name of the groups. The group base should
      specify OU= for each OU and multiple OUs should be separated by commas.
      The order of OUs is important and should get larger in scope from left
      to right.
    - Each OU should not exceed 64 characters in length.
    type: str
  group:
    description:
    - Sets the common Name (CN) of the configured directory service group
      containing users for the FlashBlade. This name should be just the
      Common Name of the group without the CN= specifier.
    - Common Names should not exceed 64 characters in length.
    type: str
extends_documentation_fragment:
- purestorage.fb
'''

EXAMPLES = r'''
- name: Delete existing array_admin directory service role
  purefb_dsrole:
    role: array_admin
    state: absent
    fb_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Create array_admin directory service role
  purefb_dsrole:
    role: array_admin
    group_base: "OU=PureGroups,OU=SANManagers"
    group: pureadmins
    fb_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592

- name: Update ops_admin directory service role
  purefb_dsrole:
    role: ops_admin
    group_base: "OU=PureGroups"
    group: opsgroup
    fb_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592
'''

RETURN = r'''
'''


HAS_PURITY_FB = True
try:
    from purity_fb import DirectoryServiceRole
except ImportError:
    HAS_PURITY_FB = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pure import get_blade, purefb_argument_spec


def update_role(module, blade):
    """Update Directory Service Role"""
    changed = False
    role = blade.directory_services.list_directory_services_roles(names=[module.params['role']])
    if role.items[0].group_base != module.params['group_base'] or role.items[0].group != module.params['group']:
        try:
            role = DirectoryServiceRole(group_base=module.params['group_base'],
                                        group=module.params['group'])
            blade.directory_services.update_directory_services_roles(names=[module.params['role']],
                                                                     directory_service_role=role)
            changed = True
        except Exception:
            module.fail_json(msg='Update Directory Service Role {0} failed'.format(module.params['role']))
    module.exit_json(changed=changed)


def delete_role(module, blade):
    """Delete Directory Service Role"""
    changed = False
    try:
        role = DirectoryServiceRole(group_base='',
                                    group='')
        blade.directory_services.update_directory_services_roles(names=[module.params['role']],
                                                                 directory_service_role=role)
        changed = True
    except Exception:
        module.fail_json(msg='Delete Directory Service Role {0} failed'.format(module.params['role']))
    module.exit_json(changed=changed)


def create_role(module, blade):
    """Create Directory Service Role"""
    changed = False
    try:
        role = DirectoryServiceRole(group_base=module.params['group_base'],
                                    group=module.params['group'])
        blade.directory_services.update_directory_services_roles(names=[module.params['role']],
                                                                 directory_service_role=role)
        changed = True
    except Exception:
        module.fail_json(msg='Create Directory Service Role {0} failed: Check configuration'.format(module.params['role']))
    module.exit_json(changed=changed)


def main():
    argument_spec = purefb_argument_spec()
    argument_spec.update(dict(
        role=dict(required=True, type='str', choices=['array_admin', 'ops_admin', 'readonly', 'storage_admin']),
        state=dict(type='str', default='present', choices=['absent', 'present']),
        group_base=dict(type='str'),
        group=dict(type='str'),
    ))

    required_together = [['group', 'group_base']]

    module = AnsibleModule(argument_spec,
                           required_together=required_together,
                           supports_check_mode=False)

    if not HAS_PURITY_FB:
        module.fail_json(msg='purity_fb sdk is required for this module')

    state = module.params['state']
    blade = get_blade(module)
    role_configured = False
    role = blade.directory_services.list_directory_services_roles(names=[module.params['role']])
    if role.items[0].group is not None:
        role_configured = True

    if state == 'absent' and role_configured:
        delete_role(module, blade)
    elif role_configured and state == 'present':
        update_role(module, blade)
    elif not role_configured and state == 'present':
        create_role(module, blade)
    else:
        module.exit_json(changed=False)


if __name__ == '__main__':
    main()
