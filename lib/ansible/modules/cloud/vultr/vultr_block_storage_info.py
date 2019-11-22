#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2018, Yanis Guenane <yanis+ansible@guenane.org>
# Copyright (c) 2019, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: vultr_block_storage_info
short_description: Get information about the Vultr block storage volumes available.
description:
  - Get infos about block storage volumes available in Vultr.
version_added: "2.9"
author:
  - "Yanis Guenane (@Spredzy)"
  - "René Moser (@resmo)"
extends_documentation_fragment: vultr
'''

EXAMPLES = r'''
- name: Get Vultr block storage infos
  vultr_block_storage_info:
  register: result

- name: Print the infos
  debug:
    var: result.vultr_block_storage_info
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
vultr_block_storage_info:
  description: Response from Vultr API as list
  returned: success
  type: complex
  contains:
    id:
      description: ID of the block storage.
      returned: success
      type: int
      sample: 17332323
    size:
      description: Size in GB of the block storage.
      returned: success
      type: int
      sample: 10
    region:
      description: Region the block storage is located in.
      returned: success
      type: str
      sample: New Jersey
    name:
      description: Name of the block storage.
      returned: success
      type: str
      sample: my volume
    cost_per_month:
      description: Cost per month of the block storage.
      returned: success
      type: float
      sample: 1.0
    date_created:
      description: Date created of the block storage.
      returned: success
      type: str
      sample: "2018-07-24 12:59:59"
    status:
      description: Status of the block storage.
      returned: success
      type: str
      sample: active
    attached_to_id:
      description: Block storage is attached to this server ID.
      returned: success
      type: str
      sample: null
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vultr import (
    Vultr,
    vultr_argument_spec,
)


class AnsibleVultrBlockStorageFacts(Vultr):

    def __init__(self, module):
        super(AnsibleVultrBlockStorageFacts, self).__init__(module, "vultr_block_storage_info")

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

    volume_info = AnsibleVultrBlockStorageFacts(module)
    result = volume_info.get_result(volume_info.get_block_storage_volumes())
    module.exit_json(**result)


if __name__ == '__main__':
    main()
