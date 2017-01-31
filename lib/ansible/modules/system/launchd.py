#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2016, Brian Coca <bcoca@ansible.com>
# (c) 2106, Theo Crevon (https://github.com/tcr-ableton)
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
module: launchd
author:
    - "Ansible Core Team"
    - Theo Crevon (@tcr-ableton)
version_added: "2.2"
short_description:  Manage OS X services.
description:
    - Controls launchd services on target hosts.
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
              Launchd does not support C(restarted) nor C(reloaded) natively, so these will both trigger a stop and start as needed.
    enabled:
        required: false
        choices: [ "yes", "no" ]
        default: null
        description:
            - Whether the service should start on boot. B(At least one of state and enabled are required.)
    sleep:
        required: false
        default: 1
        description:
        - If the service is being C(restarted) or C(reloaded) then sleep this many seconds between the stop and start command.  This helps to workaround badly behaving services.
notes:
    - One option other than name is required.
requirements:
    - A system managed by launchd
    - The plistlib python library
'''

EXAMPLES = '''
# make sure spotify webhelper is started
- launchd:
      name: com.spotify.webhelper
      state: started
      become: yes
'''

RETURN = '''
#
'''

import os
from time import sleep
try:
    import plistlib
    HAS_PLIST = True
except ImportError:
    HAS_PLIST = False
from ansible.module_utils.basic import AnsibleModule

def find_service_plist(service_name):
    ''' finds the plist file associated with a service '''

    launchd_paths = [
        '~/Library/LaunchAgents',
        '/Library/LaunchAgents',
        '/Library/LaunchDaemons',
        '/System/Library/LaunchAgents',
        '/System/Library/LaunchDaemons'
    ]

    for path in launchd_paths:
        try:
            files = os.listdir(os.path.expanduser(path))
        except OSError:
            continue

        for filename in files:
            if filename == '%s.plist' % service_name:
                return os.path.join(path, filename)

def main():
    # init
    module = AnsibleModule(
        argument_spec = dict(
                name = dict(required=True, type='str', aliases=['service']),
                state = dict(choices=[ 'started', 'stopped', 'restarted', 'reloaded'], type='str'),
                enabled = dict(type='bool'),
                sleep = dict(type='int', default=1),
            ),
            supports_check_mode=True,
            required_one_of=[['state', 'enabled']],
        )

    launch = module.get_bin_path('launchctl', True)
    service = module.params['name']
    action = module.params['state']
    rc = 0
    out = err = ''
    result = {
        'name':  service,
        'changed': False,
        'status': {},
    }


    rc, dout, err = module.run_command('%s list' % (launch))
    if rc != 0:
        module.fail_json(msg='running %s list failed' % (launch))

    running = False
    found = False
    for line in out.splitlines():
        if line.strip():
            pid, last_exit_code, label = line.split('\t')
            if label.strip() == service:
                found = True
                if pid != '-':
                    running = True
                break

    # Enable/disable service startup at boot if requested
    if module.params['enabled'] is not None:
        plist_file = find_service_plist(service)
        if plist_file is None:
            msg='unable to infer the path of %s service plist file' % service
            if not found:
                msg += ' and it was not found among active services'
            module.fail_json(msg=msg)

        # Launchctl does not expose functionalities to set the RunAtLoad
        # attribute of a job definition. So we parse and modify the job definition
        # plist file directly for this purpose.
        service_plist = plistlib.readPlist(plist_file)
        enabled = service_plist.get('RunAtLoad', False)

        if module.params['enabled'] != enabled:
            if not module.check_mode:
                service_plist['RunAtLoad'] = module.params['enabled']
                plistlib.writePlist(service_plist, plist_file)
            result['changed'] = True

    do = None
    if action is not None:
        if action == 'started':
            do = 'start'
        elif action == 'stopped':
            do = 'stop'
        elif action in ['restarted', 'reloaded']:
            # launchctl does not support a restart/reload command.
            if running:
                if not module.check_mode:
                    rc, out, err = module.run_command('%s stop %s' % (launch, service))
                do = 'stop'
            if rc == 0:
                if module.params['sleep']:
                    sleep(module.params['sleep'])
                do = 'start'

        if do is not None:
            result['changed'] = True
            if not module.check_mode:
                rc, out, err = module.run_command('%s %s %s %s' % (launch, do, service))
        if rc != 0:
            msg="Unable to %s service %s: %s" % (do, service,err)
            if not found:
                msg += '\nAlso the service was not found among active services'
            module.fail_json(msg=msg)

    module.exit_json(**result)

if __name__ == 'main':
    main()
