#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

from copy import deepcopy
from time import sleep

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.mlnxos import load_config, get_interfaces_config
from ansible.module_utils.mlnxos import mlnxos_argument_spec, check_args
from ansible.module_utils.network_common import conditional, remove_default_spec


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: mlnxos_interface
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
  mlnxos_interface:
      name: ethernet 1/2
      description: test-interface
      speed: 100 GB
      mtu: 512

- name: make interface up
  mlnxos_interface:
    name: ethernet 1/2
    enabled: True

- name: make interface down
  mlnxos_interface:
    name: ethernet 1/2
    enabled: False

- name: Check intent arguments
  mlnxos_interface:
    name: ethernet 1/2
    state: up

- name: Config + intent
  mlnxos_interface:
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


class MlnxosInterface(object):

    def __init__(self):
        """ main entry point for module execution
        """
        neighbors_spec = dict(
            host=dict(),
            port=dict()
        )

        element_spec = dict(
            name=dict(),
            description=dict(),
            speed=dict(),
            mtu=dict(),
            duplex=dict(choices=['full', 'half', 'auto']),
            enabled=dict(default=True, type='bool'),
            tx_rate=dict(),
            rx_rate=dict(),
            neighbors=dict(type='list', elements='dict',
                           options=neighbors_spec),
            delay=dict(default=10, type='int'),
            state=dict(default='present',
                       choices=['present', 'absent', 'up', 'down'])
        )

        aggregate_spec = deepcopy(element_spec)
        aggregate_spec['name'] = dict(required=True)

        # remove default in aggregate spec, to handle common arguments
        remove_default_spec(aggregate_spec)

        argument_spec = dict(
            aggregate=dict(type='list', elements='dict',
                           options=aggregate_spec),
        )

        argument_spec.update(element_spec)
        argument_spec.update(mlnxos_argument_spec)

        required_one_of = [['name', 'aggregate']]
        mutually_exclusive = [['name', 'aggregate']]

        self._module = AnsibleModule(
            argument_spec=argument_spec,
            required_one_of=required_one_of,
            mutually_exclusive=mutually_exclusive,
            supports_check_mode=True)
        self._commands = list()
        self._current_interfaces_config = list()
        self._required_interfaces_config = list()

    def main(self):
        warnings = list()
        check_args(self._module, warnings)

        result = {'changed': False}
        if warnings:
            result['warnings'] = warnings

        self.get_required_interfaces_config()
        self.load_interfaces_config()

        self.generate_commands()
        result['commands'] = self._commands

        if self._commands:
            if not self._module.check_mode:
                load_config(self._module, self._commands)
            result['changed'] = True

        failed_conditions = self.check_declarative_intent_params(result)

        if failed_conditions:
            msg = 'One or more conditional statements have not been satisfied'
            self._module.fail_json(msg=msg, failed_conditions=failed_conditions)

        self._module.exit_json(**result)

    def get_required_interfaces_config(self):
        module_params = self._module.params
        aggregate = module_params.get('aggregate')
        if aggregate:
            for item in aggregate:
                for key in item:
                    if item.get(key) is None:
                        item[key] = module_params[key]

                self.validate_param_values(item, item)
                d = item.copy()

                if d['enabled']:
                    d['disable'] = False
                else:
                    d['disable'] = True

                self._required_interfaces_config.append(d)

        else:
            params = {
                'name': module_params['name'],
                'description': module_params['description'],
                'speed': module_params['speed'],
                'mtu': module_params['mtu'],
                'duplex': module_params['duplex'],
                'state': module_params['state'],
                'delay': module_params['delay'],
                'tx_rate': module_params['tx_rate'],
                'rx_rate': module_params['rx_rate'],
                'neighbors': module_params['neighbors']
            }

            self.validate_param_values(params)
            if module_params['enabled']:
                params.update({'disable': False})
            else:
                params.update({'disable': True})

            self._required_interfaces_config.append(params)

    def validate_mtu(self, value):
        if value and not 1500 <= int(value) <= 9612:
            self._module.fail_json(msg='mtu must be between 1500 and 9612')

    def validate_param_values(self, obj, param=None):
        if param is None:
            param = self._module.params
        for key in obj:
            # validate the param value (if validator func exists)
            try:
                validator = getattr(self, 'validate_%s' % key)
                if callable(validator):
                    validator(param.get(key))
            except AttributeError:
                pass

    @classmethod
    def get_config_attr(cls, item, arg):
        return item.get(arg)

    @classmethod
    def get_mtu(cls, item):
        mtu = cls.get_config_attr(item, "MTU")
        ll = mtu.split()
        return ll[0]

    @classmethod
    def get_if_name(cls, item):
        header = cls.get_config_attr(item, "header")
        return header.replace("Eth", "ethernet ")

    @classmethod
    def get_admin_state(cls, item):
        admin_state = cls.get_config_attr(item, "Admin state")
        return str(admin_state).lower() == "enabled"

    @classmethod
    def get_oper_state(cls, item):
        oper_state = cls.get_config_attr(item, "Operational state")
        return str(oper_state).lower()

    @classmethod
    def search_obj_in_list(cls, name, lst):
        for o in lst:
            if o['name'] == name:
                return o

    def add_command_to_interface(self, interface, cmd):
        if interface not in self._commands:
            self._commands.append(interface)
        self._commands.append(cmd)

    def load_interfaces_config(self):
        config = get_interfaces_config(self._module, "ethernet")

        for item in config:
            obj = {
                'name': self.get_if_name(item),
                'description': self.get_config_attr(item, 'Description'),
                'speed': self.get_config_attr(item, 'Actual speed'),
                'mtu': self.get_mtu(item),
                'disable': not self.get_admin_state(item),
                'state': self.get_oper_state(item)
            }
            self._current_interfaces_config.append(obj)

    def generate_commands(self):
        args = ('speed', 'description', 'mtu')
        for req_if in self._required_interfaces_config:
            name = req_if['name']
            disable = req_if['disable']
            state = req_if['state']

            curr_if = self.search_obj_in_list(
                name, self._current_interfaces_config)
            interface = 'interface ' + name

            if state == 'absent' and curr_if:
                self._commands.append('no ' + interface)

            elif state in ('present', 'up', 'down'):
                if curr_if:
                    for item in args:
                        candidate = req_if.get(item)
                        running = curr_if.get(item)
                        if candidate != running:
                            if candidate:
                                cmd = item + ' ' + str(candidate)
                                if item == "mtu":
                                    cmd = cmd + ' ' + 'force'
                                self.add_command_to_interface(interface, cmd)

                    if disable and not curr_if.get('disable', False):
                        self.add_command_to_interface(interface, 'shutdown')
                    elif not disable and curr_if.get('disable', False):
                        self.add_command_to_interface(interface, 'no shutdown')
                else:
                    self._commands.append(interface)
                    for item in args:
                        value = req_if.get(item)
                        cmd = item + ' ' + str(value)
                        if item == "mtu":
                            cmd = cmd + ' ' + 'force'
                        if value:
                            self._commands.append(cmd)

                    if disable:
                        self._commands.append('no shutdown')

    def check_declarative_intent_params(self, result):
        failed_conditions = []
        for req_if in self._required_interfaces_config:
            want_state = req_if.get('state')
            name = req_if['name']
            if want_state not in ('up', 'down'):
                continue

            if result['changed']:
                sleep(req_if['delay'])
            curr_if = self.search_obj_in_list(
                name, self._current_interfaces_config)
            curr_state = curr_if['state']
            if curr_state is None or not \
                    conditional(want_state, curr_state.strip()):
                failed_conditions.append('state ' + 'eq(%s)' % want_state)
        return failed_conditions


if __name__ == '__main__':
    mlnxos_if = MlnxosInterface()
    mlnxos_if.main()
