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
module: mso_schema_template
short_description: Manage templates in schemas
description:
- Manage templates on Cisco ACI Multi-Site.
author:
- Dag Wieers (@dagwieers)
version_added: '2.8'
options:
  schema:
    description:
    - The name of the schema.
    type: str
    required: yes
  template:
    description:
    - The name of the template.
    type: str
    aliases: [ name ]
  tenant:
    description:
    - The tenant used for this template.
    type: str
  display_name:
    description:
    - The name as displayed on the MSO web interface.
    type: str
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    type: str
    choices: [ absent, present, query ]
    default: present
notes:
- This module creates schemas when needed, and removes them when the last template has been removed.
seealso:
- module: mso_schema
- module: mso_schema_site
extends_documentation_fragment: mso
'''

EXAMPLES = r'''
- name: Add a new template to a schema
  mso_schema_template:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    tenant: Tenant 1
    schema: Schema 1
    template: Template 1
    state: present
  delegate_to: localhost

- name: Remove a template from a schema
  mso_schema:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    tenant: Tenant 1
    schema: Schema 1
    template: Template 1
    state: absent
  delegate_to: localhost

- name: Query a template
  mso_schema:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    tenant: Tenant 1
    schema: Schema 1
    template: Template 1
    state: query
  delegate_to: localhost
  register: query_result

- name: Query all templates
  mso_schema:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    tenant: Tenant 1
    schema: Schema 1
    state: query
  delegate_to: localhost
  register: query_result
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.aci.mso import MSOModule, mso_argument_spec


def main():
    argument_spec = mso_argument_spec()
    argument_spec.update(
        tenant=dict(type='str', required=True),
        schema=dict(type='str', required=True),
        template=dict(type='str', required=False, aliases=['name']),
        display_name=dict(type='str'),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['template']],
            ['state', 'present', ['template']],
        ],
    )

    tenant = module.params['tenant']
    schema = module.params['schema']
    template = module.params['template']
    display_name = module.params['display_name']
    state = module.params['state']

    mso = MSOModule(module)

    # Get schema
    schema_obj = mso.get_obj('schemas', displayName=schema)
    if schema_obj:
        # Schema exists
        path = 'schemas/{id}'.format(**schema_obj)

        # Get template
        templates = [t['name'] for t in schema_obj['templates']]
        if template is None:
            mso.existing = schema_obj['templates']
        elif template in templates:
            template_idx = templates.index(template)
            mso.existing = schema_obj['templates'][template_idx]
        else:
            mso.existing = {}
    else:
        path = 'schemas'

        if template is None:
            mso.existing = []
        else:
            mso.existing = {}

    if state == 'query':
        mso.exit_json()

    mso.previous = mso.existing
    if state == 'absent':
        mso.proposed = mso.sent = {}

        if not schema_obj:
            # There was no schema to begin with
            pass
        elif len(templates) == 1:
            # There is only one tenant, remove schema
            mso.existing = {}
            if not module.check_mode:
                mso.request(path, method='DELETE')
        elif mso.existing:
            # Remove existing template
            mso.existing = {}
            operation = [
                dict(op='remove', path='/templates/{template}'.format(template=template)),
            ]
            if not module.check_mode:
                mso.request(path, method='PATCH', data=operation)
        else:
            # There was no template to begin with
            pass

    elif state == 'present':
        tenant_id = mso.lookup_tenant(tenant)

        if display_name is None:
            display_name = mso.existing.get('displayName', template)

        if not schema_obj:
            # Schema does not exist, so we have to create it
            payload = dict(
                displayName=schema,
                templates=[dict(
                    name=template,
                    displayName=display_name,
                    tenantId=tenant_id,
                )],
                sites=[],
            )

            mso.existing = payload['templates'][0]

            if not module.check_mode:
                mso.request(path, method='POST', data=payload)

        elif mso.existing:
            # Template exists, so we have to update it
            payload = dict(
                name=template,
                displayName=display_name,
                tenantId=tenant_id,
            )

            mso.sanitize(payload, collate=True)

            mso.existing = payload
            operations = [
                dict(op='replace', path='/templates/{template}/displayName'.format(template=template), value=display_name),
                dict(op='replace', path='/templates/{template}/tenantId'.format(template=template), value=tenant_id),
            ]

            if not module.check_mode:
                mso.request(path, method='PATCH', data=operations)
        else:
            # Template does not exist, so we have to add it
            payload = dict(
                name=template,
                displayName=display_name,
                tenantId=tenant_id,
            )

            mso.existing = payload
            operations = [
                dict(op='add', path='/templates/-', value=payload),
            ]

            if not module.check_mode:
                mso.request(path, method='PATCH', data=operations)

    mso.exit_json()


if __name__ == "__main__":
    main()
