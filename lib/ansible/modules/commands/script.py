# Copyright: (c) 2012, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}

DOCUMENTATION = r'''
---
module: script
version_added: "0.9"
short_description: Runs a local script on a remote node after transferring it
description:
     - The C(script) module takes the script name followed by a list of space-delimited arguments.
     - The local script at path will be transferred to the remote node and then executed.
     - The given script will be processed through the shell environment on the remote node.
     - This module does not require python on the remote system, much like the M(raw) module.
     - This module is also supported for Windows targets.
options:
  free_form:
    description:
      - Path to the local script file followed by optional arguments.
      - There is no parameter actually named 'free form', see the examples!
    required: true
  creates:
    description:
      - A filename on the remote node, when it already exists, this step will B(not) be run.
    version_added: "1.5"
  removes:
    description:
      - A filename on the remote node, when it does not exist, this step will B(not) be run.
    version_added: "1.5"
  chdir:
    description:
      - Change into this directory on the remote node before running the script.
    version_added: "2.4"
  executable:
    description:
      - Name or path of a executable to invoke the script with.
    version_added: "2.6"
notes:
  - It is usually preferable to write Ansible modules rather than pushing scripts. Convert your script to an Ansible module for bonus points!
  - The C(ssh) connection plugin will force pseudo-tty allocation via C(-tt) when scripts are executed. Pseudo-ttys do not have a stderr channel and all
    stderr is sent to stdout. If you depend on separated stdout and stderr result keys, please switch to a copy+command set of tasks instead of using script.
  - If the path to the local script contains spaces, it needs to be quoted.
  - This module is also supported for Windows targets.
seealso:
- module: shell
- module: win_shell
author:
    - Ansible Core Team
    - Michael DeHaan
extends_documentation_fragment:
    - decrypt
'''

EXAMPLES = r'''
- name: Run a script with arguments
  script: /some/local/script.sh --some-argument 1234

- name: Run a script only if file.txt does not exist on the remote node
  script: /some/local/create_file.sh --some-argument 1234
  args:
    creates: /the/created/file.txt

- name: Run a script only if file.txt exists on the remote node
  script: /some/local/remove_file.sh --some-argument 1234
  args:
    removes: /the/removed/file.txt

- name: Run a script using an executable in a non-system path
  script: /some/local/script
  args:
    executable: /some/remote/executable

- name: Run a script using an executable in a system path
  script: /some/local/script.py
  args:
    executable: python3
'''
