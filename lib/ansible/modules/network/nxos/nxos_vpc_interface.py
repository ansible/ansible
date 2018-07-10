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
module: nxos_vpc_interface
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages interface VPC configuration
description:
  - Manages interface VPC configuration
author:
  - Jason Edelman (@jedelman8)
  - Gabriele Gerbino (@GGabriele)
notes:
  - Tested against NXOSv 7.3.(0)D1(1) on VIRL
  - Either vpc or peer_link param is required, but not both.
  - C(state=absent) removes whatever VPC config is on a port-channel
    if one exists.
  - Re-assigning a vpc or peerlink from one portchannel to another is not
    supported.  The module will force the user to unconfigure an existing
    vpc/pl before configuring the same value on a new portchannel
options:
  portchannel:
    description:
      - Group number of the portchannel that will be configured.
    required: true
  vpc:
    description:
      - VPC group/id that will be configured on associated portchannel.
  peer_link:
    description:
      - Set to true/false for peer link config on associated portchannel.
  state:
    description:
      - Manages desired state of the resource.
    required: true
    choices: ['present','absent']
    default: present
'''

EXAMPLES = '''
- nxos_vpc_interface:
    portchannel: 10
    vpc: 100
'''

RETURN = '''
commands:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["interface port-channel100", "vpc 10"]
'''

from ansible.module_utils.network.nxos.nxos import get_config, load_config, run_commands
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule


def flatten_list(command_lists):
    flat_command_list = []
    for command in command_lists:
        if isinstance(command, list):
            flat_command_list.extend(command)
        else:
            flat_command_list.append(command)
    return flat_command_list


def get_portchannel_list(module):
    portchannels = []
    pc_list = []

    try:
        body = run_commands(module, ['show port-channel summary | json'])[0]
        pc_list = body['TABLE_channel']['ROW_channel']
    except (KeyError, AttributeError, TypeError):
        return portchannels

    if pc_list:
        if isinstance(pc_list, dict):
            pc_list = [pc_list]

        for pc in pc_list:
            portchannels.append(pc['group'])

    return portchannels


def get_existing_portchannel_to_vpc_mappings(module):
    pc_vpc_mapping = {}

    try:
        body = run_commands(module, ['show vpc brief | json'])[0]
        vpc_table = body['TABLE_vpc']['ROW_vpc']
    except (KeyError, AttributeError, TypeError):
        vpc_table = None

    if vpc_table:
        if isinstance(vpc_table, dict):
            vpc_table = [vpc_table]

        for vpc in vpc_table:
            pc_vpc_mapping[str(vpc['vpc-id'])] = str(vpc['vpc-ifindex'])

    return pc_vpc_mapping


def peer_link_exists(module):
    found = False
    run = get_config(module, flags=['vpc'])

    vpc_list = run.split('\n')
    for each in vpc_list:
        if 'peer-link' in each:
            found = True
    return found


def get_active_vpc_peer_link(module):
    peer_link = None

    try:
        body = run_commands(module, ['show vpc brief | json'])[0]
        peer_link = body['TABLE_peerlink']['ROW_peerlink']['peerlink-ifindex']
    except (KeyError, AttributeError, TypeError):
        return peer_link

    return peer_link


def get_portchannel_vpc_config(module, portchannel):
    peer_link_pc = None
    peer_link = False
    vpc = ""
    pc = ""
    config = {}

    try:
        body = run_commands(module, ['show vpc brief | json'])[0]
        table = body['TABLE_peerlink']['ROW_peerlink']
    except (KeyError, AttributeError, TypeError):
        table = {}

    if table:
        peer_link_pc = table.get('peerlink-ifindex', None)

    if peer_link_pc:
        plpc = str(peer_link_pc[2:])
        if portchannel == plpc:
            config['portchannel'] = portchannel
            config['peer-link'] = True
            config['vpc'] = vpc

    mapping = get_existing_portchannel_to_vpc_mappings(module)

    for existing_vpc, port_channel in mapping.items():
        port_ch = str(port_channel[2:])
        if port_ch == portchannel:
            pc = port_ch
            vpc = str(existing_vpc)

            config['portchannel'] = pc
            config['peer-link'] = peer_link
            config['vpc'] = vpc

    return config


def get_commands_to_config_vpc_interface(portchannel, delta, config_value, existing):
    commands = []

    if not delta.get('peer-link') and existing.get('peer-link'):
        commands.append('no vpc peer-link')
        commands.insert(0, 'interface port-channel{0}'.format(portchannel))

    elif delta.get('peer-link') and not existing.get('peer-link'):
        commands.append('vpc peer-link')
        commands.insert(0, 'interface port-channel{0}'.format(portchannel))

    elif delta.get('vpc') and not existing.get('vpc'):
        command = 'vpc {0}'.format(config_value)
        commands.append(command)
        commands.insert(0, 'interface port-channel{0}'.format(portchannel))

    return commands


def state_present(portchannel, delta, config_value, existing):
    commands = []

    command = get_commands_to_config_vpc_interface(
        portchannel,
        delta,
        config_value,
        existing
    )
    commands.append(command)

    return commands


def state_absent(portchannel, existing):
    commands = []
    if existing.get('vpc'):
        command = 'no vpc'
        commands.append(command)
    elif existing.get('peer-link'):
        command = 'no vpc peer-link'
        commands.append(command)
    if commands:
        commands.insert(0, 'interface port-channel{0}'.format(portchannel))

    return commands


def main():
    argument_spec = dict(
        portchannel=dict(required=True, type='str'),
        vpc=dict(required=False, type='str'),
        peer_link=dict(required=False, type='bool'),
        state=dict(choices=['absent', 'present'], default='present')
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=[['vpc', 'peer_link']],
                           supports_check_mode=True)

    warnings = list()
    commands = []
    check_args(module, warnings)
    results = {'changed': False, 'warnings': warnings}

    portchannel = module.params['portchannel']
    vpc = module.params['vpc']
    peer_link = module.params['peer_link']
    state = module.params['state']

    args = {'portchannel': portchannel, 'vpc': vpc, 'peer-link': peer_link}
    active_peer_link = None

    if portchannel not in get_portchannel_list(module):
        if not portchannel.isdigit() or int(portchannel) not in get_portchannel_list(module):
            module.fail_json(msg="The portchannel you are trying to make a"
                                 " VPC or PL is not created yet. "
                                 "Create it first!")
    if vpc:
        mapping = get_existing_portchannel_to_vpc_mappings(module)

        if vpc in mapping and portchannel != mapping[vpc].strip('Po'):
            module.fail_json(msg="This vpc is already configured on "
                                 "another portchannel. Remove it first "
                                 "before trying to assign it here. ",
                             existing_portchannel=mapping[vpc])

        for vpcid, existing_pc in mapping.items():
            if portchannel == existing_pc.strip('Po') and vpcid != vpc:
                module.fail_json(msg="This portchannel already has another"
                                     " VPC configured. Remove it first "
                                     "before assigning this one",
                                 existing_vpc=vpcid)

        if peer_link_exists(module):
            active_peer_link = get_active_vpc_peer_link(module)
            if active_peer_link[-2:] == portchannel:
                module.fail_json(msg="That port channel is the current "
                                     "PEER LINK. Remove it if you want it"
                                     " to be a VPC")
        config_value = vpc

    elif peer_link is not None:
        if peer_link_exists(module):
            active_peer_link = get_active_vpc_peer_link(module)[2::]
            if active_peer_link != portchannel:
                if peer_link:
                    module.fail_json(msg="A peer link already exists on"
                                         " the device. Remove it first",
                                     current_peer_link='Po{0}'.format(active_peer_link))
        config_value = 'peer-link'

    proposed = dict((k, v) for k, v in args.items() if v is not None)
    existing = get_portchannel_vpc_config(module, portchannel)

    if state == 'present':
        delta = dict(set(proposed.items()).difference(existing.items()))
        if delta:
            commands = state_present(portchannel, delta, config_value, existing)

    elif state == 'absent' and existing:
        commands = state_absent(portchannel, existing)

    cmds = flatten_list(commands)
    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            load_config(module, cmds)
            results['changed'] = True
            if 'configure' in cmds:
                cmds.pop(0)

    results['commands'] = cmds
    module.exit_json(**results)


if __name__ == '__main__':
    main()
