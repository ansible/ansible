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
module: nxos_vrf_af
version_added: "2.2"
short_description: Manages VRF AF.
description:
    - Manages VRF AF
author: Gabriele Gerbino (@GGabriele)
extends_documentation_fragment: nxos
notes:
    - Default, where supported, restores params default value.
options:
    vrf:
        description:
            - Name of the VRF.
        required: true
    afi:
        description:
            - Address-Family Identifier (AFI).
        required: true
        choices: ['ipv4', 'ipv6']
        default: null
    safi:
        description:
            - Sub Address-Family Identifier (SAFI).
        required: true
        choices: ['unicast', 'multicast']
        default: null
    route_target_both_auto_evpn:
        description:
            - Enable/Disable the EVPN route-target 'auto' setting for both
              import and export target communities.
        required: false
        choices: ['true', 'false']
        default: null
    state:
        description:
            - Determines whether the config should be present or
              not on the device.
        required: false
        default: present
        choices: ['present','absent']
'''
EXAMPLES = '''
- nxos_vrf_af:
    interface: nve1
    vni: 6000
    ingress_replication: true
    username: "{{ un }}"
    password: "{{ pwd }}"
    host: "{{ inventory_hostname }}"
'''
RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: verbose mode
    type: dict
    sample: {"afi": "ipv4", "route_target_both_auto_evpn": true,
            "safi": "unicast", "vrf": "test"}
existing:
    description: k/v pairs of existing configuration
    returned: verbose mode
    type: dict
    sample: {"afi": "ipv4", "route_target_both_auto_evpn": false,
            "safi": "unicast", "vrf": "test"}
end_state:
    description: k/v pairs of configuration after module execution
    returned: verbose mode
    type: dict
    sample: {"afi": "ipv4", "route_target_both_auto_evpn": true,
            "safi": "unicast", "vrf": "test"}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["vrf context test", "address-family ipv4 unicast",
            "route-target both auto evpn"]
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

BOOL_PARAMS = ['route_target_both_auto_evpn']
PARAM_TO_COMMAND_KEYMAP = {
    'route_target_both_auto_evpn': 'route-target both auto evpn',
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


def get_existing(module, args):
    existing = {}
    netcfg = get_config(module)

    parents = ['vrf context {0}'.format(module.params['vrf'])]
    parents.append('address-family {0} {1}'.format(module.params['afi'],
                                            module.params['safi']))
    config = netcfg.get_section(parents)
    if config:
        splitted_config = config.splitlines()
        vrf_index = False
        for index in range(0, len(splitted_config) - 1):
            if 'vrf' in splitted_config[index].strip():
                    vrf_index = index
                    break
        if vrf_index:
            config = '\n'.join(splitted_config[0:vrf_index])

        for arg in args:
            if arg not in ['afi', 'safi', 'vrf']:
                existing[arg] = get_value(arg, config, module)

        existing['afi'] = module.params['afi']
        existing['safi'] = module.params['safi']
        existing['vrf'] = module.params['vrf']

    return existing


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
        if value is True:
            commands.append(key)

        elif value is False:
            commands.append('no {0}'.format(key))

        elif value == 'default':
            if existing_commands.get(key):
                existing_value = existing_commands.get(key)
                commands.append('no {0} {1}'.format(key, existing_value))
        else:
            command = '{0} {1}'.format(key, value.lower())
            commands.append(command)

    if commands:
        parents = ['vrf context {0}'.format(module.params['vrf'])]
        parents.append('address-family {0} {1}'.format(module.params['afi'],
                                                module.params['safi']))
        candidate.add(commands, parents=parents)


def state_absent(module, existing, proposed, candidate):
    commands = []
    parents = ['vrf context {0}'.format(module.params['vrf'])]
    commands.append('no address-family {0} {1}'.format(module.params['afi'],
                                                module.params['safi']))
    candidate.add(commands, parents=parents)


def main():
    argument_spec = dict(
            vrf=dict(required=True, type='str'),
            safi=dict(required=True, type='str', choices=['unicast','multicast']),
            afi=dict(required=True, type='str', choices=['ipv4','ipv6']),
            route_target_both_auto_evpn=dict(required=False, type='bool'),
            m_facts=dict(required=False, default=False, type='bool'),
            state=dict(choices=['present', 'absent'], default='present',
                       required=False),
            include_defaults=dict(default=False),
            config=dict(),
            save=dict(type='bool', default=False)
    )
    module = get_network_module(argument_spec=argument_spec,
                                supports_check_mode=True)

    state = module.params['state']

    args =  [
            'vrf',
            'safi',
            'afi',
            'route_target_both_auto_evpn'
        ]

    existing = invoke('get_existing', module, args)
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
        end_state = invoke('get_existing', module, args)
        result['end_state'] = end_state
        result['existing'] = existing
        result['proposed'] = proposed_args

    if WARNINGS:
        result['warnings'] = WARNINGS

    module.exit_json(**result)


if __name__ == '__main__':
    main()
