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
module: nxos_vxlan_vtep
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages VXLAN Network Virtualization Endpoint (NVE).
description:
  - Manages VXLAN Network Virtualization Endpoint (NVE) overlay interface
    that terminates VXLAN tunnels.
author: Gabriele Gerbino (@GGabriele)
notes:
  - Tested against NXOSv 7.3.(0)D1(1) on VIRL
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
  host_reachability:
    description:
      - Specify mechanism for host reachability advertisement.
    type: bool
  shutdown:
    description:
      - Administratively shutdown the NVE interface.
    type: bool
  source_interface:
    description:
      - Specify the loopback interface whose IP address should be
        used for the NVE interface.
  source_interface_hold_down_time:
    description:
      - Suppresses advertisement of the NVE loopback address until
        the overlay has converged.
  global_mcast_group_L3:
    description:
      - Global multicast ip prefix for L3 VNIs or the keyword 'default'
        This is available on NX-OS 9K series running 9.2.x or higher.
    version_added: "2.8"
  global_mcast_group_L2:
    description:
      - Global multicast ip prefix for L2 VNIs or the keyword 'default'
        This is available on NX-OS 9K series running 9.2.x or higher.
    version_added: "2.8"
  global_suppress_arp:
    description:
      - Enables ARP suppression for all VNIs
        This is available on NX-OS 9K series running 9.2.x or higher.
    type: bool
    version_added: "2.8"
  global_ingress_replication_bgp:
    description:
      - Configures ingress replication protocol as bgp for all VNIs
        This is available on NX-OS 9K series running 9.2.x or higher.
    type: bool
    version_added: "2.8"
  state:
    description:
      - Determines whether the config should be present or not
        on the device.
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
'''

RETURN = '''
commands:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["interface nve1", "source-interface loopback0",
        "source-interface hold-down-time 30", "description simple description",
        "shutdown", "host-reachability protocol bgp"]
'''

import re

from ansible.module_utils.network.nxos.nxos import get_config, load_config
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec, check_args
from ansible.module_utils.network.nxos.nxos import run_commands
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.config import CustomNetworkConfig

BOOL_PARAMS = [
    'shutdown',
    'host_reachability',
    'global_ingress_replication_bgp',
    'global_suppress_arp',
]
PARAM_TO_COMMAND_KEYMAP = {
    'description': 'description',
    'global_suppress_arp': 'global suppress-arp',
    'global_ingress_replication_bgp': 'global ingress-replication protocol bgp',
    'global_mcast_group_L3': 'global mcast-group L3',
    'global_mcast_group_L2': 'global mcast-group L2',
    'host_reachability': 'host-reachability protocol bgp',
    'interface': 'interface',
    'shutdown': 'shutdown',
    'source_interface': 'source-interface',
    'source_interface_hold_down_time': 'source-interface hold-down-time'
}
PARAM_TO_DEFAULT_KEYMAP = {
    'description': False,
    'shutdown': True,
    'source_interface_hold_down_time': '180',
}


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
                value = False
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
        elif arg == 'global_mcast_group_L2':
            for line in config.splitlines():
                try:
                    if 'global mcast-group' in line and 'L2' in line:
                        value = line.split()[2].strip()
                        break
                except AttributeError:
                    value = ''
        elif arg == 'global_mcast_group_L3':
            for line in config.splitlines():
                try:
                    if 'global mcast-group' in line and 'L3' in line:
                        value = line.split()[2].strip()
                        break
                except AttributeError:
                    value = ''
        else:
            if PARAM_TO_COMMAND_KEYMAP[arg] in config:
                value = REGEX.search(config).group('value').strip()
    return value


def get_existing(module, args):
    existing = {}
    netcfg = CustomNetworkConfig(indent=2, contents=get_config(module, flags=['all']))

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
    no_host_reachability_command = ''
    host_reachability_command = ''

    for command in commands:
        if 'no source-interface hold-down-time' in command:
            pass
        elif 'source-interface hold-down-time' in command:
            pass
        elif 'no source-interface' in command:
            no_source_interface_command = command
        elif 'source-interface' in command:
            source_interface_command = command
        elif 'no host-reachability' in command:
            no_host_reachability_command = command
        elif 'host-reachability' in command:
            host_reachability_command = command

    if host_reachability_command:
        commands.pop(commands.index(host_reachability_command))
        commands.insert(0, host_reachability_command)

    if source_interface_command:
        commands.pop(commands.index(source_interface_command))
        commands.insert(0, source_interface_command)

    if no_host_reachability_command:
        commands.pop(commands.index(no_host_reachability_command))
        commands.append(no_host_reachability_command)

    if no_source_interface_command:
        commands.pop(commands.index(no_source_interface_command))
        commands.append(no_source_interface_command)

    commands.insert(0, 'terminal dont-ask')
    return commands


def gsa_tcam_check(module):
    '''
    global_suppress_arp is an N9k-only command that requires TCAM resources.
    This method checks the current TCAM allocation.
    Note that changing tcam_size requires a switch reboot to take effect.
    '''
    cmds = [{'command': 'show hardware access-list tcam region', 'output': 'json'}]
    body = run_commands(module, cmds)
    if body:
        tcam_region = body[0]['TCAM_Region']['TABLE_Sizes']['ROW_Sizes']
        if bool([i for i in tcam_region if i['type'].startswith('Ingress ARP-Ether ACL') and i['tcam_size'] == '0']):
            msg = "'show hardware access-list tcam region' indicates 'ARP-Ether' tcam size is 0 (no allocated resources). " +\
                  "'global_suppress_arp' will be rejected by device."
            module.fail_json(msg=msg)


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
                if 'global mcast-group' in key:
                    commands.append('no {0}'.format(key))
                else:
                    commands.append('no {0} {1}'.format(key, existing_value))
            else:
                if key.replace(' ', '_').replace('-', '_') in BOOL_PARAMS:
                    commands.append('no {0}'.format(key.lower()))
                    module.exit_json(commands=commands)
        else:
            if 'L2' in key:
                commands.append('global mcast-group ' + value + ' L2')
            elif 'L3' in key:
                commands.append('global mcast-group ' + value + ' L3')
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
        global_ingress_replication_bgp=dict(required=False, type='bool'),
        global_suppress_arp=dict(required=False, type='bool'),
        global_mcast_group_L2=dict(required=False, type='str'),
        global_mcast_group_L3=dict(required=False, type='str'),
        shutdown=dict(required=False, type='bool'),
        source_interface=dict(required=False, type='str'),
        source_interface_hold_down_time=dict(required=False, type='str'),
        state=dict(choices=['present', 'absent'], default='present', required=False),
    )

    argument_spec.update(nxos_argument_spec)

    mutually_exclusive = [('global_ingress_replication_bgp', 'global_mcast_group_L2')]

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=mutually_exclusive,
        supports_check_mode=True,
    )

    warnings = list()
    result = {'changed': False, 'commands': [], 'warnings': warnings}
    check_args(module, warnings)

    state = module.params['state']

    args = PARAM_TO_COMMAND_KEYMAP.keys()

    existing = get_existing(module, args)
    proposed_args = dict((k, v) for k, v in module.params.items()
                         if v is not None and k in args)
    proposed = {}
    for key, value in proposed_args.items():
        if key != 'interface':
            if str(value).lower() == 'default':
                value = PARAM_TO_DEFAULT_KEYMAP.get(key)
                if value is None:
                    if key in BOOL_PARAMS:
                        value = False
                    else:
                        value = 'default'
            if str(existing.get(key)).lower() != str(value).lower():
                proposed[key] = value

    candidate = CustomNetworkConfig(indent=3)

    if proposed.get('global_suppress_arp'):
        gsa_tcam_check(module)
    if state == 'present':
        if not existing:
            warnings.append("The proposed NVE interface did not exist. "
                            "It's recommended to use nxos_interface to create "
                            "all logical interfaces.")
        state_present(module, existing, proposed, candidate)
    elif state == 'absent' and existing:
        state_absent(module, existing, proposed, candidate)

    if candidate:
        candidate = candidate.items_text()
        result['commands'] = candidate
        result['changed'] = True
        load_config(module, candidate)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
