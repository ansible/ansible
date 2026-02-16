# -*- coding: utf-8 -*-
# Copyright (c) 2025, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Documentation for the display action plugin; execution is implemented in the action plugin."""

from __future__ import annotations


DOCUMENTATION = """
---
module: display
short_description: Emit a message at a configurable level
description:
  - This action lets playbook and role authors emit messages explicitly as a task,
    at a chosen display level (normal, verbose, warning, or deprecation).
  - Useful for announcing planned changes, deprecations, or warnings in shared roles.
version_added: "2.21.0"
options:
  msg:
    description: The message to emit. Supports templating.
    type: str
    required: true
  level:
    description:
      - Display level. C(display) is normal output; C(v) through C(vvvvvv) are
        verbosity levels (visible at C(-v) and above); C(warning) and C(deprecated) emit
        warnings or deprecation notices.
    type: str
    default: display
    choices:
      - display
      - v
      - vv
      - vvv
      - vvvv
      - vvvvv
      - vvvvvv
      - warning
      - deprecated
extends_documentation_fragment:
  - action_common_attributes
  - action_common_attributes.conn
  - action_common_attributes.flow
attributes:
  action:
    support: full
  async:
    support: none
  become:
    support: none
  bypass_host_loop:
    support: full
  check_mode:
    support: full
  connection:
    support: none
  delegation:
    support: none
  diff_mode:
    support: none
  platform:
    platforms: all
author:
- Ansible Core Team
"""

EXAMPLES = """
- name: Emit a deprecation notice for role users
  ansible.builtin.display:
    msg: "This role variable is changing its name!"
    level: deprecated

- name: Show a warning
  ansible.builtin.display:
    msg: "Maintenance window starts in 5 minutes."
    level: warning

- name: Normal message
  ansible.builtin.display:
    msg: "Deployment step completed."

- name: Warn about old variable
  ansible.builtin.display:
    msg: "'old_var' is deprecated; use 'new_var' instead"
    level: deprecated
  when: old_var is defined
"""

RETURN = """
msg:
  description: The message that was emitted.
  returned: always
  type: str
level:
  description: The level at which the message was emitted.
  returned: always
  type: str
changed:
  description: Always false; this action never changes state.
  returned: always
  type: bool
  sample: false
"""
