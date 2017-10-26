#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

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
short_description: Manage Interface on MLNX-OS network devices
description:
  - This module provides declarative management of Interfaces
    on MLNX-OS network devices.
notes:
  -
options:
  name:
    description:
      - Name of the Interface.
    required: true
  description:
    description:
      - Description of Interface.
  enabled:
    description:
      - Interface link status.
  speed:
    description:
      - Interface link speed.
  mtu:
    description:
      - Maximum size of transmit packet.
  aggregate:
    description: List of Interfaces definitions.
  delay:
    description:
      - Time in seconds to wait before checking for the operational state on remote
        device. This wait is applicable for operational state argument which are
        I(state) with values C(up)/C(down), I(tx_rate) and I(rx_rate).
    default: 10
  state:
    description:
      - State of the Interface configuration, C(up) means present and
        operationally up and C(down) means present and operationally C(down)
    default: present
    choices: ['present', 'absent', 'up', 'down']
"""

EXAMPLES = """
- name: configure interface
  mlnxos_lag:
      name: ethernet 1/2
      description: test-interface
      speed: 100 GB
      mtu: 512

- name: make interface up
  mlnxos_lag:
    name: ethernet 1/2
    enabled: True

- name: make interface down
  mlnxos_lag:
    name: ethernet 1/2
    enabled: False

- name: Check intent arguments
  mlnxos_lag:
    name: ethernet 1/2
    state: up

- name: Config + intent
  mlnxos_lag:
    name: ethernet 1/2
    enabled: False
    state: down
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device.
  returned: always, except for the platforms that use Netconf transport to manage the device.
  type: list
  sample:
  - interface ethernet 1/2
  - description test-interface
  - mtu 512
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
    def get_config_attr(cls, item, arg):
        return item.get(arg)

    @classmethod
    def get_mtu(cls, item):
        mtu = cls.get_config_attr(item, "MTU")
        ll = mtu.split()
        return ll[0]

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
