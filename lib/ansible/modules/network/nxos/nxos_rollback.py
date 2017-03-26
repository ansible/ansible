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
module: nxos_rollback
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Set a checkpoint or rollback to a checkpoint.
description:
    - This module offers the ability to set a configuration checkpoint
      file or rollback to a configuration checkpoint file on Cisco NXOS
      switches.
author:
    - Jason Edelman (@jedelman8)
    - Gabriele Gerbino (@GGabriele)
notes:
    - Sometimes C(transport=nxapi) may cause a timeout error.
options:
    checkpoint_file:
        description:
            - Name of checkpoint file to create. Mutually exclusive
              with rollback_to.
        required: false
        default: null
    rollback_to:
        description:
            - Name of checkpoint file to rollback to. Mutually exclusive
              with checkpoint_file.
        required: false
        default: null
'''

EXAMPLES = '''
- nxos_rollback:
    checkpoint_file: backup.cfg
    username: "{{ un }}"
    password: "{{ pwd }}"
    host: "{{ inventory_hostname }}"
- nxos_rollback:
    rollback_to: backup.cfg
    username: "{{ un }}"
    password: "{{ pwd }}"
    host: "{{ inventory_hostname }}"
'''

RETURN = '''
filename:
    description: The filename of the checkpoint/rollback file.
    returned: success
    type: string
    sample: 'backup.cfg'
status:
    description: Which operation took place and whether it was successful.
    returned: success
    type: string
    sample: 'rollback executed'
'''


import re
from ansible.module_utils.nxos import get_config, load_config, run_commands
from ansible.module_utils.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.netcfg import CustomNetworkConfig

import re


def execute_commands(cmds, module, command_type=None):
    command_type_map = {
        'cli_show': 'json',
        'cli_show_ascii': 'text'
    }

    try:
        if command_type:
            response = module.execute(cmds, command_type=command_type)
        else:
            response = module.execute(cmds)
    except ShellError:
        clie = get_exception()
        module.fail_json(msg='Error sending {0}'.format(cmds),
                         error=str(clie))
    except AttributeError:
        try:
            if command_type:
                command_type = command_type_map.get(command_type)
                module.cli.add_commands(cmds, output=command_type)
                response = module.cli.run_commands()
            else:
                module.cli.add_commands(cmds, output=command_type)
                response = module.cli.run_commands()
        except ShellError:
            clie = get_exception()
            module.fail_json(msg='Error sending {0}'.format(cmds),
                             error=str(clie))
    return response


def prepare_show_command(command, module):
    if module.params['transport'] == 'cli':
        execute_commands(command, module)
    elif module.params['transport'] == 'nxapi':
        execute_commands(command, module, command_type='cli_show_ascii')


def checkpoint(filename, module):
    commands = ['terminal dont-ask', 'checkpoint file %s' % filename]
    prepare_show_command(commands, module)


def rollback(filename, module):
    commands = ['rollback running-config file %s' % filename]
    try:
        module.configure(commands)
    except AttributeError:
        try:
            module.cli.add_commands(commands, output='config')
            module.cli.run_commands()
        except ShellError:
            clie = get_exception()
            module.fail_json(msg='Error sending CLI commands',
                             error=str(clie), commands=commands)


def main():
    argument_spec = dict(
        checkpoint_file=dict(required=False),
        rollback_to=dict(required=False),
        include_defaults=dict(default=True),
        config=dict(),
        save=dict(type='bool', default=False)
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                        mutually_exclusive=[['checkpoint_file',
                                             'rollback_to']],
                        supports_check_mode=False)

    checkpoint_file = module.params['checkpoint_file']
    rollback_to = module.params['rollback_to']

    status = None
    filename = None
    changed = False
    try:
        if checkpoint_file:
            checkpoint(checkpoint_file, module)
            status = 'checkpoint file created'
        elif rollback_to:
            rollback(rollback_to, module)
            status = 'rollback executed'
        changed = True
        filename = rollback_to or checkpoint_file
    except ShellError:
        clie = get_exception()
        module.fail_json(msg=str(clie))

    module.exit_json(changed=changed, status=status, filename=filename)


if __name__ == '__main__':
    main()

