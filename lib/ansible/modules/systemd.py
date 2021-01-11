#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2016, Brian Coca <bcoca@ansible.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
module: systemd
author:
    - Ansible Core Team
version_added: "2.2"
short_description:  Manage services
description:
    - Controls systemd services on remote hosts.
options:
    name:
        description:
            - Name of the service. This parameter takes the name of exactly one service to work with.
            - When using in a chroot environment you always need to specify the full name i.e. (crond.service).
        aliases: [ service, unit ]
    state:
        description:
            - C(started)/C(stopped) are idempotent actions that will not run commands unless necessary.
              C(restarted) will always bounce the service. C(reloaded) will always reload.
        choices: [ reloaded, restarted, started, stopped ]
    enabled:
        description:
            - Whether the service should start on boot. B(At least one of state and enabled are required.)
        type: bool
    force:
        description:
            - Whether to override existing symlinks.
        type: bool
        version_added: 2.6
    masked:
        description:
            - Whether the unit should be masked or not, a masked unit is impossible to start.
        type: bool
    daemon_reload:
        description:
            - Run daemon-reload before doing any other operations, to make sure systemd has read any changes.
            - When set to C(yes), runs daemon-reload even if the module does not start or stop anything.
        type: bool
        default: no
        aliases: [ daemon-reload ]
    daemon_reexec:
        description:
            - Run daemon_reexec command before doing any other operations, the systemd manager will serialize the manager state.
        type: bool
        default: no
        aliases: [ daemon-reexec ]
        version_added: "2.8"
    user:
        description:
            - (deprecated) run ``systemctl`` talking to the service manager of the calling user, rather than the service manager
              of the system.
            - This option is deprecated and will eventually be removed in 2.11. The ``scope`` option should be used instead.
            - The default value is C(false).
        type: bool
    scope:
        description:
            - Run systemctl within a given service manager scope, either as the default system scope C(system),
              the current user's scope C(user), or the scope of all users C(global).
            - "For systemd to work with 'user', the executing user must have its own instance of dbus started (systemd requirement).
              The user dbus process is normally started during normal login, but not during the run of Ansible tasks.
              Otherwise you will probably get a 'Failed to connect to bus: no such file or directory' error."
        choices: [ system, user, global ]
        default: system
        version_added: "2.7"
    no_block:
        description:
            - Do not synchronously wait for the requested operation to finish.
              Enqueued job will continue without Ansible blocking on its completion.
        type: bool
        default: no
        version_added: "2.3"
notes:
    - Since 2.4, one of the following options is required 'state', 'enabled', 'masked', 'daemon_reload', ('daemon_reexec' since 2.8),
      and all except 'daemon_reload' (and 'daemon_reexec' since 2.8) also require 'name'.
    - Before 2.4 you always required 'name'.
    - Globs are not supported in name, i.e ``postgres*.service``.
    - Supports C(check_mode).
requirements:
    - A system managed by systemd.
'''

EXAMPLES = '''
- name: Make sure a service is running
  ansible.builtin.systemd:
    state: started
    name: httpd

- name: Stop service cron on debian, if running
  ansible.builtin.systemd:
    name: cron
    state: stopped

- name: Restart service cron on centos, in all cases, also issue daemon-reload to pick up config changes
  ansible.builtin.systemd:
    state: restarted
    daemon_reload: yes
    name: crond

- name: Reload service httpd, in all cases
  ansible.builtin.systemd:
    name: httpd
    state: reloaded

- name: Enable service httpd and ensure it is not masked
  ansible.builtin.systemd:
    name: httpd
    enabled: yes
    masked: no

- name: Enable a timer for dnf-automatic
  ansible.builtin.systemd:
    name: dnf-automatic.timer
    state: started
    enabled: yes

- name: Just force systemd to reread configs (2.4 and above)
  ansible.builtin.systemd:
    daemon_reload: yes

- name: Just force systemd to re-execute itself (2.8 and above)
  ansible.builtin.systemd:
    daemon_reexec: yes
'''

RETURN = '''
status:
    description: A dictionary with the key=value pairs returned from `systemctl show`.
    returned: success
    type: complex
    sample: {
            "ActiveEnterTimestamp": "Sun 2016-05-15 18:28:49 EDT",
            "ActiveEnterTimestampMonotonic": "8135942",
            "ActiveExitTimestampMonotonic": "0",
            "ActiveState": "active",
            "After": "auditd.service systemd-user-sessions.service time-sync.target systemd-journald.socket basic.target system.slice",
            "AllowIsolate": "no",
            "Before": "shutdown.target multi-user.target",
            "BlockIOAccounting": "no",
            "BlockIOWeight": "1000",
            "CPUAccounting": "no",
            "CPUSchedulingPolicy": "0",
            "CPUSchedulingPriority": "0",
            "CPUSchedulingResetOnFork": "no",
            "CPUShares": "1024",
            "CanIsolate": "no",
            "CanReload": "yes",
            "CanStart": "yes",
            "CanStop": "yes",
            "CapabilityBoundingSet": "18446744073709551615",
            "ConditionResult": "yes",
            "ConditionTimestamp": "Sun 2016-05-15 18:28:49 EDT",
            "ConditionTimestampMonotonic": "7902742",
            "Conflicts": "shutdown.target",
            "ControlGroup": "/system.slice/crond.service",
            "ControlPID": "0",
            "DefaultDependencies": "yes",
            "Delegate": "no",
            "Description": "Command Scheduler",
            "DevicePolicy": "auto",
            "EnvironmentFile": "/etc/sysconfig/crond (ignore_errors=no)",
            "ExecMainCode": "0",
            "ExecMainExitTimestampMonotonic": "0",
            "ExecMainPID": "595",
            "ExecMainStartTimestamp": "Sun 2016-05-15 18:28:49 EDT",
            "ExecMainStartTimestampMonotonic": "8134990",
            "ExecMainStatus": "0",
            "ExecReload": "{ path=/bin/kill ; argv[]=/bin/kill -HUP $MAINPID ; ignore_errors=no ; start_time=[n/a] ; stop_time=[n/a] ; pid=0 ; code=(null) ; status=0/0 }",
            "ExecStart": "{ path=/usr/sbin/crond ; argv[]=/usr/sbin/crond -n $CRONDARGS ; ignore_errors=no ; start_time=[n/a] ; stop_time=[n/a] ; pid=0 ; code=(null) ; status=0/0 }",
            "FragmentPath": "/usr/lib/systemd/system/crond.service",
            "GuessMainPID": "yes",
            "IOScheduling": "0",
            "Id": "crond.service",
            "IgnoreOnIsolate": "no",
            "IgnoreOnSnapshot": "no",
            "IgnoreSIGPIPE": "yes",
            "InactiveEnterTimestampMonotonic": "0",
            "InactiveExitTimestamp": "Sun 2016-05-15 18:28:49 EDT",
            "InactiveExitTimestampMonotonic": "8135942",
            "JobTimeoutUSec": "0",
            "KillMode": "process",
            "KillSignal": "15",
            "LimitAS": "18446744073709551615",
            "LimitCORE": "18446744073709551615",
            "LimitCPU": "18446744073709551615",
            "LimitDATA": "18446744073709551615",
            "LimitFSIZE": "18446744073709551615",
            "LimitLOCKS": "18446744073709551615",
            "LimitMEMLOCK": "65536",
            "LimitMSGQUEUE": "819200",
            "LimitNICE": "0",
            "LimitNOFILE": "4096",
            "LimitNPROC": "3902",
            "LimitRSS": "18446744073709551615",
            "LimitRTPRIO": "0",
            "LimitRTTIME": "18446744073709551615",
            "LimitSIGPENDING": "3902",
            "LimitSTACK": "18446744073709551615",
            "LoadState": "loaded",
            "MainPID": "595",
            "MemoryAccounting": "no",
            "MemoryLimit": "18446744073709551615",
            "MountFlags": "0",
            "Names": "crond.service",
            "NeedDaemonReload": "no",
            "Nice": "0",
            "NoNewPrivileges": "no",
            "NonBlocking": "no",
            "NotifyAccess": "none",
            "OOMScoreAdjust": "0",
            "OnFailureIsolate": "no",
            "PermissionsStartOnly": "no",
            "PrivateNetwork": "no",
            "PrivateTmp": "no",
            "RefuseManualStart": "no",
            "RefuseManualStop": "no",
            "RemainAfterExit": "no",
            "Requires": "basic.target",
            "Restart": "no",
            "RestartUSec": "100ms",
            "Result": "success",
            "RootDirectoryStartOnly": "no",
            "SameProcessGroup": "no",
            "SecureBits": "0",
            "SendSIGHUP": "no",
            "SendSIGKILL": "yes",
            "Slice": "system.slice",
            "StandardError": "inherit",
            "StandardInput": "null",
            "StandardOutput": "journal",
            "StartLimitAction": "none",
            "StartLimitBurst": "5",
            "StartLimitInterval": "10000000",
            "StatusErrno": "0",
            "StopWhenUnneeded": "no",
            "SubState": "running",
            "SyslogLevelPrefix": "yes",
            "SyslogPriority": "30",
            "TTYReset": "no",
            "TTYVHangup": "no",
            "TTYVTDisallocate": "no",
            "TimeoutStartUSec": "1min 30s",
            "TimeoutStopUSec": "1min 30s",
            "TimerSlackNSec": "50000",
            "Transient": "no",
            "Type": "simple",
            "UMask": "0022",
            "UnitFileState": "enabled",
            "WantedBy": "multi-user.target",
            "Wants": "system.slice",
            "WatchdogTimestampMonotonic": "0",
            "WatchdogUSec": "0",
        }
'''  # NOQA

import os

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.facts.system.chroot import is_chroot
from ansible.module_utils.service import sysv_exists, sysv_is_enabled, fail_if_missing
from ansible.module_utils._text import to_native


def is_running_service(service_status):
    return service_status['ActiveState'] in set(['active', 'activating'])


def is_deactivating_service(service_status):
    return service_status['ActiveState'] in set(['deactivating'])


def request_was_ignored(out):
    return '=' not in out and ('ignoring request' in out or 'ignoring command' in out)


def parse_systemctl_show(lines):
    # The output of 'systemctl show' can contain values that span multiple lines. At first glance it
    # appears that such values are always surrounded by {}, so the previous version of this code
    # assumed that any value starting with { was a multi-line value; it would then consume lines
    # until it saw a line that ended with }. However, it is possible to have a single-line value
    # that starts with { but does not end with } (this could happen in the value for Description=,
    # for example), and the previous version of this code would then consume all remaining lines as
    # part of that value. Cryptically, this would lead to Ansible reporting that the service file
    # couldn't be found.
    #
    # To avoid this issue, the following code only accepts multi-line values for keys whose names
    # start with Exec (e.g., ExecStart=), since these are the only keys whose values are known to
    # span multiple lines.
    parsed = {}
    multival = []
    k = None
    for line in lines:
        if k is None:
            if '=' in line:
                k, v = line.split('=', 1)
                if k.startswith('Exec') and v.lstrip().startswith('{'):
                    if not v.rstrip().endswith('}'):
                        multival.append(v)
                        continue
                parsed[k] = v.strip()
                k = None
        else:
            multival.append(line)
            if line.rstrip().endswith('}'):
                parsed[k] = '\n'.join(multival).strip()
                multival = []
                k = None
    return parsed


# ===========================================
# Main control flow

def main():
    # initialize
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', aliases=['service', 'unit']),
            state=dict(type='str', choices=['reloaded', 'restarted', 'started', 'stopped']),
            enabled=dict(type='bool'),
            force=dict(type='bool'),
            masked=dict(type='bool'),
            daemon_reload=dict(type='bool', default=False, aliases=['daemon-reload']),
            daemon_reexec=dict(type='bool', default=False, aliases=['daemon-reexec']),
            user=dict(type='bool'),
            scope=dict(type='str', default='system', choices=['system', 'user', 'global']),
            no_block=dict(type='bool', default=False),
        ),
        supports_check_mode=True,
        required_one_of=[['state', 'enabled', 'masked', 'daemon_reload', 'daemon_reexec']],
        required_by=dict(
            state=('name', ),
            enabled=('name', ),
            masked=('name', ),
        ),
        mutually_exclusive=[['scope', 'user']],
    )

    unit = module.params['name']
    if unit is not None:
        for globpattern in (r"*", r"?", r"["):
            if globpattern in unit:
                module.fail_json(msg="This module does not currently support using glob patterns, found '%s' in service name: %s" % (globpattern, unit))

    systemctl = module.get_bin_path('systemctl', True)

    if os.getenv('XDG_RUNTIME_DIR') is None:
        os.environ['XDG_RUNTIME_DIR'] = '/run/user/%s' % os.geteuid()

    ''' Set CLI options depending on params '''
    if module.params['user'] is not None:
        # handle user deprecation, mutually exclusive with scope
        module.deprecate("The 'user' option is being replaced by 'scope'", version='2.11', collection_name='ansible.builtin')
        if module.params['user']:
            module.params['scope'] = 'user'
        else:
            module.params['scope'] = 'system'

    # if scope is 'system' or None, we can ignore as there is no extra switch.
    # The other choices match the corresponding switch
    if module.params['scope'] != 'system':
        systemctl += " --%s" % module.params['scope']

    if module.params['no_block']:
        systemctl += " --no-block"

    if module.params['force']:
        systemctl += " --force"

    rc = 0
    out = err = ''
    result = dict(
        name=unit,
        changed=False,
        status=dict(),
    )

    # Run daemon-reload first, if requested
    if module.params['daemon_reload'] and not module.check_mode:
        (rc, out, err) = module.run_command("%s daemon-reload" % (systemctl))
        if rc != 0:
            module.fail_json(msg='failure %d during daemon-reload: %s' % (rc, err))

    # Run daemon-reexec
    if module.params['daemon_reexec'] and not module.check_mode:
        (rc, out, err) = module.run_command("%s daemon-reexec" % (systemctl))
        if rc != 0:
            module.fail_json(msg='failure %d during daemon-reexec: %s' % (rc, err))

    if unit:
        found = False
        is_initd = sysv_exists(unit)
        is_systemd = False

        # check service data, cannot error out on rc as it changes across versions, assume not found
        (rc, out, err) = module.run_command("%s show '%s'" % (systemctl, unit))

        if rc == 0 and not (request_was_ignored(out) or request_was_ignored(err)):
            # load return of systemctl show into dictionary for easy access and return
            if out:
                result['status'] = parse_systemctl_show(to_native(out).split('\n'))

                is_systemd = 'LoadState' in result['status'] and result['status']['LoadState'] != 'not-found'

                is_masked = 'LoadState' in result['status'] and result['status']['LoadState'] == 'masked'

                # Check for loading error
                if is_systemd and not is_masked and 'LoadError' in result['status']:
                    module.fail_json(msg="Error loading unit file '%s': %s" % (unit, result['status']['LoadError']))

        # Workaround for https://github.com/ansible/ansible/issues/71528
        elif err and rc == 1 and 'Failed to parse bus message' in err:
            result['status'] = parse_systemctl_show(to_native(out).split('\n'))

            unit_base, sep, suffix = unit.partition('@')
            unit_search = '{unit_base}{sep}'.format(unit_base=unit_base, sep=sep)
            (rc, out, err) = module.run_command("{systemctl} list-unit-files '{unit_search}*'".format(systemctl=systemctl, unit_search=unit_search))
            is_systemd = unit_search in out

            (rc, out, err) = module.run_command("{systemctl} is-active '{unit}'".format(systemctl=systemctl, unit=unit))
            result['status']['ActiveState'] = out.rstrip('\n')

        else:
            # list taken from man systemctl(1) for systemd 244
            valid_enabled_states = [
                "enabled",
                "enabled-runtime",
                "linked",
                "linked-runtime",
                "masked",
                "masked-runtime",
                "static",
                "indirect",
                "disabled",
                "generated",
                "transient"]

            (rc, out, err) = module.run_command("%s is-enabled '%s'" % (systemctl, unit))
            if out.strip() in valid_enabled_states:
                is_systemd = True
            else:
                # fallback list-unit-files as show does not work on some systems (chroot)
                # not used as primary as it skips some services (like those using init.d) and requires .service/etc notation
                (rc, out, err) = module.run_command("%s list-unit-files '%s'" % (systemctl, unit))
                if rc == 0:
                    is_systemd = True
                else:
                    # Check for systemctl command
                    module.run_command(systemctl, check_rc=True)

        # Does service exist?
        found = is_systemd or is_initd
        if is_initd and not is_systemd:
            module.warn('The service (%s) is actually an init script but the system is managed by systemd' % unit)

        # mask/unmask the service, if requested, can operate on services before they are installed
        if module.params['masked'] is not None:
            # state is not masked unless systemd affirms otherwise
            (rc, out, err) = module.run_command("%s is-enabled '%s'" % (systemctl, unit))
            masked = out.strip() == "masked"

            if masked != module.params['masked']:
                result['changed'] = True
                if module.params['masked']:
                    action = 'mask'
                else:
                    action = 'unmask'

                if not module.check_mode:
                    (rc, out, err) = module.run_command("%s %s '%s'" % (systemctl, action, unit))
                    if rc != 0:
                        # some versions of system CAN mask/unmask non existing services, we only fail on missing if they don't
                        fail_if_missing(module, found, unit, msg='host')

        # Enable/disable service startup at boot if requested
        if module.params['enabled'] is not None:

            if module.params['enabled']:
                action = 'enable'
            else:
                action = 'disable'

            fail_if_missing(module, found, unit, msg='host')

            # do we need to enable the service?
            enabled = False
            (rc, out, err) = module.run_command("%s is-enabled '%s'" % (systemctl, unit))

            # check systemctl result or if it is a init script
            if rc == 0:
                enabled = True
            elif rc == 1:
                # if not a user or global user service and both init script and unit file exist stdout should have enabled/disabled, otherwise use rc entries
                if module.params['scope'] == 'system' and \
                        not module.params['user'] and \
                        is_initd and \
                        not out.strip().endswith('disabled') and \
                        sysv_is_enabled(unit):
                    enabled = True

            # default to current state
            result['enabled'] = enabled

            # Change enable/disable if needed
            if enabled != module.params['enabled']:
                result['changed'] = True
                if not module.check_mode:
                    (rc, out, err) = module.run_command("%s %s '%s'" % (systemctl, action, unit))
                    if rc != 0:
                        module.fail_json(msg="Unable to %s service %s: %s" % (action, unit, out + err))

                result['enabled'] = not enabled

        # set service state if requested
        if module.params['state'] is not None:
            fail_if_missing(module, found, unit, msg="host")

            # default to desired state
            result['state'] = module.params['state']

            # What is current service state?
            if 'ActiveState' in result['status']:
                action = None
                if module.params['state'] == 'started':
                    if not is_running_service(result['status']):
                        action = 'start'
                elif module.params['state'] == 'stopped':
                    if is_running_service(result['status']) or is_deactivating_service(result['status']):
                        action = 'stop'
                else:
                    if not is_running_service(result['status']):
                        action = 'start'
                    else:
                        action = module.params['state'][:-2]  # remove 'ed' from restarted/reloaded
                    result['state'] = 'started'

                if action:
                    result['changed'] = True
                    if not module.check_mode:
                        (rc, out, err) = module.run_command("%s %s '%s'" % (systemctl, action, unit))
                        if rc != 0:
                            module.fail_json(msg="Unable to %s service %s: %s" % (action, unit, err))
            # check for chroot
            elif is_chroot(module) or os.environ.get('SYSTEMD_OFFLINE') == '1':
                module.warn("Target is a chroot or systemd is offline. This can lead to false positives or prevent the init system tools from working.")
            else:
                # this should not happen?
                module.fail_json(msg="Service is in unknown state", status=result['status'])

    module.exit_json(**result)


if __name__ == '__main__':
    main()
