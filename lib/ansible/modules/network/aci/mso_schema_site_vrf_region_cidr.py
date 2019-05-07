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
module: mso_schema_site_vrf_region_cidr
short_description: Manage site-local VRF region CIDRs in schema template
description:
- Manage site-local VRF region CIDRs in schema template on Cisco ACI Multi-Site.
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
  vrf:
    description:
    - The name of the VRF.
    type: str
  region:
    description:
    - The name of the region.
    type: str
  cidr:
    description:
    - The name of the region CIDR to manage.
    type: str
    aliases: [ ip ]
  primary:
    description:
    - Whether this is the primary CIDR.
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
- module: mso_schema_site_vrf_region
- module: mso_schema_site_vrf_region_cidr_subnet
- module: mso_schema_template_vrf
extends_documentation_fragment: mso
'''

EXAMPLES = r'''
- name: Add a new site VRF region CIDR
  mso_schema_template_vrf_region_cidr:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    schema: Schema1
    site: Site1
    template: Template1
    vrf: VRF1
    region: us-west-1
    cidr: 14.14.14.1/24
    state: present
  delegate_to: localhost

- name: Remove a site VRF region CIDR
  mso_schema_template_vrf_region_cidr:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    schema: Schema1
    site: Site1
    template: Template1
    vrf: VRF1
    region: us-west-1
    cidr: 14.14.14.1/24
    state: absent
  delegate_to: localhost

- name: Query a specific site VRF region CIDR
  mso_schema_template_vrf_region_cidr:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    schema: Schema1
    site: Site1
    template: Template1
    vrf: VRF1
    region: us-west-1
    cidr: 14.14.14.1/24
    state: query
  delegate_to: localhost
  register: query_result

- name: Query all site VRF region CIDR
  mso_schema_template_vrf_region_cidr:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    schema: Schema1
    site: Site1
    template: Template1
    vrf: VRF1
    region: us-west-1
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
        vrf=dict(type='str', required=True),
        region=dict(type='str', required=True),
        cidr=dict(type='str', aliases=['ip']),  # This parameter is not required for querying all objects
        primary=dict(type='bool'),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['cidr']],
            ['state', 'present', ['cidr']],
        ],
    )

    schema = module.params['schema']
    site = module.params['site']
    template = module.params['template']
    vrf = module.params['vrf']
    region = module.params['region']
    cidr = module.params['cidr']
    primary = module.params['primary']
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

    # Get VRF
    vrf_ref = mso.vrf_ref(schema_id=schema_id, template=template, vrf=vrf)
    vrfs = [v['vrfRef'] for v in schema_obj['sites'][site_idx]['vrfs']]
    if vrf_ref not in vrfs:
        mso.fail_json(msg="Provided vrf '{0}' does not exist. Existing vrfs: {1}".format(vrf, ', '.join(vrfs)))
    vrf_idx = vrfs.index(vrf_ref)

    # Get Region
    regions = [r['name'] for r in schema_obj['sites'][site_idx]['vrfs'][vrf_idx]['regions']]
    if region not in regions:
        mso.fail_json(msg="Provided region '{0}' does not exist. Existing regions: {1}".format(region, ', '.join(regions)))
    region_idx = regions.index(region)

    # Get CIDR
    cidrs = [c['ip'] for c in schema_obj['sites'][site_idx]['vrfs'][vrf_idx]['regions'][region_idx]['cidrs']]
    if cidr is not None and cidr in cidrs:
        cidr_idx = cidrs.index(cidr)
        # FIXME: Changes based on index are DANGEROUS
        cidr_path = '/sites/{0}/vrfs/{1}/regions/{2}/cidrs/{3}'.format(site_template, vrf, region, cidr_idx)
        mso.existing = schema_obj['sites'][site_idx]['vrfs'][vrf_idx]['regions'][region_idx]['cidrs'][cidr_idx]

    if state == 'query':
        if cidr is None:
            mso.existing = schema_obj['sites'][site_idx]['vrfs'][vrf_idx]['regions'][region_idx]['cidrs']
        elif not mso.existing:
            mso.fail_json(msg="CIDR IP '{cidr}' not found".format(cidr=cidr))
        mso.exit_json()

    cidrs_path = '/sites/{0}/vrfs/{1}/regions/{2}/cidrs'.format(site_template, vrf, region)
    ops = []

    mso.previous = mso.existing
    if state == 'absent':
        if mso.existing:
            mso.sent = mso.existing = {}
            ops.append(dict(op='remove', path=cidr_path))

    elif state == 'present':
        if not mso.existing:
            if primary is None:
                primary = False

        payload = dict(
            ip=cidr,
            primary=primary,
        )

        mso.sanitize(payload, collate=True)

        if mso.existing:
            ops.append(dict(op='replace', path=cidr_path, value=mso.sent))
        else:
            ops.append(dict(op='add', path=cidrs_path + '/-', value=mso.sent))

        mso.existing = mso.proposed

    if not module.check_mode:
        mso.request(schema_path, method='PATCH', data=ops)

    mso.exit_json()


if __name__ == "__main__":
    main()
