#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: icx_interface
version_added: "2.9"
author: "Ruckus Wireless (@Commscope)"
short_description: Manage Interface on Ruckus ICX 7000 series switches
description:
  - This module provides declarative management of Interfaces
    on ruckus icx devices.
notes:
  - Tested against ICX 10.1.
  - For information on using ICX platform, see L(the ICX OS Platform Options guide,../network/user_guide/platform_icx.html).
options:
  name:
    description:
      - Name of the Interface.
    type: str
  description:
    description:
      - Name of the description.
    type: str
  enabled:
    description:
      - Interface link status
    default: yes
    type: bool
  speed:
    description:
      - Interface link speed/duplex
    choices: ['10-full', '10-half', '100-full', '100-half', '1000-full', '1000-full-master',
    '1000-full-slave', '10g-full', '10g-full-master', '10g-full-slave', '2500-full', '2500-full-master',
    '2500-full-slave', '5g-full', '5g-full-master', '5g-full-slave', 'auto']
    type: str
  stp:
    description:
      - enable/disable stp for the interface
    type: bool
  tx_rate:
    description:
      - Transmit rate in bits per second (bps).
      - This is state check parameter only.
      - Supports conditionals, see L(Conditionals in Networking Modules,../network/user_guide/network_working_with_command_output.html)
    type: str
  rx_rate:
    description:
      - Receiver rate in bits per second (bps).
      - This is state check parameter only.
      - Supports conditionals, see L(Conditionals in Networking Modules,../network/user_guide/network_working_with_command_output.html)
    type: str
  neighbors:
    description:
      - Check the operational state of given interface C(name) for CDP/LLDP neighbor.
      - The following suboptions are available.
    type: list
    suboptions:
      host:
        description:
          - "CDP/LLDP neighbor host for given interface C(name)."
        type: str
      port:
        description:
          - "CDP/LLDP neighbor port to which given interface C(name) is connected."
        type: str
  delay:
    description:
      - Time in seconds to wait before checking for the operational state on remote
        device. This wait is applicable for operational state argument which are
        I(state) with values C(up)/C(down), I(tx_rate) and I(rx_rate).
    type: int
    default: 10
  state:
    description:
      - State of the Interface configuration, C(up) means present and
        operationally up and C(down) means present and operationally C(down)
    default: present
    type: str
    choices: ['present', 'absent', 'up', 'down']
  power:
    description:
      - Inline power on Power over Ethernet (PoE) ports.
    type: dict
    suboptions:
        by_class:
          description:
            - "The range is 0-4"
            - "The power limit based on class value for given interface C(name)"
          choices: ['0', '1', '2', '3', '4']
          type: str
        limit:
          description:
            - "The range is 1000-15400|30000mW. For PoH ports the range is 1000-95000mW"
            - "The power limit based on actual power value for given interface C(name)"
          type: str
        priority:
          description:
            - "The range is 1 (highest) to 3 (lowest)"
            - "The priority for power management or given interface C(name)"
          choices: ['1', '2', '3']
          type: str
        enabled:
          description:
            - "enable/disable the poe of the given interface C(name)"
          default: no
          type: bool
  aggregate:
    description:
      - List of Interfaces definitions.
    type: list
    suboptions:
      name:
        description:
          - Name of the Interface.
        type: str
      description:
        description:
          - Name of the description.
        type: str
      enabled:
        description:
          - Interface link status
        type: bool
      speed:
        description:
          - Interface link speed/duplex
        choices: ['10-full', '10-half', '100-full', '100-half', '1000-full', '1000-full-master',
        '1000-full-slave', '10g-full', '10g-full-master', '10g-full-slave', '2500-full', '2500-full-master',
        '2500-full-slave', '5g-full', '5g-full-master', '5g-full-slave', 'auto']
        type: str
      stp:
        description:
          - enable/disable stp for the interface
        type: bool
      tx_rate:
        description:
          - Transmit rate in bits per second (bps).
          - This is state check parameter only.
          - Supports conditionals, see L(Conditionals in Networking Modules,../network/user_guide/network_working_with_command_output.html)
        type: str
      rx_rate:
        description:
          - Receiver rate in bits per second (bps).
          - This is state check parameter only.
          - Supports conditionals, see L(Conditionals in Networking Modules,../network/user_guide/network_working_with_command_output.html)
        type: str
      neighbors:
        description:
          - Check the operational state of given interface C(name) for CDP/LLDP neighbor.
          - The following suboptions are available.
        type: list
        suboptions:
          host:
            description:
              - "CDP/LLDP neighbor host for given interface C(name)."
            type: str
          port:
            description:
              - "CDP/LLDP neighbor port to which given interface C(name) is connected."
            type: str
      delay:
        description:
          - Time in seconds to wait before checking for the operational state on remote
            device. This wait is applicable for operational state argument which are
            I(state) with values C(up)/C(down), I(tx_rate) and I(rx_rate).
        type: int
      state:
        description:
          - State of the Interface configuration, C(up) means present and
            operationally up and C(down) means present and operationally C(down)
        type: str
        choices: ['present', 'absent', 'up', 'down']
      check_running_config:
        description:
          - Check running configuration. This can be set as environment variable.
          - Module will use environment variable value(default:True), unless it is overridden, by specifying it as module parameter.
        type: bool
      power:
        description:
          - Inline power on Power over Ethernet (PoE) ports.
        type: dict
        suboptions:
            by_class:
              description:
                - "The range is 0-4"
                - "The power limit based on class value for given interface C(name)"
              choices: ['0', '1', '2', '3', '4']
              type: str
            limit:
              description:
                - "The range is 1000-15400|30000mW. For PoH ports the range is 1000-95000mW"
                - "The power limit based on actual power value for given interface C(name)"
              type: str
            priority:
              description:
                - "The range is 1 (highest) to 3 (lowest)"
                - "The priority for power management or given interface C(name)"
              choices: ['1', '2', '3']
              type: str
            enabled:
              description:
                - "enable/disable the poe of the given interface C(name)"
              type: bool
  check_running_config:
    description:
      - Check running configuration. This can be set as environment variable.
      - Module will use environment variable value(default:True), unless it is overridden,
       by specifying it as module parameter.
    default: yes
    type: bool
"""

EXAMPLES = """
- name: enable ethernet port and set name
  icx_interface:
    name: ethernet 1/1/1
    description: interface-1
    stp: true
    enabled: true

- name: disable ethernet port 1/1/1
  icx_interface:
      name: ethernet 1/1/1
      enabled: false

- name: enable ethernet port range, set name and speed.
  icx_interface:
      name: ethernet 1/1/1 to 1/1/10
      description: interface-1
      speed: 100-full
      enabled: true

- name: enable poe. Set class.
  icx_interface:
      name: ethernet 1/1/1
      power:
       by_class: 2

- name: configure poe limit of interface
  icx_interface:
      name: ethernet 1/1/1
      power:
       limit: 10000

- name: disable poe of interface
  icx_interface:
      name: ethernet 1/1/1
      power:
       enabled: false

- name: set lag name for a range of lags
  icx_interface:
      name: lag 1 to 10
      description: test lags

- name: Disable lag
  icx_interface:
      name: lag 1
      enabled: false

- name: enable management interface
  icx_interface:
      name: management 1
      enabled: true

- name: enable loopback interface
  icx_interface:
      name: loopback 10
      enabled: true

- name: Add interface using aggregate
  icx_interface:
      aggregate:
      - { name: ethernet 1/1/1, description: test-interface-1, power: { by_class: 2 } }
      - { name: ethernet 1/1/3, description: test-interface-3}
      speed: 10-full
      enabled: true

- name: Check tx_rate, rx_rate intent arguments
  icx_interface:
    name: ethernet 1/1/10
    state: up
    tx_rate: ge(0)
    rx_rate: le(0)

- name: Check neighbors intent arguments
  icx_interface:
    name: ethernet 1/1/10
    neighbors:
    - port: 1/1/5
      host: netdev
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device.
  returned: always
  type: list
  sample:
  - interface ethernet 1/1/1
  - port-name interface-1
  - state present
  - speed-duplex 100-full
  - inline power priority 1
"""

import re
from copy import deepcopy
from time import sleep
from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.network.common.config import NetworkConfig
from ansible.module_utils.network.icx.icx import load_config, get_config
from ansible.module_utils.connection import Connection, ConnectionError, exec_command
from ansible.module_utils.network.common.utils import conditional, remove_default_spec


def parse_enable(configobj, name):
    cfg = configobj['interface %s' % name]
    cfg = '\n'.join(cfg.children)
    match = re.search(r'^disable', cfg, re.M)
    if match:
        return True
    else:
        return False


def parse_power_argument(configobj, name):
    cfg = configobj['interface %s' % name]
    cfg = '\n'.join(cfg.children)
    match = re.search(r'(^inline power|^inline power(.*))+$', cfg, re.M)
    if match:
        return match.group(1)


def parse_config_argument(configobj, name, arg=None):
    cfg = configobj['interface %s' % name]
    cfg = '\n'.join(cfg.children)
    match = re.search(r'%s (.+)$' % arg, cfg, re.M)
    if match:
        return match.group(1)


def parse_stp_arguments(module, item):
    rc, out, err = exec_command(module, 'show interfaces ' + item)
    match = re.search(r'STP configured to (\S+),', out, re.S)
    if match:
        return True if match.group(1) == "ON" else False


def search_obj_in_list(name, lst):
    for o in lst:
        if o['name'] == name:
            return o

    return None


def validate_power(module, power):
    count = 0
    for item in power:
        if power.get(item) is not None:
            count += 1
    if count > 1:
        module.fail_json(msg='power parameters are mutually exclusive: class,limit,priority,enabled')


def add_command_to_interface(interface, cmd, commands):
    if interface not in commands:
        commands.append(interface)
    commands.append(cmd)


def map_config_to_obj(module):
    compare = module.params['check_running_config']
    config = get_config(module, None, compare)
    configobj = NetworkConfig(indent=1, contents=config)
    match = re.findall(r'^interface (.+)$', config, re.M)

    if not match:
        return list()

    instances = list()

    for item in set(match):
        obj = {
            'name': item,
            'port-name': parse_config_argument(configobj, item, 'port-name'),
            'speed-duplex': parse_config_argument(configobj, item, 'speed-duplex'),
            'stp': parse_stp_arguments(module, item),
            'disable': True if parse_enable(configobj, item) else False,
            'power': parse_power_argument(configobj, item),
            'state': 'present'
        }
        instances.append(obj)
    return instances


def parse_poe_config(poe, power):
    if poe.get('by_class') is not None:
        power += 'power-by-class %s' % poe.get('by_class')
    elif poe.get('limit') is not None:
        power += 'power-limit %s' % poe.get('limit')
    elif poe.get('priority') is not None:
        power += 'priority %s' % poe.get('priority')
    elif poe.get('enabled'):
        power = 'inline power'
    elif poe.get('enabled') is False:
        power = 'no inline power'
    return power


def map_params_to_obj(module):
    obj = []
    aggregate = module.params.get('aggregate')
    if aggregate:
        for item in aggregate:
            for key in item:
                if item.get(key) is None:
                    item[key] = module.params[key]

            item['port-name'] = item.pop('description')
            item['speed-duplex'] = item.pop('speed')
            poe = item.get('power')
            if poe:

                validate_power(module, poe)
                power = 'inline power' + ' '
                power_arg = parse_poe_config(poe, power)
                item.update({'power': power_arg})

            d = item.copy()

            if d['enabled']:
                d['disable'] = False
            else:
                d['disable'] = True

            obj.append(d)

    else:
        params = {
            'name': module.params['name'],
            'port-name': module.params['description'],
            'speed-duplex': module.params['speed'],
            'stp': module.params['stp'],
            'delay': module.params['delay'],
            'state': module.params['state'],
            'tx_rate': module.params['tx_rate'],
            'rx_rate': module.params['rx_rate'],
            'neighbors': module.params['neighbors']
        }
        poe = module.params.get('power')
        if poe:
            validate_power(module, poe)
            power = 'inline power' + ' '
            power_arg = parse_poe_config(poe, power)
            params.update({'power': power_arg})

        if module.params['enabled']:
            params.update({'disable': False})
        else:
            params.update({'disable': True})

        obj.append(params)
    return obj


def map_obj_to_commands(updates):
    commands = list()
    want, have = updates

    args = ('speed-duplex', 'port-name', 'power', 'stp')
    for w in want:
        name = w['name']
        disable = w['disable']
        state = w['state']

        obj_in_have = search_obj_in_list(name, have)
        interface = 'interface ' + name

        if state == 'absent' and have == []:
            commands.append('no ' + interface)

        elif state == 'absent' and obj_in_have:
            commands.append('no ' + interface)

        elif state in ('present', 'up', 'down'):
            if obj_in_have:
                for item in args:
                    candidate = w.get(item)
                    running = obj_in_have.get(item)
                    if candidate == 'no inline power' and running is None:
                        candidate = None
                    if candidate != running:
                        if candidate:
                            if item == 'power':
                                cmd = str(candidate)
                            elif item == 'stp':
                                cmd = 'spanning-tree' if candidate else 'no spanning-tree'
                            else:
                                cmd = item + ' ' + str(candidate)
                            add_command_to_interface(interface, cmd, commands)

                if disable and not obj_in_have.get('disable', False):
                    add_command_to_interface(interface, 'disable', commands)
                elif not disable and obj_in_have.get('disable', False):
                    add_command_to_interface(interface, 'enable', commands)
            else:
                commands.append(interface)
                for item in args:
                    value = w.get(item)
                    if value:
                        if item == 'power':
                            commands.append(str(value))
                        elif item == 'stp':
                            cmd = 'spanning-tree' if item else 'no spanning-tree'
                        else:
                            commands.append(item + ' ' + str(value))

                if disable:
                    commands.append('disable')
                if disable is False:
                    commands.append('enable')

    return commands


def check_declarative_intent_params(module, want, result):
    failed_conditions = []
    have_neighbors_lldp = None
    have_neighbors_cdp = None
    for w in want:
        want_state = w.get('state')
        want_tx_rate = w.get('tx_rate')
        want_rx_rate = w.get('rx_rate')
        want_neighbors = w.get('neighbors')

        if want_state not in ('up', 'down') and not want_tx_rate and not want_rx_rate and not want_neighbors:
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
            if have_state is None or not conditional(want_state, have_state.strip()):
                failed_conditions.append('state ' + 'eq(%s)' % want_state)

        if want_tx_rate:
            match = re.search(r'%s (\d+)' % 'output rate:', out, re.M)
            have_tx_rate = None
            if match:
                have_tx_rate = match.group(1)

            if have_tx_rate is None or not conditional(want_tx_rate, have_tx_rate.strip(), cast=int):
                failed_conditions.append('tx_rate ' + want_tx_rate)

        if want_rx_rate:
            match = re.search(r'%s (\d+)' % 'input rate:', out, re.M)
            have_rx_rate = None
            if match:
                have_rx_rate = match.group(1)

            if have_rx_rate is None or not conditional(want_rx_rate, have_rx_rate.strip(), cast=int):
                failed_conditions.append('rx_rate ' + want_rx_rate)

        if want_neighbors:
            have_host = []
            have_port = []

            if have_neighbors_lldp is None:
                rc, have_neighbors_lldp, err = exec_command(module, 'show lldp neighbors detail')
                if rc != 0:
                    module.fail_json(msg=to_text(err, errors='surrogate_then_replace'), command=command, rc=rc)
            if have_neighbors_lldp:
                lines = have_neighbors_lldp.strip().split('Local port: ')

                for line in lines:
                    field = line.split('\n')
                    if field[0].strip() == w['name'].split(' ')[1]:
                        for item in field:
                            match = re.search(r'\s*\+\s+System name\s+:\s+"(.*)"', item, re.M)
                            if match:
                                have_host.append(match.group(1))

                            match = re.search(r'\s*\+\s+Port description\s+:\s+"(.*)"', item, re.M)
                            if match:
                                have_port.append(match.group(1))

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
    power_spec = dict(
        by_class=dict(choices=['0', '1', '2', '3', '4']),
        limit=dict(type='str'),
        priority=dict(choices=['1', '2', '3']),
        enabled=dict(type='bool')
    )
    neighbors_spec = dict(
        host=dict(),
        port=dict()
    )
    element_spec = dict(
        name=dict(),
        description=dict(),
        enabled=dict(default=True, type='bool'),
        speed=dict(type='str', choices=['10-full', '10-half', '100-full', '100-half', '1000-full', '1000-full-master',
                                        '1000-full-slave', '10g-full', '10g-full-master', '10g-full-slave', '2500-full', '2500-full-master',
                                        '2500-full-slave', '5g-full', '5g-full-master', '5g-full-slave', 'auto']),
        stp=dict(type='bool'),
        tx_rate=dict(),
        rx_rate=dict(),
        neighbors=dict(type='list', elements='dict', options=neighbors_spec),
        delay=dict(default=10, type='int'),
        state=dict(default='present',
                   choices=['present', 'absent', 'up', 'down']),
        power=dict(type='dict', options=power_spec),
        check_running_config=dict(default=True, type='bool', fallback=(env_fallback, ['ANSIBLE_CHECK_ICX_RUNNING_CONFIG']))
    )
    aggregate_spec = deepcopy(element_spec)
    aggregate_spec['name'] = dict(required=True)

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
    result = {}
    result['changed'] = False
    if warnings:
        result['warnings'] = warnings
    exec_command(module, 'skip')
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
