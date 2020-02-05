#!/usr/bin/python
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: onyx_interface
version_added: "2.5"
author: "Samer Deeb (@samerd)"
short_description: Manage Interfaces on Mellanox ONYX network devices
description:
  - This module provides declarative management of Interfaces
    on Mellanox ONYX network devices.
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
      - This is state check parameter only.
      - Supports conditionals, see L(Conditionals in Networking Modules,../network/user_guide/network_working_with_command_output.html)
  rx_rate:
    description:
      - Receiver rate in bits per second (bps).
      - This is state check parameter only.
      - Supports conditionals, see L(Conditionals in Networking Modules,../network/user_guide/network_working_with_command_output.html)
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
    default: false
    type: bool
  state:
    description:
      - State of the Interface configuration, C(up) means present and
        operationally up and C(down) means present and operationally C(down)
    default: present
    choices: ['present', 'absent', 'up', 'down']
"""

EXAMPLES = """
- name: configure interface
  onyx_interface:
      name: Eth1/2
      description: test-interface
      speed: 100G
      mtu: 512

- name: make interface up
  onyx_interface:
    name: Eth1/2
    enabled: True

- name: make interface down
  onyx_interface:
    name: Eth1/2
    enabled: False

- name: Check intent arguments
  onyx_interface:
    name: Eth1/2
    state: up

- name: Config + intent
  onyx_interface:
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
    - interface ethernet 1/2
    - description test-interface
    - mtu 512
    - exit
"""

from copy import deepcopy
import re
from time import sleep

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems
from ansible.module_utils.network.common.utils import conditional
from ansible.module_utils.network.common.utils import remove_default_spec

from ansible.module_utils.network.onyx.onyx import BaseOnyxModule
from ansible.module_utils.network.onyx.onyx import get_interfaces_config


class OnyxInterfaceModule(BaseOnyxModule):
    IF_ETH_REGEX = re.compile(r"^Eth(\d+\/\d+|\d+\/\d+\/\d+)$")
    IF_VLAN_REGEX = re.compile(r"^Vlan (\d+)$")
    IF_LOOPBACK_REGEX = re.compile(r"^Loopback (\d+)$")
    IF_PO_REGEX = re.compile(r"^Po(\d+)$")

    IF_TYPE_ETH = "ethernet"
    IF_TYPE_LOOPBACK = "loopback"
    IF_TYPE_VLAN = "vlan"
    IF_TYPE_PO = "port-channel"

    IF_TYPE_MAP = {
        IF_TYPE_ETH: IF_ETH_REGEX,
        IF_TYPE_VLAN: IF_VLAN_REGEX,
        IF_TYPE_LOOPBACK: IF_LOOPBACK_REGEX,
        IF_TYPE_PO: IF_PO_REGEX
    }
    UNSUPPORTED_ATTRS = {
        IF_TYPE_ETH: (),
        IF_TYPE_VLAN: ('speed', 'rx_rate', 'tx_rate'),
        IF_TYPE_LOOPBACK: ('speed', 'mtu', 'rx_rate', 'tx_rate'),
        IF_TYPE_PO: ('speed', 'rx_rate', 'tx_rate'),
    }
    UNSUPPORTED_STATES = {
        IF_TYPE_ETH: ('absent',),
        IF_TYPE_VLAN: (),
        IF_TYPE_LOOPBACK: ('up', 'down'),
        IF_TYPE_PO: ('absent'),
    }

    IF_MODIFIABLE_ATTRS = ('speed', 'description', 'mtu')
    _interface_type = None

    @classmethod
    def _get_element_spec(cls):
        return dict(
            name=dict(type='str'),
            description=dict(),
            speed=dict(choices=['1G', '10G', '25G', '40G', '50G', '56G', '100G']),
            mtu=dict(type='int'),
            enabled=dict(type='bool'),
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
        """ module initialization
        """
        element_spec = self._get_element_spec()
        aggregate_spec = self._get_aggregate_spec(element_spec)
        argument_spec = dict(
            aggregate=dict(type='list', elements='dict',
                           options=aggregate_spec),
            purge=dict(default=False, type='bool'),
        )
        argument_spec.update(element_spec)
        required_one_of = [['name', 'aggregate']]
        mutually_exclusive = [['name', 'aggregate']]
        self._module = AnsibleModule(
            argument_spec=argument_spec,
            required_one_of=required_one_of,
            mutually_exclusive=mutually_exclusive,
            supports_check_mode=True)

    def validate_purge(self, value):
        if value:
            self._module.fail_json(
                msg='Purge is not supported!')

    def validate_duplex(self, value):
        if value != 'auto':
            self._module.fail_json(
                msg='Duplex is not supported!')

    def _get_interface_type(self, if_name):
        if_type = None
        if_id = None
        for interface_type, interface_regex in iteritems(self.IF_TYPE_MAP):
            match = interface_regex.match(if_name)
            if match:
                if_type = interface_type
                if_id = match.group(1)
                break
        return if_type, if_id

    def _set_if_type(self, params):
        if_name = params['name']
        if_type, if_id = self._get_interface_type(if_name)
        if not if_id:
            self._module.fail_json(
                msg='unsupported interface: %s' % if_name)
        params['if_type'] = if_type
        params['if_id'] = if_id

    def _check_supported_attrs(self, if_obj):
        unsupported_attrs = self.UNSUPPORTED_ATTRS[self._interface_type]
        for attr in unsupported_attrs:
            val = if_obj[attr]
            if val is not None:
                self._module.fail_json(
                    msg='attribute %s is not supported for %s interface' % (
                        attr, self._interface_type))
        req_state = if_obj['state']
        unsupported_states = self.UNSUPPORTED_STATES[self._interface_type]
        if req_state in unsupported_states:
            self._module.fail_json(
                msg='%s state is not supported for %s interface' % (
                    req_state, self._interface_type))

    def _validate_interface_type(self):
        for if_obj in self._required_config:
            if_type = if_obj['if_type']
            if not self._interface_type:
                self._interface_type = if_type
            elif self._interface_type != if_type:
                self._module.fail_json(
                    msg='Cannot aggregate interfaces from different types')
            self._check_supported_attrs(if_obj)

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
                self._set_if_type(req_item)
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
            self._set_if_type(params)
            self._required_config.append(params)
        self._validate_interface_type()

    @classmethod
    def get_if_name(cls, item):
        return cls.get_config_attr(item, "header")

    @classmethod
    def get_admin_state(cls, item):
        admin_state = cls.get_config_attr(item, "Admin state")
        return str(admin_state).lower() == "enabled"

    @classmethod
    def get_oper_state(cls, item):
        oper_state = cls.get_config_attr(item, "Operational state")
        if not oper_state:
            oper_state = cls.get_config_attr(item, "State")
        return str(oper_state).lower()

    @classmethod
    def get_speed(cls, item):
        speed = cls.get_config_attr(item, 'Actual speed')
        if not speed:
            return
        try:
            speed = int(speed.split()[0])
            return "%dG" % speed
        except ValueError:
            return None

    def _create_if_data(self, name, item):
        regex = self.IF_TYPE_MAP[self._interface_type]
        if_id = ''
        match = regex.match(name)
        if match:
            if_id = match.group(1)
        return dict(
            name=name,
            description=self.get_config_attr(item, 'Description'),
            speed=self.get_speed(item),
            mtu=self.get_mtu(item),
            enabled=self.get_admin_state(item),
            state=self.get_oper_state(item),
            if_id=if_id)

    def _get_interfaces_config(self):
        return get_interfaces_config(self._module, self._interface_type)

    def load_current_config(self):
        self._os_version = self._get_os_version()
        self._current_config = dict()
        config = self._get_interfaces_config()
        if not config:
            return
        if self._os_version < self.ONYX_API_VERSION:
            for if_data in config:
                if_name = self.get_if_name(if_data)
                self._current_config[if_name] = self._create_if_data(
                    if_name, if_data)
        else:
            if_data = dict()
            for if_config in config:
                for if_name, if_attr in iteritems(if_config):
                    for config in if_attr:
                        for key, value in iteritems(config):
                            if_data[key] = value
                    self._current_config[if_name] = self._create_if_data(
                        if_name, if_data)

    def _generate_no_if_commands(self, req_if, curr_if):
        if self._interface_type == self.IF_TYPE_ETH:
            name = req_if['name']
            self._module.fail_json(
                msg='cannot remove ethernet interface %s' % name)
        if not curr_if:
            return
        if_id = req_if['if_id']
        if not if_id:
            return
        self._commands.append(
            'no interface %s %s' % (self._interface_type, if_id))

    def _add_commands_to_interface(self, req_if, cmd_list):
        if not cmd_list:
            return
        if_id = req_if['if_id']
        if not if_id:
            return
        self._commands.append(
            'interface %s %s' % (self._interface_type, if_id))
        self._commands.extend(cmd_list)
        self._commands.append('exit')

    def _generate_if_commands(self, req_if, curr_if):
        enabled = req_if['enabled']
        cmd_list = []
        for attr_name in self.IF_MODIFIABLE_ATTRS:
            candidate = req_if.get(attr_name)
            running = curr_if.get(attr_name)
            if candidate != running:
                if candidate:
                    cmd = attr_name + ' ' + str(candidate)
                    if self._interface_type == self.IF_TYPE_ETH and \
                            attr_name in ('mtu', 'speed'):
                        cmd = cmd + ' ' + 'force'
                    cmd_list.append(cmd)
        curr_enabled = curr_if.get('enabled', False)
        if enabled is not None and enabled != curr_enabled:
            cmd = 'shutdown'
            if enabled:
                cmd = "no %s" % cmd
            cmd_list.append(cmd)
        if cmd_list:
            self._add_commands_to_interface(req_if, cmd_list)

    def generate_commands(self):
        for req_if in self._required_config:
            name = req_if['name']
            curr_if = self._current_config.get(name, {})
            if not curr_if and self._interface_type == self.IF_TYPE_ETH:
                self._module.fail_json(
                    msg='could not find ethernet interface %s' % name)
                continue
            req_state = req_if['state']
            if req_state == 'absent':
                self._generate_no_if_commands(req_if, curr_if)
            else:
                self._generate_if_commands(req_if, curr_if)

    def _get_interfaces_rates(self):
        return get_interfaces_config(self._module, self._interface_type,
                                     "rates")

    def _get_interfaces_status(self):
        return get_interfaces_config(self._module, self._interface_type,
                                     "status")

    def _check_state(self, name, want_state, statuses):
        curr_if = statuses.get(name, {})
        if curr_if:
            curr_if = curr_if[0]
            curr_state = self.get_oper_state(curr_if).strip()
            if curr_state is None or not conditional(want_state, curr_state):
                return 'state eq(%s)' % want_state

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
                if statuses is None:
                    statuses = self._get_interfaces_status() or {}
                cond = self._check_state(name, want_state, statuses)
                if cond:
                    failed_conditions.append(cond)
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
    OnyxInterfaceModule.main()


if __name__ == '__main__':
    main()
