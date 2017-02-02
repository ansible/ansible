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
module: nxos_snmp_user
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages SNMP users for monitoring.
description:
    - Manages SNMP user configuration.
author:
    - Jason Edelman (@jedelman8)
notes:
    - Authentication parameters not idempotent.
options:
    user:
        description:
            - Name of the user.
        required: true
    group:
        description:
            - Group to which the user will belong to.
        required: true
    auth:
        description:
            - Auth parameters for the user.
        required: false
        default: null
        choices: ['md5', 'sha']
    pwd:
        description:
            - Auth password when using md5 or sha.
        required: false
        default: null
    privacy:
        description:
            - Privacy password for the user.
        required: false
        default: null
    encrypt:
        description:
            - Enables AES-128 bit encryption when using privacy password.
        required: false
        default: null
        choices: ['true','false']
    state:
        description:
            - Manage the state of the resource.
        required: false
        default: present
        choices: ['present','absent']
'''

EXAMPLES = '''
- nxos_snmp_user:
    user: ntc
    group: network-operator
    auth: md5
    pwd: test_password
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"authentication": "md5", "group": "network-operator",
            "pwd": "test_password", "user": "ntc"}
existing:
    description:
        - k/v pairs of existing configuration
    returned: always
    type: dict
    sample: {"authentication": "no", "encrypt": "none",
             "group": ["network-operator"], "user": "ntc"}
end_state:
    description: k/v pairs configuration vtp after module execution
    returned: always
    type: dict
    sample: {"authentication": "md5", "encrypt": "none",
             "group": ["network-operator"], "user": "ntc"}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["snmp-server user ntc network-operator auth md5 test_password"]
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


def execute_show_command(command, module, command_type='cli_show', text=False):
    if module.params['transport'] == 'cli':
        if 'show run' not in command and text is False:
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


def get_snmp_groups(module):
    command = 'show snmp group'
    body = execute_show_command(command, module)
    g_list = []

    try:
        group_table = body[0]['TABLE_role']['ROW_role']
        for each in group_table:
            g_list.append(each['role_name'])

    except (KeyError, AttributeError, IndexError):
        return g_list

    return g_list


def get_snmp_user(user, module):
    command = 'show snmp user {0}'.format(user)
    body = execute_show_command(command, module, text=True)

    if 'No such entry' not in body[0]:
        body = execute_show_command(command, module)

    resource = {}
    group_list = []
    try:
        resource_table = body[0]['TABLE_snmp_users']['ROW_snmp_users']
        resource['user'] = str(resource_table['user'])
        resource['authentication'] = str(resource_table['auth']).strip()
        encrypt = str(resource_table['priv']).strip()
        if encrypt.startswith('aes'):
            resource['encrypt'] = 'aes-128'
        else:
            resource['encrypt'] = 'none'

        group_table = resource_table['TABLE_groups']['ROW_groups']

        groups = []
        try:
            for group in group_table:
                groups.append(str(group['group']).strip())
        except TypeError:
            groups.append(str(group_table['group']).strip())

        resource['group'] = groups

    except (KeyError, AttributeError, IndexError, TypeError):
        return resource

    return resource


def remove_snmp_user(user):
    return ['no snmp-server user {0}'.format(user)]


def config_snmp_user(proposed, user, reset, new):
    if reset and not new:
        commands = remove_snmp_user(user)
    else:
        commands = []

    group = proposed.get('group', None)

    cmd = ''

    if group:
        cmd = 'snmp-server user {0} {group}'.format(user, **proposed)

    auth = proposed.get('authentication', None)
    pwd = proposed.get('pwd', None)

    if auth and pwd:
        cmd += ' auth {authentication} {pwd}'.format(**proposed)

    encrypt = proposed.get('encrypt', None)
    privacy = proposed.get('privacy', None)

    if encrypt and privacy:
        cmd += ' priv {encrypt} {privacy}'.format(**proposed)
    elif privacy:
        cmd += ' priv {privacy}'.format(**proposed)

    if cmd:
        commands.append(cmd)

    return commands


def main():
    argument_spec = dict(
        user=dict(required=True, type='str'),
        group=dict(type='str', required=True),
        pwd=dict(type='str'),
        privacy=dict(type='str'),
        authentication=dict(choices=['md5', 'sha']),
        encrypt=dict(type='bool'),
        state=dict(choices=['absent', 'present'], default='present'),
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                                required_together=[['authentication', 'pwd'],
                                                  ['encrypt', 'privacy']],
                                supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)


    user = module.params['user']
    group = module.params['group']
    pwd = module.params['pwd']
    privacy = module.params['privacy']
    encrypt = module.params['encrypt']
    authentication = module.params['authentication']
    state = module.params['state']

    if privacy and encrypt:
        if not pwd and authentication:
            module.fail_json(msg='pwd and authentication must be provided '
                                 'when using privacy and encrypt')

    if group and group not in get_snmp_groups(module):
        module.fail_json(msg='group not configured yet on switch.')

    existing = get_snmp_user(user, module)
    end_state = existing

    store = existing.get('group', None)
    if existing:
        if group not in existing['group']:
            existing['group'] = None
        else:
            existing['group'] = group

    changed = False
    commands = []
    proposed = {}

    if state == 'absent' and existing:
        commands.append(remove_snmp_user(user))

    elif state == 'present':
        new = False
        reset = False

        args = dict(user=user, pwd=pwd, group=group, privacy=privacy,
                    encrypt=encrypt, authentication=authentication)
        proposed = dict((k, v) for k, v in args.items() if v is not None)

        if not existing:
            if encrypt:
                proposed['encrypt'] = 'aes-128'
            commands.append(config_snmp_user(proposed, user, reset, new))

        elif existing:
            if encrypt and not existing['encrypt'].startswith('aes'):
                reset = True
                proposed['encrypt'] = 'aes-128'

            elif encrypt:
                proposed['encrypt'] = 'aes-128'

            delta = dict(
                set(proposed.items()).difference(existing.items()))

            if delta.get('pwd'):
                delta['authentication'] = authentication

            if delta:
                delta['group'] = group

            command = config_snmp_user(delta, user, reset, new)
            commands.append(command)

    cmds = flatten_list(commands)
    results = {}
    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            changed = True
            load_config(module, cmds)
            end_state = get_snmp_user(user, module)
            if 'configure' in cmds:
                cmds.pop(0)

    if store:
        existing['group'] = store

    results['proposed'] = proposed
    results['existing'] = existing
    results['updates'] = cmds
    results['changed'] = changed
    results['warnings'] = warnings
    results['end_state'] = end_state

    module.exit_json(**results)


if __name__ == "__main__":
    main()

