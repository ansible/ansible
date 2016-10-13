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
module: nxos_vxlan_vtep_vni
version_added: "2.2"
short_description: Creates a Virtual Network Identifier member (VNI)
description:
    - Creates a Virtual Network Identifier member (VNI) for an NVE
      overlay interface.
author: Gabriele Gerbino (@GGabriele)
extends_documentation_fragment: nxos
notes:
    - default, where supported, restores params default value.
options:
    interface:
        description:
            - Interface name for the VXLAN Network Virtualization Endpoint.
        required: true
    vni:
        description:
            - ID of the Virtual Network Identifier.
        required: true
    assoc_vrf:
        description:
            - This attribute is used to identify and separate processing VNIs
              that are associated with a VRF and used for routing. The VRF
              and VNI specified with this command must match the configuration
              of the VNI under the VRF.
        required: false
        choices: ['true','false']
        default: null
    ingress_replication:
        description:
            - Specifies mechanism for host reachability advertisement.
        required: false
        choices: ['bgp','static']
        default: null
    multicast_group:
        description:
            - The multicast group (range) of the VNI. Valid values are
              string and keyword 'default'.
        required: false
        default: null
    peer_list:
        description:
            - Set the ingress-replication static peer list. Valid values
              are an array, a space-separated string of ip addresses,
              or the keyword 'default'.
        required: false
        default: null
    suppress_arp:
        description:
            - Suppress arp under layer 2 VNI.
        required: false
        choices: ['true','false']
        default: null
    state:
        description:
            - Determines whether the config should be present or not
              on the device.
        required: false
        default: present
        choices: ['present','absent']
    include_defaults:
        description:
            - Specify to use or not the complete running configuration
              for module operations.
        required: false
        default: true
        choices: ['true','true']
    config:
        description:
            - Configuration string to be used for module operations. If not
              specified, the module will use the current running configuration.
        required: false
        default: null
    save:
        description:
            - Specify to save the running configuration after
              module operations.
        required: false
        default: false
        choices: ['true','false']
'''
EXAMPLES = '''
- nxos_vxlan_vtep_vni:
    interface: nve1
    vni: 6000
    ingress_replication: default
    username: "{{ un }}"
    password: "{{ pwd }}"
    host: "{{ inventory_hostname }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: verbose mode
    type: dict
    sample: {"ingress_replication": "default", "interface": "nve1", "vni": "6000"}
existing:
    description: k/v pairs of existing configuration
    returned: verbose mode
    type: dict
    sample: {}
end_state:
    description: k/v pairs of configuration after module execution
    returned: verbose mode
    type: dict
    sample: {"assoc_vrf": false, "ingress_replication": "", "interface": "nve1",
             "multicast_group": "", "peer_list": [],
             "suppress_arp": false, "vni": "6000"}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["interface nve1", "member vni 6000"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''

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

BOOL_PARAMS = ['suppress_arp']
PARAM_TO_COMMAND_KEYMAP = {
    'assoc_vrf': 'associate-vrf',
    'interface': 'interface',
    'vni': 'member vni',
    'ingress_replication': 'ingress-replication protocol',
    'multicast_group': 'mcast-group',
    'peer_list': 'peer-ip',
    'suppress_arp': 'suppress-arp'
}
PARAM_TO_DEFAULT_KEYMAP = {}
WARNINGS = []

def invoke(name, *args, **kwargs):
    func = globals().get(name)
    if func:
        return func(*args, **kwargs)


def get_value(arg, config, module):
    if arg in BOOL_PARAMS:
        REGEX = re.compile(r'\s+{0}\s*$'.format(PARAM_TO_COMMAND_KEYMAP[arg]), re.M)
        value = False
        try:
            if REGEX.search(config):
                value = True
        except TypeError:
            value = False
    else:
        REGEX = re.compile(r'(?:{0}\s)(?P<value>.*)$'.format(PARAM_TO_COMMAND_KEYMAP[arg]), re.M)
        value = ''
        if PARAM_TO_COMMAND_KEYMAP[arg] in config:
            value = REGEX.search(config).group('value')
    return value


def check_interface(module, netcfg):
    config = str(netcfg)

    REGEX = re.compile(r'(?:interface nve)(?P<value>.*)$', re.M)
    value = ''
    if 'interface nve' in config:
        value = 'nve{0}'.format(REGEX.search(config).group('value'))

    return value


def get_custom_value(arg, config, module):
    splitted_config = config.splitlines()
    if arg == 'assoc_vrf':
        value = False
        if 'associate-vrf' in config:
            value = True
    elif arg == 'peer_list':
        value = []
        REGEX = re.compile(r'(?:peer-ip\s)(?P<peer_value>.*)$', re.M)
        for line in splitted_config:
            peer_value = ''
            if PARAM_TO_COMMAND_KEYMAP[arg] in line:
                peer_value = REGEX.search(line).group('peer_value')
            if peer_value:
                value.append(peer_value)
    return value


def get_existing(module, args):
    existing = {}
    netcfg = get_config(module)

    custom = [
        'assoc_vrf',
        'peer_list'
        ]

    interface_exist = check_interface(module, netcfg)
    if interface_exist:
        parents = ['interface {0}'.format(interface_exist)]
        temp_config = netcfg.get_section(parents)

        if 'associate-vrf' in temp_config:
            parents.append('member vni {0} associate-vrf'.format(
                                                    module.params['vni']))
            config = netcfg.get_section(parents)
        elif 'member vni' in temp_config:
            parents.append('member vni {0}'.format(module.params['vni']))
            config = netcfg.get_section(parents)
        else:
            config = {}

        if config:
            for arg in args:
                if arg not in ['interface', 'vni']:
                    if arg in custom:
                        existing[arg] = get_custom_value(arg, config, module)
                    else:
                        existing[arg] = get_value(arg, config, module)
            existing['interface'] = interface_exist
            existing['vni'] = module.params['vni']

    return existing, interface_exist


def apply_key_map(key_map, table):
    new_dict = {}
    for key, value in table.items():
        new_key = key_map.get(key)
        if new_key:
            value = table.get(key)
            if value:
                new_dict[new_key] = value
            else:
                new_dict[new_key] = value
    return new_dict


def state_present(module, existing, proposed, candidate):
    commands = list()
    proposed_commands = apply_key_map(PARAM_TO_COMMAND_KEYMAP, proposed)
    existing_commands = apply_key_map(PARAM_TO_COMMAND_KEYMAP, existing)

    for key, value in proposed_commands.iteritems():
        if key == 'associate-vrf':
            command = 'member vni {0} {1}'.format(module.params['vni'], key)

            if value:
                commands.append(command)
            else:
                commands.append('no {0}'.format(command))

        elif key == 'peer-ip' and value != 'default':
            for peer in value:
                commands.append('{0} {1}'.format(key, peer))

        elif value is True:
            commands.append(key)

        elif value is False:
            commands.append('no {0}'.format(key))

        elif value == 'default':
            if existing_commands.get(key):
                existing_value = existing_commands.get(key)
                if key == 'peer-ip':
                    for peer in existing_value:
                        commands.append('no {0} {1}'.format(key, peer))
                else:
                    commands.append('no {0} {1}'.format(key, existing_value))
            else:
                if key.replace(' ', '_').replace('-', '_') in BOOL_PARAMS:
                    commands.append('no {0}'.format(key.lower()))
        else:
            command = '{0} {1}'.format(key, value.lower())
            commands.append(command)

    if commands:
        vni_command = 'member vni {0}'.format(module.params['vni'])
        ingress_replication_command = 'ingress-replication protocol static'
        interface_command = 'interface {0}'.format(module.params['interface'])

        if ingress_replication_command in commands:
            static_level_cmds = [cmd for cmd in commands if 'peer' in cmd]
            parents = [interface_command, vni_command, ingress_replication_command]
            candidate.add(static_level_cmds, parents=parents)
            commands = [cmd for cmd in commands if 'peer' not in cmd]

        if vni_command in commands:
            parents = [interface_command]
            commands.remove(vni_command)
            if module.params['assoc_vrf'] is None:
                parents.append(vni_command)
            candidate.add(commands, parents=parents)


def state_absent(module, existing, proposed, candidate):
    if existing['assoc_vrf']:
        commands = ['no member vni {0} associate-vrf'.format(
                                                module.params['vni'])]
    else:
        commands = ['no member vni {0}'.format(module.params['vni'])]
    parents = ['interface {0}'.format(module.params['interface'])]
    candidate.add(commands, parents=parents)


def main():
    argument_spec = dict(
            interface=dict(required=True, type='str'),
            vni=dict(required=True, type='str'),
            assoc_vrf=dict(required=False, type='bool'),
            multicast_group=dict(required=False, type='str'),
            peer_list=dict(required=False, type='list'),
            suppress_arp=dict(required=False, type='bool'),
            ingress_replication=dict(required=False, type='str',
                                     choices=['bgp', 'static', 'default']),
            state=dict(choices=['present', 'absent'], default='present',
                       required=False),
            include_defaults=dict(default=True),
            config=dict(),
            save=dict(type='bool', default=False)
    )
    module = get_network_module(argument_spec=argument_spec,
                                supports_check_mode=True)

    if module.params['assoc_vrf']:
        mutually_exclusive_params = ['multicast_group',
                                     'suppress_arp',
                                     'ingress_replication']
        for param in mutually_exclusive_params:
            if module.params[param]:
                module.fail_json(msg='assoc_vrf cannot be used with '
                                     '{0} param'.format(param))
    if module.params['peer_list']:
        if module.params['ingress_replication'] != 'static':
            module.fail_json(msg='ingress_replication=static is required '
                                 'when using peer_list param')
        else:
            peer_list = module.params['peer_list']
            if peer_list[0] == 'default':
                module.params['peer_list'] = 'default'
            else:
                stripped_peer_list = map(str.strip, peer_list)
                module.params['peer_list'] = stripped_peer_list

    state = module.params['state']
    args =  [
            'assoc_vrf',
            'interface',
            'vni',
            'ingress_replication',
            'multicast_group',
            'peer_list',
            'suppress_arp'
        ]

    existing, interface_exist = invoke('get_existing', module, args)
    end_state = existing
    proposed_args = dict((k, v) for k, v in module.params.iteritems()
                    if v is not None and k in args)

    proposed = {}
    for key, value in proposed_args.iteritems():
        if key != 'interface':
            if str(value).lower() == 'default':
                value = PARAM_TO_DEFAULT_KEYMAP.get(key)
                if value is None:
                    value = 'default'
            if existing.get(key) or (not existing.get(key) and value):
                proposed[key] = value

    result = {}
    if state == 'present' or (state == 'absent' and existing):
        if not interface_exist:
            WARNINGS.append("The proposed NVE interface does not exist. "
                            "Use nxos_interface to create it first.")
        elif interface_exist != module.params['interface']:
            module.fail_json(msg='Only 1 NVE interface is allowed on '
                                 'the switch.')
        elif (existing and state == 'absent' and
                existing['vni'] != module.params['vni']):
                module.fail_json(msg="ERROR: VNI delete failed: Could not find"
                                     " vni node for {0}".format(
                                     module.params['vni']),
                                     existing_vni=existing['vni'])
        else:
            candidate = CustomNetworkConfig(indent=3)
            invoke('state_%s' % state, module, existing, proposed, candidate)

            try:
                response = load_config(module, candidate)
                result.update(response)
            except ShellError:
                exc = get_exception()
                module.fail_json(msg=str(exc))
    else:
        result['updates'] = []

    result['connected'] = module.connected
    if module._verbosity > 0:
        end_state, interface_exist = invoke('get_existing', module, args)
        result['end_state'] = end_state
        result['existing'] = existing
        result['proposed'] = proposed_args

    if WARNINGS:
        result['warnings'] = WARNINGS

    module.exit_json(**result)


if __name__ == '__main__':
    main()
