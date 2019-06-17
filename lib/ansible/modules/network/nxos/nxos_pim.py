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
module: nxos_pim
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages configuration of a PIM instance.
description:
    - Manages configuration of a Protocol Independent Multicast (PIM) instance.
author: Gabriele Gerbino (@GGabriele)
options:
  bfd:
    description:
      - Enables BFD on all PIM interfaces.
      - "Dependency: 'feature bfd'"
    version_added: "2.9"
    type: str
    choices: ['enable', 'disable']

  ssm_range:
    description:
      - Configure group ranges for Source Specific Multicast (SSM).
        Valid values are multicast addresses or the keyword C(none)
        or keyword C(default). C(none) removes all SSM group ranges.
        C(default) will set ssm_range to the default multicast address.
        If you set multicast address, please ensure that it is not the
        same as the C(default), otherwise use the C(default) option.
    required: true
'''
EXAMPLES = '''
- name: Configure ssm_range, enable bfd
  nxos_pim:
    bfd: enable
    ssm_range: "224.0.0.0/8"

- name: Set to default
  nxos_pim:
    ssm_range: default

- name: Remove all ssm group ranges
  nxos_pim:
    ssm_range: none
'''

RETURN = '''
commands:
    description: commands sent to the device
    returned: always
    type: list
    sample:
      - ip pim bfd
      - ip pim ssm range 224.0.0.0/8
'''


import re

from ansible.module_utils.network.nxos.nxos import get_config, load_config
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.config import CustomNetworkConfig


PARAM_TO_COMMAND_KEYMAP = {
    'bfd': 'ip pim bfd',
    'ssm_range': 'ip pim ssm range',
}


def get_existing(module, args):
    existing = {}
    config = str(get_config(module))

    for arg in args:
        if 'ssm_range' in arg:
            # <value> may be 'n.n.n.n/s', 'none', or 'default'
            m = re.search(r'ssm range (?P<value>(?:[\s\d.\/]+|none|default))?$', config, re.M)
            if m:
                # Remove rsvd SSM range
                value = m.group('value').replace('232.0.0.0/8', '')
                existing[arg] = value.split()

        elif 'bfd' in arg and 'ip pim bfd' in config:
            existing[arg] = 'enable'

    return existing


def apply_key_map(key_map, table):
    new_dict = {}
    for key, value in table.items():
        new_key = key_map.get(key)
        if value is not None:
            new_dict[new_key] = value
    return new_dict


def get_commands(module, existing, proposed, candidate):
    commands = list()
    proposed_commands = apply_key_map(PARAM_TO_COMMAND_KEYMAP, proposed)

    for key, value in proposed_commands.items():
        command = ''
        if key == 'ip pim ssm range':
            if value == 'default':
                # no cmd needs a value but the actual value does not matter
                command = 'no ip pim ssm range none'
            elif value == 'none':
                command = 'ip pim ssm range none'
            elif value:
                command = 'ip pim ssm range {0}'.format(value)
        elif key == 'ip pim bfd':
            no_cmd = 'no ' if value == 'disable' else ''
            command = no_cmd + key

        if command:
            commands.append(command)

    if commands:
        candidate.add(commands, parents=[])


def main():
    argument_spec = dict(
        bfd=dict(required=False, type='str', choices=['enable', 'disable']),
        ssm_range=dict(required=False, type='list', default=[]),
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)
    warnings = list()
    check_args(module, warnings)
    result = {'changed': False, 'commands': [], 'warnings': warnings}

    params = module.params
    args = [k for k in PARAM_TO_COMMAND_KEYMAP.keys() if params[k] is not None]

    # SSM syntax check
    if 'ssm_range' in args:
        for item in params['ssm_range']:
            if re.search('none|default', item):
                break
            if len(item.split('.')) != 4:
                module.fail_json(msg="Valid ssm_range values are multicast addresses "
                                     "or the keyword 'none' or the keyword 'default'.")

    existing = get_existing(module, args)
    proposed_args = dict((k, v) for k, v in params.items() if k in args)

    proposed = {}
    for key, value in proposed_args.items():
        if key == 'ssm_range':
            if value and value[0] == 'default':
                if existing.get(key):
                    proposed[key] = 'default'
            else:
                v = sorted(set([str(i) for i in value]))
                ex = sorted(set([str(i) for i in existing.get(key, [])]))
                if v != ex:
                    proposed[key] = ' '.join(str(s) for s in v)

        elif key == 'bfd':
            if value != existing.get('bfd', 'disable'):
                proposed[key] = value

        elif value != existing.get(key):
            proposed[key] = value

    candidate = CustomNetworkConfig(indent=3)
    get_commands(module, existing, proposed, candidate)

    if candidate:
        candidate = candidate.items_text()
        result['commands'] = candidate
        result['changed'] = True
        load_config(module, candidate)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
