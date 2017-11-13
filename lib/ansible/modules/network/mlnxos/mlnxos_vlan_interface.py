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

from ansible.module_utils.basic import AnsibleModule

from ansible.module_utils.mlnxos import get_interfaces_config, show_cmd
from ansible.module_utils.mlnxos import mlnxos_argument_spec
from ansible.modules.network.mlnxos import BaseMlnxosApp


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: mlnxos_vlan_interface
version_added: "2.5"
author: "Samer Deeb (@samerd)"
short_description: Manage VLAN Interface on MLNX-OS network devices
description:
  - This module provides declarative management of vlan interface management
    on MLNX-OS network devices.
notes:
  -
options:
  vlan_id:
    description:
      - VLAN ID.
    required: true
  state:
    description:
      - vlan interface state
    required: false
    default: present
    choices: ['present', 'absent']
  ipaddress:
    description:
      - ip addesss of the vlan interface
  ipl:
    description:
      - ipl ID
    required: false
  ipl_peer:
    description:
      - IPL peer IP address
    required: false
  magp:
    description:
      - magp ID
    required: false
  magp_router_ip:
    description:
      - MAGP router ip address
    required: false
  magp_router_mac:
    description:
      - MAGP router MAC address
    required: false
"""

EXAMPLES = """
- name: run add vlan interface with ipl
  mlnxos_vlan_interface:
    vlan_id: 322
    state: present
    ipaddress: 192.168.7.1/24
    ipl: 1
    ipl_peer: 192.168.7.2

- name: run add vlan interface with magp
  mlnxos_vlan_interface:
    vlan_id: 320
    state: present
    ipaddress: 192.168.8.1/24
    magp: 103
    magp_router_ip: 192.168.8.2
    magp_router_mac: AA:1B:2C:3D:4E:5F
"""

RETURN = """
commands:
    description: The list of configuration mode commands to send to the device.
      returned: always, except for the platforms that use Netconf transport to
                manage the device.
    type: list
    sample:
        vlan 234
        exit
        interface ethernet Eth1/1 switchport mode access
        interface ethernet Eth1/1 switchport access allowed-vlan add 234
        interface ethernet Eth1/1 switchport access allowed-vlan remove 234
"""


class MlnxosVlanInterfaceApp(BaseMlnxosApp):

    @classmethod
    def _get_element_spec(cls):
        return dict(
            vlan_id=dict(type='int', required=True),
            state=dict(default='present',
                       choices=['present', 'absent']),
            ipaddress=dict(),
            ipl=dict(type='int'),
            ipl_peer=dict(),
            magp=dict(type='int'),
            magp_router_ip=dict(),
            magp_router_mac=dict(),
        )

    def get_required_config(self):
        self._required_config = list()
        module_params = self._module.params
        vlan_if = {
            'vlan_id': module_params['vlan_id'],
            'state': module_params['state'],
            'ipaddress': module_params['ipaddress'],
            'ipl': module_params['ipl'],
            'ipl_peer': module_params['ipl_peer'],
            'magp': module_params['magp'],
            'magp_router_ip': module_params['magp_router_ip'],
            'magp_router_mac': module_params['magp_router_mac'],
        }
        self.validate_param_values(vlan_if)
        self._required_config.append(vlan_if)

    @classmethod
    def get_vlan_id(cls, item):
        header = cls.get_config_attr(item, "header")
        return int(header.split()[1])

    def init_module(self):
        """ main entry point for module execution
        """
        element_spec = self._get_element_spec()
        argument_spec = dict()
        argument_spec.update(element_spec)
        argument_spec.update(mlnxos_argument_spec)
        self._module = AnsibleModule(
            argument_spec=argument_spec,
            supports_check_mode=True)

    def _create_vlan_if_data(self, item):
        vlan_id = self.get_vlan_id(item)
        vlan_if_data = {
            'vlan_id': vlan_id,
            'ipaddress': self.get_config_attr(item, "Internet Address"),
        }
        self._current_config[vlan_id] = vlan_if_data

    def _update_mlag_data(self, mlag_data):
        if not mlag_data:
            return
        mlag_summary = mlag_data.get("MLAG IPLs Summary", {})
        for ipl_id, ipl_list in mlag_summary.iteritems():
            for ipl_data in ipl_list:
                vlan_id = int(ipl_data.get("Vlan Interface", 0))
                vlan_data = self._current_config.get(vlan_id)
                if vlan_data:
                    vlan_data['ipl'] = int(ipl_id)
                    vlan_data['ipl_peer'] = ipl_data.get("Peer IP address")

    def _update_magp_data(self, magp_data):
        if not magp_data:
            return
        for magp_item in magp_data:
            vlan_id = int(magp_item.get("Interface vlan", 0))
            vlan_data = self._current_config.get(vlan_id)
            if vlan_data:
                magp_id = None
                magp_header = magp_item.get("header")
                if magp_header:
                    magp_id = int(magp_header.split()[1])
                vlan_data['magp'] = magp_id
                vlan_data['magp_router_ip'] = magp_item.get("Virtual IP")
                vlan_data['magp_router_mac'] = magp_item.get("Virtual MAC")

    def load_current_config(self):
        # called in base class in run function
        self._current_config = dict()
        config = get_interfaces_config(self._module, "vlan")
        for item in config:
            self._create_vlan_if_data(item)

        json_fmt = True
        fail_on_error = False

        cmd = "show mlag"
        mlag_data = show_cmd(self._module, cmd, json_fmt, fail_on_error)
        self._update_mlag_data(mlag_data)

        cmd = "show magp"
        magp_data = show_cmd(self._module, cmd, json_fmt, fail_on_error)
        self._update_magp_data(magp_data)

    def generate_commands(self):
        for req_valn_if in self._required_config:
            vlan_id = req_valn_if['vlan_id']
            curr_vlan_data = self._current_config.get(vlan_id, {})
            if_vlan_prefix = "interface vlan %s" % vlan_id
            state = req_valn_if['state']
            if not curr_vlan_data:
                if state == 'absent':
                    continue
                self._commands.append("vlan %s" % vlan_id)
                self._commands.append("exit")
                self._commands.append(if_vlan_prefix)
                self._commands.append("exit")
            else:
                if state == 'absent':
                    self._commands.append("no %s" % if_vlan_prefix)
                    continue
            self._generate_ipaddress_commands(
                if_vlan_prefix, req_valn_if, curr_vlan_data)
            self._generate_mlag_commands(
                if_vlan_prefix, req_valn_if, curr_vlan_data)
            self._generate_magp_commands(
                if_vlan_prefix, req_valn_if, curr_vlan_data)
        if self._commands:
            self._commands.append("exit")

    def _generate_ipaddress_commands(self, if_vlan_prefix, req_valn_if,
                                     curr_vlan_data):
        req_ipaddress = req_valn_if['ipaddress']
        if req_ipaddress:
            curr_ipaddress = curr_vlan_data.get('ipaddress')
            if req_ipaddress != curr_ipaddress:
                self._commands.append(
                    "%s ip address %s" % (if_vlan_prefix, req_ipaddress))

    def _generate_mlag_commands(self, if_vlan_prefix, req_valn_if,
                                curr_vlan_data):
        req_ipl = req_valn_if['ipl']
        if req_ipl:
            req_ipl_peer = req_valn_if['ipl_peer']
            curr_ipl = curr_vlan_data.get('ipl')
            curr_ipl_peer = curr_vlan_data.get('ipl_peer')
            if curr_ipl != req_ipl or curr_ipl_peer != req_ipl_peer:
                self._commands.append(
                    "%s ipl %s peer-address %s" %
                    (if_vlan_prefix, req_ipl, req_ipl_peer))

    def _generate_magp_commands(self, if_vlan_prefix, req_valn_if,
                                curr_vlan_data):
        req_magp = req_valn_if['magp']
        if req_magp:
            req_magp_router_ip = req_valn_if['magp_router_ip']
            req_magp_router_mac = req_valn_if['magp_router_mac']
            curr_magp = curr_vlan_data.get('magp')
            curr_magp_router_ip = curr_vlan_data.get('magp_router_ip')
            curr_magp_router_mac = curr_vlan_data.get('magp_router_mac')
            magp_prefix = "%s magp %s" % (if_vlan_prefix, req_magp)
            if curr_magp != req_magp:
                self._commands.append(magp_prefix)
                self._commands.append('exit')
            if req_magp_router_ip and \
                    req_magp_router_ip != curr_magp_router_ip:
                self._commands.append(
                    "%s ip virtual-router address %s" %
                    (magp_prefix, req_magp_router_ip))
            if req_magp_router_mac and \
                    req_magp_router_mac != curr_magp_router_mac:
                self._commands.append(
                    "%s ip virtual-router mac-address %s" %
                    (magp_prefix, req_magp_router_mac))


if __name__ == '__main__':
    MlnxosVlanInterfaceApp.main()
