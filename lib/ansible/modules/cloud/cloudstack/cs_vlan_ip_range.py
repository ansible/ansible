#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2018, David Passante <@dpassante>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cs_vlan_ip_range
short_description: Manages VLAN IP ranges on Apache CloudStack based clouds.
description:
    - Create and delete VLAN IP range.
version_added: '2.8'
author: "David Passante (@dpassante)"
options:
  network:
    description:
      - The network name or id.
    required: true
  start_ip:
    description:
      - The beginning IPv4 address in the VLAN IP range.
      - Only considered on create.
    required: true
  end_ip:
    description:
      - The ending IPv4 address in the VLAN IP range.
      - If not specified, value of I(start_ip) is used.
      - Only considered on create.
  gateway:
    description:
      - The gateway of the VLAN IP range.
      - Required if I(state=present).
  netmask:
    description:
      - The netmask of the VLAN IP range.
      - Required if I(state=present).
  start_ipv6:
    description:
      - The beginning IPv6 address in the IPv6 network range.
      - Only considered on create.
  end_ipv6:
    description:
      - The ending IPv6 address in the IPv6 network range.
      - If not specified, value of I(start_ipv6) is used.
      - Only considered on create.
  gateway_ipv6:
    description:
      - The gateway of the IPv6 network.
      - Only considered on create.
  cidr_ipv6:
    description:
      - The CIDR of IPv6 network, must be at least /64.
  vlan:
    description:
      - The ID or VID of the network.
      - If not specified, will be defaulted to the vlan of the network.
  state:
    description:
      - State of the network ip range.
    default: present
    choices: [ present, absent ]
  zone:
    description:
      - The Zone ID of the VLAN IP range.
      - If not set, default zone is used.
  domain:
    description:
      - Domain of the account owning the VLAN.
  account:
    description:
      - Account who owns the VLAN.
      - Mutually exclusive with I(project).
  project:
    description:
      - Project who owns the VLAN.
      - Mutually exclusive with I(account).
  for_virtual_network:
    description:
      - true if VLAN is of Virtual type, false if Direct.
    type: bool
    default: false
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
- name: create a VLAN IP range for network test
  local_action:
    module: cs_vlan_ip_range
    network: test
    vlan: 98
    start_ip: 10.2.4.10
    end_ip: 10.2.4.100
    gateway: 10.2.4.1
    netmask: 255.255.255.0
    zone: zone-02

- name: remove a VLAN IP range for network test
  local_action:
    module: cs_vlan_ip_range
    state: absent
    network: test
    start_ip: 10.2.4.10
    end_ip: 10.2.4.100
    zone: zone-02
'''

RETURN = '''
---
id:
  description: UUID of the VLAN IP range.
  returned: success
  type: str
  sample: 04589590-ac63-4ffc-93f5-b698b8ac38b6
network:
  description: The network of vlan range
  returned: success
  type: str
  sample: test
vlan:
  description: The ID or VID of the VLAN.
  returned: success
  type: str
  sample: vlan://98
gateway:
  description: IPv4 gateway.
  returned: success
  type: str
  sample: 10.2.4.1
netmask:
  description: IPv4 netmask.
  returned: success
  type: str
  sample: 255.255.255.0
gateway_ipv6:
  description: IPv6 gateway.
  returned: success
  type: str
  sample: 2001:db8::1
cidr_ipv6:
  description: The CIDR of IPv6 network.
  returned: success
  type: str
  sample: 2001:db8::/64
zone:
  description: Name of zone.
  returned: success
  type: str
  sample: zone-02
domain:
  description: Domain name of the VLAN IP range.
  returned: success
  type: str
  sample: ROOT
account:
  description: Account who owns the network.
  returned: success
  type: str
  sample: example account
project:
  description: Project who owns the network.
  returned: success
  type: str
  sample: example project
for_systemvms:
  description: Whether VLAN IP range is dedicated to system vms or not.
  returned: success
  type: bool
  sample: false
for_virtual_network:
  description: Whether VLAN IP range is of Virtual type or not.
  returned: success
  type: bool
  sample: false
physical_network:
  description:  The physical network VLAN IP range belongs to.
  returned: success
  type: str
  sample: 04589590-ac63-4ffc-93f5-b698b8ac38b6
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    cs_argument_spec,
    cs_required_together,
)


class AnsibleCloudStackVlanIpRange(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackVlanIpRange, self).__init__(module)
        self.returns = {
            'startip': 'start_ip',
            'endip': 'end_ip',
            'physicalnetworkid': 'physical_network',
            'vlan': 'vlan',
            'forsystemvms': 'for_systemvms',
            'forvirtualnetwork': 'for_virtual_network',
            'gateway': 'gateway',
            'netmask': 'netmask',
            'ip6gateway': 'gateway_ipv6',
            'ip6cidr': 'cidr_ipv6',
            'startipv6': 'start_ipv6',
            'endipv6': 'end_ipv6',
        }
        self.ip_range = None

    def get_vlan_ip_range(self):
        if not self.ip_range:
            args = {
                'zoneid': self.get_zone(key='id'),
                'projectid': self.get_project(key='id'),
                'account': self.get_account(key='name'),
                'domainid': self.get_domain(key='id'),
                'networkid': self.get_network(key='id'),
            }

            res = self.query_api('listVlanIpRanges', **args)
            if res:
                ip_range_list = res['vlaniprange']

                params = {
                    'startip': self.module.params.get('start_ip'),
                    'endip': self.get_or_fallback('end_ip', 'start_ip'),
                }

                for ipr in ip_range_list:
                    if params['startip'] == ipr['startip'] and params['endip'] == ipr['endip']:
                        self.ip_range = ipr
                        break

        return self.ip_range

    def present_vlan_ip_range(self):
        ip_range = self.get_vlan_ip_range()

        if not ip_range:
            ip_range = self.create_vlan_ip_range()

        return ip_range

    def create_vlan_ip_range(self):
        self.result['changed'] = True

        vlan = self.module.params.get('vlan')

        args = {
            'zoneid': self.get_zone(key='id'),
            'projectid': self.get_project(key='id'),
            'account': self.get_account(key='name'),
            'domainid': self.get_domain(key='id'),
            'startip': self.module.params.get('start_ip'),
            'endip': self.get_or_fallback('end_ip', 'start_ip'),
            'netmask': self.module.params.get('netmask'),
            'gateway': self.module.params.get('gateway'),
            'startipv6': self.module.params.get('start_ipv6'),
            'endipv6': self.get_or_fallback('end_ipv6', 'start_ipv6'),
            'ip6gateway': self.module.params.get('gateway_ipv6'),
            'ip6cidr': self.module.params.get('cidr_ipv6'),
            'vlan': self.get_network(key='vlan') if not vlan else vlan,
            'networkid': self.get_network(key='id'),
            'forvirtualnetwork': self.module.params.get('for_virtual_network'),
        }

        if not self.module.check_mode:
            res = self.query_api('createVlanIpRange', **args)

            self.ip_range = res['vlan']

        return self.ip_range

    def absent_vlan_ip_range(self):
        ip_range = self.get_vlan_ip_range()

        if ip_range:
            self.result['changed'] = True

            args = {
                'id': ip_range['id'],
            }

            if not self.module.check_mode:
                self.query_api('deleteVlanIpRange', **args)

        return ip_range


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        network=dict(type='str', required=True),
        zone=dict(type='str'),
        start_ip=dict(type='str', required=True),
        end_ip=dict(type='str'),
        gateway=dict(type='str'),
        netmask=dict(type='str'),
        start_ipv6=dict(type='str'),
        end_ipv6=dict(type='str'),
        gateway_ipv6=dict(type='str'),
        cidr_ipv6=dict(type='str'),
        vlan=dict(type='str'),
        state=dict(choices=['present', 'absent'], default='present'),
        domain=dict(type='str'),
        account=dict(type='str'),
        project=dict(type='str'),
        for_virtual_network=dict(type='bool', default=False),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        mutually_exclusive=(
            ['account', 'project'],
        ),
        required_if=(("state", "present", ("gateway", "netmask")),),
        supports_check_mode=True,
    )

    acs_vlan_ip_range = AnsibleCloudStackVlanIpRange(module)

    state = module.params.get('state')
    if state == 'absent':
        ipr = acs_vlan_ip_range.absent_vlan_ip_range()

    else:
        ipr = acs_vlan_ip_range.present_vlan_ip_range()

    result = acs_vlan_ip_range.get_result(ipr)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
