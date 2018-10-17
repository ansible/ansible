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
module: nxos_linkagg
extends_documentation_fragment: nxos
version_added: "2.5"
short_description: Manage link aggregation groups on Cisco NXOS devices.
description:
  - This module provides declarative management of link aggregation groups
    on Cisco NXOS devices.
author:
  - Trishna Guha (@trishnaguha)
notes:
  - Tested against NXOSv 7.0(3)I5(1).
  - C(state=absent) removes the portchannel config and interface if it
    already exists. If members to be removed are not explicitly
    passed, all existing members (if any), are removed.
  - Members must be a list.
  - LACP needs to be enabled first if active/passive modes are used.
options:
  group:
    description:
      - Channel-group number for the port-channel
        Link aggregation group.
    required: true
  mode:
    description:
      - Mode for the link aggregation group.
    choices: [ active, 'on', passive ]
    default: 'on'
  min_links:
    description:
      - Minimum number of ports required up
        before bringing up the link aggregation group.
  members:
    description:
      - List of interfaces that will be managed in the link aggregation group.
  force:
    description:
      - When true it forces link aggregation group members to match what
        is declared in the members param. This can be used to remove members.
    type: bool
    default: 'no'
  aggregate:
    description: List of link aggregation definitions.
  state:
    description:
      - State of the link aggregation group.
    default: present
    choices: ['present','absent']
  purge:
    description:
      - Purge links not defined in the I(aggregate) parameter.
    type: bool
    default: 'no'
"""

EXAMPLES = """
- name: create link aggregation group
  nxos_linkagg:
    group: 99
    state: present

- name: delete link aggregation group
  nxos_linkagg:
    group: 99
    state: absent

- name: set link aggregation group to members
  nxos_linkagg:
    group: 10
    min_links: 3
    mode: active
    members:
      - Ethernet1/2
      - Ethernet1/4

- name: remove link aggregation group from Ethernet1/2
  nxos_linkagg:
    group: 10
    min_links: 3
    mode: active
    members:
      - Ethernet1/4

- name: Create aggregate of linkagg definitions
  nxos_linkagg:
    aggregate:
      - { group: 3 }
      - { group: 100, min_links: 3 }

- name: Remove aggregate of linkagg definitions
  nxos_linkagg:
    aggregate:
      - { group: 3 }
      - { group: 100, min_links: 3 }
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always, except for the platforms that use Netconf transport to manage the device.
  type: list
  sample:
    - interface port-channel 30
    - lacp min-links 5
    - interface Ethernet2/1
    - channel-group 30 mode active
    - no interface port-channel 30
"""

import re
from copy import deepcopy

from ansible.module_utils.network.nxos.nxos import get_config, load_config, run_commands
from ansible.module_utils.network.nxos.nxos import get_capabilities, nxos_argument_spec
from ansible.module_utils.network.nxos.nxos import normalize_interface
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import remove_default_spec


def search_obj_in_list(group, lst):
    for o in lst:
        if o['group'] == group:
            return o


def map_obj_to_commands(updates, module):
    commands = list()
    want, have = updates
    purge = module.params['purge']
    force = module.params['force']

    for w in want:
        group = w['group']
        mode = w['mode']
        min_links = w['min_links']
        members = w.get('members') or []
        state = w['state']
        del w['state']

        obj_in_have = search_obj_in_list(group, have)

        if state == 'absent':
            if obj_in_have:
                members_to_remove = list(set(obj_in_have['members']) - set(members))
                if members_to_remove:
                    for m in members_to_remove:
                        commands.append('interface {0}'.format(m))
                        commands.append('no channel-group {0}'.format(obj_in_have['group']))
                        commands.append('exit')
                commands.append('no interface port-channel {0}'.format(group))

        elif state == 'present':
            if not obj_in_have:
                commands.append('interface port-channel {0}'.format(group))
                if min_links != 'None':
                    commands.append('lacp min-links {0}'.format(min_links))
                commands.append('exit')
                if members:
                    for m in members:
                        commands.append('interface {0}'.format(m))
                        if force:
                            commands.append('channel-group {0} force mode {1}'.format(group, mode))
                        else:
                            commands.append('channel-group {0} mode {1}'.format(group, mode))

            else:
                if members:
                    if not obj_in_have['members']:
                        for m in members:
                            commands.append('interface port-channel {0}'.format(group))
                            commands.append('exit')
                            commands.append('interface {0}'.format(m))
                            if force:
                                commands.append('channel-group {0} force mode {1}'.format(group, mode))
                            else:
                                commands.append('channel-group {0} mode {1}'.format(group, mode))

                    elif set(members) != set(obj_in_have['members']):
                        missing_members = list(set(members) - set(obj_in_have['members']))
                        for m in missing_members:
                            commands.append('interface port-channel {0}'.format(group))
                            commands.append('exit')
                            commands.append('interface {0}'.format(m))
                            if force:
                                commands.append('channel-group {0} force mode {1}'.format(group, mode))
                            else:
                                commands.append('channel-group {0} mode {1}'.format(group, mode))

                        superfluous_members = list(set(obj_in_have['members']) - set(members))
                        for m in superfluous_members:
                            commands.append('interface port-channel {0}'.format(group))
                            commands.append('exit')
                            commands.append('interface {0}'.format(m))
                            commands.append('no channel-group {0}'.format(group))
    if purge:
        for h in have:
            obj_in_want = search_obj_in_list(h['group'], want)
            if not obj_in_want:
                commands.append('no interface port-channel {0}'.format(h['group']))

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
            d['group'] = str(d['group'])
            d['min_links'] = str(d['min_links'])
            if d['members']:
                d['members'] = [normalize_interface(i) for i in d['members']]

            obj.append(d)
    else:
        members = None
        if module.params['members']:
            members = [normalize_interface(i) for i in module.params['members']]

        obj.append({
            'group': str(module.params['group']),
            'mode': module.params['mode'],
            'min_links': str(module.params['min_links']),
            'members': members,
            'state': module.params['state']
        })

    return obj


def parse_min_links(module, group):
    min_links = None

    flags = ['| section interface.port-channel{0}'.format(group)]
    config = get_config(module, flags=flags)
    match = re.search(r'lacp min-links (\S+)', config, re.M)
    if match:
        min_links = match.group(1)

    return min_links


def parse_mode(module, m):
    mode = None

    flags = ['| section interface.{0}'.format(m)]
    config = get_config(module, flags=flags)
    match = re.search(r'mode (\S+)', config, re.M)
    if match:
        mode = match.group(1)

    return mode


def get_members(channel):
    members = []
    if 'TABLE_member' in channel.keys():
        interfaces = channel['TABLE_member']['ROW_member']
    else:
        return list()

    if isinstance(interfaces, dict):
        members.append(normalize_interface(interfaces.get('port')))
    elif isinstance(interfaces, list):
        for i in interfaces:
            members.append(normalize_interface(i.get('port')))

    return members


def parse_members(output, group):
    channels = output['TABLE_channel']['ROW_channel']

    if isinstance(channels, list):
        for channel in channels:
            if channel['group'] == group:
                members = get_members(channel)
    elif isinstance(channels, dict):
        if channels['group'] == group:
            members = get_members(channels)
    else:
        return list()

    return members


def parse_channel_options(module, output, channel):
    obj = {}

    group = channel['group']
    obj['group'] = group
    obj['min-links'] = parse_min_links(module, group)
    members = parse_members(output, group)
    obj['members'] = members
    for m in members:
        obj['mode'] = parse_mode(module, m)

    return obj


def map_config_to_obj(module):
    objs = list()
    output = run_commands(module, ['show port-channel summary | json'])[0]
    if not output:
        return list()

    try:
        channels = output['TABLE_channel']['ROW_channel']
    except (TypeError, KeyError):
        return objs

    if channels:
        if isinstance(channels, list):
            for channel in channels:
                obj = parse_channel_options(module, output, channel)
                objs.append(obj)

        elif isinstance(channels, dict):
            obj = parse_channel_options(module, output, channels)
            objs.append(obj)

    return objs


def main():
    """ main entry point for module execution
    """
    element_spec = dict(
        group=dict(type='int'),
        mode=dict(required=False, choices=['on', 'active', 'passive'], default='on', type='str'),
        min_links=dict(required=False, default=None, type='int'),
        members=dict(required=False, default=None, type='list'),
        force=dict(required=False, default=False, type='bool'),
        state=dict(required=False, choices=['absent', 'present'], default='present')
    )

    aggregate_spec = deepcopy(element_spec)
    aggregate_spec['group'] = dict(required=True)

    # remove default in aggregate spec, to handle common arguments
    remove_default_spec(aggregate_spec)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec),
        purge=dict(default=False, type='bool')
    )

    argument_spec.update(element_spec)
    argument_spec.update(nxos_argument_spec)

    required_one_of = [['group', 'aggregate']]
    mutually_exclusive = [['group', 'aggregate']]
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

    module.exit_json(**result)

if __name__ == '__main__':
    main()
