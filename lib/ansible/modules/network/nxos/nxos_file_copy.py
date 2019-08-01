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
short_description: Copy a file to a remote NXOS device.
description:
  - This module supports two different workflows for copying a file
    to flash (or bootflash) on NXOS devices.  Files can either be (1) pushed
    from the Ansible controller to the device or (2) pulled from a remote SCP
    file server to the device.  File copies are initiated from the NXOS
    device to the remote SCP server.  This module only supports the
    use of connection C(network_cli) or C(Cli) transport with connection C(local).
author:
  - Jason Edelman (@jedelman8)
  - Gabriele Gerbino (@GGabriele)
notes:
  - Tested against NXOS 7.0(3)I2(5), 7.0(3)I4(6), 7.0(3)I5(3),
    7.0(3)I6(1), 7.0(3)I7(3), 6.0(2)A8(8), 7.0(3)F3(4), 7.3(0)D1(1),
    8.3(0)
  - When pushing files (file_pull is False) to the NXOS device,
    feature scp-server must be enabled.
  - When pulling files (file_pull is True) to the NXOS device,
    feature scp-server is not required.
  - When pulling files (file_pull is True) to the NXOS device,
    no transfer will take place if the file is already present.
  - Check mode will tell you if the file would be copied.
requirements:
  - paramiko (required when file_pull is False)
  - SCPClient (required when file_pull is False)
  - pexpect (required when file_pull is True)
options:
  local_file:
    description:
      - When (file_pull is False) this is the path to the local file on the Ansible controller.
        The local directory must exist.
      - When (file_pull is True) this is the file name used on the NXOS device.
  remote_file:
    description:
      - When (file_pull is False) this is the remote file path on the NXOS device.
        If omitted, the name of the local file will be used.
        The remote directory must exist.
      - When (file_pull is True) this is the full path to the file on the remote SCP
        server to be copied to the NXOS device.
  file_system:
    description:
      - The remote file system of the device. If omitted,
        devices that support a I(file_system) parameter will use
        their default values.
    default: "bootflash:"
  connect_ssh_port:
    description:
      - SSH port to connect to server during transfer of file
    default: 22
    version_added: "2.5"
  file_pull:
    description:
      - When (False) file is copied from the Ansible controller to the NXOS device.
      - When (True) file is copied from a remote SCP server to the NXOS device.
        In this mode, the file copy is initiated from the NXOS device.
      - If the file is already present on the device it will be overwritten and
        therefore the operation is NOT idempotent.
    type: bool
    default: False
    version_added: "2.7"
  local_file_directory:
    description:
      - When (file_pull is True) file is copied from a remote SCP server to the NXOS device,
        and written to this directory on the NXOS device. If the directory does not exist, it
        will be created under the file_system. This is an optional parameter.
      - When (file_pull is False), this not used.
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
  vrf:
    description:
      - The VRF used to pull the file. Useful when no vrf management is defined
    default: "management"
    version_added: "2.9"
'''

EXAMPLES = '''
# File copy from ansible controller to nxos device
  - name: "copy from server to device"
    nxos_file_copy:
      local_file: "./test_file.txt"
      remote_file: "test_file.txt"

# Initiate file copy from the nxos device to transfer file from an SCP server back to the nxos device
  - name: "initiate file copy from device"
    nxos_file_copy:
      nxos_file_copy:
      file_pull: True
      local_file: "xyz"
      local_file_directory: "dir1/dir2/dir3"
      remote_file: "/mydir/abc"
      remote_scp_server: "192.168.0.1"
      remote_scp_server_user: "myUser"
      remote_scp_server_password: "myPassword"
      vrf: "management"
'''

RETURN = '''
transfer_status:
    description: Whether a file was transferred. "No Transfer" or "Sent".
                 If file_pull is successful, it is set to "Received".
    returned: success
    type: str
    sample: 'Sent'
local_file:
    description: The path of the local file.
    returned: success
    type: str
    sample: '/path/to/local/file'
remote_file:
    description: The path of the remote file.
    returned: success
    type: str
    sample: '/path/to/remote/file'
'''
