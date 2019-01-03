#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Lenovo, Inc.
# (c) 2017, Ansible by Red Hat, inc
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
# Module to work on Interfaces with Lenovo Switches
# Lenovo Networking
#

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: cnos_interface
version_added: "2.3"
author: "Anil Kumar Muraleedharan(@amuraleedhar)"
short_description: Manage Interface on Lenovo CNOS network devices
description:
  - This module provides declarative management of Interfaces
    on Lenovo CNOS network devices.
notes:
  - Tested against CNOS 10.8.1
options:
  name:
    description:
      - Name of the Interface.
    required: true
    version_added: "2.8"
  description:
    description:
      - Description of Interface.
    version_added: "2.8"
  enabled:
    description:
      - Interface link status.
    type: bool
    default: True
    version_added: "2.8"
  speed:
    description:
      - Interface link speed.
    version_added: "2.8"
  mtu:
    description:
      - Maximum size of transmit packet.
    version_added: "2.8"
  duplex:
    description:
      - Interface link status
    default: auto
    choices: ['full', 'half', 'auto']
    version_added: "2.8"
  tx_rate:
    description:
      - Transmit rate in bits per second (bps).
      - This is state check parameter only.
      - Supports conditionals, see L(Conditionals in Networking Modules,
        ../network/user_guide/network_working_with_command_output.html)
    version_added: "2.8"
  rx_rate:
    description:
      - Receiver rate in bits per second (bps).
      - This is state check parameter only.
      - Supports conditionals, see L(Conditionals in Networking Modules,
        ../network/user_guide/network_working_with_command_output.html)
    version_added: "2.8"
  neighbors:
    description:
      - Check operational state of given interface C(name) for LLDP neighbor.
      - The following suboptions are available.
    version_added: "2.8"
    suboptions:
        host:
          description:
            - "LLDP neighbor host for given interface C(name)."
        port:
          description:
            - "LLDP neighbor port to which interface C(name) is connected."
  aggregate:
    description: List of Interfaces definitions.
    version_added: "2.8"
  delay:
    description:
      - Time in seconds to wait before checking for the operational state on
        remote device. This wait is applicable for operational state argument
        which are I(state) with values C(up)/C(down), I(tx_rate) and I(rx_rate)
    default: 20
    version_added: "2.8"
  state:
    description:
      - State of the Interface configuration, C(up) means present and
        operationally up and C(down) means present and operationally C(down)
    default: present
    version_added: "2.8"
    choices: ['present', 'absent', 'up', 'down']
  provider:
    description:
      - B(Deprecated)
      - "Starting with Ansible 2.5 we recommend using C(connection: network_cli)."
      - For more information please see the L(CNOS Platform Options guide, ../network/user_guide/platform_cnos.html).
      - HORIZONTALLINE
      - A dict object containing connection details.
    version_added: "2.8"
    suboptions:
      host:
        description:
          - Specifies the DNS host name or address for connecting to the remote
            device over the specified transport.  The value of host is used as
            the destination address for the transport.
        required: true
      port:
        description:
          - Specifies the port to use when building the connection to the remote device.
        default: 22
      username:
        description:
          - Configures the username to use to authenticate the connection to
            the remote device.  This value is used to authenticate
            the SSH session. If the value is not specified in the task, the
            value of environment variable C(ANSIBLE_NET_USERNAME) will be used instead.
      password:
        description:
          - Specifies the password to use to authenticate the connection to
            the remote device.   This value is used to authenticate
            the SSH session. If the value is not specified in the task, the
            value of environment variable C(ANSIBLE_NET_PASSWORD) will be used instead.
      timeout:
        description:
          - Specifies the timeout in seconds for communicating with the network device
            for either connecting or sending commands.  If the timeout is
            exceeded before the operation is completed, the module will error.
        default: 10
      ssh_keyfile:
        description:
          - Specifies the SSH key to use to authenticate the connection to
            the remote device.   This value is the path to the
            key used to authenticate the SSH session. If the value is not specified
            in the task, the value of environment variable C(ANSIBLE_NET_SSH_KEYFILE)
            will be used instead.
      authorize:
        description:
          - Instructs the module to enter privileged mode on the remote device
            before sending any commands.  If not specified, the device will
            attempt to execute all commands in non-privileged mode. If the value
            is not specified in the task, the value of environment variable
            C(ANSIBLE_NET_AUTHORIZE) will be used instead.
        type: bool
        default: 'no'
      auth_pass:
        description:
          - Specifies the password to use if required to enter privileged mode
            on the remote device.  If I(authorize) is false, then this argument
            does nothing. If the value is not specified in the task, the value of
            environment variable C(ANSIBLE_NET_AUTH_PASS) will be used instead.
"""

EXAMPLES = """
- name: configure interface
  cnos_interface:
      name: Ethernet1/33
      description: test-interface
      speed: 100
      duplex: half
      mtu: 999

- name: remove interface
  cnos_interface:
    name: loopback3
    state: absent

- name: make interface up
  cnos_interface:
    name: Ethernet1/33
    enabled: True

- name: make interface down
  cnos_interface:
    name: Ethernet1/33
    enabled: False

- name: Check intent arguments
  cnos_interface:
    name: Ethernet1/33
    state: up
    tx_rate: ge(0)
    rx_rate: le(0)

- name: Check neighbors intent arguments
  cnos_interface:
    name: Ethernet1/33
    neighbors:
    - port: eth0
      host: netdev

- name: Config + intent
  cnos_interface:
    name: Ethernet1/33
    enabled: False
    state: down

- name: Add interface using aggregate
  cnos_interface:
    aggregate:
    - { name: Ethernet1/33, mtu: 256, description: test-interface-1 }
    - { name: Ethernet1/44, mtu: 516, description: test-interface-2 }
    duplex: full
    speed: 100
    state: present

- name: Delete interface using aggregate
  cnos_interface:
    aggregate:
    - name: loopback3
    - name: loopback6
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device.
  returned: always, except for the platforms that use Netconf transport to
            manage the device.
  type: list
  sample:
  - interface Ethernet1/33
  - description test-interface
  - duplex half
  - mtu 512
"""
import re

from copy import deepcopy
from time import sleep

from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import exec_command
from ansible.module_utils.network.cnos.cnos import get_config, load_config
from ansible.module_utils.network.cnos.cnos import cnos_argument_spec
from ansible.module_utils.network.cnos.cnos import debugOutput, check_args
from ansible.module_utils.network.common.config import NetworkConfig
from ansible.module_utils.network.common.utils import conditional
from ansible.module_utils.network.common.utils import remove_default_spec


def validate_mtu(value, module):
    if value and not 64 <= int(value) <= 9216:
        module.fail_json(msg='mtu must be between 64 and 9216')


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

    match = re.findall(r'^interface (\S+)', config, re.M)
    if not match:
        return list()

    instances = list()

    for item in set(match):
        obj = {
            'name': item,
            'description': parse_config_argument(configobj, item, 'description'),
            'speed': parse_config_argument(configobj, item, 'speed'),
            'duplex': parse_config_argument(configobj, item, 'duplex'),
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
            'duplex': module.params['duplex'],
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
    have_neighbors_lldp = None
    for w in want:
        want_state = w.get('state')
        want_tx_rate = w.get('tx_rate')
        want_rx_rate = w.get('rx_rate')
        want_neighbors = w.get('neighbors')

        if want_state not in ('up', 'down') and not want_tx_rate and not want_rx_rate and not want_neighbors:
            continue

        if result['changed']:
            sleep(w['delay'])

        command = 'show interface %s brief' % w['name']
        rc, out, err = exec_command(module, command)
        if rc != 0:
            module.fail_json(msg=to_text(err, errors='surrogate_then_replace'), command=command, rc=rc)
        if want_state in ('up', 'down'):
            state_data = out.strip().lower().split(w['name'])
            have_state = None
            have_state = state_data[1].split()[3]
            if have_state is None or not conditional(want_state, have_state.strip()):
                failed_conditions.append('state ' + 'eq(%s)' % want_state)

        command = 'show interface %s' % w['name']
        rc, out, err = exec_command(module, command)
        have_tx_rate = None
        have_rx_rate = None
        rates = out.splitlines()
        for s in rates:
            s = s.strip()
            if 'output rate' in s and 'input rate' in s:
                sub = s.split()
                if want_tx_rate:
                    have_tx_rate = sub[8]
                    if have_tx_rate is None or not conditional(want_tx_rate, have_tx_rate.strip(), cast=int):
                        failed_conditions.append('tx_rate ' + want_tx_rate)
                if want_rx_rate:
                    have_rx_rate = sub[2]
                    if have_rx_rate is None or not conditional(want_rx_rate, have_rx_rate.strip(), cast=int):
                        failed_conditions.append('rx_rate ' + want_rx_rate)
        if want_neighbors:
            have_host = []
            have_port = []

            # Process LLDP neighbors
            if have_neighbors_lldp is None:
                rc, have_neighbors_lldp, err = exec_command(module, 'show lldp neighbors detail')
                if rc != 0:
                    module.fail_json(msg=to_text(err,
                                     errors='surrogate_then_replace'),
                                     command=command, rc=rc)

            if have_neighbors_lldp:
                lines = have_neighbors_lldp.strip().split('Local Port ID: ')
                for line in lines:
                    field = line.split('\n')
                    if field[0].strip() == w['name']:
                        for item in field:
                            if item.startswith('System Name:'):
                                have_host.append(item.split(':')[1].strip())
                            if item.startswith('Port Description:'):
                                have_port.append(item.split(':')[1].strip())

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
        duplex=dict(default='auto', choices=['full', 'half', 'auto']),
        enabled=dict(default=True, type='bool'),
        tx_rate=dict(),
        rx_rate=dict(),
        neighbors=dict(type='list', elements='dict', options=neighbors_spec),
        delay=dict(default=20, type='int'),
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
    argument_spec.update(cnos_argument_spec)

    required_one_of = [['name', 'aggregate']]
    mutually_exclusive = [['name', 'aggregate']]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=required_one_of,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)
    warnings = list()
    check_args(module, warnings)

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
        module.fail_json(msg=msg, failed_conditions=failed_conditions)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
