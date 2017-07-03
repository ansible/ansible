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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'core'}


DOCUMENTATION = r'''
---
module: win_shell
short_description: Execute shell commands on target hosts.
version_added: 2.2
description:
     - The C(win_shell) module takes the command name followed by a list of space-delimited arguments.
       It is similar to the M(win_command) module, but runs
       the command via a shell (defaults to PowerShell) on the target host.
     - For non-Windows targets, use the M(shell) module instead.
options:
  free_form:
    description:
      - The C(win_shell) module takes a free form command to run.  There is no parameter actually named 'free form'.
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
      - set the specified path as the current working directory before executing a command
  executable:
    description:
      - change the shell used to execute the command (eg, C(cmd)). The target shell must accept a C(/c) parameter followed by the raw command line to be
        executed.
notes:
   -  If you want to run an executable securely and predictably, it may be
      better to use the M(win_command) module instead. Best practices when writing
      playbooks will follow the trend of using M(win_command) unless C(win_shell) is
      explicitly required. When running ad-hoc commands, use your best judgement.
   -  WinRM will not return from a command execution until all child processes created have exited.
      Thus, it is not possible to use C(win_shell) to spawn long-running child or background processes.
      Consider creating a Windows service for managing background processes.
   - For non-Windows targets, use the M(shell) module instead.
   - See also M(win_command), M(raw)
author:
    - Matt Davis (@nitzmahone)
'''

EXAMPLES = r'''
# Execute a command in the remote shell; stdout goes to the specified
# file on the remote.
- win_shell: C:\somescript.ps1 >> c:\somelog.txt

# Change the working directory to somedir/ before executing the command.
- win_shell: C:\somescript.ps1 >> c:\somelog.txt chdir=c:\somedir

# You can also use the 'args' form to provide the options. This command
# will change the working directory to somedir/ and will only run when
# somedir/somelog.txt doesn't exist.
- win_shell: C:\somescript.ps1 >> c:\somelog.txt
  args:
    chdir: c:\somedir
    creates: c:\somelog.txt

# Run a command under a non-Powershell interpreter (cmd in this case)
- win_shell: echo %HOMEDIR%
  args:
    executable: cmd
  register: homedir_out
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
