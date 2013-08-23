
DOCUMENTATION = """
---
module: script
short_description: Runs a local script on a remote node after transferring it
description:
     - "The M(script) module takes the script name followed by a list of
       space-delimited arguments. "
     - "The local script at path will be transfered to the remote node and then executed. "
     - "The given script will be processed through the shell environment on the remote node. "
     - "This module does not require python on the remote system, much like
       the M(raw) module. "
options:
  free_form:
    description:
      - path to the local script file followed by optional arguments.
    required: true
    default: null
    aliases: []
notes:
  - It is usually preferable to write Ansible modules than pushing scripts. Convert your script to an Ansible module for bonus points!
author: Michael DeHaan
"""

EXAMPLES = '''
# Example from Ansible Playbooks
- script: /some/local/script.sh --some-arguments 1234
'''
