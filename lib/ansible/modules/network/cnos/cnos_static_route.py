#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
#
# Copyright (C) 2019 Lenovo, Inc.
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
module: cnos_static_route
version_added: "2.8"
author: "Anil Kumar Muraleedharan (@amuraleedhar)"
short_description: Manage static IP routes on Lenovo CNOS network devices
description:
  - This module provides declarative management of static
    IP routes on Lenovo CNOS network devices.
notes:
  - Tested against CNOS 10.10.1
options:
  prefix:
    description:
      - Network prefix of the static route.
  mask:
    description:
      - Network prefix mask of the static route.
  next_hop:
    description:
      - Next hop IP of the static route.
  interface:
    description:
      - Interface of the static route.
  description:
    description:
      - Name of the static route
    aliases: ['description']
  admin_distance:
    description:
      - Admin distance of the static route.
    default: 1
  tag:
    description:
      - Set tag of the static route.
  aggregate:
    description: List of static route definitions.
  state:
    description:
      - State of the static route configuration.
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: configure static route
  cnos_static_route:
    prefix: 10.241.107.0
    mask: 255.255.255.0
    next_hop: 10.241.106.1

- name: configure ultimate route with name and tag
  cnos_static_route:
    prefix: 10.241.107.0
    mask: 255.255.255.0
    interface: Ethernet1/13
    description: hello world
    tag: 100

- name: remove configuration
  cnos_static_route:
    prefix: 10.241.107.0
    mask: 255.255.255.0
    next_hop: 10.241.106.0
    state: absent

- name: Add static route aggregates
  cnos_static_route:
    aggregate:
      - { prefix: 10.241.107.0, mask: 255.255.255.0, next_hop: 10.241.105.0 }
      - { prefix: 10.241.106.0, mask: 255.255.255.0, next_hop: 10.241.104.0 }

- name: Remove static route aggregates
  cnos_static_route:
    aggregate:
      - { prefix: 10.241.107.0, mask: 255.255.255.0, next_hop: 10.241.105.0 }
      - { prefix: 10.241.106.0, mask: 255.255.255.0, next_hop: 10.241.104.0 }
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - ip route 10.241.107.0 255.255.255.0 10.241.106.0
"""
from copy import deepcopy
from re import findall
from ansible.module_utils.compat import ipaddress
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import validate_ip_address
from ansible.module_utils.network.common.utils import remove_default_spec
from ansible.module_utils.network.cnos.cnos import get_config, load_config
from ansible.module_utils.network.cnos.cnos import check_args
from ansible.module_utils.network.cnos.cnos import cnos_argument_spec


def map_obj_to_commands(want, have):
    commands = list()

    for w in want:
        state = w['state']
        command = 'ip route'
        prefix = w['prefix']
        mask = w['mask']
        command = ' '.join((command, prefix, mask))

        for key in ['interface', 'next_hop', 'admin_distance', 'tag',
                    'description']:
            if w.get(key):
                if key == 'description' and len(w.get(key).split()) > 1:
                    # name with multiple words needs to be quoted
                    command = ' '.join((command, key, '"%s"' % w.get(key)))
                elif key in ('description', 'tag'):
                    command = ' '.join((command, key, w.get(key)))
                else:
                    command = ' '.join((command, w.get(key)))

        if state == 'absent':
            commands.append('no %s' % command)
        elif state == 'present':
            commands.append(command)

    return commands


def map_config_to_obj(module):
    obj = []

    out = get_config(module, flags='| include ip route')
    for line in out.splitlines():
        # Split by whitespace but do not split quotes, needed for description
        splitted_line = findall(r'[^"\s]\S*|".+?"', line)
        route = {}
        prefix_with_mask = splitted_line[2]
        prefix = None
        mask = None
        iface = None
        nhop = None
        if validate_ip_address(prefix_with_mask) is True:
            my_net = ipaddress.ip_network(prefix_with_mask)
            prefix = str(my_net.network_address)
            mask = str(my_net.netmask)
            route.update({'prefix': prefix,
                          'mask': mask, 'admin_distance': '1'})
        if splitted_line[3] is not None:
            if validate_ip_address(splitted_line[3]) is False:
                iface = str(splitted_line[3])
                route.update(interface=iface)
                if validate_ip_address(splitted_line[4]) is True:
                    nhop = str(splitted_line[4])
                    route.update(next_hop=nhop)
                    if splitted_line[5].isdigit():
                        route.update(admin_distance=str(splitted_line[5]))
                elif splitted_line[4].isdigit():
                    route.update(admin_distance=str(splitted_line[4]))
                else:
                    if splitted_line[6] is not None and splitted_line[6].isdigit():
                        route.update(admin_distance=str(splitted_line[6]))
            else:
                nhop = str(splitted_line[3])
                route.update(next_hop=nhop)
                if splitted_line[4].isdigit():
                    route.update(admin_distance=str(splitted_line[4]))

        index = 0
        for word in splitted_line:
            if word in ('tag', 'description'):
                route.update(word=splitted_line[index + 1])
            index = index + 1
        obj.append(route)

    return obj


def map_params_to_obj(module, required_together=None):
    keys = ['prefix', 'mask', 'state', 'next_hop', 'interface', 'description',
            'admin_distance', 'tag']
    obj = []

    aggregate = module.params.get('aggregate')
    if aggregate:
        for item in aggregate:
            route = item.copy()
            for key in keys:
                if route.get(key) is None:
                    route[key] = module.params.get(key)

            route = dict((k, v) for k, v in route.items() if v is not None)
            module._check_required_together(required_together, route)
            obj.append(route)
    else:
        module._check_required_together(required_together, module.params)
        route = dict()
        for key in keys:
            if module.params.get(key) is not None:
                route[key] = module.params.get(key)
        obj.append(route)

    return obj


def main():
    """ main entry point for module execution
    """
    element_spec = dict(
        prefix=dict(type='str'),
        mask=dict(type='str'),
        next_hop=dict(type='str'),
        interface=dict(type='str'),
        description=dict(type='str'),
        admin_distance=dict(type='str', default='1'),
        tag=dict(tag='str'),
        state=dict(default='present', choices=['present', 'absent'])
    )

    aggregate_spec = deepcopy(element_spec)
    aggregate_spec['prefix'] = dict(required=True)

    # remove default in aggregate spec, to handle common arguments
    remove_default_spec(aggregate_spec)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec),
    )
    argument_spec.update(element_spec)

    required_one_of = [['aggregate', 'prefix']]
    required_together = [['prefix', 'mask']]
    mutually_exclusive = [['aggregate', 'prefix']]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=required_one_of,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    result = {'changed': False}
    if warnings:
        result['warnings'] = warnings
    want = map_params_to_obj(module, required_together=required_together)
    have = map_config_to_obj(module)

    commands = map_obj_to_commands(want, have)
    result['commands'] = commands
    if commands:
        if not module.check_mode:
            load_config(module, commands)

        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
