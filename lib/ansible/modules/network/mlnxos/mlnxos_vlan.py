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

from copy import deepcopy
from time import sleep

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network_common import conditional, \
    remove_default_spec

from ansible.module_utils.mlnxos import get_interfaces_config, show_cmd
from ansible.module_utils.mlnxos import mlnxos_argument_spec
from ansible.modules.network.mlnxos import BaseMlnxosApp
import re
import json


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: mlnxos_interface
version_added: "2.5"
author: "Alex Tabachnik (@atabachnik)"
short_description: Manage Interface on MLNX-OS network devices
description:
  - This module provides declarative management of vlan
    on MLNX-OS network devices.
notes:
  -
options:
  vlan_id:
    description:
      - Single VLAN ID.
    required: false
    default: null
  interface:
    description:
      - number of interface
    required: false
    default: null
  state:
    description:
      - create or remove vlan
    default: present
    choices: ['present', 'absent']
  mode:
    description:
      - set interface mode
    default: hybrid
    choices: ['access', 'hybrid', 'trunk', 'dot1q-tunnel', 'access-dcb']
"""

EXAMPLES = """
- name: run add vlan and assign interfaces
  mlnxos_vlan:
    vlan_id: 13
    state: present
    interface: Eth1/13,Eth1/14
    mode: hybrid
    authorize: yes
    provider:
      host: "{{ inventory_hostname }}"
- name: run add vlan only
  mlnxos_vlan:
    vlan_id: 13
    state: present
    authorize: yes
    provider:
      host: "{{ inventory_hostname }}"
- name: run remove switch interfaces from vlan
  mlnxos_vlan:
    vlan_id: 13
    state: absent
    interface: Eth1/13,Eth1/14
    mode: hybrid
    authorize: yes
    provider:
      host: "{{ inventory_hostname }}"
- name: run remove vlan
  mlnxos_vlan:
    vlan_id: 13
    state: absent
    authorize: yes
    provider:
      host: "{{ inventory_hostname }}"

"""

RETURN = """
"""


def vlan_range_to_list(vlans):
    result = []
    if vlans:
        for part in vlans.split(','):
            if part == 'none':
                break
            if '-' in part:
                start, end = part.split('-')
                start, end = int(start), int(end)
                result.extend([str(i) for i in range(start, end + 1)])
            else:
                result.append(part)
    return result

def numerical_sort(iterable):
    """Sort list of strings (VLAN IDs) that are digits in numerical order.
    """
    as_int_list = []
    for vlan in iterable:
        as_int_list.append(int(vlan))
    as_int_list.sort()

    as_str_list = []
    for vlan in as_int_list:
        as_str_list.append(str(vlan))
    return as_str_list


class MlnxosVlanApp(BaseMlnxosApp):
    IFNAME_REGEX = re.compile(r"^.*(Eth\d+\/\d+)")

    @classmethod
    def _get_element_spec(cls):
        return dict(
            vlan_id=dict(),
            vlan_name=dict(),
            interfaces=dict(type='list', default=[]),
            state=dict(default='present',
                       choices=['present', 'absent']),
            mode=dict(default='trunk',
                       choices=['access', 'hybrid', 'trunk', 'dot1q-tunnel',
                                'access-dcb']),
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
                'vlan_id': module_params['vlan_id'],
                'vlan_name': module_params['vlan_name'],
                'interfaces': module_params['interfaces'],
                'state': module_params['state'],
                'mode': module_params['mode']
            }
            self.validate_param_values(params)
            self._required_config.append(params)

    @classmethod
    def _get_aggregate_spec(cls, element_spec):
        aggregate_spec = deepcopy(element_spec)
        aggregate_spec['vlan_id'] = dict(required=True)
        # remove default in aggregate spec, to handle common arguments
        remove_default_spec(aggregate_spec)
        return aggregate_spec

    @classmethod
    def get_switchport_command_name(cls, switchportname):
        return switchportname.replace("Eth", "ethernet ")

    def init_module(self):
        """ main entry point for module execution
        """
        element_spec = self._get_element_spec()
        aggregate_spec = self._get_aggregate_spec(element_spec)
        if aggregate_spec:
            argument_spec = dict(
                aggregate=dict(type='list', elements='dict',
                               options=aggregate_spec),
            )
        else:
            argument_spec = dict()
        argument_spec.update(element_spec)
        argument_spec.update(mlnxos_argument_spec)
        required_one_of = [['vlan_id', 'aggregate']]
        mutually_exclusive = [['vlan_id', 'aggregate']]
        self._module = AnsibleModule(
            argument_spec=argument_spec,
            required_one_of=required_one_of,
            mutually_exclusive=mutually_exclusive,
            supports_check_mode=True)

    @classmethod
    def get_interfaces_of_vlan(cls, vlan_data):
        ports = cls.get_config_attr(vlan_data, 'Ports')
        members = []
        for if_name in ports.split(","):
            match = cls.IFNAME_REGEX.match(if_name)
            if match:
                members.append(match.group(1))
        return members


    def _create_vlan_data(self, vlan_id, vlan_data):
        return {
            'vlan_id': vlan_id,
            'interfaces': self.get_interfaces_of_vlan(vlan_data),
            'vlan_name': self.get_config_attr(vlan_data, 'Name')
        }

    def load_current_config(self):
        # called in base class in run function
        self._current_config = dict()
        vlan_config = show_cmd(self._module, "show vlan")
        for vlan_id, vlan_data in vlan_config.iteritems():
            self._current_config[vlan_id] = \
                self._create_vlan_data(vlan_id, vlan_data)

    def add_command_to_interface(self, interface, cmd):
        if interface not in self._commands:
            self._commands.append(interface)
        self._commands.append(cmd)

    def generate_commands(self):
        for req_conf in self._required_config:
            state = req_conf['state']
            vlan_id = req_conf['vlan_id']
            if state == 'absent':
                if vlan_id in self._current_config:
                    self._commands.append('no vlan %s' % vlan_id)
            else:
                self._generate_vlan_commands(vlan_id, req_conf)
        if self._commands:
            self._commands.append("exit")

    def _generate_vlan_commands(self, vlan_id, req_conf):
        curr_vlan = self._current_config.get(vlan_id, {})
        if not curr_vlan:
            cmd = "vlan " + vlan_id
            self._commands.append("vlan %s" % vlan_id)
            self._commands.append("exit")
        vlan_name = req_conf['vlan_name']
        if vlan_name:
            if vlan_name != curr_vlan.get('vlan_name'):
                self._commands.append("vlan %s name %s" % (vlan_id, vlan_name))
        curr_members = set(curr_vlan.get('interfaces', []))
        req_members = req_conf['interfaces']
        mode = req_conf['mode']
        for member in req_members:
            if member in curr_members:
                continue
            if_name = self.get_switchport_command_name(member)
            cmd = "interface %s switchport mode %s" % (if_name, mode)
            self._commands.append(cmd)
            cmd = "interface %s switchport %s allowed-vlan add %s" % (
                if_name, mode, vlan_id)
            self._commands.append(cmd)
        req_members = set(req_members)
        for member in curr_members:
            if member in req_members:
                continue
            if_name = self.get_switchport_command_name(member)
            cmd = "interface %s switchport %s allowed-vlan remove %s" % (
                if_name, mode, vlan_id)
            self._commands.append(cmd)


if __name__ == '__main__':
    MlnxosVlanApp.main()
