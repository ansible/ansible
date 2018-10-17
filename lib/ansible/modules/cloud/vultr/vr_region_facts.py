#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2018, Yanis Guenane <yanis+ansible@guenane.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: vr_region_facts
short_description: Gather facts about the Vultr regions available.
description:
  - Gather facts about regions available to boot servers.
version_added: "2.7"
author: "Yanis Guenane (@Spredzy)"
extends_documentation_fragment: vultr
'''

EXAMPLES = r'''
- name: Gather Vultr regions facts
  local_action:
    module: vr_region_facts

- name: Print the gathered facts
  debug:
    var: ansible_facts.vultr_region_facts
'''

RETURN = r'''
---
vultr_api:
  description: Response from Vultr API with a few additions/modification
  returned: success
  type: complex
  contains:
    api_account:
      description: Account used in the ini file to select the key
      returned: success
      type: string
      sample: default
    api_timeout:
      description: Timeout used for the API requests
      returned: success
      type: int
      sample: 60
    api_retries:
      description: Amount of max retries for the API requests
      returned: success
      type: int
      sample: 5
    api_endpoint:
      description: Endpoint used for the API requests
      returned: success
      type: string
      sample: "https://api.vultr.com"
vultr_region_facts:
  description: Response from Vultr API
  returned: success
  type: complex
  contains:
    "vultr_region_facts": [
      {
        "block_storage": false,
        "continent": "Europe",
        "country": "GB",
        "ddos_protection": true,
        "id": 8,
        "name": "London",
        "regioncode": "LHR",
        "state": ""
      }
    ]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vultr import (
    Vultr,
    vultr_argument_spec,
)


class AnsibleVultrRegionFacts(Vultr):

    def __init__(self, module):
        super(AnsibleVultrRegionFacts, self).__init__(module, "vultr_region_facts")

        self.returns = {
            "DCID": dict(key='id', convert_to='int'),
            "block_storage": dict(convert_to='bool'),
            "continent": dict(),
            "country": dict(),
            "ddos_protection": dict(convert_to='bool'),
            "name": dict(),
            "regioncode": dict(),
            "state": dict()
        }

    def get_regions(self):
        return self.api_query(path="/v1/regions/list")


def parse_regions_list(regions_list):
    return [region for id, region in regions_list.items()]


def main():
    argument_spec = vultr_argument_spec()

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    region_facts = AnsibleVultrRegionFacts(module)
    result = region_facts.get_result(parse_regions_list(region_facts.get_regions()))
    ansible_facts = {
        'vultr_region_facts': result['vultr_region_facts']
    }
    module.exit_json(ansible_facts=ansible_facts, **result)


if __name__ == '__main__':
    main()
