#!/usr/bin/env python

# Copyright 2015 Jason Edelman <jedelman8@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: nxos_snmp_host
version_added: "2.2"
short_description: Manages SNMP host configuration.
description:
    - Manages SNMP host configuration parameters.
extends_documentation_fragment: nxos
author: Jason Edelman (@jedelman8)
notes:
    - C(state=absent) removes the host configuration if it is configured.
options:
    snmp_host:
        description:
            - IP address of hostname of target host.
        required: true
    version:
        description:
            - SNMP version.
        required: false
        default: v2c
        choices: ['v2c', 'v3']
    community:
        description:
            - Community string or v3 username.
        required: false
        default: null
    udp:
        description:
            - UDP port number (0-65535).
        required: false
        default: null
    type:
        description:
            - type of message to send to host.
        required: false
        default: traps
        choices: ['trap', 'inform']
    vrf:
        description:
            - VRF to use to source traffic to source.
        required: false
        default: null
    vrf_filter:
        description:
            - Name of VRF to filter.
        required: false
        default: null
    src_intf:
        description:
            - Source interface.
        required: false
        default: null
    state:
        description:
            - Manage the state of the resource.
        required: true
        default: present
        choices: ['present','absent']

'''

EXAMPLES = '''
# ensure snmp host is configured
- nxos_snmp_host:
    snmp_host: 3.3.3.3
    community: TESTING
    state: present
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"community": "TESTING", "snmp_host": "3.3.3.3", 
            "snmp_type": "trap", "version": "v2c", "vrf_filter": "one_more_vrf"}
existing:
    description: k/v pairs of existing snmp host
    type: dict
    sample: {"community": "TESTING", "snmp_type": "trap",
            "udp": "162", "v3": "noauth", "version": "v2c",
            "vrf": "test_vrf", "vrf_filter": ["test_vrf",
            "another_test_vrf"]}
end_state:
    description: k/v pairs of switchport after module execution
    returned: always
    type: dict or null
    sample: {"community": "TESTING", "snmp_type": "trap",
            "udp": "162", "v3": "noauth", "version": "v2c",
            "vrf": "test_vrf", "vrf_filter": ["test_vrf",
            "another_test_vrf", "one_more_vrf"]}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["snmp-server host 3.3.3.3 filter-vrf another_test_vrf"]
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


def get_snmp_host(host, module):
    command = 'show snmp host'
    body = execute_show_command(command, module)

    host_map = {
        'port': 'udp',
        'version': 'version',
        'level': 'v3',
        'type': 'snmp_type',
        'secname': 'community'
    }

    resource = {}

    if body:
        try:
            resource_table = body[0]['TABLE_host']['ROW_host']

            if isinstance(resource_table, dict):
                resource_table = [resource_table]

            for each in resource_table:
                key = str(each['host'])
                src = each.get('src_intf', None)
                host_resource = apply_key_map(host_map, each)

                if src:
                    host_resource['src_intf'] = src.split(':')[1].strip()

                vrf_filt = each.get('TABLE_vrf_filters', None)
                if vrf_filt:
                    vrf_filter = vrf_filt['ROW_vrf_filters']['vrf_filter'].split(':')[1].split(',')
                    filters = [vrf.strip() for vrf in vrf_filter]
                    host_resource['vrf_filter'] = filters

                vrf = each.get('vrf', None)
                if vrf:
                    host_resource['vrf'] = vrf.split(':')[1].strip()
                resource[key] = host_resource

        except (KeyError, AttributeError, TypeError):
            return resource

        find = resource.get(host, None)

        if find:
            fix_find = {}
            for (key, value) in find.iteritems():
                if isinstance(value, str):
                    fix_find[key] = value.strip()
                else:
                    fix_find[key] = value
            return fix_find
        else:
            return {}
    else:
        return {}


def remove_snmp_host(host, existing):
    commands = []
    if existing['version'] == 'v3':
        existing['version'] = '3'
        command = 'no snmp-server host {0} {snmp_type} version \
                    {version} {v3} {community}'.format(host, **existing)

    elif existing['version'] == 'v2c':
        existing['version'] = '2c'
        command = 'no snmp-server host {0} {snmp_type} version \
                    {version} {community}'.format(host, **existing)

    if command:
        commands.append(command)
    return commands


def config_snmp_host(delta, proposed, existing, module):
    commands = []
    command_builder = []
    host = proposed['snmp_host']
    cmd = 'snmp-server host {0}'.format(proposed['snmp_host'])

    snmp_type = delta.get('snmp_type', None)
    version = delta.get('version', None)
    ver = delta.get('v3', None)
    community = delta.get('community', None)

    command_builder.append(cmd)
    if any([snmp_type, version, ver, community]):
        type_string = snmp_type or existing.get('type')
        if type_string:
            command_builder.append(type_string)

        version = version or existing.get('version')
        if version:
            if version == 'v2c':
                vn = '2c'
            elif version == 'v3':
                vn = '3'

            version_string = 'version {0}'.format(vn)
            command_builder.append(version_string)

        if ver:
            ver_string = ver or existing.get('v3')
            command_builder.append(ver_string)

        if community:
            community_string = community or existing.get('community')
            command_builder.append(community_string)

        cmd = ' '.join(command_builder)

        commands.append(cmd)

    CMDS = {
        'vrf_filter': 'snmp-server host {0} filter-vrf {vrf_filter}',
        'vrf': 'snmp-server host {0} use-vrf {vrf}',
        'udp': 'snmp-server host {0} udp-port {udp}',
        'src_intf': 'snmp-server host {0} source-interface {src_intf}'
    }

    for key, value in delta.iteritems():
        if key in ['vrf_filter', 'vrf', 'udp', 'src_intf']:
            command = CMDS.get(key, None)
            if command:
                cmd = command.format(host, **delta)
                commands.append(cmd)
            cmd = None
    return commands


def flatten_list(command_lists):
    flat_command_list = []
    for command in command_lists:
        if isinstance(command, list):
            flat_command_list.extend(command)
        else:
            flat_command_list.append(command)
    return flat_command_list


def main():
    argument_spec = dict(
            snmp_host=dict(required=True, type='str'),
            community=dict(type='str'),
            udp=dict(type='str'),
            version=dict(choices=['v2c', 'v3'], default='v2c'),
            src_intf=dict(type='str'),
            v3=dict(choices=['noauth', 'auth', 'priv']),
            vrf_filter=dict(type='str'),
            vrf=dict(type='str'),
            snmp_type=dict(choices=['trap', 'inform'], default='trap'),
            state=dict(choices=['absent', 'present'], default='present'),
    )
    module = get_network_module(argument_spec=argument_spec,
                                supports_check_mode=True)


    snmp_host = module.params['snmp_host']
    community = module.params['community']
    udp = module.params['udp']
    version = module.params['version']
    src_intf = module.params['src_intf']
    v3 = module.params['v3']
    vrf_filter = module.params['vrf_filter']
    vrf = module.params['vrf']
    snmp_type = module.params['snmp_type']

    state = module.params['state']

    if snmp_type == 'inform' and version != 'v3':
        module.fail_json(msg='inform requires snmp v3')

    if version == 'v2c' and v3:
        module.fail_json(msg='param: "v3" should not be used when '
                             'using version v2c')

    if not any([vrf_filter, vrf, udp, src_intf]):
        if not all([snmp_type, version, community]):
            module.fail_json(msg='when not configuring options like '
                                 'vrf_filter, vrf, udp, and src_intf,'
                                 'the following params are required: '
                                 'type, version, community')

    if version == 'v3' and v3 is None:
        module.fail_json(msg='when using version=v3, the param v3 '
                             '(options: auth, noauth, priv) is also required')

    existing = get_snmp_host(snmp_host, module)

    # existing returns the list of vrfs configured for a given host
    # checking to see if the proposed is in the list
    store = existing.get('vrf_filter', None)
    if existing and store:
        if vrf_filter not in existing['vrf_filter']:
            existing['vrf_filter'] = None
        else:
            existing['vrf_filter'] = vrf_filter

    args = dict(
            community=community,
            snmp_host=snmp_host,
            udp=udp,
            version=version,
            src_intf=src_intf,
            vrf_filter=vrf_filter,
            v3=v3,
            vrf=vrf,
            snmp_type=snmp_type
            )

    proposed = dict((k, v) for k, v in args.iteritems() if v is not None)

    delta = dict(set(proposed.iteritems()).difference(existing.iteritems()))

    changed = False
    commands = []
    end_state = existing

    if state == 'absent':
        if existing:
            command = remove_snmp_host(snmp_host, existing)
            commands.append(command)
    elif state == 'present':
        if delta:
            command = config_snmp_host(delta, proposed, existing, module)
            commands.append(command)

    cmds = flatten_list(commands)
    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            changed = True
            execute_config_command(cmds, module)
            end_state = get_snmp_host(snmp_host, module)
            if 'configure' in cmds:
                cmds.pop(0)

    if store:
        existing['vrf_filter'] = store

    results = {}
    results['proposed'] = proposed
    results['existing'] = existing
    results['end_state'] = end_state
    results['updates'] = cmds
    results['changed'] = changed

    module.exit_json(**results)


if __name__ == "__main__":
    main()
