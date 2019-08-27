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
module: nxos_igmp_interface
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages IGMP interface configuration.
description:
    - Manages IGMP interface configuration settings.
author:
    - Jason Edelman (@jedelman8)
    - Gabriele Gerbino (@GGabriele)
notes:
    - Tested against NXOSv 7.3.(0)D1(1) on VIRL
    - When C(state=default), supported params will be reset to a default state.
      These include C(version), C(startup_query_interval),
      C(startup_query_count), C(robustness), C(querier_timeout), C(query_mrt),
      C(query_interval), C(last_member_qrt), C(last_member_query_count),
      C(group_timeout), C(report_llg), and C(immediate_leave).
    - When C(state=absent), all configs for C(oif_ps), and
      C(oif_routemap) will be removed.
    - PIM must be enabled to use this module.
    - This module is for Layer 3 interfaces.
    - Route-map check not performed (same as CLI) check when configuring
      route-map with 'static-oif'
    - If restart is set to true with other params set, the restart will happen
      last, i.e. after the configuration takes place. However, 'restart' itself
      is not idempotent as it is an action and not configuration.
options:
    interface:
        description:
            - The full interface name for IGMP configuration.
              e.g. I(Ethernet1/2).
        required: true
    version:
        description:
            - IGMP version. It can be 2 or 3 or keyword 'default'.
        choices: ['2', '3', 'default']
    startup_query_interval:
        description:
            - Query interval used when the IGMP process starts up.
              The range is from 1 to 18000 or keyword 'default'.
              The default is 31.
    startup_query_count:
        description:
            - Query count used when the IGMP process starts up.
              The range is from 1 to 10 or keyword 'default'.
              The default is 2.
    robustness:
        description:
            - Sets the robustness variable. Values can range from 1 to 7 or
              keyword 'default'. The default is 2.
    querier_timeout:
        description:
            - Sets the querier timeout that the software uses when deciding
              to take over as the querier. Values can range from 1 to 65535
              seconds or keyword 'default'. The default is 255 seconds.
    query_mrt:
        description:
            - Sets the response time advertised in IGMP queries.
              Values can range from 1 to 25 seconds or keyword 'default'.
              The default is 10 seconds.
    query_interval:
        description:
            - Sets the frequency at which the software sends IGMP host query
              messages. Values can range from 1 to 18000 seconds or keyword
              'default'. The default is 125 seconds.
    last_member_qrt:
        description:
            - Sets the query interval waited after sending membership reports
              before the software deletes the group state. Values can range
              from 1 to 25 seconds or keyword 'default'. The default is 1 second.
    last_member_query_count:
        description:
            - Sets the number of times that the software sends an IGMP query
              in response to a host leave message.
              Values can range from 1 to 5 or keyword 'default'. The default is 2.
    group_timeout:
        description:
            - Sets the group membership timeout for IGMPv2.
              Values can range from 3 to 65,535 seconds or keyword 'default'.
              The default is 260 seconds.
    report_llg:
        description:
            - Configures report-link-local-groups.
              Enables sending reports for groups in 224.0.0.0/24.
              Reports are always sent for nonlink local groups.
              By default, reports are not sent for link local groups.
        type: bool
    immediate_leave:
        description:
            - Enables the device to remove the group entry from the multicast
              routing table immediately upon receiving a leave message for
              the group. Use this command to minimize the leave latency of
              IGMPv2 group memberships on a given IGMP interface because the
              device does not send group-specific queries.
              The default is disabled.
        type: bool
    oif_routemap:
        description:
            - Configure a routemap for static outgoing interface (OIF) or
              keyword 'default'.
    oif_prefix:
        description:
            - This argument is deprecated, please use oif_ps instead.
              Configure a prefix for static outgoing interface (OIF).
    oif_source:
        description:
            - This argument is deprecated, please use oif_ps instead.
              Configure a source for static outgoing interface (OIF).
    oif_ps:
        description:
            - Configure prefixes and sources for static outgoing interface (OIF). This
              is a list of dict where each dict has source and prefix defined or just
              prefix if source is not needed. The specified values will be configured
              on the device and if any previous prefix/sources exist, they will be removed.
              Keyword 'default' is also accpted which removes all existing prefix/sources.
        version_added: 2.6
    restart:
        description:
            - Restart IGMP. This is NOT idempotent as this is action only.
        type: bool
        default: False
    state:
        description:
            - Manages desired state of the resource.
        default: present
        choices: ['present', 'absent', 'default']
'''
EXAMPLES = '''
- nxos_igmp_interface:
    interface: ethernet1/32
    startup_query_interval: 30
    oif_ps:
      - { 'prefix': '238.2.2.6' }
      - { 'source': '192.168.0.1', 'prefix': '238.2.2.5'}
    state: present
'''
RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"startup_query_count": "30",
             "oif_ps": [{'prefix': '238.2.2.6'}, {'source': '192.168.0.1', 'prefix': '238.2.2.5'}]}
existing:
    description: k/v pairs of existing igmp_interface configuration
    returned: always
    type: dict
    sample: {"startup_query_count": "2", "oif_ps": []}
end_state:
    description: k/v pairs of igmp interface configuration after module execution
    returned: always
    type: dict
    sample: {"startup_query_count": "30",
             "oif_ps": [{'prefix': '238.2.2.6'}, {'source': '192.168.0.1', 'prefix': '238.2.2.5'}]}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["interface Ethernet1/32", "ip igmp startup-query-count 30",
             "ip igmp static-oif 238.2.2.6", "ip igmp static-oif 238.2.2.5 source 192.168.0.1"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: bool
    sample: true
'''

from ansible.module_utils.network.nxos.nxos import get_config, load_config, run_commands
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec, check_args
from ansible.module_utils.network.nxos.nxos import get_interface_type
from ansible.module_utils.basic import AnsibleModule

import re


def execute_show_command(command, module, command_type='cli_show'):
    if command_type == 'cli_show_ascii':
        cmds = [{
            'command': command,
            'output': 'text',
        }]
    else:
        cmds = [{
            'command': command,
            'output': 'json',
        }]

    return run_commands(module, cmds)


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
    elif intf_type == 'loopback' or intf_type == 'svi':
        mode = 'layer3'
    return mode


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


def flatten_list(command_lists):
    flat_command_list = []
    for command in command_lists:
        if isinstance(command, list):
            flat_command_list.extend(command)
        else:
            flat_command_list.append(command)
    return flat_command_list


def get_igmp_interface(module, interface):
    command = 'show ip igmp interface {0}'.format(interface)
    igmp = {}

    key_map = {
        'IGMPVersion': 'version',
        'ConfiguredStartupQueryInterval': 'startup_query_interval',
        'StartupQueryCount': 'startup_query_count',
        'RobustnessVariable': 'robustness',
        'ConfiguredQuerierTimeout': 'querier_timeout',
        'ConfiguredMaxResponseTime': 'query_mrt',
        'ConfiguredQueryInterval': 'query_interval',
        'LastMemberMTR': 'last_member_qrt',
        'LastMemberQueryCount': 'last_member_query_count',
        'ConfiguredGroupTimeout': 'group_timeout'
    }

    body = execute_show_command(command, module)[0]

    if body:
        if 'not running' in body:
            return igmp
        resource = body['TABLE_vrf']['ROW_vrf']['TABLE_if']['ROW_if']
        igmp = apply_key_map(key_map, resource)
        report_llg = str(resource['ReportingForLinkLocal']).lower()
        if report_llg == 'true':
            igmp['report_llg'] = True
        elif report_llg == 'false':
            igmp['report_llg'] = False

        immediate_leave = str(resource['ImmediateLeave']).lower()  # returns en or dis
        if re.search(r'^en|^true|^enabled', immediate_leave):
            igmp['immediate_leave'] = True
        elif re.search(r'^dis|^false|^disabled', immediate_leave):
            igmp['immediate_leave'] = False

    # the  next block of code is used to retrieve anything with:
    # ip igmp static-oif *** i.e.. could be route-map ROUTEMAP
    # or PREFIX source <ip>, etc.
    command = 'show run interface {0} | inc oif'.format(interface)

    body = execute_show_command(
        command, module, command_type='cli_show_ascii')[0]

    staticoif = []
    if body:
        split_body = body.split('\n')
        route_map_regex = (r'.*ip igmp static-oif route-map\s+'
                           r'(?P<route_map>\S+).*')
        prefix_source_regex = (r'.*ip igmp static-oif\s+(?P<prefix>'
                               r'((\d+.){3}\d+))(\ssource\s'
                               r'(?P<source>\S+))?.*')

        for line in split_body:
            temp = {}
            try:
                match_route_map = re.match(route_map_regex, line, re.DOTALL)
                route_map = match_route_map.groupdict()['route_map']
            except AttributeError:
                route_map = ''

            try:
                match_prefix_source = re.match(
                    prefix_source_regex, line, re.DOTALL)
                prefix_source_group = match_prefix_source.groupdict()
                prefix = prefix_source_group['prefix']
                source = prefix_source_group['source']
            except AttributeError:
                prefix = ''
                source = ''

            if route_map:
                temp['route_map'] = route_map
            if prefix:
                temp['prefix'] = prefix
            if source:
                temp['source'] = source
            if temp:
                staticoif.append(temp)

    igmp['oif_routemap'] = None
    igmp['oif_prefix_source'] = []

    if staticoif:
        if len(staticoif) == 1 and staticoif[0].get('route_map'):
            igmp['oif_routemap'] = staticoif[0]['route_map']
        else:
            igmp['oif_prefix_source'] = staticoif

    return igmp


def config_igmp_interface(delta, existing, existing_oif_prefix_source):
    CMDS = {
        'version': 'ip igmp version {0}',
        'startup_query_interval': 'ip igmp startup-query-interval {0}',
        'startup_query_count': 'ip igmp startup-query-count {0}',
        'robustness': 'ip igmp robustness-variable {0}',
        'querier_timeout': 'ip igmp querier-timeout {0}',
        'query_mrt': 'ip igmp query-max-response-time {0}',
        'query_interval': 'ip igmp query-interval {0}',
        'last_member_qrt': 'ip igmp last-member-query-response-time {0}',
        'last_member_query_count': 'ip igmp last-member-query-count {0}',
        'group_timeout': 'ip igmp group-timeout {0}',
        'report_llg': 'ip igmp report-link-local-groups',
        'immediate_leave': 'ip igmp immediate-leave',
        'oif_prefix_source': 'ip igmp static-oif {0} source {1} ',
        'oif_routemap': 'ip igmp static-oif route-map {0}',
        'oif_prefix': 'ip igmp static-oif {0}',
    }

    commands = []
    command = None
    def_vals = get_igmp_interface_defaults()

    for key, value in delta.items():
        if key == 'oif_ps' and value != 'default':
            for each in value:
                if each in existing_oif_prefix_source:
                    existing_oif_prefix_source.remove(each)
                else:
                    # add new prefix/sources
                    pf = each['prefix']
                    src = ''
                    if 'source' in each.keys():
                        src = each['source']
                    if src:
                        commands.append(CMDS.get('oif_prefix_source').format(pf, src))
                    else:
                        commands.append(CMDS.get('oif_prefix').format(pf))
            if existing_oif_prefix_source:
                for each in existing_oif_prefix_source:
                    # remove stale prefix/sources
                    pf = each['prefix']
                    src = ''
                    if 'source' in each.keys():
                        src = each['source']
                    if src:
                        commands.append('no ' + CMDS.get('oif_prefix_source').format(pf, src))
                    else:
                        commands.append('no ' + CMDS.get('oif_prefix').format(pf))
        elif key == 'oif_routemap':
            if value == 'default':
                if existing.get(key):
                    command = 'no ' + CMDS.get(key).format(existing.get(key))
            else:
                command = CMDS.get(key).format(value)
        elif value:
            if value == 'default':
                if def_vals.get(key) != existing.get(key):
                    command = CMDS.get(key).format(def_vals.get(key))
            else:
                command = CMDS.get(key).format(value)
        elif not value:
            command = 'no {0}'.format(CMDS.get(key).format(value))

        if command:
            if command not in commands:
                commands.append(command)
        command = None

    return commands


def get_igmp_interface_defaults():
    version = '2'
    startup_query_interval = '31'
    startup_query_count = '2'
    robustness = '2'
    querier_timeout = '255'
    query_mrt = '10'
    query_interval = '125'
    last_member_qrt = '1'
    last_member_query_count = '2'
    group_timeout = '260'
    report_llg = False
    immediate_leave = False

    args = dict(version=version, startup_query_interval=startup_query_interval,
                startup_query_count=startup_query_count, robustness=robustness,
                querier_timeout=querier_timeout, query_mrt=query_mrt,
                query_interval=query_interval, last_member_qrt=last_member_qrt,
                last_member_query_count=last_member_query_count,
                group_timeout=group_timeout, report_llg=report_llg,
                immediate_leave=immediate_leave)

    default = dict((param, value) for (param, value) in args.items()
                   if value is not None)

    return default


def config_default_igmp_interface(existing, delta):
    commands = []
    proposed = get_igmp_interface_defaults()
    delta = dict(set(proposed.items()).difference(existing.items()))
    if delta:
        command = config_igmp_interface(delta, existing, existing_oif_prefix_source=None)

        if command:
            for each in command:
                commands.append(each)

    return commands


def config_remove_oif(existing, existing_oif_prefix_source):
    commands = []
    command = None
    if existing.get('oif_routemap'):
        commands.append('no ip igmp static-oif route-map {0}'.format(existing.get('oif_routemap')))
    elif existing_oif_prefix_source:
        for each in existing_oif_prefix_source:
            if each.get('prefix') and each.get('source'):
                command = 'no ip igmp static-oif {0} source {1} '.format(
                    each.get('prefix'), each.get('source')
                )
            elif each.get('prefix'):
                command = 'no ip igmp static-oif {0}'.format(
                    each.get('prefix')
                )
            if command:
                commands.append(command)
            command = None

    return commands


def main():
    argument_spec = dict(
        interface=dict(required=True, type='str'),
        version=dict(required=False, type='str'),
        startup_query_interval=dict(required=False, type='str'),
        startup_query_count=dict(required=False, type='str'),
        robustness=dict(required=False, type='str'),
        querier_timeout=dict(required=False, type='str'),
        query_mrt=dict(required=False, type='str'),
        query_interval=dict(required=False, type='str'),
        last_member_qrt=dict(required=False, type='str'),
        last_member_query_count=dict(required=False, type='str'),
        group_timeout=dict(required=False, type='str'),
        report_llg=dict(type='bool'),
        immediate_leave=dict(type='bool'),
        oif_routemap=dict(required=False, type='str'),
        oif_prefix=dict(required=False, type='str', removed_in_version='2.10'),
        oif_source=dict(required=False, type='str', removed_in_version='2.10'),
        oif_ps=dict(required=False, type='raw'),
        restart=dict(type='bool', default=False),
        state=dict(choices=['present', 'absent', 'default'],
                   default='present')
    )

    argument_spec.update(nxos_argument_spec)
    mutually_exclusive = [('oif_ps', 'oif_prefix'),
                          ('oif_ps', 'oif_source'),
                          ('oif_ps', 'oif_routemap'),
                          ('oif_prefix', 'oif_routemap')]

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    state = module.params['state']
    interface = module.params['interface']
    oif_prefix = module.params['oif_prefix']
    oif_source = module.params['oif_source']
    oif_routemap = module.params['oif_routemap']
    oif_ps = module.params['oif_ps']

    if oif_source and not oif_prefix:
        module.fail_json(msg='oif_prefix required when setting oif_source')
    elif oif_source and oif_prefix:
        oif_ps = [{'source': oif_source, 'prefix': oif_prefix}]
    elif not oif_source and oif_prefix:
        oif_ps = [{'prefix': oif_prefix}]

    intf_type = get_interface_type(interface)
    if get_interface_mode(interface, intf_type, module) == 'layer2':
        module.fail_json(msg='this module only works on Layer 3 interfaces')

    existing = get_igmp_interface(module, interface)
    existing_copy = existing.copy()
    end_state = existing_copy

    if not existing.get('version'):
        module.fail_json(msg='pim needs to be enabled on the interface')

    existing_oif_prefix_source = existing.get('oif_prefix_source')
    # not json serializable
    existing.pop('oif_prefix_source')

    if oif_routemap and existing_oif_prefix_source:
        module.fail_json(msg='Delete static-oif configurations on this '
                             'interface if you want to use a routemap')

    if oif_ps and existing.get('oif_routemap'):
        module.fail_json(msg='Delete static-oif route-map configuration '
                             'on this interface if you want to config '
                             'static entries')

    args = [
        'version',
        'startup_query_interval',
        'startup_query_count',
        'robustness',
        'querier_timeout',
        'query_mrt',
        'query_interval',
        'last_member_qrt',
        'last_member_query_count',
        'group_timeout',
        'report_llg',
        'immediate_leave',
        'oif_routemap',
    ]

    changed = False
    commands = []
    proposed = dict((k, v) for k, v in module.params.items()
                    if v is not None and k in args)

    CANNOT_ABSENT = ['version', 'startup_query_interval',
                     'startup_query_count', 'robustness', 'querier_timeout',
                     'query_mrt', 'query_interval', 'last_member_qrt',
                     'last_member_query_count', 'group_timeout', 'report_llg',
                     'immediate_leave']

    if state == 'absent':
        for each in CANNOT_ABSENT:
            if each in proposed:
                module.fail_json(msg='only params: oif_prefix, oif_source, '
                                     'oif_ps, oif_routemap can be used when '
                                     'state=absent')

    # delta check for all params except oif_ps
    delta = dict(set(proposed.items()).difference(existing.items()))

    if oif_ps:
        if oif_ps == 'default':
            delta['oif_ps'] = []
        else:
            delta['oif_ps'] = oif_ps

    if state == 'present':
        if delta:
            command = config_igmp_interface(delta, existing, existing_oif_prefix_source)
            if command:
                commands.append(command)

    elif state == 'default':
        command = config_default_igmp_interface(existing, delta)
        if command:
            commands.append(command)
    elif state == 'absent':
        command = None
        if existing.get('oif_routemap') or existing_oif_prefix_source:
            command = config_remove_oif(existing, existing_oif_prefix_source)

        if command:
            commands.append(command)

        command = config_default_igmp_interface(existing, delta)
        if command:
            commands.append(command)

    cmds = []
    results = {}
    if commands:
        commands.insert(0, ['interface {0}'.format(interface)])
        cmds = flatten_list(commands)

        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            load_config(module, cmds)
            changed = True
            end_state = get_igmp_interface(module, interface)
            if 'configure' in cmds:
                cmds.pop(0)

    if module.params['restart']:
        cmd = {'command': 'restart igmp', 'output': 'text'}
        run_commands(module, cmd)

    results['proposed'] = proposed
    results['existing'] = existing_copy
    results['updates'] = cmds
    results['changed'] = changed
    results['warnings'] = warnings
    results['end_state'] = end_state

    module.exit_json(**results)


if __name__ == '__main__':
    main()
