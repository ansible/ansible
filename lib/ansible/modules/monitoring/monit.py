#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Darryl Stoflet <stoflet@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
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
  state:
    description:
      - The state of service
    required: true
    choices: [ "present", "started", "stopped", "restarted", "monitored", "unmonitored", "reloaded" ]
  timeout:
    description:
      - If there are pending actions for the service monitored by monit, then Ansible will check
        for up to this many seconds to verify the requested action has been performed.
        Ansible will sleep for five seconds between each check.
    default: 300
    version_added: "2.1"
author: "Darryl Stoflet (@dstoflet)"
'''

EXAMPLES = '''
# Manage the state of program "httpd" to be in "started" state.
- monit:
    name: httpd
    state: started
'''

import time
import re

from ansible.module_utils.basic import AnsibleModule


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

    def monit_version():
        rc, out, err = module.run_command('%s -V' % MONIT, check_rc=True)
        version_line = out.split('\n')[0]
        version = re.search(r"[0-9]+\.[0-9]+", version_line).group().split('.')
        # Use only major and minor even if there are more these should be enough
        return int(version[0]), int(version[1])

    def is_version_higher_than_5_18():
        return (MONIT_MAJOR_VERSION, MONIT_MINOR_VERSION) > (5, 18)

    def parse(parts):
        if is_version_higher_than_5_18():
            return parse_current(parts)
        else:
            return parse_older_versions(parts)

    def parse_older_versions(parts):
        if len(parts) > 2 and parts[0].lower() == 'process' and parts[1] == "'%s'" % name:
            return ' '.join(parts[2:]).lower()
        else:
            return ''

    def parse_current(parts):
        if len(parts) > 2 and parts[2].lower() == 'process' and parts[0] == name:
            return ''.join(parts[1]).lower()
        else:
            return ''

    def get_status():
        """Return the status of the process in monit, or the empty string if not present."""
        rc, out, err = module.run_command('%s %s' % (MONIT, SUMMARY_COMMAND), check_rc=True)
        for line in out.split('\n'):
            # Sample output lines:
            # Process 'name'    Running
            # Process 'name'    Running - restart pending
            parts = parse(line.split())
            if parts != '':
                return parts

        return ''

    def run_command(command):
        """Runs a monit command, and returns the new status."""
        module.run_command('%s %s %s' % (MONIT, command, name), check_rc=True)
        return get_status()

    def wait_for_monit_to_stop_pending():
        """Fails this run if there is no status or it's pending/initializing for timeout"""
        timeout_time = time.time() + timeout
        sleep_time = 5

        running_status = get_status()
        while running_status == '' or 'pending' in running_status or 'initializing' in running_status:
            if time.time() >= timeout_time:
                module.fail_json(
                    msg='waited too long for "pending", or "initiating" status to go away ({0})'.format(
                        running_status
                    ),
                    state=state
                )

            time.sleep(sleep_time)
            running_status = get_status()

    MONIT_MAJOR_VERSION, MONIT_MINOR_VERSION = monit_version()

    SUMMARY_COMMAND = ('summary', 'summary -B')[is_version_higher_than_5_18()]

    if state == 'reloaded':
        if module.check_mode:
            module.exit_json(changed=True)
        rc, out, err = module.run_command('%s reload' % MONIT)
        if rc != 0:
            module.fail_json(msg='monit reload failed', stdout=out, stderr=err)
        wait_for_monit_to_stop_pending()
        module.exit_json(changed=True, name=name, state=state)

    present = get_status() != ''

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
    running = 'running' in get_status()

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


if __name__ == '__main__':
    main()
