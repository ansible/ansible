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
module: mso_schema_template_external_epg_subnet
short_description: Manage External EPG subnets in schema templates
description:
- Manage External EPG subnets in schema templates on Cisco ACI Multi-Site.
author:
- Devarshi Shah (@devarshishah3)
version_added: '2.10'
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
  external_epg:
    description:
    - The name of the External EPG to manage.
    type: str
    required: yes
  subnet:
    description:
    - The IP range in CIDR notation.
    type: str
    required: true
  scope:
    description:
    - The scope of the subnet.
    type: list
  aggregate:
    description:
    - The aggregate option for the subnet.
    type: list
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    type: str
    choices: [ absent, present, query ]
    default: present
notes:
- Due to restrictions of the MSO REST API concurrent modifications to EPG subnets can be dangerous and corrupt data.
extends_documentation_fragment: mso
'''

EXAMPLES = r'''
- name: Add a new subnet to an External EPG
  mso_schema_template_external_epg_subnet:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    schema: Schema 1
    template: Template 1
    external_epg: EPG 1
    subnet: 10.0.0.0/24
    state: present
  delegate_to: localhost

- name: Remove a subnet from an External EPG
  mso_schema_template_external_epg_subnet:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    schema: Schema 1
    template: Template 1
    external_epg: EPG 1
    subnet: 10.0.0.0/24
    state: absent
  delegate_to: localhost

- name: Query a specific External EPG subnet
  mso_schema_template_external_epg_subnet:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    schema: Schema 1
    template: Template 1
    external_epg: EPG 1
    subnet: 10.0.0.0/24
    state: query
  delegate_to: localhost
  register: query_result

- name: Query all External EPGs subnets
  mso_schema_template_external_epg_subnet:
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
from ansible.module_utils.network.aci.mso import MSOModule, mso_argument_spec, mso_reference_spec, mso_subnet_spec


def main():
    argument_spec = mso_argument_spec()
    argument_spec.update(
        schema=dict(type='str', required=True),
        template=dict(type='str', required=True),
        external_epg=dict(type='str', required=True),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
        subnet=dict(type='str', required=True),
        scope=dict(type='list', default=[]),
        aggregate=dict(type='list', default=[]),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['subnet']],
            ['state', 'present', ['subnet']],
        ],
    )

    schema = module.params['schema']
    template = module.params['template']
    external_epg = module.params['external_epg']
    subnet = module.params['subnet']
    scope = module.params['scope']
    aggregate = module.params['aggregate']
    state = module.params['state']

    mso = MSOModule(module)

    # Get schema
    schema_obj = mso.get_obj('schemas', displayName=schema)
    if not schema_obj:
        mso.fail_json(msg="Provided schema '{0}' does not exist".format(schema))

    schema_path = 'schemas/{id}'.format(**schema_obj)

    # Get template
    templates = [t['name'] for t in schema_obj['templates']]
    if template not in templates:
        mso.fail_json(msg="Provided template '{template}' does not exist. Existing templates: {templates}".format(template=template,
                                                                                                                  templates=', '.join(templates)))
    template_idx = templates.index(template)

    # Get EPG
    external_epgs = [e['name'] for e in schema_obj['templates'][template_idx]['externalEpgs']]
    if external_epg not in external_epgs:
        mso.fail_json(msg="Provided External EPG '{epg}' does not exist. Existing epgs: {epgs}".format(epg=external_epg, epgs=', '.join(external_epgs)))
    epg_idx = external_epgs.index(external_epg)

    # Get Subnet
    subnets = [s['ip'] for s in schema_obj['templates'][template_idx]['externalEpgs'][epg_idx]['subnets']]
    if subnet in subnets:
        subnet_idx = subnets.index(subnet)
        # FIXME: Changes based on index are DANGEROUS
        subnet_path = '/templates/{0}/externalEpgs/{1}/subnets/{2}'.format(template, external_epg, subnet_idx)
        mso.existing = schema_obj['templates'][template_idx]['externalEpgs'][epg_idx]['subnets'][subnet_idx]

    if state == 'query':
        if subnet is None:
            mso.existing = schema_obj['templates'][template_idx]['externalEpgs'][epg_idx]['subnets']
        elif not mso.existing:
            mso.fail_json(msg="Subnet '{subnet}' not found".format(subnet=subnet))
        mso.exit_json()

    subnets_path = '/templates/{0}/externalEpgs/{1}/subnets'.format(template, external_epg)
    ops = []

    mso.previous = mso.existing
    if state == 'absent':
        if mso.existing:
            mso.existing = {}
            ops.append(dict(op='remove', path=subnet_path))

    elif state == 'present':
        payload = dict(
            ip=subnet,
            scope=scope,
            aggregate=aggregate,
        )

        mso.sanitize(payload, collate=True)

        if mso.existing:
            ops.append(dict(op='replace', path=subnet_path, value=mso.sent))
        else:
            ops.append(dict(op='add', path=subnets_path + '/-', value=mso.sent))

        mso.existing = mso.proposed

    if not module.check_mode:
        mso.request(schema_path, method='PATCH', data=ops)

    mso.exit_json()


if __name__ == "__main__":
    main()
