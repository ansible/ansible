#!/usr/bin/python
# -*- coding: utf-8 -*-

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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'core'}


DOCUMENTATION = """
---
module: vyos_interface
version_added: "2.4"
author: "Ganesh Nalawade (@ganeshrn)"
short_description: Manage Interface on VyOS network devices
description:
  - This module provides declarative management of Interfaces
    on VyOS network devices.
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
      - Interface link status.
    default: auto
    choices: ['full', 'half', 'auto']
  tx_rate:
    description:
      - Transmit rate.
  rx_rate:
    description:
      - Receiver rate.
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
  vyos_interface:
    name: eth0
    description: test-interface

- name: remove interface
  vyos_interface:
    name: eth0
    state: absent

- name: make interface down
  vyos_interface:
    name: eth0
    state: down

- name: make interface up
  vyos_interface:
    name: eth0
    state: up

- name: Configure interface speed, mtu, duplex
  vyos_interface:
    name: eth5
    state: present
    speed: 100
    mtu: 256
    duplex: full
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always, except for the platforms that use Netconf transport to manage the device.
  type: list
  sample:
    - set interfaces ethernet eth0 description "test-interface"
    - set interfaces ethernet eth0 speed 100
    - set interfaces ethernet eth0 mtu 256
    - set interfaces ethernet eth0 duplex full
"""
import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vyos import load_config, get_config
from ansible.module_utils.vyos import vyos_argument_spec, check_args

DEFAULT_DESCRIPTION = "'configured by vyos_interface'"


def search_obj_in_list(name, lst):
    for o in lst:
        if o['name'] == name:
            return o

    return None


def map_obj_to_commands(updates):
    commands = list()
    want, have = updates

    params = ('speed', 'description', 'duplex', 'mtu')
    for w in want:
        name = w['name']
        disable = w['disable']
        state = w['state']

        obj_in_have = search_obj_in_list(name, have)
        set_interface = 'set interfaces ethernet ' + name
        delete_interface = 'delete interfaces ethernet ' + name

        if state == 'absent' and obj_in_have:
            commands.append(delete_interface)
        elif state in ('present', 'up', 'down'):
            if obj_in_have:
                for item in params:
                    value = w.get(item)

                    if value and value != obj_in_have.get(item):
                        commands.append(set_interface + ' ' + item + ' ' + str(value))

                if disable and not obj_in_have.get('disable', False):
                    commands.append(set_interface + ' disable')
                elif not disable and obj_in_have.get('disable', False):
                    commands.append(delete_interface + ' disable')
            else:
                commands.append(set_interface)
                for item in params:
                    value = w.get(item)
                    if value:
                        commands.append(set_interface + ' ' + item + ' ' + str(value))

                if disable:
                    commands.append(set_interface + ' disable')
    return commands


def map_config_to_obj(module):
    data = get_config(module)
    obj = []
    for line in data.split('\n'):
        if line.startswith('set interfaces ethernet'):
            match = re.search(r'set interfaces ethernet (\S+)', line, re.M)
            name = match.group(1)
            if name:
                interface = {}
                for item in obj:
                    if item['name'] == name:
                        interface = item
                        break

                if not interface:
                    interface = {'name': name}
                    obj.append(interface)

                match = re.search(r'%s (\S+)' % name, line, re.M)
                if match:

                    param = match.group(1)
                    if param == 'description':
                        match = re.search(r'description (\S+)', line, re.M)
                        description = match.group(1).strip("'")
                        interface['description'] = description
                    elif param == 'speed':
                        match = re.search(r'speed (\S+)', line, re.M)
                        speed = match.group(1).strip("'")
                        interface['speed'] = speed
                    elif param == 'mtu':
                        match = re.search(r'mtu (\S+)', line, re.M)
                        mtu = match.group(1).strip("'")
                        interface['mtu'] = int(mtu)
                    elif param == 'duplex':
                        match = re.search(r'duplex (\S+)', line, re.M)
                        duplex = match.group(1).strip("'")
                        interface['duplex'] = duplex
                    elif param.strip("'") == 'disable':
                        interface['disable'] = True

    return obj


def map_params_to_obj(module):
    obj = []

    params = ['speed', 'description', 'duplex', 'mtu']
    aggregate = module.params.get('aggregate')

    if aggregate:
        for c in aggregate:
            d = c.copy()
            if 'name' not in d:
                module.fail_json(msg="missing required arguments: %s" % 'name')

            for item in params:
                if item not in d:
                    d[item] = None

            d['description'] = DEFAULT_DESCRIPTION
            if not d.get('state'):
                d['state'] = module.params['state']

            if d['state'] in ('present', 'up'):
                d['disable'] = False
            else:
                d['disable'] = True

            if d.get('speed'):
                d['speed'] = str(d['speed'])

            obj.append(d)
    else:
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


def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        name=dict(),
        description=dict(default=DEFAULT_DESCRIPTION),
        speed=dict(),
        mtu=dict(type='int'),
        duplex=dict(choices=['full', 'half', 'auto']),
        tx_rate=dict(),
        rx_rate=dict(),
        aggregate=dict(type='list'),
        purge=dict(default=False, type='bool'),
        state=dict(default='present',
                   choices=['present', 'absent', 'up', 'down'])
    )

    argument_spec.update(vyos_argument_spec)

    required_one_of = [['name', 'aggregate']]
    mutually_exclusive = [['name', 'aggregate']]

    required_together = (['speed', 'duplex'])
    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=required_one_of,
                           mutually_exclusive=mutually_exclusive,
                           required_together=required_together,
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
        commit = not module.check_mode
        diff = load_config(module, commands, commit=commit)
        if diff:
            if module._diff:
                result['diff'] = {'prepared': diff}
        result['changed'] = True

    module.exit_json(**result)

if __name__ == '__main__':
    main()
