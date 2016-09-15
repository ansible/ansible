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
module: nxos_igmp_snooping
version_added: "2.2"
short_description: Manages IGMP snooping global configuration.
description:
    - Manages IGMP snooping global configuration.
author:
    - Jason Edelman (@jedelman8)
    - Gabriele Gerbino (@GGabriele)
extends_documentation_fragment: nxos
notes:
    - When C(state=default), params will be reset to a default state.
    - C(group_timeout) also accepts I(never) as an input.
options:
    snooping:
        description:
            - Enables/disables IGMP snooping on the switch.
        required: false
        default: null
        choices: ['true', 'false']
    group_timeout:
        description:
            - Group membership timeout value for all VLANs on the device.
              Accepted values are integer in range 1-10080, I(never) and
              I(default).
        required: false
        default: null
    link_local_grp_supp:
        description:
            - Global link-local groups suppression.
        required: false
        default: null
        choices: ['true', 'false']
    report_supp:
        description:
            - Global IGMPv1/IGMPv2 Report Suppression.
        required: false
        default: null
    v3_report_supp:
        description:
            - Global IGMPv3 Report Suppression and Proxy Reporting.
        required: false
        default: null
        choices: ['true', 'false']
    state:
        description:
            - Manage the state of the resource.
        required: false
        default: present
        choices: ['present','default']
'''

EXAMPLES = '''
# ensure igmp snooping params supported in this module are in there default state
- nxos_igmp_snooping:
    state=default
    host={{ inventory_hostname }}
    username={{ un }}
    password={{ pwd }}

# ensure following igmp snooping params are in the desired state
- nxos_igmp_snooping:
   group_timeout: never
   snooping: true
   link_local_grp_supp: false
   optimize_mcast_flood: false
   report_supp: true
   v3_report_supp: true
   host: "{{ inventory_hostname }}"
   username={{ un }}
   password={{ pwd }}
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"group_timeout": "50", "link_local_grp_supp": true,
            "report_supp": false, "snooping": false, "v3_report_supp": false}
existing:
    description:
        - k/v pairs of existing configuration
    type: dict
    sample: {"group_timeout": "never", "link_local_grp_supp": false,
            "report_supp": true, "snooping": true, "v3_report_supp": true}
end_state:
    description: k/v pairs of configuration after module execution
    returned: always
    type: dict
    sample: {"group_timeout": "50", "link_local_grp_supp": true,
            "report_supp": false, "snooping": false, "v3_report_supp": false}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["ip igmp snooping link-local-groups-suppression", 
             "ip igmp snooping group-timeout 50", 
             "no ip igmp snooping report-suppression", 
             "no ip igmp snooping v3-report-suppression", 
             "no ip igmp snooping"]
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
            if isinstance(response[0], str):
                response = response[0].replace(command + '\n\n', '').strip()
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


def get_group_timeout(config):
    command = 'ip igmp snooping group-timeout'
    REGEX = re.compile(r'(?:{0}\s)(?P<value>.*)$'.format(command), re.M)
    value = ''
    if command in config:
        value = REGEX.search(config).group('value')
    return value


def get_snooping(config):
    REGEX = re.compile(r'{0}$'.format('no ip igmp snooping'), re.M)
    value = False
    try:
        if REGEX.search(config):
            value = False
    except TypeError:
        value = True
    return value


def get_igmp_snooping(module):
    command = 'show run all | include igmp.snooping'
    existing = {}
    body = execute_show_command(
                        command, module, command_type='cli_show_ascii')[0]

    if body:
        split_body = body.splitlines()

        if 'no ip igmp snooping' in split_body:
            existing['snooping'] = False
        else:
            existing['snooping'] = True

        if 'no ip igmp snooping report-suppression' in split_body:
            existing['report_supp'] = False
        elif 'ip igmp snooping report-suppression' in split_body:
            existing['report_supp'] = True

        if 'no ip igmp snooping link-local-groups-suppression' in split_body:
            existing['link_local_grp_supp'] = False
        elif 'ip igmp snooping link-local-groups-suppression' in split_body:
            existing['link_local_grp_supp'] = True

        if 'ip igmp snooping v3-report-suppression' in split_body:
            existing['v3_report_supp'] = True
        else:
            existing['v3_report_supp'] = False

        existing['group_timeout'] = get_group_timeout(body)

    return existing


def config_igmp_snooping(delta, existing, default=False):
    CMDS = {
        'snooping': 'ip igmp snooping',
        'group_timeout': 'ip igmp snooping group-timeout {}',
        'link_local_grp_supp': 'ip igmp snooping link-local-groups-suppression',
        'v3_report_supp': 'ip igmp snooping v3-report-suppression',
        'report_supp': 'ip igmp snooping report-suppression'
    }

    commands = []
    command = None
    for key, value in delta.iteritems():
        if value:
            if default and key == 'group_timeout':
                if existing.get(key):
                    command = 'no ' + CMDS.get(key).format(existing.get(key))
            else:
                command = CMDS.get(key).format(value)
        else:
            command = 'no ' + CMDS.get(key).format(value)

        if command:
            commands.append(command)
        command = None

    return commands


def get_igmp_snooping_defaults():
    group_timeout = 'dummy'
    report_supp = True
    link_local_grp_supp = True
    v3_report_supp = False
    snooping = True

    args = dict(snooping=snooping, link_local_grp_supp=link_local_grp_supp,
                report_supp=report_supp, v3_report_supp=v3_report_supp,
                group_timeout=group_timeout)

    default = dict((param, value) for (param, value) in args.iteritems()
                   if value is not None)

    return default


def main():
    argument_spec = dict(
            snooping=dict(required=False, type='bool'),
            group_timeout=dict(required=False, type='str'),
            link_local_grp_supp=dict(required=False, type='bool'),
            report_supp=dict(required=False, type='bool'),
            v3_report_supp=dict(required=False, type='bool'),
            state=dict(choices=['present', 'default'], default='present'),
    )
    module = get_network_module(argument_spec=argument_spec,
                                supports_check_mode=True)

    snooping = module.params['snooping']
    link_local_grp_supp = module.params['link_local_grp_supp']
    report_supp = module.params['report_supp']
    v3_report_supp = module.params['v3_report_supp']
    group_timeout = module.params['group_timeout']
    state = module.params['state']

    args = dict(snooping=snooping, link_local_grp_supp=link_local_grp_supp,
                report_supp=report_supp, v3_report_supp=v3_report_supp,
                group_timeout=group_timeout)

    proposed = dict((param, value) for (param, value) in args.iteritems()
                    if value is not None)

    existing = get_igmp_snooping(module)
    end_state = existing
    changed = False

    commands = []
    if state == 'present':
        delta = dict(
                    set(proposed.iteritems()).difference(existing.iteritems())
                    )
        if delta:
            command = config_igmp_snooping(delta, existing)
            if command:
                commands.append(command)
    elif state == 'default':
        proposed = get_igmp_snooping_defaults()
        delta = dict(
                     set(proposed.iteritems()).difference(existing.iteritems())
                    )
        if delta:
            command = config_igmp_snooping(delta, existing, default=True)
            if command:
                commands.append(command)

    cmds = flatten_list(commands)
    results = {}
    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            changed = True
            execute_config_command(cmds, module)
            end_state = get_igmp_snooping(module)

    results['proposed'] = proposed
    results['existing'] = existing
    results['updates'] = cmds
    results['changed'] = changed
    results['end_state'] = end_state

    module.exit_json(**results)

if __name__ == '__main__':
    main()
