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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = '''
---
module: nxos_bgp
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages BGP configuration.
description:
    - Manages BGP configurations on NX-OS switches.
author:
    - Jason Edelman (@jedelman8)
    - Gabriele Gerbino (@GGabriele)
notes:
    - Tested against NXOSv 7.3.(0)D1(1) on VIRL
    - C(state=absent) removes the whole BGP ASN configuration when
      C(vrf=default) or the whole VRF instance within the BGP process when
      using a different VRF.
    - Default when supported restores params default value.
    - Configuring global parmas is only permitted if C(vrf=default).
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
        required: false
        default: null
    bestpath_always_compare_med:
        description:
            - Enable/Disable MED comparison on paths from different
              autonomous systems.
        required: false
        choices: ['true','false']
        default: null
    bestpath_aspath_multipath_relax:
        description:
            - Enable/Disable load sharing across the providers with
              different (but equal-length) AS paths.
        required: false
        choices: ['true','false']
        default: null
    bestpath_compare_routerid:
        description:
            - Enable/Disable comparison of router IDs for identical eBGP paths.
        required: false
        choices: ['true','false']
        default: null
    bestpath_cost_community_ignore:
        description:
            - Enable/Disable Ignores the cost community for BGP best-path
              calculations.
        required: false
        choices: ['true','false']
        default: null
    bestpath_med_confed:
        description:
            - Enable/Disable enforcement of bestpath to do a MED comparison
              only between paths originated within a confederation.
        required: false
        choices: ['true','false']
        default: null
    bestpath_med_missing_as_worst:
        description:
            - Enable/Disable assigns the value of infinity to received
              routes that do not carry the MED attribute, making these routes
              the least desirable.
        required: false
        choices: ['true','false']
        default: null
    bestpath_med_non_deterministic:
        description:
            - Enable/Disable deterministic selection of the best MED pat
              from among the paths from the same autonomous system.
        required: false
        choices: ['true','false']
        default: null
    cluster_id:
        description:
            - Route Reflector Cluster-ID.
        required: false
        default: null
    confederation_id:
        description:
            - Routing domain confederation AS.
        required: false
        default: null
    confederation_peers:
        description:
            - AS confederation parameters.
        required: false
        default: null
    disable_policy_batching:
        description:
            - Enable/Disable the batching evaluation of prefix advertisement
              to all peers.
        required: false
        choices: ['true','false']
        default: null
    disable_policy_batching_ipv4_prefix_list:
        description:
            - Enable/Disable the batching evaluation of prefix advertisements
              to all peers with prefix list.
        required: false
        default: null
    disable_policy_batching_ipv6_prefix_list:
        description:
            - Enable/Disable the batching evaluation of prefix advertisements
              to all peers with prefix list.
        required: false
    enforce_first_as:
        description:
            - Enable/Disable enforces the neighbor autonomous system to be
              the first AS number listed in the AS path attribute for eBGP.
              On NX-OS, this property is only supported in the
              global BGP context.
        required: false
        choices: ['true','false']
        default: null
    event_history_cli:
        description:
            - Enable/Disable cli event history buffer.
        required: false
        choices: ['size_small', 'size_medium', 'size_large', 'size_disable', 'default']
        default: null
    event_history_detail:
        description:
            - Enable/Disable detail event history buffer.
        required: false
        choices: ['size_small', 'size_medium', 'size_large', 'size_disable', 'default']
        default: null
    event_history_events:
        description:
            - Enable/Disable event history buffer.
        required: false
        choices: ['size_small', 'size_medium', 'size_large', 'size_disable', 'default']
        default: null
    event_history_periodic:
        description:
            - Enable/Disable periodic event history buffer.
        required: false
        choices: ['size_small', 'size_medium', 'size_large', 'size_disable', 'default']
    fast_external_fallover:
        description:
            - Enable/Disable immediately reset the session if the link to a
              directly connected BGP peer goes down.  Only supported in the
              global BGP context.
        required: false
        choices: ['true','false']
        default: null
    flush_routes:
        description:
            - Enable/Disable flush routes in RIB upon controlled restart.
              On NX-OS, this property is only supported in the global
              BGP context.
        required: false
        choices: ['true','false']
        default: null
    graceful_restart:
        description:
            - Enable/Disable graceful restart.
        required: false
        choices: ['true','false']
        default: null
    graceful_restart_helper:
        description:
            - Enable/Disable graceful restart helper mode.
        required: false
        choices: ['true','false']
        default: null
    graceful_restart_timers_restart:
        description:
            - Set maximum time for a restart sent to the BGP peer.
        required: false
        choices: ['true','false']
        default: null
    graceful_restart_timers_stalepath_time:
        description:
            - Set maximum time that BGP keeps the stale routes from the
              restarting BGP peer.
        choices: ['true','false']
        default: null
    isolate:
        description:
            - Enable/Disable isolate this router from BGP perspective.
        required: false
        choices: ['true','false']
        default: null
    local_as:
        description:
            - Local AS number to be used within a VRF instance.
        required: false
        default: null
    log_neighbor_changes:
        description:
            - Enable/Disable message logging for neighbor up/down event.
        required: false
        choices: ['true','false']
        default: null
    maxas_limit:
        description:
            - Specify Maximum number of AS numbers allowed in the AS-path
              attribute. Valid values are between 1 and 512.
        required: false
        default: null
    neighbor_down_fib_accelerate:
        description:
            - Enable/Disable handle BGP neighbor down event, due to
              various reasons.
        required: false
        choices: ['true','false']
        default: null
    reconnect_interval:
        description:
            - The BGP reconnection interval for dropped sessions.
              Valid values are between 1 and 60.
        required: false
        default: null
    router_id:
        description:
            - Router Identifier (ID) of the BGP router VRF instance.
        required: false
        default: null
    shutdown:
        description:
            - Administratively shutdown the BGP protocol.
        required: false
        choices: ['true','false']
        default: null
    suppress_fib_pending:
        description:
            - Enable/Disable advertise only routes programmed in hardware
              to peers.
        required: false
        choices: ['true','false']
        default: null
    timer_bestpath_limit:
        description:
            - Specify timeout for the first best path after a restart,
              in seconds.
        required: false
        default: null
    timer_bestpath_limit_always:
        description:
            - Enable/Disable update-delay-always option.
        required: false
        choices: ['true','false']
        default: null
    timer_bgp_hold:
        description:
            - Set BGP hold timer.
        required: false
        default: null
    timer_bgp_keepalive:
        description:
            - Set BGP keepalive timer.
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
- name: Configure a simple ASN
  nxos_bgp:
      asn: 65535
      vrf: test
      router_id: 1.1.1.1
      state: present
'''

RETURN = '''
commands:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["router bgp 65535", "vrf test", "router-id 1.1.1.1"]
'''

import re

from ansible.module_utils.network.nxos.nxos import get_config, load_config
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.config import CustomNetworkConfig


BOOL_PARAMS = [
    'bestpath_always_compare_med',
    'bestpath_aspath_multipath_relax',
    'bestpath_compare_neighborid',
    'bestpath_compare_routerid',
    'bestpath_cost_community_ignore',
    'bestpath_med_confed',
    'bestpath_med_missing_as_worst',
    'bestpath_med_non_deterministic',
    'disable_policy_batching',
    'enforce_first_as',
    'fast_external_fallover',
    'flush_routes',
    'graceful_restart',
    'graceful_restart_helper',
    'isolate',
    'log_neighbor_changes',
    'neighbor_down_fib_accelerate',
    'shutdown',
    'suppress_fib_pending'
]
GLOBAL_PARAMS = [
    'disable_policy_batching',
    'disable_policy_batching_ipv4_prefix_list',
    'disable_policy_batching_ipv6_prefix_list',
    'enforce_first_as',
    'event_history_cli',
    'event_history_detail',
    'event_history_events',
    'event_history_periodic',
    'fast_external_fallover',
    'flush_routes',
    'isolate',
    'shutdown'
]
PARAM_TO_DEFAULT_KEYMAP = {
    'timer_bgp_keepalive': '60',
    'timer_bgp_hold': '180',
    'graceful_restart': True,
    'graceful_restart_timers_restart': '120',
    'graceful_restart_timers_stalepath_time': '300',
    'reconnect_interval': '60',
    'suppress_fib_pending': True,
    'fast_external_fallover': True,
    'enforce_first_as': True,
    'event_history_cli': True,
    'event_history_events': True,
    'event_history_periodic': True,
}
PARAM_TO_COMMAND_KEYMAP = {
    'asn': 'router bgp',
    'bestpath_always_compare_med': 'bestpath always-compare-med',
    'bestpath_aspath_multipath_relax': 'bestpath as-path multipath-relax',
    'bestpath_compare_neighborid': 'bestpath compare-neighborid',
    'bestpath_compare_routerid': 'bestpath compare-routerid',
    'bestpath_cost_community_ignore': 'bestpath cost-community ignore',
    'bestpath_med_confed': 'bestpath med confed',
    'bestpath_med_missing_as_worst': 'bestpath med missing-as-worst',
    'bestpath_med_non_deterministic': 'bestpath med non-deterministic',
    'cluster_id': 'cluster-id',
    'confederation_id': 'confederation identifier',
    'confederation_peers': 'confederation peers',
    'disable_policy_batching': 'disable-policy-batching',
    'disable_policy_batching_ipv4_prefix_list': 'disable-policy-batching ipv4 prefix-list',
    'disable_policy_batching_ipv6_prefix_list': 'disable-policy-batching ipv6 prefix-list',
    'enforce_first_as': 'enforce-first-as',
    'event_history_cli': 'event-history cli',
    'event_history_detail': 'event-history detail',
    'event_history_events': 'event-history events',
    'event_history_periodic': 'event-history periodic',
    'fast_external_fallover': 'fast-external-fallover',
    'flush_routes': 'flush-routes',
    'graceful_restart': 'graceful-restart',
    'graceful_restart_helper': 'graceful-restart-helper',
    'graceful_restart_timers_restart': 'graceful-restart restart-time',
    'graceful_restart_timers_stalepath_time': 'graceful-restart stalepath-time',
    'isolate': 'isolate',
    'local_as': 'local-as',
    'log_neighbor_changes': 'log-neighbor-changes',
    'maxas_limit': 'maxas-limit',
    'neighbor_down_fib_accelerate': 'neighbor-down fib-accelerate',
    'reconnect_interval': 'reconnect-interval',
    'router_id': 'router-id',
    'shutdown': 'shutdown',
    'suppress_fib_pending': 'suppress-fib-pending',
    'timer_bestpath_limit': 'timers bestpath-limit',
    'timer_bgp_hold': 'timers bgp',
    'timer_bgp_keepalive': 'timers bgp',
    'vrf': 'vrf'
}


def get_value(arg, config):
    command = PARAM_TO_COMMAND_KEYMAP.get(arg)

    if command.split()[0] == 'event-history':
        has_size = re.search(r'^\s+{0} size\s(?P<value>.*)$'.format(command), config, re.M)

        if command == 'event-history detail':
            value = False
        else:
            value = 'size_small'

        if has_size:
            value = 'size_%s' % has_size.group('value')

    elif arg in ['enforce_first_as', 'fast_external_fallover']:
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
                value = found_value

    return value


def get_existing(module, args, warnings):
    existing = {}
    netcfg = CustomNetworkConfig(indent=2, contents=get_config(module, flags=['bgp all']))

    asn_re = re.compile(r'.*router\sbgp\s(?P<existing_asn>\d+(\.\d+)?).*', re.S)
    asn_match = asn_re.match(str(netcfg))

    if asn_match:
        existing_asn = asn_match.group('existing_asn')
        bgp_parent = 'router bgp {0}'.format(existing_asn)

        if module.params['vrf'] != 'default':
            parents = [bgp_parent, 'vrf {0}'.format(module.params['vrf'])]
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
        warnings.append(msg)

    return existing


def apply_key_map(key_map, table):
    new_dict = {}
    for key in table:
        new_key = key_map.get(key)
        if new_key:
            new_dict[new_key] = table.get(key)

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
            default_value = PARAM_TO_DEFAULT_KEYMAP.get(key)
            existing_value = existing_commands.get(key)

            if default_value:
                commands.append('{0} {1}'.format(key, default_value))
            elif existing_value:
                if key == 'confederation peers':
                    existing_value = ' '.join(existing_value)
                commands.append('no {0} {1}'.format(key, existing_value))
        elif key == 'confederation peers':
            existing_confederation_peers = set(existing.get('confederation_peers', []))
            new_values = set(value.split())
            peer_string = ' '.join(existing_confederation_peers | new_values)
            commands.append('{0} {1}'.format(key, peer_string))
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
            parents.append('vrf {0}'.format(module.params['vrf']))
    elif proposed:
        if module.params['vrf'] != 'default':
            commands.append('vrf {0}'.format(module.params['vrf']))
            parents = ['router bgp {0}'.format(module.params['asn'])]
        else:
            commands.append('router bgp {0}'.format(module.params['asn']))

    candidate.add(commands, parents=parents)


def state_absent(module, existing, candidate):
    commands = []
    parents = []
    if module.params['vrf'] == 'default':
        commands.append('no router bgp {0}'.format(module.params['asn']))
    elif existing.get('vrf') == module.params['vrf']:
        commands.append('no vrf {0}'.format(module.params['vrf']))
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
        commands.pop(commands.index(local_as_command))
        commands.pop(commands.index(confederation_id_command))
        commands.append(local_as_command)
        commands.append(confederation_id_command)

    elif confederation_peers_command and confederation_id_command:
        commands.pop(commands.index(confederation_peers_command))
        commands.pop(commands.index(confederation_id_command))
        commands.append(confederation_id_command)
        commands.append(confederation_peers_command)

    return commands


def main():
    argument_spec = dict(
        asn=dict(required=True, type='str'),
        vrf=dict(required=False, type='str', default='default'),
        bestpath_always_compare_med=dict(required=False, type='bool'),
        bestpath_aspath_multipath_relax=dict(required=False, type='bool'),
        bestpath_compare_neighborid=dict(required=False, type='bool'),
        bestpath_compare_routerid=dict(required=False, type='bool'),
        bestpath_cost_community_ignore=dict(required=False, type='bool'),
        bestpath_med_confed=dict(required=False, type='bool'),
        bestpath_med_missing_as_worst=dict(required=False, type='bool'),
        bestpath_med_non_deterministic=dict(required=False, type='bool'),
        cluster_id=dict(required=False, type='str'),
        confederation_id=dict(required=False, type='str'),
        confederation_peers=dict(required=False, type='str'),
        disable_policy_batching=dict(required=False, type='bool'),
        disable_policy_batching_ipv4_prefix_list=dict(required=False, type='str'),
        disable_policy_batching_ipv6_prefix_list=dict(required=False, type='str'),
        enforce_first_as=dict(required=False, type='bool'),
        event_history_cli=dict(required=False, choices=['true', 'false', 'default', 'size_small', 'size_medium', 'size_large', 'size_disable']),
        event_history_detail=dict(required=False, choices=['true', 'false', 'default', 'size_small', 'size_medium', 'size_large', 'size_disable']),
        event_history_events=dict(required=False, choices=['true', 'false', 'default', 'size_small', 'size_medium', 'size_large', 'size_disable']),
        event_history_periodic=dict(required=False, choices=['true', 'false', 'default', 'size_small', 'size_medium', 'size_large', 'size_disable']),
        fast_external_fallover=dict(required=False, type='bool'),
        flush_routes=dict(required=False, type='bool'),
        graceful_restart=dict(required=False, type='bool'),
        graceful_restart_helper=dict(required=False, type='bool'),
        graceful_restart_timers_restart=dict(required=False, type='str'),
        graceful_restart_timers_stalepath_time=dict(required=False, type='str'),
        isolate=dict(required=False, type='bool'),
        local_as=dict(required=False, type='str'),
        log_neighbor_changes=dict(required=False, type='bool'),
        maxas_limit=dict(required=False, type='str'),
        neighbor_down_fib_accelerate=dict(required=False, type='bool'),
        reconnect_interval=dict(required=False, type='str'),
        router_id=dict(required=False, type='str'),
        shutdown=dict(required=False, type='bool'),
        suppress_fib_pending=dict(required=False, type='bool'),
        timer_bestpath_limit=dict(required=False, type='str'),
        timer_bgp_hold=dict(required=False, type='str'),
        timer_bgp_keepalive=dict(required=False, type='str'),
        state=dict(choices=['present', 'absent'], default='present', required=False),
    )
    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           required_together=[['timer_bgp_hold', 'timer_bgp_keepalive']],
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)
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
            if existing.get(key) != value:
                proposed[key] = value

    candidate = CustomNetworkConfig(indent=3)
    if state == 'present':
        state_present(module, existing, proposed, candidate)
    elif existing.get('asn') == module.params['asn']:
        state_absent(module, existing, candidate)

    if candidate:
        candidate = candidate.items_text()
        load_config(module, candidate)
        result['changed'] = True
        result['commands'] = candidate
    else:
        result['commands'] = []

    module.exit_json(**result)


if __name__ == '__main__':
    main()
