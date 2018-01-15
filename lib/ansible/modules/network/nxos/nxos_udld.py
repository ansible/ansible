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
    - When C(state=absent), it unconfigures existing settings C(msg_time) and set it
      to its default value of 15.  It is cleaner to always use C(state=present).
    - Module will fail if the udld feature has not been previously enabled.
options:
    aggressive:
        description:
            - Toggles aggressive mode.
        required: false
        default: null
        choices: ['enabled','disabled']
    msg_time:
        description:
            - Message time in seconds for UDLD packets.
        required: false
        default: null
    reset:
        description:
            - Ability to reset UDLD down interfaces.
        required: false
        default: null
        choices: ['true','false']
    state:
        description:
            - Manage the state of the resource.
        required: false
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
    type: boolean
    sample: true
'''

import re

from ansible.module_utils.network.nxos.nxos import get_config, load_config, run_commands
from ansible.module_utils.network.nxos.nxos import get_capabilities, nxos_argument_spec
from ansible.module_utils.basic import AnsibleModule


def execute_show_command(command, module, command_type='cli_show'):
    device_info = get_capabilities(module)
    network_api = device_info.get('network_api', 'nxapi')

    if network_api == 'cliconf':
        if 'show run' not in command:
            command += ' | json'
        cmds = [command]
        body = run_commands(module, cmds)
    elif network_api == 'nxapi':
        cmds = [command]
        body = run_commands(module, cmds)

    return body


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


def get_commands_config_udld_global(delta, reset):
    config_args = {
        'enabled': 'udld aggressive',
        'disabled': 'no udld aggressive',
        'msg_time': 'udld message-time {msg_time}'
    }
    commands = []
    for param, value in delta.items():
        if param == 'aggressive':
            if value == 'enabled':
                command = 'udld aggressive'
            elif value == 'disabled':
                command = 'no udld aggressive'
        else:
            command = config_args.get(param, 'DNE').format(**delta)
        if command and command != 'DNE':
            commands.append(command)
        command = None

    if reset:
        command = 'udld reset'
        commands.append(command)
    return commands


def get_commands_remove_udld_global(delta):
    config_args = {
        'aggressive': 'no udld aggressive',
        'msg_time': 'no udld message-time {msg_time}',
    }
    commands = []
    for param, value in delta.items():
        command = config_args.get(param, 'DNE').format(**delta)
        if command and command != 'DNE':
            commands.append(command)
        command = None
    return commands


def get_udld_global(module):
    command = 'show udld global'
    udld_table = execute_show_command(command, module)[0]

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
                           required_one_of=[['aggressive', 'msg_time', 'reset']],
                           supports_check_mode=True)

    warnings = list()

    aggressive = module.params['aggressive']
    msg_time = module.params['msg_time']
    reset = module.params['reset']
    state = module.params['state']

    if (aggressive or reset) and state == 'absent':
        module.fail_json(msg="It's better to use state=present when "
                             "configuring or unconfiguring aggressive mode "
                             "or using reset flag. state=absent is just for "
                             "when using msg_time param.")

    if msg_time:
        try:
            msg_time_int = int(msg_time)
            if msg_time_int < 7 or msg_time_int > 90:
                raise ValueError
        except ValueError:
            module.fail_json(msg='msg_time must be an integer'
                                 'between 7 and 90')

    args = dict(aggressive=aggressive, msg_time=msg_time, reset=reset)
    proposed = dict((k, v) for k, v in args.items() if v is not None)

    existing = get_udld_global(module)
    end_state = existing

    delta = set(proposed.items()).difference(existing.items())
    changed = False

    commands = []
    if state == 'present':
        if delta:
            command = get_commands_config_udld_global(dict(delta), reset)
            commands.append(command)

    elif state == 'absent':
        common = set(proposed.items()).intersection(existing.items())
        if common:
            command = get_commands_remove_udld_global(dict(common))
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
