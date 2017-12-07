#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: iosxr_interface
version_added: "2.4"
author: "Ganesh Nalawade (@ganeshrn)"
short_description: Manage Interface on Cisco IOS XR network devices
description:
  - This module provides declarative management of Interfaces
    on Cisco IOS XR network devices.
extends_documentation_fragment: iosxr
notes:
  - Tested against IOS XR 6.1.2
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
  duplex:
    description:
      - Interface link status
    choices: ['full', 'half']
  tx_rate:
    description:
      - Transmit rate in bits per second (bps).
  rx_rate:
    description:
      - Receiver rate in bits per second (bps).
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
  iosxr_interface:
      name: GigabitEthernet0/0/0/2
      description: test-interface
      speed: 100
      duplex: half
      mtu: 512

- name: remove interface
  iosxr_interface:
    name: GigabitEthernet0/0/0/2
    state: absent

- name: make interface up
  iosxr_interface:
    name: GigabitEthernet0/0/0/2
    enabled: True

- name: make interface down
  iosxr_interface:
    name: GigabitEthernet0/0/0/2
    enabled: False

- name: Create interface using aggregate
  iosxr_interface:
    aggregate:
    - name: GigabitEthernet0/0/0/3
    - name: GigabitEthernet0/0/0/2
    speed: 100
    duplex: full
    mtu: 512
    state: present

- name: Delete interface using aggregate
  iosxr_interface:
    aggregate:
    - name: GigabitEthernet0/0/0/3
    - name: GigabitEthernet0/0/0/2
    state: absent

- name: Check intent arguments
  iosxr_interface:
    name: GigabitEthernet0/0/0/5
    state: up
    delay: 20

- name: Config + intent
  iosxr_interface:
    name: GigabitEthernet0/0/0/5
    enabled: False
    state: down
    delay: 20
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device.
  returned: always, except for the platforms that use Netconf transport to manage the device.
  type: list
  sample:
  - interface GigabitEthernet0/0/0/2
  - description test-interface
  - duplex half
  - mtu 512
"""
import re

from time import sleep
from copy import deepcopy

from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import exec_command
from ansible.module_utils.network.iosxr.iosxr import get_config, load_config
from ansible.module_utils.network.iosxr.iosxr import iosxr_argument_spec
from ansible.module_utils.network.common.utils import conditional, remove_default_spec


def validate_mtu(value, module):
    if value and not 64 <= int(value) <= 65535:
        module.fail_json(msg='mtu must be between 64 and 65535')


def validate_param_values(module, obj, param=None):
    if param is None:
        param = module.params
    for key in obj:
        # validate the param value (if validator func exists)
        validator = globals().get('validate_%s' % key)
        if callable(validator):
            validator(param.get(key), module)


def parse_shutdown(intf_config):
    for cfg in intf_config:
        match = re.search(r'%s' % 'shutdown', cfg, re.M)
        if match:
            return True
    return False


def parse_config_argument(intf_config, arg):
    for cfg in intf_config:
        match = re.search(r'%s (.+)$' % arg, cfg, re.M)
        if match:
            return match.group(1)


def search_obj_in_list(name, lst):
    for o in lst:
        if o['name'] == name:
            return o

    return None


def map_params_to_obj(module):
    obj = []

    aggregate = module.params.get('aggregate')
    if aggregate:
        for item in aggregate:
            for key in item:
                if item.get(key) is None:
                    item[key] = module.params[key]

            validate_param_values(module, item, item)
            d = item.copy()

            if d['enabled']:
                d['disable'] = False
            else:
                d['disable'] = True

            obj.append(d)

    else:
        validate_param_values(module, module.params)
        params = {
            'name': module.params['name'],
            'description': module.params['description'],
            'speed': module.params['speed'],
            'mtu': module.params['mtu'],
            'duplex': module.params['duplex'],
            'state': module.params['state'],
            'delay': module.params['delay'],
            'tx_rate': module.params['tx_rate'],
            'rx_rate': module.params['rx_rate']
        }

        if module.params['enabled']:
            params.update({'disable': False})
        else:
            params.update({'disable': True})

        obj.append(params)
    return obj


def map_config_to_obj(module):
    data = get_config(module, config_filter='interface')
    interfaces = data.strip().rstrip('!').split('!')

    if not interfaces:
        return list()

    instances = list()

    for interface in interfaces:
        intf_config = interface.strip().splitlines()

        name = intf_config[0].strip().split()[1]

        if name == 'preconfigure':
            name = intf_config[0].strip().split()[2]

        obj = {
            'name': name,
            'description': parse_config_argument(intf_config, 'description'),
            'speed': parse_config_argument(intf_config, 'speed'),
            'duplex': parse_config_argument(intf_config, 'duplex'),
            'mtu': parse_config_argument(intf_config, 'mtu'),
            'disable': True if parse_shutdown(intf_config) else False,
            'state': 'present'
        }
        instances.append(obj)
    return instances


def map_obj_to_commands(updates):
    commands = list()
    want, have = updates

    args = ('speed', 'description', 'duplex', 'mtu')
    for w in want:
        name = w['name']
        disable = w['disable']
        state = w['state']

        obj_in_have = search_obj_in_list(name, have)
        interface = 'interface ' + name

        if state == 'absent' and obj_in_have:
            commands.append('no ' + interface)

        elif state in ('present', 'up', 'down'):
            if obj_in_have:
                for item in args:
                    candidate = w.get(item)
                    running = obj_in_have.get(item)
                    if candidate != running:
                        if candidate:
                            cmd = interface + ' ' + item + ' ' + str(candidate)
                            commands.append(cmd)

                if disable and not obj_in_have.get('disable', False):
                    commands.append(interface + ' shutdown')
                elif not disable and obj_in_have.get('disable', False):
                    commands.append('no ' + interface + ' shutdown')
            else:
                for item in args:
                    value = w.get(item)
                    if value:
                        commands.append(interface + ' ' + item + ' ' + str(value))
                if disable:
                    commands.append('no ' + interface + ' shutdown')
    return commands


def check_declarative_intent_params(module, want, result):
    failed_conditions = []
    for w in want:
        want_state = w.get('state')
        want_tx_rate = w.get('tx_rate')
        want_rx_rate = w.get('rx_rate')
        if want_state not in ('up', 'down') and not want_tx_rate and not want_rx_rate:
            continue

        if result['changed']:
            sleep(w['delay'])

        command = 'show interfaces %s' % w['name']
        rc, out, err = exec_command(module, command)
        if rc != 0:
            module.fail_json(msg=to_text(err, errors='surrogate_then_replace'), command=command, rc=rc)

        if want_state in ('up', 'down'):
            match = re.search(r'%s (\w+)' % 'line protocol is', out, re.M)
            have_state = None
            if match:
                have_state = match.group(1)
                if have_state.strip() == 'administratively':
                    match = re.search(r'%s (\w+)' % 'administratively', out, re.M)
                    if match:
                        have_state = match.group(1)

            if have_state is None or not conditional(want_state, have_state.strip()):
                failed_conditions.append('state ' + 'eq(%s)' % want_state)

        if want_tx_rate:
            match = re.search(r'%s (\d+)' % 'output rate', out, re.M)
            have_tx_rate = None
            if match:
                have_tx_rate = match.group(1)

            if have_tx_rate is None or not conditional(want_tx_rate, have_tx_rate.strip(), cast=int):
                failed_conditions.append('tx_rate ' + want_tx_rate)

        if want_rx_rate:
            match = re.search(r'%s (\d+)' % 'input rate', out, re.M)
            have_rx_rate = None
            if match:
                have_rx_rate = match.group(1)

            if have_rx_rate is None or not conditional(want_rx_rate, have_rx_rate.strip(), cast=int):
                failed_conditions.append('rx_rate ' + want_rx_rate)

    return failed_conditions


def main():
    """ main entry point for module execution
    """
    element_spec = dict(
        name=dict(),
        description=dict(),
        speed=dict(),
        mtu=dict(),
        duplex=dict(choices=['full', 'half']),
        enabled=dict(default=True, type='bool'),
        tx_rate=dict(),
        rx_rate=dict(),
        delay=dict(default=10, type='int'),
        state=dict(default='present',
                   choices=['present', 'absent', 'up', 'down'])
    )

    aggregate_spec = deepcopy(element_spec)
    aggregate_spec['name'] = dict(required=True)

    # remove default in aggregate spec, to handle common arguments
    remove_default_spec(aggregate_spec)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec),
    )

    argument_spec.update(element_spec)
    argument_spec.update(iosxr_argument_spec)

    required_one_of = [['name', 'aggregate']]
    mutually_exclusive = [['name', 'aggregate']]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=required_one_of,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    warnings = list()

    result = {'changed': False}

    want = map_params_to_obj(module)
    have = map_config_to_obj(module)

    commands = map_obj_to_commands((want, have))

    result['commands'] = commands
    result['warnings'] = warnings

    if commands:
        commit = not module.check_mode
        diff = load_config(module, commands, commit=commit)
        if diff:
            result['diff'] = dict(prepared=diff)
        result['changed'] = True

    failed_conditions = check_declarative_intent_params(module, want, result)

    if failed_conditions:
        msg = 'One or more conditional statements have not been satisfied'
        module.fail_json(msg=msg, failed_conditions=failed_conditions)

    module.exit_json(**result)

if __name__ == '__main__':
    main()
