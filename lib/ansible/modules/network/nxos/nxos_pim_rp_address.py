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
module: nxos_pim_rp_address
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages configuration of an PIM static RP address instance.
description:
  - Manages configuration of an Protocol Independent Multicast (PIM) static
    rendezvous point (RP) address instance.
author: Gabriele Gerbino (@GGabriele)
notes:
  - Tested against NXOSv 7.3.(0)D1(1) on VIRL
  - C(state=absent) is currently not supported on all platforms.
options:
  rp_address:
    description:
      - Configures a Protocol Independent Multicast (PIM) static
        rendezvous point (RP) address. Valid values are
        unicast addresses.
    required: true
  group_list:
    description:
      - Group range for static RP. Valid values are multicast addresses.
  prefix_list:
    description:
      - Prefix list policy for static RP. Valid values are prefix-list
        policy names.
  route_map:
    description:
      - Route map policy for static RP. Valid values are route-map
        policy names.
  bidir:
    description:
      - Group range is treated in PIM bidirectional mode.
    type: bool
  state:
    description:
      - Specify desired state of the resource.
    required: true
    default: present
    choices: ['present','absent','default']
'''
EXAMPLES = '''
- nxos_pim_rp_address:
    rp_address: "10.1.1.20"
    state: present
'''

RETURN = '''
commands:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["router bgp 65535", "vrf test", "router-id 1.1.1.1"]
'''


import re

from ansible.module_utils.network.nxos.nxos import get_config, load_config
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.config import CustomNetworkConfig


def get_existing(module, args, gl):
    existing = {}
    config = str(get_config(module))
    address = module.params['rp_address']

    pim_address_re = r'ip pim rp-address (?P<value>.*)$'
    for line in re.findall(pim_address_re, config, re.M):

        values = line.split()
        if values[0] != address:
            continue
        if gl and 'group-list' not in line:
            continue
        elif not gl and 'group-list' in line:
            if '224.0.0.0/4' not in line:  # ignore default group-list
                continue

        existing['bidir'] = existing.get('bidir') or 'bidir' in line
        if len(values) > 2:
            value = values[2]
            if values[1] == 'route-map':
                existing['route_map'] = value
            elif values[1] == 'prefix-list':
                existing['prefix_list'] = value
            elif values[1] == 'group-list':
                if value != '224.0.0.0/4':  # ignore default group-list
                    existing['group_list'] = value

    return existing


def state_present(module, existing, proposed, candidate):
    address = module.params['rp_address']
    command = 'ip pim rp-address {0}'.format(address)
    if module.params['group_list'] and not proposed.get('group_list'):
        command += ' group-list ' + module.params['group_list']
    if module.params['prefix_list']:
        if not proposed.get('prefix_list'):
            command += ' prefix-list ' + module.params['prefix_list']
    if module.params['route_map']:
        if not proposed.get('route_map'):
            command += ' route-map ' + module.params['route_map']
    commands = build_command(proposed, command)
    if commands:
        candidate.add(commands, parents=[])


def build_command(param_dict, command):
    for param in ['group_list', 'prefix_list', 'route_map']:
        if param_dict.get(param):
            command += ' {0} {1}'.format(
                param.replace('_', '-'), param_dict.get(param))
    if param_dict.get('bidir'):
        command += ' bidir'
    return [command]


def state_absent(module, existing, candidate):
    address = module.params['rp_address']

    commands = []
    command = 'no ip pim rp-address {0}'.format(address)
    if module.params['group_list'] == existing.get('group_list'):
        commands = build_command(existing, command)
    elif not module.params['group_list']:
        commands = [command]

    if commands:
        candidate.add(commands, parents=[])


def get_proposed(pargs, existing):
    proposed = {}

    for key, value in pargs.items():
        if key != 'rp_address':
            if str(value).lower() == 'true':
                value = True
            elif str(value).lower() == 'false':
                value = False

            if existing.get(key) != value:
                proposed[key] = value

    return proposed


def main():
    argument_spec = dict(
        rp_address=dict(required=True, type='str'),
        group_list=dict(required=False, type='str'),
        prefix_list=dict(required=False, type='str'),
        route_map=dict(required=False, type='str'),
        bidir=dict(required=False, type='bool'),
        state=dict(choices=['present', 'absent'], default='present', required=False),
    )
    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=[['group_list', 'route_map'],
                                               ['group_list', 'prefix_list'],
                                               ['route_map', 'prefix_list']],
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)
    result = {'changed': False, 'commands': [], 'warnings': warnings}

    state = module.params['state']

    args = [
        'rp_address',
        'group_list',
        'prefix_list',
        'route_map',
        'bidir'
    ]

    proposed_args = dict((k, v) for k, v in module.params.items()
                         if v is not None and k in args)

    if module.params['group_list']:
        existing = get_existing(module, args, True)
        proposed = get_proposed(proposed_args, existing)

    else:
        existing = get_existing(module, args, False)
        proposed = get_proposed(proposed_args, existing)

    candidate = CustomNetworkConfig(indent=3)
    if state == 'present' and (proposed or not existing):
        state_present(module, existing, proposed, candidate)
    elif state == 'absent' and existing:
        state_absent(module, existing, candidate)

    if candidate:
        candidate = candidate.items_text()
        result['commands'] = candidate
        result['changed'] = True
        msgs = load_config(module, candidate, True)
        if msgs:
            for item in msgs:
                if item:
                    if isinstance(item, dict):
                        err_str = item['clierror']
                    else:
                        err_str = item
                    if 'No policy was configured' in err_str:
                        if state == 'absent':
                            addr = module.params['rp_address']
                            new_cmd = 'no ip pim rp-address {0}'.format(addr)
                            load_config(module, new_cmd)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
