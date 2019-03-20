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
supported_by: community
'''

DOCUMENTATION = '''
module: openrc
author:
    - bcoca
version_added: "2.9"
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

import re

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
        'previous': {}
    }

    # locate binaries for service management
    paths = ['/sbin', '/usr/sbin', '/bin', '/usr/bin']
    conf = module.get_bin_path('rc-config', opt_dirs=paths)
    ctl = module.get_bin_path('rc-service', opt_dirs=paths)
    status = module.get_bin_path('rc-status', opt_dirs=paths)

    def runme(doit):
        return module.run_command(' '.join([ctl, name, doit]))

    # check service exists
    (rc, out, err) = module.run_command("%s -e %s" % (ctl, name))
    if rc != 0:
        module.fail_json(msg="The '%s' service was not found." % (name), rc=rc)

    # assume enabled unless in list of disabled
    is_enabled = True
    (rc, out, err) = module.run_command("%s -u" % status)
    for line in out.splitlines():
        x = line.split('[')[0].strip()
        if name == x:
            is_enabled = False
            break
    result['previous']['enabled'] = is_enabled

    # figure out run status
    def get_status():

        status = 'UNKNOWN'
        (rc, out, err) = runme('status')
        for line in out.splitlines():
            if 'status: ' in line:
                status = line.split(':')[1].strip()
                break
        return status

    result['previous']['status'] = get_status()
    is_started = ('stopped' != result['previous']['status'])

    # Enable/Disable
    result['enabled'] = is_enabled
    if enabled not in (None, is_enabled):
        # or (runlevels and set(runlevels).symetric_difference(set(services[name]['rurnlevels'])):
        result['changed'] = True
        if not module.check_mode:
            (rc, out, err) = module.run_command("%s %s %s %s" % (conf, name, 'add' if enabled else 'delete', ' '.join(runlevels)))
            result['enabled'] = (rc == 0 and enabled)
        else:
            result['enabled'] = enabled

    # Process action if needed
    if action:

        if module.check_mode:
            # asume operations work and desired state is achieved
            result['status'] = action

        rc = 0
        action = re.sub('p?ed$', '', action)

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

        if not module.check_mode and rc != 0:
            result['failed'] = True
            result['msg'] = ''.join([out, err])

    # report status of current service
    if not module.check_mode:
        # no assumptions, check actual status
        result['status'] = get_status()

    module.exit_json(**result)


if __name__ == '__main__':
    main()
