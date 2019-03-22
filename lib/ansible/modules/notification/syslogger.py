#!/usr/bin/python
# Copyright (c) 2017 Tim Rightnour <thegarbledone@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: syslogger

short_description: Log messages in the syslog

version_added: "2.4"

description:
    - "Uses syslog to add log entries to the host."
    - "Can specify facility and priority."

options:
    msg:
        description:
            - This is the message to place in syslog
        required: true
    priority:
        description:
            - Set the log priority
        choices: [ "emerg", "alert", "crit", "err", "warning", "notice", "info", "debug" ]
        required: false
        default: "info"
    facility:
        description:
            - Set the log facility
        choices: [ "kern", "user", "mail", "daemon", "auth", "lpr", "news",
                   "uucp", "cron", "syslog", "local0", "local1", "local2",
                   "local3", "local4", "local5", "local6", "local7" ]
        required: false
        default: "daemon"
    log_pid:
        description:
            - Log the pid in brackets
        type: bool
        required: false
        default: "no"

author:
    - Tim Rightnour (@garbled1)
'''

EXAMPLES = '''
# Full example
- name: Test syslog
  syslogger:
    msg: "Hello from ansible"
    priority: "err"
    facility: "daemon"
    log_pid: true

# Basic usage
- name: Simple Usage
  syslogger:
    msg: "I will end up as daemon.info"

'''

RETURN = '''
'''

from ansible.module_utils.basic import AnsibleModule
import syslog


def get_facility(x):
    return {
        'kern': syslog.LOG_KERN,
        'user': syslog.LOG_USER,
        'mail': syslog.LOG_MAIL,
        'daemon': syslog.LOG_DAEMON,
        'auth': syslog.LOG_AUTH,
        'lpr': syslog.LOG_LPR,
        'news': syslog.LOG_NEWS,
        'uucp': syslog.LOG_UUCP,
        'cron': syslog.LOG_CRON,
        'syslog': syslog.LOG_SYSLOG,
        'local0': syslog.LOG_LOCAL0,
        'local1': syslog.LOG_LOCAL1,
        'local2': syslog.LOG_LOCAL2,
        'local3': syslog.LOG_LOCAL3,
        'local4': syslog.LOG_LOCAL4,
        'local5': syslog.LOG_LOCAL5,
        'local6': syslog.LOG_LOCAL6,
        'local7': syslog.LOG_LOCAL7
    }.get(x, syslog.LOG_DAEMON)


def get_priority(x):
    return {
        'emerg': syslog.LOG_EMERG,
        'alert': syslog.LOG_ALERT,
        'crit': syslog.LOG_CRIT,
        'err': syslog.LOG_ERR,
        'warning': syslog.LOG_WARNING,
        'notice': syslog.LOG_NOTICE,
        'info': syslog.LOG_INFO,
        'debug': syslog.LOG_DEBUG
    }.get(x, syslog.LOG_INFO)


def run_module():
    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = dict(
        msg=dict(type='str', required=True),
        priority=dict(type='str', required=False,
                      choices=["emerg", "alert", "crit", "err", "warning",
                               "notice", "info", "debug"],
                      default='info'),
        facility=dict(type='str', required=False,
                      choices=["kern", "user", "mail", "daemon", "auth",
                               "lpr", "news", "uucp", "cron", "syslog",
                               "local0", "local1", "local2", "local3",
                               "local4", "local5", "local6", "local7"],
                      default='daemon'),
        log_pid=dict(type='bool', required=False, default=False)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    result = dict(
        changed=False,
        priority=module.params['priority'],
        facility=module.params['facility'],
        log_pid=module.params['log_pid'],
        msg=module.params['msg']
    )

    # basically, do nothing.
    if module.check_mode:
        return result

    # do the logging
    try:
        if module.params['log_pid']:
            syslog.openlog('ansible_syslogger',
                           logoption=syslog.LOG_PID,
                           facility=get_facility(module.params['facility']))
        else:
            syslog.openlog('ansible_syslogger',
                           facility=get_facility(module.params['facility']))
        syslog.syslog(get_priority(module.params['priority']),
                      module.params['msg'])
        syslog.closelog()
        result['changed'] = True

    except Exception:
        module.fail_json(error='Failed to write to syslog', **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
