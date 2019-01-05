#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2014, Richard Isaacson <richard.c.isaacson@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'core'}

DOCUMENTATION = '''
---
module: at
short_description: Schedule the execution of a command or script file via the at command
description:
 - Use this module to schedule a command or script file to run once in the future.
 - All jobs are executed in the 'a' queue.
version_added: "1.5"
options:
  command:
    description:
     - A command to be executed in the future.
  script_file:
    description:
     - An existing script file to be executed in the future.
  occasion:
    description:
     - Supply a specific date string to execute the job on.
     - Various formats are acceptable including midnight, noon, teatime, tomorrow, mon, JAN, next saturday, 4pm + 3 days or now + 60 minutes.
    version_added: "2.8"
  validate_occasion:
    description:
      - Set this to no to turn off validation of the occasion string and try your luck.
    type: bool
    default: yes
    version_added: "2.8"
  count:
    description:
     - The count of units in the future to execute the command or script file.
  units:
    description:
     - The type of units in the future to execute the command or script file.
    choices: [ minutes, hours, days, weeks ]
  state:
    description:
     - The state dictates if the command or script file should be evaluated as present(added) or absent(deleted).
    choices: [ absent, present ]
    default: present
  unique:
    description:
     - If a matching job is present a new job will not be added.
    type: bool
    default: 'no'
requirements:
 - at
author:
- Richard Isaacson (@risaacson)
'''

EXAMPLES = '''
- name: Schedule a command to execute in 20 minutes as root.
  at:
    command: ls -d / >/dev/null
    count: 20
    units: minutes

- name: Match a command to an existing job and delete the job.
  at:
    command: ls -d / >/dev/null
    state: absent

- name: Schedule a command to execute in 20 minutes making sure it is unique in the queue.
  at:
    command: ls -d / >/dev/null
    count: 20
    units: minutes
    unique: yes

- name: Schedule a command for tomorrow
  at:
    command: ls -d / >/dev/null
    occasion: tomorrow

- name: Schedule a command for midnight
  at:
    command: ls -d / >/dev/null
    occasion: midnight

- name: Schedule a command for noon tomorrow
  at:
    command: ls -d / >/dev/null
    occasion: noon tomorrow

- name: Schedule a command for next saturday
  at:
    command: ls -d / >/dev/null
    occasion: next saturday

- name: Schedule a command for monday
  at:
    command: ls -d / >/dev/null
    occasion: mon

- name: Schedule a command for a fixed date
  at:
    command: ls -d / >/dev/null
    occasion: 2:30 PM 17.09.2099
'''

import os
import re
import tempfile

from ansible.module_utils.basic import AnsibleModule


def add_job(module, result, at_cmd, occasion, count, units, command, script_file):
    if count:
        at_command = "%s -f %s now + %s %s" % (at_cmd, script_file, count, units)
    else:
        at_command = "%s -f %s %s" % (at_cmd, script_file, occasion)
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
        argument_spec=dict(
            command=dict(type='str'),
            script_file=dict(type='str'),
            occasion=dict(type='str'),
            validate_occasion=dict(type='bool', default=True),
            count=dict(type='int'),
            units=dict(type='str', choices=['minutes', 'hours', 'days', 'weeks']),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            unique=dict(type='bool', default=False),
        ),
        mutually_exclusive=[['command', 'script_file'], ['occasion', 'count']],
        required_one_of=[['command', 'script_file']],
        supports_check_mode=False,
    )

    at_cmd = module.get_bin_path('at', True)

    command = module.params['command']
    script_file = module.params['script_file']
    occasion = module.params['occasion']
    validate_occasion = module.params['validate_occasion']
    count = module.params['count']
    units = module.params['units']
    state = module.params['state']
    unique = module.params['unique']

    occasion_regexp = [
        "tomorrow",
        "midnight",
        "noon",
        "teatime",
        "noon tomorrow",
        "next week",
        "next monday",
        "next tuesday",
        "next wednesday",
        "next thursday",
        "next friday",
        "next saturday",
        "next sunday",
        "mon",
        "tue",
        "wed",
        "thu",
        "fri",
        "sat",
        "sun",
        r'[0-2][0-9]\:[0-9][0-9]',  # HH:MM
        r'[0-2][0-9]\:[0-9][0-9]\:[0-9][0-9]',  # HH:MM:ss
        r'[0-9]+\:[0-5][0-9] [A|P]M',  # 12:30 AM
        r'[0-9]+\:[0-5][0-9] [P|A]M [M|T|W|T|F|S][o|u|e|h|r|a][n|e|d|u|i|t]',  # 9:30 PM Thu
        r'now \+ [0-9]+ (minutes*|hours*|days*|weeks*|months*|years*)',  # now + 3 days
        r'[0-9]+ [A|P]M \+ [0-9]+ (minutes*|hours*|days*|weeks*|months*|years*)',  # 4 PM + 55 minutes
        r'[0-9]+\:[0-9]+ [A|P]M (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) [0-9]+',  # 2:30 PM Sep 17
    ]
    if (state == 'present' and ((count and not units) or (units and not count) or (not count and not units and not occasion))):
        module.fail_json(msg="present state requires count and units or occasion to be set")
    if occasion:
        if any(re.compile(regex).match(occasion) for regex in occasion_regexp) or not validate_occasion:
            pass
        else:
            module.fail_json(msg="occasion is in an invalid format. Check the format or set validate_occasion to 'no'")

    result = dict(
        changed=False,
        state=state,
    )

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
    if count:
        result['count'] = count
        result['units'] = units
    else:
        result['occasion'] = occasion

    add_job(module, result, at_cmd, occasion, count, units, command, script_file)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
