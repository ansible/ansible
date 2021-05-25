#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>, and others
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: async_status
short_description: Obtain status of asynchronous task
description:
- This module gets the status of an asynchronous task.
- This module is also supported for Windows targets.
version_added: "0.5"
options:
  jid:
    description:
    - Job or task identifier
    type: str
    required: true
  mode:
    description:
    - If C(status), obtain the status.
    - If C(cleanup), clean up the async job cache (by default in C(~/.ansible_async/)) for the specified job I(jid).
    type: str
    choices: [ cleanup, status ]
    default: status
notes:
- This module is also supported for Windows targets.
seealso:
- ref: playbooks_async
  description: Detailed information on how to use asynchronous actions and polling.
author:
- Ansible Core Team
- Michael DeHaan
'''

EXAMPLES = r'''
---
- name: Asynchronous yum task
  yum:
    name: docker-io
    state: present
  async: 1000
  poll: 0
  register: yum_sleeper

- name: Wait for asynchronous job to end
  async_status:
    jid: '{{ yum_sleeper.ansible_job_id }}'
  register: job_result
  until: job_result.finished
  retries: 100
  delay: 10
'''

RETURN = r'''
ansible_job_id:
  description: The asynchronous job id
  returned: success
  type: str
  sample: '360874038559.4169'
finished:
  description: Whether the asynchronous job has finished (C(1)) or not (C(0))
  returned: success
  type: int
  sample: 1
started:
  description: Whether the asynchronous job has started (C(1)) or not (C(0))
  returned: success
  type: int
  sample: 1
'''
