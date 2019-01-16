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
module: msc_schema
short_description: Manage schemas
description:
- Manage schemas on Cisco ACI Multi-Site.
author:
- Dag Wieers (@dagwieers)
version_added: '2.8'
options:
  schema_id:
    description:
    - The ID of the schema.
    type: str
    required: yes
  schema:
    description:
    - The name of the schema.
    type: str
    required: yes
    aliases: [ name, schema_name ]
  templates:
    description:
    - A list of templates for this schema.
    type: list
  sites:
    description:
    - A list of sites mapped to templates in this schema.
    type: list
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
- name: Add a new schema
  msc_schema:
    host: msc_host
    username: admin
    password: SomeSecretPassword
    schema: Schema 1
    state: present
    templates:
    - name: Template1
      displayName: Template 1
      tenantId: north_europe
      anps:
        <...>
    - name: Template2
      displayName: Template 2
      tenantId: nort_europe
      anps:
        <...>
  delegate_to: localhost

- name: Remove schemas
  msc_schema:
    host: msc_host
    username: admin
    password: SomeSecretPassword
    schema: Schema 1
    state: absent
  delegate_to: localhost

- name: Query a schema
  msc_schema:
    host: msc_host
    username: admin
    password: SomeSecretPassword
    schema: Schema 1
    state: query
  delegate_to: localhost
  register: query_result

- name: Query all schemas
  msc_schema:
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
        schema=dict(type='str', required=False, aliases=['name', 'schema_name']),
        schema_id=dict(type='str', required=False),
        templates=dict(type='list'),
        sites=dict(type='list'),
        # messages=dict(type='dict'),
        # associations=dict(type='list'),
        # health_faults=dict(type='list'),
        # references=dict(type='dict'),
        # policy_states=dict(type='list'),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['schema']],
            ['state', 'present', ['schema']],
        ],
    )

    schema = module.params['schema']
    schema_id = module.params['schema_id']
    templates = module.params['templates']
    sites = module.params['sites']
    state = module.params['state']

    msc = MSCModule(module)

    path = 'schemas'

    # Query for existing object(s)
    if schema_id is None and schema is None:
        msc.existing = msc.query_objs(path)
    elif schema_id is None:
        msc.existing = msc.get_obj(path, displayName=schema)
        if msc.existing:
            schema_id = msc.existing['id']
    elif schema is None:
        msc.existing = msc.get_obj(path, id=schema_id)
    else:
        msc.existing = msc.get_obj(path, id=schema_id)
        existing_by_name = msc.get_obj(path, displayName=schema)
        if existing_by_name and schema_id != existing_by_name['id']:
            msc.fail_json(msg="Provided schema '{1}' with id '{2}' does not match existing id '{3}'.".format(schema, schema_id, existing_by_name['id']))

    if schema_id:
        path = 'schemas/{id}'.format(id=schema_id)

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
            id=schema_id,
            displayName=schema,
            templates=templates,
            sites=sites,
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
