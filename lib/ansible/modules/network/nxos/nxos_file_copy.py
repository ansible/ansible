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
  - The feature must be enabled with feature scp-server if
    the file is being pushed to the device. If file_pull
    is True, feature scp-server is not needed.
  - If the file is already present, no transfer will
    take place if file_pull is False.
  - Check mode will tell you if the file would be copied.
requirements:
  - paramiko
  - SCPClient
  - pexpect
options:
  local_file:
    description:
      - Path to local file. Local directory must exist.
        If file_pull is True, this is optional, but when
        specified, the remote file name is renamed to this.
  remote_file:
    description:
      - Remote file path of the copy. Remote directories must exist.
        If omitted, the name of the local file will be used.
        If file_pull is True, this is the full path of the file
        to be copied on the device and this is required.
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
  file_pull:
    description:
      - Whether or not to pull the remote file from the device. If True,
        remote file will be copied to local file on the device. If the
        file already exists on the device, it will be overwritten, and
        the operation is NOT idempotent.
    default: False
    version_added: "2.7"
  file_pull_timeout:
    description:
      - Use this parameter to set timeout in seconds, when transferring
        large files or when the network is slow.
    default: 300
    version_added: "2.7"
  remote_scp_server:
    description:
      - The remote scp server address which is used to pull the file.
        This is required if file_pull is True.
    version_added: "2.7"
  remote_scp_server_user:
    description:
      - The remote scp server username which is used to pull the file.
        This is required if file_pull is True.
    version_added: "2.7"
  remote_scp_server_password:
    description:
      - The remote scp server password which is used to pull the file.
        This is required if file_pull is True.
    version_added: "2.7"
'''

EXAMPLES = '''
- nxos_file_copy:
    local_file: "./test_file.txt"
    remote_file: "test_file.txt"
'''

RETURN = '''
transfer_status:
    description: Whether a file was transferred. "No Transfer" or "Sent".
                 If file_pull is successful, it is set to "Received".
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
import traceback

from ansible.module_utils.network.nxos.nxos import run_commands
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native, to_text

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

try:
    import pexpect
    HAS_PEXPECT = True
except ImportError:
    HAS_PEXPECT = False


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


def transfer_file_to_device(module, dest):
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


def copy_file_from_remote(module, local, file_system='bootflash:'):
    hostname = module.params['host']
    username = module.params['username']
    password = module.params['password']
    port = module.params['connect_ssh_port']

    try:
        child = pexpect.spawn('ssh ' + username + '@' + hostname + ' -p' + str(port))
        # response could be unknown host addition or Password
        index = child.expect(['yes', 'Password'])
        if index == 0:
            child.sendline('yes')
            child.expect('Password')
        child.sendline(password)
        child.expect('#')
        command = ('copy scp://' + module.params['remote_scp_server_user'] +
                   '@' + module.params['remote_scp_server'] + module.params['remote_file'] +
                   ' ' + file_system + local + ' vrf management')
        child.sendline(command)
        # response could be remote host connection time out,
        # there is already an existing file with the same name,
        # unknown host addition or password
        index = child.expect(['timed out', 'existing', 'yes', 'password'], timeout=180)
        if index == 0:
            module.fail_json(msg='Timeout occured due to remote scp server not responding')
        elif index == 1:
            child.sendline('y')
            # response could be unknown host addition or Password
            sub_index = child.expect(['yes', 'password'])
            if sub_index == 0:
                child.sendline('yes')
                child.expect('password')
        elif index == 2:
            child.sendline('yes')
            child.expect('password')
        child.sendline(module.params['remote_scp_server_password'])
        fpt = module.params['file_pull_timeout']
        # response could be that there is no space left on device,
        # permission denied due to wrong user/password,
        # remote file non-existent or success
        index = child.expect(['No space', 'Permission denied', 'No such file', '#'], timeout=fpt)
        if index == 0:
            module.fail_json(msg='File copy failed due to no space left on the device')
        elif index == 1:
            module.fail_json(msg='Username/Password for remote scp server is wrong')
        elif index == 2:
            module.fail_json(msg='File copy failed due to remote file not present')
    except pexpect.ExceptionPexpect as e:
        module.fail_json(msg='%s' % to_native(e), exception=traceback.format_exc())

    child.close()


def main():
    argument_spec = dict(
        local_file=dict(type='str'),
        remote_file=dict(type='str'),
        file_system=dict(required=False, default='bootflash:'),
        connect_ssh_port=dict(required=False, type='int', default=22),
        file_pull=dict(type='bool', default=False),
        file_pull_timeout=dict(type='int', default=300),
        remote_scp_server=dict(type='str'),
        remote_scp_server_user=dict(type='str'),
        remote_scp_server_password=dict(no_log=True),
    )

    argument_spec.update(nxos_argument_spec)

    rt = [['remote_scp_server',
           'remote_scp_server_user',
           'remote_scp_server_password']]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_together=rt,
                           supports_check_mode=True)

    file_pull = module.params['file_pull']
    local_file = module.params['local_file']
    remote_file = module.params['remote_file']
    remote_scp_server = module.params['remote_scp_server']

    if file_pull:
        if not HAS_PEXPECT:
            module.fail_json(
                msg='library pexpect is required but does not appear to be '
                    'installed. It can be installed using `pip install pexpect`'
            )

        if not remote_file:
            module.fail_json(
                msg='remote file is required when it is copied from the device'
            )

        if not remote_scp_server:
            module.fail_json(
                msg='remote scp server is required when a file is copied from the device'
            )

    else:
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

        if not local_file:
            module.fail_json(
                msg='local file is required when it is copied to the device'
            )

    warnings = list()
    check_args(module, warnings)
    results = dict(changed=False, warnings=warnings)

    local_file = module.params['local_file']
    remote_file = module.params['remote_file']
    file_system = module.params['file_system']

    results['transfer_status'] = 'No Transfer'
    results['file_system'] = file_system

    if file_pull:
        src = remote_file.split('/')[-1]
        local = local_file or src

        if not module.check_mode:
            copy_file_from_remote(module, local, file_system=file_system)
            results['transfer_status'] = 'Received'

        results['changed'] = True
        results['remote_file'] = src
        results['local_file'] = local
    else:
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
            transfer_file_to_device(module, dest)
            results['transfer_status'] = 'Sent'

        results['local_file'] = local_file
        if remote_file is None:
            remote_file = os.path.basename(local_file)
        results['remote_file'] = remote_file

    module.exit_json(**results)

if __name__ == '__main__':
    main()
