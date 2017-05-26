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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: nxos_bgp_neighbor_af
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages BGP address-family's neighbors configuration.
description:
    - Manages BGP address-family's neighbors configurations on NX-OS switches.
author: Gabriele Gerbino (@GGabriele)
notes:
    - C(state=absent) removes the whole BGP address-family's
      neighbor configuration.
    - Default, when supported, removes properties
    - In order to default maximum-prefix configuration, only
      C(max_prefix_limit=default) is needed.
options:
    asn:
        description:
            - BGP autonomous system number. Valid values are String,
              Integer in ASPLAIN or ASDOT notation.
        required: true
    vrf:
        description:
            - Name of the VRF. The name 'default' is a valid VRF representing
              the global bgp.
        required: false
        default: default
    neighbor:
        description:
            - Neighbor Identifier. Valid values are string. Neighbors may use
              IPv4 or IPv6 notation, with or without prefix length.
        required: true
    afi:
        description:
            - Address Family Identifier.
        required: true
        choices: ['ipv4','ipv6', 'vpnv4', 'vpnv6', 'l2vpn']
    safi:
        description:
            - Sub Address Family Identifier.
        required: true
        choices: ['unicast','multicast', 'evpn']
    additional_paths_receive:
        description:
            - Valid values are enable for basic command enablement; disable
              for disabling the command at the neighbor af level
              (it adds the disable keyword to the basic command); and inherit
              to remove the command at this level (the command value is
              inherited from a higher BGP layer).
        required: false
        choices: ['enable','disable', 'inherit']
        default: null
    additional_paths_send:
        description:
            - Valid values are enable for basic command enablement; disable
              for disabling the command at the neighbor af level
              (it adds the disable keyword to the basic command); and inherit
              to remove the command at this level (the command value is
              inherited from a higher BGP layer).
        required: false
        choices: ['enable','disable', 'inherit']
        default: null
    advertise_map_exist:
        description:
            - Conditional route advertisement. This property requires two
              route maps, an advertise-map and an exist-map. Valid values are
              an array specifying both the advertise-map name and the exist-map
              name, or simply 'default' e.g. ['my_advertise_map',
              'my_exist_map']. This command is mutually exclusive with the
              advertise_map_non_exist property.
        required: false
        default: null
    advertise_map_non_exist:
        description:
            - Conditional route advertisement. This property requires two
              route maps, an advertise-map and an exist-map. Valid values are
              an array specifying both the advertise-map name and the
              non-exist-map name, or simply 'default' e.g.
              ['my_advertise_map', 'my_non_exist_map']. This command is mutually
              exclusive with the advertise_map_exist property.
        required: false
        default: null
    allowas_in:
        description:
            - Activate allowas-in property
        required: false
        default: null
    allowas_in_max:
        description:
            - Optional max-occurrences value for allowas_in. Valid values are
              an integer value or 'default'. Can be used independently or in
              conjunction with allowas_in.
        required: false
        default: null
    as_override:
        description:
            - Activate the as-override feature.
        required: false
        choices: ['true', 'false']
        default: null
    default_originate:
        description:
            - Activate the default-originate feature.
        required: false
        choices: ['true', 'false']
        default: null
    default_originate_route_map:
        description:
            - Optional route-map for the default_originate property. Can be
              used independently or in conjunction with C(default_originate).
              Valid values are a string defining a route-map name,
              or 'default'.
        required: false
        default: null
    filter_list_in:
        description:
            - Valid values are a string defining a filter-list name,
              or 'default'.
        required: false
        default: null
    filter_list_out:
        description:
            - Valid values are a string defining a filter-list name,
              or 'default'.
        required: false
        default: null
    max_prefix_limit:
        description:
            - maximum-prefix limit value. Valid values are an integer value
              or 'default'.
        required: false
        default: null
    max_prefix_interval:
        description:
            - Optional restart interval. Valid values are an integer.
              Requires max_prefix_limit.
        required: false
        default: null
    max_prefix_threshold:
        description:
            - Optional threshold percentage at which to generate a warning.
              Valid values are an integer value.
              Requires max_prefix_limit.
        required: false
        default: null
    max_prefix_warning:
        description:
            - Optional warning-only keyword. Requires max_prefix_limit.
        required: false
        choices: ['true','false']
        default: null
    next_hop_self:
        description:
            - Activate the next-hop-self feature.
        required: false
        choices: ['true','false']
        default: null
    next_hop_third_party:
        description:
            - Activate the next-hop-third-party feature.
        required: false
        choices: ['true','false']
        default: null
    prefix_list_in:
        description:
            - Valid values are a string defining a prefix-list name,
              or 'default'.
        required: false
        default: null
    prefix_list_out:
        description:
            - Valid values are a string defining a prefix-list name,
              or 'default'.
        required: false
        default: null
    route_map_in:
        description:
            - Valid values are a string defining a route-map name,
              or 'default'.
        required: false
        default: null
    route_map_out:
        description:
            - Valid values are a string defining a route-map name,
              or 'default'.
        required: false
        default: null
    route_reflector_client:
        description:
            - Router reflector client.
        required: false
        choices: ['true','false']
        default: null
    send_community:
        description:
            - send-community attribute.
        required: false
        choices: ['none', 'both', 'extended', 'standard', 'default']
        default: null
    soft_reconfiguration_in:
        description:
            - Valid values are 'enable' for basic command enablement; 'always'
              to add the always keyword to the basic command; and 'inherit' to
              remove the command at this level (the command value is inherited
              from a higher BGP layer).
        required: false
        choices: ['enable','always','inherit']
        default: null
    soo:
        description:
            - Site-of-origin. Valid values are a string defining a VPN
              extcommunity or 'default'.
        required: false
        default: null
    suppress_inactive:
        description:
            - suppress-inactive feature.
        required: false
        choices: ['true','false','default']
        default: null
    unsuppress_map:
        description:
            - unsuppress-map. Valid values are a string defining a route-map
              name or 'default'.
        required: false
        default: null
    weight:
        description:
            - Weight value. Valid values are an integer value or 'default'.
        required: false
        default: null
    state:
        description:
            - Determines whether the config should be present or not
              on the device.
        required: false
        default: present
        choices: ['present','absent']
'''
EXAMPLES = '''
- name: configure RR client
  nxos_bgp_neighbor_af:
    asn: 65535
    neighbor: '3.3.3.3'
    afi: ipv4
    safi: unicast
    route_reflector_client: true
    state: present
    username: "{{ un }}"
    password: "{{ pwd }}"
    host: "{{ inventory_hostname }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: verbose mode
    type: dict
    sample: {"afi": "ipv4", "asn": "65535",
            "neighbor": "3.3.3.3", "route_reflector_client": true,
            "safi": "unicast", "vrf": "default"}
existing:
    description: k/v pairs of existing configuration
    returned: verbose mode
    type: dict
    sample: {}
end_state:
    description: k/v pairs of configuration after module execution
    returned: verbose mode
    type: dict
    sample: {"additional_paths_receive": "inherit",
            "additional_paths_send": "inherit",
            "advertise_map_exist": [], "advertise_map_non_exist": [],
            "afi": "ipv4", "allowas_in": false,
            "allowas_in_max": "", "as_override": false,
            "asn": "65535", "default_originate": false,
            "default_originate_route_map": "", "filter_list_in": "",
            "filter_list_out": "", "max_prefix_interval": "",
            "max_prefix_limit": "", "max_prefix_threshold": "",
            "max_prefix_warning": "", "neighbor": "3.3.3.3",
            "next_hop_self": false, "next_hop_third_party": true,
            "prefix_list_in": "", "prefix_list_out": "",
            "route_map_in": "", "route_map_out": "",
            "route_reflector_client": true, "safi": "unicast",
            "send_community": "",
            "soft_reconfiguration_in": "inherit", "soo": "",
            "suppress_inactive": false, "unsuppress_map": "",
            "vrf": "default", "weight": ""}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["router bgp 65535", "neighbor 3.3.3.3",
            "address-family ipv4 unicast", "route-reflector-client"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''


import re
from ansible.module_utils.nxos import get_config, load_config, run_commands
from ansible.module_utils.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.netcfg import CustomNetworkConfig

WARNINGS = []
BOOL_PARAMS = [
    'allowas_in',
    'as_override',
    'default_originate',
    'next_hop_self',
    'next_hop_third_party',
    'route_reflector_client',
    'suppress_inactive'
]
PARAM_TO_COMMAND_KEYMAP = {
    'afi': 'address-family',
    'asn': 'router bgp',
    'neighbor': 'neighbor',
    'additional_paths_receive': 'capability additional-paths receive',
    'additional_paths_send': 'capability additional-paths send',
    'advertise_map_exist': 'advertise-map exist',
    'advertise_map_non_exist': 'advertise-map non-exist',
    'allowas_in': 'allowas-in',
    'allowas_in_max': 'allowas-in max',
    'as_override': 'as-override',
    'default_originate': 'default-originate',
    'default_originate_route_map': 'default-originate route-map',
    'filter_list_in': 'filter-list in',
    'filter_list_out': 'filter-list out',
    'max_prefix_limit': 'maximum-prefix',
    'max_prefix_interval': 'maximum-prefix options',
    'max_prefix_threshold': 'maximum-prefix options',
    'max_prefix_warning': 'maximum-prefix options',
    'next_hop_self': 'next-hop-self',
    'next_hop_third_party': 'next-hop-third-party',
    'prefix_list_in': 'prefix-list in',
    'prefix_list_out': 'prefix-list out',
    'route_map_in': 'route-map in',
    'route_map_out': 'route-map out',
    'route_reflector_client': 'route-reflector-client',
    'safi': 'address-family',
    'send_community': 'send-community',
    'soft_reconfiguration_in': 'soft-reconfiguration inbound',
    'soo': 'soo',
    'suppress_inactive': 'suppress-inactive',
    'unsuppress_map': 'unsuppress-map',
    'weight': 'weight',
    'vrf': 'vrf'
}
PARAM_TO_DEFAULT_KEYMAP = {}


def invoke(name, *args, **kwargs):
    func = globals().get(name)
    if func:
        return func(*args, **kwargs)


def get_value(arg, config, module):
    if arg in BOOL_PARAMS:
        REGEX = re.compile(r'\s+{0}\s*'.format(PARAM_TO_COMMAND_KEYMAP[arg]), re.M)
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


def in_out_param(arg, config, module):
    value = ''
    for line in config:
        if PARAM_TO_COMMAND_KEYMAP[arg].split()[0] in line:
            splitted_line = line.split()
            if splitted_line[-1] == PARAM_TO_COMMAND_KEYMAP[arg].split()[1]:
                value = splitted_line[1]
    return value


def get_custom_value(arg, config, module):
    splitted_config = config.splitlines()
    value = ''

    if (arg.startswith('filter_list') or arg.startswith('prefix_list') or
        arg.startswith('route_map')):
        value = in_out_param(arg, splitted_config, module)
    elif arg == 'send_community':
        for line in splitted_config:
            if PARAM_TO_COMMAND_KEYMAP[arg] in line:
                splitted_line = line.split()
                if len(splitted_line) == 1:
                    value = 'none'
                else:
                    value = splitted_line[1]
    elif arg == 'additional_paths_receive':
        value = 'inherit'
        for line in splitted_config:
            if PARAM_TO_COMMAND_KEYMAP[arg] in line:
                if 'disable' in line:
                    value = 'disable'
                else:
                    value = 'enable'
    elif arg == 'additional_paths_send':
        value = 'inherit'
        for line in splitted_config:
            if PARAM_TO_COMMAND_KEYMAP[arg] in line:
                if 'disable' in line:
                    value = 'disable'
                else:
                    value = 'enable'
    elif arg == 'advertise_map_exist':
        value = []
        for line in splitted_config:
            if 'advertise-map' in line and 'exist-map' in line:
                splitted_line = line.split()
                value = [splitted_line[1], splitted_line[3]]
    elif arg == 'advertise_map_non_exist':
        value = []
        for line in splitted_config:
            if 'advertise-map' in line and 'non-exist-map' in line:
                splitted_line = line.split()
                value = [splitted_line[1], splitted_line[3]]
    elif arg == 'allowas_in_max':
        for line in splitted_config:
            if 'allowas-in' in line:
                splitted_line = line.split()
                if len(splitted_line) == 2:
                    value = splitted_line[-1]
    elif arg.startswith('max_prefix'):
        for line in splitted_config:
            if 'maximum-prefix' in line:
                splitted_line = line.split()
                if arg == 'max_prefix_limit':
                    value = splitted_line[1]
                elif arg == 'max_prefix_interval' and 'restart' in line:
                    value = splitted_line[-1]
                elif arg == 'max_prefix_threshold' and len(splitted_line) > 2:
                    try:
                        int(splitted_line[2])
                        value = splitted_line[2]
                    except ValueError:
                        value = ''
                elif arg == 'max_prefix_warning':
                    if 'warning-only' in line:
                        value = True
                    else:
                        value = False
    elif arg == 'soft_reconfiguration_in':
        value = 'inherit'
        for line in splitted_config:
            if PARAM_TO_COMMAND_KEYMAP[arg] in line:
                if 'always' in line:
                    value = 'always'
                else:
                    value = 'enable'
    elif arg == 'next_hop_third_party':
        PRESENT_REGEX = re.compile(r'\s+{0}\s*'.format(PARAM_TO_COMMAND_KEYMAP[arg]), re.M)
        ABSENT_REGEX = re.compile(r'\s+no\s+{0}\s*'.format(PARAM_TO_COMMAND_KEYMAP[arg]), re.M)
        value = False
        try:
            if ABSENT_REGEX.search(config):
                value = False
            elif PRESENT_REGEX.search(config):
                value = True
        except TypeError:
            value = False

    return value


def get_existing(module, args):
    existing = {}
    netcfg = CustomNetworkConfig(indent=2, contents=get_config(module))

    custom = [
        'allowas_in_max',
        'send_community',
        'additional_paths_send',
        'additional_paths_receive',
        'advertise_map_exist',
        'advertise_map_non_exist',
        'filter_list_in',
        'filter_list_out',
        'max_prefix_limit',
        'max_prefix_interval',
        'max_prefix_threshold',
        'max_prefix_warning',
        'next_hop_third_party',
        'prefix_list_in',
        'prefix_list_out',
        'route_map_in',
        'route_map_out',
        'soft_reconfiguration_in'
    ]
    try:
        asn_regex = '.*router\sbgp\s(?P<existing_asn>\d+).*'
        match_asn = re.match(asn_regex, str(netcfg), re.DOTALL)
        existing_asn_group = match_asn.groupdict()
        existing_asn = existing_asn_group['existing_asn']
    except AttributeError:
        existing_asn = ''

    if existing_asn:
        parents = ["router bgp {0}".format(existing_asn)]
        if module.params['vrf'] != 'default':
            parents.append('vrf {0}'.format(module.params['vrf']))

        parents.append('neighbor {0}'.format(module.params['neighbor']))
        parents.append('address-family {0} {1}'.format(
            module.params['afi'], module.params['safi']))
        config = netcfg.get_section(parents)

        if config:
            for arg in args:
                if arg not in ['asn', 'vrf', 'neighbor', 'afi', 'safi']:
                    if arg in custom:
                        existing[arg] = get_custom_value(arg, config, module)
                    else:
                        existing[arg] = get_value(arg, config, module)

            existing['asn'] = existing_asn
            existing['neighbor'] = module.params['neighbor']
            existing['vrf'] = module.params['vrf']
            existing['afi'] = module.params['afi']
            existing['safi'] = module.params['safi']
    else:
        WARNINGS.append("The BGP process didn't exist but the task"
                        " just created it.")

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


def get_address_family_command(key, value, module):
    command = "address-family {0} {1}".format(
        module.params['afi'], module.params['safi'])
    return command


def get_capability_additional_paths_receive_command(key, value, module):
    command = ''
    if value == 'enable':
        command = key
    elif value == 'disable':
        command = '{0} {1}'.format(key, value)
    return command


def get_capability_additional_paths_send_command(key, value, module):
    command = ''
    if value == 'enable':
        command = key
    elif value == 'disable':
        command = '{0} {1}'.format(key, value)
    return command


def get_advertise_map_exist_command(key, value, module):
    command = 'advertise-map {0} exist-map {1}'.format(
        value[0], value[1])
    return command


def get_advertise_map_non_exist_command(key, value, module):
    command = 'advertise-map {0} non-exist-map {1}'.format(
        value[0], value[1])
    return command


def get_allowas_in_max_command(key, value, module):
    command = 'allowas-in {0}'.format(value)
    return command


def get_filter_list_in_command(key, value, module):
    command = 'filter-list {0} in'.format(value)
    return command


def get_filter_list_out_command(key, value, module):
    command = 'filter-list {0} out'.format(value)
    return command


def get_prefix_list_in_command(key, value, module):
    command = 'prefix-list {0} in'.format(value)
    return command


def get_prefix_list_out_command(key, value, module):
    command = 'prefix-list {0} out'.format(value)
    return command


def get_route_map_in_command(key, value, module):
    command = 'route-map {0} in'.format(value)
    return command


def get_route_map_out_command(key, value, module):
    command = 'route-map {0} out'.format(value)
    return command


def get_maximum_prefix_command(key, value, module):
    return get_maximum_prefix_options_command(key, value, module)


def get_maximum_prefix_options_command(key, value, module):
    command = 'maximum-prefix {0}'.format(module.params['max_prefix_limit'])
    if module.params['max_prefix_threshold']:
        command += ' {0}'.format(module.params['max_prefix_threshold'])
    if module.params['max_prefix_interval']:
        command += ' restart {0}'.format(module.params['max_prefix_interval'])
    elif module.params['max_prefix_warning']:
        command += ' warning-only'
    return command


def get_soft_reconfiguration_inbound_command(key, value, module):
    command = ''
    if value == 'enable':
        command = key
    elif value == 'always':
        command = '{0} {1}'.format(key, value)
    return command


def get_default_command(key, value, existing_commands):
    command = ''
    if key == 'send-community' and existing_commands.get(key) == 'none':
        command = 'no {0}'.format(key)

    elif existing_commands.get(key):
        existing_value = existing_commands.get(key)
        if value == 'inherit':
            if existing_value != 'inherit':
                command = 'no {0}'.format(key)
        else:
            if key == 'advertise-map exist':
                command = 'no advertise-map {0} exist-map {1}'.format(
                    existing_value[0], existing_value[1])
            elif key == 'advertise-map non-exist':
                command = 'no advertise-map {0} non-exist-map {1}'.format(
                    existing_value[0], existing_value[1])
            elif key == 'filter-list in':
                command = 'no filter-list {0} in'.format(existing_value)
            elif key == 'filter-list out':
                command = 'no filter-list {0} out'.format(existing_value)
            elif key == 'prefix-list in':
                command = 'no prefix-list {0} in'.format(existing_value)
            elif key == 'prefix-list out':
                command = 'no prefix-list {0} out'.format(existing_value)
            elif key == 'route-map in':
                command = 'no route-map {0} in'.format(existing_value)
            elif key == 'route-map out':
                command = 'no route-map {0} out'.format(existing_value)
            elif key.startswith('maximum-prefix'):
                command = 'no maximum-prefix {0}'.format(
                    existing_commands.get('maximum-prefix'))
            elif key == 'allowas-in max':
                command = ['no allowas-in {0}'.format(existing_value)]
                command.append('allowas-in')
            else:
                command = 'no {0} {1}'.format(key, existing_value)
    else:
        if key.replace(' ', '_').replace('-', '_') in BOOL_PARAMS:
            command = 'no {0}'.format(key)
    return command


def fix_proposed(module, proposed):
    allowas_in = proposed.get('allowas_in')
    allowas_in_max = proposed.get('allowas_in_max')

    if allowas_in is False and allowas_in_max:
        proposed.pop('allowas_in_max')
    elif allowas_in and allowas_in_max:
        proposed.pop('allowas_in')

    return proposed


def state_present(module, existing, proposed, candidate):
    commands = list()

    proposed = fix_proposed(module, proposed)

    proposed_commands = apply_key_map(PARAM_TO_COMMAND_KEYMAP, proposed)
    existing_commands = apply_key_map(PARAM_TO_COMMAND_KEYMAP, existing)

    custom = [
        'address-family',
        'capability additional-paths receive',
        'capability additional-paths send',
        'advertise-map exist',
        'advertise-map non-exist',
        'allowas-in max',
        'filter-list in',
        'filter-list out',
        'maximum-prefix',
        'maximum-prefix options',
        'prefix-list in',
        'prefix-list out',
        'route-map in',
        'route-map out',
        'soft-reconfiguration inbound'
    ]
    for key, value in proposed_commands.items():
        if key == 'send-community' and value == 'none':
            commands.append('{0}'.format(key))

        elif value is True and key != 'maximum-prefix options':
            commands.append(key)

        elif value is False and key != 'maximum-prefix options':
            commands.append('no {0}'.format(key))

        elif value == 'default' or value == 'inherit':
            command = get_default_command(key, value, existing_commands)

            if isinstance(command, str):
                if command and command not in commands:
                    commands.append(command)
            elif isinstance(command, list):
                for cmd in command:
                    if cmd not in commands:
                        commands.append(cmd)

        elif key in custom:
            fixed_key = key.replace(' ', '_').replace('-', '_')
            command = invoke('get_%s_command' % fixed_key, key, value, module)
            if command and command not in commands:
                commands.append(command)
        else:
            command = '{0} {1}'.format(key, value)
            commands.append(command)

    if commands:
        parents = ["router bgp {0}".format(module.params['asn'])]
        if module.params['vrf'] != 'default':
            parents.append('vrf {0}'.format(module.params['vrf']))

        parents.append('neighbor {0}'.format(module.params['neighbor']))

        if len(commands) == 1:
            candidate.add(commands, parents=parents)
        elif len(commands) > 1:
            af_command = 'address-family {0} {1}'.format(
                module.params['afi'], module.params['safi'])
            if af_command in commands:
                commands.remove(af_command)
                parents.append('address-family {0} {1}'.format(
                    module.params['afi'], module.params['safi']))
                candidate.add(commands, parents=parents)


def state_absent(module, existing, proposed, candidate):
    commands = []
    parents = ["router bgp {0}".format(module.params['asn'])]
    if module.params['vrf'] != 'default':
        parents.append('vrf {0}'.format(module.params['vrf']))

    parents.append('neighbor {0}'.format(module.params['neighbor']))
    commands.append('no address-family {0} {1}'.format(
        module.params['afi'], module.params['safi']))
    candidate.add(commands, parents=parents)


def main():
    argument_spec = dict(
        asn=dict(required=True, type='str'),
        vrf=dict(required=False, type='str', default='default'),
        neighbor=dict(required=True, type='str'),
        afi=dict(required=True, type='str'),
        safi=dict(required=True, type='str'),
        additional_paths_receive=dict(required=False, type='str',
                                choices=['enable', 'disable', 'inherit']),
        additional_paths_send=dict(required=False, type='str',
                                choices=['enable', 'disable', 'inherit']),
        advertise_map_exist=dict(required=False, type='list'),
        advertise_map_non_exist=dict(required=False, type='list'),
        allowas_in=dict(required=False, type='bool'),
        allowas_in_max=dict(required=False, type='str'),
        as_override=dict(required=False, type='bool'),
        default_originate=dict(required=False, type='bool'),
        default_originate_route_map=dict(required=False, type='str'),
        filter_list_in=dict(required=False, type='str'),
        filter_list_out=dict(required=False, type='str'),
        max_prefix_limit=dict(required=False, type='str'),
        max_prefix_interval=dict(required=False, type='str'),
        max_prefix_threshold=dict(required=False, type='str'),
        max_prefix_warning=dict(required=False, type='bool'),
        next_hop_self=dict(required=False, type='bool'),
        next_hop_third_party=dict(required=False, type='bool'),
        prefix_list_in=dict(required=False, type='str'),
        prefix_list_out=dict(required=False, type='str'),
        route_map_in=dict(required=False, type='str'),
        route_map_out=dict(required=False, type='str'),
        route_reflector_client=dict(required=False, type='bool'),
        send_community=dict(required=False, choices=['none',
                                                         'both',
                                                         'extended',
                                                         'standard',
                                                         'default']),
        soft_reconfiguration_in=dict(required=False, type='str',
                                choices=['enable', 'always', 'inherit']),
        soo=dict(required=False, type='str'),
        suppress_inactive=dict(required=False, type='bool'),
        unsuppress_map=dict(required=False, type='str'),
        weight=dict(required=False, type='str'),
        state=dict(choices=['present', 'absent'], default='present',
                       required=False),
        include_defaults=dict(default=True),
        config=dict(),
        save=dict(type='bool', default=False)
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                                mutually_exclusive=[['advertise_map_exist',
                                             'advertise_map_non_exist']],
                                supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)


    state = module.params['state']
    if ((module.params['max_prefix_interval'] or
        module.params['max_prefix_warning'] or
        module.params['max_prefix_threshold']) and
        not module.params['max_prefix_limit']):
        module.fail_json(msg='max_prefix_limit is required when using '
                             'max_prefix_warning, max_prefix_limit or '
                             'max_prefix_threshold.')
    if module.params['vrf'] == 'default' and module.params['soo']:
        module.fail_json(msg='SOO is only allowed in non-default VRF')

    args =  [
        'afi',
        'asn',
        'neighbor',
        'additional_paths_receive',
        'additional_paths_send',
        'advertise_map_exist',
        'advertise_map_non_exist',
        'allowas_in',
        'allowas_in_max',
        'as_override',
        'default_originate',
        'default_originate_route_map',
        'filter_list_in',
        'filter_list_out',
        'max_prefix_limit',
        'max_prefix_interval',
        'max_prefix_threshold',
        'max_prefix_warning',
        'next_hop_self',
        'next_hop_third_party',
        'prefix_list_in',
        'prefix_list_out',
        'route_map_in',
        'route_map_out',
        'soft_reconfiguration_in',
        'soo',
        'suppress_inactive',
        'unsuppress_map',
        'weight',
        'route_reflector_client',
        'safi',
        'send_community',
        'vrf'
    ]

    existing = invoke('get_existing', module, args)
    if existing.get('asn'):
        if (existing.get('asn') != module.params['asn'] and
            state == 'present'):
            module.fail_json(msg='Another BGP ASN already exists.',
                             proposed_asn=module.params['asn'],
                             existing_asn=existing.get('asn'))

    if module.params['advertise_map_exist'] == ['default']:
        module.params['advertise_map_exist'] = 'default'
    if module.params['advertise_map_non_exist'] == ['default']:
        module.params['advertise_map_non_exist'] = 'default'

    end_state = existing
    proposed_args = dict((k, v) for k, v in module.params.items()
                    if v is not None and k in args)

    proposed = {}
    for key, value in proposed_args.items():
        if key not in ['asn', 'vrf', 'neighbor']:
            if not isinstance(value, list):
                if str(value).lower() == 'true':
                    value = True
                elif str(value).lower() == 'false':
                    value = False
                elif str(value).lower() == 'default':
                    value = PARAM_TO_DEFAULT_KEYMAP.get(key)
                    if value is None:
                        if key in BOOL_PARAMS:
                            value = False
                        else:
                            value = 'default'
            if existing.get(key) or (not existing.get(key) and value):
                proposed[key] = value

    result = {}
    if state == 'present' or (state == 'absent' and existing):
        candidate = CustomNetworkConfig(indent=3)
        invoke('state_%s' % state, module, existing, proposed, candidate)
        response = load_config(module, candidate)
        result.update(response)

    else:
        result['updates'] = []

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

