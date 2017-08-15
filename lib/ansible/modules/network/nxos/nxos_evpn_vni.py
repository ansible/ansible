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

ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'status': ['preview'],
    'supported_by': 'community'
}


DOCUMENTATION = '''
---
module: nxos_evpn_vni
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages Cisco EVPN VXLAN Network Identifier (VNI).
description:
  - Manages Cisco Ethernet Virtual Private Network (EVPN) VXLAN Network
    Identifier (VNI) configurations of a Nexus device.
author: Gabriele Gerbino (@GGabriele)
notes:
  - default, where supported, restores params default value.
  - RD override is not permitted. You should set it to the default values
    first and then reconfigure it.
  - C(route_target_both), C(route_target_import) and
    C(route_target_export valid) values are a list of extended communities,
    (i.e. ['1.2.3.4:5', '33:55']) or the keywords 'auto' or 'default'.
  - The C(route_target_both) property is discouraged due to the inconsistent
    behavior of the property across Nexus platforms and image versions.
    For this reason it is recommended to use explicit C(route_target_export)
    and C(route_target_import) properties instead of C(route_target_both).
  - RD valid values are a string in one of the route-distinguisher formats,
    the keyword 'auto', or the keyword 'default'.
options:
  vni:
    description:
      - The EVPN VXLAN Network Identifier.
    required: true
    default: null
  route_distinguisher:
    description:
      - The VPN Route Distinguisher (RD). The RD is combined with
        the IPv4 or IPv6 prefix learned by the PE router to create a
        globally unique address.
    required: true
    default: null
  route_target_both:
    description:
      - Enables/Disables route-target settings for both import and
        export target communities using a single property.
    required: false
    default: null
  route_target_import:
    description:
      - Sets the route-target 'import' extended communities.
    required: false
    default: null
  route_target_export:
    description:
      - Sets the route-target 'import' extended communities.
    required: false
    default: null
  state:
    description:
      - Determines whether the config should be present or not
        on the device.
    required: false
    default: present
    choices: ['present','absent']
'''

EXAMPLES = '''
- name: vni configuration
  nxos_evpn_vni:
    vni: 6000
    route_distinguisher: "60:10"
    route_target_import:
      - "5000:10"
      - "4100:100"
    route_target_export: auto
    route_target_both: default
'''

RETURN = '''
commands:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["evpn", "vni 6000 l2", "route-target import 5001:10"]
'''

import re
import time
from ansible.module_utils.nxos import get_config, load_config, run_commands
from ansible.module_utils.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.netcfg import CustomNetworkConfig


PARAM_TO_COMMAND_KEYMAP = {
    'vni': 'vni',
    'route_distinguisher': 'rd',
    'route_target_both': 'route-target both',
    'route_target_import': 'route-target import',
    'route_target_export': 'route-target export'
}


def get_value(arg, config, module):
    command = PARAM_TO_COMMAND_KEYMAP.get(arg)
    command_re = re.compile(r'(?:{0}\s)(?P<value>.*)$'.format(command), re.M)
    value = ''
    if command in config:
        value = command_re.search(config).group('value')
    return value


def get_route_target_value(arg, config, module):
    splitted_config = config.splitlines()
    value_list = []
    command = PARAM_TO_COMMAND_KEYMAP.get(arg)
    command_re = re.compile(r'(?:{0}\s)(?P<value>.*)$'.format(command), re.M)

    for line in splitted_config:
        value = ''
        if command in line.strip():
            value = command_re.search(line).group('value')
            value_list.append(value)
    return value_list


def get_existing(module, args):
    existing = {}
    netcfg = CustomNetworkConfig(indent=2, contents=get_config(module))
    parents = ['evpn', 'vni {0} l2'.format(module.params['vni'])]
    config = netcfg.get_section(parents)

    if config:
        for arg in args:
            if arg != 'vni':
                if arg == 'route_distinguisher':
                    existing[arg] = get_value(arg, config, module)
                else:
                    existing[arg] = get_route_target_value(arg, config, module)

        existing_fix = dict((k, v) for k, v in existing.items() if v)
        if existing_fix:
            existing['vni'] = module.params['vni']
        else:
            existing = existing_fix

    return existing


def apply_key_map(key_map, table):
    new_dict = {}
    for key in table:
        new_key = key_map.get(key)
        if new_key:
            new_dict[new_key] = table.get(key)
    return new_dict


def fix_proposed(proposed_commands):
    new_proposed = {}
    for key, value in proposed_commands.items():
        if key == 'route-target both':
            new_proposed['route-target export'] = value
            new_proposed['route-target import'] = value
        else:
            new_proposed[key] = value
    return new_proposed


def state_present(module, existing, proposed):
    commands = list()
    parents = list()
    proposed_commands = apply_key_map(PARAM_TO_COMMAND_KEYMAP, proposed)
    existing_commands = apply_key_map(PARAM_TO_COMMAND_KEYMAP, existing)

    if proposed_commands.get('route-target both'):
        proposed_commands = fix_proposed(proposed_commands)

    for key, value in proposed_commands.items():
        if key.startswith('route-target'):
            if value == ['default']:
                existing_value = existing_commands.get(key)

                if existing_value:
                    for target in existing_value:
                        commands.append('no {0} {1}'.format(key, target))
            elif not isinstance(value, list):
                value = [value]
            for target in value:
                if existing:
                    if target not in existing.get(key.replace('-', '_').replace(' ', '_')):
                        commands.append('{0} {1}'.format(key, target))
                else:
                    commands.append('{0} {1}'.format(key, target))
        elif value == 'default':
            existing_value = existing_commands.get(key)
            if existing_value:
                commands.append('no {0} {1}'.format(key, existing_value))
        else:
            command = '{0} {1}'.format(key, value)
            commands.append(command)

    if commands:
        parents = ['evpn', 'vni {0} l2'.format(module.params['vni'])]

    return commands, parents


def state_absent(module, existing, proposed):
    commands = ['no vni {0} l2'.format(module.params['vni'])]
    parents = ['evpn']
    return commands, parents


def main():
    argument_spec = dict(
        vni=dict(required=True, type='str'),
        route_distinguisher=dict(required=False, type='str'),
        route_target_both=dict(required=False, type='list'),
        route_target_import=dict(required=False, type='list'),
        route_target_export=dict(required=False, type='list'),
        state=dict(choices=['present', 'absent'], default='present', required=False),
        include_defaults=dict(default=True),
        config=dict(),
        save=dict(type='bool', default=False)
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)
    results = dict(changed=False, warnings=warnings)

    state = module.params['state']
    args = PARAM_TO_COMMAND_KEYMAP.keys()
    existing = get_existing(module, args)
    proposed_args = dict((k, v) for k, v in module.params.items()
                         if v is not None and k in args)
    commands = []
    parents = []

    proposed = {}
    for key, value in proposed_args.items():
        if key != 'vni':
            if value == 'true':
                value = True
            elif value == 'false':
                value = False
            if existing.get(key) != value:
                proposed[key] = value

    if state == 'present':
        commands, parents = state_present(module, existing, proposed)
    elif state == 'absent' and existing:
        commands, parents = state_absent(module, existing, proposed)

    if commands:
        if (existing.get('route_distinguisher') and
                proposed.get('route_distinguisher')):
            if (existing['route_distinguisher'] != proposed['route_distinguisher'] and
                    proposed['route_distinguisher'] != 'default'):
                warnings.append('EVPN RD {0} was automatically removed. '
                                'It is highly recommended to use a task '
                                '(with default as value) to explicitly '
                                'unconfigure it.'.format(existing['route_distinguisher']))
                remove_commands = ['no rd {0}'.format(existing['route_distinguisher'])]

                candidate = CustomNetworkConfig(indent=3)
                candidate.add(remove_commands, parents=parents)
                load_config(module, candidate)
                results['changed'] = True
                results['commands'] = candidate.items_text()
                time.sleep(30)

        else:
            candidate = CustomNetworkConfig(indent=3)
            candidate.add(commands, parents=parents)
            candidate = candidate.items_text()
            load_config(module, candidate)
            results['changed'] = True
            results['commands'] = candidate
    else:
        results['commands'] = []
    module.exit_json(**results)


if __name__ == '__main__':
    main()
