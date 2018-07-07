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
module: vr_iso_facts
short_description: Gather facts about the Vultr ISO images available.
description:
  - Gather facts about ISO images available to boot servers.
version_added: "2.7"
author: "Yanis Guenane (@Spredzy)"
extends_documentation_fragment: vultr
'''

EXAMPLES = r'''
- name: Gather Vultr ISO images facts
  local_action:
    module: vr_iso_facts

- name: Print the gathered facts
  debug:
    var: ansible_facts.vultr_iso_facts
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
vultr_iso_facts:
  description: Response from Vultr API
  returned: success
  type: complex
  contains:
    public:
      description: List of the public ISO available.
      returned: success
      type: list
      sample: [{'ISOID': 42, 'description': 'OpenBSD 6,3', 'name': 'OpenBSD 6.3'}]
    account:
      description: List of the account-specific ISO available.
      returned: success
      type: list
      sample: [{'ISOID': 42, 'description': 'MY_ISO', 'name': 'MY_ISO'}]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vultr import (
    Vultr,
    vultr_argument_spec,
)


class AnsibleVultrIsoFacts(Vultr):

    def __init__(self, module):
        super(AnsibleVultrIsoFacts, self).__init__(module, "vultr_iso_facts")

    def get_public_isos(self):
        return self.api_query(path="/v1/iso/list_public")

    def get_account_isos(self):
        return self.api_query(path="/v1/iso/list")


def parse_isos_list(isos_list):
    return [iso for id, iso in isos_list.items()] if isos_list else []


def main():
    argument_spec = vultr_argument_spec()

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    iso_facts = AnsibleVultrIsoFacts(module)
    facts = {
        'public': parse_isos_list(iso_facts.get_public_isos()),
        'account': parse_isos_list(iso_facts.get_account_isos()),
    }
    ansible_facts = {
        'vultr_iso_facts': facts
    }
    result = iso_facts.get_result({})
    result['vultr_iso_facts'] = facts
    module.exit_json(ansible_facts=ansible_facts, **result)


if __name__ == '__main__':
    main()
