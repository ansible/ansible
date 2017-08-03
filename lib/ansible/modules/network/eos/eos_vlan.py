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
module: eos_vlan
version_added: "2.4"
author: "Ricardo Carrillo Cruz (@rcarrillocruz)"
short_description: Manage VLANs on Arista EOS network devices
description:
  - This module provides declarative management of VLANs
    on Arista EOS network devices.
options:
  name:
    description:
      - Name of the VLAN.
  vlan_id:
    description:
      - ID of the VLAN.
    required: true
  interfaces:
    description:
      - List of interfaces to check the VLAN has been
        configured correctly.
  aggregate:
    description: List of VLANs definitions
  purge:
    description:
      - Purge VLANs not defined in the aggregates parameter.
    default: no
  state:
    description:
      - State of the VLAN configuration.
    default: present
    choices: ['present', 'absent', 'active', 'suspend']
"""

EXAMPLES = """
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - vlan 20
    - name test-vlan
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
            commands.append('no vlan %s' % want['vlan_id'])
    elif state == 'present':
        if not have or want['name'] != have['name']:
            commands.append('vlan %s' % want['vlan_id'])
            commands.append('name %s' % want['name'])
    else:
        if not have:
            commands.append('vlan %s' % want['vlan_id'])
            commands.append('name %s' % want['name'])
            commands.append('state %s' % want['state'])
        elif have['name'] != want['name'] or have['state'] != want['state']:
            commands.append('vlan %s' % want['vlan_id'])

            if have['name'] != want['name']:
                commands.append('name %s' % want['name'])

            if have['state'] != want['state']:
                commands.append('state %s' % want['state'])

    return commands


def map_config_to_obj(module):
    obj = {}
    output = run_commands(module, ['show vlan'])

    if isinstance(output[0], str):
        for l in output[0].strip().splitlines()[2:]:
            split_line = l.split()
            vlan_id = split_line[0]
            name = split_line[1]
            status = split_line[2]

            if vlan_id == str(module.params['vlan_id']):
                obj['vlan_id'] = vlan_id
                obj['name'] = name
                obj['state'] = status
                if obj['state'] == 'suspended':
                    obj['state'] = 'suspend'
                break
    else:
        for k, v in iteritems(output[0]['vlans']):
            vlan_id = k
            name = v['name']
            status = v['status']

            if vlan_id == str(module.params['vlan_id']):
                obj['vlan_id'] = vlan_id
                obj['name'] = name
                obj['state'] = status
                if obj['state'] == 'suspended':
                    obj['state'] = 'suspend'
                break

    return obj


def map_params_to_obj(module):
    return {
        'vlan_id': str(module.params['vlan_id']),
        'name': module.params['name'],
        'state': module.params['state']
    }


def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        vlan_id=dict(required=True, type='int'),
        name=dict(),
        interfaces=dict(),
        aggregate=dict(),
        purge=dict(default=False, type='bool'),
        state=dict(default='present',
                   choices=['present', 'absent', 'active', 'suspend'])
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
