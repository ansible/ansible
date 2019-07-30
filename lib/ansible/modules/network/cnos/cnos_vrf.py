#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
#
# Copyright (C) 2019 Lenovo.
# (c) 2017, Ansible by Red Hat, inc
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
# Module to work on management of local users on Lenovo CNOS Switches
# Lenovo Networking
#
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: cnos_vrf
version_added: "2.8"
author: "Anil Kumar Muraleedharan (@amuraleedhar)"
short_description: Manage VRFs on Lenovo CNOS network devices
description:
  - This module provides declarative management of VRFs
    on Lenovo CNOS network devices.
notes:
  - Tested against CNOS 10.9.1
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
      - Identifies the set of interfaces that
        should be configured in the VRF. Interfaces must be routed
        interfaces in order to be placed into a VRF. The name of interface
        should be in expanded format and not abbreviated.
  associated_interfaces:
    description:
      - This is a intent option and checks the operational state of the for
        given vrf C(name) for associated interfaces. If the value in the
        C(associated_interfaces) does not match with the operational state of
        vrf interfaces on device it will result in failure.
  aggregate:
    description: List of VRFs contexts
  purge:
    description:
      - Purge VRFs not defined in the I(aggregate) parameter.
    default: no
    type: bool
  delay:
    description:
      - Time in seconds to wait before checking for the operational state on
        remote device. This wait is applicable for operational state arguments.
    default: 10
  state:
    description:
      - State of the VRF configuration.
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: Create vrf
  cnos_vrf:
    name: test
    rd: 1:200
    interfaces:
      - Ethernet1/33
    state: present

- name: Delete VRFs
  cnos_vrf:
    name: test
    state: absent

- name: Create aggregate of VRFs with purge
  cnos_vrf:
    aggregate:
      - { name: test4, rd: "1:204" }
      - { name: test5, rd: "1:205" }
    state: present
    purge: yes

- name: Delete aggregate of VRFs
  cnos_vrf:
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
    - vrf context test
    - rd 1:100
    - interface Ethernet1/44
    - vrf member test
"""
import re
import time

from copy import deepcopy

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import remove_default_spec
from ansible.module_utils.network.cnos.cnos import load_config, run_commands
from ansible.module_utils.network.cnos.cnos import cnos_argument_spec, check_args


def search_obj_in_list(name, lst):
    for o in lst:
        if o['name'] == name:
            return o


def get_interface_type(interface):
    intf_type = 'unknown'
    if interface.upper()[:2] in ('ET', 'GI', 'FA', 'TE', 'FO', 'HU', 'TWE'):
        intf_type = 'ethernet'
    elif interface.upper().startswith('VL'):
        intf_type = 'svi'
    elif interface.upper().startswith('LO'):
        intf_type = 'loopback'
    elif interface.upper()[:2] in ('MG', 'MA'):
        intf_type = 'management'
    elif interface.upper().startswith('PO'):
        intf_type = 'portchannel'
    elif interface.upper().startswith('NV'):
        intf_type = 'nve'

    return intf_type


def is_switchport(name, module):
    intf_type = get_interface_type(name)

    if intf_type in ('ethernet', 'portchannel'):
        config = run_commands(module,
                              ['show interface {0} switchport'.format(name)])[0]
        match = re.search(r'Switchport              : enabled', config)
        return bool(match)
    return False


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

        if name == 'default':
            module.fail_json(msg='VRF context default is reserved')
        elif len(name) > 63:
            module.fail_json(msg='VRF name is too long')
        if state == 'absent':
            if name == 'management':
                module.fail_json(msg='Management VRF context cannot be deleted')
            if obj_in_have:
                commands.append('no vrf context %s' % name)
        elif state == 'present':
            if not obj_in_have:
                commands.append('vrf context %s' % name)

                if rd is not None:
                    commands.append('rd %s' % rd)

                if w['interfaces']:
                    for i in w['interfaces']:
                        commands.append('interface %s' % i)
                        commands.append('vrf member %s' % w['name'])
            else:
                if w['rd'] is not None and w['rd'] != obj_in_have['rd']:
                    commands.append('vrf context %s' % w['name'])
                    commands.append('rd %s' % w['rd'])

                if w['interfaces']:
                    if not obj_in_have['interfaces']:
                        for i in w['interfaces']:
                            commands.append('interface %s' % i)
                            commands.append('vrf member %s' % w['name'])
                    elif set(w['interfaces']) != obj_in_have['interfaces']:
                        missing_interfaces = list(set(w['interfaces']) - set(obj_in_have['interfaces']))

                        for i in missing_interfaces:
                            commands.append('interface %s' % i)
                            commands.append('vrf member %s' % w['name'])

    if purge:
        for h in have:
            obj_in_want = search_obj_in_list(h['name'], want)
            if not obj_in_want:
                commands.append('no vrf context %s' % h['name'])

    return commands


def map_config_to_obj(module):
    objs = []
    output = run_commands(module, {'command': 'show vrf'})
    if output is not None:
        vrfText = output[0].strip()
        vrfList = vrfText.split('VRF')
        for vrfItem in vrfList:
            if 'FIB ID' in vrfItem:
                obj = dict()
                list_of_words = vrfItem.split()
                vrfName = list_of_words[0]
                obj['name'] = vrfName[:-1]
                obj['rd'] = list_of_words[list_of_words.index('RD') + 1]
                start = False
                obj['interfaces'] = []
                for intName in list_of_words:
                    if 'Interfaces' in intName:
                        start = True
                    if start is True:
                        if '!' not in intName and 'Interfaces' not in intName:
                            obj['interfaces'].append(intName.strip().lower())
                objs.append(obj)
    else:
        module.fail_json(msg='Could not fetch VRF details from device')
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
                item['interfaces'] = [intf.replace(" ", "").lower() for intf in item.get('interfaces') if intf]

            if item.get('associated_interfaces'):
                item['associated_interfaces'] = [intf.replace(" ", "").lower() for intf in item.get('associated_interfaces') if intf]

            obj.append(item.copy())
    else:
        obj.append({
            'name': module.params['name'],
            'state': module.params['state'],
            'rd': module.params['rd'],
            'interfaces': [intf.replace(" ", "").lower() for intf in module.params['interfaces']] if module.params['interfaces'] else [],
            'associated_interfaces': [intf.replace(" ", "").lower() for intf in
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
        associated_interfaces=dict(type='list'),
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
    for w in want:
        name = w['name']
        name = name.lower()
        if is_switchport(name, module):
            module.fail_json(msg='Ensure interface is configured to be a L3'
                             '\nport first before using this module. You can use'
                             '\nthe cnos_interface module for this.')
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
