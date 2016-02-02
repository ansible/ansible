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
      - uuid of the exising zone.
    default: null
    required: false
  state:
    description:
      - State of the zone.
    required: false
    default: 'present'
    choices: [ 'present', 'enabled', 'disabled', 'absent' ]
  domain:
    description:
      - Domain the zone is related to.
      - Zone is a public zone if not set.
    required: false
    default: null
  network_domain:
    description:
      - Network domain for the zone.
    required: false
    default: null
  network_type:
    description:
      - Network type of the zone.
    required: false
    default: basic
    choices: [ 'basic', 'advanced' ]
  dns1:
    description:
      - First DNS for the zone.
      - Required if C(state=present)
    required: false
    default: null
  dns2:
    description:
      - Second DNS for the zone.
    required: false
    default: null
  internal_dns1:
    description:
      - First internal DNS for the zone.
      - If not set C(dns1) will be used on C(state=present).
    required: false
    default: null
  internal_dns2:
    description:
      - Second internal DNS for the zone.
    required: false
    default: null
  dns1_ipv6:
    description:
      - First DNS for IPv6 for the zone.
    required: false
    default: null
  dns2_ipv6:
    description:
      - Second DNS for IPv6 for the zone.
    required: false
    default: null
  guest_cidr_address:
    description:
      - Guest CIDR address for the zone.
    required: false
    default: null
  dhcp_provider:
    description:
      - DHCP provider for the Zone.
    required: false
    default: null
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

try:
    from cs import CloudStack, CloudStackException, read_config
    has_lib_cs = True
except ImportError:
    has_lib_cs = False

# import cloudstack common
from ansible.module_utils.cloudstack import *

class AnsibleCloudStackZone(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackZone, self).__init__(module)
        self.returns = {
            'dns1':                     'dns1',
            'dns2':                     'dns2',
            'internaldns1':             'internal_dns1',
            'internaldns2':             'internal_dns2',
            'ipv6dns1':                 'dns1_ipv6',
            'ipv6dns2':                 'dns2_ipv6',
            'domain':                   'network_domain',
            'networktype':              'network_type',
            'securitygroupsenabled':    'securitygroups_enabled',
            'localstorageenabled':      'local_storage_enabled',
            'guestcidraddress':         'guest_cidr_address',
            'dhcpprovider':             'dhcp_provider',
            'allocationstate':          'allocation_state',
            'zonetoken':                'zone_token',
        }
        self.zone = None


    def _get_common_zone_args(self):
        args = {}
        args['name'] = self.module.params.get('name')
        args['dns1'] = self.module.params.get('dns1')
        args['dns2'] = self.module.params.get('dns2')
        args['internaldns1'] = self.get_or_fallback('internal_dns1', 'dns1')
        args['internaldns2'] = self.get_or_fallback('internal_dns2', 'dns2')
        args['ipv6dns1'] = self.module.params.get('dns1_ipv6')
        args['ipv6dns2'] = self.module.params.get('dns2_ipv6')
        args['networktype'] = self.module.params.get('network_type')
        args['domain'] = self.module.params.get('network_domain')
        args['localstorageenabled'] = self.module.params.get('local_storage_enabled')
        args['guestcidraddress'] = self.module.params.get('guest_cidr_address')
        args['dhcpprovider'] = self.module.params.get('dhcp_provider')
        state = self.module.params.get('state')
        if state in [ 'enabled', 'disabled']:
            args['allocationstate'] = state.capitalize()
        return args


    def get_zone(self):
        if not self.zone:
            args = {}

            uuid = self.module.params.get('id')
            if uuid:
                args['id'] = uuid
                zones = self.cs.listZones(**args)
                if zones:
                    self.zone = zones['zone'][0]
                    return self.zone

            args['name'] = self.module.params.get('name')
            zones = self.cs.listZones(**args)
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
            res = self.cs.createZone(**args)
            if 'errortext' in res:
                self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
            zone = res['zone']
        return zone


    def _update_zone(self):
        zone = self.get_zone()

        args = self._get_common_zone_args()
        args['id'] = zone['id']

        if self.has_changed(args, zone):
            self.result['changed'] = True

            if not self.module.check_mode:
                res = self.cs.updateZone(**args)
                if 'errortext' in res:
                    self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
                zone = res['zone']
        return zone


    def absent_zone(self):
        zone = self.get_zone()
        if zone:
            self.result['changed'] = True

            args = {}
            args['id'] = zone['id']

            if not self.module.check_mode:
                res = self.cs.deleteZone(**args)
                if 'errortext' in res:
                    self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
        return zone


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        id = dict(default=None),
        name = dict(required=True),
        dns1 = dict(default=None),
        dns2 = dict(default=None),
        internal_dns1 = dict(default=None),
        internal_dns2 = dict(default=None),
        dns1_ipv6 = dict(default=None),
        dns2_ipv6 = dict(default=None),
        network_type = dict(default='basic', choices=['Basic', 'basic', 'Advanced', 'advanced']),
        network_domain = dict(default=None),
        guest_cidr_address = dict(default=None),
        dhcp_provider = dict(default=None),
        local_storage_enabled = dict(default=None),
        securitygroups_enabled = dict(default=None),
        state = dict(choices=['present', 'enabled', 'disabled', 'absent'], default='present'),
        domain = dict(default=None),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )

    if not has_lib_cs:
        module.fail_json(msg="python library cs required: pip install cs")

    try:
        acs_zone = AnsibleCloudStackZone(module)

        state = module.params.get('state')
        if state in ['absent']:
            zone = acs_zone.absent_zone()
        else:
            zone = acs_zone.present_zone()

        result = acs_zone.get_result(zone)

    except CloudStackException as e:
        module.fail_json(msg='CloudStackException: %s' % str(e))

    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
