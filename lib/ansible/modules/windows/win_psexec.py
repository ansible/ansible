#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2017, Dag Wieers <dag@wieers.com>
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: win_psexec
version_added: '2.3'
short_description: Runs commands (remotely) as another (privileged) user
description:
- Run commands (remotely) through the PsExec service
- Run commands as another (domain) user (with elevated privileges)
options:
  command:
    description:
    - The command line to run through PsExec (limited to 260 characters).
    required: true
  executable:
    description:
    - The location of the PsExec utility (in case it is not located in your PATH).
    default: psexec.exe
  hostnames:
    description:
    - The hostnames to run the command.
    - If not provided, the command is run locally.
  username:
    description:
    - The (remote) user to run the command as.
    - If not provided, the current user is used.
  password:
    description:
    - The password for the (remote) user to run the command as.
    - This is mandatory in order authenticate yourself.
  chdir:
    description:
    - Run the command from this (remote) directory.
  noprofile:
    description:
    - Run the command without loading the account's profile.
    default: False
  elevated:
    description:
    - Run the command with elevated privileges.
    default: False
  interactive:
    description:
    - Run the program so that it interacts with the desktop on the remote system.
    default: False
  limited:
    description:
    - Run the command as limited user (strips the Administrators group and allows only privileges assigned to the Users group).
    default: False
  system:
    description:
    - Run the remote command in the System account.
    default: False
  priority:
    description:
    - Used to run the command at a different priority.
    choices:
    - background
    - low
    - belownormal
    - abovenormal
    - high
    - realtime
  timeout:
    description:
    - The connection timeout in seconds
  wait:
    description:
    - Wait for the application to terminate.
    - Only use for non-interactive applications.
    default: True
requirements: [ psexec ]
author: Dag Wieers (@dagwieers)
'''

EXAMPLES = r'''
# Test the PsExec connection to the local system (target node) with your user
- win_psexec:
    command: whoami.exe

# Run regedit.exe locally (on target node) as SYSTEM and interactively
- win_psexec:
    command: regedit.exe
    interactive: yes
    system: yes

# Run the setup.exe installer on multiple servers using the Domain Administrator
- win_psexec:
    command: E:\setup.exe /i /IACCEPTEULA
    hostnames:
    - remote_server1
    - remote_server2
    username: DOMAIN\Administrator
    password: some_password
    priority: high

# Run PsExec from custom location C:\Program Files\sysinternals\
- win_psexec:
    command: netsh advfirewall set allprofiles state off
    executable: C:\Program Files\sysinternals\psexec.exe
    hostnames: [ remote_server ]
    password: some_password
    priority: low
'''

RETURN = r'''
cmd:
    description: The complete command line used by the module, including PsExec call and additional options.
    returned: always
    type: string
    sample: psexec.exe \\remote_server -u DOMAIN\Administrator -p some_password E:\setup.exe
rc:
    description: The return code for the command
    returned: always
    type: int
    sample: 0
stdout:
    description: The standard output from the command
    returned: always
    type: string
    sample: Success.
stderr:
    description: The error output from the command
    returned: always
    type: string
    sample: Error 15 running E:\setup.exe
msg:
    description: Possible error message on failure
    returned: failed
    type: string
    sample: The 'password' parameter is a required parameter.
changed:
    description: Whether or not any changes were made.
    returned: always
    type: bool
    sample: True
'''
