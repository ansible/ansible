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
module: eos_interface
version_added: "2.5"
author: "Ganesh Nalawade (@ganeshrn)"
short_description: Manage Interface on Arista EOS network devices
description:
  - This module provides declarative management of Interfaces
    on Arista EOS network devices.
notes:
    - Tested against EOS 4.15
options:
  name:
    description:
      - Name of the Interface to be configured on remote device. The name of interface
        should be in expanded format and not abbreviated.
    required: true
  description:
    description:
      - Description of Interface upto 240 characters.
  enabled:
    description:
      - Interface link status. If the value is I(True) the interface state will be
        enabled, else if value is I(False) interface will be in disable (shutdown) state.
    default: True
  speed:
    description:
      - This option configures autoneg and speed/duplex/flowcontrol for the interface
        given in C(name) option.
  mtu:
    description:
      - Set maximum transmission unit size in bytes of transmit packet for the interface given
        in C(name) option.
  tx_rate:
    description:
      - Transmit rate in bits per second (bps) for the interface given in C(name) option.
      - This is state check parameter only.
      - Supports conditionals, see L(Conditionals in Networking Modules,../network/user_guide/network_working_with_command_output.html)
  rx_rate:
    description:
      - Receiver rate in bits per second (bps) for the interface given in C(name) option.
      - This is state check parameter only.
      - Supports conditionals, see L(Conditionals in Networking Modules,../network/user_guide/network_working_with_command_output.html)
  neighbors:
    description:
      - Check the operational state of given interface C(name) for LLDP neighbor.
      - The following suboptions are available.
    suboptions:
        host:
          description:
            - "LLDP neighbor host for given interface C(name)."
        port:
          description:
            - "LLDP neighbor port to which given interface C(name) is connected."
  aggregate:
    description:
      - List of Interfaces definitions. Each of the entry in aggregate list should
        define name of interface C(name) and other options as required.
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
extends_documentation_fragment: eos
"""

EXAMPLES = """
- name: configure interface
  eos_interface:
      name: ethernet1
      description: test-interface
      speed: 100full
      mtu: 512

- name: remove interface
  eos_interface:
    name: ethernet1
    state: absent

- name: make interface up
  eos_interface:
    name: ethernet1
    enabled: True

- name: make interface down
  eos_interface:
    name: ethernet1
    enabled: False

- name: Check intent arguments
  eos_interface:
    name: ethernet1
    state: up
    tx_rate: ge(0)
    rx_rate: le(0)

- name: Check neighbors intent arguments
  eos_interface:
    name: ethernet1
    neighbors:
    - port: eth0
      host: netdev

- name: Configure interface in disabled state and check if the operational state is disabled or not
  eos_interface:
    name: ethernet1
    enabled: False
    state: down

- name: Add interface using aggregate
  eos_interface:
    aggregate:
    - { name: ethernet1, mtu: 256, description: test-interface-1 }
    - { name: ethernet2, mtu: 516, description: test-interface-2 }
    speed: 100full
    state: present

- name: Delete interface using aggregate
  eos_interface:
    aggregate:
    - name: loopback9
    - name: loopback10
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device.
  returned: always, except for the platforms that use Netconf transport to manage the device.
  type: list
  sample:
  - interface ethernet1
  - description test-interface
  - speed 100full
  - mtu 512
"""
import re
from copy import deepcopy
from time import sleep

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.config import NetworkConfig
from ansible.module_utils.network.common.utils import conditional, remove_default_spec
from ansible.module_utils.network.eos.eos import get_config, load_config, run_commands
from ansible.module_utils.network.eos.eos import eos_argument_spec


def validate_mtu(value, module):
    if value and not 68 <= int(value) <= 65535:
        module.fail_json(msg='mtu must be between 68 and 65535')


def validate_param_values(module, obj, param=None):
    if param is None:
        param = module.params
    for key in obj:
        # validate the param value (if validator func exists)
        validator = globals().get('validate_%s' % key)
        if callable(validator):
            validator(param.get(key), module)


def parse_shutdown(configobj, name):
    cfg = configobj['interface %s' % name]
    cfg = '\n'.join(cfg.children)
    match = re.search(r'shutdown', cfg, re.M)
    return True if match else False


def parse_config_argument(configobj, name, arg=None):
    cfg = configobj['interface %s' % name]
    cfg = '\n'.join(cfg.children)
    match = re.search(r'%s (.+)$' % arg, cfg, re.M)
    if match:
        return match.group(1)


def search_obj_in_list(name, lst):
    for o in lst:
        if o['name'] == name:
            return o

    return None


def add_command_to_interface(interface, cmd, commands):
    if interface not in commands:
        commands.append(interface)
    commands.append(cmd)


def map_config_to_obj(module):
    config = get_config(module)
    configobj = NetworkConfig(indent=3, contents=config)

    match = re.findall(r'^interface (\S+)', config, re.M)
    if not match:
        return list()

    instances = list()

    for item in set(match):
        obj = {
            'name': item.lower(),
            'description': parse_config_argument(configobj, item, 'description'),
            'speed': parse_config_argument(configobj, item, 'speed'),
            'mtu': parse_config_argument(configobj, item, 'mtu'),
            'disable': parse_shutdown(configobj, item),
            'state': 'present'
        }
        instances.append(obj)
    return instances


def map_params_to_obj(module):
    obj = []
    aggregate = module.params.get('aggregate')
    if aggregate:
        for item in aggregate:
            for key in item:
                if item.get(key) is None:
                    item[key] = module.params[key]

            item['name'] = item['name'].lower()
            validate_param_values(module, item, item)
            d = item.copy()

            if d['enabled']:
                d['disable'] = False
            else:
                d['disable'] = True

            obj.append(d)

    else:
        params = {
            'name': module.params['name'].lower(),
            'description': module.params['description'],
            'speed': module.params['speed'],
            'mtu': module.params['mtu'],
            'state': module.params['state'],
            'delay': module.params['delay'],
            'tx_rate': module.params['tx_rate'],
            'rx_rate': module.params['rx_rate'],
            'neighbors': module.params['neighbors']
        }

        validate_param_values(module, params)
        if module.params['enabled']:
            params.update({'disable': False})
        else:
            params.update({'disable': True})

        obj.append(params)
    return obj


def map_obj_to_commands(updates, modules):
    commands = list()
    want, have = updates

    args = ('speed', 'description', 'mtu')
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
                            cmd = "{0} {1}".format(item, candidate)
                            add_command_to_interface(interface, cmd, commands)

                if disable and not obj_in_have.get('disable', False):
                    add_command_to_interface(interface, 'shutdown', commands)
                elif not disable and obj_in_have.get('disable', False):
                    add_command_to_interface(interface, 'no shutdown', commands)
            else:
                commands.append(interface)
                for item in args:
                    value = w.get(item)
                    if value:
                        commands.append("{0} {1}".format(item, value))

                if disable:
                    commands.append('no shutdown')
    return commands


def check_declarative_intent_params(module, want, result):
    failed_conditions = []
    have_neighbors = None
    for w in want:
        want_state = w.get('state')
        want_tx_rate = w.get('tx_rate')
        want_rx_rate = w.get('rx_rate')
        want_neighbors = w.get('neighbors')

        if want_state not in ('up', 'down') and not want_tx_rate and not want_rx_rate and not want_neighbors:
            continue

        if result['changed']:
            sleep(w['delay'])

        command = {'command': 'show interfaces %s' % w['name'], 'output': 'text'}
        output = run_commands(module, [command])

        if want_state in ('up', 'down'):
            match = re.search(r'%s (\w+)' % 'line protocol is', output[0], re.M)
            have_state = None
            if match:
                have_state = match.group(1)
            if have_state is None or not conditional(want_state, have_state.strip()):
                failed_conditions.append('state ' + 'eq(%s)' % want_state)

        if want_tx_rate:
            match = re.search(r'%s (\d+)' % 'output rate', output[0], re.M)
            have_tx_rate = None
            if match:
                have_tx_rate = match.group(1)

            if have_tx_rate is None or not conditional(want_tx_rate, have_tx_rate.strip(), cast=int):
                failed_conditions.append('tx_rate ' + want_tx_rate)

        if want_rx_rate:
            match = re.search(r'%s (\d+)' % 'input rate', output[0], re.M)
            have_rx_rate = None
            if match:
                have_rx_rate = match.group(1)

            if have_rx_rate is None or not conditional(want_rx_rate, have_rx_rate.strip(), cast=int):
                failed_conditions.append('rx_rate ' + want_rx_rate)

        if want_neighbors:
            have_host = []
            have_port = []
            if have_neighbors is None:
                command = {'command': 'show lldp neighbors {}'.format(w['name']), 'output': 'text'}
                have_neighbors = run_commands(module, [command])

            if have_neighbors[0]:
                lines = have_neighbors[0].strip().split('\n')
                col = None
                for index, line in enumerate(lines):
                    if re.search(r"^Port\s+Neighbor Device ID\s+Neighbor Port ID\s+TTL", line):
                        col = index
                        break

                if col and col < len(lines) - 1:
                    for items in lines[col + 1:]:
                        value = re.split(r'\s+', items)
                        try:
                            have_port.append(value[2])
                            have_host.append(value[1])
                        except IndexError:
                            pass

            for item in want_neighbors:
                host = item.get('host')
                port = item.get('port')
                if host and host not in have_host:
                    failed_conditions.append('host ' + host)
                if port and port not in have_port:
                    failed_conditions.append('port ' + port)
    return failed_conditions


def main():
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
        enabled=dict(default=True, type='bool'),
        tx_rate=dict(),
        rx_rate=dict(),
        neighbors=dict(type='list', elements='dict', options=neighbors_spec),
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
    argument_spec.update(eos_argument_spec)

    required_one_of = [['name', 'aggregate']]
    mutually_exclusive = [['name', 'aggregate']]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=required_one_of,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    warnings = list()
    result = {'changed': False}
    if warnings:
        result['warnings'] = warnings

    want = map_params_to_obj(module)
    have = map_config_to_obj(module)
    commands = map_obj_to_commands((want, have), module)
    result['commands'] = commands

    if commands:
        commit = not module.check_mode
        response = load_config(module, commands, commit=commit)
        if response.get('diff') and module._diff:
            result['diff'] = {'prepared': response.get('diff')}
        result['session_name'] = response.get('session')
        result['changed'] = True

    failed_conditions = check_declarative_intent_params(module, want, result)

    if failed_conditions:
        msg = 'One or more conditional statements have not been satisfied'
        module.fail_json(msg=msg, failed_conditions=failed_conditions)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
