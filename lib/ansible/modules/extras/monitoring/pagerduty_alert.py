#!/usr/bin/python
# -*- coding: utf-8 -*-
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

DOCUMENTATION = '''

module: pagerduty_alert
short_description: Trigger, acknowledge or resolve PagerDuty incidents
description:
    - This module will let you trigger, acknowledge or resolve a PagerDuty incident by sending events
version_added: "1.9"
author:
    - "Amanpreet Singh (@aps-sids)"
requirements:
    - PagerDuty API access
options:
    service_key:
        description:
            - The GUID of one of your "Generic API" services.
            - This is the "service key" listed on a Generic API's service detail page.
        required: true
    event_type:
        description:
            - Type of event to be sent.
        required: true
        choices:
            - 'trigger'
            - 'acknowledge'
            - 'resolve'
    desc:
        description:
            - For C(trigger) I(event_type) - Required. Short description of the problem that led to this trigger. This field (or a truncated version) will be used when generating phone calls, SMS messages and alert emails. It will also appear on the incidents tables in the PagerDuty UI. The maximum length is 1024 characters.
            - For C(acknowledge) or C(resolve) I(event_type) - Text that will appear in the incident's log associated with this event.
        required: false
        default: Created via Ansible
    incident_key:
        description:
            - Identifies the incident to which this I(event_type) should be applied.
            - For C(trigger) I(event_type) - If there's no open (i.e. unresolved) incident with this key, a new one will be created. If there's already an open incident with a matching key, this event will be appended to that incident's log. The event key provides an easy way to "de-dup" problem reports.
            - For C(acknowledge) or C(resolve) I(event_type) - This should be the incident_key you received back when the incident was first opened by a trigger event. Acknowledge events referencing resolved or nonexistent incidents will be discarded.
        required: false
    client:
        description:
        - The name of the monitoring client that is triggering this event.
        required: false
    client_url:
        description:
        -  The URL of the monitoring client that is triggering this event.
        required: false
'''

EXAMPLES = '''
# Trigger an incident with just the basic options
- pagerduty_alert:
        service_key=xxx
        event_type=trigger
        desc="problem that led to this trigger"

# Trigger an incident with more options
- pagerduty_alert:
        service_key=xxx
        event_type=trigger
        desc="problem that led to this trigger"
        incident_key=somekey
        client="Sample Monitoring Service"
        client_url=http://service.example.com

# Acknowledge an incident based on incident_key
- pagerduty_alert:
        service_key=xxx
        event_type=acknowledge
        incident_key=somekey
        desc="some text for incident's log"

# Resolve an incident based on incident_key
- pagerduty_alert:
        service_key=xxx
        event_type=resolve
        incident_key=somekey
        desc="some text for incident's log"
'''


def send_event(module, service_key, event_type, desc,
               incident_key=None, client=None, client_url=None):
    url = "https://events.pagerduty.com/generic/2010-04-15/create_event.json"
    headers = {
        "Content-type": "application/json"
    }

    data = {
        "service_key": service_key,
        "event_type": event_type,
        "incident_key": incident_key,
        "description": desc,
        "client": client,
        "client_url": client_url
    }

    response, info = fetch_url(module, url, method='post',
                               headers=headers, data=json.dumps(data))
    if info['status'] != 200:
        module.fail_json(msg="failed to %s. Reason: %s" %
                         (event_type, info['msg']))
    json_out = json.loads(response.read())
    return json_out, True


def main():
    module = AnsibleModule(
        argument_spec=dict(
            service_key=dict(required=True),
            event_type=dict(required=True,
                            choices=['trigger', 'acknowledge', 'resolve']),
            client=dict(required=False, default=None),
            client_url=dict(required=False, default=None),
            desc=dict(required=False, default='Created via Ansible'),
            incident_key=dict(required=False, default=None)
        )
    )

    service_key = module.params['service_key']
    event_type = module.params['event_type']
    client = module.params['client']
    client_url = module.params['client_url']
    desc = module.params['desc']
    incident_key = module.params['incident_key']

    if event_type != 'trigger' and incident_key is None:
        module.fail_json(msg="incident_key is required for "
                             "acknowledge or resolve events")

    out, changed = send_event(module, service_key, event_type, desc,
                              incident_key, client, client_url)

    module.exit_json(msg="success", result=out, changed=changed)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *

if __name__ == '__main__':
    main()
