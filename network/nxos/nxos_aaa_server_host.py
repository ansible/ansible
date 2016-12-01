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
module: nxos_aaa_server_host
version_added: "2.2"
short_description: Manages AAA server host-specific configuration.
description:
    - Manages AAA server host-specific configuration.
extends_documentation_fragment: nxos
author: Jason Edelman (@jedelman8)
notes:
    - Changes to the AAA server host key (shared secret) are not idempotent.
    - If C(state=absent) removes the whole host configuration.
options:
    server_type:
        description:
            - The server type is either radius or tacacs.
        required: true
        choices: ['radius', 'tacacs']
    address:
        description:
            - Address or name of the radius or tacacs host.
        required: true
    key:
        description:
            - Shared secret for the specified host.
        required: false
        default: null
    encrypt_type:
        description:
            - The state of encryption applied to the entered key.
              O for clear text, 7 for encrypted. Type-6 encryption is
              not supported.
        required: false
        default: null
        choices: ['0', '7']
    host_timeout:
        description:
            - Timeout period for specified host, in seconds. Range is 1-60.
        required: false
        default: null
    auth_port:
        description:
            - Alternate UDP port for RADIUS authentication.
        required: false
        default: null
    acct_port:
        description:
            - Alternate UDP port for RADIUS accounting.
        required: false
        default: null
    tacacs_port:
        description:
            - Alternate TCP port TACACS Server.
        required: false
        default: null
    state:
        description:
            - Manage the state of the resource.
        required: false
        default: present
        choices: ['present','absent']
'''
EXAMPLES = '''
# Radius Server Host Basic settings
  - name: "Radius Server Host Basic settings"
    nxos_aaa_server_host:
        state: present
        server_type: radius
        address: 1.2.3.4
        acct_port: 2084
        host_timeout: 10
        host: "{{ inventory_hostname }}"
        username: "{{ un }}"
        password: "{{ pwd }}"

# Radius Server Host Key Configuration
  - name: "Radius Server Host Key Configuration"
    nxos_aaa_server_host:
        state: present
        server_type: radius
        address: 1.2.3.4
        key: hello
        encrypt_type: 7
        host:  inventory_hostname }}
        username: "{{ un }}"
        password: "{{ pwd }}"

# TACACS Server Host Configuration
  - name: "Tacacs Server Host Configuration"
    nxos_aaa_server_host:
        state: present
        server_type: tacacs 
        tacacs_port: 89
        host_timeout: 10
        address: 5.6.7.8
        host:  inventory_hostname }}
        username:  un }}
        password:  pwd }}
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"address": "1.2.3.4", "auth_port": "2084", 
            "host_timeout": "10", "server_type": "radius"}
existing:
    description:
        - k/v pairs of existing configuration
    type: dict
    sample: {}
end_state:
    description: k/v pairs of configuration after module execution
    returned: always
    type: dict
    sample: {"address": "1.2.3.4", "auth_port": "2084", 
            "host_timeout": "10", "server_type": "radius"}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["radius-server host 1.2.3.4 auth-port 2084 timeout 10"]
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


def _match_dict(match_list, key_map):
    no_blanks = []
    match_dict = {}

    for match_set in match_list:
        match_set = tuple(v for v in match_set if v)
        no_blanks.append(match_set)

    for info in no_blanks:
        words = info[0].strip().split()
        length = len(words)
        alt_key = key_map.get(words[0])
        first = alt_key or words[0]
        last = words[length - 1]
        match_dict[first] = last.replace('\"', '')

    return match_dict


def get_aaa_host_info(module, server_type, address):
    aaa_host_info = {}
    command = 'show run | inc {0}-server.host.{1}'.format(server_type, address)
    
    body = execute_show_command(command, module, command_type='cli_show_ascii')

    if body:
        try:
            pattern = ('(acct-port \d+)|(timeout \d+)|(auth-port \d+)|'
                       '(key 7 "\w+")|( port \d+)')
            raw_match = re.findall(pattern, body[0])
            aaa_host_info = _match_dict(raw_match, {'acct-port': 'acct_port',
                                                    'auth-port': 'auth_port',
                                                    'port': 'tacacs_port',
                                                    'timeout': 'host_timeout'})
            if aaa_host_info:
                aaa_host_info['server_type'] = server_type
                aaa_host_info['address'] = address
        except TypeError:
            return {}
    else:
        return {}

    return aaa_host_info


def config_aaa_host(server_type, address, params, clear=False):
    cmds = []

    if clear:
        cmds.append('no {0}-server host {1}'.format(server_type, address))

    cmd_str = '{0}-server host {1}'.format(server_type, address)

    key = params.get('key')
    enc_type = params.get('encrypt_type', '')
    host_timeout = params.get('host_timeout')
    auth_port = params.get('auth_port')
    acct_port = params.get('acct_port')
    port = params.get('tacacs_port')

    if auth_port:
        cmd_str += ' auth-port {0}'.format(auth_port)
    if acct_port:
        cmd_str += ' acct-port {0}'.format(acct_port)
    if port:
        cmd_str += ' port {0}'.format(port)
    if host_timeout:
        cmd_str += ' timeout {0}'.format(host_timeout)
    if key:
        cmds.append('{0}-server host {1} key {2} {3}'.format(server_type,
                                                             address,
                                                             enc_type, key))

    cmds.append(cmd_str)
    return cmds


def main():
    argument_spec = dict(
            server_type=dict(choices=['radius', 'tacacs'], required=True),
            address=dict(type='str', required=True),
            key=dict(type='str'),
            encrypt_type=dict(type='str', choices=['0', '7']),
            host_timeout=dict(type='str'),
            auth_port=dict(type='str'),
            acct_port=dict(type='str'),
            tacacs_port=dict(type='str'),
            state=dict(choices=['absent', 'present'], default='present'),
    )
    module = get_network_module(argument_spec=argument_spec,
                                supports_check_mode=True)

    server_type = module.params['server_type']
    address = module.params['address']
    key = module.params['key']
    encrypt_type = module.params['encrypt_type']
    host_timeout = module.params['host_timeout']
    auth_port = module.params['auth_port']
    acct_port = module.params['acct_port']
    tacacs_port = module.params['tacacs_port']
    state = module.params['state']

    args = dict(server_type=server_type, address=address, key=key,
                encrypt_type=encrypt_type, host_timeout=host_timeout,
                auth_port=auth_port, acct_port=acct_port,
                tacacs_port=tacacs_port)

    proposed = dict((k, v) for k, v in args.iteritems() if v is not None)
    changed = False

    if encrypt_type and not key:
        module.fail_json(msg='encrypt_type must be used with key')

    if tacacs_port and server_type != 'tacacs':
        module.fail_json(
            msg='tacacs_port can only be used with server_type=tacacs')

    if (auth_port or acct_port) and server_type != 'radius':
        module.fail_json(msg='auth_port and acct_port can only be used'
                             'when server_type=radius')


    existing = get_aaa_host_info(module, server_type, address)
    end_state = existing

    commands = []
    if state == 'present':
        host_timeout = proposed.get('host_timeout')
        if host_timeout:
            try:
                if int(host_timeout) < 1 or int(host_timeout) > 60:
                    raise ValueError
            except ValueError:
                module.fail_json(
                    msg='host_timeout must be an integer between 1 and 60')

        delta = dict(
                set(proposed.iteritems()).difference(existing.iteritems()))
        if delta:
            union = existing.copy()
            union.update(delta)
            command = config_aaa_host(server_type, address, union)
            if command:
                commands.append(command)

    elif state == 'absent':
        intersect = dict(
                set(proposed.iteritems()).intersection(existing.iteritems()))
        if intersect.get('address') and intersect.get('server_type'):
            command = 'no {0}-server host {1}'.format(
                        intersect.get('server_type'), intersect.get('address'))
            commands.append(command)

    cmds = flatten_list(commands)
    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            changed = True
            execute_config_command(cmds, module)
            end_state = get_aaa_host_info(module, server_type, address)

    results = {}
    results['proposed'] = proposed
    results['existing'] = existing
    results['updates'] = cmds
    results['changed'] = changed
    results['end_state'] = end_state
 
    module.exit_json(**results)


if __name__ == '__main__':
    main()
