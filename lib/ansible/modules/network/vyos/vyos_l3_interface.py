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
module: vyos_l3_interface
version_added: "2.4"
author: "Ricardo Carrillo Cruz (@rcarrillocruz)"
short_description: Manage L3 interfaces on VyOS network devices
description:
  - This module provides declarative management of L3 interfaces
    on VyOS network devices.
options:
  name:
    description:
      - Name of the L3 interface.
  ipv4:
    description:
      - IPv4 of the L3 interface.
  ipv6:
    description:
      - IPv6 of the L3 interface.
  aggregate:
    description: List of L3 interfaces definitions
  purge:
    description:
      - Purge L3 interfaces not defined in the aggregate parameter.
    default: no
  state:
    description:
      - State of the L3 interface configuration.
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: Set eth0 IPv4 address
  vyos_l3_interface:
    name: eth0
    ipv4: 192.168.0.1/24

- name: Remove eth0 IPv4 address
  vyos_l3_interface:
    name: eth0
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always, except for the platforms that use Netconf transport to manage the device.
  type: list
  sample:
    - set interfaces ethernet eth0 address '192.168.0.1/24'
"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vyos import load_config, run_commands
from ansible.module_utils.vyos import vyos_argument_spec, check_args


def search_obj_in_list(name, lst):
    for o in lst:
        if o['name'] == name:
            return o

    return None


def map_obj_to_commands(updates, module):
    commands = list()
    want, have = updates

    for w in want:
        name = w['name']
        ipv4 = w['ipv4']
        ipv6 = w['ipv6']
        state = w['state']

        obj_in_have = search_obj_in_list(name, have)
        if state == 'absent' and obj_in_have:
            if not ipv4 and not ipv6 and (obj_in_have['ipv4'] or obj_in_have['ipv6']):
                commands.append('delete interfaces ethernet ' + name + ' address')
            else:
                if ipv4 and obj_in_have['ipv4']:
                    commands.append('delete interfaces ethernet ' + name + ' address ' + ipv4)
                if ipv6 and obj_in_have['ipv6']:
                    commands.append('delete interfaces ethernet ' + name + ' address ' + ipv6)
        elif (state == 'present' and obj_in_have):
            if ipv4 and ipv4 != obj_in_have['ipv4']:
                commands.append('set interfaces ethernet ' + name + ' address ' +
                                ipv4)

            if ipv6 and ipv6 != obj_in_have['ipv6']:
                commands.append('set interfaces ethernet ' + name + ' address ' +
                                ipv6)

    return commands


def map_config_to_obj(module):
    obj = []
    output = run_commands(module, ['show interfaces ethernet'])
    lines = output[0].splitlines()

    if len(lines) > 3:
        for line in lines[3:]:
            splitted_line = line.split()

            if len(splitted_line) > 1:
                name = splitted_line[0]
                address = splitted_line[1]

                if address == '-':
                    address = None

                if address is not None and ':' not in address:
                    obj.append({'name': name,
                                'ipv4': address,
                                'ipv6': None})
                else:
                    obj.append({'name': name,
                                'ipv6': address,
                                'ipv4': None})
            else:
                obj[-1]['ipv6'] = splitted_line[0]

    return obj


def map_params_to_obj(module):
    obj = []

    if 'aggregate' in module.params and module.params['aggregate']:
        for c in module.params['aggregate']:
            d = c.copy()

            if 'ipv4' not in d:
                d['ipv4'] = None
            if 'ipv6' not in d:
                d['ipv6'] = None
            if 'state' not in d:
                d['state'] = module.params['state']

            obj.append(d)
    else:
        obj.append({
            'name': module.params['name'],
            'ipv4': module.params['ipv4'],
            'ipv6': module.params['ipv6'],
            'state': module.params['state']
        })

    return obj


def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        name=dict(),
        ipv4=dict(),
        ipv6=dict(),
        aggregate=dict(type='list'),
        purge=dict(default=False, type='bool'),
        state=dict(default='present',
                   choices=['present', 'absent'])
    )

    argument_spec.update(vyos_argument_spec)

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

    commands = map_obj_to_commands((want, have), module)
    result['commands'] = commands

    if commands:
        commit = not module.check_mode
        load_config(module, commands, commit=commit)
        result['changed'] = True

    module.exit_json(**result)

if __name__ == '__main__':
    main()
