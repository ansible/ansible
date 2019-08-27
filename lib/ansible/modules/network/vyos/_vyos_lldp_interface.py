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
module: vyos_lldp_interface
version_added: "2.4"
author: "Ricardo Carrillo Cruz (@rcarrillocruz)"
short_description: Manage LLDP interfaces configuration on VyOS network devices
description:
  - This module provides declarative management of LLDP interfaces
    configuration on VyOS network devices.
deprecated:
  removed_in: '2.13'
  alternative: vyos_lldp_interfaces
  why: Updated modules released with more functionality.
notes:
  - Tested against VYOS 1.1.7
options:
  name:
    description:
      - Name of the interface LLDP should be configured on.
    type: str
  aggregate:
    description: List of interfaces LLDP should be configured on.
    type: list
  state:
    description:
      - State of the LLDP configuration.
    default: present
    choices: ['present', 'absent', 'enabled', 'disabled']
    type: str
extends_documentation_fragment: vyos
"""

EXAMPLES = """
- name: Enable LLDP on eth1
  net_lldp_interface:
    state: present

- name: Enable LLDP on specific interfaces
  net_lldp_interface:
    interfaces:
      - eth1
      - eth2
    state: present

- name: Disable LLDP globally
  net_lldp_interface:
    state: disabled

- name: Create aggregate of LLDP interface configurations
  vyos_lldp_interface:
    aggregate:
    - name: eth1
    - name: eth2
    state: present

- name: Delete aggregate of LLDP interface configurations
  vyos_lldp_interface:
    aggregate:
    - name: eth1
    - name: eth2
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always, except for the platforms that use Netconf transport to manage the device.
  type: list
  sample:
    - set service lldp eth1
    - set service lldp eth2 disable
"""


from copy import deepcopy

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import remove_default_spec
from ansible.module_utils.network.vyos.vyos import get_config, load_config
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
        state = w['state']

        obj_in_have = search_obj_in_list(name, have)

        if state == 'absent' and obj_in_have:
            commands.append('delete service lldp interface ' + name)
        elif state in ('present', 'enabled'):
            if not obj_in_have:
                commands.append('set service lldp interface ' + name)
            elif obj_in_have and obj_in_have['state'] == 'disabled' and state == 'enabled':
                commands.append('delete service lldp interface ' + name + ' disable')
        elif state == 'disabled':
            if not obj_in_have:
                commands.append('set service lldp interface ' + name)
                commands.append('set service lldp interface ' + name + ' disable')
            elif obj_in_have and obj_in_have['state'] != 'disabled':
                commands.append('set service lldp interface ' + name + ' disable')

    return commands


def map_config_to_obj(module):
    obj = []
    config = get_config(module).splitlines()

    output = [c for c in config if c.startswith("set service lldp interface")]

    for i in output:
        splitted_line = i.split()

        if len(splitted_line) > 5:
            new_obj = {'name': splitted_line[4]}

            if splitted_line[5] == "'disable'":
                new_obj['state'] = 'disabled'
        else:
            new_obj = {'name': splitted_line[4][1:-1]}
            new_obj['state'] = 'present'

        obj.append(new_obj)

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
        obj.append({'name': module.params['name'], 'state': module.params['state']})

    return obj


def main():
    """ main entry point for module execution
    """
    element_spec = dict(
        name=dict(),
        state=dict(default='present',
                   choices=['present', 'absent',
                            'enabled', 'disabled'])
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
