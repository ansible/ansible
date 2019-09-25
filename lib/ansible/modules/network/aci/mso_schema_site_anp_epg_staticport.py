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
module: mso_schema_site_anp_epg_staticport
short_description: Manage site-local EPG static ports in schema template
description:
- Manage site-local EPG static ports in schema template on Cisco ACI Multi-Site.
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
  type:
    description:
    - The path type of the static port
    type: str
    choices: [ port ]
    default: port
  pod:
    description:
    - The pod of the static port.
    type: str
  leaf:
    description:
    - The leaf of the static port.
    type: str
  path:
    description:
    - The path of the static port.
    type: str
  vlan:
    description:
    - The port encap VLAN id of the static port.
    type: int
  deployment_immediacy:
    description:
    - The deployment immediacy of the static port.
    - C(immediate) means B(Deploy immediate).
    - C(lazy) means B(deploy on demand).
    type: str
    choices: [ immediate, lazy ]
  mode:
    description:
    - The mode of the static port.
    - C(native) means B(Access (802.1p)).
    - C(regular) means B(Trunk).
    - C(untagged) means B(Access (untagged)).
    type: str
    choices: [ native, regular, untagged ]
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    type: str
    choices: [ absent, present, query ]
    default: present
seealso:
- module: mso_schema_site_anp_epg
- module: mso_schema_template_anp_epg
extends_documentation_fragment: mso
'''

EXAMPLES = r'''
- name: Add a new static port to a site EPG
  mso_schema_site_anp_epg_staticport:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    schema: Schema1
    site: Site1
    template: Template1
    anp: ANP1
    epg: EPG1
    type: port
    pod: pod-1
    leaf: 101
    path: eth1/1
    vlan: 126
    deployment_immediacy: immediate
    state: present
  delegate_to: localhost

- name: Remove a static port from a site EPG
  mso_schema_site_anp_epg_staticport:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    schema: Schema1
    site: Site1
    template: Template1
    anp: ANP1
    epg: EPG1
    type: port
    pod: pod-1
    leaf: 101
    path: eth1/1
    state: absent
  delegate_to: localhost

- name: Query a specific site EPG static port
  mso_schema_site_anp_epg_staticport:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    schema: Schema1
    site: Site1
    template: Template1
    anp: ANP1
    epg: EPG1
    type: port
    pod: pod-1
    leaf: 101
    path: eth1/1
    state: query
  delegate_to: localhost
  register: query_result

- name: Query all site EPG static ports
  mso_schema_site_anp_epg_staticport:
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
        type=dict(type='str', default='port', choices=['port']),
        pod=dict(type='str'),  # This parameter is not required for querying all objects
        leaf=dict(type='str'),  # This parameter is not required for querying all objects
        path=dict(type='str'),  # This parameter is not required for querying all objects
        vlan=dict(type='int'),  # This parameter is not required for querying all objects
        deployment_immediacy=dict(type='str', choices=['immediate', 'lazy']),
        mode=dict(type='str', choices=['native', 'regular', 'untagged']),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['type', 'pod', 'leaf', 'path', 'vlan']],
            ['state', 'present', ['type', 'pod', 'leaf', 'path', 'vlan']],
        ],
    )

    schema = module.params['schema']
    site = module.params['site']
    template = module.params['template']
    anp = module.params['anp']
    epg = module.params['epg']
    path_type = module.params['type']
    pod = module.params['pod']
    leaf = module.params['leaf']
    path = module.params['path']
    vlan = module.params['vlan']
    deployment_immediacy = module.params['deployment_immediacy']
    mode = module.params['mode']
    state = module.params['state']

    if path_type == 'port':
        portpath = 'topology/{0}/paths-{1}/pathep-[{2}]'.format(pod, leaf, path)

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
    portpaths = [p['path'] for p in schema_obj['sites'][site_idx]['anps'][anp_idx]['epgs'][epg_idx]['staticPorts']]
    if portpath in portpaths:
        portpath_idx = portpaths.index(portpath)
        # FIXME: Changes based on index are DANGEROUS
        port_path = '/sites/{0}/anps/{1}/epgs/{2}/staticPorts/{3}'.format(site_template, anp, epg, portpath_idx)
        mso.existing = schema_obj['sites'][site_idx]['anps'][anp_idx]['epgs'][epg_idx]['staticPorts'][portpath_idx]

    if state == 'query':
        if leaf is None or vlan is None:
            mso.existing = schema_obj['sites'][site_idx]['anps'][anp_idx]['epgs'][epg_idx]['staticPorts']
        elif not mso.existing:
            mso.fail_json(msg="Static port '{portpath}' not found".format(portpath=portpath))
        mso.exit_json()

    ports_path = '/sites/{0}/anps/{1}/epgs/{2}/staticPorts'.format(site_template, anp_idx, epg_idx)
    ops = []

    mso.previous = mso.existing
    if state == 'absent':
        if mso.existing:
            mso.sent = mso.existing = {}
            ops.append(dict(op='remove', path=port_path))

    elif state == 'present':
        if not mso.existing:
            if deployment_immediacy is None:
                deployment_immediacy = 'lazy'
            if mode is None:
                mode = 'untagged'

        payload = dict(
            deploymentImmediacy=deployment_immediacy,
            mode=mode,
            path=portpath,
            portEncapVlan=vlan,
            type=path_type,
        )

        mso.sanitize(payload, collate=True)

        if mso.existing:
            ops.append(dict(op='replace', path=port_path, value=mso.sent))
        else:
            ops.append(dict(op='add', path=ports_path + '/-', value=mso.sent))

        mso.existing = mso.proposed

    if not module.check_mode:
        mso.request(schema_path, method='PATCH', data=ops)

    mso.exit_json()


if __name__ == "__main__":
    main()
