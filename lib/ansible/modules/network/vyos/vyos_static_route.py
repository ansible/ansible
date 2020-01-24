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
module: vyos_static_route
version_added: "2.4"
author: "Trishna Guha (@trishnaguha)"
short_description: Manage static IP routes on Vyatta VyOS network devices
description:
  - This module provides declarative management of static
    IP routes on Vyatta VyOS network devices.
notes:
  - Tested against VyOS 1.1.8 (helium).
  - This module works with connection C(network_cli). See L(the VyOS OS Platform Options,../network/user_guide/platform_vyos.html).
options:
  prefix:
    description:
      - Network prefix of the static route.
        C(mask) param should be ignored if C(prefix) is provided
        with C(mask) value C(prefix/mask).
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
    description: List of static route definitions
  state:
    description:
      - State of the static route configuration.
    default: present
    choices: ['present', 'absent']
extends_documentation_fragment: vyos
"""

EXAMPLES = """
- name: configure static route
  vyos_static_route:
    prefix: 192.168.2.0
    mask: 24
    next_hop: 10.0.0.1

- name: configure static route prefix/mask
  vyos_static_route:
    prefix: 192.168.2.0/16
    next_hop: 10.0.0.1

- name: remove configuration
  vyos_static_route:
    prefix: 192.168.2.0
    mask: 16
    next_hop: 10.0.0.1
    state: absent

- name: configure aggregates of static routes
  vyos_static_route:
    aggregate:
      - { prefix: 192.168.2.0, mask: 24, next_hop: 10.0.0.1 }
      - { prefix: 192.168.3.0, mask: 16, next_hop: 10.0.2.1 }
      - { prefix: 192.168.3.0/16, next_hop: 10.0.2.1 }

- name: Remove static route collections
  vyos_static_route:
    aggregate:
      - { prefix: 172.24.1.0/24, next_hop: 192.168.42.64 }
      - { prefix: 172.24.3.0/24, next_hop: 192.168.42.64 }
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - set protocols static route 192.168.2.0/16 next-hop 10.0.0.1
"""
import re

from copy import deepcopy

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import remove_default_spec
from ansible.module_utils.network.vyos.vyos import get_config, load_config
from ansible.module_utils.network.vyos.vyos import vyos_argument_spec


def spec_to_commands(updates, module):
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
            commands.append('delete protocols static route %s/%s' % (prefix, mask))
        elif state == 'present' and w not in have:
            cmd = 'set protocols static route %s/%s next-hop %s' % (prefix, mask, next_hop)
            if admin_distance != 'None':
                cmd += ' distance %s' % (admin_distance)
            commands.append(cmd)

    return commands


def config_to_dict(module):
    data = get_config(module)
    obj = []

    for line in data.split('\n'):
        if line.startswith('set protocols static route'):
            match = re.search(r'static route (\S+)', line, re.M)
            prefix = match.group(1).split('/')[0]
            mask = match.group(1).split('/')[1]
            if 'next-hop' in line:
                match_hop = re.search(r'next-hop (\S+)', line, re.M)
                next_hop = match_hop.group(1).strip("'")

                match_distance = re.search(r'distance (\S+)', line, re.M)
                if match_distance is not None:
                    admin_distance = match_distance.group(1)[1:-1]
                else:
                    admin_distance = None

                if admin_distance is not None:
                    obj.append({'prefix': prefix,
                                'mask': mask,
                                'next_hop': next_hop,
                                'admin_distance': admin_distance})
                else:
                    obj.append({'prefix': prefix,
                                'mask': mask,
                                'next_hop': next_hop,
                                'admin_distance': 'None'})

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
            if '/' in d['prefix']:
                d['mask'] = d['prefix'].split('/')[1]
                d['prefix'] = d['prefix'].split('/')[0]

            if 'admin_distance' in d:
                d['admin_distance'] = str(d['admin_distance'])

            obj.append(d)
    else:
        prefix = module.params['prefix'].strip()
        if '/' in prefix:
            mask = prefix.split('/')[1]
            prefix = prefix.split('/')[0]
        else:
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
    argument_spec.update(vyos_argument_spec)

    required_one_of = [['aggregate', 'prefix']]
    required_together = [['prefix', 'next_hop']]
    mutually_exclusive = [['aggregate', 'prefix']]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=required_one_of,
                           required_together=required_together,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    warnings = list()

    result = {'changed': False}
    if warnings:
        result['warnings'] = warnings
    want = map_params_to_obj(module, required_together=required_together)
    have = config_to_dict(module)

    commands = spec_to_commands((want, have), module)
    result['commands'] = commands

    if commands:
        commit = not module.check_mode
        load_config(module, commands, commit=commit)
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
