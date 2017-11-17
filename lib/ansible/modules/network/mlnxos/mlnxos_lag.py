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
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: mlnxos_lag
version_added: "2.5"
author: "Samer Deeb (@samerd)"
short_description: Manage Lags on MLNX-OS network devices
description:
  - >-
      This module provides declarative management of Lags
      on MLNX-OS network devices.
notes:
  - tested on Mellanox OS 3.6.4000
options:
  lag_id:
    description:
      - "port channel ID of the LAG (1-4096)."
    required: true
  lag_mode:
    description:
      - LAG mode
    choices: ['on', 'passive', 'active']
  mtu:
    description:
      - Maximum size of transmit packet.
  aggregate:
    description: List of lags definitions.
  members:
    description:
      - ethernet interfaces LAG members.
"""

EXAMPLES = """
- name: configure LAG
  mlnxos_lag:
    lag_id: 5
    mtu: 1512
    members:
      - Eth1/6
      - Eth1/7
    lag_mode: on
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device.
  returned: always
  type: list
  sample:
    - interface port-channel 5
    - exit
    - interface port-channel 5 mtu 1500 force
    - interface ethernet 1/16 channel-group 5 mode on
    - interface ethernet 1/17 channel-group 5 mode on
"""

import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems

from ansible.module_utils.mlnxos import BaseMlnxosApp
from ansible.module_utils.mlnxos import get_interfaces_config
from ansible.module_utils.mlnxos import mlnxos_argument_spec


class MlnxosLagApp(BaseMlnxosApp):
    LAG_ID_REGEX = re.compile(r"^(.*)Po(\d+)(.*)$")
    IF_NAME_REGEX = re.compile(r"^Eth(\d+\/\d+)(.*)$")
    PORT_CHANNEL = 'port-channel'
    CHANNEL_GROUP = 'channel-group'

    def init_module(self):
        """ initialize module
        """
        element_spec = dict(
            lag_id=dict(required=True, type='int'),
            members=dict(required=True, type='list'),
            lag_mode=dict(required=True, choices=['active', 'on', 'passive']),
            mtu=dict(type='int'),
            vlan_id=dict(type='int'),
            ipl=dict(type='int'),
            dcb_pfc=dict(choices=['enabled', 'disabled']),
        )
        argument_spec = dict()

        argument_spec.update(element_spec)
        argument_spec.update(mlnxos_argument_spec)
        self._module = AnsibleModule(
            argument_spec=argument_spec,
            supports_check_mode=True)

    def get_required_config(self):
        module_params = self._module.params
        lag_params = {
            'lag_id': module_params['lag_id'],
            'lag_mode': module_params['lag_mode'],
            'mtu': module_params['mtu'],
            'members': module_params['members'],
            'vlan_id': module_params['vlan_id'],
            'ipl': module_params['ipl'],
            'dcb_pfc': module_params['dcb_pfc'],
        }
        raw_members = lag_params['members']
        if raw_members:
            members = [self.extract_if_name(member) for member in raw_members]
            lag_params['members'] = members

        self.validate_param_values(lag_params)
        self._required_config = lag_params

    def validate_lag_id(self, value):
        if value and not 1 <= int(value) <= 4096:
            self._module.fail_json(msg='lag id must be between 1 and 4096')

    @classmethod
    def get_lag_id(cls, item):
        header = cls.get_config_attr(item, "header")
        return cls.extract_lag_id(header)

    @classmethod
    def extract_lag_id(cls, header):
        match = cls.LAG_ID_REGEX.match(header)
        if match:
            return match.group(2)

    @classmethod
    def extract_if_name(cls, member):
        match = cls.IF_NAME_REGEX.match(member)
        if match:
            return match.group(1)

    @classmethod
    def get_lag_members(cls, lag_item):
        lag_members = cls.get_config_attr(lag_item, "Member Ports")
        lag_members = lag_members.split()
        return lag_members

    def load_current_config(self):
        interface_type = self.PORT_CHANNEL
        lag_config = get_interfaces_config(self._module, interface_type)
        lag_summary = get_interfaces_config(self._module, interface_type,
                                            summary=True)
        self._current_config = {}

        for item in lag_config:
            lag_id = self.get_lag_id(item)
            if lag_id:
                lag_id = int(lag_id)
            obj = {
                'lag_id': lag_id,
                'mtu': self.get_mtu(item),
                'members': []
            }
            self._current_config[lag_id] = obj

        for lag_name, lag_data in iteritems(lag_summary):
            lag_id = self.extract_lag_id(lag_name)
            if not lag_id:
                continue
            lag_id = int(lag_id)
            obj = self._current_config.get(lag_id)
            if not obj:
                continue
            lag_item = lag_data[0]
            lag_members = self.get_lag_members(lag_item)
            obj['members'] = [self.extract_if_name(member) for member in
                              lag_members]

    def _generate_initial_commands(self, lag_id, lag_obj):
        if not lag_obj:
            self._commands.append(
                "interface %s %s" % (self.PORT_CHANNEL, lag_id))
            self._commands.append("exit")
            curr_mtu = lag_obj.get('mtu', 0)
            mtu = self._required_config['mtu']
            if mtu and int(curr_mtu) != mtu:
                self._commands.append("interface %s %s mtu %s force" %
                                      (self.PORT_CHANNEL, lag_id, mtu))

    def _generate_final_commands(self, lag_id, lag_obj):
        if lag_obj:
            return
        pch_prefix = "interface %s %s" % (self.PORT_CHANNEL, lag_id)
        ipl = self._required_config['ipl']
        if ipl:
            self._commands.append("%s ipl %s" % (pch_prefix, ipl))
        dcb_pfc = self._required_config['dcb_pfc']
        if dcb_pfc:
            if dcb_pfc == "enabled":
                command = "%s dcb priority-flow-control mode on force" % \
                    pch_prefix
            else:
                command = "%s no dcb priority-flow-control mode force" % \
                    pch_prefix
            self._commands.append(command)
        vlan_id = self._required_config['vlan_id']

        if vlan_id:
            self._commands.append(
                "%s switchport mode hybrid" % pch_prefix)
            self._commands.append(
                "%s switchport mode access vlan %s" % (pch_prefix, vlan_id))
        self._commands.append(
            "%s no shutdown" % pch_prefix)

    def _generate_port_channel_commands(self, lag_id, lag_obj):
        lag_mode = self._required_config['lag_mode']
        dcb_pfc = self._required_config['dcb_pfc']
        curr_members = lag_obj.get('members', [])
        members = self._required_config['members']
        if set(members) != set(curr_members):
            for member in curr_members:
                interface_prefix = "interface ethernet %s" % member
                self._commands.append(
                    "no %s %s" % (interface_prefix, self.CHANNEL_GROUP))
            for member in members:
                interface_prefix = "interface ethernet %s" % member
                if dcb_pfc == "enabled":
                    self._commands.append(
                        "%s no dcb priority-flow-control mode force" %
                        interface_prefix)
                    self._commands.append(
                        "%s switchport force" % interface_prefix)
                    self._commands.append(
                        "%s switchport mode access" % interface_prefix)
                self._commands.append(
                    "%s %s %s mode %s" %
                    (interface_prefix, self.CHANNEL_GROUP, lag_id, lag_mode))

    def generate_commands(self):
        lag_id = self._required_config['lag_id']

        lag_obj = self._current_config.get(lag_id, {})
        self._generate_initial_commands(lag_id, lag_obj)
        self._generate_port_channel_commands(lag_id, lag_obj)
        self._generate_final_commands(lag_id, lag_obj)

        if self._commands:
            self._commands.append('exit')

    def check_declarative_intent_params(self, result):
        pass


def main():
    """ main entry point for module execution
    """
    MlnxosLagApp.main()


if __name__ == '__main__':
    main()
