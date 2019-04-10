#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: mso_tenant
short_description: Manage tenants
description:
- Manage tenants on Cisco ACI Multi-Site.
author:
- Dag Wieers (@dagwieers)
version_added: '2.8'
options:
  tenant:
    description:
    - The name of the tenant.
    type: str
    required: yes
    aliases: [ name ]
  display_name:
    description:
    - The name of the tenant to be displayed in the web UI.
    type: str
    required: yes
  description:
    description:
    - The description for this tenant.
    type: str
  users:
    description:
    - A list of associated users for this tenant.
    - Using this property will replace any existing associated users.
    type: list
  sites:
    description:
    - A list of associated sites for this tenant.
    - Using this property will replace any existing associated sites.
    type: list
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    type: str
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment: mso
'''

EXAMPLES = r'''
- name: Add a new tenant
  mso_tenant:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    tenant: north_europe
    display_name: North European Datacenter
    description: This tenant manages the NEDC environment.
    state: present
  delegate_to: localhost

- name: Remove a tenant
  mso_tenant:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    tenant: north_europe
    state: absent
  delegate_to: localhost

- name: Query a tenant
  mso_tenant:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    tenant: north_europe
    state: query
  delegate_to: localhost
  register: query_result

- name: Query all tenants
  mso_tenant:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    state: query
  delegate_to: localhost
  register: query_result
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.aci.mso import MSOModule, mso_argument_spec, issubset


def main():
    argument_spec = mso_argument_spec()
    argument_spec.update(
        description=dict(type='str'),
        display_name=dict(type='str'),
        tenant=dict(type='str', aliases=['name']),
        users=dict(type='list'),
        sites=dict(type='list'),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['tenant']],
            ['state', 'present', ['tenant']],
        ],
    )

    description = module.params['description']
    display_name = module.params['display_name']
    tenant = module.params['tenant']
    state = module.params['state']

    mso = MSOModule(module)

    # Convert sites and users
    sites = mso.lookup_sites(module.params['sites'])
    users = mso.lookup_users(module.params['users'])

    tenant_id = None
    path = 'tenants'

    # Query for existing object(s)
    if tenant:
        mso.existing = mso.get_obj(path, name=tenant)
        if mso.existing:
            tenant_id = mso.existing['id']
            # If we found an existing object, continue with it
            path = 'tenants/{id}'.format(id=tenant_id)
    else:
        mso.existing = mso.query_objs(path)

    if state == 'query':
        pass

    elif state == 'absent':
        mso.previous = mso.existing
        if mso.existing:
            if module.check_mode:
                mso.existing = {}
            else:
                mso.existing = mso.request(path, method='DELETE')

    elif state == 'present':
        mso.previous = mso.existing

        payload = dict(
            description=description,
            id=tenant_id,
            name=tenant,
            displayName=display_name,
            siteAssociations=sites,
            userAssociations=users,
        )

        mso.sanitize(payload, collate=True)

        # Ensure displayName is not undefined
        if mso.sent.get('displayName') is None:
            mso.sent['displayName'] = tenant

        # Ensure tenant has at least admin user
        if mso.sent.get('userAssociations') is None:
            mso.sent['userAssociations'] = [dict(userId="0000ffff0000000000000020")]

        if mso.existing:
            if not issubset(mso.sent, mso.existing):
                if module.check_mode:
                    mso.existing = mso.proposed
                else:
                    mso.existing = mso.request(path, method='PUT', data=mso.sent)
        else:
            if module.check_mode:
                mso.existing = mso.proposed
            else:
                mso.existing = mso.request(path, method='POST', data=mso.sent)

    mso.exit_json()


if __name__ == "__main__":
    main()
