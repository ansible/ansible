# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Dag Wieers <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


DOCUMENTATION = r"""
---
module: assert
short_description: Asserts given expressions are true
description:
     - This module asserts that given expressions are true with an optional custom message.
     - This module is also supported for Windows targets.
version_added: "1.5"
options:
  that:
    description:
      - A list of string expressions of the same form that can be passed to the C(when) statement.
    type: list
    elements: str
    required: true
  fail_msg:
    description:
      - The customized message used for a failing assertion.
      - This argument was called O(msg) before Ansible 2.7, now it is renamed to O(fail_msg) with alias O(msg).
    type: str
    aliases: [ msg ]
    version_added: "2.7"
  success_msg:
    description:
      - The customized message used for a successful assertion.
    type: str
    version_added: "2.7"
  quiet:
    description:
      - Set this to V(true) to avoid verbose output.
    type: bool
    default: no
    version_added: "2.8"
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
        support: none
    connection:
        support: none
    check_mode:
        support: full
    delegation:
        support: none
        details: Aside from C(register) and/or in combination with C(delegate_facts), it has little effect.
    diff_mode:
        support: none
    platform:
        platforms: all
seealso:
- module: ansible.builtin.debug
- module: ansible.builtin.fail
- module: ansible.builtin.meta
author:
    - Ansible Core Team
    - Michael DeHaan
"""

EXAMPLES = r"""
- name: A single condition can be supplied as string instead of list
  ansible.builtin.assert:
    that: "ansible_os_family != 'RedHat'"

- name: Use yaml multiline strings to ease escaping
  ansible.builtin.assert:
    that:
      - "'foo' in some_command_result.stdout"
      - number_of_the_counting == 3
      - >
        "reject" not in some_command_result.stderr

- name: After version 2.7 both O(msg) and O(fail_msg) can customize failing assertion message
  ansible.builtin.assert:
    that:
      - my_param <= 100
      - my_param >= 0
    fail_msg: "'my_param' must be between 0 and 100"
    success_msg: "'my_param' is between 0 and 100"

- name: Please use O(msg) when ansible version is smaller than 2.7
  ansible.builtin.assert:
    that:
      - my_param <= 100
      - my_param >= 0
    msg: "'my_param' must be between 0 and 100"

- name: Use quiet to avoid verbose output
  ansible.builtin.assert:
    that:
      - my_param <= 100
      - my_param >= 0
    quiet: true
"""
