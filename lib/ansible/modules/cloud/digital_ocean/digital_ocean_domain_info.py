#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Ansible Project
# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


DOCUMENTATION = '''
---
module: digital_ocean_domain_info
short_description: Gather information about DigitalOcean Domains
description:
    - This module can be used to gather information about DigitalOcean provided Domains.
    - This module was called C(digital_ocean_domain_facts) before Ansible 2.9. The usage did not change.
author: "Abhijeet Kasurde (@Akasurde)"
version_added: "2.6"
options:
  domain_name:
    description:
     - Name of the domain to gather information for.
    required: false
requirements:
  - "python >= 2.6"
extends_documentation_fragment: digital_ocean.documentation
'''


EXAMPLES = '''
- name: Gather information about all domains
  digital_ocean_domain_info:
    oauth_token: "{{ oauth_token }}"

- name: Gather information about domain with given name
  digital_ocean_domain_info:
    oauth_token: "{{ oauth_token }}"
    domain_name: "example.com"

- name: Get ttl from domain
  digital_ocean_domain_info:
  register: resp_out
- set_fact:
    domain_ttl: "{{ item.ttl }}"
  loop: "{{ resp_out.data|json_query(name) }}"
  vars:
    name: "[?name=='example.com']"
- debug: var=domain_ttl
'''


RETURN = '''
data:
    description: DigitalOcean Domain information
    returned: success
    type: list
    sample: [
        {
            "domain_records": [
                {
                    "data": "ns1.digitalocean.com",
                    "flags": null,
                    "id": 37826823,
                    "name": "@",
                    "port": null,
                    "priority": null,
                    "tag": null,
                    "ttl": 1800,
                    "type": "NS",
                    "weight": null
                },
            ],
            "name": "myexample123.com",
            "ttl": 1800,
            "zone_file": "myexample123.com. IN SOA ns1.digitalocean.com. hostmaster.myexample123.com. 1520702984 10800 3600 604800 1800\n",
        },
    ]
'''

from traceback import format_exc
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.digital_ocean import DigitalOceanHelper
from ansible.module_utils._text import to_native


def core(module):
    domain_name = module.params.get('domain_name', None)
    rest = DigitalOceanHelper(module)
    domain_results = []

    if domain_name is not None:
        response = rest.get("domains/%s" % domain_name)
        status_code = response.status_code

        if status_code != 200:
            module.fail_json(msg="Failed to retrieve domain for DigitalOcean")

        resp_json = response.json
        domains = [resp_json['domain']]
    else:
        domains = rest.get_paginated_data(base_url="domains?", data_key_name='domains')

    for temp_domain in domains:
        temp_domain_dict = {
            "name": temp_domain['name'],
            "ttl": temp_domain['ttl'],
            "zone_file": temp_domain['zone_file'],
            "domain_records": list(),
        }

        base_url = "domains/%s/records?" % temp_domain['name']

        temp_domain_dict["domain_records"] = rest.get_paginated_data(base_url=base_url, data_key_name='domain_records')
        domain_results.append(temp_domain_dict)

    module.exit_json(changed=False, data=domain_results)


def main():
    argument_spec = DigitalOceanHelper.digital_ocean_argument_spec()
    argument_spec.update(
        domain_name=dict(type='str', required=False),
    )
    module = AnsibleModule(argument_spec=argument_spec)
    if module._name == 'digital_ocean_domain_facts':
        module.deprecate("The 'digital_ocean_domain_facts' module has been renamed to 'digital_ocean_domain_info'", version='2.13')

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=format_exc())


if __name__ == '__main__':
    main()
