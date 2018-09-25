#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: ios_vlan
version_added: "2.5"
author: "Trishna Guha (@trishnaguha)"
short_description: Manage VLANs on IOS network devices
description:
  - This module provides declarative management of VLANs
    on Cisco IOS network devices.
notes:
  - Tested against IOS 15.2
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
  associated_interfaces:
    description:
      - This is a intent option and checks the operational state of the for given vlan C(name)
        for associated interfaces. If the value in the C(associated_interfaces) does not match with
        the operational state of vlan interfaces on device it will result in failure.
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
extends_documentation_fragment: ios
"""

EXAMPLES = """
- name: Create vlan
  ios_vlan:
    vlan_id: 100
    name: test-vlan
    state: present

- name: Add interfaces to VLAN
  ios_vlan:
    vlan_id: 100
    interfaces:
      - GigabitEthernet0/0
      - GigabitEthernet0/1

- name: Check if interfaces is assigned to VLAN
  ios_vlan:
    vlan_id: 100
    associated_interfaces:
      - GigabitEthernet0/0
      - GigabitEthernet0/1

- name: Delete vlan
  ios_vlan:
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
from ansible.module_utils.network.ios.ios import load_config, run_commands, normalize_interface
from ansible.module_utils.network.ios.ios import ios_argument_spec, check_args


def search_obj_in_list(vlan_id, lst):
    obj = list()
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
        interfaces = w['interfaces']
        state = w['state']

        obj_in_have = search_obj_in_list(vlan_id, have)

        if state == 'absent':
            if obj_in_have:
                commands.append('no vlan {0}'.format(vlan_id))

        elif state == 'present':
            if not obj_in_have:
                commands.append('vlan {0}'.format(vlan_id))
                if name:
                    commands.append('name {0}'.format(name))

                if interfaces:
                    for i in interfaces:
                        commands.append('interface {0}'.format(i))
                        commands.append('switchport mode access')
                        commands.append('switchport access vlan {0}'.format(vlan_id))

            else:
                if name:
                    if name != obj_in_have['name']:
                        commands.append('vlan {0}'.format(vlan_id))
                        commands.append('name {0}'.format(name))

                if interfaces:
                    if not obj_in_have['interfaces']:
                        for i in interfaces:
                            commands.append('vlan {0}'.format(vlan_id))
                            commands.append('interface {0}'.format(i))
                            commands.append('switchport mode access')
                            commands.append('switchport access vlan {0}'.format(vlan_id))

                    elif set(interfaces) != set(obj_in_have['interfaces']):
                        missing_interfaces = list(set(interfaces) - set(obj_in_have['interfaces']))
                        for i in missing_interfaces:
                            commands.append('vlan {0}'.format(vlan_id))
                            commands.append('interface {0}'.format(i))
                            commands.append('switchport mode access')
                            commands.append('switchport access vlan {0}'.format(vlan_id))

                        superfluous_interfaces = list(set(obj_in_have['interfaces']) - set(interfaces))
                        for i in superfluous_interfaces:
                            commands.append('vlan {0}'.format(vlan_id))
                            commands.append('interface {0}'.format(i))
                            commands.append('switchport mode access')
                            commands.append('no switchport access vlan {0}'.format(vlan_id))
        else:
            commands.append('vlan {0}'.format(vlan_id))
            if name:
                commands.append('name {0}'.format(name))
            commands.append('state {0}'.format(state))

    if purge:
        for h in have:
            obj_in_want = search_obj_in_list(h['vlan_id'], want)
            if not obj_in_want and h['vlan_id'] != '1':
                commands.append('no vlan {0}'.format(h['vlan_id']))

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
            'associated_interfaces': module.params['associated_interfaces'],
            'state': module.params['state']
        })

    return obj


def parse_to_logical_rows(out):
    started_yielding = False
    cur_row = []
    for l in out.splitlines()[2:]:
        if not l:
            """Skip empty lines."""
            continue
        if '0' < l[0] <= '9':
            """Line starting with a number."""
            if started_yielding:
                yield cur_row
                cur_row = []  # Reset it to hold a next chunk
            started_yielding = True
        cur_row.append(l)

    # Return the rest of it:
    yield cur_row


def map_ports_str_to_list(ports_str):
    return list(filter(bool, (normalize_interface(p.strip()) for p in ports_str.split(', '))))


def parse_to_obj(logical_rows):
    first_row = logical_rows[0]
    rest_rows = logical_rows[1:]
    obj = re.match(r'(?P<vlan_id>\d+)\s+(?P<name>[^\s]+)\s+(?P<state>[^\s]+)\s*(?P<interfaces>.*)', first_row).groupdict()
    if obj['state'] == 'suspended':
        obj['state'] = 'suspend'
    obj['interfaces'] = map_ports_str_to_list(obj['interfaces'])
    obj['interfaces'].extend(prts_r for prts in rest_rows for prts_r in map_ports_str_to_list(prts))
    return obj


def parse_vlan_brief(vlan_out):
    return [parse_to_obj(r) for r in parse_to_logical_rows(vlan_out)]


def map_config_to_obj(module):
    return parse_vlan_brief(run_commands(module, ['show vlan brief'])[0])


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
    argument_spec.update(ios_argument_spec)

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

    check_declarative_intent_params(want, module, result)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
