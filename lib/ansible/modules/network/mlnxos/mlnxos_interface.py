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
module: mlnxos_interface
version_added: "2.5"
author: "Samer Deeb (@samerd)"
short_description: Manage Interfaces on Mellanox MLNX-OS network devices
description:
  - This module provides declarative management of Interfaces
    on Mellanox MLNX-OS network devices.
notes:
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
    type: bool
  speed:
    description:
      - Interface link speed.
    choices: ['1G', '10G', '25G', '40G', '50G', '56G', '100G']
  mtu:
    description:
      - Maximum size of transmit packet.
  aggregate:
    description: List of Interfaces definitions.
  duplex:
    description:
      - Interface link status
    default: auto
    choices: ['full', 'half', 'auto']
  tx_rate:
    description:
      - Transmit rate in bits per second (bps).
  rx_rate:
    description:
      - Receiver rate in bits per second (bps).
  delay:
    description:
      - Time in seconds to wait before checking for the operational state on
        remote device. This wait is applicable for operational state argument
        which are I(state) with values C(up)/C(down).
    default: 10
  purge:
    description:
      - Purge Interfaces not defined in the aggregate parameter.
        This applies only for logical interface.
    default: no
  state:
    description:
      - State of the Interface configuration, C(up) means present and
        operationally up and C(down) means present and operationally C(down)
    default: present
    choices: ['present', 'absent', 'up', 'down']
"""

EXAMPLES = """
- name: configure interface
  mlnxos_interface:
      name: Eth1/2
      description: test-interface
      speed: 100 GB
      mtu: 512

- name: make interface up
  mlnxos_interface:
    name: Eth1/2
    enabled: True

- name: make interface down
  mlnxos_interface:
    name: Eth1/2
    enabled: False

- name: Check intent arguments
  mlnxos_interface:
    name: Eth1/2
    state: up

- name: Config + intent
  mlnxos_interface:
    name: Eth1/2
    enabled: False
    state: down
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device.
  returned: always
  type: list
  sample:
    - interface Eth1/2
    - description test-interface
    - mtu 512
"""

from copy import deepcopy
import re
from time import sleep

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import conditional, \
    remove_default_spec

from ansible.module_utils.network.mlnxos.mlnxos import BaseMlnxosModule, \
    get_interfaces_config


class MlnxosInterfaceModule(BaseMlnxosModule):
    ETH_IF_NAME_REGEX = re.compile(r'^Eth(\d\/\d+(|\/\d))$')

    @classmethod
    def _get_element_spec(cls):
        return dict(
            name=dict(type='str'),
            description=dict(),
            speed=dict(choices=['1G', '10G', '25G', '40G', '50G', '56G', '100G']),
            mtu=dict(type='int'),
            enabled=dict(default=True, type='bool'),
            delay=dict(default=10, type='int'),
            state=dict(default='present',
                       choices=['present', 'absent', 'up', 'down']),
            tx_rate=dict(),
            rx_rate=dict(),
        )

    @classmethod
    def _get_aggregate_spec(cls, element_spec):
        aggregate_spec = deepcopy(element_spec)
        aggregate_spec['name'] = dict(required=True)

        # remove default in aggregate spec, to handle common arguments
        remove_default_spec(aggregate_spec)
        return aggregate_spec

    def init_module(self):
        """ main entry point for module execution
        """
        element_spec = self._get_element_spec()
        aggregate_spec = self._get_aggregate_spec(element_spec)
        if aggregate_spec:
            argument_spec = dict(
                aggregate=dict(type='list', elements='dict',
                               options=aggregate_spec),
                purge=dict(default=False, type='bool'),
            )
        else:
            argument_spec = dict()
        argument_spec.update(element_spec)
        required_one_of = [['name', 'aggregate']]
        mutually_exclusive = [['name', 'aggregate']]
        self._module = AnsibleModule(
            argument_spec=argument_spec,
            required_one_of=required_one_of,
            mutually_exclusive=mutually_exclusive,
            supports_check_mode=True)

    def validate_name(self, value):
        if not self.ETH_IF_NAME_REGEX.match(value):
            self._module.fail_json(msg='Invalid interface name!')

    def validate_purge(self, value):
        if value:
            self._module.fail_json(
                msg='Purge is not supported for ethernet interfaces!')

    def validate_duplex(self, value):
        if value != 'auto':
            self._module.fail_json(
                msg='Duplex is not supported for ethernet interfaces')

    def validate_state(self, value):
        if value == 'absent':
            self._module.fail_json(
                msg='Cannot remove physical interfaces')

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
                req_item = item.copy()
                self._required_config.append(req_item)

        else:
            params = {
                'name': module_params['name'],
                'description': module_params['description'],
                'speed': module_params['speed'],
                'mtu': module_params['mtu'],
                'state': module_params['state'],
                'delay': module_params['delay'],
                'enabled': module_params['enabled'],
                'tx_rate': module_params['tx_rate'],
                'rx_rate': module_params['rx_rate'],
            }

            self.validate_param_values(params)
            self._required_config.append(params)

    @classmethod
    def get_if_name(cls, item):
        return cls.get_config_attr(item, "header")

    @classmethod
    def get_if_cmd(cls, if_name):
        return if_name.replace("Eth", "interface ethernet ")

    @classmethod
    def get_admin_state(cls, item):
        admin_state = cls.get_config_attr(item, "Admin state")
        return str(admin_state).lower() == "enabled"

    @classmethod
    def get_oper_state(cls, item):
        oper_state = cls.get_config_attr(item, "Operational state")
        return str(oper_state).lower()

    def add_command_to_interface(self, interface, cmd):
        if interface not in self._commands:
            self._commands.append(interface)
        self._commands.append(cmd)

    def get_speed(self, item):
        speed = self.get_config_attr(item, 'Actual speed')
        try:
            speed = int(speed.split()[0])
            return "%dG" % speed
        except ValueError:
            return None

    def _create_if_data(self, name, item):
        return {
            'name': name,
            'description': self.get_config_attr(item, 'Description'),
            'speed': self.get_speed(item),
            'mtu': self.get_mtu(item),
            'enabled': self.get_admin_state(item),
            'state': self.get_oper_state(item)
        }

    def _get_interfaces_config(self):
        return get_interfaces_config(self._module, "ethernet")

    def load_current_config(self):
        self._current_config = dict()
        config = self._get_interfaces_config()

        for item in config:
            name = self.get_if_name(item)
            self._current_config[name] = self._create_if_data(name, item)

    def generate_commands(self):
        for req_if in self._required_config:
            name = req_if['name']
            curr_if = self._current_config.get(name)
            if not curr_if:
                self._module.fail_json(
                    msg='could not find interface %s' % name)
                continue
            self._generate_if_commands(name, req_if, curr_if)

    def _generate_if_commands(self, name, req_if, curr_if):
        args = ('speed', 'description', 'mtu')
        enabled = req_if['enabled']
        add_exit = False
        interface_prefix = self.get_if_cmd(name)

        for attr_name in args:
            candidate = req_if.get(attr_name)
            running = curr_if.get(attr_name)
            if candidate != running:
                if candidate:
                    cmd = attr_name + ' ' + str(candidate)
                    if attr_name in ('mtu', 'speed'):
                        cmd = cmd + ' ' + 'force'
                    self.add_command_to_interface(interface_prefix, cmd)
                    add_exit = True
        curr_enabled = curr_if.get('enabled', False)
        if enabled != curr_enabled:
            cmd = 'shutdown'
            if enabled:
                cmd = "no %s" % cmd
            self.add_command_to_interface(interface_prefix, cmd)
            add_exit = True
        if add_exit:
            self._commands.append('exit')

    def _get_interfaces_rates(self):
        return get_interfaces_config(self._module, "ethernet", "rates")

    def _get_interfaces_status(self):
        return get_interfaces_config(self._module, "ethernet", "status")

    def check_declarative_intent_params(self, result):
        failed_conditions = []
        delay_called = False
        rates = None
        statuses = None
        for req_if in self._required_config:
            want_state = req_if.get('state')
            want_tx_rate = req_if.get('tx_rate')
            want_rx_rate = req_if.get('rx_rate')
            name = req_if['name']
            if want_state not in ('up', 'down') and not want_tx_rate and not \
                    want_rx_rate:
                continue
            if not delay_called and result['changed']:
                delay_called = True
                delay = req_if['delay']
                if delay > 0:
                    sleep(delay)
            if want_state in ('up', 'down'):
                if not statuses:
                    statuses = self._get_interfaces_status()
                    curr_if = statuses.get(name)
                    curr_state = None
                    if curr_if:
                        curr_if = curr_if[0]
                        curr_state = self.get_oper_state(curr_if)
                    if curr_state is None or not \
                            conditional(want_state, curr_state.strip()):
                        failed_conditions.append(
                            'state ' + 'eq(%s)' % want_state)
            if_rates = None
            if want_tx_rate or want_rx_rate:
                if not rates:
                    rates = self._get_interfaces_rates()
                if_rates = rates.get(name)
                if if_rates:
                    if_rates = if_rates[0]
            if want_tx_rate:
                have_tx_rate = None
                if if_rates:
                    have_tx_rate = if_rates.get('egress rate')
                    if have_tx_rate:
                        have_tx_rate = have_tx_rate.split()[0]
                if have_tx_rate is None or not \
                        conditional(want_tx_rate, have_tx_rate.strip(),
                                    cast=int):
                    failed_conditions.append('tx_rate ' + want_tx_rate)

            if want_rx_rate:
                have_rx_rate = None
                if if_rates:
                    have_rx_rate = if_rates.get('ingress rate')
                    if have_rx_rate:
                        have_rx_rate = have_rx_rate.split()[0]
                if have_rx_rate is None or not \
                        conditional(want_rx_rate, have_rx_rate.strip(),
                                    cast=int):
                    failed_conditions.append('rx_rate ' + want_rx_rate)

        return failed_conditions


def main():
    """ main entry point for module execution
    """
    MlnxosInterfaceModule.main()


if __name__ == '__main__':
    main()
