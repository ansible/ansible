#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2016, Andrew Gaffney <andrew@agaffney.org>
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

DOCUMENTATION = '''
module: openwrt_init
author:
    - "Andrew Gaffney (@agaffney)"
version_added: "2.3"
short_description:  Manage services on OpenWrt.
description:
    - Controls OpenWrt services on remote hosts.
options:
    name:
        required: true
        description:
            - Name of the service.
        aliases: ['service']
    state:
        required: false
        default: null
        choices: [ 'started', 'stopped', 'restarted', 'reloaded' ]
        description:
            - C(started)/C(stopped) are idempotent actions that will not run commands unless necessary.
              C(restarted) will always bounce the service. C(reloaded) will always reload.
    enabled:
        required: false
        choices: [ "yes", "no" ]
        default: null
        description:
            - Whether the service should start on boot. B(At least one of state and enabled are required.)
    pattern:
        required: false
        description:
        - If the service does not respond to the 'running' command, name a
          substring to look for as would be found in the output of the I(ps)
          command as a stand-in for a 'running' result.  If the string is found,
          the service will be assumed to be running.
notes:
    - One option other than name is required.
requirements:
    - An OpenWrt system
'''

EXAMPLES = '''
# Example action to start service httpd, if not running
- openwrt_init: state=started name=httpd
# Example action to stop service cron, if running
- openwrt_init: name=cron state=stopped
# Example action to reload service httpd, in all cases
- openwrt_init: name=httpd state=reloaded
# Example action to enable service httpd
- openwrt_init:
    name: httpd
    enabled: yes
'''

RETURN = '''
'''

import os
import glob
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_bytes, to_native

module = None
init_script = None

# ===============================
# Check if service is enabled
def is_enabled():
    (rc, out, err) = module.run_command("%s enabled" % init_script)
    if rc == 0:
        return True
    return False

# ===========================================
# Main control flow

def main():
    global module, init_script
    # init
    module = AnsibleModule(
        argument_spec = dict(
                name = dict(required=True, type='str', aliases=['service']),
                state = dict(choices=['started', 'stopped', 'restarted', 'reloaded'], type='str'),
                enabled = dict(type='bool'),
                pattern = dict(required=False, default=None),
            ),
            supports_check_mode=True,
            required_one_of=[['state', 'enabled']],
        )

    # initialize
    service = module.params['name']
    init_script = '/etc/init.d/' + service
    rc = 0
    out = err = ''
    result = {
        'name':  service,
        'changed': False,
    }

    # check if service exists
    if not os.path.exists(init_script):
        module.fail_json(msg='service %s does not exist' % service)

    # Enable/disable service startup at boot if requested
    if module.params['enabled'] is not None:
        # do we need to enable the service?
        enabled = is_enabled()

        # default to current state
        result['enabled'] = enabled

        # Change enable/disable if needed
        if enabled != module.params['enabled']:
            result['changed'] = True
            if module.params['enabled']:
                action = 'enable'
            else:
                action = 'disable'

            if not module.check_mode:
                (rc, out, err) = module.run_command("%s %s" % (init_script, action))
                # openwrt init scripts can return a non-zero exit code on a successful 'enable'
                # command if the init script doesn't contain a STOP value, so we ignore the exit
                # code and explicitly check if the service is now in the desired state
                if is_enabled() != module.params['enabled']:
                    module.fail_json(msg="Unable to %s service %s: %s" % (action, service, err))

            result['enabled'] = not enabled

    if module.params['state'] is not None:
        running = False

        # check if service is currently running
        if module.params['pattern']:
            # Find ps binary
            psbin = module.get_bin_path('ps', True)

            # this should be busybox ps, so we only want/need to the 'w' option
            (rc, psout, pserr) = module.run_command('%s w' % psbin)
            # If rc is 0, set running as appropriate
            if rc == 0:
                lines = psout.split("\n")
                for line in lines:
                    if module.params['pattern'] in line and not "pattern=" in line:
                        # so as to not confuse ./hacking/test-module
                        running = True
                        break
        else:
            (rc, out, err) = module.run_command("%s running" % init_script)
            if rc == 0:
                running = True

        # default to desired state
        result['state'] = module.params['state']

        # determine action, if any
        action = None
        if module.params['state'] == 'started':
            if not running:
                action = 'start'
                result['changed'] = True
        elif module.params['state'] == 'stopped':
            if running:
                action = 'stop'
                result['changed'] = True
        else:
            action = module.params['state'][:-2] # remove 'ed' from restarted/reloaded
            result['state'] = 'started'
            result['changed'] = True

        if action:
            if not module.check_mode:
                (rc, out, err) = module.run_command("%s %s" % (init_script, action))
                if rc != 0:
                    module.fail_json(msg="Unable to %s service %s: %s" % (action, service, err))


    module.exit_json(**result)

if __name__ == '__main__':
    main()
