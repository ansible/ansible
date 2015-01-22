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
requirements: [ ]
author: Darryl Stoflet
'''

EXAMPLES = '''
# Manage the state of program "httpd" to be in "started" state.
- monit: name=httpd state=started
'''

def main():
    arg_spec = dict(
        name=dict(required=True),
        state=dict(required=True, choices=['present', 'started', 'restarted', 'stopped', 'monitored', 'unmonitored', 'reloaded'])
    )

    module = AnsibleModule(argument_spec=arg_spec, supports_check_mode=True)

    name = module.params['name']
    state = module.params['state']

    MONIT = module.get_bin_path('monit', True)

    if state == 'reloaded':
        if module.check_mode:
            module.exit_json(changed=True)
        rc, out, err = module.run_command('%s reload' % MONIT)
        if rc != 0:
            module.fail_json(msg='monit reload failed', stdout=out, stderr=err)
        module.exit_json(changed=True, name=name, state=state)
    
    def status():
        """Return the status of the process in monit, or the empty string if not present."""
        rc, out, err = module.run_command('%s summary' % MONIT, check_rc=True)
        for line in out.split('\n'):
            # Sample output lines:
            # Process 'name'    Running
            # Process 'name'    Running - restart pending
            parts = line.split()
            if len(parts) > 2 and parts[0].lower() == 'process' and parts[1] == "'%s'" % name:
                return ' '.join(parts[2:])
        else:
            return ''

    def run_command(command):
        """Runs a monit command, and returns the new status."""
        module.run_command('%s %s %s' % (MONIT, command, name), check_rc=True)
        return status()

    present = status() != ''

    if not present and not state == 'present':
        module.fail_json(msg='%s process not presently configured with monit' % name, name=name, state=state)

    if state == 'present':
        if not present:
            if module.check_mode:
                module.exit_json(changed=True)
            status = run_command('reload')
            if status == '':
                module.fail_json(msg='%s process not configured with monit' % name, name=name, state=state)
            else:
                module.exit_json(changed=True, name=name, state=state)
        module.exit_json(changed=False, name=name, state=state)

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
        if status in ['not monitored']:
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

main()
