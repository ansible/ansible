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
module: nxos_igmp_snooping
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages IGMP snooping global configuration.
description:
    - Manages IGMP snooping global configuration.
author:
    - Jason Edelman (@jedelman8)
    - Gabriele Gerbino (@GGabriele)
notes:
    - Tested against NXOSv 7.3.(0)D1(1) on VIRL
    - When C(state=default), params will be reset to a default state.
    - C(group_timeout) also accepts I(never) as an input.
options:
    snooping:
        description:
            - Enables/disables IGMP snooping on the switch.
        type: bool
    group_timeout:
        description:
            - Group membership timeout value for all VLANs on the device.
              Accepted values are integer in range 1-10080, I(never) and
              I(default).
    link_local_grp_supp:
        description:
            - Global link-local groups suppression.
        type: bool
    report_supp:
        description:
            - Global IGMPv1/IGMPv2 Report Suppression.
        type: bool
    v3_report_supp:
        description:
            - Global IGMPv3 Report Suppression and Proxy Reporting.
        type: bool
    state:
        description:
            - Manage the state of the resource.
        default: present
        choices: ['present','default']
'''

EXAMPLES = '''
# ensure igmp snooping params supported in this module are in there default state
- nxos_igmp_snooping:
    state: default

# ensure following igmp snooping params are in the desired state
- nxos_igmp_snooping:
   group_timeout: never
   snooping: true
   link_local_grp_supp: false
   optimize_mcast_flood: false
   report_supp: true
   v3_report_supp: true
'''

RETURN = '''
commands:
    description: command sent to the device
    returned: always
    type: list
    sample: ["ip igmp snooping link-local-groups-suppression",
             "ip igmp snooping group-timeout 50",
             "no ip igmp snooping report-suppression",
             "no ip igmp snooping v3-report-suppression",
             "no ip igmp snooping"]
'''


import re

from ansible.module_utils.network.nxos.nxos import get_config, load_config, run_commands
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule


def execute_show_command(command, module, output='text'):
    command = {
        'command': command,
        'output': output,
    }

    return run_commands(module, [command])


def flatten_list(command_lists):
    flat_command_list = []
    for command in command_lists:
        if isinstance(command, list):
            flat_command_list.extend(command)
        else:
            flat_command_list.append(command)
    return flat_command_list


def get_group_timeout(config):
    match = re.search(r'  Group timeout configured: (\S+)', config, re.M)
    if match:
        value = match.group(1)
    else:
        value = ''
    return value


def get_igmp_snooping(module):
    command = 'show ip igmp snooping'
    existing = {}

    try:
        body = execute_show_command(command, module, output='json')[0]
    except IndexError:
        body = []

    if body:
        snooping = str(body.get('enabled')).lower()
        if snooping == 'true' or snooping == 'enabled':
            existing['snooping'] = True
        else:
            existing['snooping'] = False

        report_supp = str(body.get('grepsup')).lower()
        if report_supp == 'true' or report_supp == 'enabled':
            existing['report_supp'] = True
        else:
            existing['report_supp'] = False

        link_local_grp_supp = str(body.get('glinklocalgrpsup')).lower()
        if link_local_grp_supp == 'true' or link_local_grp_supp == 'enabled':
            existing['link_local_grp_supp'] = True
        else:
            existing['link_local_grp_supp'] = False

        v3_report_supp = str(body.get('gv3repsup')).lower()
        if v3_report_supp == 'true' or v3_report_supp == 'enabled':
            existing['v3_report_supp'] = True
        else:
            existing['v3_report_supp'] = False

    command = 'show ip igmp snooping'
    body = execute_show_command(command, module)[0]
    if body:
        existing['group_timeout'] = get_group_timeout(body)

    return existing


def config_igmp_snooping(delta, existing, default=False):
    CMDS = {
        'snooping': 'ip igmp snooping',
        'group_timeout': 'ip igmp snooping group-timeout {}',
        'link_local_grp_supp': 'ip igmp snooping link-local-groups-suppression',
        'v3_report_supp': 'ip igmp snooping v3-report-suppression',
        'report_supp': 'ip igmp snooping report-suppression'
    }

    commands = []
    command = None
    for key, value in delta.items():
        if value:
            if default and key == 'group_timeout':
                if existing.get(key):
                    command = 'no ' + CMDS.get(key).format(existing.get(key))
            elif value == 'default' and key == 'group_timeout':
                if existing.get(key):
                    command = 'no ' + CMDS.get(key).format(existing.get(key))
            else:
                command = CMDS.get(key).format(value)
        else:
            command = 'no ' + CMDS.get(key).format(value)

        if command:
            commands.append(command)
        command = None

    return commands


def get_igmp_snooping_defaults():
    group_timeout = 'dummy'
    report_supp = True
    link_local_grp_supp = True
    v3_report_supp = False
    snooping = True

    args = dict(snooping=snooping, link_local_grp_supp=link_local_grp_supp,
                report_supp=report_supp, v3_report_supp=v3_report_supp,
                group_timeout=group_timeout)

    default = dict((param, value) for (param, value) in args.items()
                   if value is not None)

    return default


def main():
    argument_spec = dict(
        snooping=dict(required=False, type='bool'),
        group_timeout=dict(required=False, type='str'),
        link_local_grp_supp=dict(required=False, type='bool'),
        report_supp=dict(required=False, type='bool'),
        v3_report_supp=dict(required=False, type='bool'),
        state=dict(choices=['present', 'default'], default='present'),
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)
    results = {'changed': False, 'commands': [], 'warnings': warnings}

    snooping = module.params['snooping']
    link_local_grp_supp = module.params['link_local_grp_supp']
    report_supp = module.params['report_supp']
    v3_report_supp = module.params['v3_report_supp']
    group_timeout = module.params['group_timeout']
    state = module.params['state']

    args = dict(snooping=snooping, link_local_grp_supp=link_local_grp_supp,
                report_supp=report_supp, v3_report_supp=v3_report_supp,
                group_timeout=group_timeout)

    proposed = dict((param, value) for (param, value) in args.items()
                    if value is not None)

    existing = get_igmp_snooping(module)

    commands = []
    if state == 'present':
        delta = dict(
            set(proposed.items()).difference(existing.items())
        )
        if delta:
            command = config_igmp_snooping(delta, existing)
            if command:
                commands.append(command)
    elif state == 'default':
        proposed = get_igmp_snooping_defaults()
        delta = dict(
            set(proposed.items()).difference(existing.items())
        )
        if delta:
            command = config_igmp_snooping(delta, existing, default=True)
            if command:
                commands.append(command)

    cmds = flatten_list(commands)
    if cmds:
        results['changed'] = True
        if not module.check_mode:
            load_config(module, cmds)
        if 'configure' in cmds:
            cmds.pop(0)
        results['commands'] = cmds

    module.exit_json(**results)

if __name__ == '__main__':
    main()
