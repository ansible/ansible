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
module: nxos_acl_interface
version_added: "2.2"
short_description: Manages applying ACLs to interfaces.
description:
    - Manages applying ACLs to interfaces.
extends_documentation_fragment: nxos
author:
    - Jason Edelman (@jedelman8)
    - Gabriele Gerbino (@GGabriele)
options:
    name:
        description:
            - Case sensitive name of the access list (ACL).
        required: true
    interface:
        description:
            - Full name of interface, e.g. I(Ethernet1/1).
        required: true
    direction:
        description:
            - Direction ACL to be applied in on the interface.
        required: true
        choices: ['ingress', 'egress']
    state:
        description:
            - Specify desired state of the resource.
        required: false
        default: present
        choices: ['present','absent']
'''

EXAMPLES = '''
- name: apply egress acl to ethernet1/41
  nxos_acl_interface:
    name: ANSIBLE
    interface: ethernet1/41
    direction: egress
    state: present
    username: "{{ un }}"
    password: "{{ pwd }}"
    host: "{{ inventory_hostname }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"direction": "egress", "interface": "ethernet1/41",
            "name": "ANSIBLE"}
existing:
    description: k/v pairs of existing ACL applied to the interface
    type: dict
    sample: {}
end_state:
    description: k/v pairs of interface ACL after module execution
    returned: always
    type: dict
    sample: {"direction": "egress", "interface": "ethernet1/41",
            "name": "ANSIBLE"}
acl_applied_to:
    description: list of interfaces the ACL is applied to
    returned: always
    type: list
    sample: [{"acl_type": "Router ACL", "direction": "egress",
            "interface": "Ethernet1/41", "name": "ANSIBLE"}]
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["interface ethernet1/41", "ip access-group ANSIBLE out"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''

import collections
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
    resource doesn't exist yet. Instead, we assume if '^' is found in response,
    it is an invalid command.
    """
    if 'xml' in response[0]:
        body = []
    elif '^' in response[0] or 'summary' in command:
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
                module.cli.add_commands(cmds, output=command_type)
                response = module.cli.run_commands()
        except ShellError:
            clie = get_exception()
            module.fail_json(msg='Error sending {0}'.format(cmds),
                             error=str(clie))
    return response


def execute_show_command(command, module, command_type='cli_show'):
    if module.params['transport'] == 'cli':
        if 'summary' not in command:
            command += ' | json'
        cmds = [command]
        response = execute_show(cmds, module)
        body = get_cli_body_ssh(command, response, module)
    elif module.params['transport'] == 'nxapi':
        cmds = [command]
        body = execute_show(cmds, module, command_type=command_type)

    return body


def get_acl_interface(module, acl):
    command = 'show ip access-list summary'
    name_regex = '.*IPV4\s+ACL\s+(?P<name>\S+).*'
    interface_regex = ('.*\s+(?P<interface>\w+(\d+)?\/?(\d+)?)\s-\s'
                      '(?P<direction>\w+)\s+\W(?P<acl_type>\w+\s\w+)\W.*')
    acl_list = []

    body = execute_show_command(command, module, command_type='cli_show_ascii')
    body_split = body[0].split('Active on interfaces:')

    for each_acl in body_split:
        intf_list = []
        temp = {}
        try:
            match_name = re.match(name_regex, each_acl, re.DOTALL)
            name_dict = match_name.groupdict()
            name = name_dict['name']
        except AttributeError:
            name = ''

        temp['interfaces'] = []
        for line in each_acl.split('\n'):
            intf_temp = {}
            try:
                match_interface = re.match(interface_regex, line, re.DOTALL)
                interface_dict = match_interface.groupdict()
                interface = interface_dict['interface']
                direction = interface_dict['direction']
                acl_type = interface_dict['acl_type']
            except AttributeError:
                interface = ''
                direction = ''
                acl_type = ''

            if interface:
                intf_temp['interface'] = interface
            if acl_type:
                intf_temp['acl_type'] = acl_type
            if direction:
                intf_temp['direction'] = direction
            if intf_temp:
                temp['interfaces'].append(intf_temp)
        if name:
            temp['name'] = name

        if temp:
            acl_list.append(temp)

    existing_no_null = []
    for each in acl_list:
        if each.get('name') == acl:
            interfaces = each.get('interfaces')
            for interface in interfaces:
                new_temp = {}
                new_temp['name'] = acl
                new_temp.update(interface)
                existing_no_null.append(new_temp)
    return existing_no_null


def other_existing_acl(get_existing, interface, direction):
    # now we'll just get the interface in question
    # needs to be a list since same acl could be applied in both dirs
    acls_interface = []
    if get_existing:
        for each in get_existing:
            if each.get('interface').lower() == interface:
                acls_interface.append(each)
    else:
        acls_interface = []

    if acls_interface:
        this = {}
        for each in acls_interface:
            if each.get('direction') == direction:
                this = each
    else:
        acls_interface = []
        this = {}

    return acls_interface, this


def apply_acl(proposed):
    commands = []

    commands.append('interface ' + proposed.get('interface'))
    direction = proposed.get('direction')
    if direction == 'egress':
        cmd = 'ip access-group {0} {1}'.format(proposed.get('name'), 'out')
    elif direction == 'ingress':
        cmd = 'ip access-group {0} {1}'.format(proposed.get('name'), 'in')
    commands.append(cmd)

    return commands


def remove_acl(proposed):
    commands = []

    commands.append('interface ' + proposed.get('interface'))
    direction = proposed.get('direction')
    if direction == 'egress':
        cmd = 'no ip access-group {0} {1}'.format(proposed.get('name'), 'out')
    elif direction == 'ingress':
        cmd = 'no ip access-group {0} {1}'.format(proposed.get('name'), 'in')
    commands.append(cmd)

    return commands


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


def main():
    argument_spec = dict(
            name=dict(required=False, type='str'),
            interface=dict(required=True),
            direction=dict(required=True, choices=['egress', 'ingress']),
            state=dict(choices=['absent', 'present'],
                       default='present'),
            include_defaults=dict(default=True),
            config=dict(),
            save=dict(type='bool', default=False)
    )
    module = get_network_module(argument_spec=argument_spec,
                        supports_check_mode=True)

    state = module.params['state']
    name = module.params['name']
    interface = module.params['interface'].lower()
    direction = module.params['direction'].lower()

    proposed = dict(name=name, interface=interface, direction=direction)

    # includes all interfaces the ACL is applied to (list)
    get_existing = get_acl_interface(module, name)

    # interface_acls = includes entries of this ACL on the interface (list)
    # this_dir_acl_intf = dict - not null if it already exists
    interfaces_acls, existing = other_existing_acl(
        get_existing, interface, direction)

    end_state = existing
    end_state_acls = get_existing
    changed = False

    cmds = []
    commands = []
    if state == 'present':
        if not existing:
            command = apply_acl(proposed)
            if command:
                commands.append(command)

    elif state == 'absent':
        if existing:
            command = remove_acl(proposed)
            if command:
                commands.append(command)

    if commands:
        cmds = flatten_list(commands)
        if cmds:
            if module.check_mode:
                module.exit_json(changed=True, commands=cmds)
            else:
                execute_config_command(cmds, module)
                changed = True
                end_state_acls = get_acl_interface(module, name)
                interfaces_acls, this_dir_acl_intf = other_existing_acl(
                    end_state_acls, interface, direction)
                end_state = this_dir_acl_intf
                if 'configure' in cmds:
                    cmds.pop(0)
    else:
        cmds = []

    results = {}
    results['proposed'] = proposed
    results['existing'] = existing
    results['updates'] = cmds
    results['changed'] = changed
    results['end_state'] = end_state
    results['acl_applied_to'] = end_state_acls

    module.exit_json(**results)


if __name__ == '__main__':
    main()
