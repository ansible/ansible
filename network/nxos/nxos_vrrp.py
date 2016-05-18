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

module: nxos_vrrp
version_added: "2.1"
short_description: Manages VRRP configuration on NX-OS switches
description:
    - Manages VRRP configuration on NX-OS switches
extends_documentation_fragment: nxos
author: Jason Edelman (@jedelman8), Gabriele Gerbino (@GGabriele)
notes:
    - VRRP feature needs to be enabled first on the system
    - SVIs must exist before using this module
    - Interface must be a L3 port before using this module
    - state=absent removes the vrrp group if it exists on the device
    - VRRP cannot be configured on loopback interfaces
options:
    group:
        description:
            - vrrp group number
        required: true
    interface:
        description:
            - Full name of interface that is being managed for vrrp
        required: true
    priority:
        description:
            - vrrp priority
        required: false
        default: null
    vip:
        description:
            - hsrp virtual IP address
        required: false
        default: null
    authentication:
        description:
            - clear text authentication string
        required: false
        default: null
    state:
        description:
            - Specify desired state of the resource
        required: false
        default: present
        choices: ['present','absent']
'''

EXAMPLES = '''

# ensure vrrp group 100 and vip 10.1.100.1 is on vlan10
- nxos_vrrp: interface=vlan10 group=100 vip=10.1.100.1 host={{ inventory_hostname }}

# ensure removal of the vrrp group config # vip is required to ensure the user knows what they are removing
- nxos_vrrp: interface=vlan10 group=100 vip=10.1.100.1 state=absent host={{ inventory_hostname }}

# re-config with more params
- nxos_vrrp: interface=vlan10 group=100 vip=10.1.100.1 preempt=false priority=130 authentication=AUTHKEY host={{ inventory_hostname }}

'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"authentication": "testing", "group": "150", "vip": "10.1.15.1"}
existing:
    description: k/v pairs of existing vrrp info on the interface
    type: dict
    sample: {}
end_state:
    description: k/v pairs of vrrp after module execution
    returned: always
    type: dict
    sample: {"authentication": "testing", "group": "150", "interval": "1",
            "preempt": true, "priority": "100", "vip": "10.1.15.1"}
state:
    description: state as sent in from the playbook
    returned: always
    type: string
    sample: "present"
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["interface vlan10", "vrrp 150", "address 10.1.15.1",
            "authentication text testing"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''


def execute_config_command(commands, module):
    try:
        module.configure(commands)
    except ShellError:
        clie = get_exception()
        module.fail_json(msg='Error sending CLI commands',
                         error=str(clie), commands=commands)


def get_cli_body_ssh_vrrp(command, response, module):
    """Get response for when transport=cli.  This is kind of a hack and mainly
    needed because these modules were originally written for NX-API.  And
    not every command supports "| json" when using cli/ssh.  As such, we assume
    if | json returns an XML string, it is a valid command, but that the
    resource doesn't exist yet. Instead, the output will be a raw string
    when issuing commands containing 'show run'.
    """
    if 'xml' in response[0]:
        body = []
    elif 'show run' in command:
        body = response
    else:
        try:
            response = response[0].replace(command + '\n\n', '').strip()
            body = [json.loads(response)]
        except ValueError:
            module.fail_json(msg='Command does not support JSON output',
                             command=command)
    return body


def execute_show(cmds, module, command_type=None):
    try:
        if command_type:
            response = module.execute(cmds, command_type=command_type)
        else:
            response = module.execute(cmds)
    except ShellError:
        clie = get_exception()
        module.fail_json(msg='Error sending {0}'.format(command),
                         error=str(clie))
    return response


def execute_show_command(command, module, command_type='cli_show'):
    if module.params['transport'] == 'cli':
        command += ' | json'
        cmds = [command]
        response = execute_show(cmds, module)
        body = get_cli_body_ssh_vrrp(command, response, module)
    elif module.params['transport'] == 'nxapi':
        cmds = [command]
        body = execute_show(cmds, module, command_type=command_type)

    return body


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
        if 'invalid' in body.lower():
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
    interface = {}
    mode = 'unknown'

    if intf_type in ['ethernet', 'portchannel']:
        body = execute_show_command(command, module)[0]
        interface_table = body['TABLE_interface']['ROW_interface']
        mode = str(interface_table.get('eth_mode', 'layer3'))
        if mode == 'access' or mode == 'trunk':
            mode = 'layer2'
    elif intf_type == 'svi':
        mode = 'layer3'
    return mode


def get_existing_vrrp(interface, group, module):
    command = 'show vrrp detail interface {0}'.format(interface)
    body = execute_show_command(command, module)
    vrrp = {}

    vrrp_key = {
        'sh_group_id': 'group',
        'sh_vip_addr': 'vip',
        'sh_priority': 'priority',
        'sh_group_preempt': 'preempt',
        'sh_auth_text': 'authentication',
        'sh_adv_interval': 'interval'
    }

    try:
        vrrp_table = body[0]['TABLE_vrrp_group']
    except (AttributeError, IndexError, TypeError):
        return {}

    if isinstance(vrrp_table, dict):
        vrrp_table = [vrrp_table]

    for each_vrrp in vrrp_table:
        vrrp_row = each_vrrp['ROW_vrrp_group']
        parsed_vrrp = apply_key_map(vrrp_key, vrrp_row)

        if parsed_vrrp['preempt'] == 'Disable':
            parsed_vrrp['preempt'] = False
        elif parsed_vrrp['preempt'] == 'Enable':
            parsed_vrrp['preempt'] = True

        if parsed_vrrp['group'] == group:
            return parsed_vrrp
    return vrrp


def get_commands_config_vrrp(delta, group):
    commands = []

    CMDS = {
        'priority': 'priority {0}',
        'preempt': 'preempt',
        'vip': 'address {0}',
        'interval': 'advertisement-interval {0}',
        'auth': 'authentication text {0}'
    }

    vip = delta.get('vip')
    priority = delta.get('priority')
    preempt = delta.get('preempt')
    interval = delta.get('interval')
    auth = delta.get('authentication')

    if vip:
        commands.append((CMDS.get('vip')).format(vip))
    if priority:
        commands.append((CMDS.get('priority')).format(priority))
    if preempt:
        commands.append(CMDS.get('preempt'))
    elif preempt is False:
        commands.append('no ' + CMDS.get('preempt'))
    if interval:
        commands.append((CMDS.get('interval')).format(interval))
    if auth:
        commands.append((CMDS.get('auth')).format(auth))

    commands.insert(0, 'vrrp {0}'.format(group))

    return commands


def flatten_list(command_lists):
    flat_command_list = []
    for command in command_lists:
        if isinstance(command, list):
            flat_command_list.extend(command)
        else:
            flat_command_list.append(command)
    return flat_command_list


def validate_params(param, module):
    value = module.params[param]

    if param == 'group':
        try:
            if (int(value) < 1 or int(value) > 255):
                raise ValueError
        except ValueError:
            module.fail_json(msg="Warning! 'group' must be an integer between"
                                 " 1 and 255", group=value)
    elif param == 'priority':
        try:
            if (int(value) < 1 or int(value) > 254):
                raise ValueError
        except ValueError:
            module.fail_json(msg="Warning! 'priority' must be an integer "
                                 "between 1 and 254", priority=value)


def main():
    argument_spec = dict(
            group=dict(required=True, type='str'),
            interface=dict(required=True),
            priority=dict(required=False, type='str'),
            preempt=dict(required=False, choices=BOOLEANS, type='bool'),
            vip=dict(required=False, type='str'),
            authentication=dict(required=False, type='str'),
            state=dict(choices=['absent', 'present'],
                       required=False, default='present'),
    )
    module = get_module(argument_spec=argument_spec,
                        supports_check_mode=True)

    state = module.params['state']
    interface = module.params['interface'].lower()
    group = module.params['group']
    priority = module.params['priority']
    preempt = module.params['preempt']
    vip = module.params['vip']
    authentication = module.params['authentication']

    transport = module.params['transport']

    if state == 'present' and not vip:
        module.fail_json(msg='the "vip" param is required when state=present')

    intf_type = get_interface_type(interface)
    if (intf_type != 'ethernet' and transport == 'cli'):
        if is_default(interface, module) == 'DNE':
            module.fail_json(msg='That interface does not exist yet. Create '
                                 'it first.', interface=interface)
        if intf_type == 'loopback':
            module.fail_json(msg="Loopback interfaces don't support VRRP.",
                             interface=interface)

    mode = get_interface_mode(interface, intf_type, module)
    if mode == 'layer2':
        module.fail_json(msg='That interface is a layer2 port.\nMake it '
                             'a layer 3 port first.', interface=interface)

    args = dict(group=group, priority=priority, preempt=preempt,
                vip=vip, authentication=authentication)

    proposed = dict((k, v) for k, v in args.iteritems() if v is not None)
    existing = get_existing_vrrp(interface, group, module)

    changed = False
    end_state = existing
    commands = []

    if state == 'present':
        delta = dict(
            set(proposed.iteritems()).difference(existing.iteritems()))
        if delta:
            command = get_commands_config_vrrp(delta, group)
            commands.append(command)

    elif state == 'absent':
        if existing:
            commands.append(['no vrrp {0}'.format(group)])

    if commands:
        commands.insert(0, ['interface {0}'.format(interface)])

    cmds = flatten_list(commands)
    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            execute_config_command(cmds, module)
            changed = True
            end_state = get_existing_vrrp(interface, group, module)

    results = {}
    results['proposed'] = proposed
    results['existing'] = existing
    results['state'] = state
    results['updates'] = cmds
    results['changed'] = changed
    results['end_state'] = end_state

    module.exit_json(**results)


from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
from ansible.module_utils.shell import *
from ansible.module_utils.netcfg import *
from ansible.module_utils.nxos import *
if __name__ == '__main__':
    main()
