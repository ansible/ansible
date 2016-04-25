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

DOCUMENTATION = '''
---
module: nxos_vrf_interface
version_added: "2.1"
short_description: Manages interface specific VRF configuration
description:
    - Manages interface specific VRF configuration
extends_documentation_fragment: nxos
author: Jason Edelman (@jedelman8), Gabriele Gerbino (@GGabriele)
notes:
    - VRF needs to be added globally with M(nxos_vrf) before
      adding a VRF to an interface
    - Remove a VRF from an interface will still remove
      all L3 attributes just as it does from CLI
    - VRF is not read from an interface until IP address is
      configured on that interface
options:
    vrf:
        description:
            - Name of VRF to be managed
        required: true
    interface:
        description:
            - Full name of interface to be managed, i.e. Ethernet1/1
        required: true
    state:
        description:
            - Manages desired state of the resource
        required: false
        default: present
        choices: ['present','absent']
'''

EXAMPLES = '''
# ensure vrf ntc exists on Eth1/1
- nxos_vrf_interface: vrf=ntc interface=Ethernet1/1 host={{ inventory_hostname }} state=present
# ensure ntc VRF does not exist on Eth1/1
- nxos_vrf_interface: vrf=ntc interface=Ethernet1/1 host={{ inventory_hostname }} state=absent
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"interface": "loopback16", "vrf": "ntc"}
existing:
    description: k/v pairs of existing vrf on the interface
    type: dict
    sample: {"interface": "loopback16", "vrf": ""}
end_state:
    description: k/v pairs of vrf after module execution
    returned: always
    type: dict
    sample: {"interface": "loopback16", "vrf": "ntc"}
state:
    description: state as sent in from the playbook
    returned: always
    type: string
    sample: "present"
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["interface loopback16", "vrf member ntc"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''


def execute_config_command(commands, module):
    try:
        module.configure(commands)
    except ShellError, clie:
        module.fail_json(msg='Error sending CLI commands',
                         error=str(clie), commands=commands)


def get_cli_body_ssh_vrf_interface(command, response, module):
    """Get response for when transport=cli.  This is kind of a hack and mainly
    needed because these modules were originally written for NX-API. As such,
    we assume if '^' is found in response, it is an invalid command. Instead,
    the output will be a raw string when issuing commands containing 'show run'.
    """
    if '^' in response[0]:
        body = []
    elif 'show run' in command:
        body = response
    else:
        body = [json.loads(response[0])]
    return body


def execute_show(cmds, module, command_type=None):
    try:
        if command_type:
            response = module.execute(cmds, command_type=command_type)
        else:
            response = module.execute(cmds)
    except ShellError, clie:
        module.fail_json(msg='Error sending {0}'.format(command),
                         error=str(clie))
    return response


def execute_show_command(command, module, command_type='cli_show'):
    if module.params['transport'] == 'cli':
        command += ' | json'
        cmds = [command]
        response = execute_show(cmds, module)
        body = get_cli_body_ssh_vrf_interface(command, response, module)
    elif module.params['transport'] == 'nxapi':
        cmds = [command]
        body = execute_show(cmds, module, command_type=command_type)

    return body


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
        body = execute_show_command(command, module)[0]
        interface_table = body['TABLE_interface']['ROW_interface']
        mode = str(interface_table.get('eth_mode', 'layer3'))
        if mode == 'access' or mode == 'trunk':
            mode = 'layer2'
    elif intf_type == 'loopback' or intf_type == 'svi':
        mode = 'layer3'
    return mode


def get_vrf_list(module):
    command = 'show vrf all'
    vrf_list = []
    body = execute_show_command(command, module)[0]

    try:
        vrf_table = body['TABLE_vrf']['ROW_vrf']
    except (KeyError, AttributeError):
        return vrf_list

    for each in vrf_table:
        vrf_list.append(str(each['vrf_name']))

    return vrf_list


def get_interface_info(interface, module):
    command = 'show run interface {0}'.format(interface)
    vrf_regex = ".*vrf\s+member\s+(?P<vrf>\S+).*"

    try:
        body = execute_show_command(command, module,
                                    command_type='cli_show_ascii')[0]

        match_vrf = re.match(vrf_regex, body, re.DOTALL)
        group_vrf = match_vrf.groupdict()
        vrf = group_vrf["vrf"]
    except AttributeError:
        return ""

    return vrf


def is_default(interface, module):
    command = 'show run interface {0}'.format(interface)

    try:
        body = execute_show_command(command, module,
                                    command_type='cli_show_ascii')[0]
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
            state=dict(default='present', choices=['present', 'absent'],
                       required=False),
    )
    module = get_module(argument_spec=argument_spec,
                        supports_check_mode=True)

    vrf = module.params['vrf']
    interface = module.params['interface'].lower()
    state = module.params['state']

    current_vrfs = get_vrf_list(module)
    if vrf not in current_vrfs:
        module.fail_json(msg="Ensure the VRF you're trying to config/remove on"
                             " an interface is created globally on the device"
                             " first.")

    intf_type = get_interface_type(interface)
    if (intf_type != 'ethernet' and module.params['transport'] == 'cli'):
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

    if vrf != existing['vrf'] and state == 'absent':
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
            execute_config_command(commands, module)
            changed = True
            changed_vrf = get_interface_info(interface, module)
            end_state = dict(interface=interface, vrf=changed_vrf)

    results = {}
    results['proposed'] = proposed
    results['existing'] = existing
    results['end_state'] = end_state
    results['state'] = state
    results['updates'] = commands
    results['changed'] = changed

    module.exit_json(**results)


from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
from ansible.module_utils.shell import *
from ansible.module_utils.netcfg import *
from ansible.module_utils.nxos import *
if __name__ == '__main__':
    main()
