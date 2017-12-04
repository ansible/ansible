#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: ios_static_route
version_added: "2.4"
author:
- Ricardo Carrillo Cruz (@rcarrillocruz)
short_description: Manage static IP routes on Cisco IOS network devices
description:
  - This module provides declarative management of static
    IP routes on Cisco IOS network devices.
notes:
  - Tested against IOS 15.6
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
    description: List of static route definitions.
  state:
    description:
      - State of the static route configuration.
    choices: [ absent, present ]
    default: present
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

from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import exec_command
from ansible.module_utils.network.common.utils import remove_default_spec
from ansible.module_utils.network.ios.ios import check_args, ios_argument_spec, load_config, run_commands
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

            code = splitted_line[0]

            if code != 'M':
                continue

            cidr = ip_network(to_text(splitted_line[1]))
            prefix = str(cidr.network_address)
            mask = str(cidr.netmask)
            next_hop = splitted_line[4]
            admin_distance = splitted_line[2][1]

            obj.append({'prefix': prefix, 'mask': mask,
                        'next_hop': next_hop,
                        'admin_distance': admin_distance})

    return obj


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
            d['admin_distance'] = str(module.params['admin_distance'])

            obj.append(d)
    else:
        obj.append({
            'prefix': module.params['prefix'].strip(),
            'mask': module.params['mask'].strip(),
            'next_hop': module.params['next_hop'].strip(),
            'admin_distance': str(module.params['admin_distance']),
            'state': module.params['state']
        })

    return obj


def main():
    """ main entry point for module execution
    """
    element_spec = dict(
        prefix=dict(type='str'),
        mask=dict(type='str'),
        next_hop=dict(type='str'),
        admin_distance=dict(type='int', default=1),
        state=dict(type='str', default='present', choices=['absent', 'present'])
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
                           required_together=required_together,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    result = {'changed': False}
    if warnings:
        result['warnings'] = warnings
    want = map_params_to_obj(module, required_together=required_together)
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
