#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
#
# Copyright (C) 2019 Lenovo, Inc.
# (c) 2019, Ansible by Red Hat, inc
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
module: cnos_l3_interface
version_added: "2.8"
author: "Anil Kumar Muraleedharan (@amuraleedhar)"
short_description: Manage Layer-3 interfaces on Lenovo CNOS network devices.
description:
  - This module provides declarative management of Layer-3 interfaces
    on CNOS network devices.
notes:
  - Tested against CNOS 10.8.1
options:
  name:
    description:
      - Name of the Layer-3 interface to be configured eg. Ethernet1/2
  ipv4:
    description:
      - IPv4 address to be set for the Layer-3 interface mentioned in I(name)
        option. The address format is <ipv4 address>/<mask>, the mask is number
        in range 0-32 eg. 10.241.107.1/24
  ipv6:
    description:
      - IPv6 address to be set for the Layer-3 interface mentioned in I(name)
        option. The address format is <ipv6 address>/<mask>, the mask is number
        in range 0-128 eg. fd5d:12c9:2201:1::1/64
  aggregate:
    description:
      - List of Layer-3 interfaces definitions. Each of the entry in aggregate
        list should define name of interface C(name) and a optional C(ipv4) or
        C(ipv6) address.
  state:
    description:
      - State of the Layer-3 interface configuration. It indicates if the
        configuration should be present or absent on remote device.
    default: present
    choices: ['present', 'absent']
  provider:
    description:
      - B(Deprecated)
      - "Starting with Ansible 2.5 we recommend using
         C(connection: network_cli)."
      - For more information please see the
        L(CNOS Platform Options guide, ../network/user_guide/platform_cnos.html).
      - HORIZONTALLINE
      - A dict object containing connection details.
    suboptions:
      host:
        description:
          - Specifies the DNS host name or address for connecting to the remote
            device over the specified transport.  The value of host is used as
            the destination address for the transport.
        required: true
      port:
        description:
          - Specifies the port to use when building the connection to the
            remote device.
        default: 22
      username:
        description:
          - Configures the username to use to authenticate the connection to
            the remote device.  This value is used to authenticate
            the SSH session. If the value is not specified in the task, the
            value of environment variable C(ANSIBLE_NET_USERNAME) will be used
            instead.
      password:
        description:
          - Specifies the password to use to authenticate the connection to
            the remote device.   This value is used to authenticate
            the SSH session. If the value is not specified in the task, the
            value of environment variable C(ANSIBLE_NET_PASSWORD) will be used
            instead.
      timeout:
        description:
          - Specifies the timeout in seconds for communicating with the network
            device for either connecting or sending commands.  If the timeout
            is exceeded before the operation is completed, the module will
            error.
        default: 10
      ssh_keyfile:
        description:
          - Specifies the SSH key to use to authenticate the connection to
            the remote device.   This value is the path to the
            key used to authenticate the SSH session. If the value is not
            specified in the task, the value of environment variable
            C(ANSIBLE_NET_SSH_KEYFILE)will be used instead.
      authorize:
        description:
          - Instructs the module to enter privileged mode on the remote device
            before sending any commands.  If not specified, the device will
            attempt to execute all commands in non-privileged mode. If the
            value is not specified in the task, the value of environment
            variable C(ANSIBLE_NET_AUTHORIZE) will be used instead.
        type: bool
        default: 'no'
      auth_pass:
        description:
          - Specifies the password to use if required to enter privileged mode
            on the remote device.  If I(authorize) is false, then this argument
            does nothing. If the value is not specified in the task, the value
            of environment variable C(ANSIBLE_NET_AUTH_PASS) will be used
            instead.
"""

EXAMPLES = """
- name: Remove Ethernet1/33 IPv4 and IPv6 address
  cnos_l3_interface:
    name: Ethernet1/33
    state: absent

- name: Set Ethernet1/33 IPv4 address
  cnos_l3_interface:
    name: Ethernet1/33
    ipv4: 10.241.107.1/24

- name: Set Ethernet1/33 IPv6 address
  cnos_l3_interface:
    name: Ethernet1/33
    ipv6: "fd5d:12c9:2201:1::1/64"

- name: Set Ethernet1/33 in dhcp
  cnos_l3_interface:
    name: Ethernet1/33
    ipv4: dhcp
    ipv6: dhcp

- name: Set interface Vlan1 (SVI) IPv4 address
  cnos_l3_interface:
    name: Vlan1
    ipv4: 192.168.0.5/24

- name: Set IP addresses on aggregate
  cnos_l3_interface:
    aggregate:
      - { name: Ethernet1/33, ipv4: 10.241.107.1/24 }
      - { name: Ethernet1/44, ipv4: 10.240.106.1/24,
          ipv6: "fd5d:12c9:2201:1::1/64" }

- name: Remove IP addresses on aggregate
  cnos_l3_interface:
    aggregate:
      - { name: Ethernet1/33, ipv4: 10.241.107.1/24 }
      - { name: Ethernet1/44, ipv4: 10.240.106.1/24,
          ipv6: "fd5d:12c9:2201:1::1/64" }
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always, except for the platforms that use Netconf transport to
   manage the device.
  type: list
  sample:
    - interface Ethernet1/33
    - ip address 10.241.107.1 255.255.255.0
    - ipv6 address fd5d:12c9:2201:1::1/64
"""
import re

from copy import deepcopy

from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cnos.cnos import get_config, load_config
from ansible.module_utils.network.cnos.cnos import cnos_argument_spec
from ansible.module_utils.network.cnos.cnos import run_commands
from ansible.module_utils.network.common.config import NetworkConfig
from ansible.module_utils.network.common.utils import remove_default_spec
from ansible.module_utils.network.common.utils import is_netmask, is_masklen
from ansible.module_utils.network.common.utils import to_netmask, to_masklen


def validate_ipv4(value, module):
    if value:
        address = value.split('/')
        if len(address) != 2:
            module.fail_json(
                msg='address format is <ipv4 address>/<mask>,got invalid format %s' % value)
        if not is_masklen(address[1]):
            module.fail_json(
                msg='invalid value for mask: %s, mask should be in range 0-32' % address[1])


def validate_ipv6(value, module):
    if value:
        address = value.split('/')
        if len(address) != 2:
            module.fail_json(
                msg='address format is <ipv6 address>/<mask>, got invalid format %s' % value)
        else:
            if not 0 <= int(address[1]) <= 128:
                module.fail_json(
                    msg='invalid value for mask: %s, mask should be in range 0-128' % address[1])


def validate_param_values(module, obj, param=None):
    if param is None:
        param = module.params
    for key in obj:
        # validate the param value (if validator func exists)
        validator = globals().get('validate_%s' % key)
        if callable(validator):
            validator(param.get(key), module)


def parse_config_argument(configobj, name, arg=None):
    cfg = configobj['interface %s' % name]
    cfg = '\n'.join(cfg.children)

    values = []
    matches = re.finditer(r'%s (.+)$' % arg, cfg, re.M)
    for match in matches:
        match_str = match.group(1).strip()
        if arg == 'ipv6 address':
            values.append(match_str)
        else:
            values = match_str
            break

    return values or None


def search_obj_in_list(name, lst):
    for o in lst:
        if o['name'].lower() == name.lower():
            return o

    return None


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
    for w in want:
        name = w['name']
        ipv4 = w['ipv4']
        ipv6 = w['ipv6']
        state = w['state']

        interface = 'interface ' + name
        commands.append(interface)

        obj_in_have = search_obj_in_list(name, have)
        if state == 'absent' and obj_in_have:
            if obj_in_have['ipv4']:
                if ipv4:
                    address = ipv4.split('/')
                    if len(address) == 2:
                        ipv4 = '{0} {1}'.format(
                            address[0], to_netmask(address[1]))
                    commands.append('no ip address %s' % ipv4)
                else:
                    commands.append('no ip address')
            if obj_in_have['ipv6']:
                if ipv6:
                    commands.append('no ipv6 address %s' % ipv6)
                else:
                    commands.append('no ipv6 address')
                    if 'dhcp' in obj_in_have['ipv6']:
                        commands.append('no ipv6 address dhcp')

        elif state == 'present':
            if ipv4:
                if obj_in_have is None or obj_in_have.get('ipv4') is None or ipv4 != obj_in_have['ipv4']:
                    address = ipv4.split('/')
                    if len(address) == 2:
                        ipv4 = '{0} {1}'.format(
                            address[0], to_netmask(address[1]))
                    commands.append('ip address %s' % ipv4)

            if ipv6:
                if obj_in_have is None or obj_in_have.get('ipv6') is None or ipv6.lower() not in [addr.lower() for addr in obj_in_have['ipv6']]:
                    commands.append('ipv6 address %s' % ipv6)
        if commands[-1] == interface:
            commands.pop(-1)

    return commands


def map_config_to_obj(module):
    config = get_config(module)
    configobj = NetworkConfig(indent=1, contents=config)

    match = re.findall(r'^interface (\S+)', config, re.M)
    if not match:
        return list()

    instances = list()

    for item in set(match):
        ipv4 = parse_config_argument(configobj, item, 'ip address')
        if ipv4:
            # eg. 192.168.2.10 255.255.255.0 -> 192.168.2.10/24
            address = ipv4.strip().split(' ')
            if len(address) == 2 and is_netmask(address[1]):
                ipv4 = '{0}/{1}'.format(address[0], to_text(to_masklen(address[1])))

        obj = {
            'name': item,
            'ipv4': ipv4,
            'ipv6': parse_config_argument(configobj, item, 'ipv6 address'),
            'state': 'present'
        }
        instances.append(obj)

    return instances


def map_params_to_obj(module):
    obj = []

    aggregate = module.params.get('aggregate')
    if aggregate:
        for item in aggregate:
            for key in item:
                if item.get(key) is None:
                    item[key] = module.params[key]

            validate_param_values(module, item, item)
            obj.append(item.copy())
    else:
        obj.append({
            'name': module.params['name'],
            'ipv4': module.params['ipv4'],
            'ipv6': module.params['ipv6'],
            'state': module.params['state']
        })

        validate_param_values(module, obj)

    return obj


def main():
    """ main entry point for module execution
    """
    element_spec = dict(
        name=dict(),
        ipv4=dict(),
        ipv6=dict(),
        state=dict(default='present',
                   choices=['present', 'absent'])
    )

    aggregate_spec = deepcopy(element_spec)
    aggregate_spec['name'] = dict(required=True)

    # remove default in aggregate spec, to handle common arguments
    remove_default_spec(aggregate_spec)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec),
    )

    argument_spec.update(element_spec)
    argument_spec.update(cnos_argument_spec)

    required_one_of = [['name', 'aggregate']]
    mutually_exclusive = [['name', 'aggregate']]
    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=required_one_of,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    warnings = list()

    result = {'changed': False}

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
            resp = load_config(module, commands)
            if resp is not None:
                warnings.extend((out for out in resp if out))

        result['changed'] = True

    if warnings:
        result['warnings'] = warnings
        if 'overlaps with address configured on' in warnings[0]:
            result['failed'] = True
            result['msg'] = warnings[0]
        if 'Cannot set overlapping address' in warnings[0]:
            result['failed'] = True
            result['msg'] = warnings[0]

    module.exit_json(**result)


if __name__ == '__main__':
    main()
