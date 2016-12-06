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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: nxos_smu
version_added: "2.2"
short_description: Perform SMUs on Cisco NX-OS devices.
description:
    - Perform software maintenance upgrades (SMUs) on Cisco NX-OS devices.
extends_documentation_fragment: nxos
author: Gabriele Gerbino (@GGabriele)
notes:
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
        required: false
        default: null
'''

EXAMPLES = '''
- nxos_smu:
    pkg: "nxos.CSCuz65185-n9k_EOR-1.0.0-7.0.3.I2.2d.lib32_n9000.rpm"
    username: "{{ un }}"
    password: "{{ pwd }}"
    host: "{{ inventory_hostname }}"
'''

RETURN = '''
file_system:
    description: The remote file system of the device.
    returned: always
    type: string
    sample: "bootflash:"
pkg:
    description: Name of the remote package
    type: string
    returned: always
    sample: "nxos.CSCuz65185-n9k_EOR-1.0.0-7.0.3.I2.2d.lib32_n9000.rpm"
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["install add bootflash:nxos.CSCuz65185-n9k_EOR-1.0.0-7.0.3.I2.2d.lib32_n9000.rpm",
            "install activate bootflash:nxos.CSCuz65185-n9k_EOR-1.0.0-7.0.3.I2.2d.lib32_n9000.rpm force",
            "install commit bootflash:nxos.CSCuz65185-n9k_EOR-1.0.0-7.0.3.I2.2d.lib32_n9000.rpm"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''

import time
import json
import collections

# COMMON CODE FOR MIGRATION
import re

from ansible.module_utils.basic import get_exception
from ansible.module_utils.netcfg import NetworkConfig, ConfigLine
from ansible.module_utils.shell import ShellError

try:
    from ansible.module_utils.nxos import get_module
except ImportError:
    from ansible.module_utils.nxos import NetworkModule


def to_list(val):
     if isinstance(val, (list, tuple)):
         return list(val)
     elif val is not None:
         return [val]
     else:
         return list()


class CustomNetworkConfig(NetworkConfig):

    def expand_section(self, configobj, S=None):
        if S is None:
            S = list()
        S.append(configobj)
        for child in configobj.children:
            if child in S:
                continue
            self.expand_section(child, S)
        return S

    def get_object(self, path):
        for item in self.items:
            if item.text == path[-1]:
                parents = [p.text for p in item.parents]
                if parents == path[:-1]:
                    return item

    def to_block(self, section):
        return '\n'.join([item.raw for item in section])

    def get_section(self, path):
        try:
            section = self.get_section_objects(path)
            return self.to_block(section)
        except ValueError:
            return list()

    def get_section_objects(self, path):
        if not isinstance(path, list):
            path = [path]
        obj = self.get_object(path)
        if not obj:
            raise ValueError('path does not exist in config')
        return self.expand_section(obj)


    def add(self, lines, parents=None):
        """Adds one or lines of configuration
        """

        ancestors = list()
        offset = 0
        obj = None

        ## global config command
        if not parents:
            for line in to_list(lines):
                item = ConfigLine(line)
                item.raw = line
                if item not in self.items:
                    self.items.append(item)

        else:
            for index, p in enumerate(parents):
                try:
                    i = index + 1
                    obj = self.get_section_objects(parents[:i])[0]
                    ancestors.append(obj)

                except ValueError:
                    # add parent to config
                    offset = index * self.indent
                    obj = ConfigLine(p)
                    obj.raw = p.rjust(len(p) + offset)
                    if ancestors:
                        obj.parents = list(ancestors)
                        ancestors[-1].children.append(obj)
                    self.items.append(obj)
                    ancestors.append(obj)

            # add child objects
            for line in to_list(lines):
                # check if child already exists
                for child in ancestors[-1].children:
                    if child.text == line:
                        break
                else:
                    offset = len(parents) * self.indent
                    item = ConfigLine(line)
                    item.raw = line.rjust(len(line) + offset)
                    item.parents = ancestors
                    ancestors[-1].children.append(item)
                    self.items.append(item)


def get_network_module(**kwargs):
    try:
        return get_module(**kwargs)
    except NameError:
        return NetworkModule(**kwargs)

def get_config(module, include_defaults=False):
    config = module.params['config']
    if not config:
        try:
            config = module.get_config()
        except AttributeError:
            defaults = module.params['include_defaults']
            config = module.config.get_config(include_defaults=defaults)
    return CustomNetworkConfig(indent=2, contents=config)

def load_config(module, candidate):
    config = get_config(module)

    commands = candidate.difference(config)
    commands = [str(c).strip() for c in commands]

    save_config = module.params['save']

    result = dict(changed=False)

    if commands:
        if not module.check_mode:
            try:
                module.configure(commands)
            except AttributeError:
                module.config(commands)

            if save_config:
                try:
                    module.config.save_config()
                except AttributeError:
                    module.execute(['copy running-config startup-config'])

        result['changed'] = True
        result['updates'] = commands

    return result
# END OF COMMON CODE

def execute_show(cmds, module, command_type=None):
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
                module.cli.add_commands(cmds, raw=True)
                response = module.cli.run_commands()
        except ShellError:
            clie = get_exception()
            module.fail_json(msg='Error sending {0}'.format(cmds),
                             error=str(clie))
    return response


def execute_show_command(command, module, command_type='cli_show'):
    if module.params['transport'] == 'cli':
        cmds = [command]
        body = execute_show(cmds, module)
    elif module.params['transport'] == 'nxapi':
        cmds = [command]
        body = execute_show(cmds, module, command_type=command_type)

    return body


def remote_file_exists(module, dst, file_system='bootflash:'):
    command = 'dir {0}/{1}'.format(file_system, dst)
    body = execute_show_command(command, module, command_type='cli_show_ascii')
    if 'No such file' in body[0]:
        return False
    return True


def execute_config_command(commands, module):
    try:
        output = module.configure(commands)
    except ShellError:
        clie = get_exception()
        module.fail_json(msg='Error sending CLI commands',
                         error=str(clie), commands=commands)
    except AttributeError:
        try:
            commands.insert(0, 'configure')
            module.cli.add_commands(commands, output='config')
            output = module.cli.run_commands()
        except ShellError:
            clie = get_exception()
            module.fail_json(msg='Error sending CLI commands',
                             error=str(clie), commands=commands)
    return output


def apply_patch(module, commands):
    for command in commands:
        response = execute_config_command([command], module)
        time.sleep(5)
        if 'failed' in response:
            module.fail_json(msg="Operation failed!", response=response)


def get_commands(module, pkg, file_system):
    commands = []
    splitted_pkg = pkg.split('.')
    fixed_pkg = '.'.join(splitted_pkg[0:-1])

    command = 'show install inactive'
    inactive_body = execute_show_command(command, module,
                                                command_type='cli_show_ascii')
    command = 'show install active'
    active_body = execute_show_command(command, module,
                                                command_type='cli_show_ascii')

    if fixed_pkg not in inactive_body[0] and fixed_pkg not in active_body[0]:
        commands.append('install add {0}{1}'.format(file_system, pkg))

    if fixed_pkg not in active_body[0]:
        commands.append('install activate {0}{1} force'.format(
                                                            file_system, pkg))
    command = 'show install committed'
    install_body = execute_show_command(command, module,
                                                command_type='cli_show_ascii')
    if fixed_pkg not in install_body[0]:
        commands.append('install commit {0}{1}'.format(file_system, pkg))

    return commands


def main():
    argument_spec = dict(
            pkg=dict(required=True),
            file_system=dict(required=False, default='bootflash:'),
            include_defaults=dict(default=False),
            config=dict(),
            save=dict(type='bool', default=False)
    )
    module = get_network_module(argument_spec=argument_spec,
                                supports_check_mode=True)

    pkg = module.params['pkg']
    file_system = module.params['file_system']
    changed = False
    remote_exists = remote_file_exists(module, pkg, file_system=file_system)

    if not remote_exists:
        module.fail_json(msg="The requested package doesn't exist "
                             "on the device")

    commands = get_commands(module, pkg, file_system)
    if not module.check_mode and commands:
        try:
            apply_patch(module, commands)
            changed = True
        except ShellError:
            e = get_exception()
            module.fail_json(msg=str(e))

    if 'configure' in commands:
        commands.pop(0)

    module.exit_json(changed=changed,
                     pkg=pkg,
                     file_system=file_system,
                     updates=commands)


if __name__ == '__main__':
    main()
