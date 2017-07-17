#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Dag Wieers <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}

DOCUMENTATION = r'''
---
module: sleep
short_description: Sleep the task execution for some time
description:
- Sleep the task execution for some time for a specific host.
- This module is different from the M(pause) module in that it works at the task execution level.
- 'This module is only useful for specific strategies (e.g. C(strategy: free) that allow a free flow of tasks per target.'
- This module is also supported for Windows targets.
version_added: '2.4'
options:
  minutes:
    description:
    - A positive number of minutes to sleep.
    default: 0
  seconds:
    description:
    - A positive number of seconds to sleep.
    default: 0
author:
- Dag Wieers (@dagwieers)
notes:
- If you specify 0 or negative for minutes or seconds, it will wait for 1 second,
- This module is also supported for Windows targets.
'''

EXAMPLES = r'''
- name: Sleep for 5 seconds
  sleep:
    seconds: 5

- name: Sleep a random number of seconds (between 0 and 60)
  sleep:
    seconds: '{{ 600|random }}'
'''

RETURN = r'''
elapsed:
  description: The number of seconds the action plugin was sleeping
  returned: always
  type: int
  sample: 5
'''
