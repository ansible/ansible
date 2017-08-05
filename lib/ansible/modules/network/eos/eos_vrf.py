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
module: eos_vrf
version_added: "2.4"
author: "Ricardo Carrillo Cruz (@rcarrillocruz)"
short_description: Manage VRFs on Arista EOS network devices
description:
  - This module provides declarative management of VRFs
    on Arista EOS network devices.
options:
  name:
    description:
      - Name of the VRF.
    required: true
  rd:
    description:
      - Route distinguisher of the VRF
  interfaces:
    description:
      - List of interfaces to check the VRF has been
        configured correctly.
  aggregate:
    description: List of VRFs definitions
  purge:
    description:
      - Purge VRFs not defined in the aggregates parameter.
    default: no
  state:
    description:
      - State of the VRF configuration.
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - vrf definition test
    - rd 1:100
    - interface Ethernet1
    - vrf forwarding test
"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.eos import load_config, run_commands
from ansible.module_utils.eos import eos_argument_spec, check_args
from ansible.module_utils.six import iteritems

import re


def map_obj_to_commands(updates, module):
    commands = list()
    want, have = updates
    state = module.params['state']

    if state == 'absent':
        if have:
            commands.append('no vrf definition %s' % want['name'])
    elif state == 'present':
        if not have:
            commands.append('vrf definition %s' % want['name'])

            if want['rd'] is not None:
                commands.append('rd %s' % want['rd'])

            if want['interfaces']:
                for i in want['interfaces']:
                    commands.append('interface %s' % i)
                    commands.append('vrf forwarding %s' % want['name'])
        else:
            if want['rd'] is not None and want['rd'] != have['rd']:
                commands.append('vrf definition %s' % want['name'])
                commands.append('rd %s' % want['rd'])

            if want['interfaces']:
                if not have['interfaces']:
                    for i in want['interfaces']:
                        commands.append('interface %s' % i)
                        commands.append('vrf forwarding %s' % want['name'])
                elif set(want['interfaces']) != have['interfaces']:
                    missing_interfaces = list(set(want['interfaces']) - set(have['interfaces']))

                    for i in missing_interfaces:
                        commands.append('interface %s' % i)
                        commands.append('vrf forwarding %s' % want['name'])

    return commands


def map_config_to_obj(module):
    obj = {}
    output = run_commands(module, ['show vrf %s' % module.params['name']])
    lines = output[0].strip().splitlines()

    if len(lines) > 2:
        splitted_line = re.split(r'\s{2,}', lines[2].strip())
        obj['name'] = splitted_line[0]
        obj['rd'] = splitted_line[1]
        obj['interfaces'] = None

        if len(splitted_line) > 4:
            obj['interfaces'] = []
            for i in splitted_line[4].split(','):
                obj['interfaces'].append(i.strip())

    return obj


def map_params_to_obj(module):
    return {
        'name': module.params['name'],
        'state': module.params['state'],
        'rd': module.params['rd'],
        'interfaces': module.params['interfaces']
    }


def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        name=dict(required=True),
        interfaces=dict(type='list'),
        rd=dict(),
        aggregate=dict(),
        purge=dict(default=False, type='bool'),
        state=dict(default='present', choices=['present', 'absent'])
    )

    argument_spec.update(eos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
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
        response = load_config(module, commands, commit=commit)
        if response.get('diff') and module._diff:
            result['diff'] = {'prepared': response.get('diff')}
        result['session_name'] = response.get('session')
        result['changed'] = True

    module.exit_json(**result)

if __name__ == '__main__':
    main()
