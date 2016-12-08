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
module: nxos_file_copy
version_added: "2.2"
short_description: Copy a file to a remote NXOS device over SCP.
description:
    - Copy a file to the flash (or bootflash) remote network device
      on NXOS devices.
author:
    - Jason Edelman (@jedelman8)
    - Gabriele Gerbino (@GGabriele)
extends_documentation_fragment: nxos
notes:
    - The feature must be enabled with feature scp-server.
    - If the file is already present (md5 sums match), no transfer will
      take place.
    - Check mode will tell you if the file would be copied.
options:
    local_file:
        description:
            - Path to local file. Local directory must exist.
        required: true
    remote_file:
        description:
            - Remote file path of the copy. Remote directories must exist.
              If omitted, the name of the local file will be used.
        required: false
        default: null
    file_system:
        description:
            - The remote file system of the device. If omitted,
              devices that support a file_system parameter will use
              their default values.
        required: false
        default: null
'''

EXAMPLES = '''
- nxos_file_copy:
    local_file: "./test_file.txt"
    username: "{{ un }}"
    password: "{{ pwd }}"
    host: "{{ inventory_hostname }}"
'''

RETURN = '''
transfer_status:
    description: Whether a file was transferred. "No Transfer" or "Sent".
    returned: success
    type: string
    sample: 'Sent'
local_file:
    description: The path of the local file.
    returned: success
    type: string
    sample: '/path/to/local/file'
remote_file:
    description: The path of the remote file.
    returned: success
    type: string
    sample: '/path/to/remote/file'
'''


import os
from scp import SCPClient
import paramiko
import time

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
                module.cli.add_commands(cmds, output=command_type)
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


def verify_remote_file_exists(module, dst, file_system='bootflash:'):
    command = 'dir {0}/{1}'.format(file_system, dst)
    body = execute_show_command(command, module, command_type='cli_show_ascii')
    if 'No such file' in body[0]:
        return 0
    return body[0].split()[0].strip()


def local_file_exists(module):
    return os.path.isfile(module.params['local_file'])


def get_flash_size(module):
    command = 'dir {}'.format(module.params['file_system'])
    body = execute_show_command(command, module, command_type='cli_show_ascii')

    match = re.search(r'(\d+) bytes free', body[0])
    bytes_free = match.group(1)

    return int(bytes_free)


def enough_space(module):
    flash_size = get_flash_size(module)
    file_size = os.path.getsize(module.params['local_file'])
    if file_size > flash_size:
        return False

    return True


def transfer_file(module, dest):
    file_size = os.path.getsize(module.params['local_file'])

    if not local_file_exists(module):
        module.fail_json(msg='Could not transfer file. Local file doesn\'t exist.')

    if not enough_space(module):
        module.fail_json(msg='Could not transfer file. Not enough space on device.')

    hostname = module.params['host']
    username = module.params['username']
    password = module.params['password']

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        hostname=hostname,
        username=username,
        password=password)

    full_remote_path = '{}{}'.format(module.params['file_system'], dest)
    scp = SCPClient(ssh.get_transport())
    try:
        scp.put(module.params['local_file'], full_remote_path)
    except:
        time.sleep(10)
        temp_size = verify_remote_file_exists(
                    module, dest, file_system=module.params['file_system'])
        if int(temp_size) == int(file_size):
            pass
        else:
            module.fail_json(msg='Could not transfer file. There was an error '
                             'during transfer. Please make sure remote '
                             'permissions are set.', temp_size=temp_size,
                             file_size=file_size)
    scp.close()
    return True


def main():
    argument_spec = dict(
            local_file=dict(required=True),
            remote_file=dict(required=False),
            file_system=dict(required=False, default='bootflash:'),
            include_defaults=dict(default=True),
            config=dict(),
            save=dict(type='bool', default=False)
    )
    module = get_network_module(argument_spec=argument_spec,
                        supports_check_mode=True)

    local_file = module.params['local_file']
    remote_file = module.params['remote_file']
    file_system = module.params['file_system']

    changed = False
    transfer_status = 'No Transfer'

    if not os.path.isfile(local_file):
        module.fail_json(msg="Local file {} not found".format(local_file))

    dest = remote_file or os.path.basename(local_file)
    remote_exists = remote_file_exists(module, dest, file_system=file_system)

    if not remote_exists:
        changed = True
        file_exists = False
    else:
        file_exists = True

    if not module.check_mode and not file_exists:
        try:
            transfer_file(module, dest)
            transfer_status = 'Sent'
        except ShellError:
            clie = get_exception()
            module.fail_json(msg=str(clie))

    if remote_file is None:
        remote_file = os.path.basename(local_file)

    module.exit_json(changed=changed,
                     transfer_status=transfer_status,
                     local_file=local_file,
                     remote_file=remote_file,
                     file_system=file_system)


if __name__ == '__main__':
    main()
