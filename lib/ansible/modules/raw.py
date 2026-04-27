# This is a virtual module that is entirely implemented server side

# Copyright: (c) 2012, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


DOCUMENTATION = r"""
---
module: raw
short_description: Executes a low-down and dirty command
version_added: historical
options:
  free_form:
    description:
      - The raw module takes a free form command to run.
      - There is no parameter actually named 'free form'; see the examples!
    required: true
  executable:
    description:
      - Change the shell used to execute the command. Should be an absolute path to the executable.
      - When using privilege escalation (C(become)) a default shell will be assigned if one is not provided
        as privilege escalation requires a shell.
    version_added: "1.0"
description:
     - Executes a low-down and dirty SSH command, not going through the module
       subsystem.
     - This is useful and should only be done in a few cases. A common
       case is installing C(python) on a system without python installed by default.
       Another is speaking to any devices such as
       routers that do not have any Python installed. In any other case, using
       the M(ansible.builtin.shell) or M(ansible.builtin.command) module is much more appropriate.
     - Arguments given to C(raw) are run directly through the configured remote shell.
     - Standard output, error output and return code are returned when
       available.
     - There is no change handler support for this module.
     - This module does not require python on the remote system, much like
       the M(ansible.builtin.script) module.
     - This module is also supported for Windows targets.
     - If the command returns non UTF-8 data, it must be encoded to avoid issues. One option is to pipe
       the output through C(base64).
extends_documentation_fragment:
    - action_common_attributes
    - action_common_attributes.raw
attributes:
    check_mode:
        support: none
    diff_mode:
        support: none
    platform:
        details: This action is one of the few that requires no Python on the remote as it passes the command directly into the connection string
        platforms: all
    raw:
      support: full
notes:
    - "If using raw from a playbook, you may need to disable fact gathering
      using C(gather_facts: no) if you're using C(raw) to bootstrap python
      onto the machine."
    - If you want to execute a command securely and predictably, it may be
      better to use the M(ansible.builtin.command) or M(ansible.builtin.shell) modules instead.
    - The C(environment) keyword does not work with raw normally, it requires a shell
      which means it only works if C(executable) is set or using the module
      with privilege escalation (C(become)).
seealso:
- module: ansible.builtin.command
- module: ansible.builtin.shell
- module: ansible.windows.win_command
- module: ansible.windows.win_shell
author:
    - Ansible Core Team
    - Michael DeHaan
"""

EXAMPLES = r"""
- name: Bootstrap a host without Python installed
  ansible.builtin.raw: dnf install -y python3 python3-libdnf

- name: Run a command that uses non-posix shell-isms (in this example /bin/sh doesn't handle redirection and wildcards together but bash does)
  ansible.builtin.raw: cat < /tmp/*txt
  args:
    executable: /bin/bash

- name: Safely use templated variables. Always use quote filter to avoid injection issues.
  ansible.builtin.raw: "{{ package_mgr|quote }} {{ pkg_flags|quote }} install {{ python|quote }}"

- name: List user accounts on a Windows system
  ansible.builtin.raw: Get-WmiObject -Class Win32_UserAccount
"""
