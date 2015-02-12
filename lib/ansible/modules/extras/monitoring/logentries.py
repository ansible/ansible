#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Ivan Vanderbyl <ivan@app.io>
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: logentries
author: Ivan Vanderbyl
short_description: Module for tracking logs via logentries.com 
description:
    - Sends logs to LogEntries in realtime
version_added: "1.6"
options:
    path:
        description:
            - path to a log file
        required: true
    state:
        description:
            - following state of the log
        choices: [ 'present', 'absent' ]
        required: false
        default: present
    name:
        description:
            - name of the log
        required: false
    logtype:
        description:
            - type of the log
        required: false

notes:
    - Requires the LogEntries agent which can be installed following the instructions at logentries.com
'''
EXAMPLES = '''
- logentries: path=/var/log/nginx/access.log state=present name=nginx-access-log
- logentries: path=/var/log/nginx/error.log state=absent
'''

def query_log_status(module, le_path, path, state="present"):
    """ Returns whether a log is followed or not. """

    if state == "present":
        rc, out, err = module.run_command("%s followed %s" % (le_path, path))
        if rc == 0:
            return True

        return False

def follow_log(module, le_path, logs, name=None, logtype=None):
    """ Follows one or more logs if not already followed. """

    followed_count = 0

    for log in logs:
        if query_log_status(module, le_path, log):
            continue

        if module.check_mode:
            module.exit_json(changed=True)

        cmd = [le_path, 'follow', log]
        if name:
            cmd.extend(['--name',name])
        if logtype:
            cmd.extend(['--type',logtype])
        rc, out, err = module.run_command(' '.join(cmd))

        if not query_log_status(module, le_path, log):
            module.fail_json(msg="failed to follow '%s': %s" % (log, err.strip()))

        followed_count += 1

    if followed_count > 0:
        module.exit_json(changed=True, msg="followed %d log(s)" % (followed_count,))

    module.exit_json(changed=False, msg="logs(s) already followed")

def unfollow_log(module, le_path, logs):
    """ Unfollows one or more logs if followed. """

    removed_count = 0

    # Using a for loop incase of error, we can report the package that failed
    for log in logs:
        # Query the log first, to see if we even need to remove.
        if not query_log_status(module, le_path, log):
            continue

        if module.check_mode:
            module.exit_json(changed=True)
        rc, out, err = module.run_command([le_path, 'rm', log])

        if query_log_status(module, le_path, log):
            module.fail_json(msg="failed to remove '%s': %s" % (log, err.strip()))

        removed_count += 1

    if removed_count > 0:
        module.exit_json(changed=True, msg="removed %d package(s)" % removed_count)

    module.exit_json(changed=False, msg="logs(s) already unfollowed")

def main():
    module = AnsibleModule(
        argument_spec = dict(
            path = dict(required=True),
            state = dict(default="present", choices=["present", "followed", "absent", "unfollowed"]),
            name = dict(required=False, default=None, type='str'),
            logtype = dict(required=False, default=None, type='str', aliases=['type'])
        ),
        supports_check_mode=True
    )

    le_path = module.get_bin_path('le', True, ['/usr/local/bin'])

    p = module.params

    # Handle multiple log files
    logs = p["path"].split(",")
    logs = filter(None, logs)

    if p["state"] in ["present", "followed"]:
        follow_log(module, le_path, logs, name=p['name'], logtype=p['logtype'])

    elif p["state"] in ["absent", "unfollowed"]:
        unfollow_log(module, le_path, logs)

# import module snippets
from ansible.module_utils.basic import *

main()
