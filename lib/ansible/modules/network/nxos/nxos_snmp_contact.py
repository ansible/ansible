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
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"contact": "New_Test"}
existing:
    description: k/v pairs of existing snmp contact
    returned: always
    type: dict
    sample: {"contact": "Test"}
end_state:
    description: k/v pairs of snmp contact after module execution
    returned: always
    type: dict
    sample: {"contact": "New_Test"}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["snmp-server contact New_Test"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''

from ansible.module_utils.nxos import get_config, load_config, run_commands
from ansible.module_utils.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule


import re
import re


def execute_show_command(command, module, command_type='cli_show'):
    if module.params['transport'] == 'cli':
        if 'show run' not in command:
            command += ' | json'
        cmds = [command]
        body = run_commands(module, cmds)
    elif module.params['transport'] == 'nxapi':
        cmds = [command]
        body = run_commands(module, cmds)

    return body


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
    contact_regex = '.*snmp-server\scontact\s(?P<contact>\S+).*'
    command = 'show run snmp'

    body = execute_show_command(command, module, command_type='cli_show_ascii')[0]

    try:
        match_contact = re.match(contact_regex, body, re.DOTALL)
        group_contact = match_contact.groupdict()
        contact['contact'] = group_contact["contact"]
    except AttributeError:
        contact = {}

    return contact


def main():
    argument_spec = dict(
        contact=dict(required=True, type='str'),
        state=dict(choices=['absent', 'present'],
                       default='present')
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                                supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)


    contact = module.params['contact']
    state = module.params['state']

    existing = get_snmp_contact(module)
    changed = False
    proposed = dict(contact=contact)
    end_state = existing
    commands = []

    if state == 'absent':
        if existing and existing['contact'] == contact:
            commands.append('no snmp-server contact')
    elif state == 'present':
        if not existing or existing['contact'] != contact:
            commands.append('snmp-server contact {0}'.format(contact))

    cmds = flatten_list(commands)
    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            changed = True
            load_config(module, cmds)
            end_state = get_snmp_contact(module)
            if 'configure' in cmds:
                cmds.pop(0)

    results = {}
    results['proposed'] = proposed
    results['existing'] = existing
    results['end_state'] = end_state
    results['updates'] = cmds
    results['changed'] = changed
    results['warnings'] = warnings

    module.exit_json(**results)


if __name__ == '__main__':
    main()

