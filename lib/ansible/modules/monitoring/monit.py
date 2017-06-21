#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Darryl Stoflet <stoflet@gmail.com>
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: monit
short_description: Manage the state of a program monitored via Monit
description:
     - Manage the state of a program monitored via I(Monit)
version_added: "1.2"
options:
  name:
    description:
      - The name of the I(monit) program/process to manage
    required: true
    default: null
  state:
    description:
      - The state of service
    required: true
    default: null
    choices: [ "present", "started", "stopped", "restarted", "monitored", "unmonitored", "reloaded" ]
  timeout:
    description:
      - If there are pending actions for the service monitored by monit, then Ansible will check
        for up to this many seconds to verify the the requested action has been performed.
        Ansible will sleep for five seconds between each check.
    required: false
    default: 300
    version_added: "2.1"
requirements: [ ]
author: "Darryl Stoflet (@dstoflet)"
'''

EXAMPLES = '''
# Manage the state of program "httpd" to be in "started" state.
- monit:
    name: httpd
    state: started
'''

import time


def main():
    arg_spec = dict(
        name=dict(required=True),
        timeout=dict(default=300, type='int'),
        state=dict(required=True, choices=['present', 'started', 'restarted', 'stopped', 'monitored', 'unmonitored', 'reloaded'])
    )

    module = AnsibleModule(argument_spec=arg_spec, supports_check_mode=True)

    name = module.params['name']
    state = module.params['state']
    timeout = module.params['timeout']

    MONIT = module.get_bin_path('monit', True)

    def status():
        """Return the status of the process in monit, or the empty string if not present."""
        rc, out, err = module.run_command('%s summary' % MONIT, check_rc=True)
        for line in out.split('\n'):
            # Sample output lines:
            # Process 'name'    Running
            # Process 'name'    Running - restart pending
            parts = line.split()
            if len(parts) > 2 and parts[0].lower() == 'process' and parts[1] == "'%s'" % name:
                return ' '.join(parts[2:]).lower()
        else:
            return ''

    def run_command(command):
        """Runs a monit command, and returns the new status."""
        module.run_command('%s %s %s' % (MONIT, command, name), check_rc=True)
        return status()

    def wait_for_monit_to_stop_pending():
        """Fails this run if there is no status or it's pending/initializing for timeout"""
        timeout_time = time.time() + timeout
        sleep_time = 5

        running_status = status()
        while running_status == '' or 'pending' in running_status or 'initializing' in running_status:
            if time.time() >= timeout_time:
                module.fail_json(
                    msg='waited too long for "pending", or "initiating" status to go away ({0})'.format(
                        running_status
                    ),
                    state=state
                )

            time.sleep(sleep_time)
            running_status = status()

    if state == 'reloaded':
        if module.check_mode:
            module.exit_json(changed=True)
        rc, out, err = module.run_command('%s reload' % MONIT)
        if rc != 0:
            module.fail_json(msg='monit reload failed', stdout=out, stderr=err)
        wait_for_monit_to_stop_pending()
        module.exit_json(changed=True, name=name, state=state)

    present = status() != ''

    if not present and not state == 'present':
        module.fail_json(msg='%s process not presently configured with monit' % name, name=name, state=state)

    if state == 'present':
        if not present:
            if module.check_mode:
                module.exit_json(changed=True)
            status = run_command('reload')
            if status == '':
                wait_for_monit_to_stop_pending()
            module.exit_json(changed=True, name=name, state=state)
        module.exit_json(changed=False, name=name, state=state)

    wait_for_monit_to_stop_pending()
    running = 'running' in status()

    if running and state in ['started', 'monitored']:
        module.exit_json(changed=False, name=name, state=state)

    if running and state == 'stopped':
        if module.check_mode:
            module.exit_json(changed=True)
        status = run_command('stop')
        if status in ['not monitored'] or 'stop pending' in status:
            module.exit_json(changed=True, name=name, state=state)
        module.fail_json(msg='%s process not stopped' % name, status=status)

    if running and state == 'unmonitored':
        if module.check_mode:
            module.exit_json(changed=True)
        status = run_command('unmonitor')
        if status in ['not monitored'] or 'unmonitor pending' in status:
            module.exit_json(changed=True, name=name, state=state)
        module.fail_json(msg='%s process not unmonitored' % name, status=status)

    elif state == 'restarted':
        if module.check_mode:
            module.exit_json(changed=True)
        status = run_command('restart')
        if status in ['initializing', 'running'] or 'restart pending' in status:
            module.exit_json(changed=True, name=name, state=state)
        module.fail_json(msg='%s process not restarted' % name, status=status)

    elif not running and state == 'started':
        if module.check_mode:
            module.exit_json(changed=True)
        status = run_command('start')
        if status in ['initializing', 'running'] or 'start pending' in status:
            module.exit_json(changed=True, name=name, state=state)
        module.fail_json(msg='%s process not started' % name, status=status)

    elif not running and state == 'monitored':
        if module.check_mode:
            module.exit_json(changed=True)
        status = run_command('monitor')
        if status not in ['not monitored']:
            module.exit_json(changed=True, name=name, state=state)
        module.fail_json(msg='%s process not monitored' % name, status=status)

    module.exit_json(changed=False, name=name, state=state)

# import module snippets
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
