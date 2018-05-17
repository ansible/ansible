#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2017, Brian Coca <bcoca@ansible.com>
# (c) 2017, Adam Miller <admiller@redhat.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'core'
}

DOCUMENTATION = '''
module: sysvinit
author:
    - "Ansible Core Team"
version_added: "2.6"
short_description:  Manage SysV services.
description:
    - Controls services on target hosts that use the SysV init system.
options:
    name:
        required: true
        description:
            - Name of the service.
        aliases: ['service']
    state:
        choices: [ 'started', 'stopped', 'restarted', 'reloaded' ]
        description:
            - C(started)/C(stopped) are idempotent actions that will not run commands unless necessary.
              Not all init scripts support C(restarted) nor C(reloaded) natively, so these will both trigger a stop and start as needed.
    enabled:
        type: bool
        description:
            - Whether the service should start on boot. B(At least one of state and enabled are required.)
    sleep:
        default: 1
        description:
            - If the service is being C(restarted) or C(reloaded) then sleep this many seconds between the stop and start command.
              This helps to workaround badly behaving services.
    pattern:
        description:
            - A substring to look for as would be found in the output of the I(ps) command as a stand-in for a status result.
            - If the string is found, the service will be assumed to be running.
            - "This option is mainly for use with init scripts that don't support the 'status' option."
    runlevels:
        description:
            - The runlevels this script should be enabled/disabled from.
            - Use this to override the defaults set by the package or init script itself.
    arguments:
        description:
            - Additional arguments provided on the command line that some init scripts accept.
        aliases: [ 'args' ]
    daemonize:
        type: bool
        description:
            - Have the module daemonize as the service itself might not do so properly.
            - This is useful with badly written init scripts or deamons, which
              commonly manifests as the task hanging as it is still holding the
              tty or the service dying when the task is over as the connection
              closes the session.
        default: no
notes:
    - One option other than name is required.
requirements:
    - That the service managed has a corresponding init script.
'''

EXAMPLES = '''
- name: make sure apache2 is started
  sysvinit:
      name: apache2
      state: started
      enabled: yes

- name: make sure apache2 is started on runlevels 3 and 5
  sysvinit:
      name: apache2
      state: started
      enabled: yes
      runlevels:
        - 3
        - 5
'''

RETURN = '''
results:
    description: results from actions taken
    returned: always
    type: complex
    contains:
        "attempts": 1
        "changed": true
        "name": "apache2"
        "status": {
            "enabled": {
                "changed": true,
                "rc": 0,
                "stderr": "",
                "stdout": ""
            },
            "stopped": {
                "changed": true,
                "rc": 0,
                "stderr": "",
                "stdout": "Stopping web server: apache2.\n"
            }
        }
'''

import re
from time import sleep
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.service import sysv_is_enabled, get_sysv_script, sysv_exists, fail_if_missing, get_ps, daemonize


def main():

    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True, type='str', aliases=['service']),
            state=dict(choices=['started', 'stopped', 'restarted', 'reloaded'], type='str'),
            enabled=dict(type='bool'),
            sleep=dict(type='int', default=1),
            pattern=dict(type='str'),
            arguments=dict(type='str', aliases=['args']),
            runlevels=dict(type='list'),
            daemonize=dict(type='bool', default=False),
        ),
        supports_check_mode=True,
        required_one_of=[['state', 'enabled']],
    )

    name = module.params['name']
    action = module.params['state']
    enabled = module.params['enabled']
    runlevels = module.params['runlevels']
    pattern = module.params['pattern']
    sleep_for = module.params['sleep']
    rc = 0
    out = err = ''
    result = {
        'name': name,
        'changed': False,
        'status': {}
    }

    # ensure service exists, get script name
    fail_if_missing(module, sysv_exists(name), name)
    script = get_sysv_script(name)

    # locate binaries for service management
    paths = ['/sbin', '/usr/sbin', '/bin', '/usr/bin']
    binaries = ['chkconfig', ' update-rc.d', 'insserv', 'service']

    # Keeps track of the service status for various runlevels because we can
    # operate on multiple runlevels at once
    runlevel_status = {}

    location = {}
    for binary in binaries:
        location[binary] = module.get_bin_path(binary, opt_dirs=paths)

    # figure out enable status
    if runlevels:
        for rl in runlevels:
            runlevel_status.setdefault(rl, {})
            runlevel_status[rl]["enabled"] = sysv_is_enabled(name, runlevel=rl)
    else:
        runlevel_status["enabled"] = sysv_is_enabled(name)

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

                for stopped in ['stop', 'is dead ', 'dead but ', 'could not access pid file', 'inactive']:
                    if stopped in cleanout:
                        worked = True
                        break

                if not worked:
                    for started_status in ['run', 'start', 'active']:
                        if started_status in cleanout and "not " not in cleanout:
                            is_started = True
                            worked = True
                            break

            # hope rc is not lying to us, use often used 'bad' returns
            if not worked and rc in [1, 2, 3, 4, 69]:
                worked = True

        if not worked:
            # hail mary
            if rc == 0:
                worked = True
            # ps for luck, can only assure positive match
            elif get_ps(module, name):
                is_started = True
                worked = True
                module.warn("Used ps output to match service name and determine it is up, this is very unreliable")

    if not worked:
        module.warn("Unable to determine if service is up, assuming it is down")

    ###########################################################################
    # BEGIN: Enable/Disable
    result['status'].setdefault('enabled', {})
    result['status']['enabled']['changed'] = False
    result['status']['enabled']['rc'] = None
    result['status']['enabled']['stdout'] = None
    result['status']['enabled']['stderr'] = None
    if runlevels:
        result['status']['enabled']['runlevels'] = runlevels
        for rl in runlevels:
            if enabled != runlevel_status[rl]["enabled"]:
                result['changed'] = True
                result['status']['enabled']['changed'] = True

        if not module.check_mode and result['changed']:
            # Perform enable/disable here
            if enabled:
                if location.get('update-rc.d'):
                    (rc, out, err) = module.run_command("%s %s enable %s" % (location['update-rc.d'], name, ' '.join(runlevels)))
                elif location.get('chkconfig'):
                    (rc, out, err) = module.run_command("%s --level %s %s on" % (location['chkconfig'], ''.join(runlevels), name))
            else:
                if location.get('update-rc.d'):
                    (rc, out, err) = module.run_command("%s %s disable %s" % (location['update-rc.d'], name, ' '.join(runlevels)))
                elif location.get('chkconfig'):
                    (rc, out, err) = module.run_command("%s --level %s %s off" % (location['chkconfig'], ''.join(runlevels), name))
    else:
        if enabled != runlevel_status["enabled"]:
            result['changed'] = True
            result['status']['enabled']['changed'] = True

        if not module.check_mode and result['changed']:
            # Perform enable/disable here
            if enabled:
                if location.get('update-rc.d'):
                    (rc, out, err) = module.run_command("%s %s enable" % (location['update-rc.d'], name))
                elif location.get('chkconfig'):
                    (rc, out, err) = module.run_command("%s %s on" % (location['chkconfig'], name))
            else:
                if location.get('update-rc.d'):
                    (rc, out, err) = module.run_command("%s %s disable" % (location['update-rc.d'], name))
                elif location.get('chkconfig'):
                    (rc, out, err) = module.run_command("%s %s off" % (location['chkconfig'], name))

    # Assigned above, might be useful is something goes sideways
    if not module.check_mode and result['status']['enabled']['changed']:
        result['status']['enabled']['rc'] = rc
        result['status']['enabled']['stdout'] = out
        result['status']['enabled']['stderr'] = err
        rc, out, err = None, None, None

        if "illegal runlevel specified" in result['status']['enabled']['stderr']:
            module.fail_json(msg="Illegal runlevel specified for enable operation on service %s" % name, **result)
    # END: Enable/Disable
    ###########################################################################

    ###########################################################################
    # BEGIN: state
    result['status'].setdefault(module.params['state'], {})
    result['status'][module.params['state']]['changed'] = False
    result['status'][module.params['state']]['rc'] = None
    result['status'][module.params['state']]['stdout'] = None
    result['status'][module.params['state']]['stderr'] = None
    if action:
        action = re.sub(r'p?ed$', '', action.lower())

        def runme(doit):

            cmd = "%s %s %s %s" % (script, doit, name, module.params['arguments'])
            # how to run
            if module.params['daemonize']:
                (rc, out, err) = daemonize(cmd)
            else:
                (rc, out, err) = module.run_command(cmd)
            # FIXME: ERRORS

            if rc != 0:
                module.fail_json(msg="Failed to %s service: %s" % (action, name))

            return (rc, out, err)

        if action == 'restart':
            result['changed'] = True
            result['status'][module.params['state']]['changed'] = True
            if not module.check_mode:

                # cannot rely on existing 'restart' in init script
                for dothis in ['stop', 'start']:
                    (rc, out, err) = runme(dothis)
                    if sleep_for:
                        sleep(sleep_for)

        elif is_started != (action == 'start'):
            result['changed'] = True
            result['status'][module.params['state']]['changed'] = True
            if not module.check_mode:
                rc, out, err = runme(action)

        elif is_started == (action == 'stop'):
            result['changed'] = True
            result['status'][module.params['state']]['changed'] = True
            if not module.check_mode:
                rc, out, err = runme(action)

        if not module.check_mode and result['status'][module.params['state']]['changed']:
            result['status'][module.params['state']]['rc'] = rc
            result['status'][module.params['state']]['stdout'] = out
            result['status'][module.params['state']]['stderr'] = err
            rc, out, err = None, None, None
    # END: state
    ###########################################################################

    module.exit_json(**result)


if __name__ == '__main__':
    main()
