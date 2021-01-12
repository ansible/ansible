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
module: nxos_vrrp
extends_documentation_fragment: nxos
version_added: "2.1"
short_description: Manages VRRP configuration on NX-OS switches.
description:
    - Manages VRRP configuration on NX-OS switches.
author:
    - Jason Edelman (@jedelman8)
    - Gabriele Gerbino (@GGabriele)
notes:
    - Tested against NXOSv 7.3.(0)D1(1) on VIRL
    - VRRP feature needs to be enabled first on the system.
    - SVIs must exist before using this module.
    - Interface must be a L3 port before using this module.
    - C(state=absent) removes the VRRP group if it exists on the device.
    - VRRP cannot be configured on loopback interfaces.
options:
    group:
        description:
            - VRRP group number.
        required: true
    interface:
        description:
            - Full name of interface that is being managed for VRRP.
        required: true
    interval:
        description:
            - Time interval between advertisement or 'default' keyword
        required: false
        default: 1
        version_added: 2.6
    priority:
        description:
            - VRRP priority or 'default' keyword
        default: 100
    preempt:
        description:
            - Enable/Disable preempt.
        type: bool
        default: 'yes'
    vip:
        description:
            - VRRP virtual IP address or 'default' keyword
    authentication:
        description:
            - Clear text authentication string or 'default' keyword
    admin_state:
        description:
            - Used to enable or disable the VRRP process.
        choices: ['shutdown', 'no shutdown', 'default']
        default: shutdown
    state:
        description:
            - Specify desired state of the resource.
        default: present
        choices: ['present','absent']
'''

EXAMPLES = '''
- name: Ensure vrrp group 100 and vip 10.1.100.1 is on vlan10
  nxos_vrrp:
    interface: vlan10
    group: 100
    vip: 10.1.100.1

- name: Ensure removal of the vrrp group config
  # vip is required to ensure the user knows what they are removing
  nxos_vrrp:
    interface: vlan10
    group: 100
    vip: 10.1.100.1
    state: absent

- name: Re-config with more params
  nxos_vrrp:
    interface: vlan10
    group: 100
    vip: 10.1.100.1
    preempt: false
    priority: 130
    authentication: AUTHKEY
'''

RETURN = '''
commands:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["interface vlan10", "vrrp 150", "address 10.1.15.1",
            "authentication text testing", "no shutdown"]
'''

from ansible.module_utils.network.nxos.nxos import load_config, run_commands
from ansible.module_utils.network.nxos.nxos import get_capabilities, nxos_argument_spec
from ansible.module_utils.network.nxos.nxos import get_interface_type
from ansible.module_utils.basic import AnsibleModule


PARAM_TO_DEFAULT_KEYMAP = {
    'priority': '100',
    'interval': '1',
    'vip': '0.0.0.0',
    'admin_state': 'shutdown',
}


def execute_show_command(command, module):
    if 'show run' not in command:
        output = 'json'
    else:
        output = 'text'

    commands = [{
        'command': command,
        'output': output,
    }]
    return run_commands(module, commands)[0]


def apply_key_map(key_map, table):
    new_dict = {}
    for key, value in table.items():
        new_key = key_map.get(key)
        if new_key:
            if value:
                new_dict[new_key] = str(value)
            else:
                new_dict[new_key] = value
    return new_dict


def is_default(interface, module):
    command = 'show run interface {0}'.format(interface)

    try:
        body = execute_show_command(command, module)
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
    body = execute_show_command(command, module)
    interface_table = body['TABLE_interface']['ROW_interface']
    name = interface_table.get('interface')

    if intf_type in ['ethernet', 'portchannel']:
        mode = str(interface_table.get('eth_mode', 'layer3'))

        if mode == 'access' or mode == 'trunk':
            mode = 'layer2'
    elif intf_type == 'svi':
        mode = 'layer3'

    return mode, name


def get_vrr_status(group, module, interface):
    command = 'show run all | section interface.{0}$'.format(interface)
    body = execute_show_command(command, module)
    vrf_index = None
    admin_state = 'shutdown'

    if body:
        splitted_body = body.splitlines()
        for index in range(0, len(splitted_body) - 1):
            if splitted_body[index].strip() == 'vrrp {0}'.format(group):
                vrf_index = index
        vrf_section = splitted_body[vrf_index::]

        for line in vrf_section:
            if line.strip() == 'no shutdown':
                admin_state = 'no shutdown'
                break

    return admin_state


def get_existing_vrrp(interface, group, module, name):
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
        vrrp_table = body['TABLE_vrrp_group']
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
            parsed_vrrp['admin_state'] = get_vrr_status(group, module, name)
            return parsed_vrrp

    return vrrp


def get_commands_config_vrrp(delta, existing, group):
    commands = []

    CMDS = {
        'priority': 'priority {0}',
        'preempt': 'preempt',
        'vip': 'address {0}',
        'interval': 'advertisement-interval {0}',
        'auth': 'authentication text {0}',
        'admin_state': '{0}',
    }

    for arg in ['vip', 'priority', 'interval', 'admin_state']:
        val = delta.get(arg)
        if val == 'default':
            val = PARAM_TO_DEFAULT_KEYMAP.get(arg)
            if val != existing.get(arg):
                commands.append((CMDS.get(arg)).format(val))
        elif val:
            commands.append((CMDS.get(arg)).format(val))

    preempt = delta.get('preempt')
    auth = delta.get('authentication')

    if preempt:
        commands.append(CMDS.get('preempt'))
    elif preempt is False:
        commands.append('no ' + CMDS.get('preempt'))
    if auth:
        if auth != 'default':
            commands.append((CMDS.get('auth')).format(auth))
        elif existing.get('authentication'):
            commands.append('no authentication')

    if commands:
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
        interval=dict(required=False, type='str'),
        priority=dict(required=False, type='str'),
        preempt=dict(required=False, type='bool'),
        vip=dict(required=False, type='str'),
        admin_state=dict(required=False, type='str',
                         choices=['shutdown', 'no shutdown', 'default'],
                         default='shutdown'),
        authentication=dict(required=False, type='str', no_log=True),
        state=dict(choices=['absent', 'present'], required=False, default='present')
    )
    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    warnings = list()
    results = {'changed': False, 'commands': [], 'warnings': warnings}

    state = module.params['state']
    interface = module.params['interface'].lower()
    group = module.params['group']
    priority = module.params['priority']
    interval = module.params['interval']
    preempt = module.params['preempt']
    vip = module.params['vip']
    authentication = module.params['authentication']
    admin_state = module.params['admin_state']

    device_info = get_capabilities(module)
    network_api = device_info.get('network_api', 'nxapi')

    if state == 'present' and not vip:
        module.fail_json(msg='the "vip" param is required when state=present')

    intf_type = get_interface_type(interface)
    if (intf_type != 'ethernet' and network_api == 'cliconf'):
        if is_default(interface, module) == 'DNE':
            module.fail_json(msg='That interface does not exist yet. Create '
                                 'it first.', interface=interface)
        if intf_type == 'loopback':
            module.fail_json(msg="Loopback interfaces don't support VRRP.",
                             interface=interface)

    mode, name = get_interface_mode(interface, intf_type, module)
    if mode == 'layer2':
        module.fail_json(msg='That interface is a layer2 port.\nMake it '
                             'a layer 3 port first.', interface=interface)

    args = dict(group=group, priority=priority, preempt=preempt,
                vip=vip, authentication=authentication, interval=interval,
                admin_state=admin_state)

    proposed = dict((k, v) for k, v in args.items() if v is not None)
    existing = get_existing_vrrp(interface, group, module, name)

    changed = False
    end_state = existing
    commands = []

    if state == 'present':
        delta = dict(
            set(proposed.items()).difference(existing.items()))
        if delta:
            command = get_commands_config_vrrp(delta, existing, group)
            if command:
                commands.append(command)
    elif state == 'absent':
        if existing:
            commands.append(['no vrrp {0}'.format(group)])

    if commands:
        commands.insert(0, ['interface {0}'.format(interface)])
        commands = flatten_list(commands)
        results['commands'] = commands
        results['changed'] = True
        if not module.check_mode:
            load_config(module, commands)
            if 'configure' in commands:
                commands.pop(0)

    module.exit_json(**results)


if __name__ == '__main__':
    main()
