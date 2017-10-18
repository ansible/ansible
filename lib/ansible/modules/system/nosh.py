#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Thomas Caravia <taca@kadisius.eu>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: nosh
author:
    - "Thomas Caravia"
version_added: "2.5"
short_description:  Manage services with nosh.
description:
    - Controls services on remote hosts using the nosh toolset.
options:
    name:
        required: true
        description:
            - Name of the service to manage.
    state:
        required: false
        choices: [ started, stopped, reset, restarted, reloaded ]
        description:
            - C(Started)/C(stopped) are idempotent actions that will not run
              commands unless necessary.
              C(restarted) will always bounce the service.
              C(reloaded) will send a SIGHUP or start the service.
              C(reset) will start or stop the service according to whether it is
              enabled or not.
    enabled:
        required: false
        choices: [ "yes", "no" ]
        description:
            - Whether the service is enabled or not, independently of *.preset file
              preference or running state. Mutually exclusive with C(preset). Will take
              effect prior to the C(reset) state.
    preset:
        required: false
        choices: [ "yes", "no" ]
        default: no
        description:
            - Enable or disable the service according to local preferences in *.preset files.
              Mutually exclusive with C(enabled). Only has an effect if set to true. Will take
              effect prior to the C(reset) state.
    user:
        required: false
        default: no
        choices: [ "yes", "no" ]
        description:
            - Run system-control talking to the service manager of the calling user, rather than
              the service manager of the system.
'''

EXAMPLES = '''
- name: start dnscache if not running
  nosh: name=dnscache state=started

- name: stop mpd, if running
  nosh: name=mpd state=stopped

- name: restart unbound or start it if not already running
  nosh:
    name: unbound
    state: restarted

- name: reload fail2ban or start it if not already running
  nosh:
    name: fail2ban
    state: reloaded

- name: disable nsd
  nosh: name=nsd enabled=no

- name: for package installers, set nginx running state according to local enable settings, preset and reset
  nosh: name=nginx preset=True state=reset

- name: reboot the host if nosh is the system manager, would need a "wait_for*" step at least, not recommended as-is
  nosh: name=reboot state=started
'''

RETURN = '''
name:
    description: name used to find the service
    returned: success
    type: string
    sample: "sshd"
service_path:
    description: resolved path for the service
    returned: success
    type: string
    sample: "/var/sv/sshd"
status:
    description: a dictionary with the key=value pairs returned by `system-control show-json SERVICE` or Loaded=False if the service is not loaded
    returned: success
    type: complex
    contains: {
            "After": [
                "/etc/service-bundles/targets/basic",
                "../sshdgenkeys",
                "log"
            ],
            "Before": [
                "/etc/service-bundles/targets/shutdown"
            ],
            "Conflicts": [],
            "DaemontoolsEncoreState": "running",
            "DaemontoolsState": "up",
            "Enabled": true,
            "LogService": "../cyclog@sshd",
            "MainPID": 661,
            "Paused": false,
            "ReadyAfterRun": false,
            "RemainAfterExit": false,
            "Required-By": [],
            "RestartExitStatusCode": 0,
            "RestartExitStatusNumber": 0,
            "RestartTimestamp": 4611686019935648081,
            "RestartUTCTimestamp": 1508260140,
            "RunExitStatusCode": 0,
            "RunExitStatusNumber": 0,
            "RunTimestamp": 4611686019935648081,
            "RunUTCTimestamp": 1508260140,
            "StartExitStatusCode": 1,
            "StartExitStatusNumber": 0,
            "StartTimestamp": 4611686019935648081,
            "StartUTCTimestamp": 1508260140,
            "StopExitStatusCode": 0,
            "StopExitStatusNumber": 0,
            "StopTimestamp": 4611686019935648081,
            "StopUTCTimestamp": 1508260140,
            "Stopped-By": [
                "/etc/service-bundles/targets/shutdown"
            ],
            "Timestamp": 4611686019935648081,
            "UTCTimestamp": 1508260140,
            "Want": "nothing",
            "Wanted-By": [
                "/etc/service-bundles/targets/server",
                "/etc/service-bundles/targets/sockets"
            ],
            "Wants": [
                "/etc/service-bundles/targets/basic",
                "../sshdgenkeys"
            ]
        }
'''


import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.service import fail_if_missing
from ansible.module_utils._text import to_native


def run_sys_ctl(module, args):
    sys_ctl = [module.get_bin_path('system-control', required=True)]
    if module.params['user']:
        sys_ctl = sys_ctl + ['--user']
    return module.run_command(sys_ctl + args)


def get_service_path(module, service):
    (rc, out, err) = run_sys_ctl(module, ['find', service])
    # fail if service not found
    if rc != 0:
        fail_if_missing(module, False, service, msg='host')
    else:
        return to_native(out).strip()


def service_is_enabled(module, service_path):
    (rc, out, err) = run_sys_ctl(module, ['is-enabled', service_path])
    return rc == 0


def service_is_preset_enabled(module, service_path):
    (rc, out, err) = run_sys_ctl(module, ['preset', '--dry-run', service_path])
    return to_native(out).strip().startswith("enable")


def service_is_loaded(module, service_path):
    (rc, out, err) = run_sys_ctl(module, ['is-loaded', service_path])
    return rc == 0


def get_service_status(module, service_path):
    (rc, out, err) = run_sys_ctl(module, ['show-json', service_path])
    # will fail if not service is not loaded
    if err is not None and err:
        module.fail_json(msg=err)
    else:
        json_out = json.loads(to_native(out).strip())
        status = json_out[service_path]  # descend past service path header
        return status


def service_is_running(service_status):
    return service_status['DaemontoolsEncoreState'] in set(['starting', 'started', 'running'])


def handle_enabled(module, result, service_path):
    """Enable or disable a service as needed.

    - 'preset' will set the enabled state according to available preset file settings.
    - 'enabled' will set the enabled state explicitly, independently of preset settings.

    These options are set to "mutually exclusive" but the explicit 'enabled' option will
    have priority if the check is bypassed.
    """
    enabled = service_is_enabled(module, service_path)

    # preset, effect only if option set to true (no reverse preset)
    if module.params['preset']:
        action = 'preset'
        preset = enabled is service_is_preset_enabled(module, service_path)
        result['preset'] = preset
        result['enabled'] = enabled

        # run preset if needed
        if preset != module.params['preset']:
            result['changed'] = True
            if not module.check_mode:
                (rc, out, err) = run_sys_ctl(module, [action, service_path])
                if rc != 0:
                    module.fail_json(msg="Unable to %s service %s: %s" % (action, service_path, out + err))
            result['preset'] = not preset
            result['enabled'] = not enabled

    # enabled/disabled state
    if module.params['enabled'] is not None:
        if module.params['enabled']:
            action = 'enable'
        else:
            action = 'disable'

        result['enabled'] = enabled

        # change enable/disable if needed
        if enabled != module.params['enabled']:
            result['changed'] = True
            if not module.check_mode:
                (rc, out, err) = run_sys_ctl(module, [action, service_path])
                if rc != 0:
                    module.fail_json(msg="Unable to %s service %s: %s" % (action, service_path, out + err))
            result['enabled'] = not enabled


def handle_state(module, result, service_path):
    """Set service running state as needed.

    Takes into account the fact that a service may not be loaded (no supervise directory) in
    which case it is 'stopped' as far as the service manager is concerned. No status information
    can be obtained and the service can only be 'started'.
    """
    # default to desired state, no action
    result['state'] = module.params['state']
    action = None

    # case for enabled/preset + reset + check_mode: use anticipated enabled status
    # otherwise test real enabled status
    if module.check_mode and (module.params['enabled'] is not None or module.params['preset']):
        enabled = result['enabled']
    else:
        enabled = service_is_enabled(module, service_path)

    # service not loaded -> not started by manager, no status information
    if not service_is_loaded(module, service_path):
        if module.params['state'] in ['started', 'restarted', 'reloaded']:
            action = 'start'
            result['state'] = 'started'
        elif module.params['state'] == 'reset':
            if enabled:
                action = 'start'
                result['state'] = 'started'
            else:
                result['state'] = 'stopped'
        else:
            result['state'] = 'stopped'

    # service is loaded
    else:
        # get status information
        result['status'] = get_service_status(module, service_path)
        running = service_is_running(result['status'])

        if module.params['state'] == 'started':
            if not running:
                action = 'start'
        elif module.params['state'] == 'stopped':
            if running:
                action = 'stop'
        # reset = start/stop according to enabled status
        elif module.params['state'] == 'reset':
            if enabled is not running:
                if running:
                    action = 'stop'
                    result['state'] = 'stopped'
                else:
                    action = 'start'
                    result['state'] = 'started'
        # start if not running, 'service' module constraint
        elif module.params['state'] == 'restarted':
            if not running:
                action = 'start'
                result['state'] = 'started'
            else:
                action = 'condrestart'
        # start if not running, 'service' module constraint
        elif module.params['state'] == 'reloaded':
            if not running:
                action = 'start'
                result['state'] = 'started'
            else:
                action = 'hangup'

    # change state as needed
    if action:
        result['changed'] = True
        if not module.check_mode:
            (rc, out, err) = run_sys_ctl(module, [action, service_path])
            if rc != 0:
                module.fail_json(msg="Unable to %s service %s: %s" % (action, service_path, err))

# ===========================================
# Main control flow


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            state=dict(choices=['started', 'stopped', 'reset', 'restarted', 'reloaded'], type='str'),
            enabled=dict(type='bool'),
            preset=dict(type='bool'),
            user=dict(type='bool'),
        ),
        supports_check_mode=True,
        mutually_exclusive=[['enabled', 'preset']],
    )

    service = module.params['name']
    rc = 0
    out = err = ''
    result = {
        'name': service,
        'changed': False,
        'status': {},
    }

    # check service can be found (or fail) and get path
    service_path = get_service_path(module, service)
    result['service_path'] = service_path

    # set enabled state, service need not be loaded
    if module.params['enabled'] is not None or module.params['preset']:
        handle_enabled(module, result, service_path)

    # set service running state
    if module.params['state'] is not None:
        handle_state(module, result, service_path)

    # get final service status if possible
    if service_is_loaded(module, service_path):
        result['status'] = get_service_status(module, service_path)
    else:
        result['status'] = {'Loaded': False}

    module.exit_json(**result)

if __name__ == '__main__':
    main()
