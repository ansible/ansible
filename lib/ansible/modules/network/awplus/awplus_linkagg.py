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
module: awplus_linkagg
author: Cheng Yi Kok (@cyk19)
short_description: Manage link aggregation groups on AlliedWare Plus network devices
description:
  - This module provides declarative management of link aggregation groups
    on AlliedWare Plus network devices.
version_added: "2.10"
options:
  group:
    description:
      - Channel-group number for the port-channel
        Link aggregation group. Range 1-255.
  mode:
    description:
      - Mode of the link aggregation group.
    choices: ['active', 'passive']
  members:
    description:
      - List of members of the link aggregation group.
  aggregate:
    description: List of link aggregation definitions.
  state:
    description:
      - State of the link aggregation group.
    default: present
    choices: ['present', 'absent']
  purge:
    description:
      - Purge links not defined in the I(aggregate) parameter.
    default: no
    type: bool
"""

EXAMPLES = """
    - name: delete link aggregation group
      awplus_linkagg:
        group: 100
        state: absent

    - name: delete link aggregation group
      awplus_linkagg:
        group: 3
        state: absent

    - name: set link aggregation group to members
      awplus_linkagg:
        group: 200
        mode: active
        members:
          - port1.0.4
          - port1.0.3

    - name: remove link aggregation group from port1.0.3
      awplus_linkagg:
        group: 200
        mode: active
        members:
          - port1.0.4

    - name: delete link aggregation group
      awplus_linkagg:
        group: 200
        state: absent

    - name: Create aggregate of linkagg definitions
      awplus_linkagg:
        aggregate:
          - { group: 3, mode: active, members: [port1.0.4] }
          - { group: 100, mode: passive, members: [port1.0.3] }
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - ["interface port1.0.2",
       "no switchport access vlan",
       "switchport mode access",
       "switchport access vlan 2"]
"""

import re
from copy import deepcopy

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import remove_default_spec
from ansible.module_utils.network.awplus.awplus import get_config, load_config
from ansible.module_utils.network.awplus.awplus import awplus_argument_spec


def search_obj_in_list(group, lst):
    for o in lst:
        if o['group'] == group:
            return o


def map_obj_to_commands(updates, module):
    commands = list()
    want, have = updates
    purge = module.params['purge']

    for w in want:
        group = w['group']
        mode = w['mode']
        members = w.get('members') or []
        state = w['state']
        del w['state']

        obj_in_have = search_obj_in_list(group, have)

        if state == 'absent':
            if obj_in_have:
                for member in obj_in_have['members']:
                    commands.append('interface {0}'.format(member))
                    commands.append('no channel-group')

        elif state == 'present':
            if not obj_in_have:
                if not group:
                    module.fail_json(msg='group is a required option')

                if members:
                    for m in members:
                        commands.append('interface {0}'.format(m))
                        commands.append('channel-group {0} mode {1}'.format(group, mode))
                else:
                    module.fail_json(msg='member(s) is required to form a channel-group')

            else:
                if members:
                    if 'members' not in obj_in_have.keys():
                        for m in members:
                            commands.append('interface {0}'.format(m))
                            commands.append('channel-group {0} mode {1}'.format(group, mode))

                    elif set(members) != set(obj_in_have['members']):
                        missing_members = list(set(members) - set(obj_in_have['members']))
                        for m in missing_members:
                            commands.append('interface {0}'.format(m))
                            commands.append('channel-group {0} mode {1}'.format(group, mode))

                        superfluous_members = list(set(obj_in_have['members']) - set(members))
                        for m in superfluous_members:
                            commands.append('interface {0}'.format(m))
                            commands.append('no channel-group')

    if purge:
        for h in have:
            obj_in_want = search_obj_in_list(h['group'], want)
            if not obj_in_want:
                for member in h['members']:
                    commands.append('interface {0}'.format(member))
                    commands.append('no channel-group')

    return commands


def parse_members(module, config, group):
    members = []

    for line in config.strip().split('!'):
        line = line.strip()
        if line.startswith('interface'):
            match_group = re.findall(r'channel-group {0} mode'.format(group), line, re.M)
            if match_group:
                match = re.search(r'interface (\S+)', line, re.M)
                if match:
                    members.append(match.group(1))

    return members


def parse_mode(module, config, group, member):
    mode = None
    blocks = config.strip().split('!')

    for block in blocks:
        if block.startswith('\ninterface port{0}'.format(member)):
            match_group = re.findall(r'channel-group {0} mode (\S+)'.format(group), block, re.M)
            if len(match_group) == 1:
                mode = match_group[0]
    return mode


def get_channel(module, config, group):
    match = re.findall(r'^interface port(\S+)', config, re.M)

    if not match:
        return {}

    channel = {}
    for item in set(match):
        member = item
        channel['mode'] = parse_mode(module, config, group, member)
        channel['members'] = parse_members(module, config, group)

    return channel


def map_config_to_obj(module):
    objs = list()
    config = get_config(module)

    for line in config.split('\n'):
        line = line.strip()
        match = re.search(r'interface po(\d+)', line, re.M)
        if match:
            obj = {}
            group = match.group(1)
            obj['group'] = group
            obj.update(get_channel(module, config, group))
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

            d = item.copy()
            d['group'] = str(d['group'])

            obj.append(d)
    else:
        obj.append({
            'group': str(module.params['group']),
            'mode': module.params['mode'],
            'members': module.params['members'],
            'state': module.params['state']
        })

    return obj


def main():
    """ main entry point for module execution
    """
    element_spec = dict(
        group=dict(type='int'),
        mode=dict(choices=['active', 'passive']),
        members=dict(type='list'),
        state=dict(default='present',
                   choices=['present', 'absent'])
    )

    aggregate_spec = deepcopy(element_spec)
    aggregate_spec['group'] = dict(required=True)

    required_one_of = [['group', 'aggregate']]
    required_together = [['members', 'mode']]
    mutually_exclusive = [['group', 'aggregate']]

    # remove default in aggregate spec, to handle common arguments
    remove_default_spec(aggregate_spec)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec,
                       required_together=required_together),
        purge=dict(default=False, type='bool')
    )

    argument_spec.update(element_spec)
    argument_spec.update(awplus_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=required_one_of,
                           required_together=required_together,
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
