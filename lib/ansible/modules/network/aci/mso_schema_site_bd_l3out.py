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
module: mso_schema_site_bd_l3out
short_description: Manage site-local BD l3out's in schema template
description:
- Manage site-local BDs l3out's in schema template on Cisco ACI Multi-Site.
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
  bd:
    description:
    - The name of the BD.
    type: str
    aliases: [ name ]
  l3out:
    description:
    - The name of the l3out.
    type: str
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    type: str
    choices: [ absent, present, query ]
    default: present
seealso:
- module: mso_schema_site_bd
- module: mso_schema_template_bd
extends_documentation_fragment: mso
'''

EXAMPLES = r'''
- name: Add a new site BD l3out
  mso_schema_site_bd_l3out:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    schema: Schema1
    site: Site1
    template: Template1
    bd: BD1
    l3out: L3out1
    state: present
  delegate_to: localhost

- name: Remove a site BD l3out
  mso_schema_site_bd_l3out:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    schema: Schema1
    site: Site1
    template: Template1
    bd: BD1
    l3out: L3out1
    state: absent
  delegate_to: localhost

- name: Query a specific site BD l3out
  mso_schema_site_bd_l3out:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    schema: Schema1
    site: Site1
    template: Template1
    bd: BD1
    l3out: L3out1
    state: query
  delegate_to: localhost
  register: query_result

- name: Query all site BD l3outs
  mso_schema_site_bd_l3out:
    host: mso_host
    username: admin
    password: SomeSecretPassword
    schema: Schema1
    site: Site1
    template: Template1
    bd: BD1
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
        bd=dict(type='str', required=True),
        l3out=dict(type='str', aliases=['name']),  # This parameter is not required for querying all objects
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['l3out']],
            ['state', 'present', ['l3out']],
        ],
    )

    schema = module.params['schema']
    site = module.params['site']
    template = module.params['template']
    bd = module.params['bd']
    l3out = module.params['l3out']
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

    # Get BD
    bd_ref = mso.bd_ref(schema_id=schema_id, template=template, bd=bd)
    bds = [v['bdRef'] for v in schema_obj['sites'][site_idx]['bds']]
    if bd_ref not in bds:
        mso.fail_json(msg="Provided BD '{0}' does not exist. Existing BDs: {1}".format(bd, ', '.join(bds)))
    bd_idx = bds.index(bd_ref)

    # Get L3out
    l3outs = schema_obj['sites'][site_idx]['bds'][bd_idx]['l3Outs']
    if l3out is not None and l3out in l3outs:
        l3out_idx = l3outs.index(l3out)
        l3out_path = '/sites/{0}/bds/{1}/l3Outs/{2}'.format(site_template, bd, l3out_idx)
        mso.existing = schema_obj['sites'][site_idx]['bds'][bd_idx]['l3Outs'][l3out_idx]

    if state == 'query':
        if l3out is None:
            mso.existing = schema_obj['sites'][site_idx]['bds'][bd_idx]['l3Outs']
        elif not mso.existing:
            mso.fail_json(msg="L3out '{l3out}' not found".format(l3out=l3out))
        mso.exit_json()

    l3outs_path = '/sites/{0}/bds/{1}/l3Outs'.format(site_template, bd)
    ops = []

    mso.previous = mso.existing
    if state == 'absent':
        if mso.existing:
            mso.sent = mso.existing = {}
            ops.append(dict(op='remove', path=l3out_path))

    elif state == 'present':
        mso.sent = l3out
        if not mso.existing:
            ops.append(dict(op='add', path=l3outs_path + '/-', value=l3out))

        mso.existing = mso.sent

    if not module.check_mode:
        mso.request(schema_path, method='PATCH', data=ops)

    mso.exit_json()


if __name__ == "__main__":
    main()
