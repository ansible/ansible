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
ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


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
    - If no vrf is supplied, vrf is set to default.
    - If C(state=absent), the route will be removed, regardless of the
      non-required parameters.
options:
    prefix:
        description:
            - Destination prefix of static route.
        required: true
    next_hop:
        description:
            - Next hop address or interface of static route.
              If interface, it must be the fully-qualified interface name.
        required: true
    vrf:
        description:
            - VRF for static route.
        required: false
        default: default
    tag:
        description:
            - Route tag value (numeric).
        required: false
        default: null
    route_name:
        description:
            - Name of the route. Used with the name parameter on the CLI.
        required: false
        default: null
    pref:
        description:
            - Preference or administrative difference of route (range 1-255).
        required: false
        default: null
    state:
        description:
            - Manage the state of the resource.
        required: true
        choices: ['present','absent']
'''

EXAMPLES = '''
- nxos_static_route:
    prefix: "192.168.20.64/24"
    next_hop: "3.3.3.3"
    route_name: testing
    pref: 100
    username: "{{ un }}"
    password: "{{ pwd }}"
    host: "{{ inventory_hostname }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: verbose mode
    type: dict
    sample: {"next_hop": "3.3.3.3", "pref": "100",
            "prefix": "192.168.20.64/24", "route_name": "testing",
            "vrf": "default"}
existing:
    description: k/v pairs of existing configuration
    returned: verbose mode
    type: dict
    sample: {}
end_state:
    description: k/v pairs of configuration after module execution
    returned: verbose mode
    type: dict
    sample: {"next_hop": "3.3.3.3", "pref": "100",
            "prefix": "192.168.20.0/24", "route_name": "testing",
            "tag": null}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["ip route 192.168.20.0/24 3.3.3.3 name testing 100"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''
import re

from ansible.module_utils.nxos import get_config, load_config, run_commands
from ansible.module_utils.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.netcfg import CustomNetworkConfig

def invoke(name, *args, **kwargs):
    func = globals().get(name)
    if func:
        return func(*args, **kwargs)


def state_present(module, candidate, prefix):
    commands = list()
    invoke('set_route', module, commands, prefix)
    if commands:
        if module.params['vrf'] == 'default':
            candidate.add(commands, parents=[])
        else:
            candidate.add(commands, parents=['vrf context {0}'.format(module.params['vrf'])])


def state_absent(module, candidate, prefix):
    netcfg = CustomNetworkConfig(indent=2, contents=get_config(module))
    commands = list()
    parents = 'vrf context {0}'.format(module.params['vrf'])
    invoke('set_route', module, commands, prefix)
    if module.params['vrf'] == 'default':
        config = netcfg.get_section(commands[0])
        if config:
            invoke('remove_route', module, commands, config, prefix)
            candidate.add(commands, parents=[])
    else:
        config = netcfg.get_section(parents)
        splitted_config = config.split('\n')
        splitted_config = map(str.strip, splitted_config)
        if commands[0] in splitted_config:
            invoke('remove_route', module, commands, config, prefix)
            candidate.add(commands, parents=[parents])


def fix_prefix_to_regex(prefix):
    prefix = prefix.replace('.', '\.').replace('/', '\/')
    return prefix


def get_existing(module, prefix, warnings):
    key_map = ['tag', 'pref', 'route_name', 'next_hop']
    netcfg = CustomNetworkConfig(indent=2, contents=get_config(module))
    parents = 'vrf context {0}'.format(module.params['vrf'])
    prefix_to_regex = fix_prefix_to_regex(prefix)

    route_regex = ('.*ip\sroute\s{0}\s(?P<next_hop>\S+)(\sname\s(?P<route_name>\S+))?'
                   '(\stag\s(?P<tag>\d+))?(\s(?P<pref>\d+)).*'.format(prefix_to_regex))

    if module.params['vrf'] == 'default':
        config = str(netcfg)
    else:
        config = netcfg.get_section(parents)

    if config:
        try:
            match_route = re.match(route_regex, config, re.DOTALL)
            group_route = match_route.groupdict()

            for key in key_map:
                if key not in group_route:
                    group_route[key] = ''
            group_route['prefix'] = prefix
            group_route['vrf'] = module.params['vrf']
        except (AttributeError, TypeError):
            group_route = {}
    else:
        group_route = {}
        msg = ("VRF {0} didn't exist.".format(module.params['vrf']))
        if msg not in warnings:
            warnings.append(msg)

    return group_route


def remove_route(module, commands, config, prefix):
    commands.append('no ip route {0} {1}'.format(prefix, module.params['next_hop']))


def set_route(module, commands, prefix):
    route_cmd = 'ip route {0} {1}'.format(prefix, module.params['next_hop'])

    if module.params['route_name']:
        route_cmd += ' name {0}'.format(module.params['route_name'])
    if module.params['tag']:
        route_cmd += ' tag {0}'.format(module.params['tag'])
    if module.params['pref']:
        route_cmd += ' {0}'.format(module.params['pref'])
    commands.append(route_cmd)


def get_dotted_mask(mask):
    bits = 0
    for i in xrange(32-mask,32):
        bits |= (1 << i)
    mask = ("%d.%d.%d.%d" % ((bits & 0xff000000) >> 24,
           (bits & 0xff0000) >> 16, (bits & 0xff00) >> 8 , (bits & 0xff)))
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


def main():
    argument_spec = dict(
        prefix=dict(required=True, type='str'),
        next_hop=dict(required=True, type='str'),
        vrf=dict(type='str', default='default'),
        tag=dict(type='str'),
        route_name=dict(type='str'),
        pref=dict(type='str'),
        state=dict(choices=['absent', 'present'],
                   default='present'),
        include_defaults=dict(default=True),

        config=dict(),
        save=dict(type='bool', default=False)
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    state = module.params['state']

    result = dict(changed=False)
    warnings = list()
    prefix = invoke('normalize_prefix', module, module.params['prefix'])

    existing = invoke('get_existing', module, prefix, warnings)
    end_state = existing

    args = ['route_name', 'vrf', 'pref', 'tag', 'next_hop', 'prefix']
    proposed = dict((k, v) for k, v in module.params.items() if v is not None and k in args)

    if state == 'present' or (state == 'absent' and existing):
        candidate = CustomNetworkConfig(indent=3)
        invoke('state_%s' % state, module, candidate, prefix)

        load_config(module, candidate)
    else:
        result['updates'] = []

    result['warnings'] = warnings

    if module._verbosity > 0:
        end_state = invoke('get_existing', module, prefix, warnings)
        result['end_state'] = end_state
        result['existing'] = existing
        result['proposed'] = proposed

    module.exit_json(**result)


if __name__ == '__main__':
    main()

