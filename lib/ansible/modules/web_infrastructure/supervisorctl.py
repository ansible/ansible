#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Matt Wright <matt@nobien.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: supervisorctl
short_description: Manage the state of a program or group of programs running via supervisord
description:
     - Manage the state of a program or group of programs running via supervisord
version_added: "0.7"
options:
  name:
    description:
      - The name of the supervisord program or group to manage.
      - The name will be taken as group name when it ends with a colon I(:)
      - Group support is only available in Ansible version 1.6 or later.
    required: true
    default: null
  config:
    description:
      - The supervisor configuration file path
    required: false
    default: null
    version_added: "1.3"
  server_url:
    description:
      - URL on which supervisord server is listening
    required: false
    default: null
    version_added: "1.3"
  username:
    description:
      - username to use for authentication
    required: false
    default: null
    version_added: "1.3"
  password:
    description:
      - password to use for authentication
    required: false
    default: null
    version_added: "1.3"
  state:
    description:
      - The desired state of program/group.
    required: true
    default: null
    choices: [ "present", "started", "stopped", "restarted", "absent" ]
  supervisorctl_path:
    description:
      - path to supervisorctl executable
    required: false
    default: null
    version_added: "1.4"
notes:
  - When C(state) = I(present), the module will call C(supervisorctl reread) then C(supervisorctl add) if the program/group does not exist.
  - When C(state) = I(restarted), the module will call C(supervisorctl update) then call C(supervisorctl restart).
requirements: [ "supervisorctl" ]
author:
    - "Matt Wright (@mattupstate)"
    - "Aaron Wang (@inetfuture) <inetfuture@gmail.com>"
'''

EXAMPLES = '''
# Manage the state of program to be in 'started' state.
- supervisorctl:
    name: my_app
    state: started

# Manage the state of program group to be in 'started' state.
- supervisorctl:
    name: 'my_apps:'
    state: started

# Restart my_app, reading supervisorctl configuration from a specified file.
- supervisorctl:
    name: my_app
    state: restarted
    config: /var/opt/my_project/supervisord.conf

# Restart my_app, connecting to supervisord with credentials and server URL.
- supervisorctl:
    name: my_app
    state: restarted
    username: test
    password: testpass
    server_url: http://localhost:9001
'''

import os
from ansible.module_utils.basic import AnsibleModule, is_executable


def main():
    arg_spec = dict(
        name=dict(required=True),
        config=dict(required=False, type='path'),
        server_url=dict(required=False),
        username=dict(required=False),
        password=dict(required=False, no_log=True),
        supervisorctl_path=dict(required=False, type='path'),
        state=dict(required=True, choices=['present', 'started', 'restarted', 'stopped', 'absent'])
    )

    module = AnsibleModule(argument_spec=arg_spec, supports_check_mode=True)

    name = module.params['name']
    is_group = False
    if name.endswith(':'):
        is_group = True
        name = name.rstrip(':')
    state = module.params['state']
    config = module.params.get('config')
    server_url = module.params.get('server_url')
    username = module.params.get('username')
    password = module.params.get('password')
    supervisorctl_path = module.params.get('supervisorctl_path')

    # we check error message for a pattern, so we need to make sure that's in C locale
    module.run_command_environ_update = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C', LC_CTYPE='C')

    if supervisorctl_path:
        if os.path.exists(supervisorctl_path) and is_executable(supervisorctl_path):
            supervisorctl_args = [supervisorctl_path]
        else:
            module.fail_json(
                msg="Provided path to supervisorctl does not exist or isn't executable: %s" % supervisorctl_path)
    else:
        supervisorctl_args = [module.get_bin_path('supervisorctl', True)]

    if config:
        supervisorctl_args.extend(['-c', config])
    if server_url:
        supervisorctl_args.extend(['-s', server_url])
    if username:
        supervisorctl_args.extend(['-u', username])
    if password:
        supervisorctl_args.extend(['-p', password])

    def run_supervisorctl(cmd, name=None, **kwargs):
        args = list(supervisorctl_args)  # copy the master args
        args.append(cmd)
        if name:
            args.append(name)
        return module.run_command(args, **kwargs)

    def get_matched_processes():
        matched = []
        rc, out, err = run_supervisorctl('status')
        for line in out.splitlines():
            # One status line may look like one of these two:
            # process not in group:
            #   echo_date_lonely RUNNING pid 7680, uptime 13:22:18
            # process in group:
            #   echo_date_group:echo_date_00 RUNNING pid 7681, uptime 13:22:18
            fields = [field for field in line.split(' ') if field != '']
            process_name = fields[0]
            status = fields[1]

            if is_group:
                # If there is ':', this process must be in a group.
                if ':' in process_name:
                    group = process_name.split(':')[0]
                    if group != name:
                        continue
                else:
                    continue
            else:
                if process_name != name:
                    continue

            matched.append((process_name, status))
        return matched

    def take_action_on_processes(processes, status_filter, action, expected_result):
        to_take_action_on = []
        for process_name, status in processes:
            if status_filter(status):
                to_take_action_on.append(process_name)

        if len(to_take_action_on) == 0:
            module.exit_json(changed=False, name=name, state=state)
        if module.check_mode:
            module.exit_json(changed=True)
        for process_name in to_take_action_on:
            rc, out, err = run_supervisorctl(action, process_name, check_rc=True)
            if '%s: %s' % (process_name, expected_result) not in out:
                module.fail_json(msg=out)

        module.exit_json(changed=True, name=name, state=state, affected=to_take_action_on)

    if state == 'restarted':
        rc, out, err = run_supervisorctl('update', check_rc=True)
        processes = get_matched_processes()
        if len(processes) == 0:
            module.fail_json(name=name, msg="ERROR (no such process)")

        take_action_on_processes(processes, lambda s: True, 'restart', 'started')

    processes = get_matched_processes()

    if state == 'absent':
        if len(processes) == 0:
            module.exit_json(changed=False, name=name, state=state)

        if module.check_mode:
            module.exit_json(changed=True)
        run_supervisorctl('reread', check_rc=True)
        rc, out, err = run_supervisorctl('remove', name)
        if '%s: removed process group' % name in out:
            module.exit_json(changed=True, name=name, state=state)
        else:
            module.fail_json(msg=out, name=name, state=state)

    if state == 'present':
        if len(processes) > 0:
            module.exit_json(changed=False, name=name, state=state)

        if module.check_mode:
            module.exit_json(changed=True)
        run_supervisorctl('reread', check_rc=True)
        rc, out, err = run_supervisorctl('add', name)
        if '%s: added process group' % name in out:
            module.exit_json(changed=True, name=name, state=state)
        else:
            module.fail_json(msg=out, name=name, state=state)

    if state == 'started':
        if len(processes) == 0:
            module.fail_json(name=name, msg="ERROR (no such process)")
        take_action_on_processes(processes, lambda s: s not in ('RUNNING', 'STARTING'), 'start', 'started')

    if state == 'stopped':
        if len(processes) == 0:
            module.fail_json(name=name, msg="ERROR (no such process)")
        take_action_on_processes(processes, lambda s: s in ('RUNNING', 'STARTING'), 'stop', 'stopped')

if __name__ == '__main__':
    main()
