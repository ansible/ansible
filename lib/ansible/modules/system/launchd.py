#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2016, Brian Coca <bcoca@ansible.com>
# Copyright: (c) 2016, Theo Crevon (https://github.com/tcr-ableton)
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


DOCUMENTATION = r'''
module: launchd
author:
    - "Ansible Core Team"
    - Theo Crevon (@tcr-ableton)
version_added: "2.6"
short_description:  Manage OS X services.
description:
    - This module can be used to control launchd services on target OS X hosts.
options:
    name:
      required: true
      description:
      - Name of the service.
      aliases: ['service']
    state:
      default: null
      choices: [ 'started', 'stopped', 'restarted', 'reloaded' ]
      description:
      - C(started)/C(stopped) are idempotent actions that will not run commands unless necessary.
      - Launchd does not support C(restarted) nor C(reloaded) natively, so these will both trigger a stop and start as needed.
    enabled:
      choices: [ True, False ]
      default: null
      type: 'bool'
      description:
      - Whether the service should start on boot. B(At least one of state and enabled are required.)
    sleep:
      default: 1
      description:
      - If the service is being C(restarted) or C(reloaded) then sleep this many seconds between the stop and start command.
      - This helps to workaround badly behaving services.
notes:
    - One option other than name is required.
requirements:
    - A system managed by launchd
    - The plistlib python library
'''

EXAMPLES = '''
- name: Make sure spotify webhelper is started
  launchd:
    name: com.spotify.webhelper
    state: started
    become: yes
'''

RETURN = '''
status:
    description: metadata about service status
    returned: always
    type: dict
    sample:
        {
            "current_pid": "-",
            "current_state": "stopped",
            "previous_pid": "82636",
            "previous_state": "running"
        }
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
    """Finds the plist file associated with a service"""

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
        argument_spec=dict(
            name=dict(
                required=True,
                aliases=['service']
            ),
            state=dict(
                choices=['started', 'stopped', 'restarted', 'reloaded'],
            ),
            enabled=dict(type='bool'),
            sleep=dict(type='int',
                       default=1),
        ),
        supports_check_mode=True,
        required_one_of=[
            ['state', 'enabled']
        ],
    )

    launch = module.get_bin_path('launchctl', True)
    service = module.params['name']
    action = module.params['state']
    rc = 0
    out = err = ''
    result = {
        'name': service,
        'changed': False,
        'status': {},
    }

    rc, out, err = module.run_command('%s list' % launch)
    if rc != 0:
        module.fail_json(msg='running %s list failed' % launch)

    running = False
    found = False

    for line in out.splitlines():
        if line.strip():
            pid, last_exit_code, label = line.split('\t')
            if label.strip() == service:
                found = True
                if pid != '-':
                    running = True
                    result['status']['previous_state'] = 'running'
                    result['status']['previous_pid'] = pid
                else:
                    result['status']['previous_state'] = 'stopped'
                    result['status']['previous_pid'] = '-'
                break

    if not found:
        module.fail_json(msg="Unable to find the service %s among active services." % service)

    # Enable/disable service startup at boot if requested
    if module.params['enabled'] is not None:
        plist_file = find_service_plist(service)
        if plist_file is None:
            msg = 'Unable to infer the path of %s service plist file' % service
            if not found:
                msg += ' and it was not found among active services'
            module.fail_json(msg=msg)

        # Launchctl does not expose functionality to set the RunAtLoad
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
        if action == 'started' and not running:
            do = 'start'
        elif action == 'stopped' and running:
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
                rc, out, err = module.run_command('%s %s %s' % (launch, do, service))
                if rc != 0:
                    msg = "Unable to %s service %s: %s" % (do, service, err)
                    module.fail_json(msg=msg)

        rc, out, err = module.run_command('%s list' % launch)
        if rc != 0:
            module.fail_json(msg='Failed to get status of %s after %s' % (launch, do))

        for line in out.splitlines():
            if line.strip():
                pid, last_exit_code, label = line.split('\t')
                if label.strip() == service:
                    if pid != '-':
                        result['status']['current_state'] = 'running'
                        result['status']['current_pid'] = pid
                    else:
                        result['status']['current_state'] = 'stopped'
                        result['status']['current_pid'] = '-'
                    break

    module.exit_json(**result)


if __name__ == '__main__':
    main()
