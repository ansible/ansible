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
module: nxos_snmp_location
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages SNMP location information.
description:
    - Manages SNMP location configuration.
author:
    - Jason Edelman (@jedelman8)
    - Gabriele Gerbino (@GGabriele)
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
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"

# ensure snmp location is not configured
- nxos_snmp_location:
    location: Test
    state: absent
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"location": "New_Test"}
existing:
    description: k/v pairs of existing snmp location
    returned: always
    type: dict
    sample: {"location": "Test"}
end_state:
    description: k/v pairs of location info after module execution
    returned: always
    type: dict
    sample: {"location": "New_Test"}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["snmp-server location New_Test"]
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


def apply_key_map(key_map, table):
    new_dict = {}
    for key, value in table.items():
        new_key = key_map.get(key)
        if new_key:
            value = table.get(key)
            if value:
                new_dict[new_key] = str(value)
            else:
                new_dict[new_key] = value
    return new_dict


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
    location_regex = '.*snmp-server\slocation\s(?P<location>\S+).*'
    command = 'show run snmp'

    body = execute_show_command(command, module, command_type='cli_show_ascii')
    try:
        match_location = re.match(location_regex, body[0], re.DOTALL)
        group_location = match_location.groupdict()
        location['location'] = group_location["location"]
    except (AttributeError, TypeError):
        location = {}

    return location


def main():
    argument_spec = dict(
        location=dict(required=True, type='str'),
        state=dict(choices=['absent', 'present'],
                       default='present')
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                                supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)



    location = module.params['location']
    state = module.params['state']

    existing = get_snmp_location(module)
    changed = False
    commands = []
    proposed = dict(location=location)
    end_state = existing

    if state == 'absent':
        if existing and existing['location'] == location:
            commands.append('no snmp-server location')
    elif state == 'present':
        if not existing or existing['location'] != location:
            commands.append('snmp-server location {0}'.format(location))

    cmds = flatten_list(commands)
    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            changed = True
            load_config(module, cmds)
            end_state = get_snmp_location(module)
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


from ansible.module_utils.basic import *
if __name__ == "__main__":
    main()

