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
module: iosxr_vrf
version_added: "2.5"
author: "Trishna Guha (@trishnaguha)"
short_description: Manage VRFs on Cisco IOS XR devices
description:
  - This module provides declarative management of VRFs
    on Cisco IOS XR network devices.
notes:
  - Tested against IOS XR 6.1.2
options:
  name:
    description:
      - Name of the VRF.
    required: true
  interfaces:
    description:
      - Identifies the set of interfaces that
        should be configured in the VRF.  Interfaces must be routed
        interfaces in order to be placed into a VRF.
        You must remove IPv4/IPv6 addresses from an interface prior to
        assigning, removing, or changing an interface's VRF. If this is
        not done in advance, any attempt to change the VRF on an IP
        interface is rejected.
  aggregate:
    description: List of VRFs definitions
  purge:
    description:
      - Purge VRFs not defined in the I(aggregate) parameter.
    default: no
  state:
    description:
      - State of the VRF configuration.
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: Create vrf
  iosxr_vrf:
    name: test
    state: present

- name: Remove ipv4 address from interface
  iosxr_config:
    lines:
      - no ipv4 address 172.31.0.73/32
    parents: interface GigabitEthernet0/0/0/4

- name: Assing vrf to interface
  iosxr_vrf:
    name: test
    interfaces:
      - GigabitEthernet0/0/0/4

- name: configure vrfs using aggregate
  iosxr_vrf:
    aggregate:
      - { name: test-vrf1 }
      - { name: test-vrf2 }

- name: Delete vrfs using aggregate
  iosxr_vrf:
    aggregate:
      - { name: test-vrf1 }
      - { name: test-vrf2 }
    state: absent

- name: Delete VRF
  iosxr_vrf:
    name: test
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - vrf test
    - address-family ipv4 unicast
    - address-family ipv6 unicast
    - interface GigabitEthernet0/0/0/4
    - vrf test
"""

import re
import time

from copy import deepcopy

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network_common import remove_default_spec
from ansible.module_utils.iosxr import get_config, load_config, run_commands
from ansible.module_utils.iosxr import iosxr_argument_spec, check_args


def search_obj_in_list(name, lst):
    for o in lst:
        if o['name'] == name:
            return o


def map_obj_to_commands(updates, module):
    commands = list()
    want, have = updates
    purge = module.params['purge']

    for w in want:
        name = w['name']
        interfaces = w['interfaces']
        state = w['state']
        del w['state']

        obj_in_have = search_obj_in_list(name, have)
        vrf_cmd = ['vrf {}'.format(name),
                   'address-family ipv4 unicast', 'exit',
                   'address-family ipv6 unicast', 'exit']

        if state == 'absent':
            if obj_in_have:
                commands.append('no vrf {}'.format(name))

        elif state == 'present':
            if not obj_in_have:
                commands.extend(vrf_cmd)

                if interfaces:
                    for i in interfaces:
                        commands.append('interface {}'.format(i))
                        commands.append('vrf {}'.format(name))

            else:
                if interfaces:
                    if not obj_in_have['interfaces']:
                        for i in interfaces:
                            commands.extend(vrf_cmd)
                            commands.append('interface {}'.format(i))
                            commands.append('vrf {}'.format(name))

                    elif set(interfaces) != set(obj_in_have['interfaces']):
                        missing_interfaces = list(set(interfaces) - set(obj_in_have['interfaces']))
                        for i in missing_interfaces:
                            commands.extend(vrf_cmd)
                            commands.append('interface {}'.format(i))
                            commands.append('vrf {}'.format(name))

                        superfluous_interfaces = list(set(obj_in_have['interfaces']) - set(interfaces))
                        for i in superfluous_interfaces:
                            commands.extend(vrf_cmd)
                            commands.append('interface {}'.format(i))
                            commands.append('no vrf {}'.format(name))

    if purge:
        for h in have:
            obj_in_want = search_obj_in_list(h['name'], want)
            if not obj_in_want:
                commands.append('no vrf {}'.format(h['name']))

    return commands


def map_params_to_obj(module):
    obj = list()
    aggregate = module.params.get('aggregate')
    if aggregate:
        for item in aggregate:
            for key in item:
                if item.get(key) is None:
                    item[key] = module.params[key]

            d = item.copy()
            interfaces = d['interfaces']
            if interfaces is None:
                interfaces = []
            d['interfaces'] = interfaces

            obj.append(d)
    else:
        interfaces = module.params['interfaces']
        if interfaces is None:
            interfaces = []

        obj.append({
            'name': module.params['name'],
            'state': module.params['state'],
            'interfaces': interfaces
        })

    return obj


def parse_interface(cfg, name):
    interfaces = list()
    vrf_cfg = 'vrf {}'.format(name)
    int_cfg = cfg.strip().split('interface')

    for i in int_cfg:
        if vrf_cfg in i:
            interface = i.strip('\n').split()[0]
            interfaces.append(interface)

    return interfaces


def map_config_to_obj(module):
    int_cfg = get_config(module, flags=['interface'])
    output = run_commands(module, ['show vrf all'])
    lines = output[0].strip().splitlines()[1:]

    if not lines:
        return list()

    objs = list()

    for l in lines:
        obj = {}
        splitted_line = re.split(r'\s{2,}', l.strip())
        obj['name'] = splitted_line[0]
        obj['interfaces'] = parse_interface(int_cfg, obj['name'])
        objs.append(obj)

    return objs


def check_declarative_intent_params(want, module):
    if module.params['interfaces']:
        time.sleep(module.params['delay'])
        have = map_config_to_obj(module)

        for w in want:
            for i in w['interfaces']:
                obj_in_have = search_obj_in_list(w['name'], have)

                if obj_in_have and 'interfaces' in obj_in_have and i not in obj_in_have['interfaces']:
                    module.fail_json(msg="Interface %s not configured on vrf %s" % (i, w['name']))


def main():
    """ main entry point for module execution
    """
    element_spec = dict(
        name=dict(),
        interfaces=dict(type='list'),
        delay=dict(default=10, type='int'),
        state=dict(default='present', choices=['present', 'absent'])
    )

    aggregate_spec = deepcopy(element_spec)
    aggregate_spec['name'] = dict(required=True)

    # remove default in aggregate spec, to handle common arguments
    remove_default_spec(aggregate_spec)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec),
        purge=dict(default=False, type='bool')
    )

    argument_spec.update(element_spec)
    argument_spec.update(iosxr_argument_spec)

    required_one_of = [['name', 'aggregate']]
    mutually_exclusive = [['name', 'aggregate']]
    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=required_one_of,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    result = {'changed': False}
    result['warnings'] = warnings

    want = map_params_to_obj(module)
    have = map_config_to_obj(module)

    commands = map_obj_to_commands((want, have), module)
    result['commands'] = commands

    if commands:
        if not module.check_mode:
            load_config(module, commands, result['warnings'], commit=True)
        result['changed'] = True

    if result['changed']:
        check_declarative_intent_params(want, module)

    module.exit_json(**result)

if __name__ == '__main__':
    main()
