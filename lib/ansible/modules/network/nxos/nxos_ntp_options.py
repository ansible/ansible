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

module: nxos_ntp_options
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages NTP options.
description:
    - Manages NTP options, e.g. authoritative server and logging.
author:
    - Jason Edelman (@jedelman8)
notes:
    - At least one of C(master) or C(logging) params must be supplied.
    - When C(state=absent), boolean parameters are flipped,
      e.g. C(master=true) will disable the authoritative server.
    - When C(state=absent) and C(master=true), the stratum will be removed as well.
    - When C(state=absent) and C(master=false), the stratum will be configured
      to its default value, 8.
options:
    master:
        description:
            - Sets whether the device is an authoritative NTP server.
        required: false
        default: null
        choices: ['true','false']
    stratum:
        description:
            - If C(master=true), an optional stratum can be supplied (1-15).
              The device default is 8.
        required: false
        default: null
    logging:
        description:
            - Sets whether NTP logging is enabled on the device.
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
# Basic NTP options configuration
- nxos_ntp_options:
    master: true
    stratum: 12
    logging: false
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"logging": false, "master": true, "stratum": "11"}
existing:
    description:
        - k/v pairs of existing ntp options
    returned: always
    type: dict
    sample: {"logging": true, "master": true, "stratum": "8"}
end_state:
    description: k/v pairs of ntp options after module execution
    returned: always
    type: dict
    sample: {"logging": false, "master": true, "stratum": "11"}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["no ntp logging", "ntp master 11"]
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


def get_ntp_master(module):
    command = 'show run | inc ntp.master'
    master_string = execute_show_command(command, module, command_type='cli_show_ascii')

    if master_string:
        if master_string[0]:
            master = True
        else:
            master = False
    else:
        master = False

    if master is True:
        stratum = str(master_string[0].split()[2])
    else:
        stratum = None

    return master, stratum


def get_ntp_log(module):
    command = 'show ntp logging'
    body = execute_show_command(command, module)[0]

    logging_string = body['loggingstatus']
    if 'enabled' in logging_string:
        ntp_log = True
    else:
        ntp_log = False

    return ntp_log


def get_ntp_options(module):
    existing = {}
    existing['logging'] = get_ntp_log(module)
    existing['master'], existing['stratum'] = get_ntp_master(module)

    return existing


def config_ntp_options(delta, flip=False):
    master = delta.get('master')
    stratum = delta.get('stratum')
    log = delta.get('logging')
    ntp_cmds = []

    if flip:
        log = not log
        master = not master

    if log is not None:
        if log is True:
            ntp_cmds.append('ntp logging')
        elif log is False:
            ntp_cmds.append('no ntp logging')
    if master is not None:
        if master is True:
            if not stratum:
                stratum = ''
            ntp_cmds.append('ntp master {0}'.format(stratum))
        elif master is False:
            ntp_cmds.append('no ntp master')

    return ntp_cmds


def main():
    argument_spec = dict(
        master=dict(required=False, type='bool'),
        stratum=dict(type='str'),
        logging=dict(required=False, type='bool'),
        state=dict(choices=['absent', 'present'], default='present'),
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                                required_one_of=[['master', 'logging']],
                                supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)


    master = module.params['master']
    stratum = module.params['stratum']
    logging = module.params['logging']
    state = module.params['state']

    if stratum:
        if master is None:
            module.fail_json(msg='The master param must be supplied when '
                                 'stratum is supplied')
        try:
            stratum_int = int(stratum)
            if stratum_int < 1 or stratum_int > 15:
                raise ValueError
        except ValueError:
            module.fail_json(msg='Stratum must be an integer between 1 and 15')

    existing = get_ntp_options(module)
    end_state = existing

    args = dict(master=master, stratum=stratum, logging=logging)

    changed = False
    proposed = dict((k, v) for k, v in args.items() if v is not None)

    if master is False:
        proposed['stratum'] = None
        stratum = None

    delta = dict(set(proposed.items()).difference(existing.items()))
    delta_stratum = delta.get('stratum')

    if delta_stratum:
        delta['master'] = True

    commands = []
    if state == 'present':
        if delta:
            command = config_ntp_options(delta)
            if command:
                commands.append(command)
    elif state == 'absent':
        if existing:
            isection = dict(set(proposed.items()).intersection(
                existing.items()))
            command = config_ntp_options(isection, flip=True)
            if command:
                commands.append(command)

    cmds = flatten_list(commands)
    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            changed = True
            load_config(module, cmds)
            end_state = get_ntp_options(module)
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

