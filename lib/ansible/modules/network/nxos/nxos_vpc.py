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
  - Tested against NXOSv 7.3.(0)D1(1) on VIRL
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
  system_priority:
    description:
      - System priority device.  Remember they must match between peers.
  pkl_src:
    description:
      - Source IP address used for peer keepalive link
  pkl_dest:
    description:
      - Destination (remote) IP address used for peer keepalive link
  pkl_vrf:
    description:
      - VRF used for peer keepalive link
    default: management
  peer_gw:
    description:
      - Enables/Disables peer gateway
    type: bool
  auto_recovery:
    description:
      - Enables/Disables auto recovery
    type: bool
  delay_restore:
    description:
      - manages delay restore command and config value in seconds
    type: bool
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

- name: configure
  nxos_vpc:
    domain: 100
    role_priority: 32667
    system_priority: 2000
    peer_gw: true
    pkl_src: 10.1.100.2
    pkl_dest: 192.168.100.4
    auto_recovery: true

- name: Configure VPC with delay restore and existing keepalive VRF
  nxos_vpc:
    domain: 10
    role_priority: 28672
    system_priority: 2000
    delay_restore: 180
    peer_gw: true
    pkl_src: 1.1.1.2
    pkl_dest: 1.1.1.1
    pkl_vrf: vpckeepalive
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

import re
from ansible.module_utils.network.nxos.nxos import get_config, load_config, run_commands
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule


CONFIG_ARGS = {
    'role_priority': 'role priority {role_priority}',
    'system_priority': 'system-priority {system_priority}',
    'delay_restore': 'delay restore {delay_restore}',
    'peer_gw': '{peer_gw} peer-gateway',
    'auto_recovery': '{auto_recovery} auto-recovery',
}

PARAM_TO_DEFAULT_KEYMAP = {
    'delay_restore': '60',
    'role_priority': '32667',
    'system_priority': '32667',
    'peer_gw': False,
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


def get_auto_recovery_default(module):
    auto = False
    data = run_commands(module, ['show inventory | json'])[0]
    pid = data['TABLE_inv']['ROW_inv'][0]['productid']
    if re.search(r'N7K', pid):
        auto = True
    elif re.search(r'N9K', pid):
        data = run_commands(module, ['show hardware | json'])[0]
        ver = data['kickstart_ver_str']
        if re.search(r'7.0\(3\)F', ver):
            auto = True

    return auto


def get_vpc(module):
    body = run_commands(module, ['show vpc | json'])[0]
    if body:
        domain = str(body['vpc-domain-id'])
    else:
        body = run_commands(module, ['show run vpc | inc domain'])[0]
        if body:
            domain = body.split()[2]
        else:
            domain = 'not configured'

    vpc = {}
    if domain != 'not configured':
        run = get_config(module, flags=['vpc'])
        if run:
            vpc['domain'] = domain
            for key in PARAM_TO_DEFAULT_KEYMAP.keys():
                vpc[key] = PARAM_TO_DEFAULT_KEYMAP.get(key)
            vpc['auto_recovery'] = get_auto_recovery_default(module)
            vpc_list = run.split('\n')
            for each in vpc_list:
                if 'role priority' in each:
                    line = each.split()
                    vpc['role_priority'] = line[-1]
                if 'system-priority' in each:
                    line = each.split()
                    vpc['system_priority'] = line[-1]
                if 'delay restore' in each:
                    line = each.split()
                    vpc['delay_restore'] = line[-1]
                if 'no auto-recovery' in each:
                    vpc['auto_recovery'] = False
                elif 'auto-recovery' in each:
                    vpc['auto_recovery'] = True
                if 'peer-gateway' in each:
                    vpc['peer_gw'] = True
                if 'peer-keepalive destination' in each:
                    line = each.split()
                    vpc['pkl_dest'] = line[2]
                    vpc['pkl_vrf'] = 'management'
                    if 'source' in each:
                        vpc['pkl_src'] = line[4]
                        if 'vrf' in each:
                            vpc['pkl_vrf'] = line[6]
                    else:
                        if 'vrf' in each:
                            vpc['pkl_vrf'] = line[4]

    return vpc


def get_commands_to_config_vpc(module, vpc, domain, existing):
    vpc = dict(vpc)

    domain_only = vpc.get('domain')

    commands = []
    if 'pkl_dest' in vpc:
        pkl_command = 'peer-keepalive destination {pkl_dest}'.format(**vpc)
        if 'pkl_src' in vpc:
            pkl_command += ' source {pkl_src}'.format(**vpc)
        if 'pkl_vrf' in vpc and vpc['pkl_vrf'] != 'management':
            pkl_command += ' vrf {pkl_vrf}'.format(**vpc)
        commands.append(pkl_command)

    if 'auto_recovery' in vpc:
        if not vpc.get('auto_recovery'):
            vpc['auto_recovery'] = 'no'
        else:
            vpc['auto_recovery'] = ''

    if 'peer_gw' in vpc:
        if not vpc.get('peer_gw'):
            vpc['peer_gw'] = 'no'
        else:
            vpc['peer_gw'] = ''

    for param in vpc:
        command = CONFIG_ARGS.get(param)
        if command is not None:
            command = command.format(**vpc).strip()
            if 'peer-gateway' in command:
                commands.append('terminal dont-ask')
            commands.append(command)

    if commands or domain_only:
        commands.insert(0, 'vpc domain {0}'.format(domain))
    return commands


def main():
    argument_spec = dict(
        domain=dict(required=True, type='str'),
        role_priority=dict(required=False, type='str'),
        system_priority=dict(required=False, type='str'),
        pkl_src=dict(required=False),
        pkl_dest=dict(required=False),
        pkl_vrf=dict(required=False),
        peer_gw=dict(required=False, type='bool'),
        auto_recovery=dict(required=False, type='bool'),
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

    if not pkl_dest:
        if pkl_src:
            module.fail_json(msg='dest IP for peer-keepalive is required'
                                 ' when src IP is present')
        elif pkl_vrf:
            if pkl_vrf != 'management':
                module.fail_json(msg='dest and src IP for peer-keepalive are required'
                                     ' when vrf is present')
            else:
                module.fail_json(msg='dest IP for peer-keepalive is required'
                                     ' when vrf is present')
    if pkl_vrf:
        if pkl_vrf.lower() not in get_vrf_list(module):
            module.fail_json(msg='The VRF you are trying to use for the peer '
                                 'keepalive link is not on device yet. Add it'
                                 ' first, please.')
    proposed = dict((k, v) for k, v in args.items() if v is not None)
    existing = get_vpc(module)

    commands = []
    if state == 'present':
        delta = {}
        for key, value in proposed.items():
            if str(value).lower() == 'default':
                value = PARAM_TO_DEFAULT_KEYMAP.get(key)
            if existing.get(key) != value:
                delta[key] = value
        if delta:
            command = get_commands_to_config_vpc(module, delta, domain, existing)
            commands.append(command)
    elif state == 'absent':
        if existing:
            if domain != existing['domain']:
                module.fail_json(msg="You are trying to remove a domain that "
                                     "does not exist on the device")
            else:
                commands.append('terminal dont-ask')
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
