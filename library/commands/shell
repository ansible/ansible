# There is actually no actual shell module source, when you use 'shell' in ansible,
# it runs the 'command' module with special arguments and it behaves differently.
# See the command source and the comment "#USE_SHELL".

DOCUMENTATION = '''
---
module: shell
short_description: Execute commands in nodes.
description:
     - The shell module takes the command name followed by a list of arguments,
       space delimited. It is almost exactly like the M(command) module but runs
       the command through a shell (C(/bin/sh)) on the remote node.
version_added: "0.2"
options:
  (free form):
    description:
      - The command module takes a free form command to run
    required: null
    default: null
  creates:
    description:
      - a filename, when it already exists, this step will NOT be run
    required: false
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
notes:
   -  If you want to execute a command securely and predictably, it may be
      better to use the M(command) module instead. Best practices when writing
      playbooks will follow the trend of using M(command) unless M(shell) is
      explicitly required. When running ad-hoc commands, use your best
      judgement.
requirements: [ ]
author: Michael DeHaan
'''

EXAMPLES = '''
# Execute the command in remote shell; stdout goes to the specified
# file on the remote
- shell: somescript.sh >> somelog.txt
'''
