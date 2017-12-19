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
module: nxos_portchannel
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages port-channel interfaces.
description:
  - Manages port-channel specific configuration parameters.
author:
  - Jason Edelman (@jedelman8)
  - Gabriele Gerbino (@GGabriele)
notes:
  - Tested against NXOSv 7.3.(0)D1(1) on VIRL
  - C(state=absent) removes the portchannel config and interface if it
    already exists. If members to be removed are not explicitly
    passed, all existing members (if any), are removed.
  - Members must be a list.
  - LACP needs to be enabled first if active/passive modes are used.
options:
  group:
    description:
      - Channel-group number for the port-channel.
    required: true
  mode:
    description:
      - Mode for the port-channel, i.e. on, active, passive.
    required: false
    default: on
    choices: ['active','passive','on']
  min_links:
    description:
      - Min links required to keep portchannel up.
    required: false
    default: null
  members:
    description:
      - List of interfaces that will be managed in a given portchannel.
    required: false
    default: null
  force:
    description:
      - When true it forces port-channel members to match what is
        declared in the members param. This can be used to remove
        members.
    required: false
    choices: ['true', 'false']
    default: false
  state:
    description:
      - Manage the state of the resource.
    required: false
    default: present
    choices: ['present','absent']
'''

EXAMPLES = '''
# Ensure port-channel99 is created, add two members, and set to mode on
- nxos_portchannel:
    group: 99
    members: ['Ethernet1/1','Ethernet1/2']
    mode: 'active'
    state: present
'''

RETURN = '''
commands:
    description: command sent to the device
    returned: always
    type: list
    sample: ["interface Ethernet2/6", "no channel-group 12",
             "interface Ethernet2/5", "no channel-group 12",
             "interface Ethernet2/6", "channel-group 12 mode on",
             "interface Ethernet2/5", "channel-group 12 mode on"]
'''

import collections
import re

from ansible.module_utils.network.nxos.nxos import get_config, load_config, run_commands
from ansible.module_utils.network.nxos.nxos import get_capabilities, nxos_argument_spec
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.config import CustomNetworkConfig


def get_value(arg, config, module):
    param_to_command_keymap = {
        'min_links': 'lacp min-links'
    }

    REGEX = re.compile(r'(?:{0}\s)(?P<value>.*)$'.format(param_to_command_keymap[arg]), re.M)
    value = ''
    if param_to_command_keymap[arg] in config:
        value = REGEX.search(config).group('value')
    return value


def check_interface(module, netcfg):
    config = str(netcfg)
    REGEX = re.compile(r'\s+interface port-channel{0}$'.format(module.params['group']), re.M)
    value = False
    try:
        if REGEX.search(config):
            value = True
    except TypeError:
        value = False

    return value


def get_custom_value(arg, config, module):
    REGEX = re.compile(r'\s+member vni {0} associate-vrf\s*$'.format(
        module.params['vni']), re.M)
    value = False
    try:
        if REGEX.search(config):
            value = True
    except TypeError:
        value = False
    return value


def execute_show_command(command, module):
    device_info = get_capabilities(module)
    network_api = device_info.get('network_api', 'nxapi')

    if network_api == 'cliconf':
        if 'show port-channel summary' in command:
            command += ' | json'
        cmds = [command]
        body = run_commands(module, cmds)
    elif network_api == 'nxapi':
        cmds = [command]
        body = run_commands(module, cmds)

    return body


def get_portchannel_members(pchannel):
    try:
        members = pchannel['TABLE_member']['ROW_member']
    except KeyError:
        members = []

    return members


def get_portchannel_mode(interface, protocol, module, netcfg):
    if protocol != 'LACP':
        mode = 'on'
    else:
        netcfg = CustomNetworkConfig(indent=2, contents=get_config(module))
        parents = ['interface {0}'.format(interface.capitalize())]
        body = netcfg.get_section(parents)

        mode_list = body.split('\n')

        for line in mode_list:
            this_line = line.strip()
            if this_line.startswith('channel-group'):
                find = this_line
        if 'mode' in find:
            if 'passive' in find:
                mode = 'passive'
            elif 'active' in find:
                mode = 'active'

    return mode


def get_portchannel(module, netcfg=None):
    command = 'show port-channel summary'
    portchannel = {}
    portchannel_table = {}
    members = []

    try:
        body = execute_show_command(command, module)[0]
        pc_table = body['TABLE_channel']['ROW_channel']

        if isinstance(pc_table, dict):
            pc_table = [pc_table]

        for pc in pc_table:
            if pc['group'] == module.params['group']:
                portchannel_table = pc
            elif module.params['group'].isdigit() and pc['group'] == int(module.params['group']):
                portchannel_table = pc
    except (KeyError, AttributeError, TypeError, IndexError):
        return {}

    if portchannel_table:
        portchannel['group'] = portchannel_table['group']
        protocol = portchannel_table['prtcl']
        members_list = get_portchannel_members(portchannel_table)

        if isinstance(members_list, dict):
            members_list = [members_list]

        member_dictionary = {}
        for each_member in members_list:
            interface = each_member['port']
            members.append(interface)

            pc_member = {}
            pc_member['status'] = str(each_member['port-status'])
            pc_member['mode'] = get_portchannel_mode(interface,
                                                     protocol, module, netcfg)

            member_dictionary[interface] = pc_member
            portchannel['members'] = members
            portchannel['members_detail'] = member_dictionary

        # Ensure each member have the same mode.
        modes = set()
        for each, value in member_dictionary.items():
            modes.update([value['mode']])
        if len(modes) == 1:
            portchannel['mode'] = value['mode']
        else:
            portchannel['mode'] = 'unknown'
    return portchannel


def get_existing(module, args):
    existing = {}
    netcfg = CustomNetworkConfig(indent=2, contents=get_config(module))

    interface_exist = check_interface(module, netcfg)
    if interface_exist:
        parents = ['interface port-channel{0}'.format(module.params['group'])]
        config = netcfg.get_section(parents)

        if config:
            existing['min_links'] = get_value('min_links', config, module)
            existing.update(get_portchannel(module, netcfg=netcfg))

    return existing, interface_exist


def config_portchannel(proposed, mode, group, force):
    commands = []
    # NOTE: Leading whitespace for force option is important
    force = ' force' if force else ''
    config_args = {
        'mode': 'channel-group {group}{force} mode {mode}',
        'min_links': 'lacp min-links {min_links}',
    }

    for member in proposed.get('members', []):
        commands.append('interface {0}'.format(member))
        commands.append(config_args.get('mode').format(group=group, force=force, mode=mode))

    min_links = proposed.get('min_links', None)
    if min_links:
        command = 'interface port-channel {0}'.format(group)
        commands.append(command)
        commands.append(config_args.get('min_links').format(
            min_links=min_links))

    return commands


def get_commands_to_add_members(proposed, existing, force, module):
    try:
        proposed_members = proposed['members']
    except KeyError:
        proposed_members = []

    try:
        existing_members = existing['members']
    except KeyError:
        existing_members = []

    members_to_add = list(set(proposed_members).difference(existing_members))

    commands = []
    # NOTE: Leading whitespace for force option is important
    force = ' force' if force else ''
    if members_to_add:
        for member in members_to_add:
            commands.append('interface {0}'.format(member))
            commands.append('channel-group {0}{1} mode {2}'.format(
                existing['group'], force, proposed['mode']))

    return commands


def get_commands_to_remove_members(proposed, existing, module):
    try:
        proposed_members = proposed['members']
    except KeyError:
        proposed_members = []

    try:
        existing_members = existing['members']
    except KeyError:
        existing_members = []

    members_to_remove = list(set(existing_members).difference(proposed_members))
    commands = []
    if members_to_remove:
        for member in members_to_remove:
            commands.append('interface {0}'.format(member))
            commands.append('no channel-group {0}'.format(existing['group']))

    return commands


def get_commands_if_mode_change(proposed, existing, group, mode, force, module):
    try:
        proposed_members = proposed['members']
    except KeyError:
        proposed_members = []

    try:
        existing_members = existing['members']
    except KeyError:
        existing_members = []

    try:
        members_dict = existing['members_detail']
    except KeyError:
        members_dict = {}

    members_to_remove = set(existing_members).difference(proposed_members)
    members_with_mode_change = []
    if members_dict:
        for interface, values in members_dict.items():
            if (interface in proposed_members and
                    (interface not in members_to_remove)):
                if values['mode'] != mode:
                    members_with_mode_change.append(interface)

    commands = []
    # NOTE: Leading whitespace for force option is important
    force = ' force' if force else ''
    if members_with_mode_change:
        for member in members_with_mode_change:
            commands.append('interface {0}'.format(member))
            commands.append('no channel-group {0}'.format(group))

        for member in members_with_mode_change:
            commands.append('interface {0}'.format(member))
            commands.append('channel-group {0}{1} mode {2}'.format(group, force, mode))

    return commands


def get_commands_min_links(existing, proposed, group, min_links, module):
    commands = []
    try:
        if (existing['min_links'] is None or
                (existing['min_links'] != proposed['min_links'])):
            commands.append('interface port-channel{0}'.format(group))
            commands.append('lacp min-link {0}'.format(min_links))
    except KeyError:
        commands.append('interface port-channel{0}'.format(group))
        commands.append('lacp min-link {0}'.format(min_links))
    return commands


def flatten_list(command_lists):
    flat_command_list = []
    for command in command_lists:
        if isinstance(command, list):
            flat_command_list.extend(command)
        else:
            flat_command_list.append(command)
    return flat_command_list


def state_present(module, existing, proposed, interface_exist, force, warnings):
    commands = []
    group = str(module.params['group'])
    mode = module.params['mode']
    min_links = module.params['min_links']

    if not interface_exist:
        command = config_portchannel(proposed, mode, group, force)
        commands.append(command)
        commands.insert(0, 'interface port-channel{0}'.format(group))
        warnings.append("The proposed port-channel interface did not "
                        "exist. It's recommended to use nxos_interface to "
                        "create all logical interfaces.")

    elif existing and interface_exist:
        if force:
            command = get_commands_to_remove_members(proposed, existing, module)
            commands.append(command)

        command = get_commands_to_add_members(proposed, existing, force, module)
        commands.append(command)

        mode_command = get_commands_if_mode_change(proposed, existing, group, mode, force, module)
        commands.insert(0, mode_command)

        if min_links:
            command = get_commands_min_links(existing, proposed, group, min_links, module)
            commands.append(command)

    return commands


def state_absent(module, existing, proposed):
    commands = []
    group = str(module.params['group'])
    commands.append(['no interface port-channel{0}'.format(group)])
    return commands


def main():
    argument_spec = dict(
        group=dict(required=True, type='str'),
        mode=dict(required=False, choices=['on', 'active', 'passive'], default='on', type='str'),
        min_links=dict(required=False, default=None, type='str'),
        members=dict(required=False, default=None, type='list'),
        force=dict(required=False, default='false', type='str', choices=['true', 'false']),
        state=dict(required=False, choices=['absent', 'present'], default='present'),
        include_defaults=dict(default=False),
        config=dict(),
        save=dict(type='bool', default=False)
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    warnings = list()
    results = dict(changed=False, warnings=warnings)

    group = str(module.params['group'])
    mode = module.params['mode']
    min_links = module.params['min_links']
    members = module.params['members']
    state = module.params['state']

    if str(module.params['force']).lower() == 'true':
        force = True
    elif module.params['force'] == 'false':
        force = False

    if ((min_links or mode) and
            (not members and state == 'present')):
        module.fail_json(msg='"members" is required when state=present and '
                             '"min_links" or "mode" are provided')

    args = [
        'group',
        'members',
        'min_links',
        'mode'
    ]

    existing, interface_exist = get_existing(module, args)
    proposed = dict((k, v) for k, v in module.params.items()
                    if v is not None and k in args)

    commands = []

    if state == 'absent' and existing:
        commands = state_absent(module, existing, proposed)
    elif state == 'present':
        commands = state_present(module, existing, proposed, interface_exist, force, warnings)

    cmds = flatten_list(commands)
    if cmds:
        if module.check_mode:
            module.exit_json(**results)
        else:
            load_config(module, cmds)
            results['changed'] = True
            if 'configure' in cmds:
                cmds.pop(0)

    results['commands'] = cmds
    module.exit_json(**results)


if __name__ == '__main__':
    main()
