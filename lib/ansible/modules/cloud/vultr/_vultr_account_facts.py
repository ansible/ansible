#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2017, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['deprecated'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: vultr_account_facts
short_description: Gather facts about the Vultr account.
description:
  - Gather facts about account balance, charges and payments.
version_added: "2.5"
deprecated:
  removed_in: "2.12"
  why: Transformed into an info module.
  alternative: Use M(vultr_account_info) instead.
author: "René Moser (@resmo)"
extends_documentation_fragment: vultr
'''

EXAMPLES = r'''
- name: Gather Vultr account facts
  local_action:
    module: vultr_account_facts

- name: Print the gathered facts
  debug:
    var: ansible_facts.vultr_account_facts
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
vultr_account_facts:
  description: Response from Vultr API
  returned: success
  type: complex
  contains:
    balance:
      description: Your account balance.
      returned: success
      type: float
      sample: -214.69
    pending_charges:
      description: Charges pending.
      returned: success
      type: float
      sample: 57.03
    last_payment_date:
      description: Date of the last payment.
      returned: success
      type: str
      sample: "2017-08-26 12:47:48"
    last_payment_amount:
      description: The amount of the last payment transaction.
      returned: success
      type: float
      sample: -250.0
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vultr import (
    Vultr,
    vultr_argument_spec,
)


class AnsibleVultrAccountFacts(Vultr):

    def __init__(self, module):
        super(AnsibleVultrAccountFacts, self).__init__(module, "vultr_account_facts")

        self.returns = {
            'balance': dict(convert_to='float'),
            'pending_charges': dict(convert_to='float'),
            'last_payment_date': dict(),
            'last_payment_amount': dict(convert_to='float'),
        }

    def get_account_info(self):
        return self.api_query(path="/v1/account/info")


def main():
    argument_spec = vultr_argument_spec()

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    account_facts = AnsibleVultrAccountFacts(module)
    result = account_facts.get_result(account_facts.get_account_info())
    ansible_facts = {
        'vultr_account_facts': result['vultr_account_facts']
    }
    module.exit_json(ansible_facts=ansible_facts, **result)


if __name__ == '__main__':
    main()
