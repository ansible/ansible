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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: ios_static_route
version_added: "2.4"
author: "Ricardo Carrillo Cruz (@rcarrillocruz)"
short_description: Manage static IP routes on Cisco IOS network devices
description:
  - This module provides declarative management of static
    IP routes on Cisco IOS network devices.
notes:
  - Tested against IOS 15.6
requirements:
  - Python >= 3.3 or C(ipaddress) python package
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
  aggregate:
    description: List of static route definitions.
  state:
    description:
      - State of the static route configuration.
    default: present
    choices: ['present', 'absent']
extends_documentation_fragment: ios
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

- name: Add static route aggregates
  ios_static_route:
    aggregate:
      - { prefix: 172.16.32.0, mask: 255.255.255.0, next_hop: 10.0.0.8 }
      - { prefix: 172.16.33.0, mask: 255.255.255.0, next_hop: 10.0.0.8 }

- name: Add static route aggregates
  ios_static_route:
    aggregate:
      - { prefix: 172.16.32.0, mask: 255.255.255.0, next_hop: 10.0.0.8 }
      - { prefix: 172.16.33.0, mask: 255.255.255.0, next_hop: 10.0.0.8 }
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - ip route 192.168.2.0 255.255.255.0 10.0.0.1
"""
from copy import deepcopy
import re

from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import ConnectionError
from ansible.module_utils.network.common.utils import remove_default_spec
from ansible.module_utils.network.ios.ios import get_config, load_config, run_commands
from ansible.module_utils.network.ios.ios import ios_argument_spec, check_args

try:
    from ipaddress import ip_network
    HAS_IPADDRESS = True
except ImportError:
    HAS_IPADDRESS = False


def map_obj_to_commands(want, have, module):
    commands = list()

    for w in want:
        # Try to match an existing config with the desired config
        for h in have:
            for key in ['prefix', 'mask', 'next_hop']:
                # If any key doesn't match, skip to the next set
                if w[key] != h[key]:
                    break
            # If all keys match, don't execute final else
            else:
                break
        # If no matches found, clear `h`
        else:
            h = None

        prefix = w['prefix']
        mask = w['mask']
        next_hop = w['next_hop']
        admin_distance = w.get('admin_distance')
        if not admin_distance and h:
            w['admin_distance'] = admin_distance = h['admin_distance']
        state = w['state']
        del w['state']

        if state == 'absent' and w in have:
            commands.append('no ip route %s %s %s' % (prefix, mask, next_hop))
        elif state == 'present' and w not in have:
            if admin_distance:
                commands.append('ip route %s %s %s %s' % (prefix, mask, next_hop, admin_distance))
            else:
                commands.append('ip route %s %s %s' % (prefix, mask, next_hop))

    return commands


def map_config_to_obj(module):
    obj = []

    try:
        out = run_commands(module, 'show ip static route')[0]
        match = re.search(r'.*Static local RIB for default\s*(.*)$', out, re.DOTALL)

        if match and match.group(1):
            for r in match.group(1).splitlines():
                splitted_line = r.split()

                code = splitted_line[0]

                if code != 'M':
                    continue

                cidr = ip_network(to_text(splitted_line[1]))
                prefix = str(cidr.network_address)
                mask = str(cidr.netmask)
                next_hop = splitted_line[4]
                admin_distance = splitted_line[2][1]

                obj.append({
                    'prefix': prefix, 'mask': mask, 'next_hop': next_hop,
                    'admin_distance': admin_distance
                })

    except ConnectionError:
        out = get_config(module, flags='| include ip route')

        for line in out.splitlines():
            splitted_line = line.split()
            if len(splitted_line) not in (5, 6):
                continue

            prefix = splitted_line[2]
            mask = splitted_line[3]
            next_hop = splitted_line[4]
            if len(splitted_line) == 6:
                admin_distance = splitted_line[5]
            else:
                admin_distance = '1'

            obj.append({
                'prefix': prefix, 'mask': mask, 'next_hop': next_hop,
                'admin_distance': admin_distance
            })

    return obj


def map_params_to_obj(module, required_together=None):
    keys = ['prefix', 'mask', 'next_hop', 'admin_distance', 'state']
    obj = []

    aggregate = module.params.get('aggregate')
    if aggregate:
        for item in aggregate:
            route = item.copy()
            for key in keys:
                if route.get(key) is None:
                    route[key] = module.params.get(key)

            module._check_required_together(required_together, route)
            obj.append(route)
    else:
        module._check_required_together(required_together, module.params)
        obj.append({
            'prefix': module.params['prefix'].strip(),
            'mask': module.params['mask'].strip(),
            'next_hop': module.params['next_hop'].strip(),
            'admin_distance': module.params.get('admin_distance'),
            'state': module.params['state'],
        })

    for route in obj:
        if route['admin_distance']:
            route['admin_distance'] = str(route['admin_distance'])

    return obj


def main():
    """ main entry point for module execution
    """
    element_spec = dict(
        prefix=dict(type='str'),
        mask=dict(type='str'),
        next_hop=dict(type='str'),
        admin_distance=dict(type='int'),
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
    argument_spec.update(ios_argument_spec)

    required_one_of = [['aggregate', 'prefix']]
    required_together = [['prefix', 'mask', 'next_hop']]
    mutually_exclusive = [['aggregate', 'prefix']]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=required_one_of,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    if not HAS_IPADDRESS:
        module.fail_json(msg="ipaddress python package is required")

    warnings = list()
    check_args(module, warnings)

    result = {'changed': False}
    if warnings:
        result['warnings'] = warnings
    want = map_params_to_obj(module, required_together=required_together)
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
