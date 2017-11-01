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
module: iosxr_vlan
version_added: "2.5"
author: "Trishna Guha (@trishnaguha)"
short_description: Manage VLANs on IOS XR network devices
description:
  - This module provides declarative management of VLANs
    on Cisco IOS XR network devices.
notes:
  - Tested against IOS XR 6.1.2
options:
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
    default: no
  state:
    description:
      - State of the VLAN configuration.
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: Assign vlan to a subinterface
  iosxr_vlan:
    vlan_id: 100
    interfaces: GigabitEthernet0/0/0/2
    state: present
- name: Assign VLAN to group of subinterfaces
  iosxr_vlan:
    vlan_id: 100
    interfaces:
      - GigabitEthernet0/0/0/2
      - GigabitEthernet0/0/0/3
- name: Remove vlan assigned to a subinterface
  iosxr_vlan:
    vlan_id: 100
    interfaces: GigabitEthernet0/0/0/2
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - interface GigabitEthernet0/0/0/2
    - dot1q native vlan 100
    - no dot1q native vlan 100
"""

import re
import time

from copy import deepcopy

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network_common import remove_default_spec
from ansible.module_utils.iosxr import get_config, load_config
from ansible.module_utils.iosxr import iosxr_argument_spec, check_args


def search_obj_in_list(vlan_id, interfaces, lst):
    obj = list()
    for o in lst:
        for i in interfaces:
            if o['vlan_id'] == vlan_id and i in o['interfaces']:
                obj.append(o)
    return obj


def map_obj_to_commands(updates, module):
    commands = list()
    want, have = updates
    purge = module.params['purge']

    for w in want:
        vlan_id = w['vlan_id']
        interfaces = w['interfaces']
        state = w['state']

        obj_in_have = search_obj_in_list(vlan_id, interfaces, have)

        if state == 'absent':
            if obj_in_have:
                for obj in obj_in_have:
                    for i in obj['interfaces']:
                        commands.append('interface {}'.format(i))
                        commands.append('no dot1q native vlan {}'.format(vlan_id))

        elif state == 'present':
            if not obj_in_have:
                if w['interfaces'] and w['vlan_id']:
                    for i in w['interfaces']:
                        commands.append('interface {}'.format(i))
                        commands.append('dot1q native vlan {}'.format(vlan_id))

    if purge:
        for h in have:
            obj_in_want = search_obj_in_list(h['vlan_id'], h['interfaces'], want)
            if not obj_in_want:
                for i in h['interfaces']:
                    commands.append('interface {}'.format(i))
                    commands.append('no dot1q native vlan {}'.format(h['vlan_id']))

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
            'interfaces': module.params['interfaces'],
            'state': module.params['state']
        })

    return obj


def parse_vlan_id(config):
    for cfg in config:
        match = re.search(r'dot1q native vlan (\S+)', cfg, re.M)
        if match:
            return match.group(1)


def map_config_to_obj(module):
    output = get_config(module, flags=['interface'])
    data = output.strip().rstrip('!').split('!')
    if not data:
        return list()

    objs = list()
    for instance in data:
        intf_config = instance.strip().splitlines()
        if intf_config[0].startswith('interface'):
            interface = intf_config[0].strip().split()[1]
            obj = {}
            obj['interfaces'] = []

            if interface:
                obj['vlan_id'] = parse_vlan_id(intf_config)
                obj['interfaces'].append(interface)
                obj['state'] = 'present'
            objs.append(obj)

    return objs


def check_declarative_intent_params(want, module):
    if module.params['interfaces']:
        time.sleep(module.params['delay'])
        have = map_config_to_obj(module)

        want_interface = list()
        obj_interface = list()

        for w in want:
            for i in w['interfaces']:
                want_interface.append(i)

            obj_in_have = search_obj_in_list(w['vlan_id'], w['interfaces'], have)
            if obj_in_have:
                for obj in obj_in_have:
                    obj_interface.extend(obj['interfaces'])

        for w in want:
            for i in w['interfaces']:
                if (set(obj_interface) - set(want_interface)) != set([]):
                    module.fail_json(msg='Interface {0} not configured on vlan {1}'.format(i, w['vlan_id']))


def main():
    """ main entry point for module execution
    """
    element_spec = dict(
        vlan_id=dict(type='int', required=True),
        interfaces=dict(type='list', required=True),
        delay=dict(default=10, type='int'),
        state=dict(default='present',
                   choices=['present', 'absent'])
    )

    aggregate_spec = deepcopy(element_spec)

    # remove default in aggregate spec, to handle common arguments
    remove_default_spec(aggregate_spec)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec),
        purge=dict(default=False, type='bool')
    )

    argument_spec.update(element_spec)
    argument_spec.update(iosxr_argument_spec)

    required_one_of = [['vlan_id', 'aggregate']]
    mutually_exclusive = [['vlan_id', 'aggregate']]
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           required_one_of=required_one_of,
                           mutually_exclusive=mutually_exclusive)

    warnings = list()
    check_args(module, warnings)

    result = {'changed': False}

    want = map_params_to_obj(module)
    have = map_config_to_obj(module)
    commands = map_obj_to_commands((want, have), module)

    result['commands'] = commands
    result['warnings'] = warnings

    if commands:
        if not module.check_mode:
            load_config(module, commands, result['warnings'], commit=True)
        result['changed'] = True

    if result['changed']:
        check_declarative_intent_params(want, module)

    module.exit_json(**result)

if __name__ == '__main__':
    main()
