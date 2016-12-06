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
module: nxos_hsrp
version_added: "2.2"
short_description: Manages HSRP configuration on NX-OS switches.
description:
    - Manages HSRP configuration on NX-OS switches.
extends_documentation_fragment: nxos
author:
    - Jason Edelman (@jedelman8)
    - Gabriele Gerbino (@GGabriele)
notes:
    - HSRP feature needs to be enabled first on the system.
    - SVIs must exist before using this module.
    - Interface must be a L3 port before using this module.
    - HSRP cannot be configured on loopback interfaces.
    - MD5 authentication is only possible with HSRPv2 while it is ignored if
      HSRPv1 is used instead, while it will not raise any error. Here we allow
      MD5 authentication only with HSRPv2 in order to enforce better practice.
options:
    group:
        description:
            - HSRP group number.
        required: true
    interface:
        description:
            - Full name of interface that is being managed for HSRP.
        required: true
    version:
        description:
            - HSRP version.
        required: false
        default: 2
        choices: ['1','2']
    priority:
        description:
            - HSRP priority.
        required: false
        default: null
    vip:
        description:
            - HSRP virtual IP address.
        required: false
        default: null
    auth_string:
        description:
            - Authentication string.
        required: false
        default: null
    auth_type:
        description:
            - Authentication type.
        required: false
        default: null
        choices: ['text','md5']
    state:
        description:
            - Specify desired state of the resource.
        required: false
        choices: ['present','absent']
        default: 'present'
'''

EXAMPLES = '''
- name: Ensure HSRP is configured with following params on a SVI
  nxos_hsrp:
    group: 10
    vip: 10.1.1.1
    priority: 150
    interface: vlan10
    preempt: enabled
    host: 68.170.147.165

- name: Ensure HSRP is configured with following params on a SVI
  nxos_hsrp:
    group: 10
    vip: 10.1.1.1
    priority: 150
    interface: vlan10
    preempt: enabled
    host: 68.170.147.165
    auth_type: text
    auth_string: CISCO

- name: Remove HSRP config for given interface, group, and VIP
  nxos_hsrp:
    group: 10
    interface: vlan10
    vip: 10.1.1.1
    host: 68.170.147.165
    state: absent
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"group": "30", "version": "2", "vip": "10.30.1.1"}
existing:
    description: k/v pairs of existing hsrp info on the interface
    type: dict
    sample: {}
end_state:
    description: k/v pairs of hsrp after module execution
    returned: always
    type: dict
    sample: {"auth_string": "cisco", "auth_type": "text",
            "group": "30", "interface": "vlan10", "preempt": "disabled",
            "priority": "100", "version": "2", "vip": "10.30.1.1"}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["interface vlan10", "hsrp version 2", "hsrp 30", "ip 10.30.1.1"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''

import json

# COMMON CODE FOR MIGRATION

import ansible.module_utils.nxos
from ansible.module_utils.basic import get_exception
from ansible.module_utils.netcfg import NetworkConfig, ConfigLine
from ansible.module_utils.shell import ShellError
from ansible.module_utils.network import NetworkModule


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
        output = module.configure(commands)
    except ShellError:
        clie = get_exception()
        module.fail_json(msg='Error sending CLI commands',
                         error=str(clie), commands=commands)
    except AttributeError:
        try:
            commands.insert(0, 'configure')
            module.cli.add_commands(commands, output='config')
            output = module.cli.run_commands()
        except ShellError:
            clie = get_exception()
            module.fail_json(msg='Error sending CLI commands',
                             error=str(clie), commands=commands)
    return output


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
            response = response[0].replace(command + '\n\n', '').strip()
            body = [json.loads(response)]
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


def get_interface_type(interface):
    if interface.upper().startswith('ET'):
        return 'ethernet'
    elif interface.upper().startswith('VL'):
        return 'svi'
    elif interface.upper().startswith('LO'):
        return 'loopback'
    elif interface.upper().startswith('MG'):
        return 'management'
    elif interface.upper().startswith('MA'):
        return 'management'
    elif interface.upper().startswith('PO'):
        return 'portchannel'
    else:
        return 'unknown'


def get_interface_mode(interface, intf_type, module):
    command = 'show interface {0}'.format(interface)
    interface = {}
    mode = 'unknown'

    if intf_type in ['ethernet', 'portchannel']:
        body = execute_show_command(command, module)[0]
        interface_table = body['TABLE_interface']['ROW_interface']
        mode = str(interface_table.get('eth_mode', 'layer3'))
        if mode == 'access' or mode == 'trunk':
            mode = 'layer2'
    elif intf_type == 'svi':
        mode = 'layer3'
    return mode


def get_hsrp_groups_on_interfaces(device, module):
    command = 'show hsrp all'
    body = execute_show_command(command, module)
    hsrp = {}

    try:
        get_data = body[0]['TABLE_grp_detail']['ROW_grp_detail']
    except (KeyError, AttributeError):
        return {}

    for entry in get_data:
        interface = str(entry['sh_if_index'].lower())
        value = hsrp.get(interface, 'new')
        if value == 'new':
            hsrp[interface] = []
        group = str(entry['sh_group_num'])
        hsrp[interface].append(group)

    return hsrp


def get_hsrp_group(group, interface, module):
    command = 'show hsrp group {0}'.format(group)
    body = execute_show_command(command, module)
    hsrp = {}

    hsrp_key = {
        'sh_if_index': 'interface',
        'sh_group_num': 'group',
        'sh_group_version': 'version',
        'sh_cfg_prio': 'priority',
        'sh_preempt': 'preempt',
        'sh_vip': 'vip',
        'sh_authentication_type': 'auth_type',
        'sh_authentication_data': 'auth_string'
    }

    try:
        hsrp_table = body[0]['TABLE_grp_detail']['ROW_grp_detail']
    except (AttributeError, IndexError, TypeError):
        return {}

    if isinstance(hsrp_table, dict):
        hsrp_table = [hsrp_table]

    for hsrp_group in hsrp_table:
        parsed_hsrp = apply_key_map(hsrp_key, hsrp_group)

        parsed_hsrp['interface'] = parsed_hsrp['interface'].lower()

        if parsed_hsrp['version'] == 'v1':
            parsed_hsrp['version'] = '1'
        elif parsed_hsrp['version'] == 'v2':
            parsed_hsrp['version'] = '2'

        if parsed_hsrp['interface'] == interface:
            return parsed_hsrp

    return hsrp


def get_commands_remove_hsrp(group, interface):
    commands = []
    commands.append('interface {0}'.format(interface))
    commands.append('no hsrp {0}'.format(group))
    return commands


def get_commands_config_hsrp(delta, interface, args):
    commands = []

    config_args = {
        'group': 'hsrp {group}',
        'priority': 'priority {priority}',
        'preempt': '{preempt}',
        'vip': 'ip {vip}'
    }

    preempt = delta.get('preempt', None)
    group = delta.get('group', None)
    if preempt:
        if preempt == 'enabled':
            delta['preempt'] = 'preempt'
        elif preempt == 'disabled':
            delta['preempt'] = 'no preempt'

    for key, value in delta.iteritems():
        command = config_args.get(key, 'DNE').format(**delta)
        if command and command != 'DNE':
            if key == 'group':
                commands.insert(0, command)
            else:
                commands.append(command)
        command = None

    auth_type = delta.get('auth_type', None)
    auth_string = delta.get('auth_string', None)
    if auth_type or auth_string:
        if not auth_type:
            auth_type = args['auth_type']
        elif not auth_string:
            auth_string = args['auth_string']
        if auth_type == 'md5':
            command = 'authentication md5 key-string {0}'.format(auth_string)
            commands.append(command)
        elif auth_type == 'text':
            command = 'authentication text {0}'.format(auth_string)
            commands.append(command)

    if commands and not group:
        commands.insert(0, 'hsrp {0}'.format(args['group']))

    version = delta.get('version', None)
    if version:
        if version == '2':
            command = 'hsrp version 2'
        elif version == '1':
            command = 'hsrp version 1'
        commands.insert(0, command)
        commands.insert(0, 'interface {0}'.format(interface))

    if commands:
        if not commands[0].startswith('interface'):
            commands.insert(0, 'interface {0}'.format(interface))

    return commands


def is_default(interface, module):
    command = 'show run interface {0}'.format(interface)

    try:
        body = execute_show_command(command, module)[0]
        if 'invalid' in body.lower():
            return 'DNE'
        else:
            raw_list = body.split('\n')
            if raw_list[-1].startswith('interface'):
                return True
            else:
                return False
    except (KeyError):
        return 'DNE'


def validate_config(body, vip, module):
    new_body = ''.join(body)
    if "invalid ip address" in new_body.lower():
            module.fail_json(msg="Invalid VIP. Possible duplicate IP address.",
                             vip=vip)


def validate_params(param, module):
    value = module.params[param]
    version = module.params['version']

    if param == 'group':
        try:
            if (int(value) < 0 or int(value) > 255) and version == '1':
                raise ValueError
            elif int(value) < 0 or int(value) > 4095:
                raise ValueError
        except ValueError:
            module.fail_json(msg="Warning! 'group' must be an integer between"
                                 " 0 and 255 when version 1 and up to 4095 "
                                 "when version 2.", group=value,
                                 version=version)
    elif param == 'priority':
        try:
            if (int(value) < 0 or int(value) > 255):
                raise ValueError
        except ValueError:
            module.fail_json(msg="Warning! 'priority' must be an integer "
                                 "between 0 and 255", priority=value)


def main():
    argument_spec = dict(
            group=dict(required=True, type='str'),
            interface=dict(required=True),
            version=dict(choices=['1', '2'], default='2', required=False),
            priority=dict(type='str', required=False),
            preempt=dict(type='str', choices=['disabled', 'enabled'],
                         required=False),
            vip=dict(type='str', required=False),
            auth_type=dict(choices=['text', 'md5'], required=False),
            auth_string=dict(type='str', required=False),
            state=dict(choices=['absent', 'present'], required=False,
                       default='present'),
            include_defaults=dict(default=True),
            config=dict(),
            save=dict(type='bool', default=False)
    )
    module = get_network_module(argument_spec=argument_spec,
                            supports_check_mode=True)

    interface = module.params['interface'].lower()
    group = module.params['group']
    version = module.params['version']
    state = module.params['state']
    priority = module.params['priority']
    preempt = module.params['preempt']
    vip = module.params['vip']
    auth_type = module.params['auth_type']
    auth_string = module.params['auth_string']

    transport = module.params['transport']

    if state == 'present' and not vip:
        module.fail_json(msg='the "vip" param is required when state=present')

    for param in ['group', 'priority']:
        if module.params[param] is not None:
            validate_params(param, module)

    intf_type = get_interface_type(interface)
    if (intf_type != 'ethernet' and transport == 'cli'):
        if is_default(interface, module) == 'DNE':
            module.fail_json(msg='That interface does not exist yet. Create '
                                 'it first.', interface=interface)
        if intf_type == 'loopback':
            module.fail_json(msg="Loopback interfaces don't support HSRP.",
                             interface=interface)

    mode = get_interface_mode(interface, intf_type, module)
    if mode == 'layer2':
        module.fail_json(msg='That interface is a layer2 port.\nMake it '
                             'a layer 3 port first.', interface=interface)

    if auth_type or auth_string:
        if not (auth_type and auth_string):
            module.fail_json(msg='When using auth parameters, you need BOTH '
                                 'auth_type AND auth_string.')

    args = dict(group=group, version=version, priority=priority,
                preempt=preempt, vip=vip, auth_type=auth_type,
                auth_string=auth_string)

    proposed = dict((k, v) for k, v in args.iteritems() if v is not None)

    existing = get_hsrp_group(group, interface, module)

    # This will enforce better practice with md5 and hsrp version.
    if proposed.get('auth_type', None) == 'md5':
        if proposed['version'] == '1':
            module.fail_json(msg="It's recommended to use HSRP v2 "
                                 "when auth_type=md5")

    elif not proposed.get('auth_type', None) and existing:
        if (proposed['version'] == '1' and
                existing['auth_type'] == 'md5'):
            module.fail_json(msg="Existing auth_type is md5. It's recommended "
                                 "to use HSRP v2 when using md5")

    changed = False
    end_state = existing
    commands = []
    if state == 'present':
        delta = dict(
                    set(proposed.iteritems()).difference(existing.iteritems()))
        if delta:
            command = get_commands_config_hsrp(delta, interface, args)
            commands.extend(command)

    elif state == 'absent':
        if existing:
            command = get_commands_remove_hsrp(group, interface)
            commands.extend(command)

    if commands:
        if module.check_mode:
            module.exit_json(changed=True, commands=commands)
        else:
            body = execute_config_command(commands, module)
            if transport == 'cli':
                validate_config(body, vip, module)
            changed = True
            end_state = get_hsrp_group(group, interface, module)
            if 'configure' in commands:
                commands.pop(0)

    results = {}
    results['proposed'] = proposed
    results['existing'] = existing
    results['end_state'] = end_state
    results['updates'] = commands
    results['changed'] = changed

    module.exit_json(**results)


if __name__ == '__main__':
    main()
