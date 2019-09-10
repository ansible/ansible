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
                    'status': ['deprecated'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: vyos_linkagg
version_added: "2.4"
author: "Ricardo Carrillo Cruz (@rcarrillocruz)"
short_description: Manage link aggregation groups on VyOS network devices
description:
  - This module provides declarative management of link aggregation groups
    on VyOS network devices.
deprecated:
  removed_in: '2.13'
  alternative: vyos_lag_interfaces
  why: Updated modules released with more functionality.
notes:
  - Tested against VYOS 1.1.7
options:
  name:
    description:
      - Name of the link aggregation group.
    required: true
    type: str
  mode:
    description:
      - Mode of the link aggregation group.
    choices: ['802.3ad', 'active-backup', 'broadcast',
              'round-robin', 'transmit-load-balance',
              'adaptive-load-balance', 'xor-hash', 'on']
    type: str
  members:
    description:
      - List of members of the link aggregation group.
    type: list
  aggregate:
    description: List of link aggregation definitions.
    type: list
  state:
    description:
      - State of the link aggregation group.
    default: present
    choices: ['present', 'absent', 'up', 'down']
    type: str
extends_documentation_fragment: vyos
"""

EXAMPLES = """
- name: configure link aggregation group
  vyos_linkagg:
    name: bond0
    members:
      - eth0
      - eth1

- name: remove configuration
  vyos_linkagg:
    name: bond0
    state: absent

- name: Create aggregate of linkagg definitions
  vyos_linkagg:
    aggregate:
        - { name: bond0, members: [eth1] }
        - { name: bond1, members: [eth2] }

- name: Remove aggregate of linkagg definitions
  vyos_linkagg:
    aggregate:
      - name: bond0
      - name: bond1
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always, except for the platforms that use Netconf transport to manage the device.
  type: list
  sample:
    - set interfaces bonding bond0
    - set interfaces ethernet eth0 bond-group 'bond0'
    - set interfaces ethernet eth1 bond-group 'bond0'
"""
from copy import deepcopy

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import remove_default_spec
from ansible.module_utils.network.vyos.vyos import load_config, run_commands
from ansible.module_utils.network.vyos.vyos import vyos_argument_spec


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
        members = w.get('members') or []
        mode = w['mode']

        if mode == 'on':
            mode = '802.3ad'

        state = w['state']

        obj_in_have = search_obj_in_list(name, have)

        if state == 'absent':
            if obj_in_have:
                for m in obj_in_have['members']:
                    commands.append('delete interfaces ethernet ' + m + ' bond-group')

                commands.append('delete interfaces bonding ' + name)
        else:
            if not obj_in_have:
                commands.append('set interfaces bonding ' + name + ' mode ' + mode)

                for m in members:
                    commands.append('set interfaces ethernet ' + m + ' bond-group ' + name)

                if state == 'down':
                    commands.append('set interfaces bonding ' + name + ' disable')
            else:
                if mode != obj_in_have['mode']:
                    commands.append('set interfaces bonding ' + name + ' mode ' + mode)

                missing_members = list(set(members) - set(obj_in_have['members']))
                for m in missing_members:
                    commands.append('set interfaces ethernet ' + m + ' bond-group ' + name)

                if state == 'down' and obj_in_have['state'] == 'up':
                    commands.append('set interfaces bonding ' + name + ' disable')
                elif state == 'up' and obj_in_have['state'] == 'down':
                    commands.append('delete interfaces bonding ' + name + ' disable')

    return commands


def map_config_to_obj(module):
    obj = []
    output = run_commands(module, ['show interfaces bonding slaves'])
    lines = output[0].splitlines()

    if len(lines) > 1:
        for line in lines[1:]:
            splitted_line = line.split()

            name = splitted_line[0]
            mode = splitted_line[1]
            state = splitted_line[2]

            if len(splitted_line) > 4:
                members = splitted_line[4:]
            else:
                members = []

            obj.append({'name': name,
                        'mode': mode,
                        'members': members,
                        'state': state})

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
            'mode': module.params['mode'],
            'members': module.params['members'],
            'state': module.params['state']
        })

    return obj


def main():
    """ main entry point for module execution
    """
    element_spec = dict(
        name=dict(),
        mode=dict(choices=['802.3ad', 'active-backup', 'broadcast',
                           'round-robin', 'transmit-load-balance',
                           'adaptive-load-balance', 'xor-hash', 'on'],
                  default='802.3ad'),
        members=dict(type='list'),
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
