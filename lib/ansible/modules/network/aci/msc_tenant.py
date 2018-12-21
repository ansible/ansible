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
module: msc_tenant
short_description: Manage tenants
description:
- Manage tenants on Cisco ACI Multi-Site.
author:
- Dag Wieers (@dagwieers)
version_added: '2.8'
options:
  tenant_id:
    description:
    - The ID of the tenant.
    type: str
  tenant:
    description:
    - The name of the tenant.
    - Alternative to the name, you can use C(tenant_id).
    type: str
    required: yes
    aliases: [ name, tenant_name ]
  display_name:
    description:
    - The name of the tenant to be displayed in the web UI.
    type: str
    required: yes
  description:
    description:
    - The description for this tenant.
    type: str
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
- name: Add a new tenant
  msc_tenant:
    host: msc_host
    username: admin
    password: SomeSecretPassword
    tenant: north_europe
    tenant_id: 101
    display_name: North European Datacenter
    description: This tenant manages the NEDC environment.
    state: present
  delegate_to: localhost

- name: Remove a tenant
  msc_tenant:
    host: msc_host
    username: admin
    password: SomeSecretPassword
    tenant: north_europe
    state: absent
  delegate_to: localhost

- name: Query a tenant
  msc_tenant:
    host: msc_host
    username: admin
    password: SomeSecretPassword
    tenant: north_europe
    state: query
  delegate_to: localhost
  register: query_result

- name: Query all tenants
  msc_tenant:
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
        description=dict(type='str'),
        display_name=dict(type='str'),
        tenant=dict(type='str', required=False, aliases=['name', 'tenant_name']),
        tenant_id=dict(type='str', required=False),
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
    tenant_id = module.params['tenant_id']
    state = module.params['state']

    msc = MSCModule(module)

    path = 'tenants'

    # Query for existing object(s)
    if tenant_id is None and tenant is None:
        msc.existing = msc.query_objs(path)
    elif tenant_id is None:
        msc.existing = msc.get_obj(path, name=tenant)
        if msc.existing:
            tenant_id = msc.existing['id']
    elif tenant is None:
        msc.existing = msc.get_obj(path, id=tenant_id)
    else:
        msc.existing = msc.get_obj(path, id=tenant_id)
        existing_by_name = msc.get_obj(path, name=tenant)
        if existing_by_name and tenant_id != existing_by_name['id']:
            msc.fail_json(msg="Provided tenant '{0}' with id '{1}' does not match existing id '{2}'.".format(tenant, tenant_id, existing_by_name['id']))

    # If we found an existing object, continue with it
    if tenant_id:
        path = 'tenants/{id}'.format(id=tenant_id)

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
            description=description,
            id=tenant_id,
            name=tenant,
            displayName=display_name,
            siteAssociations=[],
            userAssociations=[dict(userId="0000ffff0000000000000020")],
        )

        msc.sanitize(payload, collate=True)

        # Ensure displayName is not undefined
        if msc.sent.get('displayName') is None:
            msc.sent['displayName'] = tenant

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
