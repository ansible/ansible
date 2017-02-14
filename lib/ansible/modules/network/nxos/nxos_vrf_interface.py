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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: nxos_vrf_interface
version_added: "2.1"
short_description: Manages interface specific VRF configuration.
description:
    - Manages interface specific VRF configuration.
extends_documentation_fragment: nxos
author:
    - Jason Edelman (@jedelman8)
    - Gabriele Gerbino (@GGabriele)
notes:
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
    host: 68.170.147.165
    state: present

- name: Ensure ntc VRF does not exist on Eth1/1
  nxos_vrf_interface:
    vrf: ntc
    interface: Ethernet1/1
    host: 68.170.147.165
    state: absent
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

import json
import collections

# COMMON CODE FOR MIGRATION
import re

from ansible.module_utils.basic import get_exception
from ansible.module_utils.netcfg import NetworkConfig, ConfigLine
from ansible.module_utils.shell import ShellError

try:
    from ansible.module_utils.nxos import get_module
except ImportError:
    from ansible.module_utils.nxos import NetworkModule


def to_list(val):
    if isinstance(val, (list, tuple)):
        return list(val)
    elif val is not None:
        return [val]
    else:
        return list()


class CustomNetworkConfig(NetworkConfig):

    def expand_section(self, configobj, S=None):
        if S is None:
            S = list()
        S.append(configobj)
        for child in configobj.children:
            if child in S:
                continue
            self.expand_section(child, S)
        return S

    def get_object(self, path):
        for item in self.items:
            if item.text == path[-1]:
                parents = [p.text for p in item.parents]
                if parents == path[:-1]:
                    return item

    def to_block(self, section):
        return '\n'.join([item.raw for item in section])

    def get_section(self, path):
        try:
            section = self.get_section_objects(path)
            return self.to_block(section)
        except ValueError:
            return list()

    def get_section_objects(self, path):
        if not isinstance(path, list):
            path = [path]
        obj = self.get_object(path)
        if not obj:
            raise ValueError('path does not exist in config')
        return self.expand_section(obj)


    def add(self, lines, parents=None):
        """Adds one or lines of configuration
        """

        ancestors = list()
        offset = 0
        obj = None

        ## global config command
        if not parents:
            for line in to_list(lines):
                item = ConfigLine(line)
                item.raw = line
                if item not in self.items:
                    self.items.append(item)

        else:
            for index, p in enumerate(parents):
                try:
                    i = index + 1
                    obj = self.get_section_objects(parents[:i])[0]
                    ancestors.append(obj)

                except ValueError:
                    # add parent to config
                    offset = index * self.indent
                    obj = ConfigLine(p)
                    obj.raw = p.rjust(len(p) + offset)
                    if ancestors:
                        obj.parents = list(ancestors)
                        ancestors[-1].children.append(obj)
                    self.items.append(obj)
                    ancestors.append(obj)

            # add child objects
            for line in to_list(lines):
                # check if child already exists
                for child in ancestors[-1].children:
                    if child.text == line:
                        break
                else:
                    offset = len(parents) * self.indent
                    item = ConfigLine(line)
                    item.raw = line.rjust(len(line) + offset)
                    item.parents = ancestors
                    ancestors[-1].children.append(item)
                    self.items.append(item)


def get_network_module(**kwargs):
    try:
        return get_module(**kwargs)
    except NameError:
        return NetworkModule(**kwargs)

def get_config(module, include_defaults=False):
    config = module.params['config']
    if not config:
        try:
            config = module.get_config()
        except AttributeError:
            defaults = module.params['include_defaults']
            config = module.config.get_config(include_defaults=defaults)
    return CustomNetworkConfig(indent=2, contents=config)

def load_config(module, candidate):
    config = get_config(module)

    commands = candidate.difference(config)
    commands = [str(c).strip() for c in commands]

    save_config = module.params['save']

    result = dict(changed=False)

    if commands:
        if not module.check_mode:
            try:
                module.configure(commands)
            except AttributeError:
                module.config(commands)

            if save_config:
                try:
                    module.config.save_config()
                except AttributeError:
                    module.execute(['copy running-config startup-config'])

        result['changed'] = True
        result['updates'] = commands

    return result
# END OF COMMON CODE

WARNINGS = []

def execute_config_command(commands, module):
    try:
        module.configure(commands)
    except ShellError:
        clie = get_exception()
        module.fail_json(msg='Error sending CLI commands',
                         error=str(clie), commands=commands)
    except AttributeError:
        try:
            commands.insert(0, 'configure')
            module.cli.add_commands(commands, output='config')
            module.cli.run_commands()
        except ShellError:
            clie = get_exception()
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
    command_type_map = {
        'cli_show': 'json',
        'cli_show_ascii': 'text'
    }

    try:
        if command_type:
            response = module.execute(cmds, command_type=command_type)
        else:
            response = module.execute(cmds)
    except ShellError:
        clie = get_exception()
        module.fail_json(msg='Error sending {0}'.format(cmds),
                         error=str(clie))
    except AttributeError:
        try:
            if command_type:
                command_type = command_type_map.get(command_type)
                module.cli.add_commands(cmds, output=command_type)
                response = module.cli.run_commands()
            else:
                module.cli.add_commands(cmds, raw=True)
                response = module.cli.run_commands()
        except ShellError:
            clie = get_exception()
            module.fail_json(msg='Error sending {0}'.format(cmds),
                             error=str(clie))
    return response


def execute_show_command(command, module, command_type='cli_show'):
    if module.params['transport'] == 'cli':
        if 'show run' not in command:
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
    if not interface.startswith('loopback'):
        interface = interface.capitalize()
    command = 'show run | section interface.{0}'.format(interface)
    vrf_regex = ".*vrf\s+member\s+(?P<vrf>\S+).*"

    try:
        body = execute_show_command(command, module,
                                    command_type='cli_show_ascii')[0]
        match_vrf = re.match(vrf_regex, body, re.DOTALL)
        group_vrf = match_vrf.groupdict()
        vrf = group_vrf["vrf"]
    except (AttributeError, TypeError):
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
        include_defaults=dict(default=False),
        config=dict(),
        save=dict(type='bool', default=False)
    )
    module = get_network_module(argument_spec=argument_spec,
                                supports_check_mode=True)

    vrf = module.params['vrf']
    interface = module.params['interface'].lower()
    state = module.params['state']

    current_vrfs = get_vrf_list(module)
    if vrf not in current_vrfs:
        WARNINGS.append("The VRF is not present/active on the device. "
                        "Use nxos_vrf to fix this.")

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
            if 'configure' in commands:
                commands.pop(0)

    results = {}
    results['proposed'] = proposed
    results['existing'] = existing
    results['end_state'] = end_state
    results['updates'] = commands
    results['changed'] = changed

    if WARNINGS:
        results['warnings'] = WARNINGS

    module.exit_json(**results)


if __name__ == '__main__':
    main()
