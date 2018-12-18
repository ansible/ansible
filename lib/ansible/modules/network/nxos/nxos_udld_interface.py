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
module: nxos_udld_interface
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages UDLD interface configuration params.
description:
    - Manages UDLD interface configuration params.
author:
    - Jason Edelman (@jedelman8)
notes:
    - Tested against NXOSv 7.3.(0)D1(1) on VIRL
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
    type: bool
    sample: true
'''


from ansible.module_utils.network.nxos.nxos import load_config, run_commands
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec
from ansible.module_utils.basic import AnsibleModule


def flatten_list(command_lists):
    flat_command_list = []
    for command in command_lists:
        if isinstance(command, list):
            flat_command_list.extend(command)
        else:
            flat_command_list.append(command)
    return flat_command_list


def get_udld_interface(module, interface):
    command = 'show run udld all | section ' + interface.title() + '$'
    interface_udld = {}
    mode = None
    mode_str = None
    try:
        body = run_commands(module, [{'command': command, 'output': 'text'}])[0]
        if 'aggressive' in body:
            mode = 'aggressive'
            mode_str = 'aggressive'
        elif 'no udld enable' in body:
            mode = 'disabled'
            mode_str = 'no udld enable'
        elif 'no udld disable' in body:
            mode = 'enabled'
            mode_str = 'no udld disable'
        elif 'udld disable' in body:
            mode = 'disabled'
            mode_str = 'udld disable'
        elif 'udld enable' in body:
            mode = 'enabled'
            mode_str = 'udld enable'
        interface_udld['mode'] = mode

    except (KeyError, AttributeError, IndexError):
        interface_udld = {}

    return interface_udld, mode_str


def get_commands_config_udld_interface1(delta, interface, module, existing):
    commands = []
    mode = delta['mode']
    if mode == 'aggressive':
        commands.append('udld aggressive')
    else:
        commands.append('no udld aggressive')
    commands.insert(0, 'interface {0}'.format(interface))

    return commands


def get_commands_config_udld_interface2(delta, interface, module, existing):
    commands = []
    existing, mode_str = get_udld_interface(module, interface)
    mode = delta['mode']
    if mode == 'enabled':
        if mode_str == 'no udld enable':
            command = 'udld enable'
        else:
            command = 'no udld disable'
    else:
        if mode_str == 'no udld disable':
            command = 'udld disable'
        else:
            command = 'no udld enable'
    if command:
        commands.append(command)
        commands.insert(0, 'interface {0}'.format(interface))

    return commands


def get_commands_remove_udld_interface(delta, interface, module, existing):
    commands = []
    existing, mode_str = get_udld_interface(module, interface)

    mode = delta['mode']
    if mode == 'aggressive':
        command = 'no udld aggressive'
    else:
        if mode == 'enabled':
            if mode_str == 'udld enable':
                command = 'no udld enable'
            else:
                command = 'udld disable'
        elif mode == 'disabled':
            if mode_str == 'no udld disable':
                command = 'udld disable'
            else:
                command = 'no udld enable'
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

    interface = module.params['interface'].lower()
    mode = module.params['mode']
    state = module.params['state']

    proposed = dict(mode=mode)
    existing, mode_str = get_udld_interface(module, interface)
    end_state = existing

    delta = dict(set(proposed.items()).difference(existing.items()))

    changed = False
    commands = []
    cmds = []
    if state == 'present':
        if delta:
            command = get_commands_config_udld_interface1(delta, interface,
                                                          module, existing)
            commands.append(command)
            cmds = flatten_list(commands)
            if module.check_mode:
                module.exit_json(changed=True, commands=cmds)
            else:
                changed = True
                load_config(module, cmds)

            if delta['mode'] == 'enabled' or delta['mode'] == 'disabled':
                commands = []
                command = get_commands_config_udld_interface2(delta, interface,
                                                              module, existing)
                commands.append(command)
                cmds = flatten_list(commands)
                if module.check_mode:
                    module.exit_json(changed=True, commands=cmds)
                else:
                    load_config(module, cmds)

    else:
        common = set(proposed.items()).intersection(existing.items())
        if common:
            command = get_commands_remove_udld_interface(
                dict(common), interface, module, existing
            )
            cmds = flatten_list(commands)
            if module.check_mode:
                module.exit_json(changed=True, commands=cmds)
            else:
                changed = True
                load_config(module, cmds)

    if not module.check_mode:
        end_state, mode_str = get_udld_interface(module, interface)
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
