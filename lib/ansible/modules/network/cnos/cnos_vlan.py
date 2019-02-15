#!/usr/bin/python
# -*- coding: utf-8 -*-

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
# Module to send VLAN commands to Lenovo Switches
# Overloading aspect of vlan creation in a range is pending
# Lenovo Networking


from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: cnos_vlan
version_added: "2.3"
author: "Anil Kumar Mureleedharan(@amuraleedhar)"
short_description: Manage VLANs on CNOS network devices
description:
  - This module provides declarative management of VLANs
    on Lenovo CNOS network devices.
notes:
  - Tested against CNOS 10.8.1
options:
  name:
    description:
      - Name of the VLAN.
    version_added: "2.8"
  vlan_id:
    description:
      - ID of the VLAN. Range 1-4094.
    required: true
    version_added: "2.8"
  interfaces:
    description:
      - List of interfaces that should be associated to the VLAN.
    required: true
    version_added: "2.8"
  associated_interfaces:
    description:
      - This is a intent option and checks the operational state of the for
        given vlan C(name) for associated interfaces. If the value in the
        C(associated_interfaces) does not match with the operational state of
        vlan interfaces on device it will result in failure.
    version_added: "2.8"
  delay:
    description:
      - Delay the play should wait to check for declarative intent params
        values.
    default: 10
    version_added: "2.8"
  aggregate:
    description: List of VLANs definitions.
    version_added: "2.8"
  purge:
    description:
      - Purge VLANs not defined in the I(aggregate) parameter.
    default: no
    type: bool
    version_added: "2.8"
  state:
    description:
      - State of the VLAN configuration.
    default: present
    version_added: "2.8"
    choices: ['present', 'absent', 'active', 'suspend']
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
- name: Create vlan
  cnos_vlan:
    vlan_id: 100
    name: test-vlan
    state: present

- name: Add interfaces to VLAN
  cnos_vlan:
    vlan_id: 100
    interfaces:
      - Ethernet1/33
      - Ethernet1/44

- name: Check if interfaces is assigned to VLAN
  cnos_vlan:
    vlan_id: 100
    associated_interfaces:
      - Ethernet1/33
      - Ethernet1/44

- name: Delete vlan
  cnos_vlan:
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
from ansible.module_utils.network.cnos.cnos import load_config, run_commands
from ansible.module_utils.network.cnos.cnos import debugOutput, check_args
from ansible.module_utils.network.cnos.cnos import cnos_argument_spec
from ansible.module_utils._text import to_text


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
                            commands.append('no switchport access vlan')
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
            # 'associated_interfaces': module.params['associated_interfaces'],
            'state': module.params['state']
        })

    return obj


def parse_to_logical_rows(out):
    relevant_data = False
    cur_row = []
    for line in out.splitlines():
        if not line:
            """Skip empty lines."""
            continue
        if '0' < line[0] <= '9':
            """Line starting with a number."""
            if len(cur_row) > 0:
                yield cur_row
                cur_row = []  # Reset it to hold a next chunk
            relevant_data = True
        if relevant_data:
            data = line.strip().split('(')
            cur_row.append(data[0])
    yield cur_row


def parse_to_obj(logical_rows):
    first_row = logical_rows[0]
    rest_rows = logical_rows[1:]
    vlan_data = first_row.split()
    obj = {}
    obj['vlan_id'] = vlan_data[0]
    obj['name'] = vlan_data[1]
    obj['state'] = vlan_data[2]
    obj['interfaces'] = rest_rows
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
    argument_spec.update(cnos_argument_spec)

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
