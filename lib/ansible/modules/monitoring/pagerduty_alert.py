#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''

module: pagerduty_alert
short_description: Trigger, acknowledge or resolve PagerDuty incidents
description:
    - This module will let you trigger, acknowledge or resolve a PagerDuty incident by sending events
version_added: "1.9"
author:
    - "Amanpreet Singh (@ApsOps)"
requirements:
    - PagerDuty API access
options:
    name:
        description:
            - PagerDuty unique subdomain. Obsolete. It is not used with PagerDuty REST v2 API.
    service_id:
        description:
            - ID of PagerDuty service when incidents will be triggered, acknowledged or resolved.
        required: true
        version_added: "2.7"
    service_key:
        description:
            - The GUID of one of your "Generic API" services. Obsolete. Please use I(integration_key).
    integration_key:
        description:
            - The GUID of one of your "Generic API" services.
            - This is the "integration key" listed on a "Integrations" tab of PagerDuty service.
        required: true
        version_added: "2.7"
    state:
        description:
            - Type of event to be sent.
        required: true
        choices:
            - 'triggered'
            - 'acknowledged'
            - 'resolved'
    api_key:
        description:
            - The pagerduty API key (readonly access), generated on the pagerduty site.
        required: true
    desc:
        description:
            - For C(triggered) I(state) - Required. Short description of the problem that led to this trigger. This field (or a truncated version)
              will be used when generating phone calls, SMS messages and alert emails. It will also appear on the incidents tables in the PagerDuty UI.
              The maximum length is 1024 characters.
            - For C(acknowledged) or C(resolved) I(state) - Text that will appear in the incident's log associated with this event.
        required: false
        default: Created via Ansible
    incident_key:
        description:
            - Identifies the incident to which this I(state) should be applied.
            - For C(triggered) I(state) - If there's no open (i.e. unresolved) incident with this key, a new one will be created. If there's already an
              open incident with a matching key, this event will be appended to that incident's log. The event key provides an easy way to "de-dup"
              problem reports.
            - For C(acknowledged) or C(resolved) I(state) - This should be the incident_key you received back when the incident was first opened by a
              trigger event. Acknowledge events referencing resolved or nonexistent incidents will be discarded.
        required: false
        version_added: "2.7"
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
    name: companyabc
    integration_key: xxx
    api_key: yourapikey
    service_id: PDservice
    state: triggered
    desc: problem that led to this trigger

# Trigger an incident with more options
- pagerduty_alert:
    integration_key: xxx
    api_key: yourapikey
    service_id: PDservice
    state: triggered
    desc: problem that led to this trigger
    incident_key: somekey
    client: Sample Monitoring Service
    client_url: http://service.example.com

# Acknowledge an incident based on incident_key
- pagerduty_alert:
    integration_key: xxx
    api_key: yourapikey
    service_id: PDservice
    state: acknowledged
    incident_key: somekey
    desc: "some text for incident's log"

# Resolve an incident based on incident_key
- pagerduty_alert:
    integration_key: xxx
    api_key: yourapikey
    service_id: PDservice
    state: resolved
    incident_key: somekey
    desc: "some text for incident's log"
'''
import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url
from ansible.module_utils.six.moves.urllib.parse import urlparse, urlencode, urlunparse


def check(module, name, state, service_id, integration_key, api_key, incident_key=None, http_call=fetch_url):
    url = 'https://api.pagerduty.com/incidents'
    headers = {
        "Content-type": "application/json",
        "Authorization": "Token token=%s" % api_key,
        'Accept': 'application/vnd.pagerduty+json;version=2'
    }

    params = {
        'service_ids[]': service_id,
        'sort_by': 'incident_number:desc',
        'time_zone': 'UTC'
    }
    if incident_key:
        params['incident_key'] = incident_key

    url_parts = list(urlparse(url))
    url_parts[4] = urlencode(params, True)

    url = urlunparse(url_parts)

    response, info = http_call(module, url, method='get', headers=headers)

    if info['status'] != 200:
        module.fail_json(msg="failed to check current incident status."
                             "Reason: %s" % info['msg'])
    json_out = json.loads(response.read())["incidents"][0]

    if state != json_out["status"]:
        return json_out, True
    return json_out, False


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
    return json_out


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=False),
            service_id=dict(required=True),
            service_key=dict(required=False, no_log=True),
            integration_key=dict(required=False, no_log=True),
            api_key=dict(required=True, no_log=True),
            state=dict(required=True,
                       choices=['triggered', 'acknowledged', 'resolved']),
            client=dict(required=False, default=None),
            client_url=dict(required=False, default=None),
            desc=dict(required=False, default='Created via Ansible'),
            incident_key=dict(required=False, default=None)
        ),
        supports_check_mode=True
    )

    name = module.params['name']
    service_id = module.params['service_id']
    integration_key = module.params['integration_key']
    service_key = module.params['service_key']
    api_key = module.params['api_key']
    state = module.params['state']
    client = module.params['client']
    client_url = module.params['client_url']
    desc = module.params['desc']
    incident_key = module.params['incident_key']

    if integration_key is None:
        if service_key is not None:
            integration_key = service_key
            module.warn('"service_key" is obsolete parameter and will be removed.'
                        ' Please, use "integration_key" instead')
        else:
            module.fail_json(msg="'integration_key' is required parameter")

    state_event_dict = {
        'triggered': 'trigger',
        'acknowledged': 'acknowledge',
        'resolved': 'resolve'
    }

    event_type = state_event_dict[state]

    if event_type != 'trigger' and incident_key is None:
        module.fail_json(msg="incident_key is required for "
                             "acknowledge or resolve events")

    out, changed = check(module, name, state, service_id,
                         integration_key, api_key, incident_key)

    if not module.check_mode and changed is True:
        out = send_event(module, integration_key, event_type, desc,
                         incident_key, client, client_url)

    module.exit_json(result=out, changed=changed)


if __name__ == '__main__':
    main()
