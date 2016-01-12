#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Sebastian Kornehl <sebastian.kornehl@asideas.de>
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
# import module snippets

# Import Datadog
try:
    from datadog import initialize, api
    HAS_DATADOG = True
except:
    HAS_DATADOG = False

DOCUMENTATION = '''
---
module: datadog_monitor
short_description: Manages Datadog monitors
description:
- "Manages monitors within Datadog"
- "Options like described on http://docs.datadoghq.com/api/"
version_added: "2.0"
author: "Sebastian Kornehl (@skornehl)" 
notes: []
requirements: [datadog]
options:
    api_key:
        description: ["Your DataDog API key."]
        required: true
    app_key:
        description: ["Your DataDog app key."]
        required: true
    state:
        description: ["The designated state of the monitor."]
        required: true
        choices: ['present', 'absent', 'muted', 'unmuted']
    type:
        description:
            - "The type of the monitor."
            - The 'event alert'is available starting at Ansible 2.1
        required: false
        default: null
        choices: ['metric alert', 'service check', 'event alert']
    query:
        description: ["The monitor query to notify on with syntax varying depending on what type of monitor you are creating."]
        required: false
        default: null
    name:
        description: ["The name of the alert."]
        required: true
    message:
        description: ["A message to include with notifications for this monitor. Email notifications can be sent to specific users by using the same '@username' notation as events."]
        required: false
        default: null
    silenced:
        description: ["Dictionary of scopes to timestamps or None. Each scope will be muted until the given POSIX timestamp or forever if the value is None. "]
        required: false
        default: ""
    notify_no_data:
        description: ["A boolean indicating whether this monitor will notify when data stops reporting.."]
        required: false
        default: False
    no_data_timeframe:
        description: ["The number of minutes before a monitor will notify when data stops reporting. Must be at least 2x the monitor timeframe for metric alerts or 2 minutes for service checks."]
        required: false
        default: 2x timeframe for metric, 2 minutes for service
    timeout_h:
        description: ["The number of hours of the monitor not reporting data before it will automatically resolve from a triggered state."]
        required: false
        default: null
    renotify_interval:
        description: ["The number of minutes after the last notification before a monitor will re-notify on the current status. It will only re-notify if it's not resolved."]
        required: false
        default: null
    escalation_message:
        description: ["A message to include with a re-notification. Supports the '@username' notification we allow elsewhere. Not applicable if renotify_interval is None"]
        required: false
        default: null
    notify_audit:
        description: ["A boolean indicating whether tagged users will be notified on changes to this monitor."]
        required: false
        default: False
    thresholds:
        description: ["A dictionary of thresholds by status. Because service checks can have multiple thresholds, we don't define them directly in the query."]
        required: false
        default: {'ok': 1, 'critical': 1, 'warning': 1}
'''

EXAMPLES = '''
# Create a metric monitor
datadog_monitor:
  type: "metric alert"
  name: "Test monitor"
  state: "present"
  query: "datadog.agent.up".over("host:host1").last(2).count_by_status()"
  message: "Some message."
  api_key: "9775a026f1ca7d1c6c5af9d94d9595a4"
  app_key: "87ce4a24b5553d2e482ea8a8500e71b8ad4554ff"

# Deletes a monitor
datadog_monitor:
  name: "Test monitor"
  state: "absent"
  api_key: "9775a026f1ca7d1c6c5af9d94d9595a4"
  app_key: "87ce4a24b5553d2e482ea8a8500e71b8ad4554ff"

# Mutes a monitor
datadog_monitor:
  name: "Test monitor"
  state: "mute"
  silenced: '{"*":None}'
  api_key: "9775a026f1ca7d1c6c5af9d94d9595a4"
  app_key: "87ce4a24b5553d2e482ea8a8500e71b8ad4554ff"

# Unmutes a monitor
datadog_monitor:
  name: "Test monitor"
  state: "unmute"
  api_key: "9775a026f1ca7d1c6c5af9d94d9595a4"
  app_key: "87ce4a24b5553d2e482ea8a8500e71b8ad4554ff"
'''


def main():
    module = AnsibleModule(
        argument_spec=dict(
            api_key=dict(required=True),
            app_key=dict(required=True),
            state=dict(required=True, choises=['present', 'absent', 'mute', 'unmute']),
            type=dict(required=False, choises=['metric alert', 'service check', 'event alert']),
            name=dict(required=True),
            query=dict(required=False),
            message=dict(required=False, default=None),
            silenced=dict(required=False, default=None, type='dict'),
            notify_no_data=dict(required=False, default=False, type='bool'),
            no_data_timeframe=dict(required=False, default=None),
            timeout_h=dict(required=False, default=None),
            renotify_interval=dict(required=False, default=None),
            escalation_message=dict(required=False, default=None),
            notify_audit=dict(required=False, default=False, type='bool'),
            thresholds=dict(required=False, type='dict', default={'ok': 1, 'critical': 1, 'warning': 1}),
        )
    )

    # Prepare Datadog
    if not HAS_DATADOG:
        module.fail_json(msg='datadogpy required for this module')

    options = {
        'api_key': module.params['api_key'],
        'app_key': module.params['app_key']
    }

    initialize(**options)

    if module.params['state'] == 'present':
        install_monitor(module)
    elif module.params['state'] == 'absent':
        delete_monitor(module)
    elif module.params['state'] == 'mute':
        mute_monitor(module)
    elif module.params['state'] == 'unmute':
        unmute_monitor(module)


def _get_monitor(module):
    for monitor in api.Monitor.get_all():
        if monitor['name'] == module.params['name']:
            return monitor
    return {}


def _post_monitor(module, options):
    try:
        msg = api.Monitor.create(type=module.params['type'], query=module.params['query'],
                                 name=module.params['name'], message=module.params['message'],
                                 options=options)
        if 'errors' in msg:
            module.fail_json(msg=str(msg['errors']))
        else:
            module.exit_json(changed=True, msg=msg)
    except Exception, e:
        module.fail_json(msg=str(e))

def _equal_dicts(a, b, ignore_keys):
    ka = set(a).difference(ignore_keys)
    kb = set(b).difference(ignore_keys)
    return ka == kb and all(a[k] == b[k] for k in ka)

def _update_monitor(module, monitor, options):
    try:
        msg = api.Monitor.update(id=monitor['id'], query=module.params['query'],
                                 name=module.params['name'], message=module.params['message'],
                                 options=options)
        if 'errors' in msg:
            module.fail_json(msg=str(msg['errors']))
        elif _equal_dicts(msg, monitor, ['creator', 'overall_state']):
            module.exit_json(changed=False, msg=msg)
        else:
            module.exit_json(changed=True, msg=msg)
    except Exception, e:
        module.fail_json(msg=str(e))


def install_monitor(module):
    options = {
        "silenced": module.params['silenced'],
        "notify_no_data": module.boolean(module.params['notify_no_data']),
        "no_data_timeframe": module.params['no_data_timeframe'],
        "timeout_h": module.params['timeout_h'],
        "renotify_interval": module.params['renotify_interval'],
        "escalation_message": module.params['escalation_message'],
        "notify_audit": module.boolean(module.params['notify_audit']),
    }

    if module.params['type'] == "service check":
        options["thresholds"] = module.params['thresholds']

    monitor = _get_monitor(module)
    if not monitor:
        _post_monitor(module, options)
    else:
        _update_monitor(module, monitor, options)


def delete_monitor(module):
    monitor = _get_monitor(module)
    if not monitor:
        module.exit_json(changed=False)
    try:
        msg = api.Monitor.delete(monitor['id'])
        module.exit_json(changed=True, msg=msg)
    except Exception, e:
        module.fail_json(msg=str(e))


def mute_monitor(module):
    monitor = _get_monitor(module)
    if not monitor:
         module.fail_json(msg="Monitor %s not found!" % module.params['name'])
    elif monitor['options']['silenced']:
        module.fail_json(msg="Monitor is already muted. Datadog does not allow to modify muted alerts, consider unmuting it first.")
    elif (module.params['silenced'] is not None
         and len(set(monitor['options']['silenced']) - set(module.params['silenced'])) == 0):
        module.exit_json(changed=False)
    try:
        if module.params['silenced'] is None or module.params['silenced'] == "":
            msg = api.Monitor.mute(id=monitor['id'])
        else:
            msg = api.Monitor.mute(id=monitor['id'], silenced=module.params['silenced'])
        module.exit_json(changed=True, msg=msg)
    except Exception, e:
        module.fail_json(msg=str(e))


def unmute_monitor(module):
    monitor = _get_monitor(module)
    if not monitor:
         module.fail_json(msg="Monitor %s not found!" % module.params['name'])
    elif not monitor['options']['silenced']:
        module.exit_json(changed=False)
    try:
        msg = api.Monitor.unmute(monitor['id'])
        module.exit_json(changed=True, msg=msg)
    except Exception, e:
        module.fail_json(msg=str(e))


from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
main()
