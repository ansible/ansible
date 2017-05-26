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
module: nxos_bgp_neighbor
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages BGP neighbors configurations.
description:
    - Manages BGP neighbors configurations on NX-OS switches.
author: Gabriele Gerbino (@GGabriele)
notes:
    - C(state=absent) removes the whole BGP neighbor configuration.
    - Default, where supported, restores params default value.
options:
    asn:
        description:
            - BGP autonomous system number. Valid values are string,
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
    description:
        description:
            - Description of the neighbor.
        required: false
        default: null
    connected_check:
        description:
            - Configure whether or not to check for directly connected peer.
        required: false
        choices: ['true', 'false']
        default: null
    capability_negotiation:
        description:
            - Configure whether or not to negotiate capability with
              this neighbor.
        required: false
        choices: ['true', 'false']
        default: null
    dynamic_capability:
        description:
            - Configure whether or not to enable dynamic capability.
        required: false
        choices: ['true', 'false']
        default: null
    ebgp_multihop:
        description:
            - Specify multihop TTL for a remote peer. Valid values are
              integers between 2 and 255, or keyword 'default' to disable
              this property.
        required: false
        default: null
    local_as:
        description:
            - Specify the local-as number for the eBGP neighbor.
              Valid values are String or Integer in ASPLAIN or ASDOT notation,
              or 'default', which means not to configure it.
        required: false
        default: null
    log_neighbor_changes:
        description:
            - Specify whether or not to enable log messages for neighbor
              up/down event.
        required: false
        choices: ['enable', 'disable', 'inherit']
        default: null
    low_memory_exempt:
        description:
            - Specify whether or not to shut down this neighbor under
              memory pressure.
        required: false
        choices: ['true', 'false']
        default: null
    maximum_peers:
        description:
            - Specify Maximum number of peers for this neighbor prefix
              Valid values are between 1 and 1000, or 'default', which does
              not impose the limit.
        required: false
        default: null
    pwd:
        description:
            - Specify the password for neighbor. Valid value is string.
        required: false
        default: null
    pwd_type:
        description:
            - Specify the encryption type the password will use. Valid values
              are '3des' or 'cisco_type_7' encryption.
        required: false
        choices: ['3des', 'cisco_type_7']
        default: null
    remote_as:
        description:
            - Specify Autonomous System Number of the neighbor.
              Valid values are String or Integer in ASPLAIN or ASDOT notation,
              or 'default', which means not to configure it.
        required: false
        default: null
    remove_private_as:
        description:
            - Specify the config to remove private AS number from outbound
              updates. Valid values are 'enable' to enable this config,
              'disable' to disable this config, 'all' to remove all
              private AS number, or 'replace-as', to replace the private
              AS number.
        required: false
        choices: ['enable', 'disable', 'all', 'replace-as']
        default: null
    shutdown:
        description:
            - Configure to administratively shutdown this neighbor.
        required: false
        choices: ['true','false']
        default: null
    suppress_4_byte_as:
        description:
            - Configure to suppress 4-byte AS Capability.
        required: false
        choices: ['true','false']
        default: null
    timers_keepalive:
        description:
            - Specify keepalive timer value. Valid values are integers
              between 0 and 3600 in terms of seconds, or 'default',
              which is 60.
        required: false
        default: null
    timers_holdtime:
        description:
            - Specify holdtime timer value. Valid values are integers between
              0 and 3600 in terms of seconds, or 'default', which is 180.
        required: false
        default: null
    transport_passive_only:
        description:
            - Specify whether or not to only allow passive connection setup.
              Valid values are 'true', 'false', and 'default', which defaults
              to 'false'. This property can only be configured when the
              neighbor is in 'ip' address format without prefix length.
              This property and the transport_passive_mode property are
              mutually exclusive.
        required: false
        choices: ['true','false']
        default: null
    update_source:
        description:
            - Specify source interface of BGP session and updates.
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
# create a new neighbor
- nxos_bgp_neighbor:
    asn: 65535
    neighbor: 3.3.3.3
    local_as: 20
    remote_as: 30
    description: "just a description"
    update_source: Ethernet1/3
    shutdown: default
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
    sample: {"asn": "65535", "description": "just a description",
            "local_as": "20", "neighbor": "3.3.3.3",
            "remote_as": "30", "shutdown": "default",
            "update_source": "Ethernet1/3", "vrf": "default"}
existing:
    description: k/v pairs of existing BGP neighbor configuration
    returned: verbose mode
    type: dict
    sample: {}
end_state:
    description: k/v pairs of BGP neighbor configuration after module execution
    returned: verbose mode
    type: dict
    sample: {"asn": "65535", "capability_negotiation": false,
            "connected_check": false, "description": "just a description",
            "dynamic_capability": true, "ebgp_multihop": "",
            "local_as": "20", "log_neighbor_changes": "",
            "low_memory_exempt": false, "maximum_peers": "",
            "neighbor": "3.3.3.3", "pwd": "",
            "pwd_type": "", "remote_as": "30",
            "remove_private_as": "disable", "shutdown": false,
            "suppress_4_byte_as": false, "timers_holdtime": "180",
            "timers_keepalive": "60", "transport_passive_only": false,
            "update_source": "Ethernet1/3", "vrf": "default"}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["router bgp 65535", "neighbor 3.3.3.3",
            "remote-as 30", "update-source Ethernet1/3",
            "description just a description", "local-as 20"]
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
    'capability_negotiation',
    'shutdown',
    'connected_check',
    'dynamic_capability',
    'low_memory_exempt',
    'suppress_4_byte_as',
    'transport_passive_only'
]
PARAM_TO_COMMAND_KEYMAP = {
    'asn': 'router bgp',
    'capability_negotiation': 'dont-capability-negotiate',
    'connected_check': 'disable-connected-check',
    'description': 'description',
    'dynamic_capability': 'dynamic-capability',
    'ebgp_multihop': 'ebgp-multihop',
    'local_as': 'local-as',
    'log_neighbor_changes': 'log-neighbor-changes',
    'low_memory_exempt': 'low-memory exempt',
    'maximum_peers': 'maximum-peers',
    'neighbor': 'neighbor',
    'pwd': 'password',
    'pwd_type': 'password-type',
    'remote_as': 'remote-as',
    'remove_private_as': 'remove-private-as',
    'shutdown': 'shutdown',
    'suppress_4_byte_as': 'capability suppress 4-byte-as',
    'timers_keepalive': 'timers-keepalive',
    'timers_holdtime': 'timers-holdtime',
    'transport_passive_only': 'transport connection-mode passive',
    'update_source': 'update-source',
    'vrf': 'vrf'
}
PARAM_TO_DEFAULT_KEYMAP = {
    'shutdown': False,
    'dynamic_capability': True,
    'timers_keepalive': 60,
    'timers_holdtime': 180
}

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


def get_custom_value(arg, config, module):
    value = ''
    splitted_config = config.splitlines()

    if arg == 'log_neighbor_changes':
        for line in splitted_config:
            if 'log-neighbor-changes' in line:
                if 'disable' in line:
                    value = 'disable'
                else:
                    value = 'enable'

    elif arg == 'pwd':
        for line in splitted_config:
            if 'password' in line:
                splitted_line = line.split()
                value = splitted_line[2]

    elif arg == 'pwd_type':
        for line in splitted_config:
            if 'password' in line:
                splitted_line = line.split()
                value = splitted_line[1]

    elif arg == 'remove_private_as':
        value = 'disable'
        for line in splitted_config:
            if 'remove-private-as' in line:
                splitted_line = line.split()
                if len(splitted_line) == 1:
                    value = 'enable'
                elif len(splitted_line) == 2:
                    value = splitted_line[1]

    elif arg == 'timers_keepalive':
        REGEX = re.compile(r'(?:timers\s)(?P<value>.*)$', re.M)
        value = ''
        if 'timers' in config:
            parsed = REGEX.search(config).group('value').split()
            value = parsed[0]

    elif arg == 'timers_holdtime':
        REGEX = re.compile(r'(?:timers\s)(?P<value>.*)$', re.M)
        value = ''
        if 'timers' in config:
            parsed = REGEX.search(config).group('value').split()
            if len(parsed) == 2:
                value = parsed[1]

    return value


def get_existing(module, args):
    existing = {}
    netcfg = CustomNetworkConfig(indent=2, contents=get_config(module))
    custom = [
        'log_neighbor_changes',
        'pwd',
        'pwd_type',
        'remove_private_as',
        'timers_holdtime',
        'timers_keepalive'
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
        config = netcfg.get_section(parents)

        if config:
            for arg in args:
                if arg not in ['asn', 'vrf', 'neighbor']:
                    if arg in custom:
                        existing[arg] = get_custom_value(arg, config, module)
                    else:
                        existing[arg] = get_value(arg, config, module)

            existing['asn'] = existing_asn
            existing['neighbor'] = module.params['neighbor']
            existing['vrf'] = module.params['vrf']
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


def state_present(module, existing, proposed, candidate):
    commands = list()
    proposed_commands = apply_key_map(PARAM_TO_COMMAND_KEYMAP, proposed)
    existing_commands = apply_key_map(PARAM_TO_COMMAND_KEYMAP, existing)

    for key, value in proposed_commands.items():
        if value is True:
            commands.append(key)

        elif value is False:
            commands.append('no {0}'.format(key))

        elif value == 'default':
            if existing_commands.get(key):
                existing_value = existing_commands.get(key)
                commands.append('no {0} {1}'.format(key, existing_value))
        else:
            if key == 'log-neighbor-changes':
                if value == 'enable':
                    commands.append('{0}'.format(key))
                elif value == 'disable':
                    commands.append('{0} {1}'.format(key, value))
                elif value == 'inherit':
                    if existing_commands.get(key):
                        commands.append('no {0}'.format(key))
            elif key == 'password':
                pwd_type = module.params['pwd_type']
                if pwd_type == '3des':
                    pwd_type = 3
                else:
                    pwd_type = 7
                command = '{0} {1} {2}'.format(key, pwd_type, value)
                if command not in commands:
                    commands.append(command)
            elif key == 'remove-private-as':
                if value == 'enable':
                    command = '{0}'.format(key)
                    commands.append(command)
                elif value == 'disable':
                    if existing_commands.get(key) != 'disable':
                        command = 'no {0}'.format(key)
                        commands.append(command)
                else:
                    command = '{0} {1}'.format(key, value)
                    commands.append(command)
            elif key.startswith('timers'):
                command = 'timers {0} {1}'.format(
                    proposed_commands['timers-keepalive'],
                    proposed_commands['timers-holdtime'])
                if command not in commands:
                    commands.append(command)
            else:
                command = '{0} {1}'.format(key, value)
                commands.append(command)

    if commands:
        parents = ["router bgp {0}".format(module.params['asn'])]
        if module.params['vrf'] != 'default':
            parents.append('vrf {0}'.format(module.params['vrf']))

        parents.append('neighbor {0}'.format(module.params['neighbor']))

        # make sure that local-as is the last command in the list.
        local_as_command = 'local-as {0}'.format(module.params['local_as'])
        if local_as_command in commands:
            commands.remove(local_as_command)
            commands.append(local_as_command)
        candidate.add(commands, parents=parents)


def state_absent(module, existing, proposed, candidate):
    commands = []
    parents = ["router bgp {0}".format(module.params['asn'])]
    if module.params['vrf'] != 'default':
        parents.append('vrf {0}'.format(module.params['vrf']))

    commands.append('no neighbor {0}'.format(module.params['neighbor']))
    candidate.add(commands, parents=parents)


def main():
    argument_spec = dict(
        asn=dict(required=True, type='str'),
        vrf=dict(required=False, type='str', default='default'),
        neighbor=dict(required=True, type='str'),
        description=dict(required=False, type='str'),
        capability_negotiation=dict(required=False, type='bool'),
        connected_check=dict(required=False, type='bool'),
        dynamic_capability=dict(required=False, type='bool'),
        ebgp_multihop=dict(required=False, type='str'),
        local_as=dict(required=False, type='str'),
        log_neighbor_changes=dict(required=False, type='str', choices=['enable', 'disable', 'inherit']),
        low_memory_exempt=dict(required=False, type='bool'),
        maximum_peers=dict(required=False, type='str'),
        pwd=dict(required=False, type='str'),
        pwd_type=dict(required=False, type='str', choices=['cleartext', '3des', 'cisco_type_7', 'default']),
        remote_as=dict(required=False, type='str'),
        remove_private_as=dict(required=False, type='str', choices=['enable', 'disable', 'all', 'replace-as']),
        shutdown=dict(required=False, type='str'),
        suppress_4_byte_as=dict(required=False, type='bool'),
        timers_keepalive=dict(required=False, type='str'),
        timers_holdtime=dict(required=False, type='str'),
        transport_passive_only=dict(required=False, type='bool'),
        update_source=dict(required=False, type='str'),
        m_facts=dict(required=False, default=False, type='bool'),
        state=dict(choices=['present', 'absent'], default='present',
                       required=False),
        include_defaults=dict(default=True),
        config=dict(),
        save=dict(type='bool', default=False)
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                                required_together=[['timer_bgp_hold',
                                            'timer_bgp_keepalive']],
                                supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)


    state = module.params['state']
    if module.params['pwd_type'] == 'default':
        module.params['pwd_type'] = '0'

    args =  [
        'asn',
        'capability_negotiation',
        'connected_check',
        'description',
        'dynamic_capability',
        'ebgp_multihop',
        'local_as',
        'log_neighbor_changes',
        'low_memory_exempt',
        'maximum_peers',
        'neighbor',
        'pwd',
        'pwd_type',
        'remote_as',
        'remove_private_as',
        'shutdown',
        'suppress_4_byte_as',
        'timers_keepalive',
        'timers_holdtime',
        'transport_passive_only',
        'update_source',
        'vrf'
    ]

    existing = invoke('get_existing', module, args)
    if existing.get('asn'):
        if (existing.get('asn') != module.params['asn'] and
            state == 'present'):
            module.fail_json(msg='Another BGP ASN already exists.',
                             proposed_asn=module.params['asn'],
                             existing_asn=existing.get('asn'))

    end_state = existing
    proposed_args = dict((k, v) for k, v in module.params.items()
                    if v is not None and k in args)

    proposed = {}
    for key, value in proposed_args.items():
        if key not in ['asn', 'vrf', 'neighbor', 'pwd_type']:
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

