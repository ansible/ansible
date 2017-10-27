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
from ansible.modules.network.mlnxos.mlnxos_interface import MlnxosInterfaceApp
from ansible.module_utils.basic import AnsibleModule  # noqa:F401


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

- name: ethernet 1/1 IPv4 address
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
    @classmethod
    def _get_element_spec(cls):
        return dict(
            name=dict(),
            ipaddress=dict(),
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
            }
            self.validate_param_values(params)
            self._required_config.append(params)

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

        if state == 'absent':
            if curr_ipaddress:
                cmd = "no ip address"
                self.add_command_to_interface(interface, cmd)
        else:
            req_ipaddress = req_if.get('ipaddress')
            if curr_ipaddress != req_ipaddress:
                cmd = "no switchport force"
                self.add_command_to_interface(interface, cmd)
                cmd = "ip address %s" % req_ipaddress
                self.add_command_to_interface(interface, cmd)


if __name__ == '__main__':
    MlnxosL3InterfaceApp.main()
