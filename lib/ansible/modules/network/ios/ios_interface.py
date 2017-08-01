#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'core'}


DOCUMENTATION = """
---
module: ios_interface
version_added: "2.4"
author: "Ganesh Nalawade (@ganeshrn)"
short_description: Manage Interface on Cisco IOS network devices
description:
  - This module provides declarative management of Interfaces
    on Cisco IOS network devices.
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
    default: auto
    choices: ['full', 'half', 'auto']
  tx_rate:
    description:
      - Transmit rate
  rx_rate:
    description:
      - Receiver rate
  aggregate:
    description: List of Interfaces definitions.
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
  ios_interface:
      name: GigabitEthernet0/2
      description: test-interface
      speed: 100
      duplex: half
      mtu: 512

- name: remove interface
  ios_interface:
    name: Loopback9
    state: absent

- name: make interface up
  ios_interface:
    name: GigabitEthernet0/2
    state: up

- name: make interface down
  ios_interface:
    name: GigabitEthernet0/2
    state: down
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device.
  returned: always, except for the platforms that use Netconf transport to manage the device.
  type: list
  sample:
  - interface GigabitEthernet0/2
  - description test-interface
  - duplex half
  - mtu 512
"""
import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ios import get_config, load_config
from ansible.module_utils.ios import ios_argument_spec, check_args
from ansible.module_utils.netcfg import NetworkConfig

DEFAULT_DESCRIPTION = "configured by ios_interface"


def validate_mtu(value, module):
    if value and not 64 <= int(value) <= 9600:
        module.fail_json(msg='mtu must be between 64 and 9600')


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
    args = ['name', 'description', 'speed', 'duplex', 'mtu']

    aggregate = module.params.get('aggregate')
    if aggregate:
        for param in aggregate:
            validate_param_values(module, args, param)
            d = param.copy()

            if 'name' not in d:
                module.fail_json(msg="missing required arguments: %s" % 'name')

            # set default value
            for item in args:
                if item not in d:
                    if item == 'description':
                        d['description'] = DEFAULT_DESCRIPTION
                    else:
                        d[item] = None
                else:
                    d[item] = str(d[item])

            if not d.get('state'):
                d['state'] = module.params['state']

            if d['state'] in ('present', 'up'):
                d['disable'] = False
            else:
                d['disable'] = True

            obj.append(d)

    else:
        validate_param_values(module, args)

        params = {
            'name': module.params['name'],
            'description': module.params['description'],
            'speed': module.params['speed'],
            'mtu': module.params['mtu'],
            'duplex': module.params['duplex'],
            'state': module.params['state']
        }

        state = module.params['state']
        if state == 'present' or state == 'up':
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
                        elif running:
                            # if value present in device is default value for
                            # interface, don't delete
                            if running == 'auto' and item in ('speed', 'duplex'):
                                continue
                            cmd = 'no ' + item + ' ' + str(running)
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


def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        name=dict(),
        description=dict(default=DEFAULT_DESCRIPTION),
        speed=dict(),
        mtu=dict(),
        duplex=dict(choices=['full', 'half', 'auto']),
        enabled=dict(),
        tx_rate=dict(),
        rx_rate=dict(),
        aggregate=dict(type='list'),
        purge=dict(default=False, type='bool'),
        state=dict(default='present',
                   choices=['present', 'absent', 'up', 'down'])
    )

    argument_spec.update(ios_argument_spec)

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

    module.exit_json(**result)

if __name__ == '__main__':
    main()
