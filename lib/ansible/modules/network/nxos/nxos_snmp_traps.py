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
module: nxos_snmp_trap
version_added: "2.2"
short_description: Manages SNMP traps.
description:
    - Manages SNMP traps configurations.
extends_documentation_fragment: nxos
author:
    - Jason Edelman (@jedelman8)
notes:
    - This module works at the group level for traps.  If you need to only
      enable/disable 1 specific trap within a group, use the M(nxos_command)
      module.
    - Be aware that you can set a trap only for an enabled feature.
options:
    group:
        description:
            - Case sensitive group.
        required: true
        choices: ['aaa', 'bridge', 'callhome', 'cfs', 'config', 'entity',
          'feature-control', 'hsrp', 'license', 'link', 'lldp', 'ospf', 'pim',
          'rf', 'rmon', 'snmp', 'storm-control', 'stpx', 'sysmgr', 'system',
          'upgrade', 'vtp', 'all']
    state:
        description:
            - Manage the state of the resource.
        required: false
        default: enabled
        choices: ['enabled','disabled']
'''

EXAMPLES = '''
# ensure lldp trap configured
- nxos_snmp_traps:
    group=lldp
    state=enabled
    host={{ inventory_hostname }}
    username={{ un }}
    password={{ pwd }}

# ensure lldp trap is not configured
- nxos_snmp_traps:
    group=lldp
    state=disabled
    host={{ inventory_hostname }}
    username={{ un }}
    password={{ pwd }}
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"group": "lldp"}
existing:
    description: k/v pairs of existing trap status
    type: dict
    sample: {"lldp": [{"enabled": "No",
            "trap": "lldpRemTablesChange"}]}
end_state:
    description: k/v pairs of trap info after module execution
    returned: always
    type: dict
    sample: {"lldp": [{"enabled": "Yes",
            "trap": "lldpRemTablesChange"}]}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: "snmp-server enable traps lldp ;"
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


def flatten_list(command_lists):
    flat_command_list = []
    for command in command_lists:
        if isinstance(command, list):
            flat_command_list.extend(command)
        else:
            flat_command_list.append(command)
    return flat_command_list



def get_snmp_traps(group, module):
    command = 'show snmp trap'
    body = execute_show_command(command, module)

    trap_key = {
        'description': 'trap',
        'isEnabled': 'enabled'
    }

    resource = {}

    try:
        resource_table = body[0]['TABLE_snmp_trap']['ROW_snmp_trap']

        for each_feature in ['aaa', 'bridge', 'callhome', 'cfs', 'config',
                             'entity', 'feature-control', 'hsrp', 'license',
                             'link', 'lldp', 'ospf', 'pim', 'rf', 'rmon',
                             'snmp', 'storm-control', 'stpx', 'sysmgr',
                             'system', 'upgrade', 'vtp']:

            resource[each_feature] = []

        for each_resource in resource_table:
            key = str(each_resource['trap_type'])
            mapped_trap = apply_key_map(trap_key, each_resource)

            if key != 'Generic':
                resource[key].append(mapped_trap)

    except (KeyError, AttributeError):
        return resource

    find = resource.get(group, None)

    if group == 'all'.lower():
        return resource
    elif find:
        trap_resource = {group: resource[group]}
        return trap_resource
    else:
        # if 'find' is None, it means that 'group' is a
        # currently disabled feature.
        return {}


def get_trap_commands(group, state, existing, module):
    commands = []
    enabled = False
    disabled = False

    if group == 'all':
        if state == 'disabled':
            for feature in existing:
                trap_commands = ['no snmp-server enable traps {0}'.format(feature) for
                                    trap in existing[feature] if trap['enabled'] == 'Yes']
                trap_commands = list(set(trap_commands))
                commands.append(trap_commands)

        elif state == 'enabled':
            for feature in existing:
                trap_commands = ['snmp-server enable traps {0}'.format(feature) for
                                    trap in existing[feature] if trap['enabled'] == 'No']
                trap_commands = list(set(trap_commands))
                commands.append(trap_commands)

    else:
        if group in existing:
            for each_trap in existing[group]:
                check = each_trap['enabled']
                if check.lower() == 'yes':
                    enabled = True
                if check.lower() == 'no':
                    disabled = True

            if state == 'disabled' and enabled:
                commands.append(['no snmp-server enable traps {0}'.format(group)])
            elif state == 'enabled' and disabled:
                commands.append(['snmp-server enable traps {0}'.format(group)])
        else:
            module.fail_json(msg='{0} is not a currently '
                                 'enabled feature.'.format(group))

    return commands


def main():
    argument_spec = dict(
            state=dict(choices=['enabled', 'disabled'], required=True),
            group=dict(choices=['aaa', 'bridge', 'callhome', 'cfs', 'config',
                                'entity', 'feature-control', 'hsrp',
                                'license', 'link', 'lldp', 'ospf', 'pim', 'rf',
                                'rmon', 'snmp', 'storm-control', 'stpx',
                                'sysmgr', 'system', 'upgrade', 'vtp', 'all'],
                       required=True),
    )
    module = get_network_module(argument_spec=argument_spec,
                                supports_check_mode=True)
    
    group = module.params['group'].lower()
    state = module.params['state']

    existing = get_snmp_traps(group, module)
    proposed = {'group': group}

    changed = False
    end_state = existing
    commands = get_trap_commands(group, state, existing, module)

    cmds = flatten_list(commands)
    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            changed = True
            execute_config_command(cmds, module)
            end_state = get_snmp_traps(group, module)

    results = {}
    results['proposed'] = proposed
    results['existing'] = existing
    results['end_state'] = end_state
    results['updates'] = cmds
    results['changed'] = changed

    module.exit_json(**results)


if __name__ == '__main__':
    main()