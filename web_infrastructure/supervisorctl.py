#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Matt Wright <matt@nobien.net>
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
import os

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
    choices: [ "present", "started", "stopped", "restarted" ]
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
author: Matt Wright, Aaron Wang <inetfuture@gmail.com>
'''

EXAMPLES = '''
# Manage the state of program to be in 'started' state.
- supervisorctl: name=my_app state=started

# Manage the state of program group to be in 'started' state.
- supervisorctl: name='my_apps:' state=started

# Restart my_app, reading supervisorctl configuration from a specified file.
- supervisorctl: name=my_app state=restarted config=/var/opt/my_project/supervisord.conf

# Restart my_app, connecting to supervisord with credentials and server URL.
- supervisorctl: name=my_app state=restarted username=test password=testpass server_url=http://localhost:9001
'''


def main():
    arg_spec = dict(
        name=dict(required=True),
        config=dict(required=False),
        server_url=dict(required=False),
        username=dict(required=False),
        password=dict(required=False),
        supervisorctl_path=dict(required=False),
        state=dict(required=True, choices=['present', 'started', 'restarted', 'stopped'])
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

    if supervisorctl_path:
        supervisorctl_path = os.path.expanduser(supervisorctl_path)
        if os.path.exists(supervisorctl_path) and module.is_executable(supervisorctl_path):
            supervisorctl_args = [supervisorctl_path]
        else:
            module.fail_json(
                msg="Provided path to supervisorctl does not exist or isn't executable: %s" % supervisorctl_path)
    else:
        supervisorctl_args = [module.get_bin_path('supervisorctl', True)]

    if config:
        supervisorctl_args.extend(['-c', os.path.expanduser(config)])
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
            rc, out, err = run_supervisorctl(action, process_name)
            if '%s: %s' % (process_name, expected_result) not in out:
                module.fail_json(msg=out)

        module.exit_json(changed=True, name=name, state=state, affected=to_take_action_on)

    if state == 'restarted':
        rc, out, err = run_supervisorctl('update')
        processes = get_matched_processes()
        take_action_on_processes(processes, lambda s: True, 'restart', 'started')

    processes = get_matched_processes()

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
        take_action_on_processes(processes, lambda s: s not in ('RUNNING', 'STARTING'), 'start', 'started')

    if state == 'stopped':
        take_action_on_processes(processes, lambda s: s in ('RUNNING', 'STARTING'), 'stop', 'stopped')

# import module snippets
from ansible.module_utils.basic import *

main()
