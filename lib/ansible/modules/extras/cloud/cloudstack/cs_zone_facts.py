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
module: cs_zone_facts
short_description: Gathering facts of zones from Apache CloudStack based clouds.
description:
    - Gathering facts from the API of a zone.
version_added: "2.1"
author: "René Moser (@resmo)"
options:
  name:
    description:
      - Name of the zone.
    required: true
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
- local_action:
    module: cs_zone_facts
    name: ch-gva-1

- debug: var=cloudstack_zone
'''

RETURN = '''
---
cloudstack_zone.id:
  description: UUID of the zone.
  returned: success
  type: string
  sample: 04589590-ac63-4ffc-93f5-b698b8ac38b6
cloudstack_zone.name:
  description: Name of the zone.
  returned: success
  type: string
  sample: zone01
cloudstack_zone.dns1:
  description: First DNS for the zone.
  returned: success
  type: string
  sample: 8.8.8.8
cloudstack_zone.dns2:
  description: Second DNS for the zone.
  returned: success
  type: string
  sample: 8.8.4.4
cloudstack_zone.internal_dns1:
  description: First internal DNS for the zone.
  returned: success
  type: string
  sample: 8.8.8.8
cloudstack_zone.internal_dns2:
  description: Second internal DNS for the zone.
  returned: success
  type: string
  sample: 8.8.4.4
cloudstack_zone.dns1_ipv6:
  description: First IPv6 DNS for the zone.
  returned: success
  type: string
  sample: "2001:4860:4860::8888"
cloudstack_zone.dns2_ipv6:
  description: Second IPv6 DNS for the zone.
  returned: success
  type: string
  sample: "2001:4860:4860::8844"
cloudstack_zone.allocation_state:
  description: State of the zone.
  returned: success
  type: string
  sample: Enabled
cloudstack_zone.domain:
  description: Domain the zone is related to.
  returned: success
  type: string
  sample: ROOT
cloudstack_zone.network_domain:
  description: Network domain for the zone.
  returned: success
  type: string
  sample: example.com
cloudstack_zone.network_type:
  description: Network type for the zone.
  returned: success
  type: string
  sample: basic
cloudstack_zone.local_storage_enabled:
  description: Local storage offering enabled.
  returned: success
  type: bool
  sample: false
cloudstack_zone.securitygroups_enabled:
  description: Security groups support is enabled.
  returned: success
  type: bool
  sample: false
cloudstack_zone.guest_cidr_address:
  description: Guest CIDR address for the zone
  returned: success
  type: string
  sample: 10.1.1.0/24
cloudstack_zone.dhcp_provider:
  description: DHCP provider for the zone
  returned: success
  type: string
  sample: VirtualRouter
cloudstack_zone.zone_token:
  description: Zone token
  returned: success
  type: string
  sample: ccb0a60c-79c8-3230-ab8b-8bdbe8c45bb7
cloudstack_zone.tags:
  description: List of resource tags associated with the zone.
  returned: success
  type: dict
  sample: [ { "key": "foo", "value": "bar" } ]
'''

import base64

try:
    from cs import CloudStack, CloudStackException, read_config
    has_lib_cs = True
except ImportError:
    has_lib_cs = False

# import cloudstack common
from ansible.module_utils.cloudstack import *

class AnsibleCloudStackZoneFacts(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackZoneFacts, self).__init__(module)
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
        self.facts = {
            'cloudstack_zone': None,
        }


    def get_zone(self):
        if not self.zone:
            # TODO: add param key signature in get_zone()
            self.module.params['zone'] = self.module.params.get('name')
            super(AnsibleCloudStackZoneFacts, self).get_zone()
        return self.zone


    def run(self):
        zone = self.get_zone()
        self.facts['cloudstack_zone'] = self.get_result(zone)
        return self.facts


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        name = dict(required=True),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=False,
    )

    if not has_lib_cs:
        module.fail_json(msg="python library cs required: pip install cs")

    cs_zone_facts = AnsibleCloudStackZoneFacts(module=module).run()
    cs_facts_result = dict(changed=False, ansible_facts=cs_zone_facts)
    module.exit_json(**cs_facts_result)

from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
