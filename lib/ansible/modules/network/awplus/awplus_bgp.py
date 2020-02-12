#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2020, Allied Telesis Ltd.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: awplus_bgp
author:
    - Jeremy Toth (@jtsource)
    - Cheng Yi Kok (@cyk19)
short_description: Manages BGP configuration.
description:
    - Manages BGP configurations on AlliedWare Plus switches.
version_added: "2.10"
notes:
    - C(state=absent) removes the whole BGP ASN configuration when
      C(vrf=default) or the whole VRF instance within the BGP process when
      using a different VRF.
    - Default when supported restores params default value.
    - Configuring global params is only permitted if C(vrf=default).
options:
    asn:
        description:
            - BGP autonomous system number. Valid values are String,
              Integer in ASPLAIN or ASDOT notation.
        required: true
    vrf:
        description:
            - Name of the VRF. The name 'default' is a valid VRF representing
              the global BGP.
    bestpath_always_compare_med:
        description:
            - Enable/Disable MED comparison on paths from different
              autonomous systems.
        type: bool
    bestpath_compare_routerid:
        description:
            - Enable/Disable comparison of router IDs for identical eBGP paths.
        type: bool
    bestpath_med_confed:
        description:
            - Enable/Disable enforcement of bestpath to do a MED comparison
              only between paths originated within a confederation.
        type: bool
    bestpath_med_missing_as_worst:
        description:
            - Enable/Disable assigns the value of infinity to received
              routes that do not carry the MED attribute, making these routes
              the least desirable.
        type: bool
    cluster_id:
        description:
            - Route Reflector Cluster-ID.
    confederation_id:
        description:
            - Routing domain confederation AS.
    confederation_peers:
        description:
            - AS confederation parameters.
    enforce_first_as:
        description:
            - Enable/Disable enforces the neighbor autonomous system to be
              the first AS number listed in the AS path attribute for eBGP.
              On NX-OS, this property is only supported in the
              global BGP context.
        type: bool
    graceful_restart:
        description:
            - Enable/Disable graceful restart.
        type: bool
    graceful_restart_timers_restart:
        description:
            - Set maximum time for a restart sent to the BGP peer.
    graceful_restart_timers_stalepath_time:
        description:
            - Set maximum time that BGP keeps the stale routes from the
              restarting BGP peer.
    router_id:
        description:
            - Router Identifier (ID) of the BGP router VRF instance.
    timer_bgp_hold:
        description:
            - Set BGP hold timer.
    timer_bgp_keepalive:
        description:
            - Set BGP keepalive timer.
    state:
        description:
            - Determines whether the config should be present or not
              on the device.
        default: present
        choices: ['present','absent']
"""

EXAMPLES = """
- name: Configure a simple ASN
        awplus_bgp:
          asn: 100
          vrf: default
          router_id: 192.0.2.4
          state: present
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - ["router bgp 100", "bgp router-id 192.0.2.4"]
"""

import re

from ansible.module_utils.network.awplus.awplus import get_config, load_config
from ansible.module_utils.network.awplus.awplus import awplus_argument_spec
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.config import CustomNetworkConfig


GLOBAL_PARAMS = [
    'enforce_first_as',
    'timer_bgp_hold',
    'timer_bgp_keepalive',
    'bestpath_always_compare_med',
    'bestpath_compare_routerid',
    'bestpath_med_confed',
    'bestpath_med_missing_as_worst',
    'cluster_id',
    'confederation_id',
    'confederation_peers',
    'graceful_restart',
    'graceful_restart_timers_restart',
    'graceful_restart_timers_stalepath_time',
]

BOOL_PARAMS = [
    'bestpath_always_compare_med',
    'bestpath_compare_routerid',
    'bestpath_med_confed',
    'bestpath_med_missing_as_worst',
    'enforce_first_as',
    'graceful_restart',
]

PARAM_TO_COMMAND_KEYMAP = {
    'asn': 'router bgp',
    'bestpath_always_compare_med': 'bgp always-compare-med',
    'bestpath_compare_routerid': 'bgp bestpath compare-routerid',
    'bestpath_med_confed': 'bgp bestpath med confed',
    'bestpath_med_missing_as_worst': 'bgp bestpath med missing-as-worst',
    'cluster_id': 'bgp cluster-id',
    'confederation_id': ' bgp confederation identifier',
    'confederation_peers': 'bgp confederation peers',
    'enforce_first_as': 'bgp enforce-first-as',
    'graceful_restart': 'bgp graceful-restart',
    'graceful_restart_timers_restart': 'bgp graceful-restart restart-time',
    'graceful_restart_timers_stalepath_time': 'bgp graceful-restart stalepath-time',
    'router_id': 'bgp router-id',
    'timer_bgp_hold': 'timers bgp',
    'timer_bgp_keepalive': 'timers bgp',
    'vrf': 'address-family ipv4 vrf'
}

PARAM_TO_DEFAULT_KEYMAP = {
    'timer_bgp_keepalive': '60',
    'timer_bgp_hold': '180',
    'graceful_restart': True,
    'graceful_restart_timers_restart': '120',
    'graceful_restart_timers_stalepath_time': '300',
    'enforce_first_as': True,
    'router_id': '',
    'cluster_id': '',
    'confederation_id': '',
}


def apply_key_map(key_map, table):
    new_dict = {}
    for key in table:
        new_key = key_map.get(key)
        if new_key:
            new_dict[new_key] = table.get(key)

    return new_dict


def state_absent(module, existing, candidate):
    commands = []
    parents = []
    if module.params['vrf'] == 'default':
        commands.append('no router bgp {0}'.format(module.params['asn']))
    elif existing.get('vrf') == module.params['vrf']:
        commands.append('no address-family ipv4 vrf {0}'.format(module.params['vrf']))
        parents = ['router bgp {0}'.format(module.params['asn'])]

    candidate.add(commands, parents=parents)


def fix_commands(commands):
    local_as_command = ''
    confederation_id_command = ''
    confederation_peers_command = ''

    for command in commands:
        if 'local-as' in command:
            local_as_command = command
        elif 'confederation identifier' in command:
            confederation_id_command = command
        elif 'confederation peers' in command:
            confederation_peers_command = command

    if local_as_command and confederation_id_command:
        if 'no' in confederation_id_command:
            commands.pop(commands.index(local_as_command))
            commands.pop(commands.index(confederation_id_command))
            commands.append(confederation_id_command)
            commands.append(local_as_command)
        else:
            commands.pop(commands.index(local_as_command))
            commands.pop(commands.index(confederation_id_command))
            commands.append(local_as_command)
            commands.append(confederation_id_command)

    if confederation_peers_command and confederation_id_command:
        if local_as_command:
            if 'no' in local_as_command:
                commands.pop(commands.index(local_as_command))
                commands.pop(commands.index(confederation_id_command))
                commands.pop(commands.index(confederation_peers_command))
                commands.append(confederation_id_command)
                commands.append(confederation_peers_command)
                commands.append(local_as_command)
            else:
                commands.pop(commands.index(local_as_command))
                commands.pop(commands.index(confederation_id_command))
                commands.pop(commands.index(confederation_peers_command))
                commands.append(local_as_command)
                commands.append(confederation_id_command)
                commands.append(confederation_peers_command)
        else:
            commands.pop(commands.index(confederation_peers_command))
            commands.pop(commands.index(confederation_id_command))
            commands.append(confederation_id_command)
            commands.append(confederation_peers_command)

    return commands


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
            default_value = PARAM_TO_DEFAULT_KEYMAP.get(key)
            existing_value = existing_commands.get(key)

            if default_value:
                commands.append('{0} {1}'.format(key, default_value))
            elif existing_value:
                if key == 'confederation peers':
                    existing_value = ' '.join(existing_value)
                commands.append('no {0} {1}'.format(key, existing_value))
        elif not value:
            existing_value = existing_commands.get(key)
            if existing_value:
                commands.append('no {0} {1}'.format(key, existing_value))
        elif key == 'confederation peers':
            commands.append('{0} {1}'.format(key, value))
        elif key.startswith('timers bgp'):
            command = 'timers bgp {0} {1}'.format(
                proposed['timer_bgp_keepalive'],
                proposed['timer_bgp_hold'])
            if command not in commands:
                commands.append(command)
        else:
            if value.startswith('size'):
                value = value.replace('_', ' ')
            command = '{0} {1}'.format(key, value)
            commands.append(command)

    parents = []
    if commands:
        commands = fix_commands(commands)
        parents = ['router bgp {0}'.format(module.params['asn'])]
        if module.params['vrf'] != 'default':
            parents.append('address-family ipv4 vrf {0}'.format(module.params['vrf']))
    elif proposed:
        if module.params['vrf'] != 'default':
            commands.append('address-family ipv4 vrf {0}'.format(module.params['vrf']))
            parents = ['router bgp {0}'.format(module.params['asn'])]
        else:
            commands.append('router bgp {0}'.format(module.params['asn']))

    candidate.add(commands, parents=parents)


def get_value(arg, config):
    command = PARAM_TO_COMMAND_KEYMAP.get(arg)

    if arg == 'enforce_first_as':
        no_command_re = re.compile(r'no\s+{0}\s*'.format(command), re.M)
        value = True

        if no_command_re.search(config):
            value = False

    elif arg in BOOL_PARAMS:
        has_command = re.search(r'^\s+{0}\s*$'.format(command), config, re.M)
        value = False

        if has_command:
            value = True
    else:
        command_val_re = re.compile(r'(?:{0}\s)(?P<value>.*)'.format(command), re.M)
        value = ''

        has_command = command_val_re.search(config)
        if has_command:
            found_value = has_command.group('value')

            if arg == 'confederation_peers':
                value = found_value.split()
            elif arg == 'timer_bgp_keepalive':
                value = found_value.split()[0]
            elif arg == 'timer_bgp_hold':
                split_values = found_value.split()
                if len(split_values) == 2:
                    value = split_values[1]
            elif found_value:
                value = found_value.strip()

    return value


def get_existing(module, args, warnings):
    existing = {}
    netcfg = CustomNetworkConfig(indent=2, contents=get_config(module, flags=['bgp']))

    asn_re = re.compile(r'router bgp (?P<existing_asn>\d+)', re.S)
    asn_match = asn_re.match(str(netcfg))

    if asn_match:
        existing_asn = asn_match.group('existing_asn')

        bgp_parent = 'router bgp {0}'.format(existing_asn)

        if module.params['vrf'] != 'default':
            parents = [bgp_parent, 'address-family ipv4 vrf {0}'.format(module.params['vrf'])]
        else:
            parents = [bgp_parent]

        config = netcfg.get_section(parents)

        if config:
            for arg in args:
                if arg != 'asn' and (module.params['vrf'] == 'default' or
                                     arg not in GLOBAL_PARAMS):
                    existing[arg] = get_value(arg, config)

            existing['asn'] = existing_asn
            if module.params['vrf'] == 'default':
                existing['vrf'] = 'default'

    if not existing and module.params['vrf'] != 'default' and module.params['state'] == 'present':
        msg = ("VRF {0} doesn't exist.".format(module.params['vrf']))
        module.fail_json(msg=msg)
        warnings.append(msg)
    return existing


def main():
    argument_spec = dict(
        asn=dict(required=True, type='str'),
        vrf=dict(required=False, type='str', default='default'),
        bestpath_always_compare_med=dict(required=False, type='bool'),
        bestpath_compare_routerid=dict(required=False, type='bool'),
        bestpath_med_confed=dict(required=False, type='bool'),
        bestpath_med_missing_as_worst=dict(required=False, type='bool'),
        cluster_id=dict(required=False, type='str'),
        confederation_id=dict(required=False, type='str'),
        confederation_peers=dict(required=False, type='list'),
        enforce_first_as=dict(required=False, type='bool'),
        graceful_restart=dict(required=False, type='bool'),
        graceful_restart_timers_restart=dict(required=False, type='str'),
        graceful_restart_timers_stalepath_time=dict(required=False, type='str'),
        local_as=dict(required=False, type='str'),
        router_id=dict(required=False, type='str'),
        timer_bgp_hold=dict(required=False, type='str'),
        timer_bgp_keepalive=dict(required=False, type='str'),
        state=dict(choices=['present', 'absent'], default='present', required=False),
    )
    argument_spec.update(awplus_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           required_together=[['timer_bgp_hold', 'timer_bgp_keepalive']],
                           supports_check_mode=True)

    warnings = list()
    result = dict(changed=False, warnings=warnings)

    state = module.params['state']

    if module.params['vrf'] != 'default':
        for param in GLOBAL_PARAMS:
            if module.params[param]:
                module.fail_json(msg='Global params can be modified only under "default" VRF.',
                                 vrf=module.params['vrf'],
                                 global_param=param)

    args = PARAM_TO_COMMAND_KEYMAP.keys()
    existing = get_existing(module, args, warnings)

    if existing.get('asn') and state == 'present':
        if existing.get('asn') != module.params['asn']:
            module.fail_json(msg='Another BGP ASN already exists.',
                             proposed_asn=module.params['asn'],
                             existing_asn=existing.get('asn'))

    proposed_args = dict((k, v) for k, v in module.params.items()
                         if v is not None and k in args)
    proposed = {}
    for key, value in proposed_args.items():
        if key not in ['asn', 'vrf']:
            if str(value).lower() == 'default':
                value = PARAM_TO_DEFAULT_KEYMAP.get(key, 'default')
            if key == 'confederation_peers':
                if value[0] == 'default':
                    if existing.get(key):
                        proposed[key] = 'default'
                else:
                    v = set([int(i) for i in value])
                    ex = set([int(i) for i in existing.get(key)])
                    if v != ex:
                        proposed[key] = ' '.join(str(s) for s in v)
            else:
                if existing.get(key) != value:
                    proposed[key] = value

    candidate = CustomNetworkConfig(indent=3)
    if state == 'present':
        state_present(module, existing, proposed, candidate)
    elif existing.get('asn') == module.params['asn']:
        state_absent(module, existing, candidate)

    if candidate:
        candidate = candidate.items_text()
        if not module.check_mode:
            load_config(module, candidate)
        result['changed'] = True
        result['commands'] = candidate
    else:
        result['commands'] = []

    module.exit_json(**result)


if __name__ == '__main__':
    main()
