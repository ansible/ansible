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
module: vyos_lldp_interface
version_added: "2.4"
author: "Ricardo Carrillo Cruz (@rcarrillocruz)"
short_description: Manage LLDP interfaces configuration on VyOS network devices
description:
  - This module provides declarative management of LLDP interfaces
    configuration on VyOS network devices.
options:
  name:
    description:
      - Name of the interface LLDP should be configured on.
  aggregate:
    description: List of interfaces LLDP should be configured on.
  purge:
    description:
      - Purge interfaces not defined in the aggregate parameter.
    default: no
  state:
    description:
      - State of the LLDP configuration.
    default: present
    choices: ['present', 'absent', 'enabled', 'disabled']
"""

EXAMPLES = """
- name: Enable LLDP on eth1
  vyos_lldp_interface:
    state: present

- name: Enable LLDP on specific interfaces
  vyos_lldp_interface:
    name:
      - eth1
      - eth2
    state: present

- name: Disable LLDP globally
  vyos_lldp_interface:
    state: lldp

- name: Create aggregate of LLDP interface configurations again
  vyos_lldp_interface:
    aggregate:
    - { name: eth1, state: present }
    - { name: eth2, state: present }

- name: Delete aggregate of LLDP interface configurations
  vyos_lldp_interface:
    aggregate:
    - { name: eth1, state: absent }
    - { name: eth2, state: absent }
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
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vyos import get_config, load_config
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
    aggregate = module.params.get('aggregate')
    if aggregate:
        return aggregate
    else:
        return [{'name': module.params['name'], 'state': module.params['state']}]


def main():
    """ main entry point for module execution
    """
    element_spec = dict(
        name=dict(),
        state=dict(default='present',
                   choices=['present', 'absent',
                            'enabled', 'disabled'])
    )

    required_one_of = [['name', 'aggregate']]
    mutually_exclusive = [['name', 'aggregate'],
                          ['state', 'aggregate']]

    aggregate_spec = element_spec.copy()
    aggregate_spec['name'] = dict(required=True)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec),
        purge=dict(default=False, type='bool')
    )

    argument_spec.update(element_spec)
    argument_spec.update(vyos_argument_spec)

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
