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
module: digital_ocean_size_info
short_description: Gather information about DigitalOcean Droplet sizes
description:
    - This module can be used to gather information about droplet sizes.
    - This module was called C(digital_ocean_size_facts) before Ansible 2.9. The usage did not change.
author: "Abhijeet Kasurde (@Akasurde)"
version_added: "2.6"
requirements:
  - "python >= 2.6"
extends_documentation_fragment: digital_ocean.documentation
'''


EXAMPLES = '''
- name: Gather information about all droplet sizes
  digital_ocean_size_info:
    oauth_token: "{{ oauth_token }}"

- name: Get droplet Size Slug where vcpus is 1
  digital_ocean_size_info:
    oauth_token: "{{ oauth_token }}"
  register: resp_out
- debug: var=resp_out
- set_fact:
    size_slug: "{{ item.slug }}"
  loop: "{{ resp_out.data|json_query(name) }}"
  vars:
    name: "[?vcpus==`1`]"
- debug: var=size_slug


'''


RETURN = '''
data:
    description: DigitalOcean droplet size information
    returned: success
    type: list
    sample: [
        {
            "available": true,
            "disk": 20,
            "memory": 512,
            "price_hourly": 0.00744,
            "price_monthly": 5.0,
            "regions": [
                "ams2",
                "ams3",
                "blr1",
                "fra1",
                "lon1",
                "nyc1",
                "nyc2",
                "nyc3",
                "sfo1",
                "sfo2",
                "sgp1",
                "tor1"
            ],
            "slug": "512mb",
            "transfer": 1.0,
            "vcpus": 1
        },
    ]
'''

from traceback import format_exc
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.digital_ocean import DigitalOceanHelper
from ansible.module_utils._text import to_native


def core(module):
    rest = DigitalOceanHelper(module)

    response = rest.get('sizes')
    if response.status_code != 200:
        module.fail_json(msg="Failed to fetch 'sizes' information due to error : %s" % response.json['message'])

    module.exit_json(changed=False, data=response.json['sizes'])


def main():
    argument_spec = DigitalOceanHelper.digital_ocean_argument_spec()
    module = AnsibleModule(
        argument_spec=argument_spec,
    )
    if module._name == 'digital_ocean_size_facts':
        module.deprecate("The 'digital_ocean_size_facts' module has been renamed to 'digital_ocean_size_info'", version='2.13')

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=format_exc())


if __name__ == '__main__':
    main()
