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
    - If C(terminate), terminate the async job for the specified job I(jid). This option also implies C(cleanup). Added in 2.13.
    type: str
    choices: [ cleanup, status, terminate ]
    default: status
  signal:
    description:
      - A symbolic signal name or non-negative decimal integer, specifying the signal to be sent instead of the default TERM
    type: raw
    default: TERM
    version_added: "2.13"
extends_documentation_fragment:
- action_common_attributes
- action_common_attributes.flow
attributes:
    action:
        support: full
    async:
        support: none
    check_mode:
        support: none
    diff_mode:
        support: none
    bypass_host_loop:
        support: none
    platform:
        support: full
        platforms: posix, windows
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
  ansible.builtin.yum:
    name: docker-io
    state: present
  async: 1000
  poll: 0
  register: yum_sleeper

- name: Wait for asynchronous job to end
  ansible.builtin.async_status:
    jid: '{{ yum_sleeper.ansible_job_id }}'
  register: job_result
  until: job_result.finished
  retries: 100
  delay: 10

- name: Terminate job
  ansible.builtin.async_status:
    jid: '{{ yum_sleeper.ansible_job_id }}'
    mode: terminate
'''

RETURN = r'''
ansible_job_id:
  description: The asynchronous job id
  returned: success
  type: str
  sample: '360874038559.4169'
finished:
  description: Whether the asynchronous job has finished (C(1)) or not (C(0))
  returned: always
  type: int
  sample: 1
started:
  description: Whether the asynchronous job has started (C(1)) or not (C(0))
  returned: always
  type: int
  sample: 1
stdout:
  description: Any output returned by async_wrapper
  returned: always
  type: str
stderr:
  description: Any errors returned by async_wrapper
  returned: always
  type: str
erased:
  description: Path to erased job file
  returned: when file is erased
  type: str
terminated:
  description: Whether process was sent SIGKILL
  returned: when mode=terminate
  type: bool
'''

import json
import os
import signal

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems
from ansible.module_utils._text import to_native

SIGSTR_MAP = {k[3:]: v for k, v in signal.__dict__.items() if k[:3] == 'SIG' or '_' not in k}
SIGINTS = list(SIGSTR_MAP.values())


def main():

    module = AnsibleModule(argument_spec=dict(
        jid=dict(type='str', required=True),
        mode=dict(type='str', default='status', choices=['cleanup', 'status', 'terminate']),
        # passed in from the async_status action plugin
        _async_dir=dict(type='path', required=True),
        signal=dict(type='raw', default='TERM'),
    ))

    mode = module.params['mode']
    jid = module.params['jid']
    async_dir = module.params['_async_dir']
    sig = module.params['signal']

    if sig not in SIGSTR_MAP and sig not in SIGINTS:
        module.fail_json(msg='Invalid signal: %s' % sig)

    sig = SIGSTR_MAP.get(sig, sig)

    # setup logging directory
    logdir = os.path.expanduser(async_dir)
    log_path = os.path.join(logdir, jid)

    if not os.path.exists(log_path):
        module.fail_json(msg="could not find job", ansible_job_id=jid, started=1, finished=1)

    if mode == 'cleanup':
        os.unlink(log_path)
        module.exit_json(ansible_job_id=jid, erased=log_path)

    # NOT in cleanup mode, assume regular status mode
    # no remote kill mode currently exists, but probably should
    # consider log_path + ".pid" file and also unlink that above

    data = None
    try:
        with open(log_path) as f:
            data = json.loads(f.read())
    except Exception:
        if not data:
            # file not written yet?  That means it is running
            module.exit_json(results_file=log_path, ansible_job_id=jid, started=1, finished=0)
        else:
            module.fail_json(ansible_job_id=jid, results_file=log_path,
                             msg="Could not parse job output: %s" % data, started=1, finished=1)

    if 'started' not in data:
        data['finished'] = 1
        data['ansible_job_id'] = jid
    elif 'finished' not in data:
        data['finished'] = 0

    if not data['finished'] and mode == 'terminate':
        try:
            os.killpg(data['pid'], sig)
        except KeyError:
            module.fail_json(
                ansible_job_id=jid,
                results_file=log_path,
                started=1,
                finished=data['finished'],
                msg="Missing pid, cannot terminate"
            )
        else:
            os.unlink(log_path)
            data['terminated'] = True
    elif mode == 'terminate':
        data['terminated'] = False

    # Fix error: TypeError: exit_json() keywords must be strings
    data = {to_native(k): v for k, v in iteritems(data)}

    module.exit_json(**data)


if __name__ == '__main__':
    main()
