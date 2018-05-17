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
module: assert
short_description: Asserts given expressions are true
description:
     - This module asserts that given expressions are true with an optional custom message.
     - This module is also supported for Windows targets.
version_added: "1.5"
options:
  that:
    description:
      - "A string expression of the same form that can be passed to the 'when' statement"
      - "Alternatively, a list of string expressions"
    required: true
  msg:
    description:
      - "The customized message used for a failing assertion"
notes:
     - This module is also supported for Windows targets.
author:
    - "Ansible Core Team"
    - "Michael DeHaan"
'''

EXAMPLES = '''
- assert: { that: "ansible_os_family != 'RedHat'" }

- assert:
    that:
      - "'foo' in some_command_result.stdout"
      - "number_of_the_counting == 3"

- assert:
    that:
      - "my_param <= 100"
      - "my_param >= 0"
    msg: "'my_param' must be between 0 and 100"
'''
