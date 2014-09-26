
DOCUMENTATION = """
---
module: script
version_added: "0.9"
short_description: Runs a local script on a remote node after transferring it
description:
     - "The M(script) module takes the script name followed by a list of
       space-delimited arguments. "
     - "The local script at path will be transferred to the remote node and then executed. "
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
  creates:
    description:
      - a filename, when it already exists, this step will B(not) be run.
    required: no
    default: null
    version_added: "1.5"
  removes:
    description:
      - a filename, when it does not exist, this step will B(not) be run.
    required: no
    default: null
    version_added: "1.5"
notes:
  - It is usually preferable to write Ansible modules than pushing scripts. Convert your script to an Ansible module for bonus points!
author: Michael DeHaan
"""

EXAMPLES = '''
# Example from Ansible Playbooks
- script: /some/local/script.sh --some-arguments 1234

# Run a script that creates a file, but only if the file is not yet created
- script: /some/local/create_file.sh --some-arguments 1234 creates=/the/created/file.txt

# Run a script that removes a file, but only if the file is not yet removed
- script: /some/local/remove_file.sh --some-arguments 1234 removes=/the/removed/file.txt
'''
