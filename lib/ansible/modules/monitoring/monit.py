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
    required: false
    default: null
  service:
    description:
      - The name of the I(monit) program/process to manage. This is an alias of B(name).
    required: false
    default: null
    version_added: "2.4"
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
  path:
    description:
      - This may be used to specify the location of the I(monit) binary if it is not available in PATH
        environment.
    required: false
    default: null
    version_added: "2.4"
  config:
    description:
      - This may be used to specify the location of the configuration file.
    required: false
    default: null
    version_added: "2.4"
requirements: [ ]
author:
  - "Darryl Stoflet (@dstoflet)"
  - "Prakritish Sen Eshore (@prakritish)"
'''

EXAMPLES = '''
# Manage the state of program "httpd" to be in "started" state.
- monit:
    name: httpd
    state: started

- name: Start monit if not started
  monit:
    path: "/opt/monit/bin/monit"
    config: "/etc/monitrc"
    state: started

- name: Check service {{ ohai_machinename }} present
  monit:
    path: "/opt/monit/bin/monit"
    config: "/etc/monitrc"
    service: "{{ ohai_machinename }}"
    state: "present"

- name: Start service apache
  monit:
    path: "/opt/monit/bin/monit"
    config: "/etc/monitrc"
    name: "apache"
    state: "started"

- name: Reload monit configuration
  monit:
    path: "/opt/monit/bin/monit"
    config: "/etc/monitrc"
    state: "reloaded"

- name: Stop Service apache
  monit:
    service: "apache"
    state: "stopped"

- name: Restart apache
  monit:
    service: "apache"
    state: "restarted"

- name: Unmonitor Service apache
  monit:
    name: "apache"
    state: "unmonitored"

- name: Monitor Service apache
  monit:
    service: "apache"
    state: "monitored"

- name: Stop monit
  monit:
    state: "stopped"
'''

import time
import platform
import os
import re
from ansible.module_utils.facts import *

def main():
    arg_spec = dict(
        service=dict(required=False),
        name=dict(required=False),
        path=dict(required=False),
        config=dict(required=False),
        timeout=dict(default=300, type='int'),
        state=dict(required=True, choices=['present', 'started', 'restarted', 'stopped', 'monitored', 'unmonitored', 'reloaded'])
    )

    module = AnsibleModule(argument_spec=arg_spec, supports_check_mode=True)

    state = module.params['state']
    timeout = module.params['timeout']

    module.params['platform'] = platform.system().lower()
    module.params['architecture'] = platform.architecture()[0]
    if module.params['architecture'] == "64bit":
        module.params['arch'] = "x64"
    else:
        module.params['arch'] = "x86"

    service_status = dict()

    def start():
        """Start Monit"""
        rc, out, err = module.run_command(MONIT)
        flag = False
        for i in range(0, module.params['timeout'], 10):
            rc, out, err = module.run_command("{} -B summary".format(MONIT))
            if rc == 0:
                flag = True
                break
            else:
                time.sleep(10)
        if not flag:
            module.fail_json(msg="Opertation timed out after {} seconds with \"{}\"".format(module.params['timeout'], err), name='monit')
        else:
            module.exit_json(changed=True, name='monit', state=state)

    def summary():
        """Return the status of the process in monit, or the empty string if not present."""
        service_status = {}
        flag = False
        for i in range(3):
            rc, out, err = module.run_command("{} -B summary".format(MONIT))
            if rc == 0:
                flag = True
                break
            else:
                time.sleep(5)
        if not flag:
            module.fail_json(msg="ERROR: {}".format(err), name='monit')
        for line in out.split('\n'):
            if re.search(r"^\s*Monit\s+", line) or re.search(r"^\s*Service Name\s*Status\s*Type", line):
                continue
            match = re.search(r"^\s*(\S+)\s+(\w+)\s+(\w+)\s*", line)
            if match:
                service_status[match.group(1).lower()] = {
                    'status': match.group(2).lower(),
                    'type': match.group(3).lower()
                }

    def status(service_name):
        rc, out, err = module.run_command("{} -B status {}".format(MONIT, service_name), check_rc=True)
        for line in out.split('\n'):
            prog = re.compile(r".*'{}'".format(service_name))
            if re.search(r"^Monit\s+", line) or prog.match(line):
                continue
            match = re.search(r"^\s*(\S+ \S+|\S+)\s+(.*)\s*$", line)
            if match:
                if service_name not in service_status:
                    service_status[service_name] = {}
                service_status[service_name][match.group(1).lower()] = match.group(2).lower()

    def run_command(command, service_name):
        """Runs a monit command, and returns the new status."""
        module.run_command("{} {} {}".format(MONIT, command, service_name), check_rc=True)
        time.sleep(5)
        summary()
        status(service_name)

    def wait_for_monit_to_stop_pending(service_name):
        """Fails this run if there is no status or it's pending/initalizing for timeout"""
        timeout_time = time.time() + timeout
        sleep_time = 5

        status(service_name)
        while service_status == '' or service_status[service_name]['status'].lower() == 'pending' \
                or service_status[service_name]['status'].lower() == 'initializing':
            if time.time() >= timeout_time:
                module.fail_json(
                    msg='waited too long for "pending", or "initiating" status to go away ({})'.format(
                        service_name
                    ),
                    state=state
                )

            time.sleep(sleep_time)
            status(service_name)

    MONIT = module.params['path'] if module.params['path'] else module.get_bin_path('monit', True)
    if module.params['config']:
        MONIT += ' -c ' + module.params['config']
    name = module.params['service'] if module.params['service'] else module.params['name']
    if not name:
        if state == 'started':
            rc, out, err = module.run_command('{} summary'.format(MONIT))
            if rc > 0:
                start()
            else:
                module.exit_json(changed=False, name='monit', state=state)
        elif state == 'stopped':
            rc, out, err = module.run_command('{} summary'.format(MONIT))
            if rc > 0:
                module.exit_json(changed=False, name='monit', state=state)
            else:
                rc, out, err = module.run_command('{} quit'.format(MONIT), check_rc=True)
                module.exit_json(changed=True, name='monit', state=state)
        elif state == 'reloaded':
            rc, out, err = module.run_command('{} reload'.format(MONIT), check_rc=True)
            summary()
            module.exit_json(changed=True, name='monit', state=state)
        else:
            module.fail_json(msg='Service name is required', state=state)

    summary()
    status(name)

    if name not in service_status:
        module.fail_json(msg="{} process not presently configured with monit".format(name), name=name, state=state)

    if state == 'present':
        if name not in service_status:
            if module.check_mode:
                module.exit_json(changed=True)
            rc, out, err = module.run_command('{} reload'.format(MONIT), check_rc=True)
            status(name)
            if name not in service_status:
                module.fail_json(msg="{} process not presently configured with monit".format(name), name=name, state=state)
            else:
                module.exit_json(changed=True, name=name, state=state)
        module.exit_json(changed=False, name=name, state=state)

    wait_for_monit_to_stop_pending(name)
    status(name)

    if state == 'stopped':
        if module.check_mode:
            module.exit_json(changed=True)
        status(name)
        run_command('stop', name)
        if service_status[name]['status'] == 'not monitored' or service_status[name]['status'] == 'stop pending':
            module.exit_json(changed=True, name=name, state=state, status=service_status[name]['status'])
        module.fail_json(msg='{} process not stopped'.format(name), state=state, status=service_status[name]['status'])

    if state == 'unmonitored':
        if module.check_mode:
            module.exit_json(changed=True)
        run_command('unmonitor', name)
        if service_status[name]['monitoring status'] == 'not monitored' or service_status[name]['monitoring status'] == 'unmonitor pending':
            module.exit_json(changed=True, name=name, state=state, status=service_status[name]['status'])
        module.fail_json(msg='%s process not unmonitored'.format(name), state=state, status=service_status[name]['status'])

    elif state == 'restarted':
        if module.check_mode:
            module.exit_json(changed=True)
        run_command('restart', name)
        if service_status[name]['status'] == 'initializing' or service_status[name]['status'] == 'restart pending' or service_status[name]['status'] == 'ok':
            module.exit_json(changed=True, name=name, state=state, status=service_status[name]['status'])
        module.fail_json(msg='{} process not restarted'.format(name), state=state, status=service_status[name]['status'])

    elif state == 'started':
        if module.check_mode:
            module.exit_json(changed=True)
        if service_status[name]['status'] == 'ok' or service_status[name]['status'] == 'initializing' or service_status[name]['status'] == 'start pending':
            module.exit_json(changed=False, name=name, state=state)
        else:
            run_command('start', name)
            time.sleep(5)
            status(name)
        if service_status[name]['status'] == 'ok' or service_status[name]['status'] == 'initializing' or service_status[name]['status'] == 'start pending':
            module.exit_json(changed=True, name=name, state=state, status=service_status[name]['status'])
        else:
            module.fail_json(msg='{} process not started'.format(name), state=state, status=service_status[name]['status'])

    elif state == 'monitored':
        if module.check_mode:
            module.exit_json(changed=True)
        if service_status[name]['monitoring status'] == 'monitored':
            module.exit_json(changed=False, name=name, state=state)
        run_command('monitor', name)
        if service_status[name]['monitoring status'] == 'monitored':
            module.exit_json(changed=True, name=name, state=state, status=service_status[name]['monitoring status'])
        else:
            module.fail_json(msg='%s process not monitored'.format(name), state=state, status=service_status[name]['monitoring status'])

    module.exit_json(changed=False, name=name, state=state)

# import module snippets
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
