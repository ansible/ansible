#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2017, Brian Coca <bcoca@ansible.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = '''
metadata_version: '1.0'
status:
    - preview
supported_by': 'community'
'''

DOCUMENTATION = '''
module: sysvinit
author:
    - "Ansible Core Team"
version_added: "2.5"
short_description:  Manage SysV services.
description:
    - Controls services on target hosts that use the SysV init system.
options:
    name:
        required: true
        description:
            - Name of the service.
        aliases: ['service']
        type: string
    state:
        required: false
        type: choice
        default: null
        choices: [ 'started', 'stopped', 'restarted', 'reloaded' ]
        description:
            - C(started)/C(stopped) are idempotent actions that will not run commands unless necessary.
              Launchd does not support C(restarted) nor C(reloaded) natively, so these will both trigger a stop and start as needed.
    enabled:
        required: false
        type: boolean
        choices: [ "yes", "no" ]
        default: null
        description:
            - Whether the service should start on boot. B(At least one of state and enabled are required.)
    sleep:
        required: false
        type: number
        default: 1
        description:
            - If the service is being C(restarted) or C(reloaded) then sleep this many seconds between the stop and start command.
              This helps to workaround badly behaving services.
    pattern:
        required: false
        type: string
        description:
            - A substring to look for as would be found in the output of the I(ps) command as a stand-in for a status result.
            - If the string is found, the service will be assumed to be running.
            - This option is mainly for use with init scripts that don't support the 'status' option.
    runlevels:
        required: false
        default: null
        type: list
        description:
            - The runlevels this script should be enabled/disabled from.
            - Use this to override the defaults set by the package or init script itself.
    arguments:
        type: string
        description:
            - Additional arguments provided on the command line that some init scripts accept.
        aliases: [ 'args' ]
    daemonize:
        type: boolean
        description:
            - Have the module daemonize as the service itself might not do so properly.
            - This is useful with badly written init scripts or deamons,
              which commonly manifests as the task hanging as it is still holding the tty
              or the service dying when the task is over as the connection closes the session.
        requried: false
        default: no
notes:
    - One option other than name is required.
requirements:
    - That the service managed has a corresponding init script.
'''

EXAMPLES = '''
- sysvinit:
      name: apache2
      state: started
      enabled: yes
  name: make sure apache2 is started
'''

RETURN = '''
# defaults
'''

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
from time import sleep
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.service import sysv_is_enabled, get_sysv_script, sysv_exists, fail_if_missing, get_ps, daemonize

def main():

    module = AnsibleModule(
        argument_spec = dict(
            name = dict(required=True, type='str', aliases=['service']),
            state = dict(choices=[ 'started', 'stopped', 'restarted', 'reloaded'], type='str'),
            enabled = dict(type='bool'),
            sleep = dict(type='int', default=1),
            pattern = dict(type='str' ),
            arguments = dict(type='str' ),
            runlevels = dict(type='list' ),
            daemonize = dict(type='bool', default=False ),
        ),
        supports_check_mode=True,
        required_one_of=[['state', 'enabled']],
    )

    service = module.params['name']
    action = module.params['state']
    runlevels = module.params['runlevels']
    arguments = module.params['arguments']
    rc = 0
    out = err = ''
    result = {
        'name':  service,
        'changed': False,
        'status': {},
    }

    # ensure service exists, get script name
    fail_if_missing(module, sysv_exists(name), name)
    script = get_sysv_script(service)

    # locate binaries for service management
    paths = [ '/sbin', '/usr/sbin', '/bin', '/usr/bin' ]
    binaries = [ 'chkconfig', ' update-rc.d', 'insserv', 'service' ]
    initpaths = [ '/etc/init.d' ]

    for binary in binaries:
        location[binary] = module.get_bin_path(binary, opt_dirs=paths)

    # figure out enable status
    is_enabled = False
    if location.get('chkconfig'):
        (rc, out, err) = module.run_command("%s --list %s" % (location['chkconfig'], name))
        is_enabled = 'chkconfig --add %s' % name not in err
    #elif enable_cmd.endswith('update-rc.d'):
    #    (rc, out, err) = module.run_command("%s -n %s disable" % (enable_cmd, name))
    #elif enable_cmd.endswith('insserv'):
    #    (rc, out, err) = module.run_command("%s -rn %s" % (enable_cmd, name))
    #elif enable_cmd.endswith('service'):
    #    pass
    else:
        # just check links ourselves
        is_enabled = sysv_is_enabled(service, runlevels)

    # figure out started status, everyone does it different!
    is_started = False

    # user knows other methods fail and supplied pattern
    if pattern:
        is_started = get_ps(module, pattern)
    else:
        worked = False
        if location.get('service'):
            # standard tool that has been 'destandarized' by reimplementation in other OS/distros
            cmd = '%s %s status' % (location['service'], name)
        elif script:
            # maybe script implements status (not LSB)
            cmd = '%s status' % script
        else:
            module.fail_json(msg="Unable to determine service status")

        (rc, out, err) = module.run_command(cmd)
        if not rc == -1:
            # special case
            if name == 'iptables' and "ACCEPT" in out:
                worked = True
                is_started = True

            # check output messages, messy but sadly more reliable than rc
            if not worked and out.count('\n') <= 1:

                cleanout = out.lower().replace(name.lower(), '')

                for stopped in [ 'stop', 'is dead ', 'dead but ', 'could not access pid file', 'inactive']:
                    if stopped in cleanout:
                        worked = True
                        break

                if not worked:
                    for is_started in ['run', 'start', 'active']:
                        if stared in cleanout and not "not " in cleanout:
                            is_started = True
                            worked = True
                            break

            # hope rc is not lying to us, use often used 'bad' returns
            if not worked and rc in [1, 2, 3, 4, 69]:
                worked = True

        # ps for luck, can only assure positive match
        if not worked:
            if get_ps(module, name):
                is_started = True
                worked = True
                module.warn("Used ps output to match service name and determine it is up, this is very unreliable")

        # hail mary
        if not worked:
            if rc == 0:
                is_started = True

    if not worked:
        module.warn("Unable to determine if service is up, assuming it is down")


    # Enable/Disable
    if enabled != is_enabled:
        result['changed'] = True
        if not module.check_mode:
            pass

    # Process action if needed
    if action:
        action = action.lower().replace('p?ed$','')

        def runme(doit):

            cmd = "%s %s %s %s" % (script, doit, service, module.params['arguments'])
            # how to run
            if module.params['daemonize']:
                rc, out, err = daemonize(cmd)
            else:
                rc, out, err = self.run_command(cmd)
            #FIXME: ERRORS

        if action == 'restart':
            result['changed'] = True
            if not module.check_mode:

                # cannot rely on existing 'restart' in init script
                for dothis in ['stop', 'start']:
                    rc, out, err = runme(dothis)
                    if sleep_for:
                        sleep(sleep_for)

        elif is_started != (action == 'start'):
            result['changed'] = True
            if not module.check_mode:
                rc, out, err = runme(action)


    module.exit_json(result)
if __name__ == 'main':
    main()
