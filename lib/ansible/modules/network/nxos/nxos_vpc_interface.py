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
module: nxos_vpc_interface
version_added: "2.2"
short_description: Manages interface VPC configuration
description:
    - Manages interface VPC configuration
extends_documentation_fragment: nxos
author:
    - Jason Edelman (@jedelman8)
    - Gabriele Gerbino (@GGabriele)
notes:
    - Either vpc or peer_link param is required, but not both.
    - C(state=absent) removes whatever VPC config is on a port-channel
      if one exists.
    - Re-assigning a vpc or peerlink from one portchannel to another is not
      supported.  The module will force the user to unconfigure an existing
      vpc/pl before configuring the same value on a new portchannel
options:
    portchannel:
        description:
            - Group number of the portchannel that will be configured.
        required: true
    vpc:
        description:
            - VPC group/id that will be configured on associated portchannel.
        required: false
        default: null
    peer_link:
        description:
            - Set to true/false for peer link config on associated portchannel.
        required: false
        default: null
    state:
        description:
            - Manages desired state of the resource.
        required: true
        choices: ['present','absent']
'''

EXAMPLES = '''
- nxos_vpc_portchannel:
    portchannel: 10
    vpc: 100
    username: "{{ un }}"
    password: "{{ pwd }}"
    host: "{{ inventory_hostname }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"portchannel": "100", "vpc": "10"}
existing:
    description: k/v pairs of existing configuration
    type: dict
    sample: {}
end_state:
    description: k/v pairs of configuration after module execution
    returned: always
    type: dict
    sample:  {"peer-link": false, "portchannel": "100", "vpc": "10"}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["interface port-channel100", "vpc 10"]
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

def execute_config_command(commands, module):
    try:
        response = module.configure(commands)
    except ShellError:
        clie = get_exception()
        module.fail_json(msg='Error sending CLI commands',
                         error=str(clie), commands=commands)
    except AttributeError:
        try:
            commands.insert(0, 'configure')
            module.cli.add_commands(commands, output='config')
            response = module.cli.run_commands()
        except ShellError:
            clie = get_exception()
            module.fail_json(msg='Error sending CLI commands',
                             error=str(clie), commands=commands)
    return response


def get_cli_body_ssh(command, response, module):
    """Get response for when transport=cli.  This is kind of a hack and mainly
    needed because these modules were originally written for NX-API.  And
    not every command supports "| json" when using cli/ssh.
    """
    if '^' == response[0]:
        body = []
    elif 'running' in command or 'xml' in response[0]:
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


def get_portchannel_list(module):
    command = 'show port-channel summary'
    portchannels = []
    pc_list = []

    body = execute_show_command(command, module)

    try:
        pc_list = body[0]['TABLE_channel']['ROW_channel']
    except (KeyError, AttributeError):
        return portchannels

    if pc_list:
        if isinstance(pc_list, dict):
            pc_list = [pc_list]

        for pc in pc_list:
            portchannels.append(pc['group'])

    return portchannels


def get_existing_portchannel_to_vpc_mappings(module):
    command = 'show vpc brief'
    pc_vpc_mapping = {}

    body = execute_show_command(command, module)

    try:
        vpc_table = body[0]['TABLE_vpc']['ROW_vpc']
    except (KeyError, AttributeError, TypeError):
        vpc_table = None

    if vpc_table:
        if isinstance(vpc_table, dict):
            vpc_table = [vpc_table]

        for vpc in vpc_table:
            pc_vpc_mapping[str(vpc['vpc-id'])] = str(vpc['vpc-ifindex'])

    return pc_vpc_mapping


def peer_link_exists(module):
    found = False
    run = get_vpc_running_config(module)

    vpc_list = run.split('\n')
    for each in vpc_list:
        if 'peer-link' in each:
            found = True
    return found


def get_vpc_running_config(module):
    command = 'show running section vpc'
    body = execute_show_command(command, module,
                                command_type='cli_show_ascii')[0]

    return body


def get_active_vpc_peer_link(module):
    command = 'show vpc brief'
    peer_link = None
    body = execute_show_command(command, module)
    try:
        peer_link = body[0]['TABLE_peerlink']['ROW_peerlink']['peerlink-ifindex']
    except (KeyError, AttributeError):
        return peer_link

    return peer_link


def get_portchannel_vpc_config(module, portchannel):
    command = 'show vpc brief'
    peer_link_pc = None
    peer_link = False
    vpc = ""
    pc = ""
    config = {}

    body = execute_show_command(command, module)

    try:
        table = body[0]['TABLE_peerlink']['ROW_peerlink']
    except (KeyError, AttributeError, TypeError):
        table = {}

    if table:
        peer_link_pc = table.get('peerlink-ifindex', None)

    if peer_link_pc:
        plpc = str(peer_link_pc[2:])
        if portchannel == plpc:
            config['portchannel'] = portchannel
            config['peer-link'] = True
            config['vpc'] = vpc

    mapping = get_existing_portchannel_to_vpc_mappings(module)

    for existing_vpc, port_channel in mapping.iteritems():
        port_ch = str(port_channel[2:])
        if port_ch == portchannel:
            pc = port_ch
            vpc = str(existing_vpc)

            config['portchannel'] = pc
            config['peer-link'] = peer_link
            config['vpc'] = vpc

    return config


def get_commands_to_config_vpc_interface(portchannel, delta, config_value, existing):
    commands = []

    if delta.get('peer-link') is False and existing.get('peer-link') is True:
        command = 'no vpc peer-link'
        commands.append('no vpc peer-link')
        commands.insert(0, 'interface port-channel{0}'.format(portchannel))

    elif delta.get('peer-link') or not existing.get('vpc'):
        command = 'vpc {0}'.format(config_value)
        commands.append(command)
        commands.insert(0, 'interface port-channel{0}'.format(portchannel))

    return commands


def main():
    argument_spec = dict(
            portchannel=dict(required=True, type='str'),
            vpc=dict(required=False, type='str'),
            peer_link=dict(required=False, type='bool'),
            state=dict(choices=['absent', 'present'], default='present'),
            include_defaults=dict(default=False),
            config=dict(),
            save=dict(type='bool', default=False)
    )
    module = get_network_module(argument_spec=argument_spec,
                                mutually_exclusive=[['vpc', 'peer_link']],
                                supports_check_mode=True)

    portchannel = module.params['portchannel']
    vpc = module.params['vpc']
    peer_link = module.params['peer_link']
    state = module.params['state']

    changed = False
    args = {'portchannel': portchannel, 'vpc': vpc, 'peer-link': peer_link}
    active_peer_link = None

    if portchannel not in get_portchannel_list(module):
        module.fail_json(msg="The portchannel you are trying to make a"
                             " VPC or PL is not created yet. "
                             "Create it first!")
    if vpc:
        mapping = get_existing_portchannel_to_vpc_mappings(module)

        if vpc in mapping and portchannel != mapping[vpc].strip('Po'):
            module.fail_json(msg="This vpc is already configured on "
                                 "another portchannel.  Remove it first "
                                 "before trying to assign it here. ",
                             existing_portchannel=mapping[vpc])

        for vpcid, existing_pc in mapping.iteritems():
            if portchannel == existing_pc.strip('Po') and vpcid != vpc:
                module.fail_json(msg="This portchannel already has another"
                                     " VPC configured.  Remove it first "
                                     "before assigning this one",
                                 existing_vpc=vpcid)

        if peer_link_exists(module):
            active_peer_link = get_active_vpc_peer_link(module)
            if active_peer_link[-2:] == portchannel:
                module.fail_json(msg="That port channel is the current "
                                     "PEER LINK.  Remove it if you want it"
                                     " to be a VPC")
        config_value = vpc

    elif peer_link is not None:
        if peer_link_exists(module):
            active_peer_link = get_active_vpc_peer_link(module)[2::]
            if active_peer_link != portchannel:
                if peer_link:
                    module.fail_json(msg="A peer link already exists on"
                                         " the device.  Remove it first",
                                     current_peer_link='Po{0}'.format(
                                     active_peer_link))
        config_value = 'peer-link'


    proposed = dict((k, v) for k, v in args.iteritems() if v is not None)
    existing = get_portchannel_vpc_config(module, portchannel)
    end_state = existing
    commands = []

    if state == 'present':
        delta = dict(set(proposed.iteritems()).difference(existing.iteritems()))
        if delta:
            command = get_commands_to_config_vpc_interface(
                portchannel,
                delta,
                config_value,
                existing
                )
            commands.append(command)

    elif state == 'absent':
        if existing.get('vpc'):
            command = ['no vpc']
            commands.append(command)
        elif existing.get('peer-link'):
            command = ['no vpc peer-link']
            commands.append(command)
        if commands:
            commands.insert(0, ['interface port-channel{0}'.format(portchannel)])

    cmds = flatten_list(commands)
    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            changed = True
            output = execute_config_command(cmds, module)
            if module.params['transport'] == 'cli':
                output = ' '.join(output)
                if 'error' in output.lower():
                    module.fail_json(msg=output.replace('\n', ''))
            end_state = get_portchannel_vpc_config(module, portchannel)
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
