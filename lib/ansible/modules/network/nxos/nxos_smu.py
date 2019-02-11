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
module: nxos_smu
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Perform SMUs on Cisco NX-OS devices.
description:
    - Perform software maintenance upgrades (SMUs) on Cisco NX-OS devices.
author: Gabriele Gerbino (@GGabriele)
notes:
    - Tested against NXOSv 7.3.(0)D1(1) on VIRL
    - The module can only activate and commit a package,
      not remove or deactivate it.
    - Use C(transport=nxapi) to avoid connection timeout
options:
    pkg:
        description:
            - Name of the remote package.
        required: true
    file_system:
        description:
            - The remote file system of the device. If omitted,
              devices that support a file_system parameter will use
              their default values.
'''

EXAMPLES = '''
- nxos_smu:
    pkg: "nxos.CSCuz65185-n9k_EOR-1.0.0-7.0.3.I2.2d.lib32_n9000.rpm"
'''

RETURN = '''
commands:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["install add bootflash:nxos.CSCuz65185-n9k_EOR-1.0.0-7.0.3.I2.2d.lib32_n9000.rpm",
             "install activate bootflash:nxos.CSCuz65185-n9k_EOR-1.0.0-7.0.3.I2.2d.lib32_n9000.rpm force",
             "install commit bootflash:nxos.CSCuz65185-n9k_EOR-1.0.0-7.0.3.I2.2d.lib32_n9000.rpm"]
'''


import collections
import re
import time

from ansible.module_utils.network.nxos.nxos import get_config, load_config, run_commands
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule


def execute_show_command(command, module):
    cmds = [{
        'command': command,
        'output': 'text',
    }]

    return run_commands(module, cmds)


def remote_file_exists(module, dst, file_system='bootflash:'):
    command = 'dir {0}/{1}'.format(file_system, dst)
    body = execute_show_command(command, module)
    if 'No such file' in body[0]:
        return False
    return True


def apply_patch(module, commands):
    for command in commands:
        load_config(module, [command])
        time.sleep(5)


def get_commands(module, pkg, file_system):
    commands = []
    splitted_pkg = pkg.split('.')
    fixed_pkg = '.'.join(splitted_pkg[0:-1])

    command = 'show install inactive'
    inactive_body = execute_show_command(command, module)

    command = 'show install active'
    active_body = execute_show_command(command, module)

    if fixed_pkg not in inactive_body[0] and fixed_pkg not in active_body[0]:
        commands.append('install add {0}{1}'.format(file_system, pkg))

    if fixed_pkg not in active_body[0]:
        commands.append('install activate {0}{1} force'.format(
            file_system, pkg))
    command = 'show install committed'
    install_body = execute_show_command(command, module)
    if fixed_pkg not in install_body[0]:
        commands.append('install commit {0}{1}'.format(file_system, pkg))

    return commands


def main():
    argument_spec = dict(
        pkg=dict(required=True),
        file_system=dict(required=False, default='bootflash:'),
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)
    results = {'changed': False, 'commands': [], 'warnings': warnings}

    pkg = module.params['pkg']
    file_system = module.params['file_system']
    remote_exists = remote_file_exists(module, pkg, file_system=file_system)

    if not remote_exists:
        module.fail_json(
            msg="The requested package doesn't exist on the device"
        )

    commands = get_commands(module, pkg, file_system)
    if commands:
        results['changed'] = True
        if not module.check_mode:
            apply_patch(module, commands)
        if 'configure' in commands:
            commands.pop(0)
        results['commands'] = commands

    module.exit_json(**results)


if __name__ == '__main__':
    main()
