#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2017, Brian Coca <bcoca@ansible.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = '''
metadata_version: '1.1'
status:
    - preview
supported_by: core
'''

DOCUMENTATION = '''
module: openrc
author:
    - "Ansible Core Team"
version_added: "2.5"
short_description:  Manage OpenRC services.
description:
    - Controls services on target hosts that use the Openrc init system.
options:
    name:
        required: true
        description:
            - Name of the service.
        aliases: ['service']
    state:
        choices: [ 'started', 'stopped', 'restarted', 'reloaded', 'paused' ]
        description:
            - C(started)/C(stopped) are idempotent actions that will not run commands unless necessary.
              Not all init scripts support C(restarted) nor C(reloaded) natively, so these will both trigger a stop and start as needed.
    enabled:
        type: boolean
        description:
            - Whether the service should start on boot. B(At least one of state and enabled are required.)
    sleep:
        type: integer
        default: 1
        description:
            - If the service is being C(restarted) or C(reloaded) then sleep this many seconds between the stop and start command.
              This helps to workaround badly behaving services.
    runlevels:
        type: list
        description:
            - The runlevels this script should be enabled/disabled from.
            - Use this to override the defaults set by the package or init script itself.
        default: ['default']
notes:
    - One option other than name is required.
requirements:
    - That the service managed has a corresponding init script.
'''

EXAMPLES = '''
- openrc:
      name: apache2
      state: started
      enabled: yes
  name: make sure apache2 is started
'''

RETURN = '''
# defaults
'''

from collections import defaultdict
from time import sleep

from ansible.module_utils.basic import AnsibleModule


def main():

    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True, type='str', aliases=['service']),
            state=dict(choices=['started', 'stopped', 'restarted', 'reloaded'], type='str'),
            enabled=dict(type='bool'),
            sleep=dict(type='int', default=1),
            runlevels=dict(type='list', default=[]),
        ),
        supports_check_mode=True,
        required_one_of=[['state', 'enabled']],
    )

    name = module.params['name']
    action = module.params['state']
    enabled = module.params['enabled']
    runlevels = module.params['runlevels']
    sleep_for = module.params['sleep']
    rc = 0
    out = err = ''
    result = {
        'name': name,
        'changed': False,
        'services': {},
    }

    # locate binaries for service management
    paths = ['/sbin', '/usr/sbin', '/bin', '/usr/bin']
    rcconf = module.get_bin_path('rc-config', opt_dirs=paths)
    services = defaultdict({})
    result['services'] = services

    # figure out enable status
    (rc, out, err) = module.run_command("%s list " % rcconf)
    for line in out:
        x = line.split()
        if len(x) > 1:
            services[x[0]]['runlevel'] = x[1]
        else:
            services[x[0]]['runlevel'] = None
    is_enabled = bool(services[name]['runlevel'])

    # figure out run status
    (rc, out, err) = module.run_command("%s show all" % rcconf)
    for line in out:
        x = line.spit()
        if len(x) == 2:
            services[x[0]]['status'] = x[1].strip('[').strip(']')
    is_started = (services[name]['status'] == 'started')

    # Enable/Disable
    if enabled != is_enabled:  # or (runlevels and set(runlevels).symetric_difference(set(services[name]['rurnlevels'])):
        result['changed'] = True
        if not module.check_mode:
            if enabled:
                (rc, out, err) = module.run_command("%s add %s %s" % (rcconf, name, ' '.join(runlevels)))
            if not enabled:
                (rc, out, err) = module.run_command("%s delete %s %s" % (rcconf, name, ' '.join(runlevels)))

    # Process action if needed
    if action:
        action = action.replace('p?ed$', '')

        def runme(doit):
            return module.run_command(rcconf, doit, name)

        if action == 'restart':
            result['changed'] = True
            if not module.check_mode:
                # sleep requires us to stop/start manually
                if sleep_for:
                    for dothis in ['stop', 'start']:
                        rc, out, err = runme(dothis)
                        sleep(sleep_for)
                else:
                    rc, out, err = runme(dothis)

        elif is_started != (action == 'start'):
            result['changed'] = True
            if not module.check_mode:
                rc, out, err = runme(action)

    # report status of current service
    result['enabled'] = is_enabled
    result['status'] = services[name]['status']

    module.exit_json(result)


if __name__ == 'main':
    main()
