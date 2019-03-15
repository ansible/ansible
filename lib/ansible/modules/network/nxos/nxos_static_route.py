#!/usr/bin/python
#
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
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = '''
---
module: nxos_static_route
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages static route configuration
description:
  - Manages static route configuration
author: Gabriele Gerbino (@GGabriele)
notes:
  - Tested against NXOSv 7.3.(0)D1(1) on VIRL
  - If no vrf is supplied, vrf is set to default.
  - If C(state=absent), the route will be removed, regardless of the
    non-required parameters.
options:
  prefix:
    description:
      - Destination prefix of static route.
    required: true
    aliases:
      - address
  next_hop:
    description:
      - Next hop address or interface of static route.
        If interface, it must be the fully-qualified interface name.
    required: true
  vrf:
    description:
      - VRF for static route.
    default: default
  tag:
    description:
      - Route tag value (numeric) or keyword 'default'.
  route_name:
    description:
      - Name of the route or keyword 'default'. Used with the name parameter on the CLI.
  pref:
    description:
      - Preference or administrative difference of route (range 1-255) or keyword 'default'.
    aliases:
      - admin_distance
  aggregate:
    description: List of static route definitions
    version_added: 2.5
  track:
    description:
      - Track value (range 1 - 512). Track must already be configured on the device before adding the route.
    version_added: "2.8"
  state:
    description:
      - Manage the state of the resource.
    choices: ['present','absent']
    default: 'present'
'''

EXAMPLES = '''
- nxos_static_route:
    prefix: "192.168.20.64/24"
    next_hop: "192.0.2.3"
    route_name: testing
    pref: 100
'''

RETURN = '''
commands:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["ip route 192.168.20.0/24 192.0.2.3 name testing 100"]
'''
import re
from copy import deepcopy

from ansible.module_utils.network.nxos.nxos import get_config, load_config, run_commands
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.config import CustomNetworkConfig
from ansible.module_utils.network.common.utils import remove_default_spec


def reconcile_candidate(module, candidate, prefix, want):
    state, vrf = want['state'], want['vrf']
    if vrf == 'default':
        parents = []
        flags = " | include '^ip route'"
    else:
        parents = ['vrf context {0}'.format(vrf)]
        flags = " | section '{0}' | include '^  ip route'".format(parents[0])

    # Find existing routes in this vrf/default
    netcfg = CustomNetworkConfig(indent=2, contents=get_config(module, flags=[flags]))
    routes = str(netcfg).split('\n')
    # strip whitespace from route strings
    routes = [i.strip() for i in routes]

    prefix_and_nh = 'ip route {0} {1}'.format(prefix, want['next_hop'])
    existing = [i for i in routes if i.startswith(prefix_and_nh)]
    proposed = set_route_command(prefix, want, module)

    commands = []
    if state == 'absent' and existing:
        commands = ['no ' + existing[0]]
    elif state == 'present' and proposed not in routes:
        if existing:
            commands = ['no ' + existing[0]]
        commands.append(proposed)

    if commands:
        candidate.add(commands, parents=parents)


def get_configured_track(module, ctrack):
    check_track = '{0}'.format(ctrack)
    track_exists = False
    command = 'show track'
    try:
        body = run_commands(module, {'command': command, 'output': 'text'})
        match = re.findall(r'Track\s+(\d+)', body[0])
    except IndexError:
        return None
    if check_track in match:
        track_exists = True
    return track_exists


def set_route_command(prefix, w, module):
    route_cmd = 'ip route {0} {1}'.format(prefix, w['next_hop'])

    if w['track']:
        if w['track'] in range(1, 512):
            if get_configured_track(module, w['track']):
                route_cmd += ' track {0}'.format(w['track'])
            else:
                module.fail_json(msg='Track {0} not configured on device'.format(w['track']))
        else:
            module.fail_json(msg='Invalid track number, valid range is 1-512.')
    if w['route_name'] and w['route_name'] != 'default':
        route_cmd += ' name {0}'.format(w['route_name'])
    if w['tag']:
        if w['tag'] != 'default' and w['tag'] != '0':
            route_cmd += ' tag {0}'.format(w['tag'])
    if w['pref'] and w['pref'] != 'default':
        route_cmd += ' {0}'.format(w['pref'])

    return route_cmd


def get_dotted_mask(mask):
    bits = 0
    for i in range(32 - mask, 32):
        bits |= (1 << i)
    mask = ("%d.%d.%d.%d" % ((bits & 0xff000000) >> 24, (bits & 0xff0000) >> 16, (bits & 0xff00) >> 8, (bits & 0xff)))
    return mask


def get_network_start(address, netmask):
    address = address.split('.')
    netmask = netmask.split('.')
    return [str(int(address[x]) & int(netmask[x])) for x in range(0, 4)]


def network_from_string(address, mask, module):
    octects = address.split('.')

    if len(octects) > 4:
        module.fail_json(msg='Incorrect address format.', address=address)

    for octect in octects:
        try:
            if int(octect) < 0 or int(octect) > 255:
                module.fail_json(msg='Address may contain invalid values.',
                                 address=address)
        except ValueError:
            module.fail_json(msg='Address may contain non-integer values.',
                             address=address)

    try:
        if int(mask) < 0 or int(mask) > 32:
            module.fail_json(msg='Incorrect mask value.', mask=mask)
    except ValueError:
        module.fail_json(msg='Mask may contain non-integer values.', mask=mask)

    netmask = get_dotted_mask(int(mask))
    return '.'.join(get_network_start(address, netmask))


def normalize_prefix(module, prefix):
    splitted_prefix = prefix.split('/')

    address = splitted_prefix[0]
    if len(splitted_prefix) > 2:
        module.fail_json(msg='Incorrect address format.', address=address)
    elif len(splitted_prefix) == 2:
        mask = splitted_prefix[1]
        network = network_from_string(address, mask, module)

        normalized_prefix = str(network) + '/' + str(mask)
    else:
        normalized_prefix = prefix + '/' + str(32)

    return normalized_prefix


def map_params_to_obj(module):
    obj = []
    aggregate = module.params.get('aggregate')
    if aggregate:
        for item in aggregate:
            for key in item:
                if item.get(key) is None:
                    item[key] = module.params[key]

            d = item.copy()
            obj.append(d)
    else:
        obj.append({
            'prefix': module.params['prefix'],
            'next_hop': module.params['next_hop'],
            'vrf': module.params['vrf'],
            'tag': module.params['tag'],
            'route_name': module.params['route_name'],
            'pref': module.params['pref'],
            'state': module.params['state'],
            'track': module.params['track']
        })

    return obj


def main():
    element_spec = dict(
        prefix=dict(type='str', aliases=['address']),
        next_hop=dict(type='str'),
        vrf=dict(type='str', default='default'),
        tag=dict(type='str'),
        route_name=dict(type='str'),
        pref=dict(type='str', aliases=['admin_distance']),
        state=dict(choices=['absent', 'present'], default='present'),
        track=dict(type='int'),
    )

    aggregate_spec = deepcopy(element_spec)
    aggregate_spec['prefix'] = dict(required=True)
    aggregate_spec['next_hop'] = dict(required=True)

    # remove default in aggregate spec, to handle common arguments
    remove_default_spec(aggregate_spec)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec)
    )

    argument_spec.update(element_spec)
    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    warnings = list()
    result = {'changed': False, 'commands': []}
    if warnings:
        result['warnings'] = warnings

    want = map_params_to_obj(module)
    for w in want:
        prefix = normalize_prefix(module, w['prefix'])
        candidate = CustomNetworkConfig(indent=3)
        reconcile_candidate(module, candidate, prefix, w)

        if not module.check_mode and candidate:
            candidate = candidate.items_text()
            load_config(module, candidate)
            result['commands'].extend(candidate)
            result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
