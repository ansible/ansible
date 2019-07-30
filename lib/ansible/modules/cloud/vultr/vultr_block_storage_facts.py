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
module: vultr_block_storage_facts
short_description: Gather facts about the Vultr block storage volumes available.
description:
  - Gather facts about block storage volumes available in Vultr.
version_added: "2.7"
author: "Yanis Guenane (@Spredzy)"
extends_documentation_fragment: vultr
'''

EXAMPLES = r'''
- name: Gather Vultr block storage volumes facts
  local_action:
    module: vultr_block_storage_facts

- name: Print the gathered facts
  debug:
    var: ansible_facts.vultr_block_storage_facts
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
    api_endpoint:
      description: Endpoint used for the API requests
      returned: success
      type: str
      sample: "https://api.vultr.com"
vultr_block_storage_facts:
  description: Response from Vultr API
  returned: success
  type: complex
  contains:
    "vultr_block_storage_facts": [
      {
        "attached_to_id": null,
        "cost_per_month": 1.0,
        "date_created": "2018-07-24 12:59:59",
        "id": 17332323,
        "name": "ansible-test-volume",
        "region": "New Jersey",
        "size": 10,
        "status": "active"
      }
    ]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vultr import (
    Vultr,
    vultr_argument_spec,
)


class AnsibleVultrBlockStorageFacts(Vultr):

    def __init__(self, module):
        super(AnsibleVultrBlockStorageFacts, self).__init__(module, "vultr_block_storage_facts")

        self.returns = {
            'attached_to_SUBID': dict(key='attached_to_id'),
            'cost_per_month': dict(convert_to='float'),
            'date_created': dict(),
            'SUBID': dict(key='id'),
            'label': dict(key='name'),
            'DCID': dict(key='region', transform=self._get_region_name),
            'size_gb': dict(key='size', convert_to='int'),
            'status': dict()
        }

    def _get_region_name(self, region):
        return self.get_region(region, 'DCID').get('name')

    def get_block_storage_volumes(self):
        return self.api_query(path="/v1/block/list")


def main():
    argument_spec = vultr_argument_spec()

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    volume_facts = AnsibleVultrBlockStorageFacts(module)
    result = volume_facts.get_result(volume_facts.get_block_storage_volumes())
    ansible_facts = {
        'vultr_block_storage_facts': result['vultr_block_storage_facts']
    }
    module.exit_json(ansible_facts=ansible_facts, **result)


if __name__ == '__main__':
    main()
