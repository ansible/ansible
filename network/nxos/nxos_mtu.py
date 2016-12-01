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
module: nxos_mtu
version_added: "2.2"
short_description: Manages MTU settings on Nexus switch.
description:
    - Manages MTU settings on Nexus switch.
extends_documentation_fragment: nxos
author:
    - Jason Edelman (@jedelman8)
notes:
    - Either C(sysmtu) param is required or C(interface) AND C(mtu) params are req'd.
    - C(state=absent) unconfigures a given MTU if that value is currently present.
options:
    interface:
        description:
            - Full name of interface, i.e. Ethernet1/1.
        required: false
        default: null
    mtu:
        description:
            - MTU for a specific interface.
        required: false
        default: null
    sysmtu:
        description:
            - System jumbo MTU.
        required: false
        default: null
    state:
        description:
            - Specify desired state of the resource.
        required: false
        default: present
        choices: ['present','absent']
'''

EXAMPLES = '''
# Ensure system mtu is 9126
- nxos_mtu:
    sysmtu: 9216
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"

# Config mtu on Eth1/1 (routed interface)
- nxos_mtu:
    interface: Ethernet1/1
    mtu: 1600
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"

# Config mtu on Eth1/3 (switched interface)
- nxos_mtu:
    interface: Ethernet1/3
    mtu: 9216
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"

# Unconfigure mtu on a given interface
- nxos_mtu:
    interface: Ethernet1/3
    mtu: 9216
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"
    state: absent
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"mtu": "1700"}
existing:
    description:
        - k/v pairs of existing mtu/sysmtu on the interface/system
    type: dict
    sample: {"mtu": "1600", "sysmtu": "9216"}
end_state:
    description: k/v pairs of mtu/sysmtu values after module execution
    returned: always
    type: dict
    sample: {"mtu": "1700", sysmtu": "9216"}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["interface vlan10", "mtu 1700"]
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


def get_mtu(interface, module):
    command = 'show interface {0}'.format(interface)
    mtu = {}

    body = execute_show_command(command, module)

    try:
        mtu_table = body[0]['TABLE_interface']['ROW_interface']
        mtu['mtu'] = str(
            mtu_table.get('eth_mtu',
                          mtu_table.get('svi_mtu', 'unreadable_via_api')))
        mtu['sysmtu'] = get_system_mtu(module)['sysmtu']
    except KeyError:
        mtu = {}

    return mtu


def get_system_mtu(module):
    command = 'show run all | inc jumbomtu'
    sysmtu = ''

    body = execute_show_command(command, module, command_type='cli_show_ascii')

    if body:
        sysmtu = str(body[0].split(' ')[-1])
        try:
            sysmtu = int(sysmtu)
        except:
            sysmtu = ""

    return dict(sysmtu=str(sysmtu))


def get_commands_config_mtu(delta, interface):
    CONFIG_ARGS = {
        'mtu': 'mtu {mtu}',
        'sysmtu': 'system jumbomtu {sysmtu}',
    }

    commands = []
    for param, value in delta.iteritems():
        command = CONFIG_ARGS.get(param, 'DNE').format(**delta)
        if command and command != 'DNE':
            commands.append(command)
        command = None
    mtu_check = delta.get('mtu', None)
    if mtu_check:
        commands.insert(0, 'interface {0}'.format(interface))
    return commands


def get_commands_remove_mtu(delta, interface):
    CONFIG_ARGS = {
        'mtu': 'no mtu {mtu}',
        'sysmtu': 'no system jumbomtu {sysmtu}',
    }
    commands = []
    for param, value in delta.iteritems():
        command = CONFIG_ARGS.get(param, 'DNE').format(**delta)
        if command and command != 'DNE':
            commands.append(command)
        command = None
    mtu_check = delta.get('mtu', None)
    if mtu_check:
        commands.insert(0, 'interface {0}'.format(interface))
    return commands


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


def is_default(interface, module):
    command = 'show run interface {0}'.format(interface)

    try:
        body = execute_show_command(
                command, module, command_type='cli_show_ascii')[0]
        if body == 'DNE':
            return 'DNE'
        else:
            raw_list = body.split('\n')
            if raw_list[-1].startswith('interface'):
                return True
            else:
                return False
    except (KeyError):
        return 'DNE'


def get_interface_mode(interface, intf_type, module):
    command = 'show interface {0}'.format(interface)
    mode = 'unknown'
    interface_table = {}
    body = execute_show_command(command, module)

    try:
        interface_table = body[0]['TABLE_interface']['ROW_interface']
    except (KeyError, AttributeError, IndexError):
        return mode

    if intf_type in ['ethernet', 'portchannel']:
        mode = str(interface_table.get('eth_mode', 'layer3'))
        if mode in ['access', 'trunk']:
            mode = 'layer2'
        elif mode == 'routed':
            mode = 'layer3'
    elif intf_type in ['loopback', 'svi']:
        mode = 'layer3'
    return mode


def main():
    argument_spec = dict(
            mtu=dict(type='str'),
            interface=dict(type='str'),
            sysmtu=dict(type='str'),
            state=dict(choices=['absent', 'present'], default='present'),
    )
    module = get_network_module(argument_spec=argument_spec,
                                required_together=[['mtu', 'interface']],
                                supports_check_mode=True)

    interface = module.params['interface']
    mtu = module.params['mtu']
    sysmtu = module.params['sysmtu']
    state = module.params['state']

    if sysmtu and (interface or mtu):
        module.fail_json(msg='Proper usage-- either just use the sysmtu param '
                             'or use interface AND mtu params')

    if interface:
        intf_type = get_interface_type(interface)
        if intf_type != 'ethernet':
            if is_default(interface, module) == 'DNE':
                module.fail_json(msg='Invalid interface.  It does not exist '
                                     'on the switch.')

        existing = get_mtu(interface, module)
    else:
        existing = get_system_mtu(module)

    if interface and mtu:
        if intf_type == 'loopback':
            module.fail_json(msg='Cannot set MTU for loopback interface.')
        mode = get_interface_mode(interface, intf_type, module)
        if mode == 'layer2':
            if intf_type in ['ethernet', 'portchannel']:
                if mtu not in [existing['sysmtu'], '1500']:
                    module.fail_json(msg='MTU on L2 interfaces can only be set'
                                         ' to the system default (1500) or '
                                         'existing sysmtu value which is '
                                         ' {0}'.format(existing['sysmtu']))
        elif mode == 'layer3':
            if intf_type in ['ethernet', 'portchannel', 'svi']:
                if ((int(mtu) < 576 or int(mtu) > 9216) or
                        ((int(mtu) % 2) != 0)):
                    module.fail_json(msg='Invalid MTU for Layer 3 interface'
                                         'needs to be an even number between'
                                         '576 and 9216')
    if sysmtu:
        if ((int(sysmtu) < 576 or int(sysmtu) > 9216 or
                ((int(sysmtu) % 2) != 0))):
                    module.fail_json(msg='Invalid MTU- needs to be an even '
                                         'number between 576 and 9216')

    args = dict(mtu=mtu, sysmtu=sysmtu)
    proposed = dict((k, v) for k, v in args.iteritems() if v is not None)
    delta = dict(set(proposed.iteritems()).difference(existing.iteritems()))

    changed = False
    end_state = existing
    commands = []

    if state == 'present':
        if delta:
            command = get_commands_config_mtu(delta, interface)
            commands.append(command)

    elif state == 'absent':
        common = set(proposed.iteritems()).intersection(existing.iteritems())
        if common:
            command = get_commands_remove_mtu(dict(common), interface)
            commands.append(command)

    cmds = flatten_list(commands)
    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            changed = True
            execute_config_command(cmds, module)
            if interface:
                end_state = get_mtu(interface, module)
            else:
                end_state = get_system_mtu(module)
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
