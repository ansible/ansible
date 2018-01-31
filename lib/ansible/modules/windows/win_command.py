#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Ansible, inc
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
                    'supported_by': 'core'}


DOCUMENTATION = r'''
---
module: win_command
short_description: Executes a command on a remote Windows node
version_added: 2.2
description:
     - The C(win_command) module takes the command name followed by a list of space-delimited arguments.
     - The given command will be executed on all selected nodes. It will not be
       processed through the shell, so variables like C($env:HOME) and operations
       like C("<"), C(">"), C("|"), and C(";") will not work (use the M(win_shell)
       module if you need these features).
     - For non-Windows targets, use the M(command) module instead.
options:
  free_form:
    description:
      - the C(win_command) module takes a free form command to run.  There is no parameter actually named 'free form'.
        See the examples!
    required: true
  creates:
    description:
      - a path or path filter pattern; when the referenced path exists on the target host, the task will be skipped.
  removes:
    description:
      - a path or path filter pattern; when the referenced path B(does not) exist on the target host, the task will be skipped.
  chdir:
    description:
      - set the specified path as the current working directory before executing a command.
  stdin:
    description:
    - Set the stdin of the command directly to the specified value.
    version_added: '2.5'
notes:
    - If you want to run a command through a shell (say you are using C(<),
      C(>), C(|), etc), you actually want the M(win_shell) module instead. The
      C(win_command) module is much more secure as it's not affected by the user's
      environment.
    - C(creates), C(removes), and C(chdir) can be specified after the command. For instance, if you only want to run a command if a certain file does not
      exist, use this.
    - For non-Windows targets, use the M(command) module instead.
author:
    - Matt Davis
'''

EXAMPLES = r'''
- name: Save the result of 'whoami' in 'whoami_out'
  win_command: whoami
  register: whoami_out

- name: Run command that only runs if folder exists and runs from a specific folder
  win_command: wbadmin -backupTarget:C:\backup\
  args:
    chdir: C:\somedir\
    creates: C:\backup\

- name: Run an executable and send data to the stdin for the executable
  win_command: powershell.exe -
  args:
    stdin: Write-Host test
'''

RETURN = r'''
msg:
    description: changed
    returned: always
    type: boolean
    sample: True
start:
    description: The command execution start time
    returned: always
    type: string
    sample: '2016-02-25 09:18:26.429568'
end:
    description: The command execution end time
    returned: always
    type: string
    sample: '2016-02-25 09:18:26.755339'
delta:
    description: The command execution delta time
    returned: always
    type: string
    sample: '0:00:00.325771'
stdout:
    description: The command standard output
    returned: always
    type: string
    sample: 'Clustering node rabbit@slave1 with rabbit@master ...'
stderr:
    description: The command standard error
    returned: always
    type: string
    sample: 'ls: cannot access foo: No such file or directory'
cmd:
    description: The command executed by the task
    returned: always
    type: string
    sample: 'rabbitmqctl join_cluster rabbit@master'
rc:
    description: The command return code (0 means success)
    returned: always
    type: int
    sample: 0
stdout_lines:
    description: The command standard output split in lines
    returned: always
    type: list
    sample: [u'Clustering node rabbit@slave1 with rabbit@master ...']
'''
