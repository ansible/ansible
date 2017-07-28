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
module: nxos_vrf_af
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages VRF AF.
description:
  - Manages VRF AF
author: Gabriele Gerbino (@GGabriele)
notes:
  - Default, where supported, restores params default value.
options:
  vrf:
    description:
      - Name of the VRF.
    required: true
  afi:
    description:
      - Address-Family Identifier (AFI).
    required: true
    choices: ['ipv4', 'ipv6']
    default: null
  safi:
    description:
      - Sub Address-Family Identifier (SAFI).
    required: true
    choices: ['unicast', 'multicast']
    default: null
  route_target_both_auto_evpn:
    description:
      - Enable/Disable the EVPN route-target 'auto' setting for both
        import and export target communities.
    required: false
    choices: ['true', 'false']
    default: null
  state:
    description:
      - Determines whether the config should be present or
        not on the device.
    required: false
    default: present
    choices: ['present','absent']
'''

EXAMPLES = '''
- nxos_vrf_af:
    vrf: ntc
    afi: ipv4
    safi: unicast
    route_target_both_auto_evpn: True
    state: present
'''

RETURN = '''
commands:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["vrf context ntc", "address-family ipv4 unicast"]
'''

import re

from ansible.module_utils.nxos import get_config, load_config, run_commands
from ansible.module_utils.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.netcfg import CustomNetworkConfig


BOOL_PARAMS = ['route_target_both_auto_evpn']
PARAM_TO_COMMAND_KEYMAP = {
    'route_target_both_auto_evpn': 'route-target both auto evpn'
}
PARAM_TO_DEFAULT_KEYMAP = {}


def get_value(arg, config, module):
    command = PARAM_TO_COMMAND_KEYMAP.get(arg)
    if arg in BOOL_PARAMS:
        command_re = re.compile(r'\s+{0}\s*$'.format(command), re.M)
        value = False
        try:
            if command_re.search(config):
                value = True
        except TypeError:
            value = False
    else:
        command_re = re.compile(r'(?:{0}\s)(?P<value>.*)$'.format(command), re.M)
        value = ''
        if command in config:
            value = command_re.search(config).group('value')
    return value


def get_existing(module, args):
    existing = {}
    netcfg = CustomNetworkConfig(indent=2, contents=get_config(module))

    parents = ['vrf context {0}'.format(module.params['vrf'])]
    parents.append('address-family {0} {1}'.format(module.params['afi'],
                                                   module.params['safi']))
    config = netcfg.get_section(parents)
    if config:
        splitted_config = config.splitlines()
        vrf_index = False
        for index in range(0, len(splitted_config) - 1):
            if 'vrf' in splitted_config[index].strip():
                vrf_index = index
                break
        if vrf_index:
            config = '\n'.join(splitted_config[0:vrf_index])

        for arg in args:
            if arg not in ['afi', 'safi', 'vrf']:
                existing[arg] = get_value(arg, config, module)

        existing['afi'] = module.params['afi']
        existing['safi'] = module.params['safi']
        existing['vrf'] = module.params['vrf']

    return existing


def apply_key_map(key_map, table):
    new_dict = {}
    for key in table:
        new_key = key_map.get(key)
        if new_key:
            new_dict[new_key] = table.get(key)
    return new_dict


def state_present(module, existing, proposed, candidate):
    commands = list()
    proposed_commands = apply_key_map(PARAM_TO_COMMAND_KEYMAP, proposed)
    existing_commands = apply_key_map(PARAM_TO_COMMAND_KEYMAP, existing)

    for key, value in proposed_commands.items():
        if value is True:
            commands.append(key)

        elif value is False:
            commands.append('no {0}'.format(key))

        elif value == 'default':
            if existing_commands.get(key):
                existing_value = existing_commands.get(key)
                commands.append('no {0} {1}'.format(key, existing_value))
        else:
            command = '{0} {1}'.format(key, value.lower())
            commands.append(command)

    parents = ['vrf context {0}'.format(module.params['vrf'])]
    parents.append('address-family {0} {1}'.format(module.params['afi'],
                                                   module.params['safi']))
    candidate.add(commands, parents=parents)


def state_absent(module, existing, proposed, candidate):
    commands = []
    parents = ['vrf context {0}'.format(module.params['vrf'])]
    commands.append('no address-family {0} {1}'.format(module.params['afi'],
                                                       module.params['safi']))
    candidate.add(commands, parents=parents)


def main():
    argument_spec = dict(
        vrf=dict(required=True, type='str'),
        safi=dict(required=True, type='str', choices=['unicast', 'multicast']),
        afi=dict(required=True, type='str', choices=['ipv4', 'ipv6']),
        route_target_both_auto_evpn=dict(required=False, type='bool'),
        m_facts=dict(required=False, default=False, type='bool'),
        state=dict(choices=['present', 'absent'], default='present', required=False)
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)
    result = dict(changed=False, warnings=warnings)

    state = module.params['state']
    args = PARAM_TO_COMMAND_KEYMAP.keys()
    existing = get_existing(module, args)
    proposed_args = dict((k, v) for k, v in module.params.items()
                         if v is not None and k in args)

    proposed = {}
    for key, value in proposed_args.items():
        if key != 'interface':
            if str(value).lower() == 'default':
                value = PARAM_TO_DEFAULT_KEYMAP.get(key)
                if value is None:
                    value = 'default'
            if existing.get(key) != value:
                proposed[key] = value

    candidate = CustomNetworkConfig(indent=3)
    if state == 'present':
        state_present(module, existing, proposed, candidate)
    elif state == 'absent' and existing:
        state_absent(module, existing, proposed, candidate)

    if candidate:
        candidate = candidate.items_text()
        load_config(module, candidate)
        result['changed'] = True
        result['commands'] = candidate

    else:
        result['commands'] = []
    module.exit_json(**result)


if __name__ == '__main__':
    main()
