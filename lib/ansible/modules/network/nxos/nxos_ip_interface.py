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
module: nxos_ip_interface
version_added: "2.1"
short_description: Manages L3 attributes for IPv4 and IPv6 interfaces.
description:
    - Manages Layer 3 attributes for IPv4 and IPv6 interfaces.
extends_documentation_fragment: nxos
author:
    - Jason Edelman (@jedelman8)
    - Gabriele Gerbino (@GGabriele)
notes:
    - Interface must already be a L3 port when using this module.
    - Logical interfaces (po, loop, svi) must be created first.
    - C(mask) must be inserted in decimal format (i.e. 24) for
      both IPv6 and IPv4.
    - A single interface can have multiple IPv6 configured.
options:
    interface:
        description:
            - Full name of interface, i.e. Ethernet1/1, vlan10.
        required: true
    addr:
        description:
            - IPv4 or IPv6 Address.
        required: false
        default: null
    mask:
        description:
            - Subnet mask for IPv4 or IPv6 Address in decimal format.
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
- name: Ensure ipv4 address is configured on Ethernet1/32
  nxos_ip_interface:
    interface: Ethernet1/32
    transport: nxapi
    version: v4
    state: present
    addr: 20.20.20.20
    mask: 24

- name: Ensure ipv6 address is configured on Ethernet1/31
  nxos_ip_interface:
    interface: Ethernet1/31
    transport: cli
    version: v6
    state: present
    addr: '2001::db8:800:200c:cccb'
    mask: 64
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"addr": "20.20.20.20", "interface": "ethernet1/32", "mask": "24"}
existing:
    description: k/v pairs of existing IP attributes on the interface
    type: dict
    sample: {"addresses": [{"addr": "11.11.11.11", "mask": 17}],
            "interface": "ethernet1/32", "prefix": "11.11.0.0",
            "type": "ethernet", "vrf": "default"}
end_state:
    description: k/v pairs of IP attributes after module execution
    returned: always
    type: dict
    sample: {"addresses": [{"addr": "20.20.20.20", "mask": 24}],
            "interface": "ethernet1/32", "prefix": "20.20.20.0",
            "type": "ethernet", "vrf": "default"}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["interface ethernet1/32", "ip address 20.20.20.20/24"]
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
    elif '^' in response[0] or 'show run' in response[0] or response[0] == '\n':
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
    mode = 'unknown'

    if intf_type in ['ethernet', 'portchannel']:
        body = execute_show_command(command, module)[0]

        if isinstance(body, str):
            if 'invalid interface format' in body.lower():
                module.fail_json(msg='Invalid interface name. Please check '
                                     'its format.', interface=interface)

        interface_table = body['TABLE_interface']['ROW_interface']
        mode = str(interface_table.get('eth_mode', 'layer3'))
        if mode == 'access' or mode == 'trunk':
            mode = 'layer2'
    elif intf_type == 'svi':
        mode = 'layer3'
    return mode


def send_show_command(interface_name, version, module):
    if version == 'v4':
        command = 'show ip interface {0}'.format(interface_name)
    elif version == 'v6':
        command = 'show ipv6 interface {0}'.format(interface_name)

    if module.params['transport'] == 'nxapi' and version == 'v6':
        body = execute_show_command(command, module,
                                    command_type='cli_show_ascii')
    else:
        body = execute_show_command(command, module)
    return body


def parse_structured_data(body, interface_name, version, module):
    address_list = []

    interface_key = {
        'subnet': 'prefix',
        'prefix': 'prefix'
    }

    try:
        interface_table = body[0]['TABLE_intf']['ROW_intf']
        try:
            vrf_table = body[0]['TABLE_vrf']['ROW_vrf']
            vrf = vrf_table['vrf-name-out']
        except KeyError:
            vrf = None
    except (KeyError, AttributeError):
        return {}

    interface = apply_key_map(interface_key, interface_table)
    interface['interface'] = interface_name
    interface['type'] = get_interface_type(interface_name)
    interface['vrf'] = vrf

    if version == 'v4':
        address = {}
        address['addr'] = interface_table.get('prefix', None)
        if address['addr'] is not None:
            address['mask'] = str(interface_table.get('masklen', None))
            interface['addresses'] = [address]
            prefix = "{0}/{1}".format(address['addr'], address['mask'])
            address_list.append(prefix)
        else:
            interface['addresses'] = []

    elif version == 'v6':
        address_list = interface_table.get('addr', [])
        interface['addresses'] = []

        if address_list:
            if not isinstance(address_list, list):
                address_list = [address_list]

            for ipv6 in address_list:
                address = {}
                splitted_address = ipv6.split('/')
                address['addr'] = splitted_address[0]
                address['mask'] = splitted_address[1]
                interface['addresses'].append(address)
        else:
            interface['addresses'] = []

    return interface, address_list


def parse_unstructured_data(body, interface_name, module):
    interface = {}
    address_list = []
    vrf = None

    body = body[0]
    if "ipv6 is disabled" not in body.lower():
        splitted_body = body.split('\n')

        # We can have multiple IPv6 on the same interface.
        # We need to parse them manually from raw output.
        for index in range(0, len(splitted_body) - 1):
            if "IPv6 address:" in splitted_body[index]:
                first_reference_point = index + 1
            elif "IPv6 subnet:" in splitted_body[index]:
                last_reference_point = index
                prefix_line = splitted_body[last_reference_point]
                prefix = prefix_line.split('IPv6 subnet:')[1].strip()
                interface['prefix'] = prefix

        interface_list_table = splitted_body[
                            first_reference_point:last_reference_point]

        for each_line in interface_list_table:
            address = each_line.strip().split(' ')[0]
            if address not in address_list:
                address_list.append(address)

        interface['addresses'] = []
        if address_list:
            for ipv6 in address_list:
                address = {}
                splitted_address = ipv6.split('/')
                address['addr'] = splitted_address[0]
                address['mask'] = splitted_address[1]
                interface['addresses'].append(address)

        try:
            vrf_regex = '.*VRF\s+(?P<vrf>\S+).*'
            match_vrf = re.match(vrf_regex, body, re.DOTALL)
            group_vrf = match_vrf.groupdict()
            vrf = group_vrf["vrf"]
        except AttributeError:
            vrf = None

    else:
        # IPv6's not been configured on this interface yet.
        interface['addresses'] = []

    interface['interface'] = interface_name
    interface['type'] = get_interface_type(interface_name)
    interface['vrf'] = vrf

    return interface, address_list


def get_ip_interface(interface_name, version, module):
    body = send_show_command(interface_name, version, module)

    # nxapi default response doesn't reflect the actual interface state
    # when dealing with IPv6. That's why we need to get raw output instead
    # and manually parse it.
    if module.params['transport'] == 'nxapi' and version == 'v6':
        interface, address_list = parse_unstructured_data(
                                        body, interface_name, module)
    else:
        interface, address_list = parse_structured_data(
                                        body, interface_name, version, module)

    return interface, address_list


def get_remove_ip_config_commands(interface, addr, mask, version):
    commands = []
    commands.append('interface {0}'.format(interface))
    if version == 'v4':
        commands.append('no ip address')
    else:
        commands.append('no ipv6 address {0}/{1}'.format(addr, mask))

    return commands


def get_config_ip_commands(delta, interface, existing, version):
    commands = []
    delta = dict(delta)

    # loop used in the situation that just an IP address or just a
    # mask is changing, not both.
    for each in ['addr', 'mask']:
        if each not in delta:
            delta[each] = existing[each]

    if version == 'v4':
        command = 'ip address {addr}/{mask}'.format(**delta)
    else:
        command = 'ipv6 address {addr}/{mask}'.format(**delta)
    commands.append(command)
    commands.insert(0, 'interface {0}'.format(interface))

    return commands


def flatten_list(command_lists):
    flat_command_list = []
    for command in command_lists:
        if isinstance(command, list):
            flat_command_list.extend(command)
        else:
            flat_command_list.append(command)
    return flat_command_list


def validate_params(addr, interface, mask, version, state, intf_type, module):
    if state == "present":
        if addr is None or mask is None:
            module.fail_json(msg="An IP address AND a mask must be provided "
                                 "when state=present.")
    elif state == "absent" and version == "v6":
        if addr is None or mask is None:
            module.fail_json(msg="IPv6 address and mask must be provided when "
                                 "state=absent.")

    if (intf_type != "ethernet" and module.params["transport"] == "cli"):
        if is_default(interface, module) == "DNE":
            module.fail_json(msg="That interface does not exist yet. Create "
                                 "it first.", interface=interface)
    if mask is not None:
        try:
            if (int(mask) < 1 or int(mask) > 32) and version == "v4":
                raise ValueError
            elif int(mask) < 1 or int(mask) > 128:
                raise ValueError
        except ValueError:
            module.fail_json(msg="Warning! 'mask' must be an integer between"
                                 " 1 and 32 when version v4 and up to 128 "
                                 "when version v6.", version=version,
                                 mask=mask)


def main():
    argument_spec = dict(
            interface=dict(required=True),
            addr=dict(required=False),
            version=dict(required=False, choices=['v4', 'v6'],
                         default='v4'),
            mask=dict(type='str', required=False),
            state=dict(required=False, default='present',
                       choices=['present', 'absent']),
            include_defaults=dict(default=True),
            config=dict(),
            save=dict(type='bool', default=False)
    )
    module = get_network_module(argument_spec=argument_spec,
                        supports_check_mode=True)

    addr = module.params['addr']
    version = module.params['version']
    mask = module.params['mask']
    interface = module.params['interface'].lower()
    state = module.params['state']

    intf_type = get_interface_type(interface)
    validate_params(addr, interface, mask, version, state, intf_type, module)

    mode = get_interface_mode(interface, intf_type, module)
    if mode == 'layer2':
        module.fail_json(msg='That interface is a layer2 port.\nMake it '
                             'a layer 3 port first.', interface=interface)

    existing, address_list = get_ip_interface(interface, version, module)

    args = dict(addr=addr, mask=mask, interface=interface)
    proposed = dict((k, v) for k, v in args.iteritems() if v is not None)
    commands = []
    changed = False
    end_state = existing

    if state == 'absent' and existing['addresses']:
        if version == 'v6':
            for address in existing['addresses']:
                if address['addr'] == addr and address['mask'] == mask:
                    command = get_remove_ip_config_commands(interface, addr,
                                                            mask, version)
                    commands.append(command)

        else:
            command = get_remove_ip_config_commands(interface, addr,
                                                    mask, version)
            commands.append(command)

    elif state == 'present':
        if not existing['addresses']:
            command = get_config_ip_commands(proposed, interface,
                                             existing, version)
            commands.append(command)
        else:
            prefix = "{0}/{1}".format(addr, mask)
            if prefix not in address_list:
                command = get_config_ip_commands(proposed, interface,
                                                 existing, version)
                commands.append(command)
            else:
                for address in existing['addresses']:
                    if (address['addr'] == addr and
                            int(address['mask']) != int(mask)):
                        command = get_config_ip_commands(proposed, interface,
                                                         existing, version)
                        commands.append(command)

    cmds = flatten_list(commands)
    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            execute_config_command(cmds, module)
            changed = True
            end_state, address_list = get_ip_interface(interface, version,
                                                       module)
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
