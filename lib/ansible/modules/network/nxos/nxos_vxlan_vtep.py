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
module: nxos_vxlan_vtep
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages VXLAN Network Virtualization Endpoint (NVE).
description:
    - Manages VXLAN Network Virtualization Endpoint (NVE) overlay interface
      that terminates VXLAN tunnels.
author: Gabriele Gerbino (@GGabriele)
notes:
    - The module is used to manage NVE properties, not to create NVE
      interfaces. Use M(nxos_interface) if you wish to do so.
    - C(state=absent) removes the interface.
    - Default, where supported, restores params default value.
options:
    interface:
        description:
            - Interface name for the VXLAN Network Virtualization Endpoint.
        required: true
    description:
        description:
            - Description of the NVE interface.
        required: false
        default: null
    host_reachability:
        description:
            - Specify mechanism for host reachability advertisement.
        required: false
        choices: ['true', 'false']
        default: null
    shutdown:
        description:
            - Administratively shutdown the NVE interface.
        required: false
        choices: ['true','false']
        default: false
    source_interface:
        description:
            - Specify the loopback interface whose IP address should be
              used for the NVE interface.
        required: false
        default: null
    source_interface_hold_down_time:
        description:
            - Suppresses advertisement of the NVE loopback address until
              the overlay has converged.
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
- nxos_vxlan_vtep:
    interface: nve1
    description: default
    host_reachability: default
    source_interface: Loopback0
    source_interface_hold_down_time: 30
    shutdown: default
    username: "{{ un }}"
    password: "{{ pwd }}"
    host: "{{ inventory_hostname }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: verbose mode
    type: dict
    sample: {"description": "simple description", "host_reachability": true,
        "interface": "nve1", "shutdown": true, "source_interface": "loopback0",
        "source_interface_hold_down_time": "30"}
existing:
    description: k/v pairs of existing VXLAN VTEP configuration
    returned: verbose mode
    type: dict
    sample: {}
end_state:
    description: k/v pairs of VXLAN VTEP configuration after module execution
    returned: verbose mode
    type: dict
    sample: {"description": "simple description", "host_reachability": true,
        "interface": "nve1", "shutdown": true, "source_interface": "loopback0",
        "source_interface_hold_down_time": "30"}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["interface nve1", "source-interface loopback0",
        "source-interface hold-down-time 30", "description simple description",
        "shutdown", "host-reachability protocol bgp"]
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

BOOL_PARAMS = [
    'shutdown',
    'host_reachability'
]
PARAM_TO_COMMAND_KEYMAP = {
    'description': 'description',
    'host_reachability': 'host-reachability protocol bgp',
    'interface': 'interface',
    'shutdown': 'shutdown',
    'source_interface': 'source-interface',
    'source_interface_hold_down_time': 'source-interface hold-down-time'
}
PARAM_TO_DEFAULT_KEYMAP = {
    'description': False,
    'shutdown': True,
}

WARNINGS = []


def invoke(name, *args, **kwargs):
    func = globals().get(name)
    if func:
        return func(*args, **kwargs)


def get_value(arg, config, module):
    if arg in BOOL_PARAMS:
        REGEX = re.compile(r'\s+{0}\s*$'.format(PARAM_TO_COMMAND_KEYMAP[arg]), re.M)
        NO_SHUT_REGEX = re.compile(r'\s+no shutdown\s*$', re.M)
        value = False
        if arg == 'shutdown':
            try:
                if NO_SHUT_REGEX.search(config):
                    value = False
                elif REGEX.search(config):
                    value = True
            except TypeError:
                value = False
        else:
            try:
                if REGEX.search(config):
                    value = True
            except TypeError:
                value = False
    else:
        REGEX = re.compile(r'(?:{0}\s)(?P<value>.*)$'.format(PARAM_TO_COMMAND_KEYMAP[arg]), re.M)
        NO_DESC_REGEX = re.compile(r'\s+{0}\s*$'.format('no description'), re.M)
        SOURCE_INTF_REGEX = re.compile(r'(?:{0}\s)(?P<value>\S+)$'.format(PARAM_TO_COMMAND_KEYMAP[arg]), re.M)
        value = ''
        if arg == 'description':
            if NO_DESC_REGEX.search(config):
                value = ''
            elif PARAM_TO_COMMAND_KEYMAP[arg] in config:
                value = REGEX.search(config).group('value').strip()
        elif arg == 'source_interface':
            for line in config.splitlines():
                try:
                    if PARAM_TO_COMMAND_KEYMAP[arg] in config:
                        value = SOURCE_INTF_REGEX.search(config).group('value').strip()
                        break
                except AttributeError:
                    value = ''
        else:
            if PARAM_TO_COMMAND_KEYMAP[arg] in config:
                value = REGEX.search(config).group('value').strip()
    return value


def get_existing(module, args):
    existing = {}
    netcfg = CustomNetworkConfig(indent=2, contents=get_config(module))

    interface_string = 'interface {0}'.format(module.params['interface'].lower())
    parents = [interface_string]
    config = netcfg.get_section(parents)

    if config:
        for arg in args:
            existing[arg] = get_value(arg, config, module)

        existing['interface'] = module.params['interface'].lower()
    else:
        if interface_string in str(netcfg):
            existing['interface'] = module.params['interface'].lower()
            for arg in args:
                existing[arg] = ''
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


def fix_commands(commands, module):
    source_interface_command = ''
    no_source_interface_command = ''

    for command in commands:
        if 'no source-interface hold-down-time' in command:
            pass
        elif 'source-interface hold-down-time' in command:
            pass
        elif 'no source-interface' in command:
            no_source_interface_command = command
        elif 'source-interface' in command:
            source_interface_command = command

    if source_interface_command:
        commands.pop(commands.index(source_interface_command))
        commands.insert(0, source_interface_command)

    if no_source_interface_command:
        commands.pop(commands.index(no_source_interface_command))
        commands.append(no_source_interface_command)
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
            if existing_commands.get(key):
                existing_value = existing_commands.get(key)
                commands.append('no {0} {1}'.format(key, existing_value))
            else:
                if key.replace(' ', '_').replace('-', '_') in BOOL_PARAMS:
                    commands.append('no {0}'.format(key.lower()))
                    module.exit_json(commands=commands)
        else:
            command = '{0} {1}'.format(key, value.lower())
            commands.append(command)

    if commands:
        commands = fix_commands(commands, module)
        parents = ['interface {0}'.format(module.params['interface'].lower())]
        candidate.add(commands, parents=parents)
    else:
        if not existing and module.params['interface']:
            commands = ['interface {0}'.format(module.params['interface'].lower())]
            candidate.add(commands, parents=[])


def state_absent(module, existing, proposed, candidate):
    commands = ['no interface {0}'.format(module.params['interface'].lower())]
    candidate.add(commands, parents=[])


def main():
    argument_spec = dict(
        interface=dict(required=True, type='str'),
        description=dict(required=False, type='str'),
        host_reachability=dict(required=False, type='bool'),
        shutdown=dict(required=False, type='bool'),
        source_interface=dict(required=False, type='str'),
        source_interface_hold_down_time=dict(required=False, type='str'),
        m_facts=dict(required=False, default=False, type='bool'),
        state=dict(choices=['present', 'absent'], default='present',
                       required=False),
        include_defaults=dict(default=True),
        config=dict(),
        save=dict(type='bool', default=False)
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                                supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)


    state = module.params['state']
    interface = module.params['interface'].lower()

    args =  [
        'interface',
        'description',
        'host_reachability',
        'shutdown',
        'source_interface',
        'source_interface_hold_down_time'
    ]

    existing = invoke('get_existing', module, args)
    end_state = existing
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
                    if key in BOOL_PARAMS:
                        value = False
                    else:
                        value = 'default'
            if existing.get(key) or (not existing.get(key) and value):
                proposed[key] = value

    result = {}
    if state == 'present' or (state == 'absent' and existing):
        if not existing:
            WARNINGS.append("The proposed NVE interface did not exist. "
                            "It's recommended to use nxos_interface to create "
                            "all logical interfaces.")
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

