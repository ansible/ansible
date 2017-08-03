#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2014, Richard Isaacson <richard.c.isaacson@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'core'}


DOCUMENTATION = '''
---
module: at
short_description: Schedule the execution of a command or script file via the at command.
description:
 - Use this module to schedule a command or script file to run once in the future.
 - All jobs are executed in the 'a' queue.
version_added: "1.5"
options:
  command:
    description:
     - A command to be executed in the future.
    required: false
    default: null
  script_file:
    description:
     - An existing script file to be executed in the future.
    required: false
    default: null
  count:
    description:
     - The count of units in the future to execute the command or script file.
    required: true
  units:
    description:
     - The type of units in the future to execute the command or script file.
    required: true
    choices: ["minutes", "hours", "days", "weeks"]
  state:
    description:
     - The state dictates if the command or script file should be evaluated as present(added) or absent(deleted).
    required: false
    choices: ["present", "absent"]
    default: "present"
  unique:
    description:
     - If a matching job is present a new job will not be added.
    required: false
    default: false
requirements:
 - at
author: "Richard Isaacson (@risaacson)"
'''

EXAMPLES = '''
# Schedule a command to execute in 20 minutes as root.
- at:
    command: "ls -d / > /dev/null"
    count: 20
    units: minutes

# Match a command to an existing job and delete the job.
- at:
    command: "ls -d / > /dev/null"
    state: absent

# Schedule a command to execute in 20 minutes making sure it is unique in the queue.
- at:
    command: "ls -d / > /dev/null"
    unique: true
    count: 20
    units: minutes
'''

import os
import tempfile

from ansible.module_utils.basic import AnsibleModule


def add_job(module, result, at_cmd, count, units, command, script_file):
    at_command = "%s -f %s now + %s %s" % (at_cmd, script_file, count, units)
    rc, out, err = module.run_command(at_command, check_rc=True)
    if command:
        os.unlink(script_file)
    result['changed'] = True


def delete_job(module, result, at_cmd, command, script_file):
    for matching_job in get_matching_jobs(module, at_cmd, script_file):
        at_command = "%s -d %s" % (at_cmd, matching_job)
        rc, out, err = module.run_command(at_command, check_rc=True)
        result['changed'] = True
    if command:
        os.unlink(script_file)
    module.exit_json(**result)


def get_matching_jobs(module, at_cmd, script_file):
    matching_jobs = []

    atq_cmd = module.get_bin_path('atq', True)

    # Get list of job numbers for the user.
    atq_command = "%s" % atq_cmd
    rc, out, err = module.run_command(atq_command, check_rc=True)
    current_jobs = out.splitlines()
    if len(current_jobs) == 0:
        return matching_jobs

    # Read script_file into a string.
    script_file_string = open(script_file).read().strip()

    # Loop through the jobs.
    #   If the script text is contained in a job add job number to list.
    for current_job in current_jobs:
        split_current_job = current_job.split()
        at_command = "%s -c %s" % (at_cmd, split_current_job[0])
        rc, out, err = module.run_command(at_command, check_rc=True)
        if script_file_string in out:
            matching_jobs.append(split_current_job[0])

    # Return the list.
    return matching_jobs


def create_tempfile(command):
    filed, script_file = tempfile.mkstemp(prefix='at')
    fileh = os.fdopen(filed, 'w')
    fileh.write(command)
    fileh.close()
    return script_file


def main():

    module = AnsibleModule(
        argument_spec = dict(
            command=dict(required=False,
                         type='str'),
            script_file=dict(required=False,
                             type='str'),
            count=dict(required=False,
                       type='int'),
            units=dict(required=False,
                       default=None,
                       choices=['minutes', 'hours', 'days', 'weeks'],
                       type='str'),
            state=dict(required=False,
                       default='present',
                       choices=['present', 'absent'],
                       type='str'),
            unique=dict(required=False,
                        default=False,
                        type='bool')
        ),
        mutually_exclusive=[['command', 'script_file']],
        required_one_of=[['command', 'script_file']],
        supports_check_mode=False
    )

    at_cmd = module.get_bin_path('at', True)

    command        = module.params['command']
    script_file    = module.params['script_file']
    count          = module.params['count']
    units          = module.params['units']
    state          = module.params['state']
    unique         = module.params['unique']

    if (state == 'present') and (not count or not units):
        module.fail_json(msg="present state requires count and units")

    result = {'state': state, 'changed': False}

    # If command transform it into a script_file
    if command:
        script_file = create_tempfile(command)

    # if absent remove existing and return
    if state == 'absent':
        delete_job(module, result, at_cmd, command, script_file)

    # if unique if existing return unchanged
    if unique:
        if len(get_matching_jobs(module, at_cmd, script_file)) != 0:
            if command:
                os.unlink(script_file)
            module.exit_json(**result)

    result['script_file'] = script_file
    result['count'] = count
    result['units'] = units

    add_job(module, result, at_cmd, count, units, command, script_file)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
