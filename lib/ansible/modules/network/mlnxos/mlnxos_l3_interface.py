#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2017, Ansible by Red Hat, inc
#
# This file is part of Ansible by Red Hat
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#
import re

from ansible.module_utils.mlnxos import get_bgp_summary
from ansible.modules.network.mlnxos.mlnxos_interface import MlnxosInterfaceApp


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: mlnxos_l3_interface
version_added: "2.5"
author: "Ricardo Carrillo Cruz (@rcarrillocruz)"
short_description: Manage L3 interfaces on MLNX-OS network devices
description:
  - This module provides declarative management of L3 interfaces
    on MLNX-OS network devices.
notes:
options:
  name:
    description:
      - Name of the L3 interface.
  ipaddress:
    description:
      - IPv4 of the L3 interface: format 1.2.3.4/24
  bgp_router_as:
    description:
      - bgp router AS number
  bgp_neighbors:
    description:
      - list of bgp neighbor router IP addresses
  aggregate:
    description: List of L3 interfaces definitions
  state:
    description:
      - State of the L3 interface configuration.
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: Set ethernet 1/1 IPv4 address
  mlnxos_l3_interface:
    name: ethernet 1/1
    ipaddress: 192.168.0.1/24

- name: remove ethernet 1/1 IPv4 address
  mlnxos_l3_interface:
    name: ethernet 1/1
    ipaddress: 192.168.0.1/24
    bgp_router_as: 100
    bgp_neighbors:
      - 192.168.0.2
      - 192.168.0.3
- name: configure bgp ethernet 1/1
  mlnxos_l3_interface:
    name: ethernet 1/1
    state: absent

- name: Set IP addresses on aggregate
  mlnxos_l3_interface:
    aggregate:
      - { name: "ethernet 1/1", ipv4: 192.168.2.10/24 }
      - { name: "ethernet 1/2", ipv4: 192.168.3.10/24 }

- name: Remove IP addresses on aggregate
  mlnxos_l3_interface:
    aggregate:
      - { name: "ethernet 1/1" }
      - { name: "ethernet 1/2" }
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always, except for the platforms that use Netconf transport to
              manage the device.
  type: list
  sample:
    - interface ethernet 1/1
    - no switchport
    - ip address 1.2.3.4/24
"""


class MlnxosL3InterfaceApp(MlnxosInterfaceApp):
    LOCAL_AS_REGEX = \
        r"BGP router identifier ([0-9\.]+), local AS number (\d+)"
    NEIGHBOR_REGEX = \
        r"^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+\d+\s+(\d+)"

    def __init__(self):
        super(MlnxosL3InterfaceApp, self).__init__()
        self._local_bgp_config = {}
        self._neighbor_bgp_config = []
        self._add_bgp = False

    @classmethod
    def _get_element_spec(cls):
        return dict(
            name=dict(),
            ipaddress=dict(),
            bgp_router_as=dict(type='int'),
            bgp_neighbors=dict(type='list'),
            state=dict(default='present',
                       choices=['present', 'absent'])
        )

    def get_required_config(self):
        self._required_config = list()
        module_params = self._module.params
        aggregate = module_params.get('aggregate')
        if aggregate:
            for item in aggregate:
                for key in item:
                    if item.get(key) is None:
                        item[key] = module_params[key]

                self.validate_param_values(item, item)
                self._required_config.append(item.copy())
        else:
            params = {
                'name': module_params['name'],
                'ipaddress': module_params['ipaddress'],
                'state': module_params['state'],
                'bgp_router_as': module_params['bgp_router_as'],
                'bgp_neighbors': module_params['bgp_neighbors'],
            }
            self.validate_param_values(params)
            self._required_config.append(params)

    def _set_bgp_config(self, bgp_config):
        match = re.search(self.LOCAL_AS_REGEX, bgp_config, re.M)
        if match:
            self._local_bgp_config['bgp_router_ip'] = match.group(1)
            self._local_bgp_config['bgp_router_as'] = int(match.group(2))
        matches = re.findall(self.NEIGHBOR_REGEX, bgp_config, re.M) or []
        for match in matches:
            self._neighbor_bgp_config.append((match[0], int(match[1])))

    def load_current_config(self):
        super(MlnxosL3InterfaceApp, self).load_current_config()
        needed_bgp = False
        for req_if in self._required_config:
            if req_if['bgp_router_as']:
                needed_bgp = True
                break
        if needed_bgp:
            bgp_config = get_bgp_summary(self._module)
            if bgp_config:
                self._set_bgp_config(bgp_config)

    def _create_if_data(self, item):
        return {
            'name': self.get_if_name(item),
            'ipaddress': self.extract_ipaddress(item),
            'state': 'present'
        }

    @classmethod
    def extract_ipaddress(cls, item):
        ipaddress = cls.get_config_attr(item, "IP Address")
        if ipaddress:
            return ipaddress.replace(" ", "")

    def _generate_if_commands(self, name, req_if, curr_if):
        state = req_if['state']
        interface = 'interface ' + name
        curr_ipaddress = curr_if.get('ipaddress')
        bgp_as = req_if['bgp_router_as'] or 0
        bgp_neighbors = req_if['bgp_neighbors'] or []
        curr_bgp_as = self._local_bgp_config.get('bgp_router_as', 0)

        if state == 'absent':
            if curr_ipaddress:
                cmd = "no ip address"
                self.add_command_to_interface(interface, cmd)
                self._commands.append('exit')
            if bgp_as and bgp_as == curr_bgp_as:
                self._commands.append('no router bgp %s' % bgp_as)
        else:
            req_ipaddress = req_if.get('ipaddress')
            if curr_ipaddress != req_ipaddress:
                cmd = "no switchport force"
                self.add_command_to_interface(interface, cmd)
                cmd = "ip address %s" % req_ipaddress
                self.add_command_to_interface(interface, cmd)
                self._commands.append('exit')
            if bgp_as:
                if bgp_as != curr_bgp_as:
                    if curr_bgp_as:
                        self._commands.append(
                            'no router bgp %s' % curr_bgp_as)
                    self._add_bgp = True
                    self._commands.append('router bgp %s' % bgp_as)
                    self._commands.append('exit')
                for neighbor in bgp_neighbors:
                    found = False
                    for curr_neighbor in self._neighbor_bgp_config:
                        if curr_neighbor == (neighbor, bgp_as):
                            found = True
                            break
                    if found:
                        continue
                    self._add_bgp = True
                    self._commands.append(
                        'router bgp %s neighbor %s remote-as %s' %
                        (bgp_as, neighbor, bgp_as))

    def generate_commands(self):
        super(MlnxosL3InterfaceApp, self).generate_commands()
        if self._add_bgp:
            commands = ['ip routing', 'protocol bgp']
            commands.extend(self._commands)
            self._commands = commands


if __name__ == '__main__':
    MlnxosL3InterfaceApp.main()
