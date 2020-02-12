#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2020, Allied Telesis Ltd.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: awplus_system
version_added: "2.10"
author:
    - Jeremy Toth (@jtsource)
    - Isaac Daly (@dalyIsaac)
short_description: Manage the rip router attributes on AlliedWare Plus devices
description:
    - This module provides declarative management of rip router attributes
      on awplus devices. It provides an option to configure host system
      parameters or remove those parameters from the device active
      configuration.
options:
    network:
        description:
            - Used to specify networks or VLANs, to which rip routing
                information will be sent and received.
    passive_interface:
        description:
            - Command for blocking RIP broadcasts on the interface.
    state:
        description:
            - State of the configuration
                values in the device's current active configuration.    When set
                to I(present), the values should be configured in the device active
                configuration and when set to I(absent) the values should not be
                in the device active configuration
        default: present
        choices: ['present', 'absent']
notes:
    - Check mode is supported.
"""

EXAMPLES = """
---
- hosts: all
    connection: network_cli
    tasks:
     - name: testing out rip module
         awplus_rip:
                network: 1.3.3.4
                passive_int: yellow vlan10
                state: present
"""

RETURN = """
commands:
    description: Show the command sent.
    returned: always
    type: list
    sample: ['router rip', 'no network 1.3.3.4', 'network 195.46.3.4',]
"""

from ansible.module_utils.network.awplus.awplus import awplus_argument_spec
from ansible.module_utils.network.awplus.awplus import get_config, load_config
from ansible.module_utils.basic import AnsibleModule
import re


def diff_list(want, have):
    adds = [w for w in want if w not in have]
    removes = [h for h in have if h not in want]
    return (adds, removes)


def same_list(want, have):
    return [w for w in want if w in have]


def map_obj_to_commands(want, have, module):

    commands = list()
    commands.extend(['router rip'])

    state = module.params['state']

    if state == 'absent':
        if want['network']:
            removes = same_list(want['network'], have['network'])
        else:
            removes = []
        for item in removes:
            if item[1]:
                commands.extend(['address-family ipv4 vrf %s' % item[1],
                                 'no network %s' % item[0]])
            else:
                commands.extend(['no network %s' % item[0]])

        if want['passive-int']:
            removes = same_list(want['passive-int'], have['passive-int'])
        else:
            removes = []
        for item in removes:
            if item[1]:
                commands.extend(['address-family ipv4 vrf %s' % item[1],
                                 'no passive-interface %s' % item[0]])
            else:
                commands.extend(['no passive-interface %s' % item[0]])

    if state == 'present':
        adds, removes = diff_list(want['network'], have['network'])
        for network in adds:
            if network[1]:
                commands.extend(['address-family ipv4 vrf %s' % network[1],
                                 'network %s' % network[0]])
            else:
                commands.extend(['network %s' % network[0]])
        for network in removes:
            if network[1]:
                commands.extend(['address-family ipv4 vrf %s' % network[1],
                                 'no network %s' % network[0]])
            else:
                commands.extend(['no network %s' % network[0]])

        adds, removes = diff_list(want['passive-int'], have['passive-int'])
        for int in adds:
            if int[1]:
                commands.extend(['address-family ipv4 vrf %s' % int[1],
                                 'passive-interface %s' % int[0]])
            else:
                commands.extend(['passive-interface %s' % int[0]])
        for int in removes:
            if int[1]:
                commands.extend(['address-family ipv4 vrf %s' % int[1],
                                 'no passive-interface %s' % int[0]])
            else:
                commands.extend(['no passive-interface %s' % int[0]])

    return commands


def parse_network(config):
    networks = []
    blocks = config.split('!')
    for block in blocks:
        vrf = re.search(r'address-family ipv4 vrf (\S+)', block, re.M)
        if vrf:
            matches = re.findall(r'network (\S+)/', block, re.M)
            for match in matches:
                networks.append([match, vrf.group(1)])
        else:
            matches = re.findall(r'network (\S+)/', block, re.M)
            for match in matches:
                networks.append([match, None])
    return networks


def parse_passive_int(config):
    interfaces = []
    blocks = config.split('!')
    for block in blocks:
        vrf = re.search(r'address-family ipv4 vrf (\S+)', block, re.M)
        if vrf:
            matches = re.findall(r'passive-interface (\S+)', block, re.M)
            for match in matches:
                interfaces.append([match, vrf.group(1)])
    return interfaces


def map_config_to_obj(module):

    config = get_config(module, flags=[' router rip'])

    obj = {
        'network': parse_network(config),
        'passive-int': parse_passive_int(config),
    }

    return obj


def map_params_to_obj(module):

    obj = {
        'network': list(),
        'passive-int': list(),
        'state': module.params['state']
    }

    if module.params['network']:
        for network in module.params['network']:
            network = network.split()
            if len(network) == 1:
                obj['network'].append([network[0], None])
            else:
                obj['network'].append([network[1], network[0]])

    if module.params['passive_int']:
        for int in module.params['passive_int']:
            int = int.split()
            if len(int) == 1:
                obj['passive-int'].append([int[0], None])
            else:
                obj['passive-int'].append([int[1], int[0]])

    return obj


def main():

    argument_spec = dict(
        network=dict(type='list'),
        passive_int=dict(type='list'),
        state=dict(choices=['absent', 'present'], default='present')
    )

    argument_spec.update(awplus_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    result = {'changed': False}

    warnings = list()
    if warnings:
        result['warnings'] = warnings

    want = map_params_to_obj(module)
    have = map_config_to_obj(module)

    commands = map_obj_to_commands(want, have, module)
    result['commands'] = commands

    if commands:
        if not module.check_mode:
            load_config(module, commands)
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
