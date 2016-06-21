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
  - The ssh connection plugin will force psuedo-tty allocation via -tt when scripts are executed. psuedo-ttys do not have a stderr channel and all stderr is sent to stdout. If you depend on separated stdout and stderr result keys, please switch to a copy+command set of tasks instead of using script.
author: 
    - Ansible Core Team
    - Michael DeHaan
"""

EXAMPLES = '''
# Example from Ansible Playbooks
- script: /some/local/script.sh --some-arguments 1234

# Run a script that creates a file, but only if the file is not yet created
- script: /some/local/create_file.sh --some-arguments 1234 creates=/the/created/file.txt

# Run a script that removes a file, but only if the file is not yet removed
- script: /some/local/remove_file.sh --some-arguments 1234 removes=/the/removed/file.txt
'''
