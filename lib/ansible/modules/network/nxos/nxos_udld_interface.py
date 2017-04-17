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
module: nxos_udld_interface
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages UDLD interface configuration params.
description:
    - Manages UDLD interface configuration params.
author:
    - Jason Edelman (@jedelman8)
notes:
    - Feature UDLD must be enabled on the device to use this module.
options:
    mode:
        description:
            - Manages UDLD mode for an interface.
        required: true
        choices: ['enabled','disabled','aggressive']
    interface:
        description:
            - FULL name of the interface, i.e. Ethernet1/1-
        required: true
    state:
        description:
            - Manage the state of the resource.
        required: false
        default: present
        choices: ['present','absent']
'''
EXAMPLES = '''
# ensure Ethernet1/1 is configured to be in aggressive mode
- nxos_udld_interface:
    interface: Ethernet1/1
    mode: aggressive
    state: present
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"

# Remove the aggressive config only if it's currently in aggressive mode and then disable udld (switch default)
- nxos_udld_interface:
    interface: Ethernet1/1
    mode: aggressive
    state: absent
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"

# ensure Ethernet1/1 has aggressive mode enabled
- nxos_udld_interface:
    interface: Ethernet1/1
    mode: enabled
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"mode": "enabled"}
existing:
    description:
        - k/v pairs of existing configuration
    returned: always
    type: dict
    sample: {"mode": "aggressive"}
end_state:
    description: k/v pairs of configuration after module execution
    returned: always
    type: dict
    sample: {"mode": "enabled"}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["interface ethernet1/33",
            "no udld aggressive ; no udld disable"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''


from ansible.module_utils.nxos import get_config, load_config, run_commands
from ansible.module_utils.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule


import re
import re


def execute_show_command(command, module, command_type='cli_show'):
    if module.params['transport'] == 'cli':
        if 'show run' not in command:
            command += ' | json'
        cmds = [command]
        body = run_commands(module, cmds)
    elif module.params['transport'] == 'nxapi':
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


def get_udld_interface(module, interface):
    command = 'show udld {0}'.format(interface)
    interface_udld = {}
    mode = None
    try:
        body = execute_show_command(command, module)[0]
        table = body['TABLE_interface']['ROW_interface']

        status = str(table.get('mib-port-status', None))
        # Note: 'mib-aggresive-mode' is NOT a typo
        agg = str(table.get('mib-aggresive-mode', 'disabled'))

        if agg == 'enabled':
            mode = 'aggressive'
        else:
            mode = status

        interface_udld['mode'] = mode

    except (KeyError, AttributeError, IndexError):
        interface_udld = {}

    return interface_udld


def is_interface_copper(module, interface):
    command = 'show interface status'
    copper = []
    try:
        body = execute_show_command(command, module)[0]
        table = body['TABLE_interface']['ROW_interface']
        for each in table:
            itype = each.get('type', 'DNE')
            if 'CU' in itype or '1000' in itype or '10GBaseT' in itype:
                copper.append(str(each['interface'].lower()))
    except (KeyError, AttributeError):
        pass

    if interface in copper:
        found = True
    else:
        found = False

    return found


def get_commands_config_udld_interface(delta, interface, module, existing):
    commands = []
    copper = is_interface_copper(module, interface)
    if delta:
        mode = delta['mode']
        if mode == 'aggressive':
            command = 'udld aggressive'
        elif copper:
            if mode == 'enabled':
                if existing['mode'] == 'aggressive':
                    command = 'no udld aggressive ; udld enable'
                else:
                    command = 'udld enable'
            elif mode == 'disabled':
                command = 'no udld enable'
        elif not copper:
            if mode == 'enabled':
                if existing['mode'] == 'aggressive':
                    command = 'no udld aggressive ; no udld disable'
                else:
                    command = 'no udld disable'
            elif mode == 'disabled':
                command = 'udld disable'
    if command:
        commands.append(command)
        commands.insert(0, 'interface {0}'.format(interface))

    return commands


def get_commands_remove_udld_interface(delta, interface, module, existing):
    commands = []
    copper = is_interface_copper(module, interface)

    if delta:
        mode = delta['mode']
        if mode == 'aggressive':
            command = 'no udld aggressive'
        elif copper:
            if mode == 'enabled':
                command = 'no udld enable'
            elif mode == 'disabled':
                command = 'udld enable'
        elif not copper:
            if mode == 'enabled':
                command = 'udld disable'
            elif mode == 'disabled':
                command = 'no udld disable'
    if command:
        commands.append(command)
        commands.insert(0, 'interface {0}'.format(interface))

    return commands


def main():
    argument_spec = dict(
        mode=dict(choices=['enabled', 'disabled', 'aggressive'],
                      required=True),
        interface=dict(type='str', required=True),
        state=dict(choices=['absent', 'present'], default='present'),
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                                supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)


    interface = module.params['interface'].lower()
    mode = module.params['mode']
    state = module.params['state']

    proposed = dict(mode=mode)
    existing = get_udld_interface(module, interface)
    end_state = existing

    delta = dict(set(proposed.items()).difference(existing.items()))

    changed = False
    commands = []
    if state == 'present':
        if delta:
            command = get_commands_config_udld_interface(delta, interface,
                                                         module, existing)
            commands.append(command)
    elif state == 'absent':
        common = set(proposed.items()).intersection(existing.items())
        if common:
            command = get_commands_remove_udld_interface(
                dict(common), interface, module, existing
                )
            commands.append(command)

    cmds = flatten_list(commands)
    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            changed = True
            load_config(module, cmds)
            end_state = get_udld_interface(module, interface)
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

