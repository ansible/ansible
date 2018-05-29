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
module: nxos_switchport
extends_documentation_fragment: nxos
version_added: "2.1"
deprecated:
  removed_in: "2.9"
  why: Replaced with generic version.
  alternative: Use M(nxos_l2_interface) instead.
short_description: Manages Layer 2 switchport interfaces.
description:
  - Manages Layer 2 interfaces
author: Jason Edelman (@jedelman8)
notes:
  - Tested against NXOSv 7.3.(0)D1(1) on VIRL
  - When C(state=absent), VLANs can be added/removed from trunk links and
    the existing access VLAN can be 'unconfigured' to just having VLAN 1
    on that interface.
  - When working with trunks VLANs the keywords add/remove are always sent
    in the `switchport trunk allowed vlan` command. Use verbose mode to see
    commands sent.
  - When C(state=unconfigured), the interface will result with having a default
    Layer 2 interface, i.e. vlan 1 in access mode.
options:
  interface:
    description:
      - Full name of the interface, i.e. Ethernet1/1.
  mode:
    description:
      - Mode for the Layer 2 port.
    choices: ['access','trunk']
  access_vlan:
    description:
      - If C(mode=access), used as the access VLAN ID.
  native_vlan:
    description:
      - If C(mode=trunk), used as the trunk native VLAN ID.
  trunk_vlans:
    description:
      - If C(mode=trunk), used as the VLAN range to ADD or REMOVE
        from the trunk.
    aliases:
      - trunk_add_vlans
  state:
    description:
      - Manage the state of the resource.
    default:  present
    choices: ['present','absent', 'unconfigured']
  trunk_allowed_vlans:
    description:
      - if C(mode=trunk), these are the only VLANs that will be
        configured on the trunk, i.e. "2-10,15".
    version_added: 2.2
'''

EXAMPLES = '''
- name: Ensure Eth1/5 is in its default switchport state
  nxos_switchport:
    interface: eth1/5
    state: unconfigured

- name: Ensure Eth1/5 is configured for access vlan 20
  nxos_switchport:
    interface: eth1/5
    mode: access
    access_vlan: 20

- name: Ensure Eth1/5 only has vlans 5-10 as trunk vlans
  nxos_switchport:
    interface: eth1/5
    mode: trunk
    native_vlan: 10
    trunk_vlans: 5-10

- name: Ensure eth1/5 is a trunk port and ensure 2-50 are being tagged (doesn't mean others aren't also being tagged)
  nxos_switchport:
    interface: eth1/5
    mode: trunk
    native_vlan: 10
    trunk_vlans: 2-50

- name: Ensure these VLANs are not being tagged on the trunk
  nxos_switchport:
    interface: eth1/5
    mode: trunk
    trunk_vlans: 51-4094
    state: absent
'''

RETURN = '''
commands:
    description: command string sent to the device
    returned: always
    type: list
    sample: ["interface eth1/5", "switchport access vlan 20"]
'''

from ansible.module_utils.network.nxos.nxos import load_config, run_commands
from ansible.module_utils.network.nxos.nxos import get_capabilities, nxos_argument_spec
from ansible.module_utils.network.nxos.nxos import get_interface_type
from ansible.module_utils.basic import AnsibleModule


def get_interface_mode(interface, module):
    """Gets current mode of interface: layer2 or layer3
    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        interface (string): full name of interface, i.e. Ethernet1/1,
            loopback10, port-channel20, vlan20
    Returns:
        str: 'layer2' or 'layer3'
    """
    command = 'show interface ' + interface
    intf_type = get_interface_type(interface)
    mode = 'unknown'
    interface_table = {}

    try:
        body = execute_show_command(command, module)[0]
        interface_table = body['TABLE_interface']['ROW_interface']
    except (KeyError, AttributeError, IndexError):
        return mode

    if interface_table:
        # HACK FOR NOW
        if intf_type in ['ethernet', 'portchannel']:
            mode = str(interface_table.get('eth_mode', 'layer3'))
            if mode in ['access', 'trunk']:
                mode = 'layer2'
            if mode == 'routed':
                mode = 'layer3'
        elif intf_type == 'loopback' or intf_type == 'svi':
            mode = 'layer3'
    return mode


def interface_is_portchannel(interface, module):
    """Checks to see if an interface is part of portchannel bundle
    Args:
        interface (str): full name of interface, i.e. Ethernet1/1
    Returns:
        True/False based on if interface is a member of a portchannel bundle
    """
    intf_type = get_interface_type(interface)

    if intf_type == 'ethernet':
        command = 'show interface ' + interface
        try:
            body = execute_show_command(command, module)[0]
            interface_table = body['TABLE_interface']['ROW_interface']
        except (KeyError, AttributeError, IndexError):
            interface_table = None

        if interface_table:
            state = interface_table.get('eth_bundle')
            if state:
                return True
            else:
                return False

    return False


def get_switchport(port, module):
    """Gets current config of L2 switchport
    Args:
        device (Device): This is the device object of an NX-API enabled device
            using the Device class within device.py
        port (str): full name of interface, i.e. Ethernet1/1
    Returns:
        dictionary with k/v pairs for L2 vlan config
    """

    command = 'show interface {0} switchport'.format(port)

    try:
        body = execute_show_command(command, module)[0]
        sp_table = body['TABLE_interface']['ROW_interface']
    except (KeyError, AttributeError, IndexError):
        sp_table = None

    if sp_table:
        key_map = {
            "interface": "interface",
            "oper_mode": "mode",
            "switchport": "switchport",
            "access_vlan": "access_vlan",
            "access_vlan_name": "access_vlan_name",
            "native_vlan": "native_vlan",
            "native_vlan_name": "native_vlan_name",
            "trunk_vlans": "trunk_vlans"
        }
        sp = apply_key_map(key_map, sp_table)
        return sp

    else:
        return {}


def remove_switchport_config_commands(interface, existing, proposed, module):
    mode = proposed.get('mode')
    commands = []
    command = None

    if mode == 'access':
        av_check = existing.get('access_vlan') == proposed.get('access_vlan')
        if av_check:
            command = 'no switchport access vlan {0}'.format(existing.get('access_vlan'))
            commands.append(command)

    elif mode == 'trunk':

        # Supported Remove Scenarios for trunk_vlans_list
        # 1) Existing: 1,2,3 Proposed: 1,2,3 - Remove all
        # 2) Existing: 1,2,3 Proposed: 1,2   - Remove 1,2 Leave 3
        # 3) Existing: 1,2,3 Proposed: 2,3   - Remove 2,3 Leave 1
        # 4) Existing: 1,2,3 Proposed: 4,5,6 - None removed.
        # 5) Existing: None  Proposed: 1,2,3 - None removed.

        existing_vlans = existing.get('trunk_vlans_list')
        proposed_vlans = proposed.get('trunk_vlans_list')
        vlans_to_remove = set(proposed_vlans).intersection(existing_vlans)

        if vlans_to_remove:
            proposed_allowed_vlans = proposed.get('trunk_allowed_vlans')
            remove_trunk_allowed_vlans = proposed.get('trunk_vlans', proposed_allowed_vlans)
            command = 'switchport trunk allowed vlan remove {0}'.format(remove_trunk_allowed_vlans)
            commands.append(command)

        native_check = existing.get('native_vlan') == proposed.get('native_vlan')
        if native_check and proposed.get('native_vlan'):
            command = 'no switchport trunk native vlan {0}'.format(existing.get('native_vlan'))
            commands.append(command)

    if commands:
        commands.insert(0, 'interface ' + interface)
    return commands


def get_switchport_config_commands(interface, existing, proposed, module):
    """Gets commands required to config a given switchport interface
    """

    proposed_mode = proposed.get('mode')
    existing_mode = existing.get('mode')
    commands = []
    command = None

    if proposed_mode != existing_mode:
        if proposed_mode == 'trunk':
            command = 'switchport mode trunk'
        elif proposed_mode == 'access':
            command = 'switchport mode access'

    if command:
        commands.append(command)

    if proposed_mode == 'access':
        av_check = str(existing.get('access_vlan')) == str(proposed.get('access_vlan'))
        if not av_check:
            command = 'switchport access vlan {0}'.format(proposed.get('access_vlan'))
            commands.append(command)

    elif proposed_mode == 'trunk':
        tv_check = existing.get('trunk_vlans_list') == proposed.get('trunk_vlans_list')

        if not tv_check:
            if proposed.get('allowed'):
                command = 'switchport trunk allowed vlan {0}'.format(proposed.get('trunk_allowed_vlans'))
                commands.append(command)

            else:
                existing_vlans = existing.get('trunk_vlans_list')
                proposed_vlans = proposed.get('trunk_vlans_list')
                vlans_to_add = set(proposed_vlans).difference(existing_vlans)
                if vlans_to_add:
                    command = 'switchport trunk allowed vlan add {0}'.format(proposed.get('trunk_vlans'))
                    commands.append(command)

        native_check = str(existing.get('native_vlan')) == str(proposed.get('native_vlan'))
        if not native_check and proposed.get('native_vlan'):
            command = 'switchport trunk native vlan {0}'.format(proposed.get('native_vlan'))
            commands.append(command)

    if commands:
        commands.insert(0, 'interface ' + interface)
    return commands


def is_switchport_default(existing):
    """Determines if switchport has a default config based on mode
    Args:
        existing (dict): existing switchport configuration from Ansible mod
    Returns:
        boolean: True if switchport has OOB Layer 2 config, i.e.
           vlan 1 and trunk all and mode is access
    """

    c1 = str(existing['access_vlan']) == '1'
    c2 = str(existing['native_vlan']) == '1'
    c3 = existing['trunk_vlans'] == '1-4094'
    c4 = existing['mode'] == 'access'

    default = c1 and c2 and c3 and c4

    return default


def default_switchport_config(interface):
    commands = []
    commands.append('interface ' + interface)
    commands.append('switchport mode access')
    commands.append('switch access vlan 1')
    commands.append('switchport trunk native vlan 1')
    commands.append('switchport trunk allowed vlan all')
    return commands


def vlan_range_to_list(vlans):
    result = []
    if vlans:
        for part in vlans.split(','):
            if part == 'none':
                break
            if '-' in part:
                a, b = part.split('-')
                a, b = int(a), int(b)
                result.extend(range(a, b + 1))
            else:
                a = int(part)
                result.append(a)
        return numerical_sort(result)
    return result


def get_list_of_vlans(module):

    command = 'show vlan'
    vlan_list = []

    try:
        body = execute_show_command(command, module)[0]
        vlan_table = body['TABLE_vlanbrief']['ROW_vlanbrief']
    except (KeyError, AttributeError, IndexError):
        return []

    if isinstance(vlan_table, list):
        for vlan in vlan_table:
            vlan_list.append(str(vlan['vlanshowbr-vlanid-utf']))
    else:
        vlan_list.append('1')

    return vlan_list


def numerical_sort(string_int_list):
    """Sorts list of strings/integers that are digits in numerical order.
    """

    as_int_list = []
    as_str_list = []
    for vlan in string_int_list:
        as_int_list.append(int(vlan))
    as_int_list.sort()
    for vlan in as_int_list:
        as_str_list.append(str(vlan))
    return as_str_list


def apply_key_map(key_map, table):
    new_dict = {}
    for key, value in table.items():
        new_key = key_map.get(key)
        if new_key:
            new_dict[new_key] = value
    return new_dict


def apply_value_map(value_map, resource):
    for key, value in value_map.items():
        resource[key] = value[resource.get(key)]
    return resource


def execute_show_command(command, module, command_type='cli_show'):
    device_info = get_capabilities(module)
    network_api = device_info.get('network_api', 'nxapi')

    if network_api == 'cliconf':
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


def main():

    argument_spec = dict(
        interface=dict(required=True, type='str'),
        mode=dict(choices=['access', 'trunk'], required=False),
        access_vlan=dict(type='str', required=False),
        native_vlan=dict(type='str', required=False),
        trunk_vlans=dict(type='str', aliases=['trunk_add_vlans'], required=False),
        trunk_allowed_vlans=dict(type='str', required=False),
        state=dict(choices=['absent', 'present', 'unconfigured'], default='present')
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=[['access_vlan', 'trunk_vlans'],
                                               ['access_vlan', 'native_vlan'],
                                               ['access_vlan', 'trunk_allowed_vlans']],
                           supports_check_mode=True)

    warnings = list()
    commands = []
    results = {'changed': False}

    interface = module.params['interface']
    mode = module.params['mode']
    access_vlan = module.params['access_vlan']
    state = module.params['state']
    trunk_vlans = module.params['trunk_vlans']
    native_vlan = module.params['native_vlan']
    trunk_allowed_vlans = module.params['trunk_allowed_vlans']

    args = dict(interface=interface, mode=mode, access_vlan=access_vlan,
                native_vlan=native_vlan, trunk_vlans=trunk_vlans,
                trunk_allowed_vlans=trunk_allowed_vlans)

    proposed = dict((k, v) for k, v in args.items() if v is not None)

    interface = interface.lower()

    if mode == 'access' and state == 'present' and not access_vlan:
        module.fail_json(msg='access_vlan param is required when mode=access && state=present')

    if mode == 'trunk' and access_vlan:
        module.fail_json(msg='access_vlan param not supported when using mode=trunk')

    current_mode = get_interface_mode(interface, module)

    # Current mode will return layer3, layer2, or unknown
    if current_mode == 'unknown' or current_mode == 'layer3':
        module.fail_json(msg='Ensure interface is configured to be a L2'
                         '\nport first before using this module. You can use'
                         '\nthe nxos_interface module for this.')

    if interface_is_portchannel(interface, module):
        module.fail_json(msg='Cannot change L2 config on physical '
                         '\nport because it is in a portchannel. '
                         '\nYou should update the portchannel config.')

    # existing will never be null for Eth intfs as there is always a default
    existing = get_switchport(interface, module)

    # Safeguard check
    # If there isn't an existing, something is wrong per previous comment
    if not existing:
        module.fail_json(msg='Make sure you are using the FULL interface name')

    if trunk_vlans or trunk_allowed_vlans:
        if trunk_vlans:
            trunk_vlans_list = vlan_range_to_list(trunk_vlans)
        elif trunk_allowed_vlans:
            trunk_vlans_list = vlan_range_to_list(trunk_allowed_vlans)
            proposed['allowed'] = True

        existing_trunks_list = vlan_range_to_list((existing['trunk_vlans']))

        existing['trunk_vlans_list'] = existing_trunks_list
        proposed['trunk_vlans_list'] = trunk_vlans_list

    current_vlans = get_list_of_vlans(module)

    if state == 'present':
        if access_vlan and access_vlan not in current_vlans:
            module.fail_json(msg='You are trying to configure a VLAN'
                             ' on an interface that\ndoes not exist on the '
                             ' switch yet!', vlan=access_vlan)
        elif native_vlan and native_vlan not in current_vlans:
            module.fail_json(msg='You are trying to configure a VLAN'
                             ' on an interface that\ndoes not exist on the '
                             ' switch yet!', vlan=native_vlan)
        else:
            command = get_switchport_config_commands(interface, existing, proposed, module)
            commands.append(command)
    elif state == 'unconfigured':
        is_default = is_switchport_default(existing)
        if not is_default:
            command = default_switchport_config(interface)
            commands.append(command)
    elif state == 'absent':
        command = remove_switchport_config_commands(interface, existing, proposed, module)
        commands.append(command)

    if trunk_vlans or trunk_allowed_vlans:
        existing.pop('trunk_vlans_list')
        proposed.pop('trunk_vlans_list')

    cmds = flatten_list(commands)

    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            results['changed'] = True
            load_config(module, cmds)
            if 'configure' in cmds:
                cmds.pop(0)

    results['commands'] = cmds
    results['warnings'] = warnings

    module.exit_json(**results)


if __name__ == '__main__':
    main()
