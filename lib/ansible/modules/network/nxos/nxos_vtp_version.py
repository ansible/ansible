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

module: nxos_vtp_version
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages VTP version configuration.
description:
    - Manages VTP version configuration.
author:
    - Gabriele Gerbino (@GGabriele)
notes:
    - Tested against NXOSv 7.3.(0)D1(1) on VIRL
    - VTP feature must be active on the device to use this module.
    - This module is used to manage only VTP version.
    - Use this in combination with M(nxos_vtp_password) and M(nxos_vtp_version)
      to fully manage VTP operations.
options:
    version:
        description:
            - VTP version number.
        required: true
        choices: ['1', '2']
'''
EXAMPLES = '''
# ENSURE VTP VERSION IS 2
- nxos_vtp_version:
    version: 2
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"version": "2"}
existing:
    description:
        - k/v pairs of existing vtp
    returned: always
    type: dict
    sample: {"domain": "testing", "version": "1", "vtp_password": "\"}
end_state:
    description: k/v pairs of vtp after module execution
    returned: always
    type: dict
    sample: {"domain": "testing", "version": "2", "vtp_password": "\"}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["vtp version 2"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: bool
    sample: true
'''
from ansible.module_utils.network.nxos.nxos import load_config, run_commands
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule


import re
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


def get_vtp_config(module):
    command = 'show vtp status'
    body = execute_show_command(
        command, module)[0]
    vtp_parsed = {}

    if body:
        version_regex = r'.*VTP version running\s+:\s+(?P<version>\d).*'
        domain_regex = r'.*VTP Domain Name\s+:\s+(?P<domain>\S+).*'

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
    try:
        password = body['passwd']
        if password:
            return str(password)
        else:
            return ""
    except TypeError:
        return ""


def main():
    argument_spec = dict(
        version=dict(type='str', choices=['1', '2'], required=True),
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    version = module.params['version']

    existing = get_vtp_config(module)
    end_state = existing

    args = dict(version=version)

    changed = False
    proposed = dict((k, v) for k, v in args.items() if v is not None)
    delta = dict(set(proposed.items()).difference(existing.items()))

    commands = []
    if delta:
        commands.append(['vtp version {0}'.format(version)])

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
