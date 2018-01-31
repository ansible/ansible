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
module: nxos_vrf_interface
extends_documentation_fragment: nxos
version_added: "2.1"
short_description: Manages interface specific VRF configuration.
description:
    - Manages interface specific VRF configuration.
author:
    - Jason Edelman (@jedelman8)
    - Gabriele Gerbino (@GGabriele)
notes:
    - Tested against NXOSv 7.3.(0)D1(1) on VIRL
    - VRF needs to be added globally with M(nxos_vrf) before
      adding a VRF to an interface.
    - Remove a VRF from an interface will still remove
      all L3 attributes just as it does from CLI.
    - VRF is not read from an interface until IP address is
      configured on that interface.
options:
    vrf:
        description:
            - Name of VRF to be managed.
        required: true
    interface:
        description:
            - Full name of interface to be managed, i.e. Ethernet1/1.
        required: true
    state:
        description:
            - Manages desired state of the resource.
        required: false
        default: present
        choices: ['present','absent']
'''

EXAMPLES = '''
- name: Ensure vrf ntc exists on Eth1/1
  nxos_vrf_interface:
    vrf: ntc
    interface: Ethernet1/1
    state: present

- name: Ensure ntc VRF does not exist on Eth1/1
  nxos_vrf_interface:
    vrf: ntc
    interface: Ethernet1/1
    state: absent
'''

RETURN = '''
commands:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["interface loopback16", "vrf member ntc"]
'''
import re

from ansible.module_utils.network.nxos.nxos import load_config, run_commands
from ansible.module_utils.network.nxos.nxos import get_capabilities, nxos_argument_spec
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
    return run_commands(module, cmds)[0]


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


def get_interface_mode(interface, intf_type, module):
    command = 'show interface {0}'.format(interface)
    interface = {}
    mode = 'unknown'

    if intf_type in ['ethernet', 'portchannel']:
        body = execute_show_command(command, module)
        try:
            interface_table = body['TABLE_interface']['ROW_interface']
        except KeyError:
            return mode

        if interface_table and isinstance(interface_table, dict):
            mode = str(interface_table.get('eth_mode', 'layer3'))
            if mode == 'access' or mode == 'trunk':
                mode = 'layer2'
        else:
            return mode

    elif intf_type == 'loopback' or intf_type == 'svi':
        mode = 'layer3'
    return mode


def get_vrf_list(module):
    command = 'show vrf all'
    vrf_list = []
    body = execute_show_command(command, module)

    try:
        vrf_table = body['TABLE_vrf']['ROW_vrf']
    except (KeyError, AttributeError):
        return vrf_list

    for each in vrf_table:
        vrf_list.append(str(each['vrf_name']))

    return vrf_list


def get_interface_info(interface, module):
    if not interface.startswith('loopback'):
        interface = interface.capitalize()

    command = 'show run interface {0}'.format(interface)
    vrf_regex = r".*vrf\s+member\s+(?P<vrf>\S+).*"

    try:
        body = execute_show_command(command, module)
        match_vrf = re.match(vrf_regex, body, re.DOTALL)
        group_vrf = match_vrf.groupdict()
        vrf = group_vrf["vrf"]
    except (AttributeError, TypeError):
        return ""

    return vrf


def is_default(interface, module):
    command = 'show run interface {0}'.format(interface)

    try:
        body = execute_show_command(command, module)
        raw_list = body.split('\n')
        if raw_list[-1].startswith('interface'):
            return True
        else:
            return False

    except (KeyError, IndexError):
        return 'DNE'


def main():
    argument_spec = dict(
        vrf=dict(required=True),
        interface=dict(type='str', required=True),
        state=dict(default='present', choices=['present', 'absent'], required=False),
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    warnings = list()
    results = {'changed': False, 'commands': [], 'warnings': warnings}

    vrf = module.params['vrf']
    interface = module.params['interface'].lower()
    state = module.params['state']

    device_info = get_capabilities(module)
    network_api = device_info.get('network_api', 'nxapi')

    current_vrfs = get_vrf_list(module)
    if vrf not in current_vrfs:
        warnings.append("The VRF is not present/active on the device. "
                        "Use nxos_vrf to fix this.")

    intf_type = get_interface_type(interface)
    if (intf_type != 'ethernet' and network_api == 'cliconf'):
        if is_default(interface, module) == 'DNE':
            module.fail_json(msg="interface does not exist on switch. Verify "
                                 "switch platform or create it first with "
                                 "nxos_interface if it's a logical interface")

    mode = get_interface_mode(interface, intf_type, module)
    if mode == 'layer2':
        module.fail_json(msg='Ensure interface is a Layer 3 port before '
                             'configuring a VRF on an interface. You can '
                             'use nxos_interface')

    proposed = dict(interface=interface, vrf=vrf)

    current_vrf = get_interface_info(interface, module)
    existing = dict(interface=interface, vrf=current_vrf)
    changed = False
    end_state = existing

    if not existing['vrf']:
        pass
    elif vrf != existing['vrf'] and state == 'absent':
        module.fail_json(msg='The VRF you are trying to remove '
                             'from the interface does not exist '
                             'on that interface.',
                         interface=interface, proposed_vrf=vrf,
                         existing_vrf=existing['vrf'])

    commands = []
    if existing:
        if state == 'absent':
            if existing and vrf == existing['vrf']:
                command = 'no vrf member {0}'.format(vrf)
                commands.append(command)

        elif state == 'present':
            if existing['vrf'] != vrf:
                command = 'vrf member {0}'.format(vrf)
                commands.append(command)

    if commands:
        commands.insert(0, 'interface {0}'.format(interface))

    if commands:
        if module.check_mode:
            module.exit_json(changed=True, commands=commands)
        else:
            load_config(module, commands)
            changed = True
            changed_vrf = get_interface_info(interface, module)
            end_state = dict(interface=interface, vrf=changed_vrf)
            if 'configure' in commands:
                commands.pop(0)

    results['commands'] = commands
    results['changed'] = changed

    module.exit_json(**results)


if __name__ == '__main__':
    main()
