#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Tomasz Nowodzinski <tomasz.nowodzinski@gmail.com>
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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: datadog_downtime
short_description: Manages Datadog downtimes
description:
- "Manages downtimes within Datadog"
- "Options like described on http://docs.datadoghq.com/api/"
- "Downtimes API Reference - http://docs.datadoghq.com/api/?lang=python#downtimes"
version_added: "2.3"
author: "Tomasz Nowodzinski (@dzinek)"
requirements: [datadog]
options:
    api_key:
        description: ["Your DataDog API key."]
        required: true
    app_key:
        description: ["Your DataDog app key."]
        required: true
    state:
        description: ["The designated state of the downtime."]
        required: true
        choices: ['scheduled', 'canceled']
    message:
        description: ["A message to include with notifications for this downtime. Email notifications can be sent to specific users by using the same '@username' notation as events. Downtime message template variables can be accessed by using double square brackets, i.e '[[' and ']]'."]
        required: false
        default: null
    scope:
        description: ["The scope to apply the downtime to, e.g. 'host:app2'."]
        required: true
    start:
        description: ["POSIX timestamp to start the downtime. In the default case, the downtime will start immediately."]
        required: false
        default: null
    end:
        description: ["POSIX timestamp to end the downtime. In the default case, the downtime will go until cancelled."]
        required: false
        default: null
    id:
        description: ["The id of the downtime to be updated or deleted."]
        required: false
        default: null
'''

EXAMPLES = '''
# Schedule a monitor downtime
- datadog_downtime:
    state: "scheduled"
    message: "Scheduled downtime on [[environment]] - deploying version [[version]]. End after 3h."
    scope: "env:staging"
    start: "{{ansible_date_time.epoch}}"
    end: "{{ansible_date_time.epoch|int+(3*60*60)}}"
    api_key: "9775a026f1ca7d1c6c5af9d94d9595a4"
    app_key: "87ce4a24b5553d2e482ea8a8500e71b8ad4554ff"
register: output

# Update a scheduled monitor downtime
- datadog_downtime:
    id: 1223
    state: "scheduled"
    message: "Scheduled downtime on [[environment]] - deploying version [[version]]. End after 4h."
    scope: "env:staging"
    start: "{{ansible_date_time.epoch}}"
    end: "{{ansible_date_time.epoch|int+(4*60*60)}}"
    api_key: "9775a026f1ca7d1c6c5af9d94d9595a4"
    app_key: "87ce4a24b5553d2e482ea8a8500e71b8ad4554ff"

# Deletes a scheduled monitor downtime
- datadog_downtime:
    id: "{{output.msg.id}}"
    state: "canceled"
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
            state=dict(required=True, choises=['scheduled', 'canceled']),
            message=dict(required=False, default=None),
            scope=dict(required=True),
            start=dict(required=False, default=None, type='int'),
            end=dict(required=False, default=None, type='int'),
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

    if module.params['state'] == 'scheduled':
        schedule_downtime(module)
    elif module.params['state'] == 'canceled':
        cancel_downtime(module)

def _fix_template_vars(message):
    if message:
        return message.replace('[[', '{{').replace(']]', '}}')
    return message

def _get_downtime(module):
    if module.params['id'] is not None:
        downtime = api.Downtime.get(module.params['id'])
        if 'errors' in downtime:
            module.fail_json(msg="Failed to retrieve downtime with id %s, errors are %s" % (module.params['id'], str(downtime['errors'])))
        return downtime
    return {}

def _post_downtime(module):
    try:
        kwargs = dict(message=_fix_template_vars(module.params['message']), scope=module.params['scope'],
            start=module.params['start'], end=module.params['end'])
        msg=api.Downtime.create(**kwargs)
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

def _update_downtime(module, downtime):
    try:
        kwargs = dict(id=downtime['id'], message=_fix_template_vars(module.params['message']),
                      scope=module.params['scope'], start=module.params['start'], end=module.params['end'])
        msg=api.Downtime.update(**kwargs)
        if 'errors' in msg:
            module.fail_json(msg=str(msg['errors']))
        elif _equal_dicts(msg, downtime, ['creator_id', 'updater_id']):
            module.exit_json(changed=False, msg=msg)
        else:
            module.exit_json(changed=True, msg=msg)
    except Exception:
        e = get_exception()
        module.fail_json(msg=str(e))

def schedule_downtime(module):
    downtime = _get_downtime(module)
    if not downtime:
        _post_downtime(module)
    else:
        _update_downtime(module, downtime)

def cancel_downtime(module):
    downtime = _get_downtime(module)
    if not downtime:
        module.exit_json(changed=False)
    try:
        msg = api.Downtime.delete(downtime['id'])
        module.exit_json(changed=True, msg=msg)
    except Exception:
        e = get_exception()
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
