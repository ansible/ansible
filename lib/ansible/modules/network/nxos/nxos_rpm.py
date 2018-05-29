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
module: nxos_rpm
extends_documentation_fragment: nxos
version_added: "2.7"
short_description: Install rpms on Cisco NX-OS devices.
description:
    - Install software maintenance upgrade (smu) RPMS and
      3rd party RPMS on Cisco NX-OS devices.
author: Sai Chintalapudi (@saichint)
notes:
    - Tested against NXOSv 7.0(3)I7(3) on VIRL
    - The module can add, activate and commit a package,
      and also decactivate and remove it.
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
        default: bootflash
    state:
        description:
            - If the state is present, the rpm will be installed,
              if the state is absent, it will be removed.
        default: present.
        choices: ['present', 'absent']
'''

EXAMPLES = '''
- nxos_rpm:
    pkg: "nxos.sample-n9k_ALL-1.0.0-7.0.3.I7.3.lib32_n9000.rpm"
'''

RETURN = '''
commands:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["install add bootflash:nxos.sample-n9k_ALL-1.0.0-7.0.3.I7.3.lib32_n9000.rpm forced",
             "install activate nxos.sample-n9k_ALL-1.0.0-7.0.3.I7.3.lib32_n9000 forced",
             "install commit nxos.sample-n9k_ALL-1.0.0-7.0.3.I7.3.lib32_n9000"]
'''


import time

from ansible.module_utils.network.nxos.nxos import load_config, run_commands
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule


def execute_show_command(command, module):
    iteration = 0
    cmds = [{
        'command': command,
        'output': 'text',
    }]

    while iteration < 10:
        body = run_commands(module, cmds)[0]
        if body:
            return body
        else:
            time.sleep(2)
            iteration += 1


def remote_file_exists(module, dst, file_system):
    command = 'dir {0}:/{1}'.format(file_system, dst)
    body = execute_show_command(command, module)
    if 'No such file' in body:
        return False
    return True


def config_cmd_operation(module, cmd):
    iteration = 0
    while iteration < 10:
        msg = load_config(module, [cmd], True)
        if msg:
            if 'Another install operation is in progress' in msg[0]:
                time.sleep(2)
                iteration += 1
            else:
                return
        else:
            return


def validate_operation(module, show_cmd, cfg_cmd, pkg, pkg_not_present):
    iteration = 0
    while iteration < 10:
        body = execute_show_command(show_cmd, module)
        if pkg_not_present:
            if pkg not in body:
                return
        else:
            if pkg in body:
                return
        time.sleep(2)
        iteration += 1

    err = 'Operation "{0}" Failed'.format(cfg_cmd)
    module.fail_json(msg=err)


def add_operation(module, show_cmd, file_system, pkg, fixed_pkg):
    cmd = 'install add {0}:{1}'.format(file_system, pkg)
    config_cmd_operation(module, cmd)
    validate_operation(module, show_cmd, cmd, fixed_pkg, False)
    return cmd


def activate_operation(module, show_cmd, fixed_pkg):
    cmd = 'install activate {0} forced'.format(fixed_pkg)
    config_cmd_operation(module, cmd)
    validate_operation(module, show_cmd, cmd, fixed_pkg, False)
    return cmd


def commit_operation(module, show_cmd, fixed_pkg):
    cmd = 'install commit {0}'.format(fixed_pkg)
    config_cmd_operation(module, cmd)
    validate_operation(module, show_cmd, cmd, fixed_pkg, False)
    return cmd


def deactivate_operation(module, show_cmd, fixed_pkg, flag):
    cmd = 'install deactivate {0} forced'.format(fixed_pkg)
    config_cmd_operation(module, cmd)
    validate_operation(module, show_cmd, cmd, fixed_pkg, flag)
    return cmd


def remove_operation(module, show_cmd, fixed_pkg):
    cmd = 'install remove {0} forced'.format(fixed_pkg)
    config_cmd_operation(module, cmd)
    validate_operation(module, show_cmd, cmd, fixed_pkg, True)
    return cmd


def install_remove_rpm(module, pkg, file_system, state):
    commands = []

    splitted_pkg = pkg.split('.')
    fixed_pkg = '.'.join(splitted_pkg[0:-1])

    show_inactive = 'show install inactive'
    show_active = 'show install active'
    show_commit = 'show install committed'
    show_patches = 'show install patches'

    if state == 'present':
        inactive_body = execute_show_command(show_inactive, module)
        active_body = execute_show_command(show_active, module)

        if fixed_pkg not in inactive_body and fixed_pkg not in active_body:
            commands.append(add_operation(module, show_inactive, file_system, pkg, fixed_pkg))

        if fixed_pkg not in active_body:
            commands.append(activate_operation(module, show_active, fixed_pkg))

        commit_body = execute_show_command(show_commit, module)
        if fixed_pkg not in commit_body:
            patch_body = execute_show_command(show_patches, module)
            if fixed_pkg in patch_body:
                # this is an smu
                commands.append(commit_operation(module, show_active, fixed_pkg))
            else:
                err = 'Operation "install activate {0} forced" Failed'.format(fixed_pkg)
                module.fail_json(msg=err)

    else:
        commit_body = execute_show_command(show_commit, module)
        active_body = execute_show_command(show_active, module)

        if fixed_pkg in commit_body and fixed_pkg in active_body:
            commands.append(deactivate_operation(module, show_active, fixed_pkg, True))
            commit_body = execute_show_command(show_commit, module)
            if fixed_pkg in commit_body:
                # this is smu
                commands.append(commit_operation(module, show_inactive, fixed_pkg))
            commands.append(remove_operation(module, show_inactive, fixed_pkg))

        elif fixed_pkg in commit_body:
            # this is smu
            commands.append(commit_operation(module, show_inactive, fixed_pkg))
            commands.append(remove_operation(module, show_inactive, fixed_pkg))

        elif fixed_pkg in active_body:
            # this is smu
            commands.append(deactivate_operation(module, show_inactive, fixed_pkg, False))
            commands.append(remove_operation(module, show_inactive, fixed_pkg))

        else:
            inactive_body = execute_show_command(show_inactive, module)
            if fixed_pkg in inactive_body:
                commands.append(remove_operation(module, show_inactive, fixed_pkg))

    return commands


def main():
    argument_spec = dict(
        pkg=dict(required=True),
        file_system=dict(required=False, default='bootflash'),
        state=dict(choices=['absent', 'present'], required=False, default='present')
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=False)

    warnings = list()
    check_args(module, warnings)
    results = {'changed': False, 'commands': [], 'warnings': warnings}

    pkg = module.params['pkg']
    file_system = module.params['file_system']
    state = module.params['state']

    if state == 'present':
        remote_exists = remote_file_exists(module, pkg, file_system=file_system)

        if not remote_exists:
            module.fail_json(
                msg="The requested package doesn't exist on the device"
            )

    cmds = install_remove_rpm(module, pkg, file_system, state)

    if cmds:
        results['changed'] = True
        results['commands'] = cmds

    module.exit_json(**results)


if __name__ == '__main__':
    main()
