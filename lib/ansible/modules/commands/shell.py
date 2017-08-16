# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# # There is no actual shell module source, when you use 'shell' in ansible,
# it runs the 'command' module with special arguments and it behaves differently.
# See the command source and the comment "#USE_SHELL".

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}


DOCUMENTATION = '''
---
module: shell
short_description: Execute commands in nodes.
description:
     - The C(shell) module takes the command name followed by a list of space-delimited arguments.
       It is almost exactly like the M(command) module but runs
       the command through a shell (C(/bin/sh)) on the remote node.
     - For Windows targets, use the M(win_shell) module instead.
version_added: "0.2"
options:
  free_form:
    description:
      - The shell module takes a free form command to run, as a string.  There's not an actual
        option named "free form".  See the examples!
    required: true
    default: null
  creates:
    description:
      - a filename, when it already exists, this step will B(not) be run.
    required: no
    default: null
  removes:
    description:
      - a filename, when it does not exist, this step will B(not) be run.
    version_added: "0.8"
    required: no
    default: null
  chdir:
    description:
      - cd into this directory before running the command
    required: false
    default: null
    version_added: "0.6"
  executable:
    description:
      - change the shell used to execute the command. Should be an absolute path to the executable.
    required: false
    default: null
    version_added: "0.9"
  warn:
    description:
      - if command warnings are on in ansible.cfg, do not warn about this particular line if set to no/false.
    required: false
    default: True
    version_added: "1.8"
notes:
   -  If you want to execute a command securely and predictably, it may be
      better to use the M(command) module instead. Best practices when writing
      playbooks will follow the trend of using M(command) unless the C(shell)
      module is explicitly required. When running ad-hoc commands, use your best
      judgement.
   -  To sanitize any variables passed to the shell module, you should use
      "{{ var | quote }}" instead of just "{{ var }}" to make sure they don't include evil things like semicolons.
   - For Windows targets, use the M(win_shell) module instead.
requirements: [ ]
author:
    - Ansible Core Team
    - Michael DeHaan
'''

EXAMPLES = '''
- name: Execute the command in remote shell; stdout goes to the specified file on the remote.
  shell: somescript.sh >> somelog.txt

- name: Change the working directory to somedir/ before executing the command.
  shell: somescript.sh >> somelog.txt
  args:
    chdir: somedir/

# You can also use the 'args' form to provide the options.
- name: This command will change the working directory to somedir/ and will only run when somedir/somelog.txt doesn't exist.
  shell: somescript.sh >> somelog.txt
  args:
    chdir: somedir/
    creates: somelog.txt

- name: Run a command that uses non-posix shell-isms (in this example /bin/sh doesn't handle redirection and wildcards together but bash does)
  shell: cat < /tmp/*txt
  args:
    executable: /bin/bash

- name: Run a command using a templated variable (always use quote filter to avoid injection)
  shell: cat {{ myfile|quote }}

# You can use shell to run other executables to perform actions inline
- name: Run expect to wait for a successful PXE boot via out-of-band CIMC
  shell: |
    set timeout 300
    spawn ssh admin@{{ cimc_host }}

    expect "password:"
    send "{{ cimc_password }}\\n"

    expect "\\n{{ cimc_name }}"
    send "connect host\\n"

    expect "pxeboot.n12"
    send "\\n"

    exit 0
  args:
    executable: /usr/bin/expect
  delegate_to: localhost
'''

RETURN = '''
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
