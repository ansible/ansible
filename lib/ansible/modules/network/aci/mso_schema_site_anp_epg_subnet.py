#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: mso_schema_site_anp_epg_subnet
short_description: Manage site-local EPG subnets in schema template
description:
- Manage site-local EPG subnets in schema template on Cisco ACI Multi-Site.
author:
- Dag Wieers (@dagwieers)
version_added: '2.8'
options:
  schema:
    description:
    - The name of the schema.
    type: str
    required: yes
  site:
    description:
    - The name of the site.
    type: str
    required: yes
  template:
    description:
    - The name of the template.
    type: str
    required: yes
  anp:
    description:
    - The name of the ANP.
    type: str
  epg:
    description:
    - The name of the EPG.
    type: str
  subnet:
    description:
    - The IP range in CIDR notation.
    type: str
    required: true
    aliases: [ ip ]
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
notes:
- The ACI MultiSite PATCH API has a deficiency requiring some objects to be referenced by index.
  This can cause silent corruption on concurrent access when changing/removing on object as
  the wrong object may be referenced. This module is affected by this deficiency.
seealso:
- module: mso_schema_site_anp_epg
- module: mso_schema_template_anp_epg_subnet
extends_documentation_fragment: mso
'''

EXAMPLES = r'''
- name: Add a new subnet to a site EPG
  mso_schema_site_anp_epg_subnet:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    schema: Schema1
    site: Site1
    template: Template1
    anp: ANP1
    epg: EPG1
    subnet: 10.0.0.0/24
    state: present
  delegate_to: localhost

- name: Remove a subnet from a site EPG
  mso_schema_site_anp_epg_subnet:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    schema: Schema1
    site: Site1
    template: Template1
    anp: ANP1
    epg: EPG1
    subnet: 10.0.0.0/24
    state: absent
  delegate_to: localhost

- name: Query a specific site EPG subnet
  mso_schema_site_anp_epg_subnet:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    schema: Schema1
    site: Site1
    template: Template1
    anp: ANP1
    epg: EPG1
    subnet: 10.0.0.0/24
    state: query
  delegate_to: localhost
  register: query_result

- name: Query all site EPG subnets
  mso_schema_site_anp_epg_subnet:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    schema: Schema1
    site: Site1
    template: Template1
    anp: ANP1
    state: query
  delegate_to: localhost
  register: query_result
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.aci.mso import MSOModule, mso_argument_spec, mso_subnet_spec, issubset


def main():
    argument_spec = mso_argument_spec()
    argument_spec.update(
        schema=dict(type='str', required=True),
        site=dict(type='str', required=True),
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
            ['state', 'absent', ['subnet']],
            ['state', 'present', ['subnet']],
        ],
    )

    schema = module.params['schema']
    site = module.params['site']
    template = module.params['template']
    anp = module.params['anp']
    epg = module.params['epg']
    subnet = module.params['subnet']
    description = module.params['description']
    scope = module.params['scope']
    shared = module.params['shared']
    no_default_gateway = module.params['no_default_gateway']
    state = module.params['state']

    mso = MSOModule(module)

    # Get schema_id
    schema_obj = mso.get_obj('schemas', displayName=schema)
    if not schema_obj:
        mso.fail_json(msg="Provided schema '{0}' does not exist".format(schema))

    schema_path = 'schemas/{id}'.format(**schema_obj)
    schema_id = schema_obj['id']

    # Get site
    site_id = mso.lookup_site(site)

    # Get site_idx
    sites = [(s['siteId'], s['templateName']) for s in schema_obj['sites']]
    if (site_id, template) not in sites:
        mso.fail_json(msg="Provided site/template '{0}-{1}' does not exist. Existing sites/templates: {2}".format(site, template, ', '.join(sites)))

    # Schema-access uses indexes
    site_idx = sites.index((site_id, template))
    # Path-based access uses site_id-template
    site_template = '{0}-{1}'.format(site_id, template)

    # Get ANP
    anp_ref = mso.anp_ref(schema_id=schema_id, template=template, anp=anp)
    anps = [a['anpRef'] for a in schema_obj['sites'][site_idx]['anps']]
    if anp_ref not in anps:
        mso.fail_json(msg="Provided anp '{0}' does not exist. Existing anps: {1}".format(anp, ', '.join(anps)))
    anp_idx = anps.index(anp_ref)

    # Get EPG
    epg_ref = mso.epg_ref(schema_id=schema_id, template=template, anp=anp, epg=epg)
    epgs = [e['epgRef'] for e in schema_obj['sites'][site_idx]['anps'][anp_idx]['epgs']]
    if epg_ref not in epgs:
        mso.fail_json(msg="Provided epg '{0}' does not exist. Existing epgs: {1}".format(epg, ', '.join(epgs)))
    epg_idx = epgs.index(epg_ref)

    # Get Subnet
    subnets = [s['ip'] for s in schema_obj['sites'][site_idx]['anps'][anp_idx]['epgs'][epg_idx]['subnets']]
    if subnet in subnets:
        subnet_idx = subnets.index(subnet)
        # FIXME: Changes based on index are DANGEROUS
        subnet_path = '/sites/{0}/anps/{1}/epgs/{2}/subnets/{3}'.format(site_template, anp, epg, subnet_idx)
        mso.existing = schema_obj['sites'][site_idx]['anps'][anp_idx]['epgs'][epg_idx]['subnets'][subnet_idx]

    if state == 'query':
        if subnet is None:
            mso.existing = schema_obj['sites'][site_idx]['anps'][anp_idx]['epgs'][epg_idx]['subnets']
        elif not mso.existing:
            mso.fail_json(msg="Subnet '{subnet}' not found".format(subnet=subnet))
        mso.exit_json()

    subnets_path = '/sites/{0}/anps/{1}/epgs/{2}/subnets'.format(site_template, anp, epg)
    ops = []

    mso.previous = mso.existing
    if state == 'absent':
        if mso.existing:
            mso.sent = mso.existing = {}
            ops.append(dict(op='remove', path=subnet_path))

    elif state == 'present':
        if not mso.existing:
            if description is None:
                description = subnet
            if scope is None:
                scope = 'private'
            if shared is None:
                shared = False
            if no_default_gateway is None:
                no_default_gateway = False

        payload = dict(
            ip=subnet,
            description=description,
            scope=scope,
            shared=shared,
            noDefaultGateway=no_default_gateway,
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
