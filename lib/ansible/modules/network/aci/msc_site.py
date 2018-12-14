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
module: msc_site
short_description: Manage sites
description:
- Manage sites on Cisco ACI Multi-Site.
author:
- Dag Wieers (@dagwieers)
version_added: '2.8'
options:
  apic_password:
    description:
    - The password for the APICs.
    type: str
    required: yes
  apic_site_id:
    description:
    - The site ID of the APICs.
    type: str
    required: yes
  apic_username:
    description:
    - The username for the APICs.
    type: str
    required: yes
    default: admin
  site_id:
    description:
    - The ID of the site.
    type: str
    required: yes
  site:
    description:
    - The name of the site.
    type: str
    required: yes
    aliases: [ name, site_name ]
  labels:
    description:
    - The labels for this site.
    type: list
  urls:
    description:
    - A list of URLs to reference the APICs.
    type: list
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    type: str
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment: msc
'''

EXAMPLES = r'''
- name: Add a new site
  msc_site:
    host: msc_host
    username: admin
    password: SomeSecretPassword
    site: north_europe
    site_id: 101
    description: North European Datacenter
    state: present
  delegate_to: localhost

- name: Remove a site
  msc_site:
    host: msc_host
    username: admin
    password: SomeSecretPassword
    site: north_europe
    state: absent
  delegate_to: localhost

- name: Query a site
  msc_site:
    host: msc_host
    username: admin
    password: SomeSecretPassword
    site: north_europe
    state: query
  delegate_to: localhost
  register: query_result

- name: Query all sites
  msc_site:
    host: msc_host
    username: admin
    password: SomeSecretPassword
    state: query
  delegate_to: localhost
  register: query_result
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.aci.msc import MSCModule, msc_argument_spec, issubset


def main():
    argument_spec = msc_argument_spec()
    argument_spec.update(
        apic_password=dict(type='str', no_log=True),
        apic_site_id=dict(type='str'),
        apic_username=dict(type='str', default='admin'),
        labels=dict(type='list'),
        site=dict(type='str', required=False, aliases=['name', 'site_name']),
        site_id=dict(type='str', required=False),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
        urls=dict(type='list'),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['site']],
            ['state', 'present', ['apic_site_id', 'site']],
        ],
    )

    apic_username = module.params['apic_username']
    apic_password = module.params['apic_password']
    apic_site_id = module.params['apic_site_id']
    site = module.params['site']
    site_id = module.params['site_id']
    state = module.params['state']
    urls = module.params['urls']

    msc = MSCModule(module)

    path = 'sites'

    # Query for msc.existing object(s)
    if site_id is None and site is None:
        msc.existing = msc.query_objs(path)
    elif site_id is None:
        msc.existing = msc.get_obj(path, name=site)
        if msc.existing:
            site_id = msc.existing['id']
    elif site is None:
        msc.existing = msc.get_obj(path, id=site_id)
    else:
        msc.existing = msc.get_obj(path, id=site_id)
        existing_by_name = msc.get_obj(path, name=site)
        if existing_by_name and site_id != existing_by_name['id']:
            msc.fail_json(msg="Provided site '{0}' with id '{1}' does not match existing id '{2}'.".format(site, site_id, existing_by_name['id']))

    # If we found an existing object, continue with it
    if site_id:
        path = 'sites/{id}'.format(id=site_id)

    if state == 'query':
        pass

    elif state == 'absent':
        msc.previous = msc.existing
        if msc.existing:
            if module.check_mode:
                msc.existing = {}
            else:
                msc.existing = msc.request(path, method='DELETE')

    elif state == 'present':
        msc.previous = msc.existing

        msc.sanitize(dict(
            apicSiteId=apic_site_id,
            id=site_id,
            name=site,
            urls=urls,
            username=apic_username,
            password=apic_password,
        ), collate=True)

        if msc.existing:
            if not issubset(msc.sent, msc.existing):
                if module.check_mode:
                    msc.existing = msc.proposed
                else:
                    msc.request(path, method='PUT', data=msc.sent)
        else:
            if module.check_mode:
                msc.existing = msc.proposed
            else:
                msc.request(path, method='POST', data=msc.sent)

    msc.exit_json()


if __name__ == "__main__":
    main()
