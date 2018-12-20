#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: msc_role
short_description: Manage roles
description:
- Manage roles on Cisco ACI Multi-Site.
author:
- Dag Wieers (@dagwieers)
version_added: '2.8'
options:
  role_id:
    description:
    - The ID of the role.
    type: str
  role:
    description:
    - The name of the role.
    - Alternative to the name, you can use C(role_id).
    type: str
    required: yes
    aliases: [ name, role_name ]
  display_name:
    description:
    - The name of the role to be displayed in the web UI.
    type: str
  description:
    description:
    - The description of the role.
    type: str
  permissions:
    description:
    - A list of permissions tied to this role.
    type: list
    choices:
    - backup-db
    - manage-audit-records
    - manage-labels
    - manage-roles
    - manage-schemas
    - manage-sites
    - manage-tenants
    - manage-tenant-schemas
    - manage-users
    - platform-logs
    - view-all-audit-records
    - view-labels
    - view-roles
    - view-schemas
    - view-sites
    - view-tenants
    - view-tenant-schemas
    - view-users
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    type: str
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment: msc
'''

EXAMPLES = r'''
- name: Add a new role
  msc_role:
    host: msc_host
    username: admin
    password: SomeSecretPassword
    role: readOnly
    display_name: Read Only
    description: Read-only access for troubleshooting
    permissions:
    - view-roles
    - view-schemas
    - view-sites
    - view-tenants
    - view-tenant-schemas
    - view-users
    state: present
  delegate_to: localhost

- name: Remove a role
  msc_role:
    host: msc_host
    username: admin
    password: SomeSecretPassword
    role: readOnly
    state: absent
  delegate_to: localhost

- name: Query a role
  msc_role:
    host: msc_host
    username: admin
    password: SomeSecretPassword
    role: readOnly
    state: query
  delegate_to: localhost
  register: query_result

- name: Query all roles
  msc_role:
    host: msc_host
    username: admin
    password: SomeSecretPassword
    state: query
  delegate_to: localhost
  register: query_result
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.aci.msc import MSCModule, msc_argument_spec, issubset


def main():
    argument_spec = msc_argument_spec()
    argument_spec.update(
        role=dict(type='str', required=False, aliases=['name', 'role_name']),
        role_id=dict(type='str', required=False),
        display_name=dict(type='str'),
        description=dict(type='str'),
        permissions=dict(type='list', choices=[
            'backup-db',
            'manage-audit-records',
            'manage-labels',
            'manage-roles',
            'manage-schemas',
            'manage-sites',
            'manage-tenants',
            'manage-tenant-schemas',
            'manage-users',
            'platform-logs',
            'view-all-audit-records',
            'view-labels',
            'view-roles',
            'view-schemas',
            'view-sites',
            'view-tenants',
            'view-tenant-schemas',
            'view-users',
        ]),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['role']],
            ['state', 'present', ['role']],
        ],
    )

    role = module.params['role']
    role_id = module.params['role_id']
    description = module.params['description']
    permissions = module.params['permissions']
    state = module.params['state']

    msc = MSCModule(module)

    path = 'roles'

    # Query for existing object(s)
    if role_id is None and role is None:
        msc.existing = msc.query_objs(path)
    elif role_id is None:
        msc.existing = msc.get_obj(path, name=role)
        if msc.existing:
            role_id = msc.existing['id']
    elif role is None:
        msc.existing = msc.get_obj(path, id=role_id)
    else:
        msc.existing = msc.get_obj(path, id=role_id)
        existing_by_name = msc.get_obj(path, name=role)
        if existing_by_name and role_id != existing_by_name['id']:
            msc.fail_json(msg="Provided role '{0}' with id '{1}' does not match existing id '{2}'.".format(role, role_id, existing_by_name['id']))

    # If we found an existing object, continue with it
    if role_id:
        path = 'roles/{id}'.format(id=role_id)

    if state == 'query':
        pass

    elif state == 'absent':
        msc.previous = msc.existing
        if msc.existing:
            if module.check_mode:
                msc.existing = {}
            else:
                msc.existing = msc.request(path, method='DELETE')

    elif state == 'present':
        msc.previous = msc.existing

        payload = dict(
            id=role_id,
            name=role,
            displayName=role,
            description=description,
            permissions=permissions,
        )

        msc.sanitize(payload, collate=True)

        if msc.existing:
            if not issubset(msc.sent, msc.existing):
                if module.check_mode:
                    msc.existing = msc.proposed
                else:
                    msc.existing = msc.request(path, method='PUT', data=msc.sent)
        else:
            if module.check_mode:
                msc.existing = msc.proposed
            else:
                msc.existing = msc.request(path, method='POST', data=msc.sent)

    msc.exit_json()


if __name__ == "__main__":
    main()
