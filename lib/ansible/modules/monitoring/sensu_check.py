#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2014, Anders Ingemann <aim@secoya.dk>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: sensu_check
short_description: Manage Sensu checks
version_added: 2.0
description:
  - Manage the checks that should be run on a machine by I(Sensu).
  - Most options do not have a default and will not be added to the check definition unless specified.
  - All defaults except I(path), I(state), I(backup) and I(metric) are not managed by this module,
  - they are simply specified for your convenience.
options:
  name:
    description:
      - The name of the check
      - This is the key that is used to determine whether a check exists
    required: true
  state:
    description:
      - Whether the check should be present or not
    choices: [ 'present', 'absent' ]
    default: present
  path:
    description:
      - Path to the json file of the check to be added/removed.
      - Will be created if it does not exist (unless I(state=absent)).
      - The parent folders need to exist when I(state=present), otherwise an error will be thrown
    default: /etc/sensu/conf.d/checks.json
  backup:
    description:
      - Create a backup file (if yes), including the timestamp information so
      - you can get the original file back if you somehow clobbered it incorrectly.
    type: bool
    default: 'no'
  command:
    description:
      - Path to the sensu check to run (not required when I(state=absent))
    required: true
  handlers:
    description:
      - List of handlers to notify when the check fails
    default: []
  subscribers:
    description:
      - List of subscribers/channels this check should run for
      - See sensu_subscribers to subscribe a machine to a channel
    default: []
  interval:
    description:
      - Check interval in seconds
  timeout:
    description:
      - Timeout for the check
    default: 10
  ttl:
    description:
      - Time to live in seconds until the check is considered stale
    version_added: 2.4
  handle:
    description:
      - Whether the check should be handled or not
    type: bool
    default: 'yes'
  subdue_begin:
    description:
      - When to disable handling of check failures
  subdue_end:
    description:
      - When to enable handling of check failures
  dependencies:
    description:
      - Other checks this check depends on, if dependencies fail,
      - handling of this check will be disabled
    default: []
  metric:
    description:
      - Whether the check is a metric
    type: bool
    default: 'no'
  standalone:
    description:
      - Whether the check should be scheduled by the sensu client or server
      - This option obviates the need for specifying the I(subscribers) option
    type: bool
    default: 'no'
  publish:
    description:
      - Whether the check should be scheduled at all.
      - You can still issue it via the sensu api
    type: bool
    default: 'yes'
  occurrences:
    description:
      - Number of event occurrences before the handler should take action
    default: 1
  refresh:
    description:
      - Number of seconds handlers should wait before taking second action
  aggregate:
    description:
      - Classifies the check as an aggregate check,
      - making it available via the aggregate API
    type: bool
    default: 'no'
  low_flap_threshold:
    description:
      - The low threshold for flap detection
  high_flap_threshold:
    description:
      - The high threshold for flap detection
  custom:
    version_added: "2.1"
    description:
      - A hash/dictionary of custom parameters for mixing to the configuration.
      - You can't rewrite others module parameters using this
    default: {}
  source:
    version_added: "2.1"
    description:
      - The check source, used to create a JIT Sensu client for an external resource (e.g. a network switch).
author: "Anders Ingemann (@andsens)"
'''

EXAMPLES = '''
# Fetch metrics about the CPU load every 60 seconds,
# the sensu server has a handler called 'relay' which forwards stats to graphite
- name: get cpu metrics
  sensu_check:
    name: cpu_load
    command: /etc/sensu/plugins/system/cpu-mpstat-metrics.rb
    metric: yes
    handlers: relay
    subscribers: common
    interval: 60

# Check whether nginx is running
- name: check nginx process
  sensu_check:
    name: nginx_running
    command: /etc/sensu/plugins/processes/check-procs.rb -f /var/run/nginx.pid
    handlers: default
    subscribers: nginx
    interval: 60

# Stop monitoring the disk capacity.
# Note that the check will still show up in the sensu dashboard,
# to remove it completely you need to issue a DELETE request to the sensu api.
- name: check disk
  sensu_check:
    name: check_disk_capacity
    state: absent
'''

import json
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


def sensu_check(module, path, name, state='present', backup=False):
    changed = False
    reasons = []

    stream = None
    try:
        try:
            stream = open(path, 'r')
            config = json.load(stream)
        except IOError as e:
            if e.errno is 2:  # File not found, non-fatal
                if state == 'absent':
                    reasons.append('file did not exist and state is `absent\'')
                    return changed, reasons
                config = {}
            else:
                module.fail_json(msg=to_native(e), exception=traceback.format_exc())
        except ValueError:
            msg = '{path} contains invalid JSON'.format(path=path)
            module.fail_json(msg=msg)
    finally:
        if stream:
            stream.close()

    if 'checks' not in config:
        if state == 'absent':
            reasons.append('`checks\' section did not exist and state is `absent\'')
            return changed, reasons
        config['checks'] = {}
        changed = True
        reasons.append('`checks\' section did not exist')

    if state == 'absent':
        if name in config['checks']:
            del config['checks'][name]
            changed = True
            reasons.append('check was present and state is `absent\'')

    if state == 'present':
        if name not in config['checks']:
            check = {}
            config['checks'][name] = check
            changed = True
            reasons.append('check was absent and state is `present\'')
        else:
            check = config['checks'][name]
        simple_opts = ['command',
                       'handlers',
                       'subscribers',
                       'interval',
                       'timeout',
                       'ttl',
                       'handle',
                       'dependencies',
                       'standalone',
                       'publish',
                       'occurrences',
                       'refresh',
                       'aggregate',
                       'low_flap_threshold',
                       'high_flap_threshold',
                       'source',
                       ]
        for opt in simple_opts:
            if module.params[opt] is not None:
                if opt not in check or check[opt] != module.params[opt]:
                    check[opt] = module.params[opt]
                    changed = True
                    reasons.append('`{opt}\' did not exist or was different'.format(opt=opt))
            else:
                if opt in check:
                    del check[opt]
                    changed = True
                    reasons.append('`{opt}\' was removed'.format(opt=opt))

        if module.params['custom']:
            # Convert to json
            custom_params = module.params['custom']
            overwrited_fields = set(custom_params.keys()) & set(simple_opts + ['type', 'subdue', 'subdue_begin', 'subdue_end'])
            if overwrited_fields:
                msg = 'You can\'t overwriting standard module parameters via "custom". You are trying overwrite: {opt}'.format(opt=list(overwrited_fields))
                module.fail_json(msg=msg)

            for k, v in custom_params.items():
                if k in config['checks'][name]:
                    if not config['checks'][name][k] == v:
                        changed = True
                        reasons.append('`custom param {opt}\' was changed'.format(opt=k))
                else:
                    changed = True
                    reasons.append('`custom param {opt}\' was added'.format(opt=k))
                check[k] = v
            simple_opts += custom_params.keys()

        # Remove obsolete custom params
        for opt in set(config['checks'][name].keys()) - set(simple_opts + ['type', 'subdue', 'subdue_begin', 'subdue_end']):
            changed = True
            reasons.append('`custom param {opt}\' was deleted'.format(opt=opt))
            del check[opt]

        if module.params['metric']:
            if 'type' not in check or check['type'] != 'metric':
                check['type'] = 'metric'
                changed = True
                reasons.append('`type\' was not defined or not `metric\'')
        if not module.params['metric'] and 'type' in check:
            del check['type']
            changed = True
            reasons.append('`type\' was defined')

        if module.params['subdue_begin'] is not None and module.params['subdue_end'] is not None:
            subdue = {'begin': module.params['subdue_begin'],
                      'end': module.params['subdue_end'],
                      }
            if 'subdue' not in check or check['subdue'] != subdue:
                check['subdue'] = subdue
                changed = True
                reasons.append('`subdue\' did not exist or was different')
        else:
            if 'subdue' in check:
                del check['subdue']
                changed = True
                reasons.append('`subdue\' was removed')

    if changed and not module.check_mode:
        if backup:
            module.backup_local(path)
        try:
            try:
                stream = open(path, 'w')
                stream.write(json.dumps(config, indent=2) + '\n')
            except IOError as e:
                module.fail_json(msg=to_native(e), exception=traceback.format_exc())
        finally:
            if stream:
                stream.close()

    return changed, reasons


def main():

    arg_spec = {'name': {'type': 'str', 'required': True},
                'path': {'type': 'str', 'default': '/etc/sensu/conf.d/checks.json'},
                'state': {'type': 'str', 'default': 'present', 'choices': ['present', 'absent']},
                'backup': {'type': 'bool', 'default': 'no'},
                'command': {'type': 'str'},
                'handlers': {'type': 'list'},
                'subscribers': {'type': 'list'},
                'interval': {'type': 'int'},
                'timeout': {'type': 'int'},
                'ttl': {'type': 'int'},
                'handle': {'type': 'bool'},
                'subdue_begin': {'type': 'str'},
                'subdue_end': {'type': 'str'},
                'dependencies': {'type': 'list'},
                'metric': {'type': 'bool', 'default': 'no'},
                'standalone': {'type': 'bool'},
                'publish': {'type': 'bool'},
                'occurrences': {'type': 'int'},
                'refresh': {'type': 'int'},
                'aggregate': {'type': 'bool'},
                'low_flap_threshold': {'type': 'int'},
                'high_flap_threshold': {'type': 'int'},
                'custom': {'type': 'dict'},
                'source': {'type': 'str'},
                }

    required_together = [['subdue_begin', 'subdue_end']]

    module = AnsibleModule(argument_spec=arg_spec,
                           required_together=required_together,
                           supports_check_mode=True)
    if module.params['state'] != 'absent' and module.params['command'] is None:
        module.fail_json(msg="missing required arguments: %s" % ",".join(['command']))

    path = module.params['path']
    name = module.params['name']
    state = module.params['state']
    backup = module.params['backup']

    changed, reasons = sensu_check(module, path, name, state, backup)

    module.exit_json(path=path, changed=changed, msg='OK', name=name, reasons=reasons)


if __name__ == '__main__':
    main()
