#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Sebastian Kornehl <sebastian.kornehl@asideas.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: datadog_monitor
short_description: Manages Datadog monitors
description:
  - Manages monitors within Datadog.
  - Options as described on https://docs.datadoghq.com/api/.
version_added: "2.0"
author: Sebastian Kornehl (@skornehl)
requirements: [datadog]
options:
    api_key:
        description:
          - Your Datadog API key.
        required: true
        type: str
    app_key:
        description:
          - Your Datadog app key.
        required: true
        type: str
    state:
        description:
          - The designated state of the monitor.
        required: true
        choices: ['present', 'absent', 'mute', 'unmute']
        type: str
    tags:
        description:
          - A list of tags to associate with your monitor when creating or updating.
          - This can help you categorize and filter monitors.
        version_added: "2.2"
        type: list
    type:
        description:
          - The type of the monitor.
        choices: ['metric alert', 'service check', 'event alert']
        type: str
    query:
        description:
          - The monitor query to notify on.
          - Syntax varies depending on what type of monitor you are creating.
        type: str
    name:
        description:
          - The name of the alert.
        required: true
        type: str
    message:
        description:
          - A message to include with notifications for this monitor.
          - Email notifications can be sent to specific users by using the same '@username' notation as events.
          - Monitor message template variables can be accessed by using double square brackets, i.e '[[' and ']]'.
        type: str
    silenced:
        description:
          - Dictionary of scopes to silence, with timestamps or None.
          - Each scope will be muted until the given POSIX timestamp or forever if the value is None.
        default: ""
    notify_no_data:
        description:
          - Whether this monitor will notify when data stops reporting.
        type: bool
        default: 'no'
    no_data_timeframe:
        description:
          - The number of minutes before a monitor will notify when data stops reporting.
          - Must be at least 2x the monitor timeframe for metric alerts or 2 minutes for service checks.
        default: 2x timeframe for metric, 2 minutes for service
        type: str
    timeout_h:
        description:
          - The number of hours of the monitor not reporting data before it will automatically resolve from a triggered state.
        type: str
    renotify_interval:
        description:
          - The number of minutes after the last notification before a monitor will re-notify on the current status.
          - It will only re-notify if it is not resolved.
        type: str
    escalation_message:
        description:
          - A message to include with a re-notification. Supports the '@username' notification we allow elsewhere.
          - Not applicable if I(renotify_interval=None).
        type: str
    notify_audit:
        description:
          - Whether tagged users will be notified on changes to this monitor.
        type: bool
        default: 'no'
    thresholds:
        description:
          - A dictionary of thresholds by status.
          - Only available for service checks and metric alerts.
          - Because each of them can have multiple thresholds, we do not define them directly in the query.
        default: {'ok': 1, 'critical': 1, 'warning': 1}
    locked:
        description:
          - Whether changes to this monitor should be restricted to the creator or admins.
        type: bool
        default: 'no'
        version_added: "2.2"
    require_full_window:
        description:
          - Whether this monitor needs a full window of data before it gets evaluated.
          - We highly recommend you set this to False for sparse metrics, otherwise some evaluations will be skipped.
        version_added: "2.3"
        type: bool
    new_host_delay:
        description:
          - A positive integer representing the number of seconds to wait before evaluating the monitor for new hosts.
          - This gives the host time to fully initialize.
        version_added: "2.4"
        type: str
    evaluation_delay:
        description:
          - Time to delay evaluation (in seconds).
          - Effective for sparse values.
        version_added: "2.7"
        type: str
    id:
        description:
          - The ID of the alert.
          - If set, will be used instead of the name to locate the alert.
        version_added: "2.3"
        type: str
'''

EXAMPLES = '''
# Create a metric monitor
- datadog_monitor:
    type: "metric alert"
    name: "Test monitor"
    state: "present"
    query: "datadog.agent.up.over('host:host1').last(2).count_by_status()"
    message: "Host [[host.name]] with IP [[host.ip]] is failing to report to datadog."
    api_key: "9775a026f1ca7d1c6c5af9d94d9595a4"
    app_key: "87ce4a24b5553d2e482ea8a8500e71b8ad4554ff"

# Deletes a monitor
- datadog_monitor:
    name: "Test monitor"
    state: "absent"
    api_key: "9775a026f1ca7d1c6c5af9d94d9595a4"
    app_key: "87ce4a24b5553d2e482ea8a8500e71b8ad4554ff"

# Mutes a monitor
- datadog_monitor:
    name: "Test monitor"
    state: "mute"
    silenced: '{"*":None}'
    api_key: "9775a026f1ca7d1c6c5af9d94d9595a4"
    app_key: "87ce4a24b5553d2e482ea8a8500e71b8ad4554ff"

# Unmutes a monitor
- datadog_monitor:
    name: "Test monitor"
    state: "unmute"
    api_key: "9775a026f1ca7d1c6c5af9d94d9595a4"
    app_key: "87ce4a24b5553d2e482ea8a8500e71b8ad4554ff"
'''
import traceback

# Import Datadog
DATADOG_IMP_ERR = None
try:
    from datadog import initialize, api
    HAS_DATADOG = True
except Exception:
    DATADOG_IMP_ERR = traceback.format_exc()
    HAS_DATADOG = False

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils._text import to_native


def main():
    module = AnsibleModule(
        argument_spec=dict(
            api_key=dict(required=True, no_log=True),
            app_key=dict(required=True, no_log=True),
            state=dict(required=True, choices=['present', 'absent', 'mute', 'unmute']),
            type=dict(required=False, choices=['metric alert', 'service check', 'event alert']),
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
            evaluation_delay=dict(required=False, default=None),
            id=dict(required=False)
        )
    )

    # Prepare Datadog
    if not HAS_DATADOG:
        module.fail_json(msg=missing_required_lib('datadogpy'), exception=DATADOG_IMP_ERR)

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
            if monitor['name'] == _fix_template_vars(module.params['name']):
                return monitor
    return {}


def _post_monitor(module, options):
    try:
        kwargs = dict(type=module.params['type'], query=module.params['query'],
                      name=_fix_template_vars(module.params['name']),
                      message=_fix_template_vars(module.params['message']),
                      escalation_message=_fix_template_vars(module.params['escalation_message']),
                      options=options)
        if module.params['tags'] is not None:
            kwargs['tags'] = module.params['tags']
        msg = api.Monitor.create(**kwargs)
        if 'errors' in msg:
            module.fail_json(msg=str(msg['errors']))
        else:
            module.exit_json(changed=True, msg=msg)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())


def _equal_dicts(a, b, ignore_keys):
    ka = set(a).difference(ignore_keys)
    kb = set(b).difference(ignore_keys)
    return ka == kb and all(a[k] == b[k] for k in ka)


def _update_monitor(module, monitor, options):
    try:
        kwargs = dict(id=monitor['id'], query=module.params['query'],
                      name=_fix_template_vars(module.params['name']),
                      message=_fix_template_vars(module.params['message']),
                      escalation_message=_fix_template_vars(module.params['escalation_message']),
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
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())


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
        "new_host_delay": module.params['new_host_delay'],
        "evaluation_delay": module.params['evaluation_delay']
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
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())


def mute_monitor(module):
    monitor = _get_monitor(module)
    if not monitor:
        module.fail_json(msg="Monitor %s not found!" % module.params['name'])
    elif monitor['options']['silenced']:
        module.fail_json(msg="Monitor is already muted. Datadog does not allow to modify muted alerts, consider unmuting it first.")
    elif (module.params['silenced'] is not None and len(set(monitor['options']['silenced']) ^ set(module.params['silenced'])) == 0):
        module.exit_json(changed=False)
    try:
        if module.params['silenced'] is None or module.params['silenced'] == "":
            msg = api.Monitor.mute(id=monitor['id'])
        else:
            msg = api.Monitor.mute(id=monitor['id'], silenced=module.params['silenced'])
        module.exit_json(changed=True, msg=msg)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())


def unmute_monitor(module):
    monitor = _get_monitor(module)
    if not monitor:
        module.fail_json(msg="Monitor %s not found!" % module.params['name'])
    elif not monitor['options']['silenced']:
        module.exit_json(changed=False)
    try:
        msg = api.Monitor.unmute(monitor['id'])
        module.exit_json(changed=True, msg=msg)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
