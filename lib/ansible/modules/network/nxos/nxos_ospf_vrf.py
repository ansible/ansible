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
module: nxos_ospf_vrf
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages a VRF for an OSPF router.
description:
  - Manages a VRF for an OSPF router.
author: Gabriele Gerbino (@GGabriele)
notes:
  - Tested against NXOSv 7.3.(0)D1(1) on VIRL
  - Value I(default) restores params default value, if any.
    Otherwise it removes the existing param configuration.
options:
  vrf:
    description:
      - Name of the resource instance. Valid value is a string.
        The name 'default' is a valid VRF representing the global OSPF.
    default: default
  ospf:
    description:
      - Name of the OSPF instance.
    required: true
  router_id:
    description:
      - Router Identifier (ID) of the OSPF router VRF instance.
  default_metric:
    description:
      - Specify the default Metric value. Valid values are an integer
        or the keyword 'default'.
  log_adjacency:
    description:
      - Controls the level of log messages generated whenever a
        neighbor changes state. Valid values are 'log', 'detail',
        and 'default'.
    choices: ['log','detail','default']
  timer_throttle_lsa_start:
    description:
      - Specify the start interval for rate-limiting Link-State
        Advertisement (LSA) generation. Valid values are an integer,
        in milliseconds, or the keyword 'default'.
  timer_throttle_lsa_hold:
    description:
      - Specify the hold interval for rate-limiting Link-State
        Advertisement (LSA) generation. Valid values are an integer,
        in milliseconds, or the keyword 'default'.
  timer_throttle_lsa_max:
    description:
      - Specify the max interval for rate-limiting Link-State
        Advertisement (LSA) generation. Valid values are an integer,
        in milliseconds, or the keyword 'default'.
  timer_throttle_spf_start:
    description:
      - Specify initial Shortest Path First (SPF) schedule delay.
        Valid values are an integer, in milliseconds, or
        the keyword 'default'.
  timer_throttle_spf_hold:
    description:
      - Specify minimum hold time between Shortest Path First (SPF)
        calculations. Valid values are an integer, in milliseconds,
        or the keyword 'default'.
  timer_throttle_spf_max:
    description:
      - Specify the maximum wait time between Shortest Path First (SPF)
        calculations. Valid values are an integer, in milliseconds,
        or the keyword 'default'.
  auto_cost:
    description:
      - Specifies the reference bandwidth used to assign OSPF cost.
        Valid values are an integer, in Mbps, or the keyword 'default'.
  bfd:
    description:
      - Enables BFD on all OSPF interfaces.
      - "Dependency: 'feature bfd'"
    version_added: "2.9"
    type: str
    choices: ['enable', 'disable']
  passive_interface:
    description:
      - Setting to C(yes) will suppress routing update on interface.
    version_added: "2.4"
    type: bool
  state:
    description:
      - State of ospf vrf configuration.
    default: present
    choices: ['present', 'absent']
'''

EXAMPLES = '''
- nxos_ospf_vrf:
    ospf: 1
    timer_throttle_spf_start: 50
    timer_throttle_spf_hold: 1000
    timer_throttle_spf_max: 2000
    timer_throttle_lsa_start: 60
    timer_throttle_lsa_hold: 1100
    timer_throttle_lsa_max: 3000
    vrf: test
    bfd: enable
    state: present
'''

RETURN = '''
commands:
    description: commands sent to the device
    returned: always
    type: list
    sample:
      - router ospf 1
      - vrf test
      - bfd
      - timers throttle lsa 60 1100 3000
'''

import re
from ansible.module_utils.network.nxos.nxos import get_config, load_config
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.config import CustomNetworkConfig


BOOL_PARAMS = [
    'passive_interface'
]
PARAM_TO_COMMAND_KEYMAP = {
    'vrf': 'vrf',
    'router_id': 'router-id',
    'default_metric': 'default-metric',
    'log_adjacency': 'log-adjacency-changes',
    'timer_throttle_lsa_start': 'timers throttle lsa',
    'timer_throttle_lsa_max': 'timers throttle lsa',
    'timer_throttle_lsa_hold': 'timers throttle lsa',
    'timer_throttle_spf_max': 'timers throttle spf',
    'timer_throttle_spf_start': 'timers throttle spf',
    'timer_throttle_spf_hold': 'timers throttle spf',
    'auto_cost': 'auto-cost reference-bandwidth',
    'bfd': 'bfd',
    'passive_interface': 'passive-interface default'
}
PARAM_TO_DEFAULT_KEYMAP = {
    'timer_throttle_lsa_start': '0',
    'timer_throttle_lsa_max': '5000',
    'timer_throttle_lsa_hold': '5000',
    'timer_throttle_spf_start': '200',
    'timer_throttle_spf_max': '5000',
    'timer_throttle_spf_hold': '1000',
    'auto_cost': '40000',
    'bfd': 'disable',
    'default_metric': '',
    'passive_interface': False,
    'router_id': '',
    'log_adjacency': '',
}


def get_existing(module, args):
    existing = {}
    netcfg = CustomNetworkConfig(indent=2, contents=get_config(module))
    parents = ['router ospf {0}'.format(module.params['ospf'])]

    if module.params['vrf'] != 'default':
        parents.append('vrf {0}'.format(module.params['vrf']))

    config = netcfg.get_section(parents)
    for arg in args:
        if arg not in ['ospf', 'vrf']:
            existing[arg] = PARAM_TO_DEFAULT_KEYMAP.get(arg)

    if config:
        if module.params['vrf'] == 'default':
            splitted_config = config.splitlines()
            vrf_index = False
            for index in range(0, len(splitted_config) - 1):
                if 'vrf' in splitted_config[index].strip():
                    vrf_index = index
                    break
            if vrf_index:
                config = '\n'.join(splitted_config[0:vrf_index])

        splitted_config = config.splitlines()
        for line in splitted_config:
            if 'passive' in line:
                existing['passive_interface'] = True
            elif 'router-id' in line:
                existing['router_id'] = re.search(r'router-id (\S+)', line).group(1)
            elif 'metric' in line:
                existing['default_metric'] = re.search(r'default-metric (\S+)', line).group(1)
            elif 'adjacency' in line:
                log = re.search(r'log-adjacency-changes(?: (\S+))?', line).group(1)
                if log:
                    existing['log_adjacency'] = log
                else:
                    existing['log_adjacency'] = 'log'
            elif 'auto' in line:
                cost = re.search(r'auto-cost reference-bandwidth (\d+) (\S+)', line).group(1)
                if 'Gbps' in line:
                    cost = int(cost) * 1000
                existing['auto_cost'] = str(cost)
            elif 'bfd' in line:
                existing['bfd'] = 'enable'
            elif 'timers throttle lsa' in line:
                tmp = re.search(r'timers throttle lsa (\S+) (\S+) (\S+)', line)
                existing['timer_throttle_lsa_start'] = tmp.group(1)
                existing['timer_throttle_lsa_hold'] = tmp.group(2)
                existing['timer_throttle_lsa_max'] = tmp.group(3)
            elif 'timers throttle spf' in line:
                tmp = re.search(r'timers throttle spf (\S+) (\S+) (\S+)', line)
                existing['timer_throttle_spf_start'] = tmp.group(1)
                existing['timer_throttle_spf_hold'] = tmp.group(2)
                existing['timer_throttle_spf_max'] = tmp.group(3)
        existing['vrf'] = module.params['vrf']
        existing['ospf'] = module.params['ospf']

    return existing


def apply_key_map(key_map, table):
    new_dict = {}
    for key in table:
        new_key = key_map.get(key)
        if new_key:
            new_dict[new_key] = table.get(key)
    return new_dict


def get_timer_prd(key, proposed):
    if proposed.get(key):
        return proposed.get(key)
    else:
        return PARAM_TO_DEFAULT_KEYMAP.get(key)


def state_present(module, existing, proposed, candidate):
    commands = list()
    proposed_commands = apply_key_map(PARAM_TO_COMMAND_KEYMAP, proposed)
    existing_commands = apply_key_map(PARAM_TO_COMMAND_KEYMAP, existing)

    for key, value in proposed_commands.items():
        if key == 'vrf':
            continue
        if value is True:
            commands.append(key)

        elif value is False:
            if key == 'passive-interface default':
                if existing_commands.get(key):
                    commands.append('no {0}'.format(key))
            else:
                commands.append('no {0}'.format(key))

        elif value == 'default' or value == '':
            if key == 'log-adjacency-changes':
                commands.append('no {0}'.format(key))
            elif existing_commands.get(key):
                existing_value = existing_commands.get(key)
                commands.append('no {0} {1}'.format(key, existing_value))
        else:
            if key == 'timers throttle lsa':
                command = '{0} {1} {2} {3}'.format(
                    key,
                    get_timer_prd('timer_throttle_lsa_start', proposed),
                    get_timer_prd('timer_throttle_lsa_hold', proposed),
                    get_timer_prd('timer_throttle_lsa_max', proposed))
            elif key == 'timers throttle spf':
                command = '{0} {1} {2} {3}'.format(
                    key,
                    get_timer_prd('timer_throttle_spf_start', proposed),
                    get_timer_prd('timer_throttle_spf_hold', proposed),
                    get_timer_prd('timer_throttle_spf_max', proposed))
            elif key == 'log-adjacency-changes':
                if value == 'log':
                    command = key
                elif value == 'detail':
                    command = '{0} {1}'.format(key, value)
            elif key == 'auto-cost reference-bandwidth':
                if len(value) < 5:
                    command = '{0} {1} Mbps'.format(key, value)
                else:
                    value = str(int(value) // 1000)
                    command = '{0} {1} Gbps'.format(key, value)
            elif key == 'bfd':
                command = 'no bfd' if value == 'disable' else 'bfd'
            else:
                command = '{0} {1}'.format(key, value.lower())

            if command not in commands:
                commands.append(command)

    if commands:
        parents = ['router ospf {0}'.format(module.params['ospf'])]
        if module.params['vrf'] != 'default':
            parents.append('vrf {0}'.format(module.params['vrf']))
        candidate.add(commands, parents=parents)


def state_absent(module, existing, proposed, candidate):
    commands = []
    parents = ['router ospf {0}'.format(module.params['ospf'])]
    if module.params['vrf'] == 'default':
        existing_commands = apply_key_map(PARAM_TO_COMMAND_KEYMAP, existing)
        for key, value in existing_commands.items():
            if value and key != 'vrf':
                command = None
                if key == 'passive-interface default':
                    command = 'no {0}'.format(key)
                elif key == 'timers throttle lsa':
                    if (existing['timer_throttle_lsa_start'] !=
                        PARAM_TO_DEFAULT_KEYMAP.get('timer_throttle_lsa_start') or
                        existing['timer_throttle_lsa_hold'] !=
                        PARAM_TO_DEFAULT_KEYMAP.get('timer_throttle_lsa_hold') or
                        existing['timer_throttle_lsa_max'] !=
                            PARAM_TO_DEFAULT_KEYMAP.get('timer_throttle_lsa_max')):
                        command = 'no {0} {1} {2} {3}'.format(
                            key,
                            existing['timer_throttle_lsa_start'],
                            existing['timer_throttle_lsa_hold'],
                            existing['timer_throttle_lsa_max'])
                elif key == 'timers throttle spf':
                    if (existing['timer_throttle_spf_start'] !=
                        PARAM_TO_DEFAULT_KEYMAP.get('timer_throttle_spf_start') or
                        existing['timer_throttle_spf_hold'] !=
                        PARAM_TO_DEFAULT_KEYMAP.get('timer_throttle_spf_hold') or
                        existing['timer_throttle_spf_max'] !=
                            PARAM_TO_DEFAULT_KEYMAP.get('timer_throttle_spf_max')):
                        command = 'no {0} {1} {2} {3}'.format(
                            key,
                            existing['timer_throttle_spf_start'],
                            existing['timer_throttle_spf_hold'],
                            existing['timer_throttle_spf_max'])
                elif key == 'log-adjacency-changes':
                    command = 'no {0}'.format(key)
                elif key == 'auto-cost reference-bandwidth':
                    if value != PARAM_TO_DEFAULT_KEYMAP.get('auto_cost'):
                        command = 'no {0}'.format(key)
                    else:
                        command = None
                elif key == 'bfd':
                    if value == 'enable':
                        command = 'no bfd'
                else:
                    existing_value = existing_commands.get(key)
                    command = 'no {0} {1}'.format(key, existing_value)

                if command:
                    if command not in commands:
                        commands.append(command)
    else:
        if (existing.get('vrf') and
                existing.get('vrf') == module.params['vrf']):
            commands = ['no vrf {0}'.format(module.params['vrf'])]

    if commands:
        candidate.add(commands, parents=parents)


def main():
    argument_spec = dict(
        vrf=dict(required=False, type='str', default='default'),
        ospf=dict(required=True, type='str'),
        router_id=dict(required=False, type='str'),
        default_metric=dict(required=False, type='str'),
        log_adjacency=dict(required=False, type='str', choices=['log', 'detail', 'default']),
        timer_throttle_lsa_start=dict(required=False, type='str'),
        timer_throttle_lsa_hold=dict(required=False, type='str'),
        timer_throttle_lsa_max=dict(required=False, type='str'),
        timer_throttle_spf_start=dict(required=False, type='str'),
        timer_throttle_spf_hold=dict(required=False, type='str'),
        timer_throttle_spf_max=dict(required=False, type='str'),
        auto_cost=dict(required=False, type='str'),
        bfd=dict(required=False, type='str', choices=['enable', 'disable']),
        passive_interface=dict(required=False, type='bool'),
        state=dict(choices=['present', 'absent'], default='present', required=False)
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)
    result = dict(changed=False, commands=[], warnings=warnings)

    state = module.params['state']
    args = PARAM_TO_COMMAND_KEYMAP.keys()
    existing = get_existing(module, args)
    proposed_args = dict((k, v) for k, v in module.params.items()
                         if v is not None and k in args)

    proposed = {}
    for key, value in proposed_args.items():
        if key != 'interface':
            if str(value).lower() == 'true':
                value = True
            elif str(value).lower() == 'false':
                value = False
            elif str(value).lower() == 'default':
                value = PARAM_TO_DEFAULT_KEYMAP.get(key)
                if value is None:
                    value = 'default'
            if existing.get(key) != value:
                proposed[key] = value

    candidate = CustomNetworkConfig(indent=3)
    if state == 'present':
        state_present(module, existing, proposed, candidate)
    if state == 'absent' and existing:
        state_absent(module, existing, proposed, candidate)

    if candidate:
        candidate = candidate.items_text()
        result['commands'] = candidate
        if not module.check_mode:
            load_config(module, candidate)
            result['changed'] = True
    module.exit_json(**result)


if __name__ == '__main__':
    main()
