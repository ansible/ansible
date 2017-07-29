#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'core'}

DOCUMENTATION = """
---
module: net_command
version_added: "2.4"
author: "Trishna Guha (@trishnag)"
short_description: Run arbitrary commands on a network device
description:
  - Sends an arbitrary set of commands to network node and returns the results
    read from the device.  This module includes an
    argument that will cause the module to wait for a specific condition
    before returning or timing out if the condition is not met.
options:
  commands:
    description:
      - The commands to send to the remote network device over the
        configured provider.  The resulting output from the command
        is returned.  If the I(wait_for) argument is provided, the
        module is not returned until the condition is satisfied or
        the number of I(retries) has been exceeded.
    required: true
  wait_for:
    description:
      - Specifies what to evaluate from the output of the command
        and what conditionals to apply.  This argument will cause
        the task to wait for a particular conditional to be true
        before moving forward.   If the conditional is not true
        by the configured retries, the task fails.  See examples.
    required: false
    default: null
    aliases: ['waitfor']
    version_added: "2.2"
  match:
    description:
      - The I(match) argument is used in conjunction with the
        I(wait_for) argument to specify the match policy.  Valid
        values are C(all) or C(any).  If the value is set to C(all)
        then all conditionals in the I(wait_for) must be satisfied.  If
        the value is set to C(any) then only one of the values must be
        satisfied.
    required: false
    default: all
    choices: ['any', 'all']
    version_added: "2.2"
  retries:
    description:
      - Specifies the number of retries a command should be tried
        before it is considered failed.  The command is run on the
        target device every retry and evaluated against the I(wait_for)
        conditionals.
    required: false
    default: 10
  interval:
    description:
      - Configures the interval in seconds to wait between retries
        of the command.  If the command does not pass the specified
        conditional, the interval indicates how to long to wait before
        trying the command again.
    required: false
    default: 1
"""

EXAMPLES = """
- name: run show version on remote devices
  net_command:
    commands: show version
- name: run show version and check to see if output contains Network vendor name
  net_command:
    commands: show version
    wait_for: result[0] contains Network vendor name
- name: run multiple commands on remote nodes
  net_command:
    commands:
      - show version
      - show interfaces
- name: run multiple commands and evaluate the output
  net_command:
    commands:
      - show version
      - show interfaces
    wait_for:
      - result[0] contains Network vendor name
      - result[1] contains Loopback0
- name: run commands and specify the output format
  net_command:
    commands:
      - command: show version
        output: json
"""

RETURN = """
stdout:
  description: The set of responses from the commands
  returned: always apart from low level errors (such as action plugin)
  type: list
  sample: ['...', '...']
stdout_lines:
  description: The value of stdout split into a list
  returned: always apart from low level errors (such as action plugin)
  type: list
  sample: [['...', '...'], ['...'], ['...']]
failed_conditions:
  description: The list of conditionals that have failed
  returned: failed
  type: list
  sample: ['...', '...']
"""
