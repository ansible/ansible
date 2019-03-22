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

DOCUMENTATION = '''
---
module: vultr_block_storage
short_description: Manages block storage volumes on Vultr.
description:
  - Manage block storage volumes on Vultr.
version_added: "2.7"
author: "Yanis Guenane (@Spredzy)"
options:
  name:
    description:
      - Name of the block storage volume.
    required: true
    aliases: [ description, label ]
  size:
    description:
      - Size of the block storage volume in GB.
    required: true
  region:
    description:
      - Region the block storage volume is deployed into.
    required: true
  state:
    description:
      - State of the block storage volume.
    default: present
    choices: [ present, absent ]
extends_documentation_fragment: vultr
'''

EXAMPLES = '''
- name: Ensure a block storage volume is present
  local_action:
    module: vultr_block_storage
    name: myvolume
    size: 10
    region: Amsterdam

- name: Ensure a block storage volume is absent
  local_action:
    module: vultr_block_storage
    name: myvolume
    state: absent
'''

RETURN = '''
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
vultr_block_storage:
  description: Response from Vultr API
  returned: success
  type: complex
  contains:
    attached_to_id:
      description: The ID of the server the volume is attached to
      returned: success
      type: str
      sample: "10194376"
    cost_per_month:
      description: Cost per month for the volume
      returned: success
      type: float
      sample: 1.00
    date_created:
      description: Date when the volume was created
      returned: success
      type: str
      sample: "2017-08-26 12:47:48"
    id:
      description: ID of the block storage volume
      returned: success
      type: str
      sample: "1234abcd"
    name:
      description: Name of the volume
      returned: success
      type: str
      sample: "ansible-test-volume"
    region:
      description: Region the volume was deployed into
      returned: success
      type: str
      sample: "New Jersey"
    size:
      description: Information about the volume size in GB
      returned: success
      type: int
      sample: 10
    status:
      description: Status about the deployment of the volume
      returned: success
      type: str
      sample: "active"

'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vultr import (
    Vultr,
    vultr_argument_spec,
)


class AnsibleVultrBlockStorage(Vultr):

    def __init__(self, module):
        super(AnsibleVultrBlockStorage, self).__init__(module, "vultr_block_storage")

        self.returns = {
            'SUBID': dict(key='id'),
            'label': dict(key='name'),
            'DCID': dict(key='region', transform=self._get_region_name),
            'attached_to_SUBID': dict(key='attached_to_id'),
            'cost_per_month': dict(convert_to='float'),
            'date_created': dict(),
            'size_gb': dict(key='size', convert_to='int'),
            'status': dict()
        }

    def _get_region_name(self, region):
        return self.get_region(region, 'DCID').get('name')

    def get_block_storage_volumes(self):
        volumes = self.api_query(path="/v1/block/list")
        if volumes:
            for volume in volumes:
                if volume.get('label') == self.module.params.get('name'):
                    return volume
        return {}

    def present_block_storage_volume(self):
        volume = self.get_block_storage_volumes()
        if not volume:
            volume = self._create_block_storage_volume(volume)
        return volume

    def _create_block_storage_volume(self, volume):
        self.result['changed'] = True
        data = {
            'label': self.module.params.get('name'),
            'DCID': self.get_region().get('DCID'),
            'size_gb': self.module.params.get('size')
        }
        self.result['diff']['before'] = {}
        self.result['diff']['after'] = data

        if not self.module.check_mode:
            self.api_query(
                path="/v1/block/create",
                method="POST",
                data=data
            )
            volume = self.get_block_storage_volumes()
        return volume

    def absent_block_storage_volume(self):
        volume = self.get_block_storage_volumes()
        if volume:
            self.result['changed'] = True

            data = {
                'SUBID': volume['SUBID'],
            }

            self.result['diff']['before'] = volume
            self.result['diff']['after'] = {}

            if not self.module.check_mode:
                self.api_query(
                    path="/v1/block/delete",
                    method="POST",
                    data=data
                )
        return volume


def main():
    argument_spec = vultr_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True, aliases=['description', 'label']),
        size=dict(type='int'),
        region=dict(),
        state=dict(choices=['present', 'absent'], default='present'),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[['state', 'present', ['size', 'region']]]
    )

    vultr_block_storage = AnsibleVultrBlockStorage(module)
    if module.params.get('state') == "absent":
        volume = vultr_block_storage.absent_block_storage_volume()
    else:
        volume = vultr_block_storage.present_block_storage_volume()

    result = vultr_block_storage.get_result(volume)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
