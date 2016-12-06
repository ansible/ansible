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

module: nxos_ntp_options
short_description: Manages NTP options.
description:
    - Manages NTP options, e.g. authoritative server and logging.
extends_documentation_fragment: nxos
author:
    - Jason Edelman (@jedelman8)
notes:
    - At least one of C(master) or C(logging) params must be supplied.
    - When C(state=absent), boolean parameters are flipped,
      e.g. C(master=true) will disable the authoritative server.
    - When C(state=absent) and C(master=true), the stratum will be removed as well.
    - When C(state=absent) and C(master=false), the stratum will be configured
      to its default value, 8.
options:
    master:
        description:
            - Sets whether the device is an authoritative NTP server.
        required: false
        default: null
        choices: ['true','false']
    stratum:
        description:
            - If C(master=true), an optional stratum can be supplied (1-15).
              The device default is 8.
        required: false
        default: null
    logging:
        description:
            - Sets whether NTP logging is enabled on the device.
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
# Basic NTP options configuration
- nxos_ntp_options:
    master: true
    stratum: 12
    logging: false
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"logging": false, "master": true, "stratum": "11"}
existing:
    description:
        - k/v pairs of existing ntp options
    type: dict
    sample: {"logging": true, "master": true, "stratum": "8"}
end_state:
    description: k/v pairs of ntp options after module execution
    returned: always
    type: dict
    sample: {"logging": false, "master": true, "stratum": "11"}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["no ntp logging", "ntp master 11"]
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


def get_ntp_master(module):
    command = 'show run | inc ntp.master'
    master_string = execute_show_command(command, module, command_type='cli_show_ascii')

    if master_string:
        if master_string[0]:
            master = True
        else:
            master = False
    else:
        master = False

    if master is True:
        stratum = str(master_string[0].split()[2])
    else:
        stratum = None

    return master, stratum


def get_ntp_log(module):
    command = 'show ntp logging'
    body = execute_show_command(command, module)[0]

    logging_string = body['loggingstatus']
    if 'enabled' in logging_string:
        ntp_log = True
    else:
        ntp_log = False

    return ntp_log


def get_ntp_options(module):
    existing = {}
    existing['logging'] = get_ntp_log(module)
    existing['master'], existing['stratum'] = get_ntp_master(module)

    return existing


def config_ntp_options(delta, flip=False):
    master = delta.get('master')
    stratum = delta.get('stratum')
    log = delta.get('logging')
    ntp_cmds = []

    if flip:
        log = not log
        master = not master

    if log is not None:
        if log is True:
            ntp_cmds.append('ntp logging')
        elif log is False:
            ntp_cmds.append('no ntp logging')
    if master is not None:
        if master is True:
            if not stratum:
                stratum = ''
            ntp_cmds.append('ntp master {0}'.format(stratum))
        elif master is False:
            ntp_cmds.append('no ntp master')

    return ntp_cmds


def main():
    argument_spec = dict(
            master=dict(required=False, type='bool'),
            stratum=dict(type='str'),
            logging=dict(required=False, type='bool'),
            state=dict(choices=['absent', 'present'], default='present'),
    )
    module = get_network_module(argument_spec=argument_spec,
                                required_one_of=[['master', 'logging']],
                                supports_check_mode=True)

    master = module.params['master']
    stratum = module.params['stratum']
    logging = module.params['logging']
    state = module.params['state']

    if stratum:
        if master is None:
            module.fail_json(msg='The master param must be supplied when '
                                 'stratum is supplied')
        try:
            stratum_int = int(stratum)
            if stratum_int < 1 or stratum_int > 15:
                raise ValueError
        except ValueError:
            module.fail_json(msg='Stratum must be an integer between 1 and 15')

    existing = get_ntp_options(module)
    end_state = existing

    args = dict(master=master, stratum=stratum, logging=logging)

    changed = False
    proposed = dict((k, v) for k, v in args.iteritems() if v is not None)

    if master is False:
        proposed['stratum'] = None
        stratum = None

    delta = dict(set(proposed.iteritems()).difference(existing.iteritems()))
    delta_stratum = delta.get('stratum')

    if delta_stratum:
        delta['master'] = True

    commands = []
    if state == 'present':
        if delta:
            command = config_ntp_options(delta)
            if command:
                commands.append(command)
    elif state == 'absent':
        if existing:
            isection = dict(set(proposed.iteritems()).intersection(
                existing.iteritems()))
            command = config_ntp_options(isection, flip=True)
            if command:
                commands.append(command)

    cmds = flatten_list(commands)
    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            changed = True
            execute_config_command(cmds, module)
            end_state = get_ntp_options(module)
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
