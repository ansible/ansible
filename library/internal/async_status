#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>, and others
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

DOCUMENTATION = '''
---
module: async_status
short_description: Obtain status of asynchronous task
description:
     - "This module gets the status of an asynchronous task."
version_added: "0.5"
options:
  jid:
    description:
      - Job or task identifier
    required: true
    default: null
    aliases: []
  mode:
    description:
      - if C(status), obtain the status; if C(cleanup), clean up the async job cache
        located in C(~/.ansible_async/) for the specified job I(jid).
    required: false
    choices: [ "status", "cleanup" ]
    default: "status"
notes:
    - See also U(http://docs.ansible.com/playbooks_async.html)
requirements: []
author: Michael DeHaan
'''

import datetime
import traceback

def main():

    module = AnsibleModule(argument_spec=dict(
        jid=dict(required=True),
        mode=dict(default='status', choices=['status','cleanup']),
    ))

    mode = module.params['mode']
    jid  = module.params['jid']

    # setup logging directory
    logdir = os.path.expanduser("~/.ansible_async")
    log_path = os.path.join(logdir, jid)

    if not os.path.exists(log_path):
        module.fail_json(msg="could not find job", ansible_job_id=jid)

    if mode == 'cleanup':
        os.unlink(log_path)
        module.exit_json(ansible_job_id=jid, erased=log_path)

    # NOT in cleanup mode, assume regular status mode
    # no remote kill mode currently exists, but probably should
    # consider log_path + ".pid" file and also unlink that above

    data = file(log_path).read()
    try:
        data = json.loads(data)
    except Exception, e:
        if data == '':
            # file not written yet?  That means it is running
            module.exit_json(results_file=log_path, ansible_job_id=jid, started=1, finished=0)
        else:
            module.fail_json(ansible_job_id=jid, results_file=log_path,
                msg="Could not parse job output: %s" % data)

    if not 'started' in data:
        data['finished'] = 1
        data['ansible_job_id'] = jid

    # Fix error: TypeError: exit_json() keywords must be strings
    data = dict([(str(k), v) for k, v in data.iteritems()])

    module.exit_json(**data)

# import module snippets
from ansible.module_utils.basic import *
main()
