#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Ivan Vanderbyl <ivan@app.io>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: logentries
author: "Ivan Vanderbyl (@ivanvanderbyl)"
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
# Track nginx logs
- logentries:
    path: /var/log/nginx/access.log
    state: present
    name: nginx-access-log

# Stop tracking nginx logs
- logentries:
    path: /var/log/nginx/error.log
    state: absent
'''

from ansible.module_utils.basic import AnsibleModule


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
            cmd.extend(['--name', name])
        if logtype:
            cmd.extend(['--type', logtype])
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

    # Using a for loop in case of error, we can report the package that failed
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
        argument_spec=dict(
            path=dict(required=True),
            state=dict(default="present", choices=["present", "followed", "absent", "unfollowed"]),
            name=dict(required=False, default=None, type='str'),
            logtype=dict(required=False, default=None, type='str', aliases=['type'])
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


if __name__ == '__main__':
    main()
