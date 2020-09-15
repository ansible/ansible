#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
#
# Copyright (C) 2017 Lenovo, Inc.
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
# Module to work on Link Aggregation with Lenovo Switches
# Lenovo Networking
#
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: cnos_linkagg
version_added: "2.8"
author: "Anil Kumar Muraleedharan (@auraleedhar)"
short_description: Manage link aggregation groups on Lenovo CNOS devices
description:
  - This module provides declarative management of link aggregation groups
    on Lenovo CNOS network devices.
notes:
  - Tested against CNOS 10.8.1
options:
  group:
    description:
      - Channel-group number for the port-channel
        Link aggregation group. Range 1-255.
  mode:
    description:
      - Mode of the link aggregation group.
    choices: ['active', 'on', 'passive']
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
    type: bool
    default: no
  provider:
    description:
      - B(Deprecated)
      - "Starting with Ansible 2.5 we recommend using C(connection: network_cli)."
      - For more information please see the L(CNOS Platform Options guide, ../network/user_guide/platform_cnos.html).
      - HORIZONTALLINE
      - A dict object containing connection details.
    version_added: "2.8"
    suboptions:
      host:
        description:
          - Specifies the DNS host name or address for connecting to the remote
            device over the specified transport.  The value of host is used as
            the destination address for the transport.
        required: true
      port:
        description:
          - Specifies the port to use when building the connection to the remote device.
        default: 22
      username:
        description:
          - Configures the username to use to authenticate the connection to
            the remote device.  This value is used to authenticate
            the SSH session. If the value is not specified in the task, the
            value of environment variable C(ANSIBLE_NET_USERNAME) will be used instead.
      password:
        description:
          - Specifies the password to use to authenticate the connection to
            the remote device.   This value is used to authenticate
            the SSH session. If the value is not specified in the task, the
            value of environment variable C(ANSIBLE_NET_PASSWORD) will be used instead.
      timeout:
        description:
          - Specifies the timeout in seconds for communicating with the network device
            for either connecting or sending commands.  If the timeout is
            exceeded before the operation is completed, the module will error.
        default: 10
      ssh_keyfile:
        description:
          - Specifies the SSH key to use to authenticate the connection to
            the remote device.   This value is the path to the
            key used to authenticate the SSH session. If the value is not specified
            in the task, the value of environment variable C(ANSIBLE_NET_SSH_KEYFILE)
            will be used instead.
      authorize:
        description:
          - Instructs the module to enter privileged mode on the remote device
            before sending any commands.  If not specified, the device will
            attempt to execute all commands in non-privileged mode. If the value
            is not specified in the task, the value of environment variable
            C(ANSIBLE_NET_AUTHORIZE) will be used instead.
        type: bool
        default: 'no'
      auth_pass:
        description:
          - Specifies the password to use if required to enter privileged mode
            on the remote device.  If I(authorize) is false, then this argument
            does nothing. If the value is not specified in the task, the value of
            environment variable C(ANSIBLE_NET_AUTH_PASS) will be used instead.
"""

EXAMPLES = """
- name: create link aggregation group
  cnos_linkagg:
    group: 10
    state: present

- name: delete link aggregation group
  cnos_linkagg:
    group: 10
    state: absent

- name: set link aggregation group to members
  cnos_linkagg:
    group: 200
    mode: active
    members:
      - Ethernet1/33
      - Ethernet1/44

- name: remove link aggregation group from GigabitEthernet0/0
  cnos_linkagg:
    group: 200
    mode: active
    members:
      - Ethernet1/33

- name: Create aggregate of linkagg definitions
  cnos_linkagg:
    aggregate:
      - { group: 3, mode: on, members: [Ethernet1/33] }
      - { group: 100, mode: passive, members: [Ethernet1/44] }
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always, except for the platforms that use Netconf transport to
    manage the device.
  type: list
  sample:
    - interface port-channel 30
    - interface Ethernet1/33
    - channel-group 30 mode on
    - no interface port-channel 30
"""

import re
from copy import deepcopy

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.config import CustomNetworkConfig
from ansible.module_utils.network.common.utils import remove_default_spec
from ansible.module_utils.network.cnos.cnos import get_config, load_config
from ansible.module_utils.network.cnos.cnos import cnos_argument_spec


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
                commands.append('no interface port-channel {0}'.format(group))

        elif state == 'present':
            cmd = ['interface port-channel {0}'.format(group),
                   'exit']
            if not obj_in_have:
                if not group:
                    module.fail_json(msg='group is a required option')
                commands.extend(cmd)

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
                            commands.append('no channel-group')

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

            obj.append(d)
    else:
        obj.append({
            'group': str(module.params['group']),
            'mode': module.params['mode'],
            'members': module.params['members'],
            'state': module.params['state']
        })

    return obj


def parse_mode(module, config, group, member):
    mode = None
    netcfg = CustomNetworkConfig(indent=1, contents=config)
    parents = ['interface {0}'.format(member)]
    body = netcfg.get_section(parents)

    match_int = re.findall(r'interface {0}\n'.format(member), body, re.M)
    if match_int:
        match = re.search(r'channel-group {0} mode (\S+)'.format(group),
                          body, re.M)
        if match:
            mode = match.group(1)

    return mode


def parse_members(module, config, group):
    members = []

    for line in config.strip().split('!'):
        l = line.strip()
        if l.startswith('interface'):
            match_group = re.findall(r'channel-group {0} mode'.format(group), l, re.M)
            if match_group:
                match = re.search(r'interface (\S+)', l, re.M)
                if match:
                    members.append(match.group(1))

    return members


def get_channel(module, config, group):
    match = re.findall(r'^interface (\S+)', config, re.M)

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
        l = line.strip()
        match = re.search(r'interface port-channel(\S+)', l, re.M)
        if match:
            obj = {}
            group = match.group(1)
            obj['group'] = group
            obj.update(get_channel(module, config, group))
            objs.append(obj)

    return objs


def main():
    """ main entry point for module execution
    """
    element_spec = dict(
        group=dict(type='int'),
        mode=dict(choices=['active', 'on', 'passive']),
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
    argument_spec.update(cnos_argument_spec)

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
