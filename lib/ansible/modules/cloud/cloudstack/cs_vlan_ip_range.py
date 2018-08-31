#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2017, Netservers Ltd. <support@netservers.co.uk>
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
module: cs_vlan_ip_range
short_description: Manages VLAN IP ranges on Apache CloudStack based clouds.
description:
    - Create and remove VLAN IP ranges.
    - VLAN IP ranges cannot be updated
version_added: "2.4"
author: "Netservers Ltd. (@netservers)"
options:
  zone:
    description:
      - Zone name.
    required: true
  pod:
    description:
      - Pod name.
    required: false
  project:
    description:
      - Project name.
    required: false
  network:
    description:
      - Network name.
    required: false
  ipv4_start:
    description:
      - Start address for ipv4 range.
    required: false
    default: none
  ipv4_end:
    description:
      - End address for ipv4 range.
    required: false
    default: none
  ipv4_gateway:
    description:
      - Gateway IP for ipv4 range.
    required: false
    default: none
  ipv4_netmask:
    description:
      - Gateway IP for ipv4 range.
    required: false
    default: none
  ipv6_start:
    description:
      - Start address for ipv6 range.
    required: false
    default: none
  ipv6_end:
    description:
      - End address for ipv6 range.
    required: false
    default: none
  ipv6_gateway:
    description:
      - Gateway IP for ipv6 range.
    required: false
    default: none
  ipv6_cidr:
    description:
      - The CIDR of IPv6 network, must be at least /64
    required: false
    default: none
  for_virtual_network:
    description:
      - true if VLAN is of Virtual type, false if Direct
    required: false
    default: none
  vlan:
    description:
      - the ID or VID of the VLAN.
      - If not specified, will be defaulted to the vlan of the network or if vlan of the network is null - to Untagged
    required: false
    default: null
  url:
    description:
      - URL for the cluster
    required: false
    default: null
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
# Ensure a vlan_ip_range is present
- local_action:
    module: cs_vlan_ip_range
    zone: zone01
    ipv4_start: 1.0.0.10
    ipv4_end: 1.0.0.100
    ipv4_netmask: 255.255.255.0
    vlan: 200

# Ensure a vlan_ip_range is absent
- local_action:
    module: cs_vlan_ip_range
    zone: zone01
    ipv4_start: 1.0.0.10
    state: absent
'''

RETURN = '''
---
id:
  description: UUID of the VLAN IP range.
  returned: success
  type: string
  sample: a3fca65a-7db1-4891-b97c-48806a978a96
account:
  description: The account for th VLAN IP range.
  returned: success
  type: string
  sample: Bob
domain:
  description: Domain for th VLAN IP range.
  returned: success
  type: string
  sample: example.co.uk
domainid:
  description: UUID of the domain for the VLAN IP range.
  returned: success
  type: string
  sample: 0fd61425-4531-4c42-9a28-f0415daf4f19

'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    CloudStackException,
    cs_argument_spec,
    cs_required_together,
)


class AnsibleCloudStackVlanIpRange(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackVlanIpRange, self).__init__(module)
        self.returns = {
            'startip': 'ipv4_start',
            'endip': 'ipv4_end',
            'gateway': 'ipv4_gateway',
            'netmask': 'ipv4_netmask',
            'startipv6': 'ipv6_start',
            'endipv6': 'ipv6_end',
            'ip6gateway': 'ipv6_gateway',
            'ip6cidr': 'ipv6_cidr',
            'vlan': 'vlan',
            'forvirtualnetwork': 'for_virtual_network',
        }
        self.vlan_ip_range = None
        self.physical_network = None
        self.network = None
        self.zone = None
        self.project = None
        self.pod = None
        self.domain = None
        self.account = None

    def _get_common_args(self):
        args = {
            'physicalnetworkid': self.get_physical_network(key='id'),
            'projectid': self.get_project(key='id'),
            'account': self.get_account(key='id'),
            'domainid': self.get_domain(key='id'),
            'networkid': self.get_network(key='id'),
            'zoneid': self.get_zone(key='id'),
            'podid': self.get_pod(key='id'),
            'vlan': self.module.params.get('vlan'),
            'startip': self.module.params.get('ipv4_start'),
            'endip': self.module.params.get('ipv4_end'),
            'gateway': self.module.params.get('ipv4_gateway'),
            'netmask': self.module.params.get('ipv4_netmask'),
            'startipv6': self.module.params.get('ipv6_start'),
            'endipv6': self.module.params.get('ipv6_end'),
            'ip6gateway': self.module.params.get('ipv6_gateway'),
            'ip6cidr': self.module.params.get('ipv6_cidr'),
        }
        return args

    def get_vlan_ip_range(self, key=None):
        if self.vlan_ip_range:
            return self.vlan_ip_range
        account = self.module.params.get('account')
        domain = self.module.params.get('domain')
        zone = self.module.params.get('zone')
        project = self.module.params.get('project')
        pod = self.module.params.get('pod')
        physical_network = self.module.params.get('physical_network')
        ipv4_start = self.module.params.get('ipv4_start')
        ipv6_start = self.module.params.get('ipv6_start')

        args = {}
        if account and domain:
            args['account'] = self.get_account(key='id')
            args['domainid'] = self.get_domain(key='id')

        if zone:
            args['zoneid'] = self.get_zone(key='id')

        if physical_network:
            args['physicalnetworkid'] = self.get_physical_network(key='id')

        if pod:
            args['podid'] = self.get_pod(key='id')

        if project:
            args['projectid'] = self.get_project(key='id')

        if not ipv4_start and not ipv6_start:
            self.module.fail_json(msg="Either ipv4_start or ipv6_start must be specified")

        ranges = self.cs.listVlanIpRanges(**args)
        if ranges:
            for r in ranges['vlaniprange']:
                if ipv4_start and ipv4_start == r['startip']:
                    self.vlan_ip_range = r
                    break

                if ipv6_start and ipv6_start == r['startipv6']:
                    self.vlan_ip_range = r
                    break

        return self.vlan_ip_range

    def present_vlan_ip_range(self):
        range = self.get_vlan_ip_range()
        if range:
            return range
        else:
            range = self._create_vlan_ip_range()
        return range

    def _create_vlan_ip_range(self):
        args = self._get_common_args()
        if not self.module.check_mode:
            res = self.cs.createVlanIpRange(**args)
            if 'errortext' in res:
                self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
            range = res['vlan']

        self.result['changed'] = True
        return range

    def absent_vlan_ip_range(self):
        range = self.get_vlan_ip_range()
        if range:
            self.result['changed'] = True

            args = {
                'id': range['id'],
            }
            if not self.module.check_mode:
                res = self.cs.deleteVlanIpRange(**args)
                if 'errortext' in res:
                    self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
        return range

    def get_pod(self, key=None):
        pod = self.module.params.get('pod')
        if not pod:
            return None
        args = {
            'name': self.module.params.get('pod'),
            'zoneid': self.get_zone(key='id'),
        }
        pods = self.cs.listPods(**args)
        if pods:
            return self._get_by_key(key, pods['pod'][0])
        self.module.fail_json(msg="Pod %s not found in zone %s." % (self.module.params.get('pod'), self.get_zone(key='name')))

    def get_physical_network(self, key=None):
        if self.physical_network:
            return self._get_by_key(key, self.physical_network)

        physical_network = self.module.params.get('physical_network')
        networks = self.cs.listPhysicalNetworks()

        if not networks:
            self.module.fail_json(msg="No physical networks available. Please create a physical network first")

        # use the first network if no physical_network param given
        if not physical_network:
            self.physical_network = networks['physicalnetwork'][0]
            return self._get_by_key(key, self.physical_network)

        if networks:
            for n in networks['physicalnetwork']:
                if physical_network.lower() in [n['name'].lower(), n['id']]:
                    self.physical_network = n
                    return self._get_by_key(key, self.physical_network)
        self.module.fail_json(msg="physical network '%s' not found" % zone)


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        zone=dict(default=None),
        physical_network=dict(default=None),
        network=dict(default=None),
        pod=dict(default=None),
        project=dict(default=None),
        domain=dict(default=None),
        account=dict(default=None),
        vlan=dict(default=None),
        ipv4_start=dict(default=None),
        ipv4_end=dict(default=None),
        ipv4_gateway=dict(default=None),
        ipv4_netmask=dict(default=None),
        ipv6_start=dict(default=None),
        ipv6_end=dict(default=None),
        ipv6_gateway=dict(default=None),
        ipv6_cidr=dict(default=None),
        state=dict(choices=['present', 'absent'], default='present'),
        url=dict(default=None),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )

    try:
        acs_vlan_ip_range = AnsibleCloudStackVlanIpRange(module)

        state = module.params.get('state')
        if state in ['absent']:
            range = acs_vlan_ip_range.absent_vlan_ip_range()
        else:
            range = acs_vlan_ip_range.present_vlan_ip_range()

        result = acs_vlan_ip_range.get_result(range)

    except CloudStackException as e:
        module.fail_json(msg='CloudStackException: %s' % str(e))

    module.exit_json(**result)

if __name__ == '__main__':
    main()
