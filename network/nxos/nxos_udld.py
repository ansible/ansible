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

module: nxos_udld
version_added: "2.2"
short_description: Manages UDLD global configuration params.
description:
    - Manages UDLD global configuration params.
extends_documentation_fragment: nxos
author:
    - Jason Edelman (@jedelman8)
notes:
    - When C(state=absent), it unconfigures existing setings C(msg_time) and set it
      to its default value of 15.  It is cleaner to always use C(state=present).
    - Module will fail if the udld feature has not been previously enabled.
options:
    aggressive:
        description:
            - Toggles aggressive mode.
        required: false
        default: null
        choices: ['enabled','disabled']
    msg_time:
        description:
            - Message time in seconds for UDLD packets.
        required: false
        default: null
    reset:
        description:
            - Ability to reset UDLD down interfaces.
        required: false
        default: null
        choices: ['true','false']
    state:
        description:
            - Manage the state of the resource.
        required: false
        default: present
        choices: ['present','absent']

'''
EXAMPLES = '''
# ensure udld aggressive mode is globally disabled and se global message interval is 20
- nxos_udld:
    aggressive: disabled
    msg_time: 20
    host: {{ inventory_hostname }}
    username: {{ un }}
    password: {{ pwd }}

# Ensure agg mode is globally enabled and msg time is 15
- nxos_udld:
    aggressive: enabled
    msg_time: 15
    host: {{ inventory_hostname }}
    username: {{ un }}
    password: {{ pwd }}
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"aggressive": "enabled", "msg_time": "40"}
existing:
    description:
        - k/v pairs of existing udld configuration
    type: dict
    sample: {"aggressive": "disabled", "msg_time": "15"}
end_state:
    description: k/v pairs of udld configuration after module execution
    returned: always
    type: dict
    sample: {"aggressive": "enabled", "msg_time": "40"}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["udld message-time 40", "udld aggressive"]
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
            body = [json.loads(response[0])]
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



def get_commands_config_udld_global(delta, reset):
    config_args = {
        'enabled': 'udld aggressive',
        'disabled': 'no udld aggressive',
        'msg_time': 'udld message-time {msg_time}'
    }
    commands = []
    for param, value in delta.iteritems():
        if param == 'aggressive':
            if value == 'enabled':
                command = 'udld aggressive'
            elif value == 'disabled':
                command = 'no udld aggressive'
        else:
            command = config_args.get(param, 'DNE').format(**delta)
        if command and command != 'DNE':
            commands.append(command)
        command = None

    if reset:
        command = 'udld reset'
        commands.append(command)
    return commands


def get_commands_remove_udld_global(delta):
    config_args = {
        'aggressive': 'no udld aggressive',
        'msg_time': 'no udld message-time {msg_time}',
    }
    commands = []
    for param, value in delta.iteritems():
        command = config_args.get(param, 'DNE').format(**delta)
        if command and command != 'DNE':
            commands.append(command)
        command = None
    return commands


def get_udld_global(module):
    command = 'show udld global'
    udld_table = execute_show_command(command, module)[0]

    status = str(udld_table.get('udld-global-mode', None))
    if status == 'enabled-aggressive':
        aggressive = 'enabled'
    else:
        aggressive = 'disabled'

    interval = str(udld_table.get('message-interval', None))
    udld = dict(msg_time=interval, aggressive=aggressive)

    return udld


def main():
    argument_spec = dict(
            aggressive=dict(required=False, choices=['enabled', 'disabled']),
            msg_time=dict(required=False, type='str'),
            reset=dict(required=False, type='bool'),
            state=dict(choices=['absent', 'present'], default='present'),
    )
    module = get_network_module(argument_spec=argument_spec,
                                required_one_of=[['aggressive', 'msg_time', 'reset']],
                                supports_check_mode=True)

    aggressive = module.params['aggressive']
    msg_time = module.params['msg_time']
    reset = module.params['reset']
    state = module.params['state']

    if (aggressive or reset) and state == 'absent':
        module.fail_json(msg="It's better to use state=present when "
                             "configuring or unconfiguring aggressive mode "
                             "or using reset flag. state=absent is just for "
                             "when using msg_time param.")

    if msg_time:
        try:
            msg_time_int = int(msg_time)
            if msg_time_int < 7 or msg_time_int > 90:
                raise ValueError
        except ValueError:
            module.fail_json(msg='msg_time must be an integer'
                                 'between 7 and 90')

    args = dict(aggressive=aggressive, msg_time=msg_time, reset=reset)
    proposed = dict((k, v) for k, v in args.iteritems() if v is not None)

    existing = get_udld_global(module)
    end_state = existing

    delta = set(proposed.iteritems()).difference(existing.iteritems())
    changed = False

    commands = []
    if state == 'present':
        if delta:
            command = get_commands_config_udld_global(dict(delta), reset)
            commands.append(command)

    elif state == 'absent':
        common = set(proposed.iteritems()).intersection(existing.iteritems())
        if common:
            command = get_commands_remove_udld_global(dict(common))
            commands.append(command)

    cmds = flatten_list(commands)
    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            changed = True
            execute_config_command(cmds, module)
            end_state = get_udld_global(module)
            if 'configure' in cmds:
                cmds.pop(0)

    results = {}
    results['proposed'] = proposed
    results['existing'] = existing
    results['end_state'] = end_state
    results['updates'] = cmds
    results['changed'] = changed

    module.exit_json(**results)


if __name__ == '__main__':
    main()
