#!/usr/bin/python
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
module: vr_dns_domain_facts
short_description: Gather facts about the Vultr DNS domains available.
description:
  - Gather facts about DNS domains available in Vultr.
version_added: "2.7"
author: "Yanis Guenane (@Spredzy)"
extends_documentation_fragment: vultr
'''

EXAMPLES = r'''
- name: Gather Vultr DNS domains facts
  local_action:
    module: vr_dns_domains_facts

- name: Print the gathered facts
  debug:
    var: ansible_facts.vultr_dns_domain_facts
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
vultr_dns_domain_facts:
  description: Response from Vultr API
  returned: success
  type: complex
  contains:
    "vultr_dns_domain_facts": [
      {
        "date_created": "2018-07-19 07:14:21",
        "domain": "ansibletest.com"
      }
    ]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vultr import (
    Vultr,
    vultr_argument_spec,
)


class AnsibleVultrDnsDomainFacts(Vultr):

    def __init__(self, module):
        super(AnsibleVultrDnsDomainFacts, self).__init__(module, "vultr_dns_domain_facts")

        self.returns = {
            "date_created": dict(),
            "domain": dict(),
        }

    def get_domains(self):
        return self.api_query(path="/v1/dns/list")


def main():
    argument_spec = vultr_argument_spec()

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    domain_facts = AnsibleVultrDnsDomainFacts(module)
    result = domain_facts.get_result(domain_facts.get_domains())
    ansible_facts = {
        'vultr_dns_domain_facts': result['vultr_dns_domain_facts']
    }
    module.exit_json(ansible_facts=ansible_facts, **result)


if __name__ == '__main__':
    main()
