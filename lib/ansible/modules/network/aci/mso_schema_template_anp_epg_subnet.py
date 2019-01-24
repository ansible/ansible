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
module: mso_schema_template_anp_epg_subnet
short_description: Manage EPG subnets in schema templates
description:
- Manage EPG subnets in schema templates on Cisco ACI Multi-Site.
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
    type: list
  anp:
    description:
    - The name of the ANP.
    type: str
  epg:
    description:
    - The name of the EPG to manage.
    type: str
  ip:
    description:
    - The IP range in CIDR notation.
    type: str
    required: true
  description:
    description:
    - The description of this subnet.
    type: str
  scope:
    description:
    - The scope of the subnet.
    type: str
    choices: [ private, public ]
  shared:
    description:
    - Whether this subnet is shared between VRFs.
    type: bool
  no_default_gateway:
    description:
    - Whether this subnet has a default gateway.
    type: bool
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
- name: Add a new subnet to an EPG
  mso_schema_template_anp_subnet:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    schema: Schema 1
    template: Template 1
    anp: ANP 1
    epg: EPG 1
    ip: 10.0.0.0/24
    state: present
  delegate_to: localhost

- name: Remove an EPG
  mso_schema_template_anp_epg:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    schema: Schema 1
    template: Template 1
    anp: ANP 1
    epg: EPG 1
    ip: 10.0.0.0/24
    state: absent
  delegate_to: localhost

- name: Query a specific EPG
  mso_schema_template_anp_epg:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    schema: Schema 1
    template: Template 1
    anp: ANP 1
    epg: EPG 1
    ip: 10.0.0.0/24
    state: query
  delegate_to: localhost
  register: query_result

- name: Query all EPGs
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
from ansible.module_utils.network.aci.mso import MSOModule, mso_argument_spec, mso_reference_spec, mso_subnet_spec


def main():
    argument_spec = mso_argument_spec()
    argument_spec.update(
        schema=dict(type='str', required=True),
        template=dict(type='str', required=True),
        anp=dict(type='str', required=True),
        epg=dict(type='str', required=True),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )
    argument_spec.update(mso_subnet_spec())

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['ip']],
            ['state', 'present', ['ip']],
        ],
    )

    schema = module.params['schema']
    template = module.params['template']
    anp = module.params['anp']
    epg = module.params['epg']
    ip = module.params['ip']
    description = module.params['description']
    scope = module.params['scope']
    shared = module.params['shared']
    no_default_gateway = module.params['no_default_gateway']
    state = module.params['state']

    mso = MSOModule(module)

    # Get schema_id
    schema_obj = mso.get_obj('schemas', displayName=schema)
    if schema_obj:
        schema_id = schema_obj['id']
    else:
        mso.fail_json(msg="Provided schema '{0}' does not exist".format(schema))

    path = 'schemas/{id}'.format(id=schema_id)

    # Get template
    templates = [t['name'] for t in schema_obj['templates']]
    if template not in templates:
        mso.fail_json(msg="Provided template '{template}' does not exist. Existing templates: {templates}".format(template=template,
                                                                                                                  templates=', '.join(templates)))
    template_idx = templates.index(template)

    # Get ANP
    anps = [a['name'] for a in schema_obj['templates'][template_idx]['anps']]
    if anp not in anps:
        mso.fail_json(msg="Provided anp '{anp}' does not exist. Existing anps: {anps}".format(anp=anp, anps=', '.join(anps)))
    anp_idx = anps.index(anp)

    # Get EPG
    epgs = [e['name'] for e in schema_obj['templates'][template_idx]['anps'][anp_idx]['epgs']]
    if epg not in epgs:
        mso.fail_json(msg="Provided epg '{epg}' does not exist. Existing epgs: {epgs}".format(epg=epg, epgs=', '.join(epgs)))
    epg_idx = epgs.index(epg)

    # Get Subnet
    subnets = [s['ip'] for s in schema_obj['templates'][template_idx]['anps'][anp_idx]['epgs'][epg_idx]['subnets']]
    if ip in subnets:
        ip_idx = subnets.index(ip)
        # FIXME: Forced to use index here
        mso.existing = schema_obj['templates'][template_idx]['anps'][anp_idx]['epgs'][epg_idx]['subnets'][ip_idx]

    if state == 'query':
        if ip is None:
            mso.existing = schema_obj['templates'][template_idx]['anps'][anp_idx]['epgs'][epg_idx]['subnets']
        elif not mso.existing:
            mso.fail_json(msg="Subnet '{ip}' not found".format(ip=ip))
        mso.exit_json()

    mso.previous = mso.existing
    if state == 'absent':
        if mso.existing:
            mso.sent = mso.existing = {}
            operation = [dict(
                op='remove',
                # FIXME: Forced to use index here
                path='/templates/{template}/anps/{anp}/epgs/{epg}/subnets/{ip}'.format(template=template, anp=anp, epg=epg, ip=ip_idx),
            )]
            if not module.check_mode:
                mso.request(path, method='PATCH', data=operation)

    elif state == 'present':
        if description is None and not mso.existing:
            description = ip
        if scope is None and not mso.existing:
            scope = 'private'
        if shared is None and not mso.existing:
            shared = False
        if no_default_gateway is None and not mso.existing:
            no_default_gateway = False

        payload = dict(
            ip=ip,
            description=description,
            scope=scope,
            shared=shared,
            noDefaultGateway=no_default_gateway,
        )

        mso.sanitize(payload, collate=True)

        if mso.existing:
            operation = [dict(
                op='replace',
                # FIXME: Forced to use index here
                path='/templates/{template}/anps/{anp}/epgs/{epg}/subnets/{ip}'.format(template=template, anp=anp, epg=epg, ip=ip_idx),
                value=mso.sent,
            )]
        else:
            operation = [dict(
                op='add',
                path='/templates/{template}/anps/{anp}/epgs/{epg}/subnets/-'.format(template=template, anp=anp, epg=epg),
                value=mso.sent,
            )]

        mso.existing = mso.proposed
        if not module.check_mode:
            mso.request(path, method='PATCH', data=operation)

    mso.exit_json()


if __name__ == "__main__":
    main()
