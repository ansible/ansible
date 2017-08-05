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

ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'status': ['preview'],
    'supported_by': 'community'
}


DOCUMENTATION = '''
---
module: nxos_interface
extends_documentation_fragment: nxos
version_added: "2.1"
short_description: Manages physical attributes of interfaces.
description:
    - Manages physical attributes of interfaces of NX-OS switches.
author: Jason Edelman (@jedelman8)
notes:
  - This module is also used to create logical interfaces such as
    svis and loopbacks.
  - Be cautious of platform specific idiosyncrasies. For example,
    when you default a loopback interface, the admin state toggles
    on certain versions of NX-OS.
  - The M(nxos_overlay_global) C(anycast_gateway_mac) attribute must be
    set before setting the C(fabric_forwarding_anycast_gateway) property.
options:
  interface:
    description:
      - Full name of interface, i.e. Ethernet1/1, port-channel10.
    required: true
    default: null
  interface_type:
    description:
      - Interface type to be unconfigured from the device.
    required: false
    default: null
    choices: ['loopback', 'portchannel', 'svi', 'nve']
    version_added: "2.2"
  admin_state:
    description:
      - Administrative state of the interface.
    required: false
    default: up
    choices: ['up','down']
  description:
    description:
      - Interface description.
    required: false
    default: null
  mode:
    description:
      - Manage Layer 2 or Layer 3 state of the interface.
    required: false
    default: null
    choices: ['layer2','layer3']
  ip_forward:
    description:
      - Enable/Disable ip forward feature on SVIs.
    required: false
    default: null
    choices: ['enable','disable']
    version_added: "2.2"
  fabric_forwarding_anycast_gateway:
    description:
      - Associate SVI with anycast gateway under VLAN configuration mode.
    required: false
    default: null
    choices: ['true','false']
    version_added: "2.2"
  state:
    description:
      - Specify desired state of the resource.
    required: true
    default: present
    choices: ['present','absent','default']
'''

EXAMPLES = '''
- name: Ensure an interface is a Layer 3 port and that it has the proper description
  nxos_interface:
    interface: Ethernet1/1
    description: 'Configured by Ansible'
    mode: layer3
    host: 68.170.147.165

- name: Admin down an interface
  nxos_interface:
    interface: Ethernet2/1
    host: 68.170.147.165
    admin_state: down

- name: Remove all loopback interfaces
  nxos_interface:
    interface: loopback
    state: absent
    host: 68.170.147.165

- name: Remove all logical interfaces
  nxos_interface:
    interface_type: "{{ item }} "
    state: absent
    host: "{{ inventory_hostname }}"
  with_items:
    - loopback
    - portchannel
    - svi
    - nve

- name: Admin up all loopback interfaces
  nxos_interface:
    interface: loopback 0-1023
    admin_state: up

- name: Admin down all loopback interfaces
  nxos_interface:
    interface: looback 0-1023
    admin_state: down
'''

RETURN = '''
commands:
    description: command list sent to the device
    returned: always
    type: list
    sample: ["interface port-channel101", "shutdown"]
'''

from ansible.module_utils.nxos import get_config, load_config, run_commands
from ansible.module_utils.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule


def is_default_interface(interface, module):
    """Checks to see if interface exists and if it is a default config
    Args:
        interface (str): full name of interface, i.e. vlan10,
            Ethernet1/1, loopback10
    Returns:
        True: if interface has default config
        False: if it does not have a default config
        DNE (str): if the interface does not exist - loopbacks, SVIs, etc.
    """
    command = 'show run interface {0}'.format(interface)

    try:
        body = execute_show_command(command, module)[0]
    except IndexError:
        body = ''

    if body:
        raw_list = body.split('\n')
        found = False
        for line in raw_list:
            if line.startswith('interface'):
                found = True
            if found and line and not line.startswith('interface'):
                return False
        return True

    else:
        return 'DNE'


def get_interface_type(interface):
    """Gets the type of interface
    Args:
        interface (str): full name of interface, i.e. Ethernet1/1, loopback10,
            port-channel20, vlan20
    Returns:
        type of interface: ethernet, svi, loopback, management, portchannel,
         or unknown
    """
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
    elif interface.upper().startswith('NV'):
        return 'nve'
    else:
        return 'unknown'


def get_manual_interface_attributes(interface, module):
    """Gets admin state and description of a SVI interface. Hack due to API.
    Args:
        interface (str): full name of SVI interface, i.e. vlan10
    Returns:
        dictionary that has two k/v pairs: admin_state & description
            if not an svi, returns None
    """

    if get_interface_type(interface) == 'svi':
        command = 'show interface {0}'.format(interface)
        try:
            body = run_commands(module, [command])[0]
        except IndexError:
            return None

        if body:
            command_list = body.split('\n')
            desc = None
            admin_state = 'up'
            for each in command_list:
                if 'Description:' in each:
                    line = each.split('Description:')
                    desc = line[1].strip().split('MTU')[0].strip()
                elif 'Administratively down' in each:
                    admin_state = 'down'

            return dict(description=desc, admin_state=admin_state)
    else:
        return None


def get_interface(intf, module):
    """Gets current config/state of interface
    Args:
        intf (string): full name of interface, i.e. Ethernet1/1, loopback10,
            port-channel20, vlan20
    Returns:
      dictionary that has relevant config/state data about the given
          interface based on the type of interface it is
    """
    base_key_map = {
        'interface': 'interface',
        'admin_state': 'admin_state',
        'desc': 'description',
    }
    mode_map = {
        'eth_mode': 'mode'
    }
    loop_map = {
        'state': 'admin_state'
    }
    svi_map = {
        'svi_admin_state': 'admin_state',
        'desc': 'description'
    }
    mode_value_map = {
        "mode": {
            "access": "layer2",
            "trunk": "layer2",
            "routed": "layer3",
            "layer3": "layer3"
        }
    }

    key_map = {}
    interface = {}

    command = 'show interface {0}'.format(intf)
    try:
        body = execute_show_command(command, module)[0]
    except IndexError:
        body = []

    if body:
        interface_table = body['TABLE_interface']['ROW_interface']
        intf_type = get_interface_type(intf)
        if intf_type in ['portchannel', 'ethernet']:
            if not interface_table.get('eth_mode'):
                interface_table['eth_mode'] = 'layer3'

        if intf_type == 'ethernet':
            key_map.update(base_key_map)
            key_map.update(mode_map)
            temp_dict = apply_key_map(key_map, interface_table)
            temp_dict = apply_value_map(mode_value_map, temp_dict)
            interface.update(temp_dict)

        elif intf_type == 'svi':
            key_map.update(svi_map)
            temp_dict = apply_key_map(key_map, interface_table)
            interface.update(temp_dict)
            attributes = get_manual_interface_attributes(intf, module)
            interface['admin_state'] = str(attributes.get('admin_state',
                                                          'nxapibug'))
            interface['description'] = str(attributes.get('description',
                                                          'nxapi_bug'))
            command = 'show run interface {0}'.format(intf)
            body = execute_show_command(command, module)[0]
            if 'ip forward' in body:
                interface['ip_forward'] = 'enable'
            else:
                interface['ip_forward'] = 'disable'
            if 'fabric forwarding mode anycast-gateway' in body:
                interface['fabric_forwarding_anycast_gateway'] = True
            else:
                interface['fabric_forwarding_anycast_gateway'] = False

        elif intf_type == 'loopback':
            key_map.update(base_key_map)
            key_map.pop('admin_state')
            key_map.update(loop_map)
            temp_dict = apply_key_map(key_map, interface_table)
            if not temp_dict.get('description'):
                temp_dict['description'] = "None"
            interface.update(temp_dict)

        elif intf_type == 'management':
            key_map.update(base_key_map)
            temp_dict = apply_key_map(key_map, interface_table)
            interface.update(temp_dict)

        elif intf_type == 'portchannel':
            key_map.update(base_key_map)
            key_map.update(mode_map)
            temp_dict = apply_key_map(key_map, interface_table)
            temp_dict = apply_value_map(mode_value_map, temp_dict)
            if not temp_dict.get('description'):
                temp_dict['description'] = "None"
            interface.update(temp_dict)

        elif intf_type == 'nve':
            key_map.update(base_key_map)
            temp_dict = apply_key_map(key_map, interface_table)
            if not temp_dict.get('description'):
                temp_dict['description'] = "None"
            interface.update(temp_dict)

    interface['type'] = intf_type

    return interface


def get_intf_args(interface):
    intf_type = get_interface_type(interface)

    arguments = ['admin_state', 'description']

    if intf_type in ['ethernet', 'portchannel']:
        arguments.extend(['mode'])
    if intf_type == 'svi':
        arguments.extend(['ip_forward', 'fabric_forwarding_anycast_gateway'])

    return arguments


def get_interfaces_dict(module):
    """Gets all active interfaces on a given switch
    Returns:
        dictionary with interface type (ethernet,svi,loop,portchannel) as the
            keys.  Each value is a list of interfaces of given interface (key)
            type.
    """
    command = 'show interface status'
    try:
        body = execute_show_command(command, module)[0]
    except IndexError:
        body = {}

    interfaces = {
        'ethernet': [],
        'svi': [],
        'loopback': [],
        'management': [],
        'portchannel': [],
        'nve': [],
        'unknown': []
    }

    if body:
        interface_list = body['TABLE_interface']['ROW_interface']
        for index in interface_list:
            intf = index['interface']
            intf_type = get_interface_type(intf)

            interfaces[intf_type].append(intf)

    return interfaces


def normalize_interface(if_name):
    """Return the normalized interface name
    """
    def _get_number(if_name):
        digits = ''
        for char in if_name:
            if char.isdigit() or char == '/':
                digits += char
        return digits

    if if_name.lower().startswith('et'):
        if_type = 'Ethernet'
    elif if_name.lower().startswith('vl'):
        if_type = 'Vlan'
    elif if_name.lower().startswith('lo'):
        if_type = 'loopback'
    elif if_name.lower().startswith('po'):
        if_type = 'port-channel'
    elif if_name.lower().startswith('nv'):
        if_type = 'nve'
    else:
        if_type = None

    number_list = if_name.split(' ')
    if len(number_list) == 2:
        number = number_list[-1].strip()
    else:
        number = _get_number(if_name)

    if if_type:
        proper_interface = if_type + number
    else:
        proper_interface = if_name

    return proper_interface


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


def apply_value_map(value_map, resource):
    for key, value in value_map.items():
        resource[key] = value[resource.get(key)]
    return resource


def get_interface_config_commands(interface, intf, existing):
    """Generates list of commands to configure on device
    Args:
        interface (str): k/v pairs in the form of a set that should
            be configured on the device
        intf (str): full name of interface, i.e. Ethernet1/1
    Returns:
      list: ordered list of commands to be sent to device
    """

    commands = []
    desc = interface.get('description')
    if desc:
        commands.append('description {0}'.format(desc))

    mode = interface.get('mode')
    if mode:
        if mode == 'layer2':
            command = 'switchport'
        elif mode == 'layer3':
            command = 'no switchport'
        commands.append(command)

    admin_state = interface.get('admin_state')
    if admin_state:
        command = get_admin_state(interface, intf, admin_state)
        commands.append(command)

    ip_forward = interface.get('ip_forward')
    if ip_forward:
        if ip_forward == 'enable':
            commands.append('ip forward')
        else:
            commands.append('no ip forward')

    fabric_forwarding_anycast_gateway = interface.get(
        'fabric_forwarding_anycast_gateway')
    if fabric_forwarding_anycast_gateway is not None:
        if fabric_forwarding_anycast_gateway is True:
            commands.append('fabric forwarding mode anycast-gateway')
        elif fabric_forwarding_anycast_gateway is False:
            commands.append('no fabric forwarding mode anycast-gateway')

    if commands:
        commands.insert(0, 'interface {0}'.format(intf))

    return commands


def get_admin_state(interface, intf, admin_state):
    command = ''
    if admin_state == 'up':
        command = 'no shutdown'
    elif admin_state == 'down':
        command = 'shutdown'
    return command


def get_proposed(existing, normalized_interface, args):

    # gets proper params that are allowed based on interface type
    allowed_params = get_intf_args(normalized_interface)

    proposed = {}

    # retrieves proper interface params from args (user defined params)
    for param in allowed_params:
        temp = args.get(param)
        if temp is not None:
            proposed[param] = temp

    return proposed


def smart_existing(module, intf_type, normalized_interface):

    # 7K BUG MAY CAUSE THIS TO FAIL

    all_interfaces = get_interfaces_dict(module)
    if normalized_interface in all_interfaces[intf_type]:
        existing = get_interface(normalized_interface, module)
        is_default = is_default_interface(normalized_interface, module)
    else:
        if intf_type == 'ethernet':
            module.fail_json(msg='Invalid Ethernet interface provided.',
                             interface=normalized_interface)
        elif intf_type in ['loopback', 'portchannel', 'svi', 'nve']:
            existing = {}
            is_default = 'DNE'
    return existing, is_default


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


def get_interface_type_removed_cmds(interfaces):
    commands = []

    for interface in interfaces:
        if interface != 'Vlan1':
            commands.append('no interface {0}'.format(interface))

    return commands


def main():

    argument_spec = dict(
        interface=dict(required=False,),
        admin_state=dict(default='up', choices=['up', 'down'], required=False),
        description=dict(required=False, default=None),
        mode=dict(choices=['layer2', 'layer3'], required=False),
        interface_type=dict(required=False, choices=['loopback', 'portchannel', 'svi', 'nve']),
        ip_forward=dict(required=False, choices=['enable', 'disable']),
        fabric_forwarding_anycast_gateway=dict(required=False, type='bool'),
        state=dict(choices=['absent', 'present', 'default'], default='present', required=False)
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=[['interface', 'interface_type']],
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    results = dict(changed=False, warnings=warnings)

    interface = module.params['interface']
    interface_type = module.params['interface_type']
    admin_state = module.params['admin_state']
    description = module.params['description']
    mode = module.params['mode']
    ip_forward = module.params['ip_forward']
    fabric_forwarding_anycast_gateway = module.params['fabric_forwarding_anycast_gateway']
    state = module.params['state']

    if interface:
        interface = interface.lower()
        intf_type = get_interface_type(interface)
        normalized_interface = normalize_interface(interface)

        if normalized_interface == 'Vlan1' and state == 'absent':
            module.fail_json(msg='ERROR: CANNOT REMOVE VLAN 1!')

        if intf_type == 'nve':
            if description or mode:
                module.fail_json(msg='description and mode params are not '
                                     'supported in this module. Use '
                                     'nxos_vxlan_vtep instead.')
        if (ip_forward or fabric_forwarding_anycast_gateway) and intf_type != 'svi':
            module.fail_json(msg='The ip_forward and '
                                 'fabric_forwarding_anycast_gateway features '
                                 ' are only available for SVIs.')
        args = dict(interface=interface, admin_state=admin_state,
                    description=description, mode=mode, ip_forward=ip_forward,
                    fabric_forwarding_anycast_gateway=fabric_forwarding_anycast_gateway)

        if intf_type == 'unknown':
            module.fail_json(msg='unknown interface type found-1',
                             interface=interface)

        existing, is_default = smart_existing(module, intf_type, normalized_interface)
        proposed = get_proposed(existing, normalized_interface, args)
    else:
        intf_type = normalized_interface = interface_type
        proposed = dict(interface_type=interface_type)

    commands = []
    if interface:
        delta = dict()

        if state == 'absent':
            if intf_type in ['svi', 'loopback', 'portchannel', 'nve']:
                if is_default != 'DNE':
                    cmds = ['no interface {0}'.format(normalized_interface)]
                    commands.append(cmds)
            elif intf_type in ['ethernet']:
                if is_default is False:
                    cmds = ['default interface {0}'.format(normalized_interface)]
                    commands.append(cmds)
        elif state == 'present':
            if not existing:
                cmds = get_interface_config_commands(proposed, normalized_interface, existing)
                commands.append(cmds)
            else:
                delta = dict(set(proposed.items()).difference(existing.items()))
                if delta:
                    cmds = get_interface_config_commands(delta, normalized_interface, existing)
                    commands.append(cmds)
        elif state == 'default':
            if is_default is False:
                cmds = ['default interface {0}'.format(normalized_interface)]
                commands.append(cmds)
            elif is_default == 'DNE':
                module.exit_json(msg='interface you are trying to default does not exist')
    elif interface_type:
        if state == 'present':
            module.fail_json(msg='The interface_type param can be used only with state absent.')

        existing = get_interfaces_dict(module)[interface_type]
        cmds = get_interface_type_removed_cmds(existing)
        commands.append(cmds)

    cmds = flatten_list(commands)
    end_state = existing

    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            load_config(module, cmds)
            results['changed'] = True
            if module.params['interface']:
                if delta.get('mode'):
                    # if the mode changes from L2 to L3, the admin state
                    # seems to change after the API call, so adding a second API
                    # call to ensure it's in the desired state.
                    admin_state = delta.get('admin_state') or admin_state
                    c1 = 'interface {0}'.format(normalized_interface)
                    c2 = get_admin_state(delta, normalized_interface, admin_state)
                    cmds2 = [c1, c2]
                    load_config(module, cmds2)
                    cmds.extend(cmds2)
                end_state, is_default = smart_existing(module, intf_type,
                                                       normalized_interface)
            else:
                end_state = get_interfaces_dict(module)[interface_type]
            cmds = [cmd for cmd in cmds if cmd != 'configure']

    results['commands'] = cmds

    module.exit_json(**results)


if __name__ == '__main__':
    main()
