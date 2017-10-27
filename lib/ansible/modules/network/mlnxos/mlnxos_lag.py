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

import re

from ansible.module_utils.basic import AnsibleModule

from ansible.module_utils.mlnxos import get_interfaces_config
from ansible.module_utils.mlnxos import mlnxos_argument_spec
from ansible.modules.network.mlnxos import BaseMlnxosApp


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
  - This module provides declarative management of Lags
    on MLNX-OS network devices.
notes:
  -
options:
  lag_id:
    description:
      - port channel ID of the LAG (1-4096).
    required: true
  lag_mode:
    description:
      - LAG mode:
    choices: [on, passive, active].
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
      - 1/6
      - 1/7
    lag_mode: on
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device.
  returned: always, except for the platforms that use Netconf transport to
  type: list
  sample:
    - interface port-channel 5
    - exit
    - interface port-channel 5 mtu 1500 force
    - interface ethernet 1/16 channel-group 5 mode on
    - interface ethernet 1/17 channel-group 5 mode on
"""


class MlnxosLagApp(BaseMlnxosApp):
    LAG_ID_REGEX = re.compile(r"^(.*)Po(\d+)(.*)$")
    IF_NAME_REGEX = re.compile(r"^Eth(\d+\/\d+)(.*)$")

    def init_module(self):
        """ initialize module
        """
        element_spec = dict(
            mtu=dict(),
            lag_id=dict(required=True),
            members=dict(required=True, type='list'),
            lag_mode=dict(required=True, choices=['active', 'on', 'passive']),
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
        }

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
            return match.groups()[1]

    @classmethod
    def extract_if_name(cls, member):
        match = cls.IF_NAME_REGEX.match(member)
        if match:
            return match.groups()[0]

    def load_current_config(self):
        interface_type = "port-channel"
        lag_config = get_interfaces_config(self._module, interface_type)
        lag_summary = get_interfaces_config(self._module, interface_type,
                                            summary=True)
        self._current_config = {}

        for item in lag_config:
            lag_id = self.get_lag_id(item)
            obj = {
                'lag_id': lag_id,
                'mtu': self.get_mtu(item),
                'members': None
            }
            self._current_config[lag_id] = obj

        for lag_name, lag_data in lag_summary.iteritems():
            lag_id = self.extract_lag_id(lag_name)
            if not lag_id:
                continue
            obj = self._current_config.get(lag_id)
            if not obj:
                continue
            lag_members = self.get_config_attr(lag_data[0], "Member Ports")
            lag_members = lag_members.split()
            obj['members'] = [self.extract_if_name(member) for member in
                              lag_members]

    def generate_commands(self):
        lag_id = self._required_config['lag_id']
        mtu = self._required_config['mtu']
        lag_mode = self._required_config['lag_mode']
        members = self._required_config['members']
        lag_obj = self._current_config.get(lag_id, {})
        if not lag_obj:
            self._commands.append("interface port-channel %s" % lag_id)
            self._commands.append("exit")
        curr_mtu = lag_obj.get('mtu')
        curr_members = lag_obj.get('members', [])
        if mtu and curr_mtu != mtu:
            self._commands.append("interface port-channel %s mtu %s force" %
                                  (lag_id, mtu))
        if set(members) != set(curr_members):
            for member in curr_members:
                self._commands.append(
                    "no interface ethernet %s channel-group" % member)
            for member in members:
                self._commands.append(
                    "interface ethernet %s channel-group %s mode %s" %
                    (member, lag_id, lag_mode))

    def check_declarative_intent_params(self, result):
        pass


if __name__ == '__main__':
    MlnxosLagApp.main()
