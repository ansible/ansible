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

DOCUMENTATION = '''
---
module: nxos_vrf
version_added: "2.1"
short_description: Manages global VRF configuration
description:
    - Manages global VRF configuration
extends_documentation_fragment: nxos
author: Jason Edelman (@jedelman8), Gabriele Gerbino (@GGabriele)
notes:
    - Cisco NX-OS creates the default VRF by itself. Therefore,
      you're not allowed to use default as I(vrf) name in this module.
    - I(vrf) name must be shorter than 32 chars.
    - VRF names are not case sensible in NX-OS. Anyway, the name is stored
      just like it's inserted by the user and it'll not be changed again
      unless the VRF is removed and re-created. i.e. I(vrf=NTC) will create
      a VRF named NTC, but running it again with I(vrf=ntc) will not cause
      a configuration change.
options:
    vrf:
        description:
            - Name of VRF to be managed
        required: true
    admin_state:
        description:
            - Administrative state of the VRF
        required: false
        default: up
        choices: ['up','down']
    state:
        description:
            - Manages desired state of the resource
        required: false
        default: present
        choices: ['present','absent']
    description:
        description:
            - Description of the VRF
        required: false
        default: null
'''

EXAMPLES = '''
# ensure ntc VRF exists on switch
- nxos_vrf: vrf=ntc host={{ inventory_hostname }}
# ensure ntc VRF does not exist on switch
- nxos_vrf: vrf=ntc host={{ inventory_hostname }} state=absent
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"admin_state": "Up", "description": "Test test",
            "vrf": "ntc"}
existing:
    description: k/v pairs of existing vrf
    type: dict
    sample: {"admin_state": "Up", "description": "Old test",
            "vrf": "old_ntc"}
end_state:
    description: k/v pairs of vrf info after module execution
    returned: always
    type: dict
    sample: {"admin_state": "Up", "description": "Test test",
            "vrf": "ntc"}
state:
    description: state as sent in from the playbook
    returned: always
    type: string
    sample: "present"
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["vrf context ntc", "shutdown"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''


def execute_config_command(commands, module):
    try:
        module.configure(commands)
    except ShellError:
        clie = get_exception()
        module.fail_json(msg='Error sending CLI commands',
                         error=str(clie), commands=commands)


def get_cli_body_ssh_vrf(command, response):
    """Get response for when transport=cli.  This is kind of a hack and mainly
    needed because these modules were originally written for NX-API.  And
    not every command supports "| json" when using cli/ssh.  As such, we assume
    if | json returns an XML string, it is a valid command, but that the
    resource doesn't exist yet. Instead, the output will be a raw string
    when using multiple |.
    """
    command_splitted = command.split('|')
    if len(command_splitted) > 2:
        body = response
    elif 'xml' in response[0]:
        body = []
    else:
        body = [json.loads(response[0])]
    return body


def execute_show(cmds, module, command_type=None):
    try:
        if command_type:
            response = module.execute(cmds, command_type=command_type)
        else:
            response = module.execute(cmds)
    except ShellError:
        clie = get_exception()
        module.fail_json(msg='Error sending {0}'.format(cmds),
                         error=str(clie))
    return response


def execute_show_command(command, module, command_type='cli_show'):
    if module.params['transport'] == 'cli':
        command += ' | json'
        cmds = [command]
        response = execute_show(cmds, module)
        body = get_cli_body_ssh_vrf(command, response)
    elif module.params['transport'] == 'nxapi':
        cmds = [command]
        body = execute_show(cmds, module, command_type=command_type)

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


def get_commands_to_config_vrf(delta, vrf):
    commands = []
    for param, value in delta.iteritems():
        command = ''
        if param == 'description':
            command = 'description {0}'.format(value)
        elif param == 'admin_state':
            if value.lower() == 'up':
                command = 'no shutdown'
            elif value.lower() == 'down':
                command = 'shutdown'
        if command:
            commands.append(command)
    if commands:
        commands.insert(0, 'vrf context {0}'.format(vrf))
    return commands


def get_vrf_description(vrf, module):
    cmd_type = 'cli_show_ascii'
    command = ('show run section vrf | begin ^vrf\scontext\s{0} '
               '| end ^vrf.*'.format(vrf))

    description = ''
    descr_regex = ".*description\s(?P<descr>[\S+\s]+).*"
    body = execute_show_command(command, module, cmd_type)

    try:
        body = body[0]
        splitted_body = body.split('\n')
    except (AttributeError, IndexError):
        return description

    for element in splitted_body:
        if 'description' in element:
            match_description = re.match(descr_regex, element,
                                         re.DOTALL)
            group_description = match_description.groupdict()
            description = group_description["descr"]

    return description


def get_vrf(vrf, module):
    command = 'show vrf {0}'.format(vrf)
    vrf_key = {
        'vrf_name': 'vrf',
        'vrf_state': 'admin_state'
        }

    body = execute_show_command(command, module)

    try:
        vrf_table = body[0]['TABLE_vrf']['ROW_vrf']
    except (TypeError, IndexError):
        return {}

    parsed_vrf = apply_key_map(vrf_key, vrf_table)
    parsed_vrf['description'] = get_vrf_description(
                                    parsed_vrf['vrf'], module)

    return parsed_vrf


def main():
    argument_spec = dict(
            vrf=dict(required=True),
            description=dict(default=None, required=False),
            admin_state=dict(default='up', choices=['up', 'down'],
                             required=False),
            state=dict(default='present', choices=['present', 'absent'],
                       required=False),
    )
    module = get_module(argument_spec=argument_spec,
                        supports_check_mode=True)

    vrf = module.params['vrf']
    admin_state = module.params['admin_state'].lower()
    description = module.params['description']
    state = module.params['state']

    if vrf == 'default':
        module.fail_json(msg='cannot use default as name of a VRF')
    elif len(vrf) > 32:
        module.fail_json(msg='VRF name exceeded max length of 32',
                         vrf=vrf)

    existing = get_vrf(vrf, module)
    args = dict(vrf=vrf, description=description,
                admin_state=admin_state)

    end_state = existing
    changed = False
    proposed = dict((k, v) for k, v in args.iteritems() if v is not None)

    """Since 'admin_state' is either 'Up' or 'Down' from outputs,
    we use the following to make sure right letter case is used so that delta
    results will be consistent to the actual configuration."""
    if existing:
        if existing['admin_state'].lower() == admin_state:
            proposed['admin_state'] = existing['admin_state']

    delta = dict(set(proposed.iteritems()).difference(existing.iteritems()))
    changed = False
    end_state = existing
    commands = []
    if state == 'absent':
        if existing:
            command = ['no vrf context {0}'.format(vrf)]
            commands.extend(command)

    elif state == 'present':
        if not existing:
            command = get_commands_to_config_vrf(delta, vrf)
            commands.extend(command)
        elif delta:
                command = get_commands_to_config_vrf(delta, vrf)
                commands.extend(command)

    if commands:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            execute_config_command(commands, module)
            changed = True
            end_state = get_vrf(vrf, module)

    results = {}
    results['proposed'] = proposed
    results['existing'] = existing
    results['end_state'] = end_state
    results['state'] = state
    results['updates'] = commands
    results['changed'] = changed

    module.exit_json(**results)


from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
from ansible.module_utils.shell import *
from ansible.module_utils.netcfg import *
from ansible.module_utils.nxos import *
if __name__ == '__main__':
    main()
