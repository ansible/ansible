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
module: mso_schema_template_externalepg
short_description: Manage external EPGs in schema templates
description:
- Manage external EPGs in schema templates on Cisco ACI Multi-Site.
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
    required: yes
  externalepg:
    description:
    - The name of the external EPG to manage.
    type: str
    aliases: [ name ]
  display_name:
    description:
    - The name as displayed on the MSO web interface.
    type: str
  vrf:
    description:
    - The VRF associated to this ANP.
    type: dict
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
- name: Add a new external EPG
  mso_schema_template_externalepg:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    schema: Schema 1
    template: Template 1
    externalepg: External EPG 1
    state: present
  delegate_to: localhost

- name: Remove an external EPG
  mso_schema_template_externalepg:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    schema: Schema 1
    template: Template 1
    externalepg: external EPG1
    state: absent
  delegate_to: localhost

- name: Query a specific external EPGs
  mso_schema_template_externalepg:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    schema: Schema 1
    template: Template 1
    externalepg: external EPG1
    state: query
  delegate_to: localhost
  register: query_result

- name: Query all external EPGs
  mso_schema_template_externalepg:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    schema: Schema 1
    template: Template 1
    state: query
  delegate_to: localhost
  register: query_result
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.aci.mso import MSOModule, mso_argument_spec, mso_reference_spec, issubset


def main():
    argument_spec = mso_argument_spec()
    argument_spec.update(
        schema=dict(type='str', required=True),
        template=dict(type='str', required=True),
        externalepg=dict(type='str', aliases=['name']),  # This parameter is not required for querying all objects
        display_name=dict(type='str'),
        vrf=dict(type='dict', options=mso_reference_spec()),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['externalepg']],
            ['state', 'present', ['externalepg', 'vrf']],
        ],
    )

    schema = module.params['schema']
    template = module.params['template']
    externalepg = module.params['externalepg']
    display_name = module.params['display_name']
    vrf = module.params['vrf']
    state = module.params['state']

    mso = MSOModule(module)

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

    # Get external EPGs
    externalepgs = [e['name'] for e in schema_obj['templates'][template_idx]['externalEpgs']]

    if externalepg is not None and externalepg in externalepgs:
        externalepg_idx = externalepgs.index(externalepg)
        mso.existing = schema_obj['templates'][template_idx]['externalEpgs'][externalepg_idx]

    if state == 'query':
        if externalepg is None:
            mso.existing = schema_obj['templates'][template_idx]['externalEpgs']
        elif not mso.existing:
            mso.fail_json(msg="External EPG '{externalepg}' not found".format(externalepg=externalepg))
        mso.exit_json()

    eepgs_path = '/templates/{0}/externalEpgs'.format(template)
    eepg_path = '/templates/{0}/externalEpgs/{1}'.format(template, externalepg)
    ops = []

    mso.previous = mso.existing
    if state == 'absent':
        if mso.existing:
            mso.sent = mso.existing = {}
            ops.append(dict(op='remove', path=eepg_path))

    elif state == 'present':
        vrf_ref = mso.make_reference(vrf, 'vrf', schema_id, template)

        if display_name is None and not mso.existing:
            display_name = externalepg

        payload = dict(
            name=externalepg,
            displayName=display_name,
            vrfRef=vrf_ref,
            # FIXME
            subnets=[],
            contractRelationships=[],
        )

        mso.sanitize(payload, collate=True)

        if mso.existing:
            ops.append(dict(op='replace', path=eepg_path, value=mso.sent))
        else:
            ops.append(dict(op='add', path=eepgs_path + '/-', value=mso.sent))

        mso.existing = mso.proposed

    if not module.check_mode:
        mso.request(schema_path, method='PATCH', data=ops)

    mso.exit_json()


if __name__ == "__main__":
    main()
