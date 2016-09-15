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

module: nxos_aaa_server
version_added: "2.2"
short_description: Manages AAA server global configuration.
description:
    - Manages AAA server global configuration
extends_documentation_fragment: nxos
author:
    - Jason Edelman (@jedelman8)
notes:
    - The server_type parameter is always required.
    - If encrypt_type is not supplied, the global AAA server key will be
      stored as encrypted (type 7).
    - Changes to the global AAA server key with encrypt_type=0
      are not idempotent.
    - If global AAA server key is not found, it's shown as "unknown"
    - state=default will set the supplied parameters to their default values.
      The parameters that you want to default must also be set to default.
      If global_key=default, the global key will be removed.
options:
    server_type:
        description:
            - The server type is either radius or tacacs.
        required: true
        choices: ['radius', 'tacacs']
    global_key:
        description:
            - Global AAA shared secret.
        required: false
        default: null
    encrypt_type:
        description:
            - The state of encryption applied to the entered global key.
              O clear text, 7 encrypted. Type-6 encryption is not supported.
        required: false
        default: null
        choices: ['0', '7']
    deadtime:
        description:
            - Duration for which a non-reachable AAA server is skipped,
              in minutes. Range is 1-1440. Device default is 0.
        required: false
        default: null
    server_timeout:
        description:
            - Global AAA server timeout period, in seconds. Range is 1-60.
              Device default is 5.
        required: false
        default: null
    directed_request:
        description:
            - Enables direct authentication requests to AAA server.
              Device default is disabled.
        required: false
        default: null
        choices: ['enabled', 'disabled']
    state:
        description:
            - Manage the state of the resource.
        required: true
        default: present
        choices: ['present','default']
'''

EXAMPLES = '''
# Radius Server Basic settings
  - name: "Radius Server Basic settings"
    nxos_aaa_server:
        server_type=radius
        server_timeout=9
        deadtime=20
        directed_request=enabled
        host={{ inventory_hostname }}
        username={{ un }}
        password={{ pwd }}

# Tacacs Server Basic settings
  - name: "Tacacs Server Basic settings"
    nxos_aaa_server:
        server_type=tacacs
        server_timeout=8
        deadtime=19
        directed_request=disabled
        host={{ inventory_hostname }}
        username={{ un }}
        password={{ pwd }}

# Setting Global Key
  - name: "AAA Server Global Key"
    nxos_aaa_server:
        server_type=radius
        global_key=test_key
        host={{ inventory_hostname }}
        username={{ un }}
        password={{ pwd }}
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"deadtime": "22", "directed_request": "enabled",
            "server_type": "radius", "server_timeout": "11"}
existing:
    description:
        - k/v pairs of existing aaa server
    type: dict
    sample: {"deadtime": "0", "directed_request": "disabled",
            "global_key": "unknown", "server_timeout": "5"}
end_state:
    description: k/v pairs of aaa params after module execution
    returned: always
    type: dict
    sample: {"deadtime": "22", "directed_request": "enabled",
            "global_key": "unknown", "server_timeout": "11"}
state:
    description: state as sent in from the playbook
    returned: always
    type: string
    sample: "present"
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["radius-server deadtime 22", "radius-server timeout 11",
             "radius-server directed-request"]
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
    cmds = [command]
    if module.params['transport'] == 'cli':
        body = execute_show(cmds, module)
    elif module.params['transport'] == 'nxapi':
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



def get_aaa_server_info(server_type, module):
    aaa_server_info = {}
    server_command = 'show {0}-server'.format(server_type)
    request_command = 'show {0}-server directed-request'.format(server_type)
    global_key_command = 'show run | sec {0}'.format(server_type)
    aaa_regex = '.*{0}-server\skey\s\d\s+(?P<key>\S+).*'.format(server_type)

    server_body = execute_show_command(
                server_command, module, command_type='cli_show_ascii')[0]

    split_server = server_body.splitlines()

    for line in split_server:
        if line.startswith('timeout'):
            aaa_server_info['server_timeout'] = line.split(':')[1]

        elif line.startswith('deadtime'):
            aaa_server_info['deadtime'] = line.split(':')[1]

    request_body = execute_show_command(
                request_command, module, command_type='cli_show_ascii')[0]
    aaa_server_info['directed_request'] = request_body.replace('\n', '')

    key_body = execute_show_command(
                global_key_command, module, command_type='cli_show_ascii')[0]

    try:
        match_global_key = re.match(aaa_regex, key_body, re.DOTALL)
        group_key = match_global_key.groupdict()
        aaa_server_info['global_key'] = group_key["key"].replace('\"', '')
    except (AttributeError, TypeError):
        aaa_server_info['global_key'] = 'unknown'

    return aaa_server_info


def set_aaa_server_global_key(encrypt_type, key, server_type):
    if not encrypt_type:
        encrypt_type = ''
    return '{0}-server key {1} {2}'.format(
        server_type, encrypt_type, key)


def config_aaa_server(params, server_type):
    cmds = []

    deadtime = params.get('deadtime')
    server_timeout = params.get('server_timeout')
    directed_request = params.get('directed_request')
    encrypt_type = params.get('encrypt_type', '7')
    global_key = params.get('global_key')

    if deadtime is not None:
        cmds.append('{0}-server deadtime {1}'.format(server_type, deadtime))

    if server_timeout is not None:
        cmds.append('{0}-server timeout {1}'.format(server_type, server_timeout))

    if directed_request is not None:
        if directed_request == 'enabled':
            cmds.append('{0}-server directed-request'.format(server_type))
        elif directed_request == 'disabled':
            cmds.append('no {0}-server directed-request'.format(server_type))

    if global_key is not None:
        cmds.append('{0}-server key {1} {2}'.format(server_type, encrypt_type,
                                                    global_key))

    return cmds


def default_aaa_server(existing, params, server_type):
    cmds = []

    deadtime = params.get('deadtime')
    server_timeout = params.get('server_timeout')
    directed_request = params.get('directed_request')
    global_key = params.get('global_key')
    existing_key = existing.get('global_key')

    if deadtime is not None:
        cmds.append('no {0}-server deadtime 1'.format(server_type))

    if server_timeout is not None:
        cmds.append('no {0}-server timeout 1'.format(server_type))

    if directed_request is not None:
        cmds.append('no {0}-server directed-request'.format(server_type))

    if global_key is not None and existing_key is not None:
        cmds.append('no {0}-server key 7 {1}'.format(server_type, existing_key))

    return cmds


def main():
    argument_spec = dict(
            server_type=dict(type='str',
                             choices=['radius', 'tacacs'], required=True),
            global_key=dict(type='str'),
            encrypt_type=dict(type='str', choices=['0', '7']),
            deadtime=dict(type='str'),
            server_timeout=dict(type='str'),
            directed_request=dict(type='str',
                                  choices=['enabled', 'disabled', 'default']),
            state=dict(choices=['default', 'present'], default='present'),
    )
    module = get_network_module(argument_spec=argument_spec,
                                supports_check_mode=True)
    
    server_type = module.params['server_type']
    global_key = module.params['global_key']
    encrypt_type = module.params['encrypt_type']
    deadtime = module.params['deadtime']
    server_timeout = module.params['server_timeout']
    directed_request = module.params['directed_request']
    state = module.params['state']

    if encrypt_type and not global_key:
        module.fail_json(msg='encrypt_type must be used with global_key.')

    args = dict(server_type=server_type, global_key=global_key,
                encrypt_type=encrypt_type, deadtime=deadtime,
                server_timeout=server_timeout, directed_request=directed_request)

    changed = False
    proposed = dict((k, v) for k, v in args.iteritems() if v is not None)

    existing = get_aaa_server_info(server_type, module)
    end_state = existing

    commands = []
    if state == 'present':
        if deadtime:
            try:
                if int(deadtime) < 0 or int(deadtime) > 1440:
                    raise ValueError
            except ValueError:
                module.fail_json(
                        msg='deadtime must be an integer between 0 and 1440')

        if server_timeout:
            try:
                if int(server_timeout) < 1 or int(server_timeout) > 60:
                    raise ValueError
            except ValueError:
                module.fail_json(
                    msg='server_timeout must be an integer between 1 and 60')

        delta = dict(set(proposed.iteritems()).difference(
                                                    existing.iteritems()))
        if delta:
            command = config_aaa_server(delta, server_type)
            if command:
                commands.append(command)

    elif state == 'default':
        for key, value in proposed.iteritems():
            if key != 'server_type' and value != 'default':
                module.fail_json(
                    msg='Parameters must be set to "default"'
                        'when state=default')
        command = default_aaa_server(existing, proposed, server_type)
        if command:
            commands.append(command)
    
    cmds = flatten_list(commands)
    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            changed = True
            execute_config_command(cmds, module)
            end_state = get_aaa_server_info(server_type, module)

    results = {}
    results['proposed'] = proposed
    results['existing'] = existing
    results['updates'] = cmds
    results['changed'] = changed
    results['end_state'] = end_state

    module.exit_json(**results)


if __name__ == '__main__':
    main()