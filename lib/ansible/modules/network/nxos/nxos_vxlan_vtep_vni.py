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
module: nxos_vxlan_vtep_vni
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Creates a Virtual Network Identifier member (VNI)
description:
  - Creates a Virtual Network Identifier member (VNI) for an NVE
    overlay interface.
author: Gabriele Gerbino (@GGabriele)
notes:
  - Tested against NXOSv 7.3.(0)D1(1) on VIRL
  - default, where supported, restores params default value.
options:
  interface:
    description:
      - Interface name for the VXLAN Network Virtualization Endpoint.
    required: true
  vni:
    description:
      - ID of the Virtual Network Identifier.
    required: true
  assoc_vrf:
    description:
      - This attribute is used to identify and separate processing VNIs
        that are associated with a VRF and used for routing. The VRF
        and VNI specified with this command must match the configuration
        of the VNI under the VRF.
    type: bool
  ingress_replication:
    description:
      - Specifies mechanism for host reachability advertisement.
    choices: ['bgp','static', 'default']
  multicast_group:
    description:
      - The multicast group (range) of the VNI. Valid values are
        string and keyword 'default'.
  peer_list:
    description:
      - Set the ingress-replication static peer list. Valid values
        are an array, a space-separated string of ip addresses,
        or the keyword 'default'.
  suppress_arp:
    description:
      - Suppress arp under layer 2 VNI.
    type: bool
  state:
    description:
      - Determines whether the config should be present or not
        on the device.
    default: present
    choices: ['present','absent']
'''
EXAMPLES = '''
- nxos_vxlan_vtep_vni:
    interface: nve1
    vni: 6000
    ingress_replication: default
'''

RETURN = '''
commands:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["interface nve1", "member vni 6000"]
'''

import re
from ansible.module_utils.network.nxos.nxos import get_config, load_config
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.config import CustomNetworkConfig

BOOL_PARAMS = [
    'assoc_vrf',
    'suppress_arp',
]
PARAM_TO_DEFAULT_KEYMAP = {
    'multicast_group': '',
    'peer_list': [],
    'ingress_replication': '',
}
PARAM_TO_COMMAND_KEYMAP = {
    'assoc_vrf': 'associate-vrf',
    'interface': 'interface',
    'vni': 'member vni',
    'ingress_replication': 'ingress-replication protocol',
    'multicast_group': 'mcast-group',
    'peer_list': 'peer-ip',
    'suppress_arp': 'suppress-arp'
}


def get_value(arg, config, module):
    command = PARAM_TO_COMMAND_KEYMAP[arg]
    command_val_re = re.compile(r'(?:{0}\s)(?P<value>.*)$'.format(command), re.M)

    if arg in BOOL_PARAMS:
        command_re = re.compile(r'\s+{0}\s*$'.format(command), re.M)
        value = False
        if command_re.search(config):
            value = True
    elif arg == 'peer_list':
        has_command_val = command_val_re.findall(config, re.M)
        value = []
        if has_command_val:
            value = has_command_val
    else:
        value = ''
        has_command_val = command_val_re.search(config, re.M)
        if has_command_val:
            value = has_command_val.group('value')
    return value


def check_interface(module, netcfg):
    config = str(netcfg)

    has_interface = re.search(r'(?:interface nve)(?P<value>.*)$', config, re.M)
    value = ''
    if has_interface:
        value = 'nve{0}'.format(has_interface.group('value'))

    return value


def get_existing(module, args):
    existing = {}
    netcfg = CustomNetworkConfig(indent=2, contents=get_config(module))

    interface_exist = check_interface(module, netcfg)
    if interface_exist:
        parents = ['interface {0}'.format(interface_exist)]
        temp_config = netcfg.get_section(parents)

        if 'member vni {0} associate-vrf'.format(module.params['vni']) in temp_config:
            parents.append('member vni {0} associate-vrf'.format(module.params['vni']))
            config = netcfg.get_section(parents)
        elif "member vni {0}".format(module.params['vni']) in temp_config:
            parents.append('member vni {0}'.format(module.params['vni']))
            config = netcfg.get_section(parents)
        else:
            config = {}

        if config:
            for arg in args:
                if arg not in ['interface', 'vni']:
                    existing[arg] = get_value(arg, config, module)
            existing['interface'] = interface_exist
            existing['vni'] = module.params['vni']

    return existing, interface_exist


def apply_key_map(key_map, table):
    new_dict = {}
    for key, value in table.items():
        new_key = key_map.get(key)
        if new_key:
            new_dict[new_key] = value
    return new_dict


def state_present(module, existing, proposed, candidate):
    commands = list()
    proposed_commands = apply_key_map(PARAM_TO_COMMAND_KEYMAP, proposed)
    existing_commands = apply_key_map(PARAM_TO_COMMAND_KEYMAP, existing)

    for key, value in proposed_commands.items():
        if key == 'associate-vrf':
            command = 'member vni {0} {1}'.format(module.params['vni'], key)
            if not value:
                command = 'no {0}'.format(command)
            commands.append(command)

        elif key == 'peer-ip' and value != []:
            for peer in value:
                commands.append('{0} {1}'.format(key, peer))

        elif key == 'mcast-group' and value != existing_commands.get(key):
            commands.append('no {0}'.format(key))
            vni_command = 'member vni {0}'.format(module.params['vni'])
            if vni_command not in commands:
                commands.append('member vni {0}'.format(module.params['vni']))
            if value != PARAM_TO_DEFAULT_KEYMAP.get('multicast_group', 'default'):
                commands.append('{0} {1}'.format(key, value))

        elif key == 'ingress-replication protocol' and value != existing_commands.get(key):
            evalue = existing_commands.get(key)
            dvalue = PARAM_TO_DEFAULT_KEYMAP.get('ingress_replication', 'default')
            if value != dvalue:
                if evalue and evalue != dvalue:
                    commands.append('no {0} {1}'.format(key, evalue))
                commands.append('{0} {1}'.format(key, value))
            else:
                if evalue:
                    commands.append('no {0} {1}'.format(key, evalue))

        elif value is True:
            commands.append(key)
        elif value is False:
            commands.append('no {0}'.format(key))
        elif value == 'default' or value == []:
            if existing_commands.get(key):
                existing_value = existing_commands.get(key)
                if key == 'peer-ip':
                    for peer in existing_value:
                        commands.append('no {0} {1}'.format(key, peer))
                else:
                    commands.append('no {0} {1}'.format(key, existing_value))
            else:
                if key.replace(' ', '_').replace('-', '_') in BOOL_PARAMS:
                    commands.append('no {0}'.format(key.lower()))
        else:
            command = '{0} {1}'.format(key, value.lower())
            commands.append(command)

    if commands:
        vni_command = 'member vni {0}'.format(module.params['vni'])
        ingress_replications_command = 'ingress-replication protocol static'
        ingress_replicationb_command = 'ingress-replication protocol bgp'
        ingress_replicationns_command = 'no ingress-replication protocol static'
        ingress_replicationnb_command = 'no ingress-replication protocol bgp'
        interface_command = 'interface {0}'.format(module.params['interface'])

        if any(c in commands for c in (ingress_replications_command, ingress_replicationb_command,
               ingress_replicationnb_command, ingress_replicationns_command)):
            static_level_cmds = [cmd for cmd in commands if 'peer' in cmd]
            parents = [interface_command, vni_command]
            for cmd in commands:
                parents.append(cmd)
            candidate.add(static_level_cmds, parents=parents)
            commands = [cmd for cmd in commands if 'peer' not in cmd]

        elif 'peer-ip' in commands[0]:
            static_level_cmds = [cmd for cmd in commands]
            parents = [interface_command, vni_command, ingress_replications_command]
            candidate.add(static_level_cmds, parents=parents)

        if vni_command in commands:
            parents = [interface_command]
            commands.remove(vni_command)
            if module.params['assoc_vrf'] is None:
                parents.append(vni_command)
            candidate.add(commands, parents=parents)


def state_absent(module, existing, proposed, candidate):
    if existing['assoc_vrf']:
        commands = ['no member vni {0} associate-vrf'.format(
            module.params['vni'])]
    else:
        commands = ['no member vni {0}'.format(module.params['vni'])]
    parents = ['interface {0}'.format(module.params['interface'])]
    candidate.add(commands, parents=parents)


def main():
    argument_spec = dict(
        interface=dict(required=True, type='str'),
        vni=dict(required=True, type='str'),
        assoc_vrf=dict(required=False, type='bool'),
        multicast_group=dict(required=False, type='str'),
        peer_list=dict(required=False, type='list'),
        suppress_arp=dict(required=False, type='bool'),
        ingress_replication=dict(required=False, type='str', choices=['bgp', 'static', 'default']),
        state=dict(choices=['present', 'absent'], default='present', required=False),
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)
    result = {'changed': False, 'commands': [], 'warnings': warnings}

    if module.params['assoc_vrf']:
        mutually_exclusive_params = ['multicast_group',
                                     'suppress_arp',
                                     'ingress_replication']
        for param in mutually_exclusive_params:
            if module.params[param]:
                module.fail_json(msg='assoc_vrf cannot be used with '
                                     '{0} param'.format(param))
    if module.params['peer_list']:
        if module.params['peer_list'][0] != 'default' and module.params['ingress_replication'] != 'static':
            module.fail_json(msg='ingress_replication=static is required '
                                 'when using peer_list param')
        else:
            peer_list = module.params['peer_list']
            if peer_list[0] == 'default':
                module.params['peer_list'] = 'default'
            else:
                stripped_peer_list = map(str.strip, peer_list)
                module.params['peer_list'] = stripped_peer_list

    state = module.params['state']
    args = PARAM_TO_COMMAND_KEYMAP.keys()
    existing, interface_exist = get_existing(module, args)

    if state == 'present':
        if not interface_exist:
            module.fail_json(msg="The proposed NVE interface does not exist. Use nxos_interface to create it first.")
        elif interface_exist != module.params['interface']:
            module.fail_json(msg='Only 1 NVE interface is allowed on the switch.')
    elif state == 'absent':
        if interface_exist != module.params['interface']:
            module.exit_json(**result)
        elif existing and existing['vni'] != module.params['vni']:
            module.fail_json(
                msg="ERROR: VNI delete failed: Could not find vni node for {0}".format(module.params['vni']),
                existing_vni=existing['vni']
            )

    proposed_args = dict((k, v) for k, v in module.params.items()
                         if v is not None and k in args)

    proposed = {}
    for key, value in proposed_args.items():
        if key in ['multicast_group', 'peer_list', 'ingress_replication']:
            if str(value).lower() == 'default':
                value = PARAM_TO_DEFAULT_KEYMAP.get(key, 'default')
        if key != 'interface' and existing.get(key) != value:
            proposed[key] = value

    candidate = CustomNetworkConfig(indent=3)
    if state == 'present':
        state_present(module, existing, proposed, candidate)
    elif existing and state == 'absent':
        state_absent(module, existing, proposed, candidate)

    if candidate:
        candidate = candidate.items_text()
        result['changed'] = True
        result['commands'] = candidate
        if not module.check_mode:
            load_config(module, candidate)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
