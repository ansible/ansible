#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2016, Ansible, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'core'}

DOCUMENTATION = r'''
---
module: win_shell
short_description: Execute shell commands on target hosts
version_added: 2.2
description:
     - The C(win_shell) module takes the command name followed by a list of space-delimited arguments.
       It is similar to the M(win_command) module, but runs
       the command via a shell (defaults to PowerShell) on the target host.
     - For non-Windows targets, use the M(shell) module instead.
options:
  free_form:
    description:
      - The C(win_shell) module takes a free form command to run.
      - There is no parameter actually named 'free form'. See the examples!
    required: yes
  creates:
    description:
      - A path or path filter pattern; when the referenced path exists on the target host, the task will be skipped.
  removes:
    description:
      - A path or path filter pattern; when the referenced path B(does not) exist on the target host, the task will be skipped.
  chdir:
    description:
      - Set the specified path as the current working directory before executing a command
  executable:
    description:
      - Change the shell used to execute the command (eg, C(cmd)).
      - The target shell must accept a C(/c) parameter followed by the raw command line to be executed.
  stdin:
    description:
    - Set the stdin of the command directly to the specified value.
    version_added: '2.5'
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
- win_shell: C:\somescript.ps1 >> C:\somelog.txt

# Change the working directory to somedir/ before executing the command.
- win_shell: C:\somescript.ps1 >> C:\somelog.txt chdir=C:\somedir

# You can also use the 'args' form to provide the options. This command
# will change the working directory to somedir/ and will only run when
# somedir/somelog.txt doesn't exist.
- win_shell: C:\somescript.ps1 >> C:\somelog.txt
  args:
    chdir: C:\somedir
    creates: C:\somelog.txt

# Run a command under a non-Powershell interpreter (cmd in this case)
- win_shell: echo %HOMEDIR%
  args:
    executable: cmd
  register: homedir_out

- name: run multi-lined shell commands
  win_shell: |
    $value = Test-Path -Path C:\temp
    if ($value) {
        Remove-Item -Path C:\temp -Force
    }
    New-Item -Path C:\temp -ItemType Directory

- name: retrieve the input based on stdin
  win_shell: '$string = [Console]::In.ReadToEnd(); Write-Output $string.Trim()'
  args:
    stdin: Input message
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
