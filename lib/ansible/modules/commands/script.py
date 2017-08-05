# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}


DOCUMENTATION = """
---
module: script
version_added: "0.9"
short_description: Runs a local script on a remote node after transferring it
description:
     - "The C(script) module takes the script name followed by a list of
       space-delimited arguments. "
     - "The local script at path will be transferred to the remote node and then executed. "
     - "The given script will be processed through the shell environment on the remote node. "
     - "This module does not require python on the remote system, much like
       the M(raw) module. "
     - This module is also supported for Windows targets.
options:
  free_form:
    description:
      - path to the local script file followed by optional arguments. There is no parameter actually named 'free form'; see the examples!
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
  chdir:
    description:
      - cd into this directory on the remote node before running the script
    version_added: "2.4"
    required: false
    default: null
notes:
  - It is usually preferable to write Ansible modules than pushing scripts. Convert your script to an Ansible module for bonus points!
  - The ssh connection plugin will force pseudo-tty allocation via -tt when scripts are executed. pseudo-ttys do not have a stderr channel and all
    stderr is sent to stdout. If you depend on separated stdout and stderr result keys, please switch to a copy+command set of tasks instead of using script.
  - This module is also supported for Windows targets.
author:
    - Ansible Core Team
    - Michael DeHaan
extends_documentation_fragment:
    - decrypt
"""

EXAMPLES = '''
# Example from Ansible Playbooks
- script: /some/local/script.sh --some-arguments 1234

# Run a script that creates a file, but only if the file is not yet created
- script: /some/local/create_file.sh --some-arguments 1234
  args:
    creates: /the/created/file.txt

# Run a script that removes a file, but only if the file is not yet removed
- script: /some/local/remove_file.sh --some-arguments 1234
  args:
    removes: /the/removed/file.txt
'''
