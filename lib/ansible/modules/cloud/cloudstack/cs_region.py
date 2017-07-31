#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2016, René Moser <mail@renemoser.net>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cs_region
short_description: Manages regions on Apache CloudStack based clouds.
description:
    - Add, update and remove regions.
version_added: "2.3"
author: "René Moser (@resmo)"
options:
  id:
    description:
      - ID of the region.
      - Must be an number (int).
    required: true
  name:
    description:
      - Name of the region.
      - Required if C(state=present)
    required: false
    default: null
  endpoint:
    description:
      - Endpoint URL of the region.
      - Required if C(state=present)
    required: false
    default: null
  state:
    description:
      - State of the region.
    required: false
    default: 'present'
    choices: [ 'present', 'absent' ]
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
# create a region
local_action:
  module: cs_region
  id: 2
  name: geneva
  endpoint: https://cloud.gva.example.com

# remove a region with ID 2
local_action:
  module: cs_region
  id: 2
  state: absent
'''

RETURN = '''
---
id:
  description: ID of the region.
  returned: success
  type: int
  sample: 1
name:
  description: Name of the region.
  returned: success
  type: string
  sample: local
endpoint:
  description: Endpoint of the region.
  returned: success
  type: string
  sample: http://cloud.example.com
gslb_service_enabled:
  description: Whether the GSLB service is enabled or not.
  returned: success
  type: bool
  sample: true
portable_ip_service_enabled:
  description: Whether the portable IP service is enabled or not.
  returned: success
  type: bool
  sample: true
'''


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    cs_argument_spec,
    cs_required_together
)


class AnsibleCloudStackRegion(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackRegion, self).__init__(module)
        self.returns = {
            'endpoint': 'endpoint',
            'gslbserviceenabled': 'gslb_service_enabled',
            'portableipserviceenabled': 'portable_ip_service_enabled',
        }

    def get_region(self):
        id = self.module.params.get('id')
        regions = self.query_api('listRegions', id=id)
        if regions:
            return regions['region'][0]
        return None

    def present_region(self):
        region = self.get_region()
        if not region:
            region = self._create_region(region=region)
        else:
            region = self._update_region(region=region)
        return region

    def _create_region(self, region):
        self.result['changed'] = True
        args = {
            'id': self.module.params.get('id'),
            'name': self.module.params.get('name'),
            'endpoint': self.module.params.get('endpoint')
        }
        if not self.module.check_mode:
            res = self.query_api('addRegion', **args)
            region = res['region']
        return region

    def _update_region(self, region):
        args = {
            'id': self.module.params.get('id'),
            'name': self.module.params.get('name'),
            'endpoint': self.module.params.get('endpoint')
        }
        if self.has_changed(args, region):
            self.result['changed'] = True
            if not self.module.check_mode:
                res = self.query_api('updateRegion', **args)
                region = res['region']
        return region

    def absent_region(self):
        region = self.get_region()
        if region:
            self.result['changed'] = True
            if not self.module.check_mode:
                self.query_api('removeRegion', id=region['id'])
        return region


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        id=dict(required=True, type='int'),
        name=dict(),
        endpoint=dict(),
        state=dict(choices=['present', 'absent'], default='present'),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        required_if=[
            ('state', 'present', ['name', 'endpoint']),
        ],
        supports_check_mode=True
    )

    acs_region = AnsibleCloudStackRegion(module)

    state = module.params.get('state')
    if state == 'absent':
        region = acs_region.absent_region()
    else:
        region = acs_region.present_region()

    result = acs_region.get_result(region)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
