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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = """
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
    default whoami.exe
  executable:
    description:
    - The location of the PsExec utility (in case it is not located in your PATH).
    required: false
    default: psexec.exe
  hostname:
    description:
    - The hostname to run the command.
    - If not provided, the command is run locally.
    required: false
  username:
    description:
    - The (remote) user to run the command as.
    - If not provided, the current user is used.
  password:
    description:
    - The password for the (remote) user to run the command as.
    - This is mandatory in order authenticate yourself.
    required: true
  chdir:
    description:
    - The (remote) directory to work from.
    required: false
  timeout:
    description:
    - The connection timeout in seconds
    required: false
  priority:
    description:
    - The priority to run the command as.
author: Dag Wieers (@dagwieers)
"""

EXAMPLES = r'''
# Test the PsExec connection to the local system with your user (runs whoami)
- win_psexec:
    password: some_password

- win_psexec:
    commandline: E:\setup.exe
    hostname: remote_server
    username: DOMAIN\Administrator
    password: some_password
'''

RETURN = '''
cmd:
    description: The complete command line used by the module, including PsExec call and additional options.
    returned: always
    type: string
    sample: 'psexec.exe \\remote_server -u DOMAIN\Administrator -p some_password E:\setup.exe'
rc:
    description: The return code for the command
    returned: always
    type: int
    sample: 0
stdout:
    description: The standard output from the command
    returned: always
    type: string
    sample: 'Success.'
stderr:
    description: The error output from the command
    returned: always
    type: string
    sample: 'Error 15 running E:\setup.exe'
msg:
    description: Possible error message on failure
    returned: failed
    type: string
    sample: "The 'password' parameter is a required parameter."
changed:
    description: Whether or not any changes were made.
    returned: always
    type: bool
    sample: True
'''
