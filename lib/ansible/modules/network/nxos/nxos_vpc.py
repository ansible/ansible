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

ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'status': ['preview'],
    'supported_by': 'community',
}


DOCUMENTATION = '''
---
module: nxos_vpc
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages global VPC configuration
description:
  - Manages global VPC configuration
author:
  - Jason Edelman (@jedelman8)
  - Gabriele Gerbino (@GGabriele)
notes:
  - The feature vpc must be enabled before this module can be used
  - If not using management vrf, vrf must be globally on the device
    before using in the pkl config
  - Although source IP isn't required on the command line it is
    required when using this module.  The PKL VRF must also be configured
    prior to using this module.
  - Both pkl_src and pkl_dest are needed when changing PKL VRF.
options:
  domain:
    description:
      - VPC domain
    required: true
  role_priority:
    description:
      - Role priority for device. Remember lower is better.
    required: false
    default: null
  system_priority:
    description:
      - System priority device.  Remember they must match between peers.
    required: false
    default: null
  pkl_src:
    description:
      - Source IP address used for peer keepalive link
    required: false
    default: null
  pkl_dest:
    description:
      - Destination (remote) IP address used for peer keepalive link
    required: false
    default: null
  pkl_vrf:
    description:
      - VRF used for peer keepalive link
    required: false
    default: management
  peer_gw:
    description:
      - Enables/Disables peer gateway
    required: true
    choices: ['true','false']
  auto_recovery:
    description:
      - Enables/Disables auto recovery
    required: true
    choices: ['true','false']
  delay_restore:
    description:
      - manages delay restore command and config value in seconds
    required: false
    default: null
  state:
    description:
      - Manages desired state of the resource
    required: true
    choices: ['present','absent']
'''

EXAMPLES = '''
- name: configure a simple asn
  nxos_vpc:
    domain: 100
    role_priority: 1000
    system_priority: 2000
    pkl_dest: 192.168.100.4
    pkl_src: 10.1.100.20
    peer_gw: true
    auto_recovery: true

# peer-gateway might ask for confirmation to apply changes
# Device should be configured with terminal dont-ask that makes
# the device take default answer on confirmation prompt

- name: Make device take default answer
  nxos_command:
    commands: terminal dont-ask

- name: configure
  nxos_vpc:
    domain: 100
    role_priority: 32667
    system_priority: 2000
    peer_gw: true
    pkl_src: 10.1.100.2
    pkl_dest: 192.168.100.4
    auto_recovery: true
'''

RETURN = '''
commands:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["vpc domain 100",
            "peer-keepalive destination 192.168.100.4 source 10.1.100.20 vrf management",
            "auto-recovery", "peer-gateway"]
'''

from ansible.module_utils.nxos import get_config, load_config, run_commands
from ansible.module_utils.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule


CONFIG_ARGS = {
    'role_priority': 'role priority {role_priority}',
    'system_priority': 'system-priority {system_priority}',
    'delay_restore': 'delay restore {delay_restore}',
    'peer_gw': '{peer_gw} peer-gateway',
    'auto_recovery': '{auto_recovery} auto-recovery',
}


def flatten_list(command_lists):
    flat_command_list = []
    for command in command_lists:
        if isinstance(command, list):
            flat_command_list.extend(command)
        else:
            flat_command_list.append(command)
    return flat_command_list


def get_vrf_list(module):

    try:
        body = run_commands(module, ['show vrf all | json'])[0]
        vrf_table = body['TABLE_vrf']['ROW_vrf']
    except (KeyError, AttributeError):
        return []

    vrf_list = []
    if vrf_table:
        for each in vrf_table:
            vrf_list.append(str(each['vrf_name'].lower()))

    return vrf_list


def get_vpc(module):
    body = run_commands(module, ['show vpc | json'])[0]

    domain = str(body['vpc-domain-id'])
    auto_recovery = 'enabled' in str(body['vpc-auto-recovery-status']).lower()

    vpc = {}
    if domain != 'not configured':
        delay_restore = None
        pkl_src = None
        role_priority = '32667'
        system_priority = None
        pkl_dest = None
        pkl_vrf = None
        peer_gw = False

        run = get_config(module, flags=['section vpc'])
        if run:
            vpc_list = run.split('\n')
            for each in vpc_list:
                if 'delay restore' in each:
                    line = each.split()
                    if len(line) == 5:
                        delay_restore = line[-1]
                if 'peer-keepalive destination' in each:
                    line = each.split()
                    pkl_dest = line[2]
                    for word in line:
                        if 'source' in word:
                            index = line.index(word)
                            pkl_src = line[index + 1]
                if 'role priority' in each:
                    line = each.split()
                    role_priority = line[-1]
                if 'system-priority' in each:
                    line = each.split()
                    system_priority = line[-1]
                if 'peer-gateway' in each:
                    peer_gw = True

        body = run_commands(module, ['show vpc peer-keepalive | json'])[0]

        if body:
            pkl_dest = body['vpc-keepalive-dest']
            if 'N/A' in pkl_dest:
                pkl_dest = None
            elif len(pkl_dest) == 2:
                pkl_dest = pkl_dest[0]
            pkl_vrf = str(body['vpc-keepalive-vrf'])

        vpc['domain'] = domain
        vpc['auto_recovery'] = auto_recovery
        vpc['delay_restore'] = delay_restore
        vpc['pkl_src'] = pkl_src
        vpc['role_priority'] = role_priority
        vpc['system_priority'] = system_priority
        vpc['pkl_dest'] = pkl_dest
        vpc['pkl_vrf'] = pkl_vrf
        vpc['peer_gw'] = peer_gw

    return vpc


def get_commands_to_config_vpc(module, vpc, domain, existing):
    vpc = dict(vpc)

    domain_only = vpc.get('domain')
    pkl_src = vpc.get('pkl_src')
    pkl_dest = vpc.get('pkl_dest')
    pkl_vrf = vpc.get('pkl_vrf') or existing.get('pkl_vrf')
    vpc['pkl_vrf'] = pkl_vrf

    commands = []
    if pkl_src or pkl_dest:
        if pkl_src is None:
            vpc['pkl_src'] = existing.get('pkl_src')
        elif pkl_dest is None:
            vpc['pkl_dest'] = existing.get('pkl_dest')
        pkl_command = 'peer-keepalive destination {pkl_dest}'.format(**vpc) \
                      + ' source {pkl_src} vrf {pkl_vrf}'.format(**vpc)
        commands.append(pkl_command)
    elif pkl_vrf:
        pkl_src = existing.get('pkl_src')
        pkl_dest = existing.get('pkl_dest')
        if pkl_src and pkl_dest:
            pkl_command = ('peer-keepalive destination {0}'
                           ' source {1} vrf {2}'.format(pkl_dest, pkl_src, pkl_vrf))
            commands.append(pkl_command)

    if vpc.get('auto_recovery') is False:
        vpc['auto_recovery'] = 'no'
    else:
        vpc['auto_recovery'] = ''

    if 'peer_gw' in vpc:
        if vpc.get('peer_gw') is False:
            vpc['peer_gw'] = 'no'
        else:
            vpc['peer_gw'] = ''
    else:
        if existing.get('peer_gw') is False:
            vpc['peer_gw'] = 'no'
        else:
            vpc['peer_gw'] = ''

    for param in vpc:
        command = CONFIG_ARGS.get(param)
        if command is not None:
            command = command.format(**vpc).strip()
            commands.append(command)

    if commands or domain_only:
        commands.insert(0, 'vpc domain {0}'.format(domain))
    return commands


def get_commands_to_remove_vpc_interface(portchannel, config_value):
    commands = []
    command = 'no vpc {0}'.format(config_value)
    commands.append(command)
    commands.insert(0, 'interface port-channel{0}'.format(portchannel))
    return commands


def main():
    argument_spec = dict(
        domain=dict(required=True, type='str'),
        role_priority=dict(required=False, type='str'),
        system_priority=dict(required=False, type='str'),
        pkl_src=dict(required=False),
        pkl_dest=dict(required=False),
        pkl_vrf=dict(required=False, default='management'),
        peer_gw=dict(required=True, type='bool'),
        auto_recovery=dict(required=True, type='bool'),
        delay_restore=dict(required=False, type='str'),
        state=dict(choices=['absent', 'present'], default='present'),
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)
    results = {'changed': False, 'warnings': warnings}

    domain = module.params['domain']
    role_priority = module.params['role_priority']
    system_priority = module.params['system_priority']
    pkl_src = module.params['pkl_src']
    pkl_dest = module.params['pkl_dest']
    pkl_vrf = module.params['pkl_vrf']
    peer_gw = module.params['peer_gw']
    auto_recovery = module.params['auto_recovery']
    delay_restore = module.params['delay_restore']
    state = module.params['state']

    args = dict(domain=domain, role_priority=role_priority,
                system_priority=system_priority, pkl_src=pkl_src,
                pkl_dest=pkl_dest, pkl_vrf=pkl_vrf, peer_gw=peer_gw,
                auto_recovery=auto_recovery,
                delay_restore=delay_restore)

    if not (pkl_src and pkl_dest and pkl_vrf):
        # if only the source or dest is set, it'll fail and ask to set the
        # other
        if pkl_src or pkl_dest:
            module.fail_json(msg='source AND dest IP for pkl are required at '
                                 'this time (although source is technically not '
                                 ' required by the device.)')

        args.pop('pkl_src')
        args.pop('pkl_dest')
        args.pop('pkl_vrf')

    if pkl_vrf:
        if pkl_vrf.lower() not in get_vrf_list(module):
            module.fail_json(msg='The VRF you are trying to use for the peer '
                                 'keepalive link is not on device yet. Add it'
                                 ' first, please.')
    proposed = dict((k, v) for k, v in args.items() if v is not None)
    existing = get_vpc(module)

    commands = []
    if state == 'present':
        delta = set(proposed.items()).difference(existing.items())
        if delta:
            command = get_commands_to_config_vpc(module, delta, domain, existing)
            commands.append(command)
    elif state == 'absent':
        if existing:
            if domain != existing['domain']:
                module.fail_json(msg="You are trying to remove a domain that "
                                     "does not exist on the device")
            else:
                commands.append('no vpc domain {0}'.format(domain))

    cmds = flatten_list(commands)
    results['commands'] = cmds

    if cmds:
        results['changed'] = True
        if not module.check_mode:
            load_config(module, cmds)
            if 'configure' in cmds:
                cmds.pop(0)

    module.exit_json(**results)


if __name__ == '__main__':
    main()
