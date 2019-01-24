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
module: mso_schema_template_contract_filter
short_description: Manage contract filters in schema templates
description:
- Manage contract filters in schema templates on Cisco ACI Multi-Site.
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
    type: list
  contract:
    description:
    - The name of the contract to manage.
    type: str
  contract_display_name:
    description:
    - The name as displayed on the MSO web interface.
    type: str
  contract_scope:
    description:
    - The scope of the contract
    type: str
    choices: [ application-profile, global, tenant, vrf ]
  filter:
    description:
    - The filter to associate with this contract.
    type: str
    aliases: [ name ]
  filter_template:
    description:
    - The template name in which the filter is located.
    type: str
  filter_schema:
    description:
    - The schema name in which the filter is located.
    type: str
  filter_type:
    description:
    - The type of filter to manage.
    type: str
    choices: [ both-directions, consumer-to-provider, provider-to-consumer ]
    default: both-directions
    aliases: [ type ]
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
- name: Add a new contract filter
  mso_schema_template_contract_filter:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    schema: Schema 1
    template: Template 1
    contract: Contract 1
    scope: global
    filter: Filter 1
    state: present
  delegate_to: localhost

- name: Remove a contract filter
  mso_schema_template_contract_filter:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    schema: Schema 1
    template: Template 1
    contract: Contract 1
    filter: Filter 1
    state: absent
  delegate_to: localhost

- name: Query a specific contract filter
  mso_schema_template_contract_filter:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    schema: Schema 1
    template: Template 1
    contract: Contract 1
    filter: Filter 1
    state: query
  delegate_to: localhost
  register: query_result

- name: Query all contract filters
  mso_schema_template_contract_filter:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    schema: Schema 1
    template: Template 1
    contract: Contract 1
    state: query
  delegate_to: localhost
  register: query_result
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.aci.mso import MSOModule, mso_argument_spec, mso_reference_spec, issubset

FILTER_KEYS = {
    'both-directions': 'filterRelationships',
    'consumer-to-provider': 'filterRelationshipsConsumerToProvider',
    'provider-to-consumer': 'filterRelationshipsProviderToConsumer',
}


def main():
    argument_spec = mso_argument_spec()
    argument_spec.update(
        schema=dict(type='str', required=True),
        template=dict(type='str', required=True),
        contract=dict(type='str', required=False),  # This parameter is not required for querying all objects
        contract_display_name=dict(type='str'),
        contract_scope=dict(type='str', required=True, choices=['application-profile', 'global', 'tenant', 'vrf']),
        filter=dict(type='str', aliases=['name']),
        filter_template=dict(type='str'),
        filter_schema=dict(type='str'),
        filter_type=dict(type='str', default='both-directions', choices=FILTER_KEYS.keys(), aliases=['type']),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['filter']],
            ['state', 'present', ['filter']],
        ],
    )

    schema = module.params['schema']
    template = module.params['template']
    contract = module.params['contract']
    contract_display_name = module.params['contract_display_name']
    contract_scope = module.params['contract_scope']
    filter_name = module.params['filter']
    filter_template = module.params['filter_template']
    filter_schema = module.params['filter_schema']
    filter_type = module.params['filter_type']
    state = module.params['state']

    if filter_template is None:
        filter_template = template

    if filter_schema is None:
        filter_schema = schema

    filter_key = FILTER_KEYS[filter_type]

    mso = MSOModule(module)

    filter_schema_id = mso.lookup_schema(filter_schema)

    # Get schema object
    schema_obj = mso.get_obj('schemas', displayName=schema)
    if schema_obj:
        schema_id = schema_obj['id']
    else:
        mso.fail_json(msg="Provided schema '{0}' does not exist".format(schema))

    path = 'schemas/{id}'.format(id=schema_id)

    # Get template
    templates = [t['name'] for t in schema_obj['templates']]
    if template not in templates:
        mso.fail_json(msg="Provided template '{0}' does not exist. Existing templates: {1}".format(template, ', '.join(templates)))
    template_idx = templates.index(template)

    # Get contracts
    mso.existing = {}
    contract_idx = None
    entry_idx = None
    contracts = [c['name'] for c in schema_obj['templates'][template_idx]['contracts']]

    if contract in contracts:
        contract_idx = contracts.index(contract)

        filters = [f['filterRef'] for f in schema_obj['templates'][template_idx]['contracts'][contract_idx][filter_key]]
        filter_ref = mso.filter_ref(filter_schema_id, filter_template, filter_name)
        if filter_ref in filters:
            filter_idx = filters.index(filter_ref)
            mso.existing = schema_obj['templates'][template_idx]['contracts'][contract_idx][filter_key][filter_idx]

    if state == 'query':
        if filter_name is None:
            mso.existing = schema_obj['templates'][template_idx]['contractss'][contract_idx][filter_key]
        elif not mso.existing:
            mso.fail_json(msg="FilterRef '{filter_ref}' not found".format(filter_ref=filter_ref))
        mso.exit_json()

    mso.previous = mso.existing
    if state == 'absent':
        mso.proposed = mso.sent = {}

        if contract_idx is None:
            # There was no contract to begin with
            pass
        elif filter_idx is None:
            # There was no filter to begin with
            pass
        elif len(filters) == 1:
            # There is only one filter, remove contract
            mso.existing = {}
            operations = [
                dict(op='remove', path='/templates/{template}/contracts/{contract}'.format(template=template, contract=contract)),
            ]
            if not module.check_mode:
                mso.request(path, method='PATCH', data=operations)
        else:
            # FIXME: Removing based on index is DANGEROUS
            # Remove filter
            mso.existing = {}
            operations = [
                dict(
                    op='remove',
                    path='/templates/{template}/contracts/{contract}/{filter_key}/{filter_idx}'.format(
                        template=template,
                        contract=contract,
                        filter_key=filter_key,
                        filter_idx=filter_idx,
                    ),
                ),
            ]
            if not module.check_mode:
                mso.request(path, method='PATCH', data=operations)

    elif state == 'present':

        payload = dict(
            filterRef=dict(
                filterName=filter_name,
                templateName=filter_template,
                schemaId=filter_schema_id,
            ),
            directives=[],
        )

        mso.sanitize(payload, collate=True)
        mso.existing = mso.sent

        if contract_idx is None:
            # COntract does not exist, so we have to create it
            if contract_display_name is None:
                contract_display_name = contract

            payload = {
                'name': contract,
                'displayName': contract_display_name,
                'scope': contract_scope,
                filter_key: [mso.sent],
            }

            operations = [
                dict(op='add', path='/templates/{template}/contracts/-'.format(template=template), value=payload),
            ]

        elif filter_idx is None:
            # Filter does not exist, so we have to add it
            operations = [
                dict(
                    op='add',
                    path='/templates/{template}/contracts/{contract}/{filter_key}/-'.format(
                        template=template,
                        contract=contract,
                        filter_key=filter_key,
                    ),
                    value=mso.sent,
                ),
            ]

        else:
            # FIXME: Updating based on index is DANGEROUS
            # Filter exists, we have to update it
            operations = [
                dict(
                    op='replace',
                    path='/templates/{template}/contracts/{contract}/{filter_key}/{filter_idx}'.format(
                        template=template,
                        contract=contract,
                        filter_key=filter_key,
                        filter_idx=filter_idx,
                    ),
                    value=mso.sent,
                ),
            ]

        if not module.check_mode:
            mso.request(path, method='PATCH', data=operations)

    mso.exit_json()


if __name__ == "__main__":
    main()
