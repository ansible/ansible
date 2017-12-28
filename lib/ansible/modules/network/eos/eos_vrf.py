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
module: eos_vrf
version_added: "2.4"
author: "Ricardo Carrillo Cruz (@rcarrillocruz)"
short_description: Manage VRFs on Arista EOS network devices
description:
  - This module provides declarative management of VRFs
    on Arista EOS network devices.
notes:
  - Tested against EOS 4.15
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
      - Purge VRFs not defined in the I(aggregate) parameter.
    default: no
  delay:
    description:
      - Time in seconds to wait before checking for the operational state on remote
        device. This wait is applicable for operational state arguments.
    default: 10
  state:
    description:
      - State of the VRF configuration.
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: Create vrf
  eos_vrf:
    name: test
    rd: 1:200
    interfaces:
      - Ethernet2
    state: present

- name: Delete VRFs
  eos_vrf:
    name: test
    state: absent

- name: Create aggregate of VRFs with purge
  eos_vrf:
    aggregate:
      - { name: test4, rd: "1:204" }
      - { name: test5, rd: "1:205" }
    state: present
    purge: yes

- name: Delete aggregate of VRFs
  eos_vrf:
    aggregate:
      - name: test2
      - name: test3
      - name: test4
      - name: test5
    state: absent
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
import re
import time

from copy import deepcopy

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import remove_default_spec
from ansible.module_utils.network.eos.eos import load_config, run_commands
from ansible.module_utils.network.eos.eos import eos_argument_spec, check_args


def search_obj_in_list(name, lst):
    for o in lst:
        if o['name'] == name:
            return o


def map_obj_to_commands(updates, module):
    commands = list()
    want, have = updates
    state = module.params['state']
    purge = module.params['purge']

    for w in want:
        name = w['name']
        rd = w['rd']
        interfaces = w['interfaces']

        obj_in_have = search_obj_in_list(name, have)

        if state == 'absent':
            if obj_in_have:
                commands.append('no vrf definition %s' % name)
        elif state == 'present':
            if not obj_in_have:
                commands.append('vrf definition %s' % name)

                if rd is not None:
                    commands.append('rd %s' % rd)

                if w['interfaces']:
                    for i in w['interfaces']:
                        commands.append('interface %s' % i)
                        commands.append('vrf forwarding %s' % w['name'])
            else:
                if w['rd'] is not None and w['rd'] != obj_in_have['rd']:
                    commands.append('vrf definition %s' % w['name'])
                    commands.append('rd %s' % w['rd'])

                if w['interfaces']:
                    if not obj_in_have['interfaces']:
                        for i in w['interfaces']:
                            commands.append('interface %s' % i)
                            commands.append('vrf forwarding %s' % w['name'])
                    elif set(w['interfaces']) != obj_in_have['interfaces']:
                        missing_interfaces = list(set(w['interfaces']) - set(obj_in_have['interfaces']))

                        for i in missing_interfaces:
                            commands.append('interface %s' % i)
                            commands.append('vrf forwarding %s' % w['name'])

    if purge:
        for h in have:
            obj_in_want = search_obj_in_list(h['name'], want)
            if not obj_in_want:
                commands.append('no vrf definition %s' % h['name'])

    return commands


def map_config_to_obj(module):
    objs = []
    output = run_commands(module, ['show vrf'])
    lines = output[0].strip().splitlines()[2:]

    for l in lines:
        if not l:
            continue

        splitted_line = re.split(r'\s{2,}', l.strip())

        if len(splitted_line) == 1:
            continue
        else:
            obj = {}
            obj['name'] = splitted_line[0]
            obj['rd'] = splitted_line[1]
            obj['interfaces'] = None

            if len(splitted_line) > 4:
                obj['interfaces'] = []

                for i in splitted_line[4].split(','):
                    obj['interfaces'].append(i.strip())

            objs.append(obj)

    return objs


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
            'state': module.params['state'],
            'rd': module.params['rd'],
            'interfaces': module.params['interfaces']
        })

    return obj


def check_declarative_intent_params(want, module):
    if module.params['interfaces']:
        time.sleep(module.params['delay'])
        have = map_config_to_obj(module)

        for w in want:
            for i in w['interfaces']:
                obj_in_have = search_obj_in_list(w['name'], have)

                if obj_in_have:
                    interfaces = obj_in_have.get('interfaces')
                    if interfaces is not None and i not in interfaces:
                        module.fail_json(msg="Interface %s not configured on vrf %s" % (i, w['name']))


def main():
    """ main entry point for module execution
    """
    element_spec = dict(
        name=dict(),
        interfaces=dict(type='list'),
        delay=dict(default=10, type='int'),
        rd=dict(),
        state=dict(default='present', choices=['present', 'absent'])
    )

    aggregate_spec = deepcopy(element_spec)

    # remove default in aggregate spec, to handle common arguments
    remove_default_spec(aggregate_spec)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec),
        purge=dict(default=False, type='bool')
    )

    argument_spec.update(element_spec)
    argument_spec.update(eos_argument_spec)

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
        response = load_config(module, commands, commit=commit)
        if response.get('diff') and module._diff:
            result['diff'] = {'prepared': response.get('diff')}
        result['session_name'] = response.get('session')
        result['changed'] = True

    if result['changed']:
        check_declarative_intent_params(want, module)

    module.exit_json(**result)

if __name__ == '__main__':
    main()
