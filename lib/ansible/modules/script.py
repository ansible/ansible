# Copyright: (c) 2012, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


DOCUMENTATION = r"""
---
module: script
version_added: "0.9"
short_description: Runs a local script on a remote node after transferring it
description:
  - The M(ansible.builtin.script) module takes the script name followed by a list of space-delimited arguments.
  - Either a free-form command or O(cmd) parameter is required, see the examples.
  - The local script at the path will be transferred to the remote node and then executed.
  - The given script will be processed through the shell environment on the remote node.
  - This module does not require Python on the remote system, much like the M(ansible.builtin.raw) module.
  - This module is also supported for Windows targets.
options:
  free_form:
    description:
      - Path to the local script file followed by optional arguments.
    type: str
  cmd:
    type: str
    description:
      - Path to the local script to run followed by optional arguments.
  creates:
    description:
      - A filename on the remote node, when it already exists, this step will B(not) be run.
    version_added: "1.5"
    type: str
  removes:
    description:
      - A filename on the remote node, when it does not exist, this step will B(not) be run.
    version_added: "1.5"
    type: str
  chdir:
    description:
      - Change into this directory on the remote node before running the script.
    version_added: "2.4"
    type: str
  executable:
    description:
      - Name or path of an executable to invoke the script with.
    version_added: "2.6"
    type: str
notes:
  - It is usually preferable to write Ansible modules rather than pushing scripts. Convert your script to an Ansible module for bonus points!
  - The P(ansible.builtin.ssh#connection) connection plugin will force pseudo-tty allocation via C(-tt) when scripts are executed.
    Pseudo-ttys do not have a stderr channel and all stderr is sent to stdout. If you depend on separated stdout and stderr result keys,
    please switch to a set of tasks that comprises M(ansible.builtin.copy) with M(ansible.builtin.command) instead of using M(ansible.builtin.script).
  - If the path to the local script contains spaces, it needs to be quoted.
  - This module is also supported for Windows targets.
  - If the script returns non-UTF-8 data, it must be encoded to avoid issues. One option is to pipe
    the output through C(base64).
seealso:
  - module: ansible.builtin.shell
  - module: ansible.windows.win_shell
author:
  - Ansible Core Team
  - Michael DeHaan
extends_documentation_fragment:
    - action_common_attributes
    - action_common_attributes.files
    - action_common_attributes.raw
    - decrypt
attributes:
    check_mode:
        support: partial
        details: while the script itself is arbitrary and cannot be subject to the check mode semantics it adds O(creates)/O(removes) options as a workaround
    diff_mode:
        support: none
    platform:
        details: This action is one of the few that requires no Python on the remote as it passes the command directly into the connection string
        platforms: all
    raw:
      support: full
    safe_file_operations:
        support: none
    vault:
        support: full
"""

EXAMPLES = r"""
- name: Run a script with arguments (free form)
  ansible.builtin.script: /some/local/script.sh --some-argument 1234

- name: Run a script with arguments (using 'cmd' parameter)
  ansible.builtin.script:
    cmd: /some/local/script.sh --some-argument 1234

- name: Run a script only if file.txt does not exist on the remote node
  ansible.builtin.script: /some/local/create_file.sh --some-argument 1234
  args:
    creates: /the/created/file.txt

- name: Run a script only if file.txt exists on the remote node
  ansible.builtin.script: /some/local/remove_file.sh --some-argument 1234
  args:
    removes: /the/removed/file.txt

- name: Run a script using an executable in a non-system path
  ansible.builtin.script: /some/local/script
  args:
    executable: /some/remote/executable

- name: Run a script using an executable in a system path
  ansible.builtin.script: /some/local/script.py
  args:
    executable: python3

- name: Run a Powershell script on a Windows host
  script: subdirectories/under/path/with/your/playbook/script.ps1
"""
