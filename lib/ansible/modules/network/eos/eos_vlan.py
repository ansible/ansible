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
notes:
  - Tested against EOS 4.15
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
      - List of interfaces that should be associated to the VLAN. The name of interface is
        case sensitive and should be in expanded format and not abbreviated.
  associated_interfaces:
    description:
      - This is a intent option and checks the operational state of the for given vlan C(name)
        for associated interfaces. The name of interface is case sensitive and should be in
        expanded format and not abbreviated. If the value in the C(associated_interfaces)
        does not match with the operational state of vlan interfaces on device it will result in failure.
    version_added: "2.5"
  delay:
    description:
      - Delay the play should wait to check for declarative intent params values.
    default: 10
  aggregate:
    description: List of VLANs definitions.
  purge:
    description:
      - Purge VLANs not defined in the I(aggregate) parameter.
    default: no
  state:
    description:
      - State of the VLAN configuration.
    default: present
    choices: ['present', 'absent', 'active', 'suspend']
extends_documentation_fragment: eos
"""

EXAMPLES = """
- name: Create vlan
  eos_vlan:
    vlan_id: 4000
    name: vlan-4000
    state: present

- name: Add interfaces to vlan
  eos_vlan:
    vlan_id: 4000
    state: present
    interfaces:
      - Ethernet1
      - Ethernet2

- name: Check if interfaces is assigned to vlan
  eos_vlan:
    vlan_id: 4000
    associated_interfaces:
      - Ethernet1
      - Ethernet2

- name: Suspend vlan
  eos_vlan:
    vlan_id: 4000
    state: suspend

- name: Unsuspend vlan
  eos_vlan:
    vlan_id: 4000
    state: active

- name: Create aggregate of vlans
  eos_vlan:
    aggregate:
      - vlan_id: 4000
      - {vlan_id: 4001, name: vlan-4001}
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
import re
import time

from copy import deepcopy

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import remove_default_spec
from ansible.module_utils.network.eos.eos import load_config, run_commands
from ansible.module_utils.network.eos.eos import eos_argument_spec, check_args


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
        interfaces = w['interfaces']

        obj_in_have = search_obj_in_list(vlan_id, have)

        if state == 'absent':
            if obj_in_have:
                commands.append('no vlan %s' % w['vlan_id'])
        elif state == 'present':
            if not obj_in_have:
                commands.append('vlan %s' % w['vlan_id'])
                if w['name']:
                    commands.append('name %s' % w['name'])

                if w['interfaces']:
                    for i in w['interfaces']:
                        commands.append('interface %s' % i)
                        commands.append('switchport access vlan %s' % w['vlan_id'])
            else:
                if w['name'] and w['name'] != obj_in_have['name']:
                    commands.append('vlan %s' % w['vlan_id'])
                    commands.append('name %s' % w['name'])

                if w['interfaces']:
                    if not obj_in_have['interfaces']:
                        for i in w['interfaces']:
                            commands.append('vlan %s' % w['vlan_id'])
                            commands.append('interface %s' % i)
                            commands.append('switchport access vlan %s' % w['vlan_id'])
                    elif set(w['interfaces']) != obj_in_have['interfaces']:
                        missing_interfaces = list(set(w['interfaces']) - set(obj_in_have['interfaces']))
                        for i in missing_interfaces:
                            commands.append('vlan %s' % w['vlan_id'])
                            commands.append('interface %s' % i)
                            commands.append('switchport access vlan %s' % w['vlan_id'])

                        superfluous_interfaces = list(set(obj_in_have['interfaces']) - set(w['interfaces']))
                        for i in superfluous_interfaces:
                            commands.append('vlan %s' % w['vlan_id'])
                            commands.append('interface %s' % i)
                            commands.append('no switchport access vlan %s' % w['vlan_id'])
        else:
            if not obj_in_have:
                commands.append('vlan %s' % w['vlan_id'])
                if w['name']:
                    commands.append('name %s' % w['name'])
                commands.append('state %s' % w['state'])
            elif (w['name'] and obj_in_have['name'] != w['name']) or obj_in_have['state'] != w['state']:
                commands.append('vlan %s' % w['vlan_id'])

                if w['name']:
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
    vlans = run_commands(module, ['show vlan conf | json'])

    for vlan in vlans[0]['vlans']:
        obj = {}
        obj['vlan_id'] = vlan
        obj['name'] = vlans[0]['vlans'][vlan]['name']
        obj['state'] = vlans[0]['vlans'][vlan]['status']
        obj['interfaces'] = []

        interfaces = vlans[0]['vlans'][vlan]

        for interface in interfaces['interfaces']:
            obj['interfaces'].append(interface)

        if obj['state'] == 'suspended':
            obj['state'] = 'suspend'

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

            if item.get('interfaces'):
                item['interfaces'] = [intf.replace(" ", "") for intf in item.get('interfaces') if intf]

            if item.get('associated_interfaces'):
                item['associated_interfaces'] = [intf.replace(" ", "") for intf in item.get('associated_interfaces') if intf]

            d = item.copy()
            d['vlan_id'] = str(d['vlan_id'])

            obj.append(d)
    else:
        obj.append({
            'vlan_id': str(module.params['vlan_id']),
            'name': module.params['name'],
            'state': module.params['state'],
            'interfaces': [intf.replace(" ", "") for intf in module.params['interfaces']] if module.params['interfaces'] else [],
            'associated_interfaces': [intf.replace(" ", "") for intf in
                                      module.params['associated_interfaces']] if module.params['associated_interfaces'] else []

        })

    return obj


def check_declarative_intent_params(want, module, result):
    have = None
    is_delay = False

    for w in want:
        if w.get('associated_interfaces') is None:
            continue

        if result['changed'] and not is_delay:
            time.sleep(module.params['delay'])
            is_delay = True

        if have is None:
            have = map_config_to_obj(module)

        for i in w['associated_interfaces']:
            obj_in_have = search_obj_in_list(w['vlan_id'], have)

            if obj_in_have and 'interfaces' in obj_in_have and i not in obj_in_have['interfaces']:
                module.fail_json(msg="Interface %s not configured on vlan %s" % (i, w['vlan_id']))


def main():
    """ main entry point for module execution
    """
    element_spec = dict(
        vlan_id=dict(type='int'),
        name=dict(),
        interfaces=dict(type='list'),
        associated_interfaces=dict(type='list'),
        delay=dict(default=10, type='int'),
        state=dict(default='present',
                   choices=['present', 'absent', 'active', 'suspend'])
    )

    aggregate_spec = deepcopy(element_spec)
    aggregate_spec['vlan_id'] = dict(required=True)

    # remove default in aggregate spec, to handle common arguments
    remove_default_spec(aggregate_spec)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec),
        purge=dict(default=False, type='bool')
    )

    argument_spec.update(element_spec)
    argument_spec.update(eos_argument_spec)

    required_one_of = [['vlan_id', 'aggregate']]
    mutually_exclusive = [['vlan_id', 'aggregate']]
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           required_one_of=required_one_of,
                           mutually_exclusive=mutually_exclusive)

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

    check_declarative_intent_params(want, module, result)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
