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
module: digital_ocean_volume_facts
short_description: Gather facts about DigitalOcean volumes
description:
    - This module can be used to gather facts about DigitalOcean provided volumes.
author: "Abhijeet Kasurde (@Akasurde)"
version_added: "2.6"
options:
  region_name:
    description:
     - Name of region to restrict results to volumes available in a specific region.
     - Please use M(digital_ocean_region_facts) for getting valid values related regions.
    required: false

requirements:
  - "python >= 2.6"

extends_documentation_fragment: digital_ocean.documentation
'''


EXAMPLES = '''
- name: Gather facts about all volume
  digital_ocean_volume_facts:
    oauth_token: "{{ oauth_token }}"

- name: Gather facts about volume in given region
  digital_ocean_volume_facts:
    region_name: nyc1
    oauth_token: "{{ oauth_token }}"

- name: Get facts about volume named nyc3-test-volume
  digital_ocean_volume_facts:
  register: resp_out
- set_fact:
    volume_id: "{{ item.id }}"
  with_items: "{{ resp_out.data|json_query(name) }}"
  vars:
    name: "[?name=='nyc3-test-volume']"
- debug: var=volume_id
'''


RETURN = '''
data:
    description: DigitalOcean volume facts
    returned: success
    type: list
    sample: [
        {
          "id": "506f78a4-e098-11e5-ad9f-000f53306ae1",
          "region": {
            "name": "New York 1",
            "slug": "nyc1",
            "sizes": [
              "s-1vcpu-1gb",
              "s-1vcpu-2gb",
              "s-1vcpu-3gb",
              "s-2vcpu-2gb",
              "s-3vcpu-1gb",
              "s-2vcpu-4gb",
              "s-4vcpu-8gb",
              "s-6vcpu-16gb",
              "s-8vcpu-32gb",
              "s-12vcpu-48gb",
              "s-16vcpu-64gb",
              "s-20vcpu-96gb",
              "s-24vcpu-128gb",
              "s-32vcpu-192gb"
            ],
            "features": [
              "private_networking",
              "backups",
              "ipv6",
              "metadata"
            ],
            "available": true
          },
          "droplet_ids": [

          ],
          "name": "example",
          "description": "Block store for examples",
          "size_gigabytes": 10,
          "created_at": "2016-03-02T17:00:49Z"
        }
    ]
'''

from traceback import format_exc
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.digital_ocean import DigitalOceanHelper
from ansible.module_utils._text import to_native


def core(module):
    region_name = module.params.get('region_name', None)

    rest = DigitalOceanHelper(module)

    base_url = 'volumes?'
    if region_name is not None:
        base_url += "region=%s&" % region_name

    volumes = rest.get_paginated_data(base_url=base_url, data_key_name='volumes')

    module.exit_json(changed=False, data=volumes)


def main():
    argument_spec = DigitalOceanHelper.digital_ocean_argument_spec()
    argument_spec.update(
        region_name=dict(type='str', required=False),
    )
    module = AnsibleModule(argument_spec=argument_spec)

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=format_exc())


if __name__ == '__main__':
    main()
