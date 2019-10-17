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
module: mso_schema_site_anp_epg_staticleaf
short_description: Manage site-local EPG static leafs in schema template
description:
- Manage site-local EPG static leafs in schema template on Cisco ACI Multi-Site.
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
  pod:
    description:
    - The pod of the static leaf.
    type: str
  leaf:
    description:
    - The path of the static leaf.
    type: str
    aliases: [ name ]
  vlan:
    description:
    - The VLAN id of the static leaf.
    type: int
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
- module: mso_schema_template_anp_epg
extends_documentation_fragment: mso
'''

EXAMPLES = r'''
- name: Add a new static leaf to a site EPG
  mso_schema_site_anp_epg_staticleaf:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    schema: Schema1
    site: Site1
    template: Template1
    anp: ANP1
    epg: EPG1
    leaf: Leaf1
    vlan: 123
    state: present
  delegate_to: localhost

- name: Remove a static leaf from a site EPG
  mso_schema_site_anp_epg_staticleaf:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    schema: Schema1
    site: Site1
    template: Template1
    anp: ANP1
    epg: EPG1
    leaf: Leaf1
    state: absent
  delegate_to: localhost

- name: Query a specific site EPG static leaf
  mso_schema_site_anp_epg_staticleaf:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    schema: Schema1
    site: Site1
    template: Template1
    anp: ANP1
    epg: EPG1
    leaf: Leaf1
    state: query
  delegate_to: localhost
  register: query_result

- name: Query all site EPG static leafs
  mso_schema_site_anp_epg_staticleaf:
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
from ansible.module_utils.network.aci.mso import MSOModule, mso_argument_spec


def main():
    argument_spec = mso_argument_spec()
    argument_spec.update(
        schema=dict(type='str', required=True),
        site=dict(type='str', required=True),
        template=dict(type='str', required=True),
        anp=dict(type='str', required=True),
        epg=dict(type='str', required=True),
        pod=dict(type='str'),  # This parameter is not required for querying all objects
        leaf=dict(type='str', aliases=['name']),
        vlan=dict(type='int'),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['pod', 'leaf', 'vlan']],
            ['state', 'present', ['pod', 'leaf', 'vlan']],
        ],
    )

    schema = module.params['schema']
    site = module.params['site']
    template = module.params['template']
    anp = module.params['anp']
    epg = module.params['epg']
    pod = module.params['pod']
    leaf = module.params['leaf']
    vlan = module.params['vlan']
    state = module.params['state']

    leafpath = 'topology/{0}/node-{1}'.format(pod, leaf)

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

    # Get Leaf
    leafs = [(l['path'], l['portEncapVlan']) for l in schema_obj['sites'][site_idx]['anps'][anp_idx]['epgs'][epg_idx]['staticLeafs']]
    if (leafpath, vlan) in leafs:
        leaf_idx = leafs.index((leafpath, vlan))
        # FIXME: Changes based on index are DANGEROUS
        leaf_path = '/sites/{0}/anps/{1}/epgs/{2}/staticLeafs/{3}'.format(site_template, anp, epg, leaf_idx)
        mso.existing = schema_obj['sites'][site_idx]['anps'][anp_idx]['epgs'][epg_idx]['staticLeafs'][leaf_idx]

    if state == 'query':
        if leaf is None or vlan is None:
            mso.existing = schema_obj['sites'][site_idx]['anps'][anp_idx]['epgs'][epg_idx]['staticLeafs']
        elif not mso.existing:
            mso.fail_json(msg="Static leaf '{leaf}/{vlan}' not found".format(leaf=leaf, vlan=vlan))
        mso.exit_json()

    leafs_path = '/sites/{0}/anps/{1}/epgs/{2}/staticLeafs'.format(site_template, anp, epg)
    ops = []

    mso.previous = mso.existing
    if state == 'absent':
        if mso.existing:
            mso.sent = mso.existing = {}
            ops.append(dict(op='remove', path=leaf_path))

    elif state == 'present':
        payload = dict(
            path=leafpath,
            portEncapVlan=vlan,
        )

        mso.sanitize(payload, collate=True)

        if mso.existing:
            ops.append(dict(op='replace', path=leaf_path, value=mso.sent))
        else:
            ops.append(dict(op='add', path=leafs_path + '/-', value=mso.sent))

        mso.existing = mso.proposed

    if not module.check_mode:
        mso.request(schema_path, method='PATCH', data=ops)

    mso.exit_json()


if __name__ == "__main__":
    main()
