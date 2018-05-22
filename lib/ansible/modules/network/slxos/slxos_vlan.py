#!/usr/bin/python
#
# (c) 2018 Extreme Networks Inc.
#
# This file is part of Ansible
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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: slxos_vlan
version_added: "2.6"
author: "Lindsay Hill (@lindsayhill)"
short_description: Manage VLANs on Extreme Networks SLX-OS network devices
description:
  - This module provides declarative management of VLANs
    on Extreme SLX-OS network devices.
notes:
  - Tested against SLX-OS 17s.1.02
options:
  name:
    description:
      - Name of the VLAN.
  vlan_id:
    description:
      - ID of the VLAN. Range 1-4094.
    required: true
  interfaces:
    description:
      - List of interfaces that should be associated to the VLAN.
    required: true
  delay:
    description:
      - Delay the play should wait to check for declarative intent params values.
    default: 10
  aggregate:
    description: List of VLANs definitions.
  purge:
    description:
      - Purge VLANs not defined in the I(aggregate) parameter.
    type: bool
    default: no
  state:
    description:
      - State of the VLAN configuration.
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: Create vlan
  slxos_vlan:
    vlan_id: 100
    name: test-vlan
    state: present
- name: Add interfaces to VLAN
  slxos_vlan:
    vlan_id: 100
    interfaces:
      - Ethernet 0/1
      - Ethernet 0/2
- name: Delete vlan
  slxos_vlan:
    vlan_id: 100
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - vlan 100
    - name test-vlan
"""

import re
import time

from copy import deepcopy

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import remove_default_spec
from ansible.module_utils.network.slxos.slxos import load_config, run_commands


def search_obj_in_list(vlan_id, lst):
    obj = list()
    for o in lst:
        if o['vlan_id'] == vlan_id:
            return o
    return None


def map_obj_to_commands(updates, module):
    commands = list()
    want, have = updates
    purge = module.params['purge']

    for w in want:
        vlan_id = w['vlan_id']
        name = w['name']
        interfaces = w['interfaces']
        state = w['state']

        obj_in_have = search_obj_in_list(vlan_id, have)

        if state == 'absent':
            if obj_in_have:
                commands.append('no vlan %s' % vlan_id)

        elif state == 'present':
            if not obj_in_have:
                commands.append('vlan %s' % vlan_id)
                if name:
                    commands.append('name %s' % name)

                if interfaces:
                    for i in interfaces:
                        commands.append('interface %s' % i)
                        commands.append('switchport')
                        commands.append('switchport mode access')
                        commands.append('switchport access vlan %s' % vlan_id)

            else:
                if name:
                    if name != obj_in_have['name']:
                        commands.append('vlan %s' % vlan_id)
                        commands.append('name %s' % name)

                if interfaces:
                    if not obj_in_have['interfaces']:
                        for i in interfaces:
                            commands.append('vlan %s ' % vlan_id)
                            commands.append('interface %s' % i)
                            commands.append('switchport')
                            commands.append('switchport mode access')
                            commands.append('switchport access vlan %s' % vlan_id)

                    elif set(interfaces) != set(obj_in_have['interfaces']):
                        missing_interfaces = list(set(interfaces) - set(obj_in_have['interfaces']))
                        for i in missing_interfaces:
                            commands.append('vlan %s' % vlan_id)
                            commands.append('interface %s' % i)
                            commands.append('switchport')
                            commands.append('switchport mode access')
                            commands.append('switchport access vlan %s' % vlan_id)

                        superfluous_interfaces = list(set(obj_in_have['interfaces']) - set(interfaces))
                        for i in superfluous_interfaces:
                            commands.append('vlan %s' % vlan_id)
                            commands.append('interface %s' % i)
                            commands.append('switchport mode access')
                            commands.append('no switchport access vlan %s' % vlan_id)

    if purge:
        for h in have:
            obj_in_want = search_obj_in_list(h['vlan_id'], want)
            if not obj_in_want and h['vlan_id'] != '1':
                commands.append('no vlan %s' % h['vlan_id'])

    return commands


def map_params_to_obj(module):
    obj = []
    aggregate = module.params.get('aggregate')
    if aggregate:
        for item in aggregate:
            for key in item:
                if item.get(key) is None:
                    item[key] = module.params[key]

            d = item.copy()
            d['vlan_id'] = str(d['vlan_id'])

            obj.append(d)
    else:
        obj.append({
            'vlan_id': str(module.params['vlan_id']),
            'name': module.params['name'],
            'interfaces': module.params['interfaces'],
            'state': module.params['state']
        })

    return obj


def map_config_to_obj(module):
    output = run_commands(module, ['show vlan brief'])
    lines = output[0].strip().splitlines()[5:]

    if not lines:
        return list()

    objs = list()
    obj = {}

    for l in lines:
        splitted_line = re.split(r'([0-9]+)? +(\S.{14})? +(ACTIVE|INACTIVE\(.+?\))? +(Eth .+?|Po .+?)\([ut]\)\s*$', l.rstrip())
        if len(splitted_line) == 1:
            # Handle situation where VLAN is configured, but has no associated ports
            inactive = re.match(r'([0-9]+)? +(\S.{14}) +INACTIVE\(no member port\)$', l.rstrip())
            if inactive:
                splitted_line = ['', inactive.groups()[0], inactive.groups()[1], '', '']
            else:
                continue

        splitted_line[4] = splitted_line[4].replace('Eth', 'Ethernet').replace('Po', 'Port-channel')

        if splitted_line[1] is None:
            obj['interfaces'].append(splitted_line[4])
            continue

        obj = {}
        obj['vlan_id'] = splitted_line[1]
        obj['name'] = splitted_line[2].strip()
        obj['interfaces'] = [splitted_line[4]]

        objs.append(obj)

    return objs


def check_declarative_intent_params(want, module):
    if module.params['interfaces']:
        time.sleep(module.params['delay'])
        have = map_config_to_obj(module)

        for w in want:
            for i in w['interfaces']:
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
        delay=dict(default=10, type='int'),
        state=dict(default='present',
                   choices=['present', 'absent'])
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

    required_one_of = [['vlan_id', 'aggregate']]
    mutually_exclusive = [['vlan_id', 'aggregate']]

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
        if not module.check_mode:
            load_config(module, commands)
        result['changed'] = True

    if result['changed']:
        check_declarative_intent_params(want, module)

    module.exit_json(**result)

if __name__ == '__main__':
    main()
