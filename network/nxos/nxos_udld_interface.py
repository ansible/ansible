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
module: nxos_udld_interface
version_added: "2.2"
short_description: Manages UDLD interface configuration params.
description:
    - Manages UDLD interface configuration params.
extends_documentation_fragment: nxos
author:
    - Jason Edelman (@jedelman8)
notes:
    - Feature UDLD must be enabled on the device to use this module.
options:
    mode:
        description:
            - Manages UDLD mode for an interface.
        required: true
        choices: ['enabled','disabled','aggressive']
    interface:
        description:
            - FULL name of the interface, i.e. Ethernet1/1-
        required: true
    state:
        description:
            - Manage the state of the resource.
        required: false
        default: present
        choices: ['present','absent']
'''
EXAMPLES = '''
# ensure Ethernet1/1 is configured to be in aggressive mode
- nxos_udld_interface:
    interface=Ethernet1/1
    mode=aggressive
    state=present
    host={{ inventory_hostname }}
    username={{ un }}
    password={{ pwd }}

# Remove the aggressive config only if it's currently in aggressive mode and then disable udld (switch default)
- nxos_udld_interface:
    interface=Ethernet1/1
    mode=aggressive
    state=absent
    host={{ inventory_hostname }}
    username={{ un }}
    password={{ pwd }}

# ensure Ethernet1/1 has aggressive mode enabled
- nxos_udld_interface:
    interface=Ethernet1/1
    mode=enabled
    host={{ inventory_hostname }}
    username={{ un }}
    password={{ pwd }}
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"mode": "enabled"}
existing:
    description:
        - k/v pairs of existing configuration
    type: dict
    sample: {"mode": "aggressive"}
end_state:
    description: k/v pairs of configuration after module execution
    returned: always
    type: dict
    sample: {"mode": "enabled"}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["interface ethernet1/33", 
            "no udld aggressive ; no udld disable"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''


import json

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


def get_cli_body_ssh(command, response, module):
    """Get response for when transport=cli.  This is kind of a hack and mainly
    needed because these modules were originally written for NX-API.  And
    not every command supports "| json" when using cli/ssh.  As such, we assume
    if | json returns an XML string, it is a valid command, but that the
    resource doesn't exist yet. Instead, the output will be a raw string
    when issuing commands containing 'show run'.
    """
    if 'xml' in response[0] or response[0] == '\n':
        body = []
    elif 'show run' in command:
        body = response
    else:
        try:
            if isinstance(response[0], str):
                body = [json.loads(response[0])]
            else:
                body = response
        except ValueError:
            module.fail_json(msg='Command does not support JSON output',
                             command=command)
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
                module.cli.add_commands(cmds)
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
        body = get_cli_body_ssh(command, response, module)
    elif module.params['transport'] == 'nxapi':
        cmds = [command]
        body = execute_show(cmds, module, command_type=command_type)

    return body


def flatten_list(command_lists):
    flat_command_list = []
    for command in command_lists:
        if isinstance(command, list):
            flat_command_list.extend(command)
        else:
            flat_command_list.append(command)
    return flat_command_list


def get_udld_interface(module, interface):
    command = 'show udld {0}'.format(interface)
    interface_udld = {}
    mode = None
    try:
        body = execute_show_command(command, module)[0]
        table = body['TABLE_interface']['ROW_interface']

        status = str(table.get('mib-port-status', None))
        agg = str(table.get('mib-aggresive-mode', 'disabled'))

        if agg == 'enabled':
            mode = 'aggressive'
        else:
            mode = status

        interface_udld['mode'] = mode

    except (KeyError, AttributeError, IndexError):
        interface_udld = {}

    return interface_udld


def is_interface_copper(module, interface):
    command = 'show interface status'
    copper = []
    try:
        body = execute_show_command(command, module)[0]
        table = body['TABLE_interface']['ROW_interface']
        for each in table:
            itype = each.get('type', 'DNE')
            if 'CU' in itype or '1000' in itype or '10GBaseT' in itype:
                copper.append(str(each['interface'].lower()))
    except (KeyError, AttributeError):
        pass

    if interface in copper:
        found = True
    else:
        found = False

    return found


def get_commands_config_udld_interface(delta, interface, module, existing):
    commands = []
    copper = is_interface_copper(module, interface)
    if delta:
        mode = delta['mode']
        if mode == 'aggressive':
            command = 'udld aggressive'
        elif copper:
            if mode == 'enabled':
                if existing['mode'] == 'aggressive':
                    command = 'no udld aggressive ; udld enable'
                else:
                    command = 'udld enable'
            elif mode == 'disabled':
                command = 'no udld enable'
        elif not copper:
            if mode == 'enabled':
                if existing['mode'] == 'aggressive':
                    command = 'no udld aggressive ; no udld disable'
                else:
                    command = 'no udld disable'
            elif mode == 'disabled':
                command = 'udld disable'
    if command:
        commands.append(command)
        commands.insert(0, 'interface {0}'.format(interface))

    return commands


def get_commands_remove_udld_interface(delta, interface, module, existing):
    commands = []
    copper = is_interface_copper(module, interface)

    if delta:
        mode = delta['mode']
        if mode == 'aggressive':
            command = 'no udld aggressive'
        elif copper:
            if mode == 'enabled':
                command = 'no udld enable'
            elif mode == 'disabled':
                command = 'udld enable'
        elif not copper:
            if mode == 'enabled':
                command = 'udld disable'
            elif mode == 'disabled':
                command = 'no udld disable'
    if command:
        commands.append(command)
        commands.insert(0, 'interface {0}'.format(interface))

    return commands


def main():
    argument_spec = dict(
            mode=dict(choices=['enabled', 'disabled', 'aggressive'],
                      required=True),
            interface=dict(type='str', required=True),
            state=dict(choices=['absent', 'present'], default='present'),
    )
    module = get_network_module(argument_spec=argument_spec,
                                supports_check_mode=True)

    interface = module.params['interface'].lower()
    mode = module.params['mode']
    state = module.params['state']

    proposed = dict(mode=mode)
    existing = get_udld_interface(module, interface)
    end_state = existing

    delta = dict(set(proposed.iteritems()).difference(existing.iteritems()))

    changed = False
    commands = []
    if state == 'present':
        if delta:
            command = get_commands_config_udld_interface(delta, interface,
                                                         module, existing)
            commands.append(command)
    elif state == 'absent':
        common = set(proposed.iteritems()).intersection(existing.iteritems())
        if common:
            command = get_commands_remove_udld_interface(
                dict(common), interface, module, existing
                )
            commands.append(command)

    cmds = flatten_list(commands)
    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            changed = True
            execute_config_command(cmds, module)
            end_state = get_udld_interface(module, interface)

    results = {}
    results['proposed'] = proposed
    results['existing'] = existing
    results['end_state'] = end_state
    results['updates'] = cmds
    results['changed'] = changed

    module.exit_json(**results)

if __name__ == '__main__':
    main()