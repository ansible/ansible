#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# this is a windows documentation stub, actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_wait_for_process
version_added: '2.7'
short_description: Waits for a process to exist or not exist before continuing.
description:
- Waiting for a process to start or stop is useful when Windows services
  behave poorly and do not enumerate external dependencies in their
  manifest.
options:
  process_name_exact:
    description:
      - The name of the process(es) for which to wait.
      - Must inclue the file extension of the process binary (.exe)
  process_name_pattern:
     description:
      - RegEx pattern matching desired process(es)
  sleep:
    description:
    - Number of seconds to sleep between checks.
    - Only applies when waiting for a process to start.  Waiting for a process to start
      does not have a native non-polling mechanism. Waiting for a stop uses native PowerShell
      and does not require polling.
    default: 1
  process_min_count:
    description:
      - Minimum number of process matching the supplied pattern to satisfy C(present) condition.
      - Only applies to C(present).
    default: 1
  state:
    description:
    - When checking for a running process C(present) will block execution
      until the process exists, or until the timeout has been reached.
      C(absent) will block execution untile the processs no longer exists,
      or until the timeout has been reached.
    - When waiting for C(present), the module will return changed only if
      the process was not present on the initial check but became present on
      subsequent checks.
    - If, while waiting for C(absent), new processes matching the supplied
      pattern are started, these new processes will not be included in the
      action.
    default: present
    choices: [ absent,  present ]
  timeout:
    description:
    - The maximum number of seconds to wait for a for a process to start or stop
      before erroring out.
    default: 300
author:
- Charles Crossan (@crossan007)
'''

EXAMPLES = r'''
- name: Wait 300 seconds for all Oracle VirtualBox processes to stop. (VBoxHeadless, VirtualBox, VBoxSVC)
  win_wait_for_process:
    process_name: "v(irtual)?box(headless|svc)?"
    state: absent
    timeout: 500


- name: Wait 300 seconds for 3 instances of cmd to start, waiting 5 seconds between each check
  win_wait_for_process:
    process_name: "cmd\\.exe"
    state: present
    timeout: 500
    sleep: 5
    process_min_count: 3

'''

RETURN = r'''
elapsed:
  description: The elapsed seconds between the start of poll and the end of the
    module.
  returned: always
  type: float
  sample: 3.14159265
changed:
  description: True if a process was started or stopped during the module execution.
  returned: always
  type: bool
matched_processes:
  description: Count of processes stopped or started.
  returned: always
  type: int
'''
