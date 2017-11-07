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
module: iosxr_static_route
version_added: "2.5"
author: "Trishna Guha (@trishnaguha)"
short_description: Manage static IP routes on Cisco IOS XR network devices
description:
  - This module provides declarative management of static
    IP routes on Cisco IOS XR network devices.
notes:
  - Tested against IOS XR 6.1.2
options:
  address:
    description:
      - Network address with prefix of the static route.
    required: true
    aliases: ['prefix']
  next_hop:
    description:
      - Next hop IP of the static route.
    required: true
  admin_distance:
    description:
      - Admin distance of the static route.
  aggregate:
    description: List of static route definitions
  state:
    description:
      - State of the static route configuration.
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: configure static route
  iosxr_static_route:
    address: 10.0.2.0/24
    next_hop: 10.8.38.1
    admin_distance: 2
- name: delete static route
  iosxr_static_route:
    address: 10.0.2.0/24
    next_hop: 10.8.38.1
    state: absent
- name: configure static routes using aggregate
  iosxr_static_route:
    aggregate:
      - { address: 10.0.1.0/24, next_hop: 10.8.38.1 }
      - { address: 10.0.3.0/24, next_hop: 10.8.38.1 }
- name: Delete static route using aggregate
  iosxr_static_route:
    aggregate:
      - { address: 10.0.1.0/24, next_hop: 10.8.38.1 }
      - { address: 10.0.3.0/24, next_hop: 10.8.38.1 }
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - router static
    - address-family ipv4 unicast
    - 10.0.2.0/24 10.8.38.1 2
    - no 10.0.2.0/24 10.8.38.1
"""
from copy import deepcopy

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network_common import remove_default_spec
from ansible.module_utils.network_common import validate_ip_address, validate_prefix
from ansible.module_utils.iosxr import get_config, load_config
from ansible.module_utils.iosxr import iosxr_argument_spec, check_args


def map_obj_to_commands(updates, module):
    commands = list()
    want, have = updates

    for w in want:
        address = w['address']
        next_hop = w['next_hop']
        admin_distance = w['admin_distance']
        state = w['state']
        del w['state']

        if state == 'absent' and w in have:
            commands.append('router static')
            commands.append('address-family ipv4 unicast')
            commands.append('no {0} {1}'.format(address, next_hop))

        elif state == 'present' and w not in have:
            commands.append('router static')
            commands.append('address-family ipv4 unicast')
            if not admin_distance:
                commands.append('{0} {1}'.format(address, next_hop))
            else:
                commands.append('{0} {1} {2}'.format(address, next_hop, admin_distance))

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
            d['admin_distance'] = str(module.params['admin_distance'])

            obj.append(d)
    else:
        obj.append({
            'address': module.params['address'].strip(),
            'next_hop': module.params['next_hop'].strip(),
            'admin_distance': str(module.params['admin_distance']),
            'state': module.params['state']
        })

    return obj


def map_config_to_obj(module):
    config = get_config(module, flags=['router static'])
    data = config.strip().rstrip('!').split('!')[0].strip()
    if not data:
        return list()

    objs = list()
    routes = data.split('\n')[2:]
    for r in routes:
        obj = {}
        route = r.split()
        obj['address'] = route[0]
        obj['next_hop'] = route[1]
        if len(route) > 2:
            obj['admin_distance'] = route[2]

        objs.append(obj)

    return objs


def main():
    """ main entry point for module execution
    """

    element_spec = dict(
        address=dict(type='str', aliases=['prefix']),
        next_hop=dict(type='str'),
        admin_distance=dict(type='int'),
        state=dict(default='present', choices=['present', 'absent'])
    )

    aggregate_spec = deepcopy(element_spec)
    aggregate_spec['address'] = dict(required=True)

    # remove default in aggregate spec, to handle common arguments
    remove_default_spec(aggregate_spec)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec),
    )

    argument_spec.update(element_spec)
    argument_spec.update(iosxr_argument_spec)

    required_one_of = [['aggregate', 'address']]
    required_together = [['address', 'next_hop']]
    mutually_exclusive = [['aggregate', 'address']]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=required_one_of,
                           required_together=required_together,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    address = module.params['address']
    prefix = address.split('/')[-1]
    warnings = list()
    check_args(module, warnings)

    if '/' not in address or not validate_ip_address(address.split('/')[0]):
        module.fail_json(msg='{} is not a valid IP address'.format(address))

    if not validate_prefix(prefix):
        module.fail_json(msg='Length of prefix should be between 0 and 32 bits')

    result = {'changed': False}
    result['warnings'] = warnings

    want = map_params_to_obj(module)
    have = map_config_to_obj(module)

    commands = map_obj_to_commands((want, have), module)
    result['commands'] = commands

    if commands:
        if not module.check_mode:
            load_config(module, commands, result['warnings'], commit=True)
        result['changed'] = True

    module.exit_json(**result)

if __name__ == '__main__':
    main()
