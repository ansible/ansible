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
module: nxos_aaa_server_host
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages AAA server host-specific configuration.
description:
    - Manages AAA server host-specific configuration.
author: Jason Edelman (@jedelman8)
notes:
    - Tested against NXOSv 7.3.(0)D1(1) on VIRL
    - Changes to the AAA server host key (shared secret) are not idempotent.
    - If C(state=absent) removes the whole host configuration.
options:
    server_type:
        description:
            - The server type is either radius or tacacs.
        required: true
        choices: ['radius', 'tacacs']
    address:
        description:
            - Address or name of the radius or tacacs host.
        required: true
    key:
        description:
            - Shared secret for the specified host.
        required: false
        default: null
    encrypt_type:
        description:
            - The state of encryption applied to the entered key.
              O for clear text, 7 for encrypted. Type-6 encryption is
              not supported.
        required: false
        default: null
        choices: ['0', '7']
    host_timeout:
        description:
            - Timeout period for specified host, in seconds. Range is 1-60.
        required: false
        default: null
    auth_port:
        description:
            - Alternate UDP port for RADIUS authentication.
        required: false
        default: null
    acct_port:
        description:
            - Alternate UDP port for RADIUS accounting.
        required: false
        default: null
    tacacs_port:
        description:
            - Alternate TCP port TACACS Server.
        required: false
        default: null
    state:
        description:
            - Manage the state of the resource.
        required: false
        default: present
        choices: ['present','absent']
'''
EXAMPLES = '''
# Radius Server Host Basic settings
  - name: "Radius Server Host Basic settings"
    nxos_aaa_server_host:
        state: present
        server_type: radius
        address: 1.2.3.4
        acct_port: 2084
        host_timeout: 10
        host: "{{ inventory_hostname }}"
        username: "{{ un }}"
        password: "{{ pwd }}"

# Radius Server Host Key Configuration
  - name: "Radius Server Host Key Configuration"
    nxos_aaa_server_host:
        state: present
        server_type: radius
        address: 1.2.3.4
        key: hello
        encrypt_type: 7
        host:  inventory_hostname }}
        username: "{{ un }}"
        password: "{{ pwd }}"

# TACACS Server Host Configuration
  - name: "Tacacs Server Host Configuration"
    nxos_aaa_server_host:
        state: present
        server_type: tacacs
        tacacs_port: 89
        host_timeout: 10
        address: 5.6.7.8
        host:  inventory_hostname }}
        username:  un }}
        password:  pwd }}
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"address": "1.2.3.4", "auth_port": "2084",
            "host_timeout": "10", "server_type": "radius"}
existing:
    description:
        - k/v pairs of existing configuration
    returned: always
    type: dict
    sample: {}
end_state:
    description: k/v pairs of configuration after module execution
    returned: always
    type: dict
    sample: {"address": "1.2.3.4", "auth_port": "2084",
            "host_timeout": "10", "server_type": "radius"}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["radius-server host 1.2.3.4 auth-port 2084 timeout 10"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''
import re

from ansible.module_utils.network.nxos.nxos import load_config, run_commands
from ansible.module_utils.network.nxos.nxos import get_capabilities, nxos_argument_spec
from ansible.module_utils.basic import AnsibleModule


def execute_show_command(command, module, command_type='cli_show'):
    device_info = get_capabilities(module)
    network_api = device_info.get('network_api', 'nxapi')

    if network_api == 'cliconf':
        if 'show run' not in command:
            command += ' | json'
        cmds = [command]
        body = run_commands(module, cmds)
    elif network_api == 'nxapi':
        cmds = {'command': command, 'output': 'text'}
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


def _match_dict(match_list, key_map):
    no_blanks = []
    match_dict = {}

    for match_set in match_list:
        match_set = tuple(v for v in match_set if v)
        no_blanks.append(match_set)

    for info in no_blanks:
        words = info[0].strip().split()
        length = len(words)
        alt_key = key_map.get(words[0])
        first = alt_key or words[0]
        last = words[length - 1]
        match_dict[first] = last.replace('\"', '')

    return match_dict


def get_aaa_host_info(module, server_type, address):
    aaa_host_info = {}
    command = 'show run | inc {0}-server.host.{1}'.format(server_type, address)

    body = execute_show_command(command, module, command_type='cli_show_ascii')

    if body[0]:
        try:
            pattern = (r'(acct-port \d+)|(timeout \d+)|(auth-port \d+)|'
                       r'(key 7 "\w+")|( port \d+)')
            raw_match = re.findall(pattern, body[0])
            aaa_host_info = _match_dict(raw_match, {'acct-port': 'acct_port',
                                                    'auth-port': 'auth_port',
                                                    'port': 'tacacs_port',
                                                    'timeout': 'host_timeout'})
            aaa_host_info['server_type'] = server_type
            aaa_host_info['address'] = address
        except TypeError:
            return {}
    else:
        return {}

    return aaa_host_info


def config_aaa_host(server_type, address, params, clear=False):
    cmds = []

    if clear:
        cmds.append('no {0}-server host {1}'.format(server_type, address))

    cmd_str = '{0}-server host {1}'.format(server_type, address)

    key = params.get('key')
    enc_type = params.get('encrypt_type', '')
    host_timeout = params.get('host_timeout')
    auth_port = params.get('auth_port')
    acct_port = params.get('acct_port')
    port = params.get('tacacs_port')

    if auth_port:
        cmd_str += ' auth-port {0}'.format(auth_port)
    if acct_port:
        cmd_str += ' acct-port {0}'.format(acct_port)
    if port:
        cmd_str += ' port {0}'.format(port)
    if host_timeout:
        cmd_str += ' timeout {0}'.format(host_timeout)
    if key:
        cmds.append('{0}-server host {1} key {2} {3}'.format(server_type,
                                                             address,
                                                             enc_type, key))

    cmds.append(cmd_str)
    return cmds


def main():
    argument_spec = dict(
        server_type=dict(choices=['radius', 'tacacs'], required=True),
        address=dict(type='str', required=True),
        key=dict(type='str'),
        encrypt_type=dict(type='str', choices=['0', '7']),
        host_timeout=dict(type='str'),
        auth_port=dict(type='str'),
        acct_port=dict(type='str'),
        tacacs_port=dict(type='str'),
        state=dict(choices=['absent', 'present'], default='present'),
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    warnings = list()

    server_type = module.params['server_type']
    address = module.params['address']
    key = module.params['key']
    encrypt_type = module.params['encrypt_type']
    host_timeout = module.params['host_timeout']
    auth_port = module.params['auth_port']
    acct_port = module.params['acct_port']
    tacacs_port = module.params['tacacs_port']
    state = module.params['state']

    args = dict(server_type=server_type, address=address, key=key,
                encrypt_type=encrypt_type, host_timeout=host_timeout,
                auth_port=auth_port, acct_port=acct_port,
                tacacs_port=tacacs_port)

    proposed = dict((k, v) for k, v in args.items() if v is not None)
    changed = False

    if encrypt_type and not key:
        module.fail_json(msg='encrypt_type must be used with key')

    if tacacs_port and server_type != 'tacacs':
        module.fail_json(
            msg='tacacs_port can only be used with server_type=tacacs')

    if (auth_port or acct_port) and server_type != 'radius':
        module.fail_json(msg='auth_port and acct_port can only be used'
                             'when server_type=radius')

    existing = get_aaa_host_info(module, server_type, address)
    end_state = existing

    commands = []
    if state == 'present':
        host_timeout = proposed.get('host_timeout')
        if host_timeout:
            try:
                if int(host_timeout) < 1 or int(host_timeout) > 60:
                    raise ValueError
            except ValueError:
                module.fail_json(
                    msg='host_timeout must be an integer between 1 and 60')

        delta = dict(
            set(proposed.items()).difference(existing.items()))
        if delta:
            union = existing.copy()
            union.update(delta)
            command = config_aaa_host(server_type, address, union)
            if command:
                commands.append(command)

    elif state == 'absent':
        intersect = dict(
            set(proposed.items()).intersection(existing.items()))
        if intersect.get('address') and intersect.get('server_type'):
            command = 'no {0}-server host {1}'.format(
                intersect.get('server_type'), intersect.get('address'))
            commands.append(command)

    cmds = flatten_list(commands)
    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            changed = True
            load_config(module, cmds)
            end_state = get_aaa_host_info(module, server_type, address)

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
