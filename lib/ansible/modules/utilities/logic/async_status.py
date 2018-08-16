#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>, and others
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}


DOCUMENTATION = '''
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
    required: true
  mode:
    description:
      - if C(status), obtain the status; if C(cleanup), clean up the async job cache (by default in C(~/.ansible_async/)) for the specified job I(jid).
    choices: [ "status", "cleanup" ]
    default: "status"
notes:
    - See also U(https://docs.ansible.com/playbooks_async.html)
    - This module is also supported for Windows targets.
author:
    - "Ansible Core Team"
    - "Michael DeHaan"
'''

import json
import os

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems


def main():

    module = AnsibleModule(argument_spec=dict(
        jid=dict(required=True),
        mode=dict(default='status', choices=['status', 'cleanup']),
    ))

    mode = module.params['mode']
    jid = module.params['jid']

    async_dir = os.environ.get('ANSIBLE_ASYNC_DIR', '~/.ansible_async')

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
        data = open(log_path).read()
        data = json.loads(data)
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

    # Fix error: TypeError: exit_json() keywords must be strings
    data = dict([(str(k), v) for k, v in iteritems(data)])

    module.exit_json(**data)


if __name__ == '__main__':
    main()
