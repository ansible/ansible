#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Dag Wieers <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}

DOCUMENTATION = r'''
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
      - A list of string expressions of the same form that can be passed to the 'when' statement.
    type: list
    required: true
  fail_msg:
    description:
      - The customized message used for a failing assertion.
      - This argument was called 'msg' before Ansible 2.7, now it is renamed to 'fail_msg' with alias 'msg'.
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
      - Set this to C(yes) to avoid verbose output.
    type: bool
    default: no
    version_added: "2.8"
notes:
     - This module is also supported for Windows targets.
seealso:
- module: debug
- module: fail
- module: meta
author:
    - Ansible Core Team
    - Michael DeHaan
'''

EXAMPLES = r'''
- assert: { that: "ansible_os_family != 'RedHat'" }

- assert:
    that:
      - "'foo' in some_command_result.stdout"
      - number_of_the_counting == 3

- name: After version 2.7 both 'msg' and 'fail_msg' can customize failing assertion message
  assert:
    that:
      - my_param <= 100
      - my_param >= 0
    fail_msg: "'my_param' must be between 0 and 100"
    success_msg: "'my_param' is between 0 and 100"

- name: Please use 'msg' when ansible version is smaller than 2.7
  assert:
    that:
      - my_param <= 100
      - my_param >= 0
    msg: "'my_param' must be between 0 and 100"

- name: use quiet to avoid verbose output
  assert:
    that:
      - my_param <= 100
      - my_param >= 0
    quiet: true
'''
