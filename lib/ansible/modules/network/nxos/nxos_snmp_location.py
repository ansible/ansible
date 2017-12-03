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
module: nxos_snmp_location
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages SNMP location information.
description:
    - Manages SNMP location configuration.
author:
    - Jason Edelman (@jedelman8)
    - Gabriele Gerbino (@GGabriele)
notes:
    - Tested against NXOSv 7.3.(0)D1(1) on VIRL
options:
    location:
        description:
            - Location information.
        required: true
    state:
        description:
            - Manage the state of the resource.
        required: false
        default: present
        choices: ['present','absent']
'''

EXAMPLES = '''
# ensure snmp location is configured
- nxos_snmp_location:
    location: Test
    state: present

# ensure snmp location is not configured
- nxos_snmp_location:
    location: Test
    state: absent
'''

RETURN = '''
commands:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["snmp-server location New_Test"]
'''


import re

from ansible.module_utils.network.nxos.nxos import load_config, run_commands
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule


def execute_show_command(command, module):
    command = {
        'command': command,
        'output': 'text',
    }

    return run_commands(module, command)


def flatten_list(command_lists):
    flat_command_list = []
    for command in command_lists:
        if isinstance(command, list):
            flat_command_list.extend(command)
        else:
            flat_command_list.append(command)
    return flat_command_list


def get_snmp_location(module):
    location = {}
    location_regex = r'^\s*snmp-server\s+location\s+(?P<location>.+)$'

    body = execute_show_command('show run snmp', module)[0]
    match_location = re.search(location_regex, body, re.M)
    if match_location:
        location['location'] = match_location.group("location")

    return location


def main():
    argument_spec = dict(
        location=dict(required=True, type='str'),
        state=dict(choices=['absent', 'present'], default='present'),
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)
    results = {'changed': False, 'commands': [], 'warnings': warnings}

    location = module.params['location']
    state = module.params['state']

    existing = get_snmp_location(module)
    commands = []

    if state == 'absent':
        if existing and existing['location'] == location:
            commands.append('no snmp-server location')
    elif state == 'present':
        if not existing or existing['location'] != location:
            commands.append('snmp-server location {0}'.format(location))

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
