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
module: digital_ocean_region_info
short_description: Gather information about DigitalOcean regions
description:
    - This module can be used to gather information about regions.
    - This module was called C(digital_ocean_region_facts) before Ansible 2.9. The usage did not change.
author: "Abhijeet Kasurde (@Akasurde)"
version_added: "2.6"
extends_documentation_fragment: digital_ocean.documentation
requirements:
  - "python >= 2.6"
'''


EXAMPLES = '''
- name: Gather information about all regions
  digital_ocean_region_info:
    oauth_token: "{{ oauth_token }}"

- name: Get Name of region where slug is known
  digital_ocean_region_info:
    oauth_token: "{{ oauth_token }}"
  register: resp_out
- debug: var=resp_out
- set_fact:
    region_slug: "{{ item.name }}"
  loop: "{{ resp_out.data|json_query(name) }}"
  vars:
    name: "[?slug==`nyc1`]"
- debug: var=region_slug
'''


RETURN = '''
data:
    description: DigitalOcean regions information
    returned: success
    type: list
    sample: [
        {
            "available": true,
            "features": [
                "private_networking",
                "backups",
                "ipv6",
                "metadata",
                "install_agent",
                "storage"
            ],
            "name": "New York 1",
            "sizes": [
                "512mb",
                "s-1vcpu-1gb",
                "1gb",
                "s-3vcpu-1gb",
                "s-1vcpu-2gb",
                "s-2vcpu-2gb",
                "2gb",
                "s-1vcpu-3gb",
                "s-2vcpu-4gb",
                "4gb",
                "c-2",
                "m-1vcpu-8gb",
                "8gb",
                "s-4vcpu-8gb",
                "s-6vcpu-16gb",
                "16gb"
            ],
            "slug": "nyc1"
        },
    ]
'''

from traceback import format_exc
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.digital_ocean import DigitalOceanHelper
from ansible.module_utils._text import to_native


def core(module):
    rest = DigitalOceanHelper(module)

    base_url = 'regions?'
    regions = rest.get_paginated_data(base_url=base_url, data_key_name='regions')

    module.exit_json(changed=False, data=regions)


def main():
    argument_spec = DigitalOceanHelper.digital_ocean_argument_spec()
    module = AnsibleModule(argument_spec=argument_spec)
    if module._name == 'digital_ocean_region_facts':
        module.deprecate("The 'digital_ocean_region_facts' module has been renamed to 'digital_ocean_region_info'", version='2.13')

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=format_exc())


if __name__ == '__main__':
    main()
