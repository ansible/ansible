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
- name: Configure ssm_range
  nxos_pim:
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
    sample: ["ip pim ssm range 224.0.0.0/8"]
'''


import re

from ansible.module_utils.network.nxos.nxos import get_config, load_config
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.config import CustomNetworkConfig


PARAM_TO_COMMAND_KEYMAP = {
    'ssm_range': 'ip pim ssm range'
}


def get_existing(module, args):
    existing = {}
    config = str(get_config(module))

    for arg in args:
        command = PARAM_TO_COMMAND_KEYMAP[arg]
        has_command = re.search(r'^{0}\s(?P<value>.*)$'.format(command), config, re.M)

        value = ''
        if has_command:
            value = has_command.group('value')
            if value == '232.0.0.0/8':
                value = ''  # remove the reserved value
        existing[arg] = value.split()
    return existing


def apply_key_map(key_map, table):
    new_dict = {}
    for key, value in table.items():
        new_key = key_map.get(key)
        if value:
            new_dict[new_key] = value
    return new_dict


def get_commands(module, existing, proposed, candidate):
    commands = list()
    proposed_commands = apply_key_map(PARAM_TO_COMMAND_KEYMAP, proposed)

    for key, value in proposed_commands.items():
        if key == 'ip pim ssm range' and value == 'default':
            # no cmd needs a value but the actual value does not matter
            command = 'no ip pim ssm range none'
            commands.append(command)
        else:
            command = '{0} {1}'.format(key, value)
            commands.append(command)

    if commands:
        candidate.add(commands, parents=[])


def main():
    argument_spec = dict(
        ssm_range=dict(required=True, type='list'),
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)
    result = {'changed': False, 'commands': [], 'warnings': warnings}

    ssm_range_list = module.params['ssm_range']
    for item in ssm_range_list:
        splitted_ssm_range = item.split('.')
        if len(splitted_ssm_range) != 4 and item != 'none' and item != 'default':
            module.fail_json(msg="Valid ssm_range values are multicast addresses "
                                 "or the keyword 'none' or the keyword 'default'.")

    args = PARAM_TO_COMMAND_KEYMAP.keys()

    existing = get_existing(module, args)
    proposed_args = dict((k, v) for k, v in module.params.items() if k in args)

    proposed = {}
    for key, value in proposed_args.items():
        if key == 'ssm_range':
            if value[0] == 'default':
                if existing.get(key):
                    proposed[key] = 'default'
            else:
                v = sorted(set([str(i) for i in value]))
                ex = sorted(set([str(i) for i in existing.get(key)]))
                if v != ex:
                    proposed[key] = ' '.join(str(s) for s in v)

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
