#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2016, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cs_region
short_description: Manages regions on Apache CloudStack based clouds.
description:
    - Add, update and remove regions.
version_added: '2.3'
author: René Moser (@resmo)
options:
  id:
    description:
      - ID of the region.
      - Must be an number (int).
    type: int
    required: true
  name:
    description:
      - Name of the region.
      - Required if I(state=present)
    type: str
  endpoint:
    description:
      - Endpoint URL of the region.
      - Required if I(state=present)
    type: str
  state:
    description:
      - State of the region.
    type: str
    default: present
    choices: [ present, absent ]
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
- name: create a region
  cs_region:
    id: 2
    name: geneva
    endpoint: https://cloud.gva.example.com
  delegate_to: localhost

- name: remove a region with ID 2
  cs_region:
    id: 2
    state: absent
  delegate_to: localhost
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
  type: str
  sample: local
endpoint:
  description: Endpoint of the region.
  returned: success
  type: str
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
