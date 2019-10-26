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
module: vultr_plan_info
short_description: Gather information about the Vultr plans available.
description:
  - Gather information about plans available to boot servers.
version_added: "2.9"
author: "Yanis Guenane (@Spredzy)"
extends_documentation_fragment: vultr
'''

EXAMPLES = r'''
- name: Gather Vultr plans information
  local_action:
    module: vultr_plan_info
  register: result

- name: Print the gathered information
  debug:
    var: result.vultr_plan_info
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
      type: str
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
    api_retry_max_delay:
      description: Exponential backoff delay in seconds between retries up to this max delay value.
      returned: success
      type: int
      sample: 12
      version_added: '2.9'
    api_endpoint:
      description: Endpoint used for the API requests
      returned: success
      type: str
      sample: "https://api.vultr.com"
vultr_plan_info:
  description: Response from Vultr API
  returned: success
  type: complex
  contains:
    plan:
      description: List of the plans available.
      returned: success
      type: list
      sample: [{
        "available_locations": [
          1
        ],
        "bandwidth": 40.0,
        "bandwidth_gb": 40960,
        "disk": 110,
        "id": 118,
        "name": "32768 MB RAM,110 GB SSD,40.00 TB BW",
        "plan_type": "DEDICATED",
        "price_per_month": 240.0,
        "ram": 32768,
        "vcpu_count": 8,
        "windows": false
      }]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vultr import (
    Vultr,
    vultr_argument_spec,
)


class AnsibleVultrPlanInfo(Vultr):

    def __init__(self, module):
        super(AnsibleVultrPlanInfo, self).__init__(module, "vultr_plan_info")

        self.returns = {
            "VPSPLANID": dict(key='id', convert_to='int'),
            "available_locations": dict(),
            "bandwidth": dict(convert_to='float'),
            "bandwidth_gb": dict(convert_to='int'),
            "disk": dict(convert_to='int'),
            "name": dict(),
            "plan_type": dict(),
            "price_per_month": dict(convert_to='float'),
            "ram": dict(convert_to='int'),
            "vcpu_count": dict(convert_to='int'),
            "windows": dict(convert_to='bool')
        }

    def get_plans(self):
        return self.api_query(path="/v1/plans/list")


def parse_plans_list(plans_list):
    return [plan for id, plan in plans_list.items()]


def main():
    argument_spec = vultr_argument_spec()

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    plan_info = AnsibleVultrPlanInfo(module)
    result = plan_info.get_result(parse_plans_list(plan_info.get_plans()))
    module.exit_json(**result)


if __name__ == '__main__':
    main()
