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
module: nxos_overlay_global
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Configures anycast gateway MAC of the switch.
description:
  - Configures anycast gateway MAC of the switch.
author: Gabriele Gerbino (@GGabriele)
notes:
  - Tested against NXOSv 7.3.(0)D1(1) on VIRL
  - Default restores params default value
  - Supported MAC address format are "E.E.E", "EE-EE-EE-EE-EE-EE",
    "EE:EE:EE:EE:EE:EE" and "EEEE.EEEE.EEEE"
options:
  anycast_gateway_mac:
    description:
      - Anycast gateway mac of the switch.
    required: true
    default: null
'''

EXAMPLES = '''
- nxos_overlay_global:
    anycast_gateway_mac: "b.b.b"
'''

RETURN = '''
commands:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["fabric forwarding anycast-gateway-mac 000B.000B.000B"]
'''

import re
from ansible.module_utils.network.nxos.nxos import get_config, load_config
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.config import CustomNetworkConfig

PARAM_TO_COMMAND_KEYMAP = {
    'anycast_gateway_mac': 'fabric forwarding anycast-gateway-mac',
}


def get_existing(module, args):
    existing = {}
    config = str(get_config(module))

    for arg in args:
        command = PARAM_TO_COMMAND_KEYMAP[arg]
        has_command = re.findall(r'(?:{0}\s)(?P<value>.*)$'.format(command), config, re.M)
        value = ''
        if has_command:
            value = has_command[0]
        existing[arg] = value

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
    existing_commands = apply_key_map(PARAM_TO_COMMAND_KEYMAP, existing)

    for key, proposed in proposed_commands.items():
        existing_value = existing_commands.get(key)
        if proposed == 'default' and existing_value:
            commands.append('no {0} {1}'.format(key, existing_value))
        elif 'anycast-gateway-mac' in key and proposed != 'default':
            proposed = normalize_mac(proposed, module)
            existing_value = normalize_mac(existing_value, module)
            if proposed != existing_value:
                command = '{0} {1}'.format(key, proposed)
                commands.append(command)
    if commands:
        candidate.add(commands, parents=[])


def normalize_mac(proposed_mac, module):
    if proposed_mac is None:
        return ''
    try:
        if '-' in proposed_mac:
            splitted_mac = proposed_mac.split('-')
            if len(splitted_mac) != 6:
                raise ValueError

            for octect in splitted_mac:
                if len(octect) != 2:
                    raise ValueError

        elif '.' in proposed_mac:
            splitted_mac = []
            splitted_dot_mac = proposed_mac.split('.')
            if len(splitted_dot_mac) != 3:
                raise ValueError

            for octect in splitted_dot_mac:
                if len(octect) > 4:
                    raise ValueError
                else:
                    octect_len = len(octect)
                    padding = 4 - octect_len
                    splitted_mac.append(octect.zfill(padding + 1))

        elif ':' in proposed_mac:
            splitted_mac = proposed_mac.split(':')
            if len(splitted_mac) != 6:
                raise ValueError

            for octect in splitted_mac:
                if len(octect) != 2:
                    raise ValueError
        else:
            raise ValueError
    except ValueError:
        module.fail_json(msg='Invalid MAC address format', proposed_mac=proposed_mac)

    joined_mac = ''.join(splitted_mac)
    mac = [joined_mac[i:i + 4] for i in range(0, len(joined_mac), 4)]
    return '.'.join(mac).upper()


def main():
    argument_spec = dict(
        anycast_gateway_mac=dict(required=True, type='str'),
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)
    result = {'changed': False, 'commands': [], 'warnings': warnings}

    args = PARAM_TO_COMMAND_KEYMAP.keys()

    existing = get_existing(module, args)
    proposed = dict((k, v) for k, v in module.params.items()
                    if v is not None and k in args)

    candidate = CustomNetworkConfig(indent=3)
    get_commands(module, existing, proposed, candidate)

    if candidate:
        candidate = candidate.items_text()
        result['commands'] = candidate

        if not module.check_mode:
            load_config(module, candidate)
            result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
