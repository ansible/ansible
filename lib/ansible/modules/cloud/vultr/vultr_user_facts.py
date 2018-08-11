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
module: vr_user_facts
short_description: Gather facts about the Vultr user available.
description:
  - Gather facts about users available in Vultr.
version_added: "2.7"
author: "Yanis Guenane (@Spredzy)"
extends_documentation_fragment: vultr
'''

EXAMPLES = r'''
- name: Gather Vultr user facts
  local_action:
    module: vr_user_facts

- name: Print the gathered facts
  debug:
    var: ansible_facts.vultr_user_facts
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
vultr_user_facts:
  description: Response from Vultr API
  returned: success
  type: complex
  contains:
    "vultr_user_facts": [
      {
        "acls": [],
        "api_enabled": "yes",
        "email": "mytestuser@example.com",
        "id": "a235b4f45e87f",
        "name": "mytestuser"
      }
    ]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vultr import (
    Vultr,
    vultr_argument_spec,
)


class AnsibleVultrUserFacts(Vultr):

    def __init__(self, module):
        super(AnsibleVultrUserFacts, self).__init__(module, "vultr_user_facts")

        self.returns = {
            "USERID": dict(key='id'),
            "acls": dict(),
            "api_enabled": dict(),
            "email": dict(),
            "name": dict()
        }

    def get_regions(self):
        return self.api_query(path="/v1/user/list")


def main():
    argument_spec = vultr_argument_spec()

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    user_facts = AnsibleVultrUserFacts(module)
    result = user_facts.get_result(user_facts.get_regions())
    ansible_facts = {
        'vultr_user_facts': result['vultr_user_facts']
    }
    module.exit_json(ansible_facts=ansible_facts, **result)


if __name__ == '__main__':
    main()
