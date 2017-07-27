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


from ansible.module_utils.nxos import nxos_argument_spec, run_commands
from ansible.module_utils.basic import AnsibleModule


def checkpoint(filename, module):
    commands = [{
        'command': 'terminal dont-ask',
        'output': 'text', }, {
        'command': 'checkpoint file %s' % filename,
        'output': 'text',
    }]
    run_commands(module, commands)


def rollback(filename, module):
    commands = [{
        'command': 'rollback running-config file %s' % filename,
        'output': 'text',
    }]
    run_commands(module, commands)


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

    if checkpoint_file:
        checkpoint(checkpoint_file, module)
        status = 'checkpoint file created'
    elif rollback_to:
        rollback(rollback_to, module)
        status = 'rollback executed'
    changed = True
    filename = rollback_to or checkpoint_file

    module.exit_json(changed=changed, status=status, filename=filename)


if __name__ == '__main__':
    main()
