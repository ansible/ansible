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
module: vr_os_facts
short_description: Gather facts about the Vultr OSes available.
description:
  - Gather facts about OSes available to boot servers.
version_added: "2.7"
author: "Yanis Guenane (@Spredzy)"
extends_documentation_fragment: vultr
'''

EXAMPLES = r'''
- name: Gather Vultr OSes facts
  local_action:
    module: vr_os_facts

- name: Print the gathered facts
  debug:
    var: ansible_facts.vultr_os_facts
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
ansible_facts:
  description: Response from Vultr API
  returned: success
  type: complex
  contains:
    "vultr_os_facts": [
      {
        "arch": "x64",
        "family": "openbsd",
        "id": 234,
        "name": "OpenBSD 6 x64",
        "windows": false
      }
    ]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vultr import (
    Vultr,
    vultr_argument_spec,
)


class AnsibleVultrOSFacts(Vultr):

    def __init__(self, module):
        super(AnsibleVultrOSFacts, self).__init__(module, "vultr_os_facts")

        self.returns = {
            "OSID": dict(key='id', convert_to='int'),
            "arch": dict(),
            "family": dict(),
            "name": dict(),
            "windows": dict(convert_to='bool')
        }

    def get_oses(self):
        return self.api_query(path="/v1/os/list")


def parse_oses_list(oses_list):
        return [os for id, os in oses_list.items()]


def main():
    argument_spec = vultr_argument_spec()

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    os_facts = AnsibleVultrOSFacts(module)
    result = os_facts.get_result(parse_oses_list(os_facts.get_oses()))
    ansible_facts = {
        'vultr_os_facts': result['vultr_os_facts']
    }
    module.exit_json(ansible_facts=ansible_facts, **result)


if __name__ == '__main__':
    main()
