#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: 2017, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
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
    required: yes
  executable:
    description:
    - The location of the PsExec utility (in case it is not located in your PATH).
    type: path
    default: psexec.exe
  hostnames:
    description:
    - The hostnames to run the command.
    - If not provided, the command is run locally.
    type: list
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
    type: path
  nobanner:
    description:
    - Do not display the startup banner and copyright message.
    - This only works for specific versions of the PsExec binary.
    type: bool
    default: 'no'
    version_added: '2.4'
  noprofile:
    description:
    - Run the command without loading the account's profile.
    type: bool
    default: 'no'
  elevated:
    description:
    - Run the command with elevated privileges.
    type: bool
    default: 'no'
  interactive:
    description:
    - Run the program so that it interacts with the desktop on the remote system.
    type: bool
    default: 'no'
  limited:
    description:
    - Run the command as limited user (strips the Administrators group and allows only privileges assigned to the Users group).
    type: bool
    default: 'no'
  system:
    description:
    - Run the remote command in the System account.
    type: bool
    default: 'no'
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
    type: int
  wait:
    description:
    - Wait for the application to terminate.
    - Only use for non-interactive applications.
    type: bool
    default: 'yes'
notes:
- More information related to Microsoft PsExec is available from
  U(https://technet.microsoft.com/en-us/sysinternals/bb897553.aspx)
requirements:
- Microsoft PsExec
author:
- Dag Wieers (@dagwieers)
'''

EXAMPLES = r'''
- name: Test the PsExec connection to the local system (target node) with your user
  win_psexec:
    command: whoami.exe

- name: Run regedit.exe locally (on target node) as SYSTEM and interactively
  win_psexec:
    command: regedit.exe
    interactive: yes
    system: yes

- name: Run the setup.exe installer on multiple servers using the Domain Administrator
  win_psexec:
    command: E:\setup.exe /i /IACCEPTEULA
    hostnames:
    - remote_server1
    - remote_server2
    username: DOMAIN\Administrator
    password: some_password
    priority: high

- name: Run PsExec from custom location C:\Program Files\sysinternals\
  win_psexec:
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
    sample: psexec.exe -nobanner \\remote_server -u "DOMAIN\Administrator" -p "some_password" -accepteula E:\setup.exe
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
'''
