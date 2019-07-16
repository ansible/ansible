#!/usr/bin/python
#
# (c) 2018 Extreme Networks Inc.
#
# This file is part of Ansible
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
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: slxos_interface
version_added: "2.6"
author: "Lindsay Hill (@LindsayHill)"
short_description: Manage Interfaces on Extreme SLX-OS network devices
description:
  - This module provides declarative management of Interfaces
    on Extreme SLX-OS network devices.
notes:
  - Tested against SLX-OS 17s.1.02
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
    default: True
    type: bool
  speed:
    description:
      - Interface link speed.
  mtu:
    description:
      - Maximum size of transmit packet.
  tx_rate:
    description:
      - Transmit rate in bits per second (bps).
  rx_rate:
    description:
      - Receiver rate in bits per second (bps).
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
  slxos_interface:
      name: Ethernet 0/2
      description: test-interface
      speed: 1000
      mtu: 9216

- name: remove interface
  slxos_interface:
    name: Loopback 9
    state: absent

- name: make interface up
  slxos_interface:
    name: Ethernet 0/2
    enabled: True

- name: make interface down
  slxos_interface:
    name: Ethernet 0/2
    enabled: False

- name: Check intent arguments
  slxos_interface:
    name: Ethernet 0/2
    state: up
    tx_rate: ge(0)
    rx_rate: le(0)

- name: Check neighbors intent arguments
  slxos_interface:
    name: Ethernet 0/41
    neighbors:
    - port: Ethernet 0/41
      host: SLX

- name: Config + intent
  slxos_interface:
    name: Ethernet 0/2
    enabled: False
    state: down

- name: Add interface using aggregate
  slxos_interface:
    aggregate:
    - { name: Ethernet 0/1, mtu: 1548, description: test-interface-1 }
    - { name: Ethernet 0/2, mtu: 1548, description: test-interface-2 }
    speed: 10000
    state: present

- name: Delete interface using aggregate
  slxos_interface:
    aggregate:
    - name: Loopback 9
    - name: Loopback 10
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device.
  returned: always, except for the platforms that use Netconf transport to manage the device.
  type: list
  sample:
  - interface Ethernet 0/2
  - description test-interface
  - mtu 1548
"""
import re

from copy import deepcopy
from time import sleep

from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import exec_command
from ansible.module_utils.network.slxos.slxos import get_config, load_config
from ansible.module_utils.network.common.config import NetworkConfig
from ansible.module_utils.network.common.utils import conditional, remove_default_spec


def validate_mtu(value, module):
    if value and not 1548 <= int(value) <= 9216:
        module.fail_json(msg='mtu must be between 1548 and 9216')


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
    match = re.search(r'^shutdown', cfg, re.M)
    if match:
        return True
    else:
        return False


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
    configobj = NetworkConfig(indent=1, contents=config)

    match = re.findall(r'^interface (\S+ \S+)', config, re.M)
    if not match:
        return list()

    instances = list()

    for item in set(match):
        obj = {
            'name': item,
            'description': parse_config_argument(configobj, item, 'description'),
            'speed': parse_config_argument(configobj, item, 'speed'),
            'mtu': parse_config_argument(configobj, item, 'mtu'),
            'disable': True if parse_shutdown(configobj, item) else False,
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

            validate_param_values(module, item, item)
            d = item.copy()

            if d['enabled']:
                d['disable'] = False
            else:
                d['disable'] = True

            obj.append(d)

    else:
        params = {
            'name': module.params['name'],
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


def map_obj_to_commands(updates):
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
                            cmd = item + ' ' + str(candidate)
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
                        commands.append(item + ' ' + str(value))

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

        command = 'show interface %s' % w['name']
        rc, out, err = exec_command(module, command)
        if rc != 0:
            module.fail_json(msg=to_text(err, errors='surrogate_then_replace'), command=command, rc=rc)

        if want_state in ('up', 'down'):
            match = re.search(r'%s (\w+)' % 'line protocol is', out, re.M)
            have_state = None
            if match:
                have_state = match.group(1)
            if have_state is None or not conditional(want_state, have_state.strip()):
                failed_conditions.append('state ' + 'eq(%s)' % want_state)

        if want_tx_rate:
            match = re.search(r'%s (\d+)' % 'Output', out, re.M)
            have_tx_rate = None
            if match:
                have_tx_rate = match.group(1)

            if have_tx_rate is None or not conditional(want_tx_rate, have_tx_rate.strip(), cast=int):
                failed_conditions.append('tx_rate ' + want_tx_rate)

        if want_rx_rate:
            match = re.search(r'%s (\d+)' % 'Input', out, re.M)
            have_rx_rate = None
            if match:
                have_rx_rate = match.group(1)

            if have_rx_rate is None or not conditional(want_rx_rate, have_rx_rate.strip(), cast=int):
                failed_conditions.append('rx_rate ' + want_rx_rate)

        if want_neighbors:
            have_host = []
            have_port = []
            if have_neighbors is None:
                rc, have_neighbors, err = exec_command(module, 'show lldp neighbors detail')
                if rc != 0:
                    module.fail_json(msg=to_text(err, errors='surrogate_then_replace'), command=command, rc=rc)

            if have_neighbors:
                lines = have_neighbors.strip().split('Local Interface: ')
                short_name = w['name'].replace('Ethernet', 'Eth')
                for line in lines:
                    field = line.split('\n')
                    if field[0].split('(')[0].strip() == short_name:
                        for item in field:
                            if item.startswith('System Name:'):
                                have_host.append(item.split(':')[1].strip())
                            if item.startswith('Remote Interface:'):
                                have_port.append(item.split(':')[1].split('(')[0].strip())
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

    commands = map_obj_to_commands((want, have))
    result['commands'] = commands

    if commands:
        if not module.check_mode:
            load_config(module, commands)
        result['changed'] = True

    failed_conditions = check_declarative_intent_params(module, want, result)

    if failed_conditions:
        msg = 'One or more conditional statements have not been satisfied'
        module.fail_json(msg=msg, failed_conditions=failed_conditions, changed=result['changed'])

    module.exit_json(**result)


if __name__ == '__main__':
    main()
