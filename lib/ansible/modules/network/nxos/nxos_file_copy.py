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
module: nxos_file_copy
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Copy a file to a remote NXOS device over SCP.
description:
  - Copy a file to the flash (or bootflash) remote network device
    on NXOS devices. This module only supports the use of connection
    C(network_cli) or C(Cli) transport with connection C(local).
author:
  - Jason Edelman (@jedelman8)
  - Gabriele Gerbino (@GGabriele)
notes:
  - Tested against NXOSv 7.3.(0)D1(1) on VIRL
  - The feature must be enabled with feature scp-server.
  - If the file is already present (md5 sums match), no transfer will
    take place.
  - Check mode will tell you if the file would be copied.
requirements:
  - paramiko
options:
  local_file:
    description:
      - Path to local file. Local directory must exist.
    required: true
  remote_file:
    description:
      - Remote file path of the copy. Remote directories must exist.
        If omitted, the name of the local file will be used.
  file_system:
    description:
      - The remote file system of the device. If omitted,
        devices that support a I(file_system) parameter will use
        their default values.
  connect_ssh_port:
    description:
      - SSH port to connect to server during transfer of file
    default: 22
    version_added: "2.5"
'''

EXAMPLES = '''
- nxos_file_copy:
    local_file: "./test_file.txt"
    remote_file: "test_file.txt"
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
import re
import time

from ansible.module_utils.network.nxos.nxos import run_commands
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule

try:
    import paramiko
    HAS_PARAMIKO = True
except ImportError:
    HAS_PARAMIKO = False

try:
    from scp import SCPClient
    HAS_SCP = True
except ImportError:
    HAS_SCP = False


def remote_file_exists(module, dst, file_system='bootflash:'):
    command = 'dir {0}/{1}'.format(file_system, dst)
    body = run_commands(module, {'command': command, 'output': 'text'})[0]
    if 'No such file' in body:
        return False
    return True


def verify_remote_file_exists(module, dst, file_system='bootflash:'):
    command = 'dir {0}/{1}'.format(file_system, dst)
    body = run_commands(module, {'command': command, 'output': 'text'})[0]
    if 'No such file' in body:
        return 0
    return body.split()[0].strip()


def local_file_exists(module):
    return os.path.isfile(module.params['local_file'])


def get_flash_size(module):
    command = 'dir {0}'.format(module.params['file_system'])
    body = run_commands(module, {'command': command, 'output': 'text'})[0]

    match = re.search(r'(\d+) bytes free', body)
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

    if not enough_space(module):
        module.fail_json(msg='Could not transfer file. Not enough space on device.')

    hostname = module.params['host']
    username = module.params['username']
    password = module.params['password']
    port = module.params['connect_ssh_port']

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        hostname=hostname,
        username=username,
        password=password,
        port=port)

    full_remote_path = '{0}{1}'.format(module.params['file_system'], dest)
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
    ssh.close()
    return True


def main():
    argument_spec = dict(
        local_file=dict(required=True),
        remote_file=dict(required=False),
        file_system=dict(required=False, default='bootflash:'),
        connect_ssh_port=dict(required=False, type='int', default=22),
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    if not HAS_PARAMIKO:
        module.fail_json(
            msg='library paramiko is required but does not appear to be '
                'installed. It can be installed using `pip install paramiko`'
        )

    if not HAS_SCP:
        module.fail_json(
            msg='library scp is required but does not appear to be '
                'installed. It can be installed using `pip install scp`'
        )

    warnings = list()
    check_args(module, warnings)
    results = dict(changed=False, warnings=warnings)

    local_file = module.params['local_file']
    remote_file = module.params['remote_file']
    file_system = module.params['file_system']

    results['transfer_status'] = 'No Transfer'
    results['local_file'] = local_file
    results['file_system'] = file_system

    if not local_file_exists(module):
        module.fail_json(msg="Local file {0} not found".format(local_file))

    dest = remote_file or os.path.basename(local_file)
    remote_exists = remote_file_exists(module, dest, file_system=file_system)

    if not remote_exists:
        results['changed'] = True
        file_exists = False
    else:
        file_exists = True

    if not module.check_mode and not file_exists:
        transfer_file(module, dest)
        results['transfer_status'] = 'Sent'

    if remote_file is None:
        remote_file = os.path.basename(local_file)
    results['remote_file'] = remote_file

    module.exit_json(**results)

if __name__ == '__main__':
    main()
