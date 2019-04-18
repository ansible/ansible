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
module: mso_schema_template_anp_epg_contract
short_description: Manage EPG contracts in schema templates
description:
- Manage EPG contracts in schema templates on Cisco ACI Multi-Site.
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
    - The name of the template to change.
    type: str
    required: yes
  anp:
    description:
    - The name of the ANP.
    type: str
    required: yes
  epg:
    description:
    - The name of the EPG to manage.
    type: str
    required: yes
  contract:
    description:
    - A contract associated to this EPG.
    type: dict
    suboptions:
      name:
        description:
        - The name of the COntract to associate with.
        required: true
        type: str
      schema:
        description:
        - The schema that defines the referenced BD.
        - If this parameter is unspecified, it defaults to the current schema.
        type: str
      template:
        description:
        - The template that defines the referenced BD.
        type: str
      type:
        description:
        - The type of contract.
        type: str
        required: true
        choices: [ consumer, provider ]
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    type: str
    choices: [ absent, present, query ]
    default: present
seealso:
- module: mso_schema_template_anp_epg
- module: mso_schema_template_contract_filter
extends_documentation_fragment: mso
'''

EXAMPLES = r'''
- name: Add a contract to an EPG
  mso_schema_template_anp_epg:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    schema: Schema 1
    template: Template 1
    anp: ANP 1
    epg: EPG 1
    contract:
      name: Contract 1
      type: consumer
    state: present
  delegate_to: localhost

- name: Remove a Contract
  mso_schema_template_anp_epg:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    schema: Schema 1
    template: Template 1
    anp: ANP 1
    epg: EPG 1
    contract:
      name: Contract 1
    state: absent
  delegate_to: localhost

- name: Query a specific Contract
  mso_schema_template_anp_epg:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    schema: Schema 1
    template: Template 1
    anp: ANP 1
    epg: EPG 1
    contract:
      name: Contract 1
    state: query
  delegate_to: localhost
  register: query_result

- name: Query all Contracts
  mso_schema_template_anp_epg:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    schema: Schema 1
    template: Template 1
    anp: ANP 1
    state: query
  delegate_to: localhost
  register: query_result
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.aci.mso import MSOModule, mso_argument_spec, mso_contractref_spec, issubset


def main():
    argument_spec = mso_argument_spec()
    argument_spec.update(
        schema=dict(type='str', required=True),
        template=dict(type='str', required=True),
        anp=dict(type='str', required=True),
        epg=dict(type='str', required=True),
        contract=dict(type='dict', options=mso_contractref_spec()),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['contract']],
            ['state', 'present', ['contract']],
        ],
    )

    schema = module.params['schema']
    template = module.params['template']
    anp = module.params['anp']
    epg = module.params['epg']
    contract = module.params['contract']
    state = module.params['state']

    mso = MSOModule(module)

    if contract:
        if contract.get('schema') is None:
            contract['schema'] = schema
        contract['schema_id'] = mso.lookup_schema(contract['schema'])
        if contract.get('template') is None:
            contract['template'] = template

    # Get schema_id
    schema_obj = mso.get_obj('schemas', displayName=schema)
    if schema_obj:
        schema_id = schema_obj['id']
    else:
        mso.fail_json(msg="Provided schema '{0}' does not exist".format(schema))

    schema_path = 'schemas/{id}'.format(**schema_obj)

    # Get template
    templates = [t['name'] for t in schema_obj['templates']]
    if template not in templates:
        mso.fail_json(msg="Provided template '{0}' does not exist. Existing templates: {1}".format(template, ', '.join(templates)))
    template_idx = templates.index(template)

    # Get ANP
    anps = [a['name'] for a in schema_obj['templates'][template_idx]['anps']]
    if anp not in anps:
        mso.fail_json(msg="Provided anp '{0}' does not exist. Existing anps: {1}".format(anp, ', '.join(anps)))
    anp_idx = anps.index(anp)

    # Get EPG
    epgs = [e['name'] for e in schema_obj['templates'][template_idx]['anps'][anp_idx]['epgs']]
    if epg not in epgs:
        mso.fail_json(msg="Provided epg '{epg}' does not exist. Existing epgs: {epgs}".format(epg=epg, epgs=', '.join(epgs)))
    epg_idx = epgs.index(epg)

    # Get Contract
    if contract:
        contracts = [(c['contractRef'],
                      c['relationshipType']) for c in schema_obj['templates'][template_idx]['anps'][anp_idx]['epgs'][epg_idx]['contractRelationships']]
        contract_ref = mso.contract_ref(**contract)
        if (contract_ref, contract['type']) in contracts:
            contract_idx = contracts.index((contract_ref, contract['type']))
            # FIXME: Changes based on index are DANGEROUS
            contract_path = '/templates/{0}/anps/{1}/epgs/{2}/contractRelationships/{3}'.format(template, anp, epg, contract_idx)
            mso.existing = schema_obj['templates'][template_idx]['anps'][anp_idx]['epgs'][epg_idx]['contractRelationships'][contract_idx]

    if state == 'query':
        if not contract:
            mso.existing = schema_obj['templates'][template_idx]['anps'][anp_idx]['epgs'][epg_idx]['contractRelationships']
        elif not mso.existing:
            mso.fail_json(msg="Contract '{0}' not found".format(contract_ref))
        mso.exit_json()

    contracts_path = '/templates/{0}/anps/{1}/epgs/{2}/contractRelationships'.format(template, anp, epg)
    ops = []

    mso.previous = mso.existing
    if state == 'absent':
        if mso.existing:
            mso.sent = mso.existing = {}
            ops.append(dict(op='remove', path=contract_path))

    elif state == 'present':
        payload = dict(
            relationshipType=contract['type'],
            contractRef=dict(
                contractName=contract['name'],
                templateName=contract['template'],
                schemaId=contract['schema_id'],
            ),
        )

        mso.sanitize(payload, collate=True)

        if mso.existing:
            ops.append(dict(op='replace', path=contract_path, value=mso.sent))
        else:
            ops.append(dict(op='add', path=contracts_path + '/-', value=mso.sent))

        mso.existing = mso.proposed

    if not module.check_mode:
        mso.request(schema_path, method='PATCH', data=ops)

    mso.exit_json()


if __name__ == "__main__":
    main()
