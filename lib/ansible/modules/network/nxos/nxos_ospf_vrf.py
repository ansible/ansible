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
    required: false
    default: default
  ospf:
    description:
      - Name of the OSPF instance.
    required: true
    default: null
  router_id:
    description:
      - Router Identifier (ID) of the OSPF router VRF instance.
    required: false
    default: null
  default_metric:
    description:
      - Specify the default Metric value. Valid values are an integer
        or the keyword 'default'.
    required: false
    default: null
  log_adjacency:
    description:
      - Controls the level of log messages generated whenever a
        neighbor changes state. Valid values are 'log', 'detail',
        and 'default'.
    required: false
    choices: ['log','detail','default']
    default: null
  timer_throttle_lsa_start:
    description:
      - Specify the start interval for rate-limiting Link-State
        Advertisement (LSA) generation. Valid values are an integer,
        in milliseconds, or the keyword 'default'.
    required: false
    default: null
  timer_throttle_lsa_hold:
    description:
      - Specify the hold interval for rate-limiting Link-State
        Advertisement (LSA) generation. Valid values are an integer,
        in milliseconds, or the keyword 'default'.
    required: false
    default: null
  timer_throttle_lsa_max:
    description:
      - Specify the max interval for rate-limiting Link-State
        Advertisement (LSA) generation. Valid values are an integer,
        in milliseconds, or the keyword 'default'.
    required: false
    default: null
  timer_throttle_spf_start:
    description:
      - Specify initial Shortest Path First (SPF) schedule delay.
        Valid values are an integer, in milliseconds, or
        the keyword 'default'.
    required: false
    default: null
  timer_throttle_spf_hold:
    description:
      - Specify minimum hold time between Shortest Path First (SPF)
        calculations. Valid values are an integer, in milliseconds,
        or the keyword 'default'.
    required: false
    default: null
  timer_throttle_spf_max:
    description:
      - Specify the maximum wait time between Shortest Path First (SPF)
        calculations. Valid values are an integer, in milliseconds,
        or the keyword 'default'.
    required: false
    default: null
  auto_cost:
    description:
      - Specifies the reference bandwidth used to assign OSPF cost.
        Valid values are an integer, in Mbps, or the keyword 'default'.
    required: false
    default: null
  passive_interface:
    description:
      - Setting to true will suppress routing update on interface.
        Valid values are 'true' and 'false'.
    version_added: "2.4"
    required: false
    choices: ['true','false']
    default: null
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
    state: present
'''

RETURN = '''
commands:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["router ospf 1", "vrf test", "timers throttle lsa 60 1100 3000",
             "ospf 1", "timers throttle spf 50 1000 2000", "vrf test"]
'''

import re
from ansible.module_utils.nxos import get_config, load_config
from ansible.module_utils.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.netcfg import CustomNetworkConfig


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
    'passive_interface': 'passive-interface default'
}
PARAM_TO_DEFAULT_KEYMAP = {
    'timer_throttle_lsa_start': '0',
    'timer_throttle_lsa_max': '5000',
    'timer_throttle_lsa_hold': '5000',
    'timer_throttle_spf_start': '200',
    'timer_throttle_spf_max': '5000',
    'timer_throttle_spf_hold': '1000',
    'auto_cost': '40000'
}


def get_value(arg, config, module):
    command = PARAM_TO_COMMAND_KEYMAP.get(arg)
    command_re = re.compile(r'(?:{0}\s)(?P<value>.*)$'.format(command), re.M)
    value = ''

    if command in config:
        if arg == 'log_adjacency':
            if 'log-adjacency-changes detail' in config:
                value = 'detail'
            else:
                value = 'log'
        elif arg == 'passive_interface':
            if 'passive-interface default' in config:
                value = True
            else:
                value = False
        else:
            value_list = command_re.search(config).group('value').split()
            if 'hold' in arg:
                value = value_list[1]
            elif 'max' in arg:
                value = value_list[2]
            elif 'auto' in arg:
                if 'Gbps' in value_list:
                    value = str(int(value_list[0]) * 1000)
                else:
                    value = value_list[0]
            else:
                value = value_list[0]
    return value


def get_existing(module, args):
    existing = {}
    netcfg = CustomNetworkConfig(indent=2, contents=get_config(module))
    parents = ['router ospf {0}'.format(module.params['ospf'])]

    if module.params['vrf'] != 'default':
        parents.append('vrf {0}'.format(module.params['vrf']))

    config = netcfg.get_section(parents)
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

        for arg in args:
            if arg not in ['ospf', 'vrf']:
                existing[arg] = get_value(arg, config, module)

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


def state_present(module, existing, proposed, candidate):
    commands = list()
    proposed_commands = apply_key_map(PARAM_TO_COMMAND_KEYMAP, proposed)
    existing_commands = apply_key_map(PARAM_TO_COMMAND_KEYMAP, existing)

    for key, value in proposed_commands.items():
        if value is True:
            commands.append(key)

        elif value is False:
            if key == 'passive-interface default':
                if existing_commands.get(key):
                    commands.append('no {0}'.format(key))
            else:
                commands.append('no {0}'.format(key))

        elif value == 'default':
            if existing_commands.get(key):
                existing_value = existing_commands.get(key)
                commands.append('no {0} {1}'.format(key, existing_value))
        else:
            if key == 'timers throttle lsa':
                command = '{0} {1} {2} {3}'.format(
                    key,
                    proposed['timer_throttle_lsa_start'],
                    proposed['timer_throttle_lsa_hold'],
                    proposed['timer_throttle_lsa_max'])
            elif key == 'timers throttle spf':
                command = '{0} {1} {2} {3}'.format(
                    key,
                    proposed['timer_throttle_spf_start'],
                    proposed['timer_throttle_spf_hold'],
                    proposed['timer_throttle_spf_max'])
            elif key == 'log-adjacency-changes':
                if value == 'log':
                    command = key
                elif value == 'detail':
                    command = '{0} {1}'.format(key, value)
            elif key == 'auto-cost reference-bandwidth':
                if len(value) < 5:
                    command = '{0} {1} Mbps'.format(key, value)
                else:
                    value = str(int(value) / 1000)
                    command = '{0} {1} Gbps'.format(key, value)
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
                if key == 'passive-interface default':
                    command = 'no {0}'.format(key)
                elif key == 'timers throttle lsa':
                    command = 'no {0} {1} {2} {3}'.format(
                        key,
                        existing['timer_throttle_lsa_start'],
                        existing['timer_throttle_lsa_hold'],
                        existing['timer_throttle_lsa_max'])
                elif key == 'timers throttle spf':
                    command = 'no {0} {1} {2} {3}'.format(
                        key,
                        existing['timer_throttle_spf_start'],
                        existing['timer_throttle_spf_hold'],
                        existing['timer_throttle_spf_max'])
                else:
                    existing_value = existing_commands.get(key)
                    command = 'no {0} {1}'.format(key, existing_value)

                if command not in commands:
                    commands.append(command)
    else:
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
        passive_interface=dict(required=False, type='bool'),
        state=dict(choices=['present', 'absent'], default='present', required=False),
        include_defaults=dict(default=True),
        config=dict(),
        save=dict(type='bool', default=False)
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)
    result = dict(changed=False, warnings=warnings)

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
        load_config(module, candidate)
        result['changed'] = True
        result['commands'] = candidate

    else:
        result['commands'] = []
    module.exit_json(**result)


if __name__ == '__main__':
    main()
