# There is actually no actual shell module source, when you use 'shell' in ansible,
# it runs the 'command' module with special arguments and it behaves differently.
# See the command source and the comment "#USE_SHELL".

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

DOCUMENTATION = '''
---
module: shell
short_description: Execute commands in nodes.
description:
     - The M(shell) module takes the command name followed by a list of space-delimited arguments.
       It is almost exactly like the M(command) module but runs
       the command through a shell (C(/bin/sh)) on the remote node.
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
      playbooks will follow the trend of using M(command) unless M(shell) is
      explicitly required. When running ad-hoc commands, use your best
      judgement.
   -  To sanitize any variables passed to the shell module, you should use 
      "{{ var | quote }}" instead of just "{{ var }}" to make sure they don't include evil things like semicolons.

requirements: [ ]
author: 
    - Ansible Core Team
    - Michael DeHaan
'''

EXAMPLES = '''
# Execute the command in remote shell; stdout goes to the specified
# file on the remote.
- shell: somescript.sh >> somelog.txt

# Change the working directory to somedir/ before executing the command.
- shell: somescript.sh >> somelog.txt chdir=somedir/

# You can also use the 'args' form to provide the options. This command
# will change the working directory to somedir/ and will only run when
# somedir/somelog.txt doesn't exist.
- shell: somescript.sh >> somelog.txt
  args:
    chdir: somedir/
    creates: somelog.txt

# Run a command that uses non-posix shell-isms (in this example /bin/sh
# doesn't handle redirection and wildcards together but bash does)
- shell: cat < /tmp/*txt
  args:
    executable: /bin/bash
'''
