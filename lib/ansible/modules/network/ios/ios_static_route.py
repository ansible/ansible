#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
#
# This file is part of Ansible by Red Hat
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'core'}


DOCUMENTATION = """
---
module: ios_static_route
version_added: "2.4"
author: "Ricardo Carrillo Cruz (@rcarrillocruz)"
short_description: Manage static IP routes on Cisco IOS network devices
description:
  - This module provides declarative management of static
    IP routes on Cisco IOS network devices.
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
  admin_distance:
    description:
      - Admin distance of the static route.
    default: 1
  aggregate:
    description: List of static route definitions
  purge:
    description:
      - Purge static routes not defined in the aggregates parameter.
    default: no
  state:
    description:
      - State of the static route configuration.
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: configure static route
  ios_static_route:
    prefix: 192.168.2.0
    mask: 255.255.255.0
    next_hop: 10.0.0.1

- name: remove configuration
  ios_static_route:
    prefix: 192.168.2.0
    mask: 255.255.255.0
    next_hop: 10.0.0.1
    state: absent

- name: configure aggregates of static routes
  ios_static_route:
    aggregate:
      - { prefix: 192.168.2.0, mask 255.255.255.0, next_hop: 10.0.0.1 }
      - { prefix: 192.168.3.0, mask 255.255.255.0, next_hop: 10.0.2.1 }
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - ip route 192.168.2.0 255.255.255.0 10.0.0.1
"""

from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import exec_command
from ansible.module_utils.ios import load_config, run_commands
from ansible.module_utils.ios import ios_argument_spec, check_args
from ipaddress import ip_network
import re


def map_obj_to_commands(updates, module):
    commands = list()
    want, have = updates

    for w in want:
        prefix = w['prefix']
        mask = w['mask']
        next_hop = w['next_hop']
        admin_distance = w['admin_distance']
        state = w['state']
        del w['state']

        if state == 'absent' and w in have:
            commands.append('no ip route %s %s %s' % (prefix, mask, next_hop))
        elif state == 'present' and w not in have:
            commands.append('ip route %s %s %s %s' % (prefix, mask, next_hop,
                                                      admin_distance))

    return commands


def map_config_to_obj(module):
    obj = []

    rc, out, err = exec_command(module, 'show ip static route')
    match = re.search(r'.*Static local RIB for default\s*(.*)$', out, re.DOTALL)

    if match and match.group(1):
        for r in match.group(1).splitlines():
            splitted_line = r.split()

            cidr = ip_network(to_text(splitted_line[1]))
            prefix = str(cidr.network_address)
            mask = str(cidr.netmask)
            next_hop = splitted_line[4]
            admin_distance = splitted_line[2][1]

            obj.append({'prefix': prefix, 'mask': mask,
                        'next_hop': next_hop,
                        'admin_distance': admin_distance})

    return obj


def map_params_to_obj(module):
    obj = []

    if 'aggregate' in module.params and module.params['aggregate']:
        for c in module.params['aggregate']:
            d = c.copy()

            if 'state' not in d:
                d['state'] = module.params['state']
            if 'admin_distance' not in d:
                d['admin_distance'] = str(module.params['admin_distance'])

            obj.append(d)
    else:
        prefix = module.params['prefix'].strip()
        mask = module.params['mask'].strip()
        next_hop = module.params['next_hop'].strip()
        admin_distance = str(module.params['admin_distance'])
        state = module.params['state']

        obj.append({
            'prefix': prefix,
            'mask': mask,
            'next_hop': next_hop,
            'admin_distance': admin_distance,
            'state': state
        })

    return obj


def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        prefix=dict(type='str'),
        mask=dict(type='str'),
        next_hop=dict(type='str'),
        admin_distance=dict(default=1, type='int'),
        aggregate=dict(type='list'),
        purge=dict(type='bool'),
        state=dict(default='present', choices=['present', 'absent'])
    )

    argument_spec.update(ios_argument_spec)
    required_one_of = [['aggregate', 'prefix']]
    required_together = [['prefix', 'mask', 'next_hop']]
    mutually_exclusive = [['aggregate', 'prefix']]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=required_one_of,
                           required_together=required_together,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

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
