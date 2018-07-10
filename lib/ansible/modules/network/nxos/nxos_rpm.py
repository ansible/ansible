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
short_description: Install patch or feature rpms on Cisco NX-OS devices.
description:
    - Install software maintenance upgrade (smu) RPMS and
      3rd party RPMS on Cisco NX-OS devices.
author: Sai Chintalapudi (@saichint)
notes:
    - Tested against NXOSv 7.0(3)I2(5), 7.0(3)I4(6), 7.0(3)I5(3),
      7.0(3)I6(1), 7.0(3)I7(3)
    - For patches, the minimum platform version needed is 7.0(3)I2(5)
    - For feature rpms, the minimum platform version needed is 7.0(3)I6(1)
    - The module manages the entire RPM lifecycle (Add, activate, commit, deactivate, remove)
    - For reload patches, this module is NOT idempotent until the patch is
      committed.
options:
    pkg:
        description:
            - Name of the RPM package.
        required: true
    file_system:
        description:
            - The remote file system of the device. If omitted,
              devices that support a file_system parameter will use
              their default values.
        default: bootflash
    aggregate:
        description:
            - List of RPM/patch definitions.
    state:
        description:
            - If the state is present, the rpm will be installed,
              If the state is absent, it will be removed.
        default: present
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

from copy import deepcopy

from ansible.module_utils.network.nxos.nxos import load_config, run_commands
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import remove_default_spec


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
            if 'another install operation is in progress' in msg[0].lower() or 'failed' in msg[0].lower():
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


def add_operation(module, show_cmd, file_system, full_pkg, pkg):
    cmd = 'install add {0}:{1}'.format(file_system, full_pkg)
    config_cmd_operation(module, cmd)
    validate_operation(module, show_cmd, cmd, pkg, False)
    return cmd


def activate_operation(module, show_cmd, pkg):
    cmd = 'install activate {0} forced'.format(pkg)
    config_cmd_operation(module, cmd)
    validate_operation(module, show_cmd, cmd, pkg, False)
    return cmd


def activate_reload(module, pkg, flag):
    iteration = 0
    if flag:
        cmd = 'install activate {0} forced'.format(pkg)
    else:
        cmd = 'install deactivate {0} forced'.format(pkg)
    opts = {'ignore_timeout': True}
    while iteration < 10:
        msg = load_config(module, [cmd], True, opts)
        if msg:
            if isinstance(msg[0], int):
                if msg[0] == -32603:
                    return cmd
            elif isinstance(msg[0], str):
                if 'another install operation is in progress' in msg[0].lower() or 'failed' in msg[0].lower():
                    time.sleep(2)
                    iteration += 1


def commit_operation(module, show_cmd, pkg):
    cmd = 'install commit {0}'.format(pkg)
    config_cmd_operation(module, cmd)
    validate_operation(module, show_cmd, cmd, pkg, False)
    return cmd


def deactivate_operation(module, show_cmd, pkg, flag):
    cmd = 'install deactivate {0} forced'.format(pkg)
    config_cmd_operation(module, cmd)
    validate_operation(module, show_cmd, cmd, pkg, flag)
    return cmd


def remove_operation(module, show_cmd, pkg):
    cmd = 'install remove {0} forced'.format(pkg)
    config_cmd_operation(module, cmd)
    validate_operation(module, show_cmd, cmd, pkg, True)
    return cmd


def install_remove_rpm(module, full_pkg, file_system, state):
    commands = []
    reload_patch = False

    splitted_pkg = full_pkg.split('.')
    pkg = '.'.join(splitted_pkg[0:-1])

    show_inactive = 'show install inactive'
    show_active = 'show install active'
    show_commit = 'show install committed'
    show_patches = 'show install patches'
    show_pkg_info = 'show install pkg-info {0}'.format(pkg)

    if state == 'present':
        inactive_body = execute_show_command(show_inactive, module)
        active_body = execute_show_command(show_active, module)

        if pkg not in inactive_body and pkg not in active_body:
            commands.append(add_operation(module, show_inactive, file_system, full_pkg, pkg))

        patch_type_body = execute_show_command(show_pkg_info, module)
        if patch_type_body and 'Patch Type    :  reload' in patch_type_body:
            # This is reload smu/patch rpm
            reload_patch = True

        if pkg not in active_body:
            if reload_patch:
                commands.append(activate_reload(module, pkg, True))
                return commands
            else:
                commands.append(activate_operation(module, show_active, pkg))

        commit_body = execute_show_command(show_commit, module)
        if pkg not in commit_body:
            patch_body = execute_show_command(show_patches, module)
            if pkg in patch_body:
                # This is smu/patch rpm
                commands.append(commit_operation(module, show_active, pkg))
            else:
                err = 'Operation "install activate {0} forced" Failed'.format(pkg)
                module.fail_json(msg=err)

    else:
        commit_body = execute_show_command(show_commit, module)
        active_body = execute_show_command(show_active, module)

        patch_type_body = execute_show_command(show_pkg_info, module)
        if patch_type_body and 'Patch Type    :  reload' in patch_type_body:
            # This is reload smu/patch rpm
            reload_patch = True

        if pkg in commit_body and pkg in active_body:
            if reload_patch:
                commands.append(activate_reload(module, pkg, False))
                return commands
            else:
                commands.append(deactivate_operation(module, show_active, pkg, True))
                commit_body = execute_show_command(show_commit, module)
                if pkg in commit_body:
                    # This is smu/patch rpm
                    commands.append(commit_operation(module, show_inactive, pkg))
                commands.append(remove_operation(module, show_inactive, pkg))

        elif pkg in commit_body:
            # This is smu/patch rpm
            commands.append(commit_operation(module, show_inactive, pkg))
            commands.append(remove_operation(module, show_inactive, pkg))

        elif pkg in active_body:
            # This is smu/patch rpm
            if reload_patch:
                commands.append(activate_reload(module, pkg, False))
                return commands
            else:
                commands.append(deactivate_operation(module, show_inactive, pkg, False))
                commands.append(remove_operation(module, show_inactive, pkg))

        else:
            inactive_body = execute_show_command(show_inactive, module)
            if pkg in inactive_body:
                commands.append(remove_operation(module, show_inactive, pkg))

    return commands


def main():
    element_spec = dict(
        pkg=dict(type='str'),
        file_system=dict(type='str', default='bootflash'),
        state=dict(choices=['absent', 'present'], default='present')
    )

    aggregate_spec = deepcopy(element_spec)
    aggregate_spec['pkg'] = dict(required=True)

    # remove default in aggregate spec, to handle common arguments
    remove_default_spec(aggregate_spec)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec)
    )

    argument_spec.update(element_spec)
    argument_spec.update(nxos_argument_spec)

    required_one_of = [['pkg', 'aggregate']]
    mutually_exclusive = [['pkg', 'aggregate']]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=required_one_of,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=False)

    warnings = list()
    results = {'changed': False, 'commands': [], 'warnings': warnings}

    aggregate = module.params.get('aggregate')
    objects = []
    if aggregate:
        for item in aggregate:
            for key in item:
                if item.get(key) is None:
                    item[key] = module.params[key]

            d = item.copy()
            objects.append(d)
    else:
        objects.append({
            'pkg': module.params['pkg'],
            'file_system': module.params['file_system'],
            'state': module.params['state']
        })

    for obj in objects:
        if obj['state'] == 'present':
            remote_exists = remote_file_exists(module, obj['pkg'], file_system=obj['file_system'])

            if not remote_exists:
                module.fail_json(
                    msg="The requested package doesn't exist on the device"
                )

        cmds = install_remove_rpm(module, obj['pkg'], obj['file_system'], obj['state'])

        if cmds:
            results['changed'] = True
            results['commands'].extend(cmds)

    module.exit_json(**results)


if __name__ == '__main__':
    main()
