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
                    'status': ['deprecated'],
                    'supported_by': 'network'}

DOCUMENTATION = '''
---
module: nxos_mtu
extends_documentation_fragment: nxos
version_added: "2.2"
deprecated: Deprecated in 2.3 use M(nxos_system)'s C(mtu) option.
short_description: Manages MTU settings on Nexus switch.
description:
    - Manages MTU settings on Nexus switch.
author:
    - Jason Edelman (@jedelman8)
notes:
    - Tested against NXOSv 7.3.(0)D1(1) on VIRL
    - Either C(sysmtu) param is required or (C(interface) AND C(mtu)) parameters are required.
    - C(state=absent) unconfigures a given MTU if that value is currently present.
options:
    interface:
        description:
            - Full name of interface, i.e. Ethernet1/1.
        required: false
        default: null
    mtu:
        description:
            - MTU for a specific interface. Must be an even number between 576 and 9216.
        required: false
        default: null
    sysmtu:
        description:
            - System jumbo MTU. Must be an even number between 576 and 9216.
        required: false
        default: null
    state:
        description:
            - Specify desired state of the resource.
        required: false
        default: present
        choices: ['present','absent']
'''

EXAMPLES = '''
# Ensure system mtu is 9126
- nxos_mtu:
    sysmtu: 9216
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"

# Config mtu on Eth1/1 (routed interface)
- nxos_mtu:
    interface: Ethernet1/1
    mtu: 1600
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"

# Config mtu on Eth1/3 (switched interface)
- nxos_mtu:
    interface: Ethernet1/3
    mtu: 9216
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"

# Unconfigure mtu on a given interface
- nxos_mtu:
    interface: Ethernet1/3
    mtu: 9216
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"
    state: absent
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"mtu": "1700"}
existing:
    description:
        - k/v pairs of existing mtu/sysmtu on the interface/system
    returned: always
    type: dict
    sample: {"mtu": "1600", "sysmtu": "9216"}
end_state:
    description: k/v pairs of mtu/sysmtu values after module execution
    returned: always
    type: dict
    sample: {"mtu": "1700", sysmtu": "9216"}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["interface vlan10", "mtu 1700"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''
from ansible.module_utils.network.nxos.nxos import load_config, run_commands
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule


def execute_show_command(command, module):
    if 'show run' not in command:
        output = 'json'
    else:
        output = 'text'
    cmds = [{
        'command': command,
        'output': output,
    }]

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


def get_mtu(interface, module):
    command = 'show interface {0}'.format(interface)
    mtu = {}

    body = execute_show_command(command, module)

    try:
        mtu_table = body[0]['TABLE_interface']['ROW_interface']
        mtu['mtu'] = str(
            mtu_table.get('eth_mtu',
                          mtu_table.get('svi_mtu', 'unreadable_via_api')))
        mtu['sysmtu'] = get_system_mtu(module)['sysmtu']
    except KeyError:
        mtu = {}

    return mtu


def get_system_mtu(module):
    command = 'show run all | inc jumbomtu'
    sysmtu = ''

    body = execute_show_command(command, module)

    if body:
        sysmtu = str(body[0].split(' ')[-1])
        try:
            sysmtu = int(sysmtu)
        except:
            sysmtu = ""

    return dict(sysmtu=str(sysmtu))


def get_commands_config_mtu(delta, interface):
    CONFIG_ARGS = {
        'mtu': 'mtu {mtu}',
        'sysmtu': 'system jumbomtu {sysmtu}',
    }

    commands = []
    for param, value in delta.items():
        command = CONFIG_ARGS.get(param, 'DNE').format(**delta)
        if command and command != 'DNE':
            commands.append(command)
        command = None
    mtu_check = delta.get('mtu', None)
    if mtu_check:
        commands.insert(0, 'interface {0}'.format(interface))
    return commands


def get_commands_remove_mtu(delta, interface):
    CONFIG_ARGS = {
        'mtu': 'no mtu {mtu}',
        'sysmtu': 'no system jumbomtu {sysmtu}',
    }
    commands = []
    for param, value in delta.items():
        command = CONFIG_ARGS.get(param, 'DNE').format(**delta)
        if command and command != 'DNE':
            commands.append(command)
        command = None
    mtu_check = delta.get('mtu', None)
    if mtu_check:
        commands.insert(0, 'interface {0}'.format(interface))
    return commands


def get_interface_type(interface):
    if interface.upper().startswith('ET'):
        return 'ethernet'
    elif interface.upper().startswith('VL'):
        return 'svi'
    elif interface.upper().startswith('LO'):
        return 'loopback'
    elif interface.upper().startswith('MG'):
        return 'management'
    elif interface.upper().startswith('MA'):
        return 'management'
    elif interface.upper().startswith('PO'):
        return 'portchannel'
    else:
        return 'unknown'


def is_default(interface, module):
    command = 'show run interface {0}'.format(interface)

    try:
        body = execute_show_command(command, module)[0]
        if body == 'DNE':
            return 'DNE'
        else:
            raw_list = body.split('\n')
            if raw_list[-1].startswith('interface'):
                return True
            else:
                return False
    except (KeyError):
        return 'DNE'


def get_interface_mode(interface, intf_type, module):
    command = 'show interface {0}'.format(interface)
    mode = 'unknown'
    interface_table = {}
    body = execute_show_command(command, module)

    try:
        interface_table = body[0]['TABLE_interface']['ROW_interface']
    except (KeyError, AttributeError, IndexError):
        return mode

    if intf_type in ['ethernet', 'portchannel']:
        mode = str(interface_table.get('eth_mode', 'layer3'))
        if mode in ['access', 'trunk']:
            mode = 'layer2'
        elif mode == 'routed':
            mode = 'layer3'
    elif intf_type in ['loopback', 'svi']:
        mode = 'layer3'
    return mode


def main():
    argument_spec = dict(
        mtu=dict(type='str'),
        interface=dict(type='str'),
        sysmtu=dict(type='str'),
        state=dict(choices=['absent', 'present'], default='present'),
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           required_together=[['mtu', 'interface']],
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    interface = module.params['interface']
    mtu = module.params['mtu']
    sysmtu = module.params['sysmtu']
    state = module.params['state']

    if sysmtu and (interface or mtu):
        module.fail_json(msg='Proper usage-- either just use the sysmtu param '
                             'or use interface AND mtu params')

    if interface:
        intf_type = get_interface_type(interface)
        if intf_type != 'ethernet':
            if is_default(interface, module) == 'DNE':
                module.fail_json(msg='Invalid interface.  It does not exist '
                                     'on the switch.')

        existing = get_mtu(interface, module)
    else:
        existing = get_system_mtu(module)

    if interface and mtu:
        if intf_type == 'loopback':
            module.fail_json(msg='Cannot set MTU for loopback interface.')
        mode = get_interface_mode(interface, intf_type, module)
        if mode == 'layer2':
            if intf_type in ['ethernet', 'portchannel']:
                if mtu not in [existing['sysmtu'], '1500']:
                    module.fail_json(msg='MTU on L2 interfaces can only be set'
                                         ' to the system default (1500) or '
                                         'existing sysmtu value which is '
                                         ' {0}'.format(existing['sysmtu']))
        elif mode == 'layer3':
            if intf_type in ['ethernet', 'portchannel', 'svi']:
                if ((int(mtu) < 576 or int(mtu) > 9216) or
                        ((int(mtu) % 2) != 0)):
                    module.fail_json(msg='Invalid MTU for Layer 3 interface'
                                         'needs to be an even number between'
                                         '576 and 9216')
    if sysmtu:
        if ((int(sysmtu) < 576 or int(sysmtu) > 9216 or
                ((int(sysmtu) % 2) != 0))):
            module.fail_json(msg='Invalid MTU- needs to be an even '
                                 'number between 576 and 9216')

    args = dict(mtu=mtu, sysmtu=sysmtu)
    proposed = dict((k, v) for k, v in args.items() if v is not None)
    delta = dict(set(proposed.items()).difference(existing.items()))

    changed = False
    end_state = existing
    commands = []

    if state == 'present':
        if delta:
            command = get_commands_config_mtu(delta, interface)
            commands.append(command)

    elif state == 'absent':
        common = set(proposed.items()).intersection(existing.items())
        if common:
            command = get_commands_remove_mtu(dict(common), interface)
            commands.append(command)

    cmds = flatten_list(commands)
    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            changed = True
            load_config(module, cmds)
            if interface:
                end_state = get_mtu(interface, module)
            else:
                end_state = get_system_mtu(module)
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
