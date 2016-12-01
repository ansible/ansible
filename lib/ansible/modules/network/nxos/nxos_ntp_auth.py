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

module: nxos_ntp_auth
version_added: "2.2"
short_description: Manages NTP authentication.
description:
    - Manages NTP authentication.
extends_documentation_fragment: nxos
author:
    - Jason Edelman (@jedelman8)
notes:
    - If C(state=absent), the module will attempt to remove the given key configuration.
      If a matching key configuration isn't found on the device, the module will fail.
    - If C(state=absent) and C(authentication=on), authentication will be turned off.
    - If C(state=absent) and C(authentication=off), authentication will be turned on.
options:
    key_id:
        description:
            - Authentication key identifier (numeric).
        required: true
    md5string:
        description:
            - MD5 String.
        required: true
        default: null
    auth_type:
        description:
            - Whether the given md5string is in cleartext or
              has been encrypted. If in cleartext, the device
              will encrypt it before storing it.
        required: false
        default: text
        choices: ['text', 'encrypt']
    trusted_key:
        description:
            - Whether the given key is required to be supplied by a time source
              for the device to synchronize to the time source.
        required: false
        default: false
        choices: ['true', 'false']
    authentication:
        description:
            - Turns NTP authentication on or off.
        required: false
        default: null
        choices: ['on', 'off']
    state:
        description:
            - Manage the state of the resource.
        required: false
        default: present
        choices: ['present','absent']
'''

EXAMPLES = '''
# Basic NTP authentication configuration
- nxos_ntp_auth:
    key_id: 32
    md5string: hello
    auth_type: text
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"auth_type": "text", "authentication": "off",
            "key_id": "32", "md5string": "helloWorld",
            "trusted_key": "true"}
existing:
    description:
        - k/v pairs of existing ntp authentication
    type: dict
    sample: {"authentication": "off", "trusted_key": "false"}
end_state:
    description: k/v pairs of ntp authentication after module execution
    returned: always
    type: dict
    sample: {"authentication": "off", "key_id": "32",
            "md5string": "kapqgWjwdg", "trusted_key": "true"}
state:
    description: state as sent in from the playbook
    returned: always
    type: string
    sample: "present"
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["ntp authentication-key 32 md5 helloWorld 0", "ntp trusted-key 32"]
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
    if 'xml' in response[0]:
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


def get_ntp_auth(module):
    command = 'show ntp authentication-status'

    body = execute_show_command(command, module)[0]
    ntp_auth_str = body['authentication']

    if 'enabled' in ntp_auth_str:
        ntp_auth = True
    else:
        ntp_auth = False

    return ntp_auth


def get_ntp_trusted_key(module):
    trusted_key_list = []
    command = 'show run | inc ntp.trusted-key'

    trusted_key_str = execute_show_command(
                command, module, command_type='cli_show_ascii')[0]
    if trusted_key_str:
        trusted_keys = trusted_key_str.splitlines()

    else:
        trusted_keys = []

    for line in trusted_keys:
        if line:
            trusted_key_list.append(str(line.split()[2]))

    return trusted_key_list


def get_ntp_auth_key(key_id, module):
    authentication_key = {}
    command = 'show run | inc ntp.authentication-key.{0}'.format(key_id)
    auth_regex = (".*ntp\sauthentication-key\s(?P<key_id>\d+)\s"
                  "md5\s(?P<md5string>\S+).*")

    body = execute_show_command(command, module, command_type='cli_show_ascii')

    try:
        match_authentication = re.match(auth_regex, body[0], re.DOTALL)
        group_authentication = match_authentication.groupdict()
        key_id = group_authentication["key_id"]
        md5string = group_authentication['md5string']
        authentication_key['key_id'] = key_id
        authentication_key['md5string'] = md5string
    except (AttributeError, TypeError):
        authentication_key = {}

    return authentication_key


def get_ntp_auth_info(key_id, module):
    auth_info = get_ntp_auth_key(key_id, module)
    trusted_key_list = get_ntp_trusted_key(module)
    auth_power = get_ntp_auth(module)

    if key_id in trusted_key_list:
        auth_info['trusted_key'] = 'true'
    else:
        auth_info['trusted_key'] = 'false'

    if auth_power:
        auth_info['authentication'] = 'on'
    else:
        auth_info['authentication'] = 'off'

    return auth_info


def auth_type_to_num(auth_type):
    if auth_type == 'encrypt' :
        return '7'
    else:
        return '0'


def set_ntp_auth_key(key_id, md5string, auth_type, trusted_key, authentication):
    ntp_auth_cmds = []
    auth_type_num = auth_type_to_num(auth_type)
    ntp_auth_cmds.append(
        'ntp authentication-key {0} md5 {1} {2}'.format(
            key_id, md5string, auth_type_num))

    if trusted_key == 'true':
        ntp_auth_cmds.append(
            'ntp trusted-key {0}'.format(key_id))
    elif trusted_key == 'false':
        ntp_auth_cmds.append(
            'no ntp trusted-key {0}'.format(key_id))

    if authentication == 'on':
        ntp_auth_cmds.append(
            'ntp authenticate')
    elif authentication == 'off':
        ntp_auth_cmds.append(
            'no ntp authenticate')

    return ntp_auth_cmds


def remove_ntp_auth_key(key_id, md5string, auth_type, trusted_key, authentication):
    auth_remove_cmds = []
    auth_type_num = auth_type_to_num(auth_type)
    auth_remove_cmds.append(
        'no ntp authentication-key {0} md5 {1} {2}'.format(
            key_id, md5string, auth_type_num))

    if authentication == 'on':
        auth_remove_cmds.append(
            'no ntp authenticate')
    elif authentication == 'off':
        auth_remove_cmds.append(
            'ntp authenticate')

    return auth_remove_cmds


def main():
    argument_spec = dict(
            key_id=dict(required=True, type='str'),
            md5string=dict(required=True, type='str'),
            auth_type=dict(choices=['text', 'encrypt'], default='text'),
            trusted_key=dict(choices=['true', 'false'], default='false'),
            authentication=dict(choices=['on', 'off']),
            state=dict(choices=['absent', 'present'], default='present'),
    )
    module = get_network_module(argument_spec=argument_spec,
                                supports_check_mode=True)

    key_id = module.params['key_id']
    md5string = module.params['md5string']
    auth_type = module.params['auth_type']
    trusted_key = module.params['trusted_key']
    authentication = module.params['authentication']
    state = module.params['state']

    args = dict(key_id=key_id, md5string=md5string,
                auth_type=auth_type, trusted_key=trusted_key,
                authentication=authentication)

    changed = False
    proposed = dict((k, v) for k, v in args.iteritems() if v is not None)

    existing = get_ntp_auth_info(key_id, module)
    end_state = existing

    delta = dict(set(proposed.iteritems()).difference(existing.iteritems()))

    commands = []
    if state == 'present':
        if delta:
            command = set_ntp_auth_key(
                key_id, md5string, auth_type, trusted_key, delta.get('authentication'))
            if command:
                commands.append(command)
    elif state == 'absent':
        if existing:
            auth_toggle = None
            if authentication == existing.get('authentication'):
                auth_toggle = authentication
            command = remove_ntp_auth_key(
                key_id, md5string, auth_type, trusted_key, auth_toggle)
            if command:
                commands.append(command)

    cmds = flatten_list(commands)
    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            try:
                execute_config_command(cmds, module)
            except ShellError:
                clie = get_exception()
                module.fail_json(msg=str(clie) + ": " + cmds)
            end_state = get_ntp_auth_info(key_id, module)
            delta = dict(set(end_state.iteritems()).difference(existing.iteritems()))
            if delta or (len(existing) != len(end_state)):
                changed = True
            if 'configure' in cmds:
                cmds.pop(0)

    results = {}
    results['proposed'] = proposed
    results['existing'] = existing
    results['updates'] = cmds
    results['changed'] = changed
    results['end_state'] = end_state

    module.exit_json(**results)

if __name__ == '__main__':
    main()
