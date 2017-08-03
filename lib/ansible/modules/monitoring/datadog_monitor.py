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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: datadog_monitor
short_description: Manages Datadog monitors
description:
- "Manages monitors within Datadog"
- "Options like described on http://docs.datadoghq.com/api/"
version_added: "2.0"
author: "Sebastian Kornehl (@skornehl)"
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
    tags:
        description: ["A list of tags to associate with your monitor when creating or updating. This can help you categorize and filter monitors."]
        required: false
        default: None
        version_added: "2.2"
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
        description:
            - A message to include with notifications for this monitor. Email notifications can be sent to specific users by using the same
              '@username' notation as events. Monitor message template variables can be accessed by using double square brackets, i.e '[[' and ']]'.
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
        description:
            - The number of minutes before a monitor will notify when data stops reporting. Must be at least 2x the monitor timeframe for metric
              alerts or 2 minutes for service checks.
        required: false
        default: 2x timeframe for metric, 2 minutes for service
    timeout_h:
        description: ["The number of hours of the monitor not reporting data before it will automatically resolve from a triggered state."]
        required: false
        default: null
    renotify_interval:
        description:
            - The number of minutes after the last notification before a monitor will re-notify on the current status. It will only re-notify if it's
              not resolved.
        required: false
        default: null
    escalation_message:
        description:
            - A message to include with a re-notification. Supports the '@username' notification we allow elsewhere. Not applicable if renotify_interval
              is None
        required: false
        default: null
    notify_audit:
        description: ["A boolean indicating whether tagged users will be notified on changes to this monitor."]
        required: false
        default: False
    thresholds:
        description:
            - A dictionary of thresholds by status. This option is only available for service checks and metric alerts. Because each of them can have
              multiple thresholds, we don't define them directly in the query."]
        required: false
        default: {'ok': 1, 'critical': 1, 'warning': 1}
    locked:
        description: ["A boolean indicating whether changes to this monitor should be restricted to the creator or admins."]
        required: false
        default: False
        version_added: "2.2"
    require_full_window:
        description:
            - A boolean indicating whether this monitor needs a full window of data before it's evaluated. We highly recommend you set this to False for
              sparse metrics, otherwise some evaluations will be skipped.
        required: false
        default: null
        version_added: "2.3"
    new_host_delay:
        description: ["A positive integer representing the number of seconds to wait before evaluating the monitor for new hosts.
        This gives the host time to fully initialize."]
        required: false
        default: null
        version_added: "2.4"
    id:
        description: ["The id of the alert. If set, will be used instead of the name to locate the alert."]
        required: false
        default: null
        version_added: "2.3"
'''

EXAMPLES = '''
# Create a metric monitor
datadog_monitor:
  type: "metric alert"
  name: "Test monitor"
  state: "present"
  query: "datadog.agent.up.over('host:host1').last(2).count_by_status()"
  message: "Host [[host.name]] with IP [[host.ip]] is failing to report to datadog."
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

# Import Datadog
try:
    from datadog import initialize, api
    HAS_DATADOG = True
except:
    HAS_DATADOG = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception


def main():
    module = AnsibleModule(
        argument_spec=dict(
            api_key=dict(required=True, no_log=True),
            app_key=dict(required=True, no_log=True),
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
            thresholds=dict(required=False, type='dict', default=None),
            tags=dict(required=False, type='list', default=None),
            locked=dict(required=False, default=False, type='bool'),
            require_full_window=dict(required=False, default=None, type='bool'),
            new_host_delay=dict(required=False, default=None),
            id=dict(required=False)
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

    # Check if api_key and app_key is correct or not
    # if not, then fail here.
    response = api.Monitor.get_all()
    if isinstance(response, dict):
        msg = response.get('errors', None)
        if msg:
            module.fail_json(msg="Failed to connect Datadog server using given app_key and api_key : {0}".format(msg[0]))

    if module.params['state'] == 'present':
        install_monitor(module)
    elif module.params['state'] == 'absent':
        delete_monitor(module)
    elif module.params['state'] == 'mute':
        mute_monitor(module)
    elif module.params['state'] == 'unmute':
        unmute_monitor(module)


def _fix_template_vars(message):
    if message:
        return message.replace('[[', '{{').replace(']]', '}}')
    return message


def _get_monitor(module):
    if module.params['id'] is not None:
        monitor = api.Monitor.get(module.params['id'])
        if 'errors' in monitor:
            module.fail_json(msg="Failed to retrieve monitor with id %s, errors are %s" % (module.params['id'], str(monitor['errors'])))
        return monitor
    else:
        monitors = api.Monitor.get_all()
        for monitor in monitors:
            if monitor['name'] == module.params['name']:
                return monitor
    return {}


def _post_monitor(module, options):
    try:
        kwargs = dict(type=module.params['type'], query=module.params['query'],
                      name=module.params['name'], message=_fix_template_vars(module.params['message']),
                      options=options)
        if module.params['tags'] is not None:
            kwargs['tags'] = module.params['tags']
        msg = api.Monitor.create(**kwargs)
        if 'errors' in msg:
            module.fail_json(msg=str(msg['errors']))
        else:
            module.exit_json(changed=True, msg=msg)
    except Exception:
        e = get_exception()
        module.fail_json(msg=str(e))


def _equal_dicts(a, b, ignore_keys):
    ka = set(a).difference(ignore_keys)
    kb = set(b).difference(ignore_keys)
    return ka == kb and all(a[k] == b[k] for k in ka)


def _update_monitor(module, monitor, options):
    try:
        kwargs = dict(id=monitor['id'], query=module.params['query'],
                      name=module.params['name'], message=_fix_template_vars(module.params['message']),
                      options=options)
        if module.params['tags'] is not None:
            kwargs['tags'] = module.params['tags']
        msg = api.Monitor.update(**kwargs)

        if 'errors' in msg:
            module.fail_json(msg=str(msg['errors']))
        elif _equal_dicts(msg, monitor, ['creator', 'overall_state', 'modified', 'matching_downtimes', 'overall_state_modified']):
            module.exit_json(changed=False, msg=msg)
        else:
            module.exit_json(changed=True, msg=msg)
    except Exception:
        e = get_exception()
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
        "locked": module.boolean(module.params['locked']),
        "require_full_window": module.params['require_full_window'],
        "new_host_delay": module.params['new_host_delay']
    }

    if module.params['type'] == "service check":
        options["thresholds"] = module.params['thresholds'] or {'ok': 1, 'critical': 1, 'warning': 1}
    if module.params['type'] == "metric alert" and module.params['thresholds'] is not None:
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
    except Exception:
        e = get_exception()
        module.fail_json(msg=str(e))


def mute_monitor(module):
    monitor = _get_monitor(module)
    if not monitor:
        module.fail_json(msg="Monitor %s not found!" % module.params['name'])
    elif monitor['options']['silenced']:
        module.fail_json(msg="Monitor is already muted. Datadog does not allow to modify muted alerts, consider unmuting it first.")
    elif (module.params['silenced'] is not None and len(set(monitor['options']['silenced']) - set(module.params['silenced'])) == 0):
        module.exit_json(changed=False)
    try:
        if module.params['silenced'] is None or module.params['silenced'] == "":
            msg = api.Monitor.mute(id=monitor['id'])
        else:
            msg = api.Monitor.mute(id=monitor['id'], silenced=module.params['silenced'])
        module.exit_json(changed=True, msg=msg)
    except Exception:
        e = get_exception()
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
    except Exception:
        e = get_exception()
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
