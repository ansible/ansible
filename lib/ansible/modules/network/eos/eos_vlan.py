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
  trunk_groups:
    description:
      - List of trunk groups that should be associated to the VLAN.
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


def search_obj_in_list(vlan_id, lst):
    for o in lst:
        if o['vlan_id'] == vlan_id:
            return o


def map_obj_to_commands(updates, module):
    commands = list()
    want, have = updates
    purge = module.params['purge']

    for w in want:
        vlan_id = w['vlan_id']
        name = w['name']
        state = w['state']
        trunk_groups = w['trunk_groups']

        obj_in_have = search_obj_in_list(vlan_id, have)

        if state == 'absent':
            if obj_in_have:
                commands.append('no vlan %s' % w['vlan_id'])
        elif state == 'present':
            if not obj_in_have or w['name'] != obj_in_have['name']:
                commands.append('vlan %s' % w['vlan_id'])
                commands.append('name %s' % w['name'])
        else:
            if not obj_in_have:
                commands.append('vlan %s' % w['vlan_id'])
                commands.append('name %s' % w['name'])
                commands.append('state %s' % w['state'])
            elif obj_in_have['name'] != w['name'] or obj_in_have['state'] != w['state']:
                commands.append('vlan %s' % w['vlan_id'])

                if obj_in_have['name'] != w['name']:
                    commands.append('name %s' % w['name'])

                if obj_in_have['state'] != w['state']:
                    commands.append('state %s' % w['state'])

    if purge:
        for h in have:
            obj_in_want = search_obj_in_list(h['vlan_id'], want)
            if not obj_in_want and h['vlan_id'] != '1':
                commands.append('no vlan %s' % h['vlan_id'])

    return commands


def map_config_to_obj(module):
    objs = []
    output = run_commands(module, ['show vlan'])
    lines = output[0].strip().splitlines()[2:]

    for l in lines:
        splitted_line = re.split(r'\s{2,}', l.strip())
        obj = {}
        obj['vlan_id'] = splitted_line[0]
        obj['name'] = splitted_line[1]
        obj['state'] = splitted_line[2]

        if obj['state'] == 'suspended':
            obj['state'] = 'suspend'

        if len(splitted_line) > 3:
            obj['trunk_groups'] = []

            for i in splitted_line[3].split(','):
                obj['trunk_groups'].append(i.strip())

        objs.append(obj)

    return objs


def map_params_to_obj(module):
    obj = []

    if 'aggregate' in module.params and module.params['aggregate']:
        for v in module.params['aggregate']:
            d = v.copy()

            if 'state' not in d:
                d['state'] = module.params['state']

            obj.append(d)
    else:
        vlan_id = str(module.params['vlan_id'])
        name = module.params['name']
        state = module.params['state']
        trunk_groups = module.params['trunk_groups']

        obj.append({
            'vlan_id': vlan_id,
            'name': name,
            'state': state,
            'trunk_groups': trunk_groups
        })

    return obj


def check_declarative_intent_params(want, module):
    pass


def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        vlan_id=dict(type='int'),
        name=dict(),
        trunk_groups=dict(type='list'),
        aggregate=dict(type='list'),
        purge=dict(default=False, type='bool'),
        state=dict(default='present',
                   choices=['present', 'absent', 'active', 'suspend'])
    )

    argument_spec.update(eos_argument_spec)

    required_one_of = [['vlan_id', 'aggregate']]
    mutually_exclusive = [['vlan_id', 'aggregate']]
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
