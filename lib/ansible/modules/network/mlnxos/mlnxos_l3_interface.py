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
from __future__ import absolute_import, division, print_function

from ansible.modules.network.mlnxos.mlnxos_interface import MlnxosInterfaceApp
from ansible.module_utils.mlnxos import get_interfaces_config


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
  aggregate:
    description: List of L3 interfaces definitions
  if_type:
    description: interface type
    default: ethernet
    choices: ['ethernet', 'loopback']
  state:
    description:
      - State of the L3 interface configuration.
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: Set Eth1/1 IPv4 address
  mlnxos_l3_interface:
    name: Eth1/1
    ipaddress: 192.168.0.1/24

- name: remove Eth1/1 IPv4 address
  mlnxos_l3_interface:
    name: Eth1/1
    state: absent

- name: Set IP addresses on aggregate
  mlnxos_l3_interface:
    aggregate:
      - { name: "Eth1/1", ipv4: 192.168.2.10/24 }
      - { name: "Eth1/2", ipv4: 192.168.3.10/24 }

- name: Remove IP addresses on aggregate
  mlnxos_l3_interface:
    aggregate:
      - { name: "Eth1/1" }
      - { name: "Eth1/2" }
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always, except for the platforms that use Netconf transport to
              manage the device.
  type: list
  sample:
    - interface Eth1/1
    - no switchport
    - ip address 1.2.3.4/24
"""


class MlnxosL3InterfaceApp(MlnxosInterfaceApp):
    @classmethod
    def _get_element_spec(cls):
        return dict(
            name=dict(),
            ipaddress=dict(),
            if_type=dict(default='ethernet',
                         choices=['ethernet', 'loopback']),
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
                'if_type': module_params['if_type'],
                'state': module_params['state'],
            }
            self.validate_param_values(params)
            self._required_config.append(params)

    def load_current_config(self):
        super(MlnxosL3InterfaceApp, self).load_current_config()
        config = get_interfaces_config(self._module, "loopback")

        for item in config:
            name = self.get_if_name(item)
            name = name.split()[1]
            self._current_config[name] = self._create_if_data(
                name, item, 'loopback')

    def _create_if_data(self, name, item, if_type='ethernet'):
        return {
            'name': name,
            'ipaddress': self.extract_ipaddress(item),
            'state': 'present',
            'if_type': if_type
        }

    @classmethod
    def extract_ipaddress(cls, item):
        ipaddress = cls.get_config_attr(item, "IP Address")
        if ipaddress:
            return ipaddress.replace(" ", "")
        return cls.get_config_attr(item, "Internet Address")

    def _is_allowed_missing_interface(self, req_if):
        return req_if['if_type'] == 'loopback'

    def _generate_if_commands(self, name, req_if, curr_if):
        state = req_if['state']
        if req_if['if_type'] == 'ethernet':
            interface_prefix = self.get_if_cmd(name)
        else:
            interface_prefix = "interface loopback %s" % name
        curr_ipaddress = curr_if.get('ipaddress') if curr_if else None

        if state == 'absent':
            if curr_ipaddress:
                cmd = "no ip address"
                self.add_command_to_interface(interface_prefix, cmd)
                self._commands.append('exit')
        else:
            req_ipaddress = req_if.get('ipaddress')
            if curr_ipaddress != req_ipaddress:
                if req_if['if_type'] == 'ethernet':
                    cmd = "no switchport force"
                    self.add_command_to_interface(interface_prefix, cmd)
                cmd = "ip address %s" % req_ipaddress
                self.add_command_to_interface(interface_prefix, cmd)
                self._commands.append('exit')
        with open('/tmp/l3.log', 'w') as fp:
            fp.write(str(self._commands))


if __name__ == '__main__':
    MlnxosL3InterfaceApp.main()
