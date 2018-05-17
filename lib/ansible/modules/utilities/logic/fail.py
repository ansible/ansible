#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2012 Dag Wieers <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}


DOCUMENTATION = '''
---
module: fail
short_description: Fail with custom message
description:
     - This module fails the progress with a custom message. It can be
       useful for bailing out when a certain condition is met using C(when).
     - This module is also supported for Windows targets.
version_added: "0.8"
options:
  msg:
    description:
      - The customized message used for failing execution. If omitted,
        fail will simply bail out with a generic message.
    required: false
    default: "'Failed as requested from task'"
notes:
    - This module is also supported for Windows targets.

author: "Dag Wieers (@dagwieers)"
'''

EXAMPLES = '''
# Example playbook using fail and when together
- fail:
    msg: "The system may not be provisioned according to the CMDB status."
  when: cmdb_status != "to-be-staged"
'''
