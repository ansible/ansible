#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Dag Wieers <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: fail
short_description: Fail with custom message
description:
- This module fails the progress with a custom message.
- It can be useful for bailing out when a certain condition is met using C(when).
- This module is also supported for Windows targets.
version_added: "0.8"
options:
  msg:
    description:
    - The customized message used for failing execution.
    - If omitted, fail will simply bail out with a generic message.
    type: str
    default: Failed as requested from task
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
        support: none
    diff_mode:
        support: none
    delegation:
        details: Aside from C(register) and/or in combination with C(delegate_facts), it has little effect.
        support:  partial
    platform:
        platforms: all
seealso:
- module: ansible.builtin.assert
- module: ansible.builtin.debug
- module: ansible.builtin.meta
author:
- Dag Wieers (@dagwieers)
'''

EXAMPLES = r'''
- name: Example using fail and when together
  fail:
    msg: The system may not be provisioned according to the CMDB status.
  when: cmdb_status != "to-be-staged"
'''
