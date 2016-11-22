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
module: nxos_vrrp
version_added: "2.1"
short_description: Manages VRRP configuration on NX-OS switches
description:
    - Manages VRRP configuration on NX-OS switches
extends_documentation_fragment: nxos
author:
    - Jason Edelman (@jedelman8)
    - Gabriele Gerbino (@GGabriele)
notes:
    - VRRP feature needs to be enabled first on the system
    - SVIs must exist before using this module
    - Interface must be a L3 port before using this module
    - I(state)=absent removes the vrrp group if it exists on the device
    - VRRP cannot be configured on loopback interfaces
options:
    group:
        description:
            - VRRP group number
        required: true
    interface:
        description:
            - Full name of interface that is being managed for VRRP
        required: true
    priority:
        description:
            - VRRP priority
        required: false
        default: null
    vip:
        description:
            - VRRP virtual IP address
        required: false
        default: null
    authentication:
        description:
            - clear text authentication string
        required: false
        default: null
    admin_state:
        description:
            - Used to enable or disable the VRRP process
        required: false
        choices: ['shutdown', 'no shutdown']
        default: no shutdown
        version_added: "2.2"
    state:
        description:
            - Specify desired state of the resource
        required: false
        default: present
        choices: ['present','absent']
'''

EXAMPLES = '''
- name: Ensure vrrp group 100 and vip 10.1.100.1 is on vlan10
  nxos_vrrp:
    interface: vlan10
    group: 100
    vip: 10.1.100.1
    host: 68.170.147.165

- name: Ensure removal of the vrrp group config
  # vip is required to ensure the user knows what they are removing
  nxos_vrrp:
    interface: vlan10
    group: 100
    vip: 10.1.100.1
    state: absent
    host: 68.170.147.165

- name: Re-config with more params
  nxos_vrrp:
    interface: vlan10
    group: 100
    vip: 10.1.100.1
    preempt: false
    priority: 130
    authentication: AUTHKEY
    host: 68.170.147.165
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"authentication": "testing", "group": "150", "vip": "10.1.15.1",
            "admin_state": "no shutdown"}
existing:
    description: k/v pairs of existing vrrp info on the interface
    type: dict
    sample: {}
end_state:
    description: k/v pairs of vrrp after module execution
    returned: always
    type: dict
    sample: {"authentication": "testing", "group": "150", "interval": "1",
            "preempt": true, "priority": "100", "vip": "10.1.15.1",
            "admin_state": "no shutdown"}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["interface vlan10", "vrrp 150", "address 10.1.15.1",
            "authentication text testing", "no shutdown"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''

import json
import collections

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


def get_cli_body_ssh_vrrp(command, response, module):
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
        body = get_cli_body_ssh_vrrp(command, response, module)
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


def get_interface_mode(interface, intf_type, module):
    command = 'show interface {0}'.format(interface)
    interface = {}
    mode = 'unknown'
    body = execute_show_command(command, module)[0]
    interface_table = body['TABLE_interface']['ROW_interface']
    name = interface_table.get('interface')

    if intf_type in ['ethernet', 'portchannel']:
        mode = str(interface_table.get('eth_mode', 'layer3'))

        if mode == 'access' or mode == 'trunk':
            mode = 'layer2'
    elif intf_type == 'svi':
        mode = 'layer3'

    return mode, name


def get_vrr_status(group, module, interface):
    command = 'show run all | section interface.{0}$'.format(interface)
    body = execute_show_command(command, module, command_type='cli_show_ascii')[0]
    vrf_index = None
    admin_state = 'shutdown'

    if body:
        splitted_body = body.splitlines()
        for index in range(0, len(splitted_body) - 1):
            if splitted_body[index].strip() == 'vrrp {0}'.format(group):
                vrf_index = index
        vrf_section = splitted_body[vrf_index::]

        for line in vrf_section:
            if line.strip() == 'no shutdown':
                admin_state = 'no shutdown'
                break

    return admin_state


def get_existing_vrrp(interface, group, module, name):
    command = 'show vrrp detail interface {0}'.format(interface)
    body = execute_show_command(command, module)
    vrrp = {}

    vrrp_key = {
        'sh_group_id': 'group',
        'sh_vip_addr': 'vip',
        'sh_priority': 'priority',
        'sh_group_preempt': 'preempt',
        'sh_auth_text': 'authentication',
        'sh_adv_interval': 'interval'
    }

    try:
        vrrp_table = body[0]['TABLE_vrrp_group']
    except (AttributeError, IndexError, TypeError):
        return {}

    if isinstance(vrrp_table, dict):
        vrrp_table = [vrrp_table]

    for each_vrrp in vrrp_table:
        vrrp_row = each_vrrp['ROW_vrrp_group']
        parsed_vrrp = apply_key_map(vrrp_key, vrrp_row)

        if parsed_vrrp['preempt'] == 'Disable':
            parsed_vrrp['preempt'] = False
        elif parsed_vrrp['preempt'] == 'Enable':
            parsed_vrrp['preempt'] = True

        if parsed_vrrp['group'] == group:
            parsed_vrrp['admin_state'] = get_vrr_status(group, module, name)

            return parsed_vrrp
    return vrrp


def get_commands_config_vrrp(delta, group):
    commands = []

    CMDS = {
        'priority': 'priority {0}',
        'preempt': 'preempt',
        'vip': 'address {0}',
        'interval': 'advertisement-interval {0}',
        'auth': 'authentication text {0}'
    }

    vip = delta.get('vip')
    priority = delta.get('priority')
    preempt = delta.get('preempt')
    interval = delta.get('interval')
    auth = delta.get('authentication')
    admin_state = delta.get('admin_state')

    if vip:
        commands.append((CMDS.get('vip')).format(vip))
    if priority:
        commands.append((CMDS.get('priority')).format(priority))
    if preempt:
        commands.append(CMDS.get('preempt'))
    elif preempt is False:
        commands.append('no ' + CMDS.get('preempt'))
    if interval:
        commands.append((CMDS.get('interval')).format(interval))
    if auth:
        commands.append((CMDS.get('auth')).format(auth))
    if admin_state:
        commands.append(admin_state)

    commands.insert(0, 'vrrp {0}'.format(group))

    return commands


def flatten_list(command_lists):
    flat_command_list = []
    for command in command_lists:
        if isinstance(command, list):
            flat_command_list.extend(command)
        else:
            flat_command_list.append(command)
    return flat_command_list


def validate_params(param, module):
    value = module.params[param]

    if param == 'group':
        try:
            if (int(value) < 1 or int(value) > 255):
                raise ValueError
        except ValueError:
            module.fail_json(msg="Warning! 'group' must be an integer between"
                                 " 1 and 255", group=value)
    elif param == 'priority':
        try:
            if (int(value) < 1 or int(value) > 254):
                raise ValueError
        except ValueError:
            module.fail_json(msg="Warning! 'priority' must be an integer "
                                 "between 1 and 254", priority=value)


def main():
    argument_spec = dict(
            group=dict(required=True, type='str'),
            interface=dict(required=True),
            priority=dict(required=False, type='str'),
            preempt=dict(required=False, type='bool'),
            vip=dict(required=False, type='str'),
            admin_state=dict(required=False, type='str',
                                choices=['shutdown', 'no shutdown'],
                                default='no shutdown'),
            authentication=dict(required=False, type='str'),
            state=dict(choices=['absent', 'present'],
                       required=False, default='present'),
            include_defaults=dict(default=False),
            config=dict(),
            save=dict(type='bool', default=False)
    )
    module = get_network_module(argument_spec=argument_spec,
                                supports_check_mode=True)

    state = module.params['state']
    interface = module.params['interface'].lower()
    group = module.params['group']
    priority = module.params['priority']
    preempt = module.params['preempt']
    vip = module.params['vip']
    authentication = module.params['authentication']
    admin_state = module.params['admin_state']

    transport = module.params['transport']

    if state == 'present' and not vip:
        module.fail_json(msg='the "vip" param is required when state=present')

    intf_type = get_interface_type(interface)
    if (intf_type != 'ethernet' and transport == 'cli'):
        if is_default(interface, module) == 'DNE':
            module.fail_json(msg='That interface does not exist yet. Create '
                                 'it first.', interface=interface)
        if intf_type == 'loopback':
            module.fail_json(msg="Loopback interfaces don't support VRRP.",
                             interface=interface)

    mode, name = get_interface_mode(interface, intf_type, module)
    if mode == 'layer2':
        module.fail_json(msg='That interface is a layer2 port.\nMake it '
                             'a layer 3 port first.', interface=interface)

    args = dict(group=group, priority=priority, preempt=preempt,
                vip=vip, authentication=authentication,
                admin_state=admin_state)

    proposed = dict((k, v) for k, v in args.iteritems() if v is not None)
    existing = get_existing_vrrp(interface, group, module, name)

    changed = False
    end_state = existing
    commands = []

    if state == 'present':
        delta = dict(
            set(proposed.iteritems()).difference(existing.iteritems()))
        if delta:
            command = get_commands_config_vrrp(delta, group)
            commands.append(command)

    elif state == 'absent':
        if existing:
            commands.append(['no vrrp {0}'.format(group)])

    if commands:
        commands.insert(0, ['interface {0}'.format(interface)])

    cmds = flatten_list(commands)
    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            execute_config_command(cmds, module)
            changed = True
            end_state = get_existing_vrrp(interface, group, module, name)
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
