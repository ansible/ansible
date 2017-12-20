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
module: nxos_snmp_contact
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages SNMP contact info.
description:
    - Manages SNMP contact information.
author:
    - Jason Edelman (@jedelman8)
    - Gabriele Gerbino (@GGabriele)
notes:
    - Tested against NXOSv 7.3.(0)D1(1) on VIRL
    - C(state=absent) removes the contact configuration if it is configured.
options:
    contact:
        description:
            - Contact information.
        required: true
    state:
        description:
            - Manage the state of the resource.
        required: true
        default: present
        choices: ['present','absent']
'''

EXAMPLES = '''
# ensure snmp contact is configured
- nxos_snmp_contact:
    contact: Test
    state: present
'''

RETURN = '''
commands:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["snmp-server contact New_Test"]
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


def get_snmp_contact(module):
    contact = {}
    contact_regex = r'^\s*snmp-server\scontact\s(?P<contact>.+)$'

    body = execute_show_command('show run snmp', module)[0]
    match_contact = re.search(contact_regex, body, re.M)
    if match_contact:
        contact['contact'] = match_contact.group("contact")

    return contact


def main():
    argument_spec = dict(
        contact=dict(required=True, type='str'),
        state=dict(choices=['absent', 'present'], default='present'),
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)
    results = {'changed': False, 'commands': [], 'warnings': warnings}

    contact = module.params['contact']
    state = module.params['state']

    existing = get_snmp_contact(module)
    commands = []

    if state == 'absent':
        if existing and existing['contact'] == contact:
            commands.append('no snmp-server contact')
    elif state == 'present':
        if not existing or existing['contact'] != contact:
            commands.append('snmp-server contact {0}'.format(contact))

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
