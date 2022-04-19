# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# There is no actual shell module source, when you use 'shell' in ansible,
# it runs the 'command' module with special arguments and it behaves differently.
# See the command source and the comment "#USE_SHELL".

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: shell
short_description: Execute shell commands on targets
description:
     - The C(shell) module takes the command name followed by a list of space-delimited arguments.
     - Either a free form command or C(cmd) parameter is required, see the examples.
     - It is almost exactly like the M(ansible.builtin.command) module but runs
       the command through a shell (C(/bin/sh)) on the remote node.
     - For Windows targets, use the M(ansible.windows.win_shell) module instead.
version_added: "0.2"
options:
  free_form:
    description:
      - The shell module takes a free form command to run, as a string.
      - There is no actual parameter named 'free form'.
      - See the examples on how to use this module.
    type: str
  cmd:
    type: str
    description:
      - The command to run followed by optional arguments.
  creates:
    description:
      - A filename, when it already exists, this step will B(not) be run.
    type: path
  removes:
    description:
      - A filename, when it does not exist, this step will B(not) be run.
    type: path
    version_added: "0.8"
  chdir:
    description:
      - Change into this directory before running the command.
    type: path
    version_added: "0.6"
  executable:
    description:
      - Change the shell used to execute the command.
      - This expects an absolute path to the executable.
    type: path
    version_added: "0.9"
  stdin:
    description:
      - Set the stdin of the command directly to the specified value.
    type: str
    version_added: "2.4"
  stdin_add_newline:
    description:
      - Whether to append a newline to stdin data.
    type: bool
    default: yes
    version_added: "2.8"
extends_documentation_fragment:
    - action_common_attributes
    - action_common_attributes.raw
attributes:
    check_mode:
        details: while the command itself is arbitrary and cannot be subject to the check mode semantics it adds C(creates)/C(removes) options as a workaround
        support: partial
    diff_mode:
        support: none
    platform:
      support: full
      platforms: posix
    raw:
      support: full
notes:
  - If you want to execute a command securely and predictably, it may be
    better to use the M(ansible.builtin.command) module instead. Best practices
    when writing playbooks will follow the trend of using M(ansible.builtin.command)
    unless the M(ansible.builtin.shell) module is explicitly required. When running ad-hoc
    commands, use your best judgement.
  - To sanitize any variables passed to the shell module, you should use
    C({{ var | quote }}) instead of just C({{ var }}) to make sure they
    do not include evil things like semicolons.
  - An alternative to using inline shell scripts with this module is to use
    the M(ansible.builtin.script) module possibly together with the M(ansible.builtin.template) module.
  - For rebooting systems, use the M(ansible.builtin.reboot) or M(ansible.windows.win_reboot) module.
seealso:
- module: ansible.builtin.command
- module: ansible.builtin.raw
- module: ansible.builtin.script
- module: ansible.windows.win_shell
author:
    - Ansible Core Team
    - Michael DeHaan
'''

EXAMPLES = r'''
- name: Execute the command in remote shell; stdout goes to the specified file on the remote
  ansible.builtin.shell: somescript.sh >> somelog.txt

- name: Change the working directory to somedir/ before executing the command
  ansible.builtin.shell: somescript.sh >> somelog.txt
  args:
    chdir: somedir/

# You can also use the 'args' form to provide the options.
- name: This command will change the working directory to somedir/ and will only run when somedir/somelog.txt doesn't exist
  ansible.builtin.shell: somescript.sh >> somelog.txt
  args:
    chdir: somedir/
    creates: somelog.txt

# You can also use the 'cmd' parameter instead of free form format.
- name: This command will change the working directory to somedir/
  ansible.builtin.shell:
    cmd: ls -l | grep log
    chdir: somedir/

- name: Run a command that uses non-posix shell-isms (in this example /bin/sh doesn't handle redirection and wildcards together but bash does)
  ansible.builtin.shell: cat < /tmp/*txt
  args:
    executable: /bin/bash

- name: Run a command using a templated variable (always use quote filter to avoid injection)
  ansible.builtin.shell: cat {{ myfile|quote }}

# You can use shell to run other executables to perform actions inline
- name: Run expect to wait for a successful PXE boot via out-of-band CIMC
  ansible.builtin.shell: |
    set timeout 300
    spawn ssh admin@{{ cimc_host }}

    expect "password:"
    send "{{ cimc_password }}\n"

    expect "\n{{ cimc_name }}"
    send "connect host\n"

    expect "pxeboot.n12"
    send "\n"

    exit 0
  args:
    executable: /usr/bin/expect
  delegate_to: localhost
'''

RETURN = r'''
msg:
    description: changed
    returned: always
    type: bool
    sample: True
start:
    description: The command execution start time.
    returned: always
    type: str
    sample: '2016-02-25 09:18:26.429568'
end:
    description: The command execution end time.
    returned: always
    type: str
    sample: '2016-02-25 09:18:26.755339'
delta:
    description: The command execution delta time.
    returned: always
    type: str
    sample: '0:00:00.325771'
stdout:
    description: The command standard output.
    returned: always
    type: str
    sample: 'Clustering node rabbit@slave1 with rabbit@master …'
stderr:
    description: The command standard error.
    returned: always
    type: str
    sample: 'ls: cannot access foo: No such file or directory'
cmd:
    description: The command executed by the task.
    returned: always
    type: str
    sample: 'rabbitmqctl join_cluster rabbit@master'
rc:
    description: The command return code (0 means success).
    returned: always
    type: int
    sample: 0
stdout_lines:
    description: The command standard output split in lines.
    returned: always
    type: list
    sample: [u'Clustering node rabbit@slave1 with rabbit@master …']
stderr_lines:
    description: The command standard error split in lines.
    returned: always
    type: list
    sample: [u'ls cannot access foo: No such file or directory', u'ls …']
'''
