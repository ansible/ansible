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
module: nxos_udld
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages UDLD global configuration params.
description:
    - Manages UDLD global configuration params.
author:
    - Jason Edelman (@jedelman8)
notes:
    - Tested against NXOSv 7.3.(0)D1(1) on VIRL
    - Module will fail if the udld feature has not been previously enabled.
options:
    aggressive:
        description:
            - Toggles aggressive mode.
        choices: ['enabled','disabled']
    msg_time:
        description:
            - Message time in seconds for UDLD packets or keyword 'default'.
    reset:
        description:
            - Ability to reset all ports shut down by UDLD. 'state' parameter
              cannot be 'absent' when this is present.
        type: bool
        default: 'no'
    state:
        description:
            - Manage the state of the resource. When set to 'absent',
              aggressive and msg_time are set to their default values.
        default: present
        choices: ['present','absent']

'''
EXAMPLES = '''
# ensure udld aggressive mode is globally disabled and se global message interval is 20
- nxos_udld:
    aggressive: disabled
    msg_time: 20
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"

# Ensure agg mode is globally enabled and msg time is 15
- nxos_udld:
    aggressive: enabled
    msg_time: 15
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"aggressive": "enabled", "msg_time": "40"}
existing:
    description:
        - k/v pairs of existing udld configuration
    returned: always
    type: dict
    sample: {"aggressive": "disabled", "msg_time": "15"}
end_state:
    description: k/v pairs of udld configuration after module execution
    returned: always
    type: dict
    sample: {"aggressive": "enabled", "msg_time": "40"}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["udld message-time 40", "udld aggressive"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: bool
    sample: true
'''

import re

from ansible.module_utils.network.nxos.nxos import get_config, load_config, run_commands
from ansible.module_utils.network.nxos.nxos import get_capabilities, nxos_argument_spec
from ansible.module_utils.basic import AnsibleModule


PARAM_TO_DEFAULT_KEYMAP = {
    'msg_time': '15',
}


def flatten_list(command_lists):
    flat_command_list = []
    for command in command_lists:
        if isinstance(command, list):
            flat_command_list.extend(command)
        else:
            flat_command_list.append(command)
    return flat_command_list


def apply_key_map(key_map, table):
    new_dict = {}
    for key, value in table.items():
        new_key = key_map.get(key)
        if new_key:
            value = table.get(key)
            if value:
                new_dict[new_key] = str(value)
            else:
                new_dict[new_key] = value
    return new_dict


def get_commands_config_udld_global(delta, reset, existing):
    commands = []
    for param, value in delta.items():
        if param == 'aggressive':
            command = 'udld aggressive' if value == 'enabled' else 'no udld aggressive'
            commands.append(command)
        elif param == 'msg_time':
            if value == 'default':
                if existing.get('msg_time') != PARAM_TO_DEFAULT_KEYMAP.get('msg_time'):
                    commands.append('no udld message-time')
            else:
                commands.append('udld message-time ' + value)
    if reset:
        command = 'udld reset'
        commands.append(command)
    return commands


def get_commands_remove_udld_global(existing):
    commands = []
    if existing.get('aggressive') == 'enabled':
        command = 'no udld aggressive'
        commands.append(command)
    if existing.get('msg_time') != PARAM_TO_DEFAULT_KEYMAP.get('msg_time'):
        command = 'no udld message-time'
        commands.append(command)
    return commands


def get_udld_global(module):
    command = 'show udld global | json'
    udld_table = run_commands(module, [command])[0]

    status = str(udld_table.get('udld-global-mode', None))
    if status == 'enabled-aggressive':
        aggressive = 'enabled'
    else:
        aggressive = 'disabled'

    interval = str(udld_table.get('message-interval', None))
    udld = dict(msg_time=interval, aggressive=aggressive)

    return udld


def main():
    argument_spec = dict(
        aggressive=dict(required=False, choices=['enabled', 'disabled']),
        msg_time=dict(required=False, type='str'),
        reset=dict(required=False, type='bool'),
        state=dict(choices=['absent', 'present'], default='present'),
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    warnings = list()

    aggressive = module.params['aggressive']
    msg_time = module.params['msg_time']
    reset = module.params['reset']
    state = module.params['state']

    if reset and state == 'absent':
        module.fail_json(msg="state must be present when using reset flag.")

    args = dict(aggressive=aggressive, msg_time=msg_time, reset=reset)
    proposed = dict((k, v) for k, v in args.items() if v is not None)

    existing = get_udld_global(module)
    end_state = existing

    delta = set(proposed.items()).difference(existing.items())
    changed = False

    commands = []
    if state == 'present':
        if delta:
            command = get_commands_config_udld_global(dict(delta), reset, existing)
            commands.append(command)

    elif state == 'absent':
        command = get_commands_remove_udld_global(existing)
        if command:
            commands.append(command)

    cmds = flatten_list(commands)
    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            changed = True
            load_config(module, cmds)
            end_state = get_udld_global(module)
            if 'configure' in cmds:
                cmds.pop(0)

    results = {}
    results['proposed'] = proposed
    results['existing'] = existing
    results['end_state'] = end_state
    results['updates'] = cmds
    results['changed'] = changed
    results['warnings'] = warnings

    module.exit_json(**results)


if __name__ == '__main__':
    main()
