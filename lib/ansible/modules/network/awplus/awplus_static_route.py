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
module: awplus_static_route
version_added: "2.10"
author:
    - Cheng Yi Kok (@cyk19)
    - Isaac Daly (@dalyIsaac)
short_description: Manage static IP routes on AlliedWare Plus network devices
description:
    - This module provides declarative management of static
        IP routes on AlliedWare Plus network devices.
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
    vrf:
        description:
            - VRF of the static route.
    interface:
        description:
            - Interface of the static route.
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
notes:
    - Check mode is supported.
"""

EXAMPLES = """
- name: configure static route
    awplus_static_route:
        prefix: 192.168.6.0
        mask: 25
        next_hop: 10.0.0.1

- name: remove configuration
    awplus_static_route:
        prefix: 192.168.6.0
        mask: 25
        next_hop: 10.0.0.1
        state: absent

- name: Add static route aggregates
    awplus_static_route:
        aggregate:
            - { prefix: 172.16.32.0, mask: 25, next_hop: 10.0.0.8 }
            - { prefix: 172.16.33.0, mask: 25, next_hop: 10.0.0.8 }

- name: Remove static route aggregates
    awplus_static_route:
        aggregate:
            - { prefix: 172.16.32.0, mask: 25, next_hop: 10.0.0.8 }
            - { prefix: 172.16.33.0, mask: 25, next_hop: 10.0.0.8 }
        state: absent

- name: configure static route in vrf orange
    awplus_static_route:
        prefix: 192.168.2.0
        mask: 25
        vrf: orange
        interface: vlan2
"""

RETURN = """
commands:
    description: The list of configuration mode commands to send to the device
    returned: always
    type: list
    sample:
        - ip route 192.168.2.0 255.255.255.0 10.0.0.1
"""

from ansible.module_utils.network.awplus.awplus import awplus_argument_spec
from ansible.module_utils.network.awplus.awplus import get_config, load_config
from ansible.module_utils.network.common.utils import remove_default_spec, validate_ip_address
from ansible.module_utils.basic import AnsibleModule
from re import findall
from copy import deepcopy


def map_obj_to_commands(want, have):
    commands = list()

    for w in want:
        state = w['state']
        del w['state']
        # Try to match an existing config with the desired config
        for h in have:
            # To delete admin_distance param from have if not it want before comparing both fields
            if not w.get('admin_distance') and h.get('admin_distance'):
                del h['admin_distance']
            diff = list(set(w.items()) ^ set(h.items()))
            if not diff:
                break
            # if route is present with name or name already starts with wanted name it will not change
            elif len(diff) == 2 and diff[0][0] == diff[1][0] == 'name' and (not w['name'] or h['name'].startswith(w['name'])):
                break
        # If no matches found, clear `h`
        else:
            h = None

        command = 'ip route'
        prefix = w['prefix']
        mask = w['mask']
        vrf = w.get('vrf')
        prefix_mask = prefix + '/' + mask

        if vrf:
            command = ' '.join((command, 'vrf', vrf, prefix_mask))
        else:
            command = ' '.join((command, prefix_mask))

        for key in ['next_hop', 'interface', 'admin_distance']:
            if w.get(key):
                command = ' '.join((command, w.get(key)))

        if state == 'absent' and h:
            commands.append('no %s' % command)
        elif state == 'present' and not h:
            commands.append(command)

    return commands


def map_config_to_obj(module):
    obj = []
    route = {}
    out = get_config(module, flags='ip route')

    for line in out.splitlines():
        # Split by whitespace but do not split quotes, needed for name parameter
        splitted_line = findall(r'[^"\s]\S*|".+?"', line)

        if len(splitted_line) <= 1:
            continue

        if splitted_line[2] == 'vrf':
            route = {'vrf': splitted_line[3]}
            del splitted_line[:4]  # Removes the words ip route vrf vrf_name
        else:
            route = {}
            del splitted_line[:2]  # Removes the words ip route

        prefix_mask = splitted_line[0]
        prefix_mask_list = prefix_mask.split('/')
        prefix = prefix_mask_list[0]
        mask = prefix_mask_list[1]
        route.update({'prefix': prefix, 'mask': mask, 'admin_distance': '1'})

        for word in splitted_line[1:]:
            if validate_ip_address(word):
                route.update(next_hop=word)
            elif word.isdigit():
                route.update(admin_distance=word)
            else:
                route.update(interface=word)

        obj.append(route)

    return obj


def map_params_to_obj(module, required_together=None):
    keys = ['prefix', 'mask', 'state', 'next_hop',
            'vrf', 'interface', 'admin_distance']
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
        vrf=dict(type='str'),
        interface=dict(type='str'),
        admin_distance=dict(type='str'),
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
    argument_spec.update(awplus_argument_spec)

    required_one_of = [['aggregate', 'prefix']]
    required_together = [['prefix', 'mask']]
    mutually_exclusive = [['aggregate', 'prefix']]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=required_one_of,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    warnings = list()

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
