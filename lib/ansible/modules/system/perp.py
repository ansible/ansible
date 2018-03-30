#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2017, Dimitar Ianakiev <dimitar.q@siteground.com>
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
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: perp
author: "Dimitar Ianakiev"
version_added: "2.6"
short_description:  Manage perp services.
description:
    - Controls perp services on remote hosts using the perpctl utility.
options:
    name:
        required: true
        description:
            - Name of the service to manage.
    state:
        required: false
        choices: [ started, stopped, restarted, reloaded ]
        description:
            - C(started)/C(stopped) are idempotent actions that will not run
              commands unless necessary.  C(restarted) will always bounce the
              service (perpctl X and perpctl A).
              C(reloaded) will send a HUP (perpctl h).
'''

EXAMPLES = '''
# Example action to start nginx, if not running
 - perp:
    name: nginx
    state: started

# Example action to stop nginx, if running
 - perp:
    name: nginx
    state: stopped

# Example action to restart nginx, in all cases
 - perp:
    name: nginx
    state: restarted

# Example action to reload nginx, in all cases
 - perp:
    name: nginx
    state: reloaded
'''

RETURN = '''
full_state:
    description: The full output from perpstat
    returned: always
    type: string
    sample: "service_name: activated 1910849 seconds\n  main: up 1910849 seconds (pid 14383)\n   log: up 1910849 seconds (pid 14382)\n"
name:
    description: The name of the service being managed
    returned: always
    type: string
    sample: service_name
pid:
    description: The pid of the service in question
    returned: always
    type: int
    sample: 14383
state:
    description: The state of the service
    returned: always
    type: string
    sample: started
'''

from re import search
from ansible.module_utils.basic import AnsibleModule


class Perp(object):
    """
    Main class that handles perp.
    """

    def __init__(self, module):
        self.extra_paths = []
        self.report_vars = ['state', 'enabled', 'name', 'pid', 'duration', 'full_state']

        self.module = module

        self.name = module.params['name']
        self.enabled = None
        self.full_state = None
        self.state = None
        self.pid = None
        self.duration = None

        self.svc_cmd = module.get_bin_path('perpctl', opt_dirs=self.extra_paths)
        self.svstat_cmd = module.get_bin_path('perpstat', opt_dirs=self.extra_paths)

    def get_status(self):
        (rc, out, err) = self.execute_command([self.svstat_cmd, self.name])

        if err is not None and err:
            self.full_state = self.state = err
        else:
            self.full_state = out

            m = search(r'main.*\(pid (\d+)\)', out)
            if m:
                self.pid = m.group(1)

            m = search(r': activated (\d+)s', out)
            if m:
                self.duration = m.group(1)

            if search(r': activated', out):
                self.state = 'started'
            elif search(r'not activated', out):
                self.state = 'stopped'
            else:
                self.state = 'unknown'
                return

    def started(self):
        return self.start()

    def start(self):
        return self.execute_command([self.svc_cmd, 'A', self.name])

    def stopped(self):
        return self.stop()

    def stop(self):
        return self.execute_command([self.svc_cmd, 'X', self.name])

    def reloaded(self):
        return self.reload()

    def reload(self):
        return self.execute_command([self.svc_cmd, 'h', self.name])

    def restarted(self):
        return self.restart()

    def restart(self):
        return self.execute_command([self.svc_cmd, 'i', self.name])

    def execute_command(self, cmd):
        try:
            (rc, out, err) = self.module.run_command(' '.join(cmd))
        except Exception as e:
            self.module.fail_json(msg="failed to execute: %s" % str(e))
        return (rc, out, err)

    def report(self):
        self.get_status()
        states = {}
        for k in self.report_vars:
            states[k] = self.__dict__[k]
        return states

# ===========================================
# Main control flow


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            state=dict(type='str', choices=['started', 'stopped', 'restarted', 'reloaded']),
        ),
        supports_check_mode=True,
    )

    module.run_command_environ_update = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C', LC_CTYPE='C')

    state = module.params['state']

    perp = Perp(module)
    changed = False

    if state is not None and state != perp.state:
        changed = True
        if not module.check_mode:
            getattr(perp, state)()

    module.exit_json(changed=changed, perp=perp.report())


if __name__ == '__main__':
    main()
