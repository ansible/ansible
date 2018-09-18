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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cs_zone
short_description: Manages zones on Apache CloudStack based clouds.
description:
    - Create, update and remove zones.
version_added: "2.1"
author: "René Moser (@resmo)"
options:
  name:
    description:
      - Name of the zone.
    required: true
  id:
    description:
      - uuid of the existing zone.
  state:
    description:
      - State of the zone.
    default: 'present'
    choices: [ 'present', 'enabled', 'disabled', 'absent' ]
  domain:
    description:
      - Domain the zone is related to.
      - Zone is a public zone if not set.
  network_domain:
    description:
      - Network domain for the zone.
  network_type:
    description:
      - Network type of the zone.
    default: basic
    choices: [ 'basic', 'advanced' ]
  dns1:
    description:
      - First DNS for the zone.
      - Required if C(state=present)
  dns2:
    description:
      - Second DNS for the zone.
  internal_dns1:
    description:
      - First internal DNS for the zone.
      - If not set C(dns1) will be used on C(state=present).
  internal_dns2:
    description:
      - Second internal DNS for the zone.
  dns1_ipv6:
    description:
      - First DNS for IPv6 for the zone.
  dns2_ipv6:
    description:
      - Second DNS for IPv6 for the zone.
  guest_cidr_address:
    description:
      - Guest CIDR address for the zone.
  dhcp_provider:
    description:
      - DHCP provider for the Zone.
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
# Ensure a zone is present
- local_action:
    module: cs_zone
    name: ch-zrh-ix-01
    dns1: 8.8.8.8
    dns2: 8.8.4.4
    network_type: basic

# Ensure a zone is disabled
- local_action:
    module: cs_zone
    name: ch-zrh-ix-01
    state: disabled

# Ensure a zone is enabled
- local_action:
    module: cs_zone
    name: ch-zrh-ix-01
    state: enabled

# Ensure a zone is absent
- local_action:
    module: cs_zone
    name: ch-zrh-ix-01
    state: absent
'''

RETURN = '''
---
id:
  description: UUID of the zone.
  returned: success
  type: string
  sample: 04589590-ac63-4ffc-93f5-b698b8ac38b6
name:
  description: Name of the zone.
  returned: success
  type: string
  sample: zone01
dns1:
  description: First DNS for the zone.
  returned: success
  type: string
  sample: 8.8.8.8
dns2:
  description: Second DNS for the zone.
  returned: success
  type: string
  sample: 8.8.4.4
internal_dns1:
  description: First internal DNS for the zone.
  returned: success
  type: string
  sample: 8.8.8.8
internal_dns2:
  description: Second internal DNS for the zone.
  returned: success
  type: string
  sample: 8.8.4.4
dns1_ipv6:
  description: First IPv6 DNS for the zone.
  returned: success
  type: string
  sample: "2001:4860:4860::8888"
dns2_ipv6:
  description: Second IPv6 DNS for the zone.
  returned: success
  type: string
  sample: "2001:4860:4860::8844"
allocation_state:
  description: State of the zone.
  returned: success
  type: string
  sample: Enabled
domain:
  description: Domain the zone is related to.
  returned: success
  type: string
  sample: ROOT
network_domain:
  description: Network domain for the zone.
  returned: success
  type: string
  sample: example.com
network_type:
  description: Network type for the zone.
  returned: success
  type: string
  sample: basic
local_storage_enabled:
  description: Local storage offering enabled.
  returned: success
  type: bool
  sample: false
securitygroups_enabled:
  description: Security groups support is enabled.
  returned: success
  type: bool
  sample: false
guest_cidr_address:
  description: Guest CIDR address for the zone
  returned: success
  type: string
  sample: 10.1.1.0/24
dhcp_provider:
  description: DHCP provider for the zone
  returned: success
  type: string
  sample: VirtualRouter
zone_token:
  description: Zone token
  returned: success
  type: string
  sample: ccb0a60c-79c8-3230-ab8b-8bdbe8c45bb7
tags:
  description: List of resource tags associated with the zone.
  returned: success
  type: dict
  sample: [ { "key": "foo", "value": "bar" } ]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    cs_argument_spec,
    cs_required_together,
)


class AnsibleCloudStackZone(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackZone, self).__init__(module)
        self.returns = {
            'dns1': 'dns1',
            'dns2': 'dns2',
            'internaldns1': 'internal_dns1',
            'internaldns2': 'internal_dns2',
            'ipv6dns1': 'dns1_ipv6',
            'ipv6dns2': 'dns2_ipv6',
            'domain': 'network_domain',
            'networktype': 'network_type',
            'securitygroupsenabled': 'securitygroups_enabled',
            'localstorageenabled': 'local_storage_enabled',
            'guestcidraddress': 'guest_cidr_address',
            'dhcpprovider': 'dhcp_provider',
            'allocationstate': 'allocation_state',
            'zonetoken': 'zone_token',
        }
        self.zone = None

    def _get_common_zone_args(self):
        args = {
            'name': self.module.params.get('name'),
            'dns1': self.module.params.get('dns1'),
            'dns2': self.module.params.get('dns2'),
            'internaldns1': self.get_or_fallback('internal_dns1', 'dns1'),
            'internaldns2': self.get_or_fallback('internal_dns2', 'dns2'),
            'ipv6dns1': self.module.params.get('dns1_ipv6'),
            'ipv6dns2': self.module.params.get('dns2_ipv6'),
            'networktype': self.module.params.get('network_type'),
            'domain': self.module.params.get('network_domain'),
            'localstorageenabled': self.module.params.get('local_storage_enabled'),
            'guestcidraddress': self.module.params.get('guest_cidr_address'),
            'dhcpprovider': self.module.params.get('dhcp_provider'),
        }
        state = self.module.params.get('state')
        if state in ['enabled', 'disabled']:
            args['allocationstate'] = state.capitalize()
        return args

    def get_zone(self):
        if not self.zone:
            args = {}

            uuid = self.module.params.get('id')
            if uuid:
                args['id'] = uuid
                zones = self.query_api('listZones', **args)
                if zones:
                    self.zone = zones['zone'][0]
                    return self.zone

            args['name'] = self.module.params.get('name')
            zones = self.query_api('listZones', **args)
            if zones:
                self.zone = zones['zone'][0]
        return self.zone

    def present_zone(self):
        zone = self.get_zone()
        if zone:
            zone = self._update_zone()
        else:
            zone = self._create_zone()
        return zone

    def _create_zone(self):
        required_params = [
            'dns1',
        ]
        self.module.fail_on_missing_params(required_params=required_params)

        self.result['changed'] = True

        args = self._get_common_zone_args()
        args['domainid'] = self.get_domain(key='id')
        args['securitygroupenabled'] = self.module.params.get('securitygroups_enabled')

        zone = None
        if not self.module.check_mode:
            res = self.query_api('createZone', **args)
            zone = res['zone']
        return zone

    def _update_zone(self):
        zone = self.get_zone()

        args = self._get_common_zone_args()
        args['id'] = zone['id']

        if self.has_changed(args, zone):
            self.result['changed'] = True

            if not self.module.check_mode:
                res = self.query_api('updateZone', **args)
                zone = res['zone']
        return zone

    def absent_zone(self):
        zone = self.get_zone()
        if zone:
            self.result['changed'] = True

            args = {
                'id': zone['id']
            }
            if not self.module.check_mode:
                self.query_api('deleteZone', **args)

        return zone


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        id=dict(),
        name=dict(required=True),
        dns1=dict(),
        dns2=dict(),
        internal_dns1=dict(),
        internal_dns2=dict(),
        dns1_ipv6=dict(),
        dns2_ipv6=dict(),
        network_type=dict(default='basic', choices=['Basic', 'basic', 'Advanced', 'advanced']),
        network_domain=dict(),
        guest_cidr_address=dict(),
        dhcp_provider=dict(),
        local_storage_enabled=dict(type='bool'),
        securitygroups_enabled=dict(type='bool'),
        state=dict(choices=['present', 'enabled', 'disabled', 'absent'], default='present'),
        domain=dict(),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )

    acs_zone = AnsibleCloudStackZone(module)

    state = module.params.get('state')
    if state in ['absent']:
        zone = acs_zone.absent_zone()
    else:
        zone = acs_zone.present_zone()

    result = acs_zone.get_result(zone)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
