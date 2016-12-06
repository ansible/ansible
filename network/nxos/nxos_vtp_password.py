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

module: nxos_vtp
version_added: "2.2"
short_description: Manages VTP password configuration.
description:
    - Manages VTP password configuration.
extends_documentation_fragment: nxos
author:
    - Gabriele Gerbino (@GGabriele)
notes:
    - VTP feature must be active on the device to use this module.
    - This module is used to manage only VTP passwords.
    - Use this in combination with M(nxos_vtp_domain) and M(nxos_vtp_version)
      to fully manage VTP operations.
    - You can set/remove password only if a VTP domain already exist.
    - If C(state=absent) and no C(vtp_password) is provided, it remove the current
      VTP password.
    - If C(state=absent) and C(vtp_password) is provided, the proposed C(vtp_password)
      has to match the existing one in order to remove it.
options:
    vtp_password:
        description:
            - VTP password
        required: false
        default: null
    state:
        description:
            - Manage the state of the resource
        required: false
        default: present
        choices: ['present','absent']
'''

EXAMPLES = '''
# ENSURE VTP PASSWORD IS SET
- nxos_vtp_password:
    password: ntc
    state: present
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"

# ENSURE VTP PASSWORD IS REMOVED
- nxos_vtp_password:
    password: ntc
    state: absent
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"vtp_password": "new_ntc"}
existing:
    description:
        - k/v pairs of existing vtp
    type: dict
    sample: {"domain": "ntc", "version": "1", "vtp_password": "ntc"}
end_state:
    description: k/v pairs of vtp after module execution
    returned: always
    type: dict
    sample: {"domain": "ntc", "version": "1", "vtp_password": "new_ntc"}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["vtp password new_ntc"]
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


def get_vtp_config(module):
    command = 'show vtp status'

    body = execute_show_command(
            command, module, command_type='cli_show_ascii')[0]
    vtp_parsed = {}

    if body:
        version_regex = '.*VTP version running\s+:\s+(?P<version>\d).*'
        domain_regex = '.*VTP Domain Name\s+:\s+(?P<domain>\S+).*'

        try:
            match_version = re.match(version_regex, body, re.DOTALL)
            version = match_version.groupdict()['version']
        except AttributeError:
            version = ''

        try:
            match_domain = re.match(domain_regex, body, re.DOTALL)
            domain = match_domain.groupdict()['domain']
        except AttributeError:
            domain = ''

        if domain and version:
            vtp_parsed['domain'] = domain
            vtp_parsed['version'] = version
            vtp_parsed['vtp_password'] = get_vtp_password(module)

    return vtp_parsed


def get_vtp_password(module):
    command = 'show vtp password'
    body = execute_show_command(command, module)[0]
    password = body['passwd']
    if password:
        return str(password)
    else:
        return ""


def main():
    argument_spec = dict(
            vtp_password=dict(type='str', no_log=True),
            state=dict(choices=['absent', 'present'],
                       default='present'),
    )
    module = get_network_module(argument_spec=argument_spec,
                                supports_check_mode=True)

    vtp_password = module.params['vtp_password'] or None
    state = module.params['state']

    existing = get_vtp_config(module)
    end_state = existing

    args = dict(vtp_password=vtp_password)

    changed = False
    proposed = dict((k, v) for k, v in args.iteritems() if v is not None)
    delta = dict(set(proposed.iteritems()).difference(existing.iteritems()))

    commands = []
    if state == 'absent':
        if vtp_password is not None:
            if existing['vtp_password'] == proposed['vtp_password']:
                commands.append(['no vtp password'])
            else:
                module.fail_json(msg="Proposed vtp password doesn't match "
                                     "current vtp password. It cannot be "
                                     "removed when state=absent. If you are "
                                     "trying to change the vtp password, use "
                                     "state=present.")
        else:
            if not existing.get('domain'):
                    module.fail_json(msg='Cannot remove a vtp password '
                                         'before vtp domain is set.')

            elif existing['vtp_password'] != ('\\'):
                commands.append(['no vtp password'])

    elif state == 'present':
        if delta:
            if not existing.get('domain'):
                module.fail_json(msg='Cannot set vtp password '
                                     'before vtp domain is set.')

            else:
                commands.append(['vtp password {0}'.format(vtp_password)])

    cmds = flatten_list(commands)
    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            changed = True
            execute_config_command(cmds, module)
            end_state = get_vtp_config(module)
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
