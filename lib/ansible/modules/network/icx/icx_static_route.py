#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: icx_static_route
version_added: "2.9"
author: "Ruckus Wireless (@Commscope)"
short_description: Manage static IP routes on Ruckus ICX 7000 series switches
description:
  - This module provides declarative management of static
    IP routes on Ruckus ICX network devices.
notes:
  - Tested against ICX 10.1.
  - For information on using ICX platform, see L(the ICX OS Platform Options guide,../network/user_guide/platform_icx.html).
options:
  prefix:
    description:
      - Network prefix of the static route.
    type: str
  mask:
    description:
      - Network prefix mask of the static route.
    type: str
  next_hop:
    description:
      - Next hop IP of the static route.
    type: str
  admin_distance:
    description:
      - Admin distance of the static route. Range is 1 to 255.
    type: int
  aggregate:
    description: List of static route definitions.
    type: list
    suboptions:
      prefix:
        description:
          - Network prefix of the static route.
        type: str
      mask:
        description:
          - Network prefix mask of the static route.
        type: str
      next_hop:
        description:
          - Next hop IP of the static route.
        type: str
      admin_distance:
        description:
          - Admin distance of the static route. Range is 1 to 255.
        type: int
      state:
        description:
          - State of the static route configuration.
        type: str
        choices: ['present', 'absent']
      check_running_config:
        description:
          - Check running configuration. This can be set as environment variable.
           Module will use environment variable value(default:True), unless it is overridden, by specifying it as module parameter.
        type: bool
  purge:
    description:
      - Purge routes not defined in the I(aggregate) parameter.
    default: no
    type: bool
  state:
    description:
      - State of the static route configuration.
    type: str
    default: present
    choices: ['present', 'absent']
  check_running_config:
    description:
      - Check running configuration. This can be set as environment variable.
       Module will use environment variable value(default:True), unless it is overridden, by specifying it as module parameter.
    type: bool
    default: yes
"""

EXAMPLES = """
- name: configure static route
  icx_static_route:
    prefix: 192.168.2.0/24
    next_hop: 10.0.0.1

- name: remove configuration
  icx_static_route:
    prefix: 192.168.2.0
    mask: 255.255.255.0
    next_hop: 10.0.0.1
    state: absent

- name: Add static route aggregates
  icx_static_route:
    aggregate:
      - { prefix: 172.16.32.0, mask: 255.255.255.0, next_hop: 10.0.0.8 }
      - { prefix: 172.16.33.0, mask: 255.255.255.0, next_hop: 10.0.0.8 }

- name: remove static route aggregates
  icx_static_route:
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
from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.connection import ConnectionError
from ansible.module_utils.network.common.utils import remove_default_spec
from ansible.module_utils.network.icx.icx import get_config, load_config

try:
    from ipaddress import ip_network
    HAS_IPADDRESS = True
except ImportError:
    HAS_IPADDRESS = False


def map_obj_to_commands(want, have, module):
    commands = list()
    purge = module.params['purge']
    for w in want:
        for h in have:
            for key in ['prefix', 'mask', 'next_hop']:
                if w[key] != h[key]:
                    break
            else:
                break
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

        if state == 'absent' and have == []:
            commands.append('no ip route %s %s %s' % (prefix, mask, next_hop))

        if state == 'absent' and w in have:
            commands.append('no ip route %s %s %s' % (prefix, mask, next_hop))
        elif state == 'present' and w not in have:
            if admin_distance:
                commands.append('ip route %s %s %s distance %s' % (prefix, mask, next_hop, admin_distance))
            else:
                commands.append('ip route %s %s %s' % (prefix, mask, next_hop))
    if purge:
        commands = []
        for h in have:
            if h not in want:
                commands.append('no ip route %s %s %s' % (prefix, mask, next_hop))
    return commands


def map_config_to_obj(module):
    obj = []
    compare = module.params['check_running_config']
    out = get_config(module, flags='| include ip route', compare=compare)

    for line in out.splitlines():
        splitted_line = line.split()
        if len(splitted_line) not in (4, 5, 6):
            continue
        cidr = ip_network(to_text(splitted_line[2]))
        prefix = str(cidr.network_address)
        mask = str(cidr.netmask)
        next_hop = splitted_line[3]
        if len(splitted_line) == 6:
            admin_distance = splitted_line[5]
        else:
            admin_distance = '1'

        obj.append({
            'prefix': prefix, 'mask': mask, 'next_hop': next_hop,
            'admin_distance': admin_distance
        })

    return obj


def prefix_length_parser(prefix, mask, module):
    if '/' in prefix and mask is not None:
        module.fail_json(msg='Ambigous, specifed both length and mask')
    if '/' in prefix:
        cidr = ip_network(to_text(prefix))
        prefix = str(cidr.network_address)
        mask = str(cidr.netmask)
    return prefix, mask


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

            prefix, mask = prefix_length_parser(route['prefix'], route['mask'], module)
            route.update({'prefix': prefix, 'mask': mask})

            obj.append(route)
    else:
        module._check_required_together(required_together, module.params)
        prefix, mask = prefix_length_parser(module.params['prefix'], module.params['mask'], module)

        obj.append({
            'prefix': prefix,
            'mask': mask,
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
        state=dict(default='present', choices=['present', 'absent']),
        check_running_config=dict(default=True, type='bool', fallback=(env_fallback, ['ANSIBLE_CHECK_ICX_RUNNING_CONFIG']))
    )

    aggregate_spec = deepcopy(element_spec)
    aggregate_spec['prefix'] = dict(required=True)

    remove_default_spec(aggregate_spec)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec),
        purge=dict(default=False, type='bool')
    )

    argument_spec.update(element_spec)

    required_one_of = [['aggregate', 'prefix']]
    required_together = [['prefix', 'next_hop']]
    mutually_exclusive = [['aggregate', 'prefix']]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=required_one_of,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    if not HAS_IPADDRESS:
        module.fail_json(msg="ipaddress python package is required")

    warnings = list()

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
