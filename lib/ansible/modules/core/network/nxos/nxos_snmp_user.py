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
module: nxos_snmp_user
version_added: "2.2"
short_description: Manages SNMP users for monitoring.
description:
    - Manages SNMP user configuration.
extends_documentation_fragment: nxos
author:
    - Jason Edelman (@jedelman8)
notes:
    - Authentication parameters not idempotent.
options:
    user:
        description:
            - Name of the user.
        required: true
    group:
        description:
            - Group to which the user will belong to.
        required: true
    auth:
        description:
            - Auth parameters for the user.
        required: false
        default: null
        choices: ['md5', 'sha']
    pwd:
        description:
            - Auth password when using md5 or sha.
        required: false
        default: null
    privacy:
        description:
            - Privacy password for the user.
        required: false
        default: null
    encrypt:
        description:
            - Enables AES-128 bit encryption when using privacy password.
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
- nxos_snmp_user:
    user: ntc
    group: network-operator
    auth: md5
    pwd: test_password
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"authentication": "md5", "group": "network-operator", 
            "pwd": "test_password", "user": "ntc"}
existing:
    description:
        - k/v pairs of existing configuration
    type: dict
    sample: {"authentication": "no", "encrypt": "none", 
             "group": ["network-operator"], "user": "ntc"}
end_state:
    description: k/v pairs configuration vtp after module execution
    returned: always
    type: dict
    sample: {"authentication": "md5", "encrypt": "none", 
             "group": ["network-operator"], "user": "ntc"}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["snmp-server user ntc network-operator auth md5 test_password"]
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


def get_cli_body_ssh(command, response, module, text=False):
    """Get response for when transport=cli.  This is kind of a hack and mainly
    needed because these modules were originally written for NX-API.  And
    not every command supports "| json" when using cli/ssh.  As such, we assume
    if | json returns an XML string, it is a valid command, but that the
    resource doesn't exist yet. Instead, the output will be a raw string
    when issuing commands containing 'show run'.
    """
    if 'xml' in response[0] or response[0] == '\n':
        body = []
    elif 'show run' in command or text:
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


def execute_show_command(command, module, command_type='cli_show', text=False):
    if module.params['transport'] == 'cli':
        if 'show run' not in command and text is False:
            command += ' | json'
        cmds = [command]
        response = execute_show(cmds, module)
        body = get_cli_body_ssh(command, response, module, text=text)
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


def get_snmp_groups(module):
    command = 'show snmp group'
    body = execute_show_command(command, module)
    g_list = []

    try:
        group_table = body[0]['TABLE_role']['ROW_role']
        for each in group_table:
            g_list.append(each['role_name'])

    except (KeyError, AttributeError, IndexError):
        return g_list

    return g_list


def get_snmp_user(user, module):
    command = 'show snmp user {0}'.format(user)
    body = execute_show_command(command, module, text=True)

    if 'No such entry' not in body[0]:
        body = execute_show_command(command, module)

    resource = {}
    group_list = []
    try:
        resource_table = body[0]['TABLE_snmp_users']['ROW_snmp_users']
        resource['user'] = str(resource_table['user'])
        resource['authentication'] = str(resource_table['auth']).strip()
        encrypt = str(resource_table['priv']).strip()
        if encrypt.startswith('aes'):
            resource['encrypt'] = 'aes-128'
        else:
            resource['encrypt'] = 'none'

        group_table = resource_table['TABLE_groups']['ROW_groups']

        groups = []
        try:
            for group in group_table:
                groups.append(str(group['group']).strip())
        except TypeError:
            groups.append(str(group_table['group']).strip())

        resource['group'] = groups

    except (KeyError, AttributeError, IndexError, TypeError):
        return resource

    return resource


def remove_snmp_user(user):
    return ['no snmp-server user {0}'.format(user)]


def config_snmp_user(proposed, user, reset, new):
    if reset and not new:
        commands = remove_snmp_user(user)
    else:
        commands = []

    group = proposed.get('group', None)

    cmd = ''

    if group:
        cmd = 'snmp-server user {0} {group}'.format(user, **proposed)

    auth = proposed.get('authentication', None)
    pwd = proposed.get('pwd', None)

    if auth and pwd:
        cmd += ' auth {authentication} {pwd}'.format(**proposed)

    encrypt = proposed.get('encrypt', None)
    privacy = proposed.get('privacy', None)

    if encrypt and privacy:
        cmd += ' priv {encrypt} {privacy}'.format(**proposed)
    elif privacy:
        cmd += ' priv {privacy}'.format(**proposed)

    if cmd:
        commands.append(cmd)

    return commands


def main():
    argument_spec = dict(
            user=dict(required=True, type='str'),
            group=dict(type='str', required=True),
            pwd=dict(type='str'),
            privacy=dict(type='str'),
            authentication=dict(choices=['md5', 'sha']),
            encrypt=dict(type='bool'),
            state=dict(choices=['absent', 'present'], default='present'),
    )
    module = get_network_module(argument_spec=argument_spec,
                                required_together=[['authentication', 'pwd'],
                                                  ['encrypt', 'privacy']],
                                supports_check_mode=True)

    user = module.params['user']
    group = module.params['group']
    pwd = module.params['pwd']
    privacy = module.params['privacy']
    encrypt = module.params['encrypt']
    authentication = module.params['authentication']
    state = module.params['state']

    if privacy and encrypt:
        if not pwd and authentication:
            module.fail_json(msg='pwd and authentication must be provided '
                                 'when using privacy and encrypt')

    if group and group not in get_snmp_groups(module):
        module.fail_json(msg='group not configured yet on switch.')

    existing = get_snmp_user(user, module)
    end_state = existing

    store = existing.get('group', None)
    if existing:
        if group not in existing['group']:
            existing['group'] = None
        else:
            existing['group'] = group

    changed = False
    commands = []
    proposed = {}

    if state == 'absent' and existing:
        commands.append(remove_snmp_user(user))

    elif state == 'present':
        new = False
        reset = False

        args = dict(user=user, pwd=pwd, group=group, privacy=privacy,
                    encrypt=encrypt, authentication=authentication)
        proposed = dict((k, v) for k, v in args.iteritems() if v is not None)

        if not existing:
            if encrypt:
                proposed['encrypt'] = 'aes-128'
            commands.append(config_snmp_user(proposed, user, reset, new))

        elif existing:
            if encrypt and not existing['encrypt'].startswith('aes'):
                reset = True
                proposed['encrypt'] = 'aes-128'

            elif encrypt:
                proposed['encrypt'] = 'aes-128'

            delta = dict(
                    set(proposed.iteritems()).difference(existing.iteritems()))

            if delta.get('pwd'):
                delta['authentication'] = authentication

            if delta:
                delta['group'] = group

            command = config_snmp_user(delta, user, reset, new)
            commands.append(command)

    cmds = flatten_list(commands)
    results = {}
    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            changed = True
            execute_config_command(cmds, module)
            end_state = get_snmp_user(user, module)
            if 'configure' in cmds:
                cmds.pop(0)

    if store:
        existing['group'] = store

    results['proposed'] = proposed
    results['existing'] = existing
    results['updates'] = cmds
    results['changed'] = changed
    results['end_state'] = end_state

    module.exit_json(**results)


if __name__ == "__main__":
    main()
