#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['deprecated'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: eos_linkagg
version_added: "2.5"
author: "Trishna Guha (@trishnaguha)"
short_description: Manage link aggregation groups on Arista EOS network devices
description:
  - This module provides declarative management of link aggregation groups
    on Arista EOS network devices.
deprecated:
  removed_in: "2.13"
  alternative: eos_lag_interfaces
  why: Updated modules released with more functionality
notes:
  - Tested against EOS 4.15
options:
  group:
    description:
      - Channel-group number for the port-channel
        Link aggregation group. Range 1-2000.
  mode:
    description:
      - Mode of the link aggregation group.
    choices: ['active', 'on', 'passive']
  members:
    description:
      - List of members of the link aggregation group.
  min_links:
    description:
      - Minimum number of ports required up
        before bringing up the link aggregation group.
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
extends_documentation_fragment: eos
"""

EXAMPLES = """
- name: create link aggregation group
  eos_linkagg:
    group: 10
    state: present

- name: delete link aggregation group
  eos_linkagg:
    group: 10
    state: absent

- name: set link aggregation group to members
  eos_linkagg:
    group: 200
    min_links: 3
    mode: active
    members:
      - Ethernet0
      - Ethernet1

- name: remove link aggregation group from Ethernet0
  eos_linkagg:
    group: 200
    min_links: 3
    mode: active
    members:
      - Ethernet1

- name: Create aggregate of linkagg definitions
  eos_linkagg:
    aggregate:
      - { group: 3, mode: on, members: [Ethernet1] }
      - { group: 100, mode: passive, min_links: 3, members: [Ethernet2] }

- name: Remove aggregate of linkagg definitions
  eos_linkagg:
    aggregate:
      - { group: 3, mode: on, members: [Ethernet1] }
      - { group: 100, mode: passive, min_links: 3, members: [Ethernet2] }
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always, except for the platforms that use Netconf transport to manage the device.
  type: list
  sample:
    - interface port-channel 30
    - port-channel min-links 5
    - interface Ethernet3
    - channel-group 30 mode on
    - no interface port-channel 30
"""

import re
from copy import deepcopy

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import remove_default_spec
from ansible.module_utils.network.eos.eos import get_config, load_config
from ansible.module_utils.network.eos.eos import eos_argument_spec


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
        min_links = w['min_links']
        members = w.get('members') or []
        state = w['state']
        del w['state']

        obj_in_have = search_obj_in_list(group, have)

        if state == 'absent':
            if obj_in_have:
                commands.append('no interface port-channel {0}'.format(group))

        elif state == 'present':
            cmd = ['interface port-channel {0}'.format(group),
                   'end']
            if not obj_in_have:
                if not group:
                    module.fail_json(msg='group is a required option')
                commands.extend(cmd)

                if min_links != 'None':
                    commands.append('port-channel min-links {0}'.format(min_links))

                if members:
                    for m in members:
                        commands.append('interface {0}'.format(m))
                        commands.append('channel-group {0} mode {1}'.format(group, mode))

            else:
                if members:
                    if 'members' not in obj_in_have.keys():
                        for m in members:
                            commands.extend(cmd)
                            commands.append('interface {0}'.format(m))
                            commands.append('channel-group {0} mode {1}'.format(group, mode))

                    elif set(members) != set(obj_in_have['members']):
                        missing_members = list(set(members) - set(obj_in_have['members']))
                        for m in missing_members:
                            commands.extend(cmd)
                            commands.append('interface {0}'.format(m))
                            commands.append('channel-group {0} mode {1}'.format(group, mode))

                        superfluous_members = list(set(obj_in_have['members']) - set(members))
                        for m in superfluous_members:
                            commands.extend(cmd)
                            commands.append('interface {0}'.format(m))
                            commands.append('no channel-group {0}'.format(group))

    if purge:
        for h in have:
            obj_in_want = search_obj_in_list(h['group'], want)
            if not obj_in_want:
                commands.append('no interface port-channel {0}'.format(h['group']))

    return commands


def map_params_to_obj(module, required_together=None):
    obj = []

    aggregate = module.params.get('aggregate')
    if aggregate:
        for item in aggregate:
            for key in item:
                if item.get(key) is None:
                    item[key] = module.params[key]

            module._check_required_together(required_together, item)
            d = item.copy()
            d['group'] = str(d['group'])
            d['min_links'] = str(d['min_links'])

            obj.append(d)
    else:
        obj.append({
            'group': str(module.params['group']),
            'mode': module.params['mode'],
            'min_links': str(module.params['min_links']),
            'members': module.params['members'],
            'state': module.params['state']
        })

    return obj


def parse_mode(group, member, config):
    mode = None

    for line in config.strip().split('!'):
        match_int = re.findall(r'interface {0}\\b'.format(member), line, re.M)
        if match_int:
            match = re.search(r'channel-group {0} mode (\S+)'.format(group), line, re.M)
            if match:
                mode = match.group(1)

    return mode


def parse_members(group, config):
    members = []

    for line in config.strip().split('!'):
        match_group = re.findall(r'channel-group {0} mode'.format(group), line, re.M)
        if match_group:
            match = re.search(r'interface (\S+)', line, re.M)
            if match:
                members.append(match.group(1))

    return members


def get_channel(group, module):
    channel = {}
    config = get_config(module, flags=['| section channel-group'])

    for line in config.split('\n'):
        l = line.strip()
        match = re.search(r'interface (\S+)', l, re.M)

        if match:
            member = match.group(1)
            channel['mode'] = parse_mode(group, member, config)
            channel['members'] = parse_members(group, config)

    return channel


def parse_min_links(group, config):
    min_links = ''

    for line in config.strip().split('!'):
        match_pc = re.findall(r'interface Port-Channel{0}\\b'.format(group), line, re.M)
        if match_pc:
            match = re.search(r'port-channel min-links (\S+)', line, re.M)
            if match:
                min_links = match.group(1)

    return min_links


def map_config_to_obj(module):
    objs = list()
    config = get_config(module, flags=['| section port-channel'])

    for line in config.split('\n'):
        l = line.strip()
        match = re.search(r'interface Port-Channel(\S+)', l, re.M)
        if match:
            obj = {}
            group = match.group(1)
            obj['group'] = group
            obj['min_links'] = parse_min_links(group, config)
            obj.update(get_channel(group, module))
            objs.append(obj)

    return objs


def main():
    """ main entry point for module execution
    """
    element_spec = dict(
        group=dict(type='int'),
        mode=dict(choices=['active', 'on', 'passive']),
        min_links=dict(type='int'),
        members=dict(type='list'),
        state=dict(default='present',
                   choices=['present', 'absent'])
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
    argument_spec.update(eos_argument_spec)

    required_one_of = [['group', 'aggregate']]
    required_together = [['members', 'mode']]
    mutually_exclusive = [['group', 'aggregate']]
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
        commit = not module.check_mode
        response = load_config(module, commands, commit=commit)
        if response.get('diff') and module._diff:
            result['diff'] = {'prepared': response.get('diff')}
        result['session_name'] = response.get('session')
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
