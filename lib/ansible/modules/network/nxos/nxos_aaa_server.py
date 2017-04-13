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

module: nxos_aaa_server
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages AAA server global configuration.
description:
    - Manages AAA server global configuration
author:
    - Jason Edelman (@jedelman8)
notes:
    - The server_type parameter is always required.
    - If encrypt_type is not supplied, the global AAA server key will be
      stored as encrypted (type 7).
    - Changes to the global AAA server key with encrypt_type=0
      are not idempotent.
    - If global AAA server key is not found, it's shown as "unknown"
    - state=default will set the supplied parameters to their default values.
      The parameters that you want to default must also be set to default.
      If global_key=default, the global key will be removed.
options:
    server_type:
        description:
            - The server type is either radius or tacacs.
        required: true
        choices: ['radius', 'tacacs']
    global_key:
        description:
            - Global AAA shared secret.
        required: false
        default: null
    encrypt_type:
        description:
            - The state of encryption applied to the entered global key.
              O clear text, 7 encrypted. Type-6 encryption is not supported.
        required: false
        default: null
        choices: ['0', '7']
    deadtime:
        description:
            - Duration for which a non-reachable AAA server is skipped,
              in minutes. Range is 1-1440. Device default is 0.
        required: false
        default: null
    server_timeout:
        description:
            - Global AAA server timeout period, in seconds. Range is 1-60.
              Device default is 5.
        required: false
        default: null
    directed_request:
        description:
            - Enables direct authentication requests to AAA server.
              Device default is disabled.
        required: false
        default: null
        choices: ['enabled', 'disabled']
    state:
        description:
            - Manage the state of the resource.
        required: true
        default: present
        choices: ['present','default']
'''

EXAMPLES = '''
# Radius Server Basic settings
  - name: "Radius Server Basic settings"
    nxos_aaa_server:
        server_type: radius
        server_timeout: 9
        deadtime: 20
        directed_request: enabled
        host:  inventory_hostname }}
        username:  un }}
        password:  pwd }}

# Tacacs Server Basic settings
  - name: "Tacacs Server Basic settings"
    nxos_aaa_server:
        server_type: tacacs
        server_timeout: 8
        deadtime: 19
        directed_request: disabled
        host:  inventory_hostname }}
        username:  un }}
        password:  pwd }}

# Setting Global Key
  - name: "AAA Server Global Key"
    nxos_aaa_server:
        server_type: radius
        global_key: test_key
        host:  inventory_hostname }}
        username:  un }}
        password:  pwd }}
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"deadtime": "22", "directed_request": "enabled",
            "server_type": "radius", "server_timeout": "11"}
existing:
    description:
        - k/v pairs of existing aaa server
    returned: always
    type: dict
    sample: {"deadtime": "0", "directed_request": "disabled",
            "global_key": "unknown", "server_timeout": "5"}
end_state:
    description: k/v pairs of aaa params after module execution
    returned: always
    type: dict
    sample: {"deadtime": "22", "directed_request": "enabled",
            "global_key": "unknown", "server_timeout": "11"}
state:
    description: state as sent in from the playbook
    returned: always
    type: string
    sample: "present"
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["radius-server deadtime 22", "radius-server timeout 11",
             "radius-server directed-request"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''
import re

from ansible.module_utils.nxos import load_config, run_commands
from ansible.module_utils.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule


def execute_show_command(command, module, command_type='cli_show'):
    cmds = [command]
    if module.params['transport'] == 'cli':
        body = run_commands(module, cmds)
    elif module.params['transport'] == 'nxapi':
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



def get_aaa_server_info(server_type, module):
    aaa_server_info = {}
    server_command = 'show {0}-server'.format(server_type)
    request_command = 'show {0}-server directed-request'.format(server_type)
    global_key_command = 'show run | sec {0}'.format(server_type)
    aaa_regex = '.*{0}-server\skey\s\d\s+(?P<key>\S+).*'.format(server_type)

    server_body = execute_show_command(
        server_command, module, command_type='cli_show_ascii')[0]

    split_server = server_body.splitlines()

    for line in split_server:
        if line.startswith('timeout'):
            aaa_server_info['server_timeout'] = line.split(':')[1]

        elif line.startswith('deadtime'):
            aaa_server_info['deadtime'] = line.split(':')[1]

    request_body = execute_show_command(
        request_command, module, command_type='cli_show_ascii')[0]
    aaa_server_info['directed_request'] = request_body.replace('\n', '')

    key_body = execute_show_command(
        global_key_command, module, command_type='cli_show_ascii')[0]

    try:
        match_global_key = re.match(aaa_regex, key_body, re.DOTALL)
        group_key = match_global_key.groupdict()
        aaa_server_info['global_key'] = group_key["key"].replace('\"', '')
    except (AttributeError, TypeError):
        aaa_server_info['global_key'] = 'unknown'

    return aaa_server_info


def set_aaa_server_global_key(encrypt_type, key, server_type):
    if not encrypt_type:
        encrypt_type = ''
    return '{0}-server key {1} {2}'.format(
        server_type, encrypt_type, key)


def config_aaa_server(params, server_type):
    cmds = []

    deadtime = params.get('deadtime')
    server_timeout = params.get('server_timeout')
    directed_request = params.get('directed_request')
    encrypt_type = params.get('encrypt_type', '7')
    global_key = params.get('global_key')

    if deadtime is not None:
        cmds.append('{0}-server deadtime {1}'.format(server_type, deadtime))

    if server_timeout is not None:
        cmds.append('{0}-server timeout {1}'.format(server_type, server_timeout))

    if directed_request is not None:
        if directed_request == 'enabled':
            cmds.append('{0}-server directed-request'.format(server_type))
        elif directed_request == 'disabled':
            cmds.append('no {0}-server directed-request'.format(server_type))

    if global_key is not None:
        cmds.append('{0}-server key {1} {2}'.format(server_type, encrypt_type,
                                                    global_key))

    return cmds


def default_aaa_server(existing, params, server_type):
    cmds = []

    deadtime = params.get('deadtime')
    server_timeout = params.get('server_timeout')
    directed_request = params.get('directed_request')
    global_key = params.get('global_key')
    existing_key = existing.get('global_key')

    if deadtime is not None:
        cmds.append('no {0}-server deadtime 1'.format(server_type))

    if server_timeout is not None:
        cmds.append('no {0}-server timeout 1'.format(server_type))

    if directed_request is not None:
        cmds.append('no {0}-server directed-request'.format(server_type))

    if global_key is not None and existing_key is not None:
        cmds.append('no {0}-server key 7 {1}'.format(server_type, existing_key))

    return cmds


def main():
    argument_spec = dict(
        server_type=dict(type='str',
                             choices=['radius', 'tacacs'], required=True),
        global_key=dict(type='str'),
        encrypt_type=dict(type='str', choices=['0', '7']),
        deadtime=dict(type='str'),
        server_timeout=dict(type='str'),
        directed_request=dict(type='str',
                                  choices=['enabled', 'disabled', 'default']),
        state=dict(choices=['default', 'present'], default='present'),
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                                supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)


    server_type = module.params['server_type']
    global_key = module.params['global_key']
    encrypt_type = module.params['encrypt_type']
    deadtime = module.params['deadtime']
    server_timeout = module.params['server_timeout']
    directed_request = module.params['directed_request']
    state = module.params['state']

    if encrypt_type and not global_key:
        module.fail_json(msg='encrypt_type must be used with global_key.')

    args = dict(server_type=server_type, global_key=global_key,
                encrypt_type=encrypt_type, deadtime=deadtime,
                server_timeout=server_timeout, directed_request=directed_request)

    changed = False
    proposed = dict((k, v) for k, v in args.items() if v is not None)

    existing = get_aaa_server_info(server_type, module)
    end_state = existing

    commands = []
    if state == 'present':
        if deadtime:
            try:
                if int(deadtime) < 0 or int(deadtime) > 1440:
                    raise ValueError
            except ValueError:
                module.fail_json(
                    msg='deadtime must be an integer between 0 and 1440')

        if server_timeout:
            try:
                if int(server_timeout) < 1 or int(server_timeout) > 60:
                    raise ValueError
            except ValueError:
                module.fail_json(
                    msg='server_timeout must be an integer between 1 and 60')

        delta = dict(set(proposed.items()).difference(
            existing.items()))
        if delta:
            command = config_aaa_server(delta, server_type)
            if command:
                commands.append(command)

    elif state == 'default':
        for key, value in proposed.items():
            if key != 'server_type' and value != 'default':
                module.fail_json(
                    msg='Parameters must be set to "default"'
                        'when state=default')
        command = default_aaa_server(existing, proposed, server_type)
        if command:
            commands.append(command)

    cmds = flatten_list(commands)
    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            changed = True
            load_config(module, cmds)
            end_state = get_aaa_server_info(server_type, module)
            if 'configure' in cmds:
                cmds.pop(0)

    results = {}
    results['proposed'] = proposed
    results['existing'] = existing
    results['updates'] = cmds
    results['changed'] = changed
    results['warnings'] = warnings
    results['end_state'] = end_state

    module.exit_json(**results)


if __name__ == '__main__':
    main()

