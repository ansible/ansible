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

module: nxos_vtp_password
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages VTP password configuration.
description:
    - Manages VTP password configuration.
author:
    - Gabriele Gerbino (@GGabriele)
notes:
    - VTP feature must be active on the device to use this module.
    - This module is used to manage only VTP passwords.
    - Use this in combination with M(nxos_vtp_domain) and M(nxos_vtp_version)
      to fully manage VTP operations.
    - You can set/remove password only if a VTP domain already exist.
    - If C(state=absent) and no C(vtp_password) is provided, it remove the current
      VTP password.
    - If C(state=absent) and C(vtp_password) is provided, the proposed C(vtp_password)
      has to match the existing one in order to remove it.
options:
    vtp_password:
        description:
            - VTP password
        required: false
        default: null
    state:
        description:
            - Manage the state of the resource
        required: false
        default: present
        choices: ['present','absent']
'''

EXAMPLES = '''
# ENSURE VTP PASSWORD IS SET
- nxos_vtp_password:
    password: ntc
    state: present
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"

# ENSURE VTP PASSWORD IS REMOVED
- nxos_vtp_password:
    password: ntc
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
    sample: {"vtp_password": "new_ntc"}
existing:
    description:
        - k/v pairs of existing vtp
    returned: always
    type: dict
    sample: {"domain": "ntc", "version": "1", "vtp_password": "ntc"}
end_state:
    description: k/v pairs of vtp after module execution
    returned: always
    type: dict
    sample: {"domain": "ntc", "version": "1", "vtp_password": "new_ntc"}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["vtp password new_ntc"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''

from ansible.module_utils.nxos import load_config, run_commands
from ansible.module_utils.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule
import re


def execute_show_command(command, module, command_type='cli_show'):
    if 'status' not in command:
        output = 'json'
    else:
        output = 'text'
    cmds = [{
        'command': command,
        'output': output,
    }]
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


def get_vtp_config(module):
    command = 'show vtp status'

    body = execute_show_command(
        command, module)[0]
    vtp_parsed = {}

    if body:
        version_regex = '.*VTP version running\s+:\s+(?P<version>\d).*'
        domain_regex = '.*VTP Domain Name\s+:\s+(?P<domain>\S+).*'

        try:
            match_version = re.match(version_regex, body, re.DOTALL)
            version = match_version.groupdict()['version']
        except AttributeError:
            version = ''

        try:
            match_domain = re.match(domain_regex, body, re.DOTALL)
            domain = match_domain.groupdict()['domain']
        except AttributeError:
            domain = ''

        if domain and version:
            vtp_parsed['domain'] = domain
            vtp_parsed['version'] = version
            vtp_parsed['vtp_password'] = get_vtp_password(module)

    return vtp_parsed


def get_vtp_password(module):
    command = 'show vtp password'
    body = execute_show_command(command, module)[0]
    password = body['passwd']
    if password:
        return str(password)
    else:
        return ""


def main():
    argument_spec = dict(
        vtp_password=dict(type='str', no_log=True),
        state=dict(choices=['absent', 'present'],
                       default='present'),
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                                supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    vtp_password = module.params['vtp_password'] or None
    state = module.params['state']

    existing = get_vtp_config(module)
    end_state = existing

    args = dict(vtp_password=vtp_password)

    changed = False
    proposed = dict((k, v) for k, v in args.items() if v is not None)
    delta = dict(set(proposed.items()).difference(existing.items()))

    commands = []
    if state == 'absent':
        if vtp_password is not None:
            if existing['vtp_password'] == proposed['vtp_password']:
                commands.append(['no vtp password'])
            else:
                module.fail_json(msg="Proposed vtp password doesn't match "
                                     "current vtp password. It cannot be "
                                     "removed when state=absent. If you are "
                                     "trying to change the vtp password, use "
                                     "state=present.")
        else:
            if not existing.get('domain'):
                module.fail_json(msg='Cannot remove a vtp password '
                                     'before vtp domain is set.')

            elif existing['vtp_password'] != ('\\'):
                commands.append(['no vtp password'])

    elif state == 'present':
        if delta:
            if not existing.get('domain'):
                module.fail_json(msg='Cannot set vtp password '
                                     'before vtp domain is set.')

            else:
                commands.append(['vtp password {0}'.format(vtp_password)])

    cmds = flatten_list(commands)
    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            changed = True
            load_config(module, cmds)
            end_state = get_vtp_config(module)
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
