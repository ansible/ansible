#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: ios_l2_interface
extends_documentation_fragment: ios
version_added: "2.5"
short_description: Manage Layer-2 interface on Cisco IOS devices.
description:
  - This module provides declarative management of Layer-2 interface on
    Cisco IOS devices.
author:
  - Nathaniel Case (@qalthos)
options:
  name:
    description:
      - Full name of the interface excluding any logical
        unit number, i.e. GigabitEthernet0/1.
    required: true
    aliases: ['interface']
  mode:
    description:
      - Mode in which interface needs to be configured.
    default: access
    choices: ['access', 'trunk']
  access_vlan:
    description:
      - Configure given VLAN in access port.
        If C(mode=access), used as the access VLAN ID.
  trunk_vlans:
    description:
      - List of VLANs to be configured in trunk port.
        If C(mode=trunk), used as the VLAN range to ADD or REMOVE
        from the trunk.
  native_vlan:
    description:
      - Native VLAN to be configured in trunk port.
        If C(mode=trunk), used as the trunk native VLAN ID.
  trunk_allowed_vlans:
    description:
      - List of allowed VLANs in a given trunk port.
        If C(mode=trunk), these are the only VLANs that will be
        configured on the trunk, i.e. "2-10,15".
  aggregate:
    description:
      - List of Layer-2 interface definitions.
  state:
    description:
      - Manage the state of the Layer-2 Interface configuration.
    default:  present
    choices: ['present','absent', 'unconfigured']
"""

EXAMPLES = """
- name: Ensure GigabitEthernet0/5 is in its default l2 interface state
  ios_l2_interface:
    name: GigabitEthernet0/5
    state: unconfigured

- name: Ensure GigabitEthernet0/5 is configured for access vlan 20
  ios_l2_interface:
    name: GigabitEthernet0/5
    mode: access
    access_vlan: 20

- name: Ensure GigabitEthernet0/5 only has vlans 5-10 as trunk vlans
  ios_l2_interface:
    name: GigabitEthernet0/5
    mode: trunk
    native_vlan: 10
    trunk_vlans: 5-10

- name: Ensure GigabitEthernet0/5 is a trunk port and ensure 2-50 are being tagged (doesn't mean others aren't also being tagged)
  ios_l2_interface:
    name: GigabitEthernet0/5
    mode: trunk
    native_vlan: 10
    trunk_vlans: 2-50

- name: Ensure these VLANs are not being tagged on the trunk
  ios_l2_interface:
    name: GigabitEthernet0/5
    mode: trunk
    trunk_vlans: 51-4094
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always, except for the platforms that use Netconf transport to manage the device.
  type: list
  sample:
    - interface GigabitEthernet0/5
    - switchport access vlan 20
"""

import re
from copy import deepcopy

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import remove_default_spec
from ansible.module_utils.network.ios.ios import get_config, load_config, run_commands
from ansible.module_utils.network.ios.ios import ios_argument_spec


def get_interface_type(interface):
    intf_type = 'unknown'
    if interface.upper()[:2] in ('ET', 'GI'):
        intf_type = 'ethernet'
    elif interface.upper().startswith('VL'):
        intf_type = 'svi'
    elif interface.upper().startswith('LO'):
        intf_type = 'loopback'
    elif interface.upper()[:2] in ('MG', 'MA'):
        intf_type = 'management'
    elif interface.upper().startswith('PO'):
        intf_type = 'portchannel'
    elif interface.upper().startswith('NV'):
        intf_type = 'nve'

    return intf_type


def is_switchport(name, module):
    intf_type = get_interface_type(name)

    if intf_type in ('ethernet', 'portchannel'):
        config = run_commands(module, ['show interface {0} switchport'.format(name)])[0]
        match = re.search(r'Switchport: Enabled', config)
        return bool(match)
    return False


def interface_is_portchannel(name, module):
    if get_interface_type(name) == 'ethernet':
        config = run_commands(module, ['show run interface {0}'.format(name)])[0]
        if any(c in config for c in ['channel group', 'channel-group']):
            return True
    return False


def get_switchport(name, module):
    config = run_commands(module, ['show interface {0} switchport'.format(name)])[0]
    mode = re.search(r'Administrative Mode: (?:.* )?(\w+)$', config, re.M)
    access = re.search(r'Access Mode VLAN: (\d+)', config)
    native = re.search(r'Trunking Native Mode VLAN: (\d+)', config)
    trunk = re.search(r'Trunking VLANs Enabled: (.+)$', config, re.M)
    if mode:
        mode = mode.group(1)
    if access:
        access = access.group(1)
    if native:
        native = native.group(1)
    if trunk:
        trunk = trunk.group(1)
    if trunk == 'ALL':
        trunk = '1-4094'

    switchport_config = {
        "interface": name,
        "mode": mode,
        "access_vlan": access,
        "native_vlan": native,
        "trunk_vlans": trunk,
    }

    return switchport_config


def remove_switchport_config_commands(name, existing, proposed, module):
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
        commands.insert(0, 'interface ' + name)
    return commands


def get_switchport_config_commands(name, existing, proposed, module):
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
        commands.insert(0, 'interface ' + name)
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


def default_switchport_config(name):
    commands = []
    commands.append('interface ' + name)
    commands.append('switchport mode access')
    commands.append('switch access vlan 1')
    commands.append('switchport trunk native vlan 1')
    commands.append('switchport trunk allowed vlan all')
    return commands


def vlan_range_to_list(vlans):
    result = []
    if vlans:
        for part in vlans.split(','):
            if part.lower() == 'none':
                break
            if '-' in part:
                start, stop = (int(i) for i in part.split('-'))
                result.extend(range(start, stop + 1))
            else:
                result.append(int(part))
    return sorted(result)


def get_list_of_vlans(module):
    config = run_commands(module, ['show vlan'])[0]
    vlans = set()

    lines = config.strip().splitlines()
    for line in lines:
        line_parts = line.split()
        if line_parts:
            try:
                int(line_parts[0])
            except ValueError:
                continue
            vlans.add(line_parts[0])

    return list(vlans)


def flatten_list(commands):
    flat_list = []
    for command in commands:
        if isinstance(command, list):
            flat_list.extend(command)
        else:
            flat_list.append(command)
    return flat_list


def map_params_to_obj(module):
    obj = []

    aggregate = module.params.get('aggregate')
    if aggregate:
        for item in aggregate:
            for key in item:
                if item.get(key) is None:
                    item[key] = module.params[key]

            obj.append(item.copy())
    else:
        obj.append({
            'name': module.params['name'],
            'mode': module.params['mode'],
            'access_vlan': module.params['access_vlan'],
            'native_vlan': module.params['native_vlan'],
            'trunk_vlans': module.params['trunk_vlans'],
            'trunk_allowed_vlans': module.params['trunk_allowed_vlans'],
            'state': module.params['state']
        })

    return obj


def main():
    """ main entry point for module execution
    """
    element_spec = dict(
        name=dict(type='str', aliases=['interface']),
        mode=dict(choices=['access', 'trunk']),
        access_vlan=dict(type='str'),
        native_vlan=dict(type='str'),
        trunk_vlans=dict(type='str'),
        trunk_allowed_vlans=dict(type='str'),
        state=dict(choices=['absent', 'present', 'unconfigured'], default='present')
    )

    aggregate_spec = deepcopy(element_spec)

    # remove default in aggregate spec, to handle common arguments
    remove_default_spec(aggregate_spec)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec),
    )

    argument_spec.update(element_spec)
    argument_spec.update(ios_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=[['access_vlan', 'trunk_vlans'],
                                               ['access_vlan', 'native_vlan'],
                                               ['access_vlan', 'trunk_allowed_vlans']],
                           supports_check_mode=True)

    warnings = list()
    commands = []
    result = {'changed': False, 'warnings': warnings}

    want = map_params_to_obj(module)
    for w in want:
        name = w['name']
        mode = w['mode']
        access_vlan = w['access_vlan']
        state = w['state']
        trunk_vlans = w['trunk_vlans']
        native_vlan = w['native_vlan']
        trunk_allowed_vlans = w['trunk_allowed_vlans']

        args = dict(name=name, mode=mode, access_vlan=access_vlan,
                    native_vlan=native_vlan, trunk_vlans=trunk_vlans,
                    trunk_allowed_vlans=trunk_allowed_vlans)

        proposed = dict((k, v) for k, v in args.items() if v is not None)

        name = name.lower()

        if mode == 'access' and state == 'present' and not access_vlan:
            module.fail_json(msg='access_vlan param is required when mode=access && state=present')

        if mode == 'trunk' and access_vlan:
            module.fail_json(msg='access_vlan param not supported when using mode=trunk')

        if not is_switchport(name, module):
            module.fail_json(msg='Ensure interface is configured to be a L2'
                             '\nport first before using this module. You can use'
                             '\nthe ios_interface module for this.')

        if interface_is_portchannel(name, module):
            module.fail_json(msg='Cannot change L2 config on physical '
                             '\nport because it is in a portchannel. '
                             '\nYou should update the portchannel config.')

        # existing will never be null for Eth intfs as there is always a default
        existing = get_switchport(name, module)

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
                command = get_switchport_config_commands(name, existing, proposed, module)
                commands.append(command)
        elif state == 'unconfigured':
            is_default = is_switchport_default(existing)
            if not is_default:
                command = default_switchport_config(name)
                commands.append(command)
        elif state == 'absent':
            command = remove_switchport_config_commands(name, existing, proposed, module)
            commands.append(command)

        if trunk_vlans or trunk_allowed_vlans:
            existing.pop('trunk_vlans_list')
            proposed.pop('trunk_vlans_list')

    cmds = flatten_list(commands)
    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            result['changed'] = True
            load_config(module, cmds)
            if 'configure' in cmds:
                cmds.pop(0)

    result['commands'] = cmds

    module.exit_json(**result)


if __name__ == '__main__':
    main()
