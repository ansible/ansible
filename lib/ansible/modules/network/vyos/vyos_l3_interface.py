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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: vyos_l3_interface
version_added: "2.4"
author: "Ricardo Carrillo Cruz (@rcarrillocruz)"
short_description: Manage L3 interfaces on VyOS network devices
description:
  - This module provides declarative management of L3 interfaces
    on VyOS network devices.
notes:
  - Tested against VYOS 1.1.7
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
  state:
    description:
      - State of the L3 interface configuration.
    default: present
    choices: ['present', 'absent']
extends_documentation_fragment: vyos
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

- name: Set IP addresses on aggregate
  vyos_l3_interface:
    aggregate:
      - { name: eth1, ipv4: 192.168.2.10/24 }
      - { name: eth2, ipv4: 192.168.3.10/24, ipv6: "fd5d:12c9:2201:1::1/64" }

- name: Remove IP addresses on aggregate
  vyos_l3_interface:
    aggregate:
      - { name: eth1, ipv4: 192.168.2.10/24 }
      - { name: eth2, ipv4: 192.168.3.10/24, ipv6: "fd5d:12c9:2201:1::1/64" }
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

import socket
import re

from copy import deepcopy

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import is_masklen, validate_ip_address
from ansible.module_utils.network.common.utils import remove_default_spec
from ansible.module_utils.network.vyos.vyos import load_config, run_commands
from ansible.module_utils.network.vyos.vyos import vyos_argument_spec


def is_ipv4(value):
    if value:
        address = value.split('/')
        if is_masklen(address[1]) and validate_ip_address(address[0]):
            return True
    return False


def is_ipv6(value):
    if value:
        address = value.split('/')
        if 0 <= int(address[1]) <= 128:
            try:
                socket.inet_pton(socket.AF_INET6, address[0])
            except socket.error:
                return False
            return True
    return False


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
                if name == "lo":
                    commands.append('delete interfaces loopback lo address')
                else:
                    commands.append('delete interfaces ethernet ' + name + ' address')
            else:
                if ipv4 and ipv4 in obj_in_have['ipv4']:
                    if name == "lo":
                        commands.append('delete interfaces loopback lo address ' + ipv4)
                    else:
                        commands.append('delete interfaces ethernet ' + name + ' address ' + ipv4)
                if ipv6 and ipv6 in obj_in_have['ipv6']:
                    if name == "lo":
                        commands.append('delete interfaces loopback lo address ' + ipv6)
                    else:
                        commands.append('delete interfaces ethernet ' + name + ' address ' + ipv6)
        elif (state == 'present' and obj_in_have):
            if ipv4 and ipv4 not in obj_in_have['ipv4']:
                if name == "lo":
                    commands.append('set interfaces loopback lo address ' + ipv4)
                else:
                    commands.append('set interfaces ethernet ' + name + ' address ' + ipv4)

            if ipv6 and ipv6 not in obj_in_have['ipv6']:
                if name == "lo":
                    commands.append('set interfaces loopback lo address ' + ipv6)
                else:
                    commands.append('set interfaces ethernet ' + name + ' address ' + ipv6)

    return commands


def map_config_to_obj(module):
    obj = []
    output = run_commands(module, ['show interfaces'])
    lines = re.split(r'\n[e|l]', output[0])[1:]

    if len(lines) > 0:
        for line in lines:
            splitted_line = line.split()

            if len(splitted_line) > 0:
                ipv4 = []
                ipv6 = []

                if splitted_line[0].lower().startswith('th'):
                    name = 'e' + splitted_line[0].lower()
                elif splitted_line[0].lower().startswith('o'):
                    name = 'l' + splitted_line[0].lower()

                for i in splitted_line[1:]:
                    if (('.' in i or ':' in i) and '/' in i):
                        value = i.split(r'\n')[0]
                        if is_ipv4(value):
                            ipv4.append(value)
                        elif is_ipv6(value):
                            ipv6.append(value)

                obj.append({'name': name,
                            'ipv4': ipv4,
                            'ipv6': ipv6})

    return obj


def map_params_to_obj(module):
    obj = []

    aggregate = module.params.get('aggregate')
    if aggregate:
        for item in aggregate:
            for key in item:
                if item.get(key) is None:
                    item[key] = module.params[key]

            obj.append(item.copy())
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
    element_spec = dict(
        name=dict(),
        ipv4=dict(),
        ipv6=dict(),
        state=dict(default='present',
                   choices=['present', 'absent'])
    )

    aggregate_spec = deepcopy(element_spec)
    aggregate_spec['name'] = dict(required=True)

    # remove default in aggregate spec, to handle common arguments
    remove_default_spec(aggregate_spec)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec),
    )

    argument_spec.update(element_spec)
    argument_spec.update(vyos_argument_spec)

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
        load_config(module, commands, commit=commit)
        result['changed'] = True

    module.exit_json(**result)

if __name__ == '__main__':
    main()
