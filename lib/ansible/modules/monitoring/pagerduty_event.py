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
---
module: pagerduty_event

short_description: Trigger, acknowledge or resolve PagerDuty incidents via Events API

description:
    - This module will let you trigger, acknowledge or resolve a PagerDuty incident by sending events to PagerDuty Events API.
    - Supports both PagerDuty Events API v1 and v2. PagerDuty Events API v2 is recommended.
    - See U(https://v2.developer.pagerduty.com/docs/trigger-events) for PagerDuty Events API v1 overview.
    - See U(https://v2.developer.pagerduty.com/docs/send-an-event-events-api-v2) for PagerDuty Events API v2 overview.

version_added: "2.7"

author:
    - "Stephen Barry (@TheMonolithX64)"
requirements:
    - PagerDuty integration key
options:
    routing_key:
        description:
            - The GUID of one of your "Events API v2" integrations.
            - This is the "Integration Key" listed on the Events API V2 integration's detail page.
        required: true
        aliases: [ service_key ]
    state:
        description:
            - Type of event to be sent.
        required: true
        choices:
            - 'triggered'
            - 'acknowledged'
            - 'resolved'
    desc:
        description:
            - A brief text summary of the event, used to generate the summaries/titles of any associated alerts.
            - Required when C(state=triggered).
        required: false
        default: 'Created by Ansible'
    api_version:
        description:
            - PagerDuty Events API version to execute against.
        required: false
        choices:
            - 'v1'
            - 'v2'
        default: 'v2'
    source:
        description:
            - The unique location of the affected system, preferably a hostname or FQDN.
            - Required when C(state=triggered).
            - An Ansible fact or registered variable is a good option for this value to identify the remote host and executor.
            - For example - C(ansible_hostname) or C(ansible_eth0.ipv4.address).
        required: false
        default: 'Ansible'
    severity:
        description:
            - The perceived severity of the status the event is describing with respect to the affected system.
            - Required when C(state=triggered).
        required: false
        choices:
            - 'critical'
            - 'error'
            - 'warning'
            - 'info'
        default: info
    dedup_key:
        description:
            - Identifies the incident to which this I(state) should be applied.
            - If omitted, it will be generated automatically by PagerDuty and returned in the Events API v2 response.
            - For C(state=triggered) - If there's no open (i.e. unresolved) incident with this key, a new one will be created. If there's already an
              open incident with a matching key, this event will be appended to that incident's log. The event key provides an easy way to "de-dup"
              problem reports.
            - For C(state=acknowledged) or C(state=resolved) - This should be the incident_key you received back when the incident was first opened by a
              trigger event. Acknowledge events referencing resolved or nonexistent incidents will be discarded.
            - A MD5, SHA1, SHA512 or any string is a good option for this value.
            - Maximum permitted length of this property is I(255 characters).
        required: false
        aliases: [ incident_key ]
    component:
        description: Component of the source machine that is responsible for the event, for example C(mysql) or C(eth0).
        required: false
    group:
        description: Logical grouping of components of a service, for example C(app-stack).
        required: false
    class_type:
        description: The class/type of the event, for example C(ping failure) or C(cpu load).
        required: false
    client:
        description:
        - The name of the monitoring client that is triggering this event.
        required: false
    client_url:
        description:
        -  The URL of the monitoring client that is triggering this event.
        required: false
    custom_details:
        description:
            - Additional details about the event and affected system.
            - key, value pairs of data to load into the incident.
        required: false
        aliases: [ details ]
'''

EXAMPLES = '''
# Trigger an incident with just the basic options
- pagerduty_incident:
    routing_key: xxx
    state: triggered
    severity: warning
    desc: problem that led to this trigger
    source: host.example.com
  register: new_incident

# Print incident key generated by PagerDuty API v2
- debug:
    # For Events API v1 use: "{{ new_incident['response']['incident_key'] }}"
    msg: "{{ new_incident['response']['dedup_key'] }}"

# Trigger an incident with more options
- pagerduty_incident:
    routing_key: xxx
    state: triggered
    severity: critical
    desc: problem that led to this trigger
    dedup_key: "{{ 'zzz' | hash('md5') }}"
    source: "{{ ansible_hostname }}"
    client: Sample Monitoring Service
    client_url: http://service.example.com
    custom_details:
      ping_time: "1500ms"
      load_avg: "0.75"

# Acknowledge an incident based on incident_key
- pagerduty_incident:
    routing_key: xxx
    state: acknowledged
    dedup_key: somekey

# Resolve an incident based on incident_key
- pagerduty_incident:
    routing_key: xxx
    state: resolved
    dedup_key: somekey
'''

RETURN = '''
api_version:
    description: PagerDuty Event API version.
    returned: changed
    type: string
payload:
    description: Output JSON payload provided to module.
    returned: changed
    type: dict
status:
    description: Output HTTP status code.
    returned: success
    type: string
response:
    description: Output HTTP response body.
    returned: success
    type: complex
    contains:
        message:
            description: Response message.
            type: string
            returned: success
            sample:
                - "Event processed"
        status:
            description: Response status code.
            type: string
            returned: success
            sample:
                - "202"
        dedup_key:
            description: Response incident key - Events API v1 returns C(incident_key) and v2 returns C(dedup_key).
            type: string
            returned: success
            sample:
                - "somekey"
'''
import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url


def run_module():
    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = dict(
        routing_key=dict(type='str', required=True, aliases=['service_key']),
        state=dict(type='str', required=True,
                   choices=['triggered', 'acknowledged', 'resolved']),
        api_version=dict(type='str', required=False, default='v2',
                    choices=['v1', 'v2']),
        desc=dict(type='str', required=False, default='Created by Ansible'),
        source=dict(type='str', required=False, default='Ansible'),
        severity=dict(type='str', required=False, default='info',
                      choices=['critical', 'error', 'warning', 'info']),
        dedup_key=dict(type='str', required=False, default=None, aliases=['incident_key']),
        component=dict(type='str', required=False, default=None),
        group=dict(type='str', required=False, default=None),
        class_type=dict(type='str', required=False, default=None),
        client=dict(type='str', required=False, default=None),
        client_url=dict(type='str', required=False, default=None),
        custom_details=dict(type='dict', required=False, default=None, aliases=['details'])
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        payload='',
        status='',
        msg='',
        response=''
    )

    # the Ansible module object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    params = module.params
    routing_key = params['routing_key']
    state = params['state']
    api_version = params['api_version']
    desc = params['desc']
    source = params['source']
    severity = params['severity']
    dedup_key = params['dedup_key']
    component = params['component']
    group = params['group']
    class_type = params['class_type']
    client = params['client']
    client_url = params['client_url']
    custom_details = params['custom_details']

    state_action_dict = {
        'triggered': 'trigger',
        'acknowledged': 'acknowledge',
        'resolved': 'resolve'
    }

    event_action = state_action_dict[state]

    if event_action != 'trigger' and dedup_key is None:
        module.fail_json(msg="dedup_key is required for "
                             "acknowledge or resolve events")

    if api_version == 'v1':
       url = "https://events.pagerduty.com/generic/2010-04-15/create_event.json"
       headers = {
           "Accept": "application/vnd.pagerduty+json;version=2",
           "Content-type": "application/json"
       }
    else:
        url = "https://events.pagerduty.com/v2/enqueue"
        headers = {
            "Accept": "application/vnd.pagerduty+json;version=2",
            "Content-type": "application/json"
        }

    # Truncate dedup_key if greater than 255 characters
    if dedup_key and len(dedup_key) >= 255:
        dedup_key = dedup_key[:255]

    # Prepare the payload for JSON body for Events API v1
    if api_version == 'v1':
        data = {
            "service_key": routing_key,
            "event_type": event_action,
            "incident_key": dedup_key,
            "description": desc,
            "client": client,
            "client_url": client_url,
            "details": custom_details
        }
    # Prepare the payload for JSON body for Events API v2
    else:
        data = {
            "routing_key": routing_key,
            "event_action": event_action,
            "dedup_key": dedup_key,
            "client": client,
            "client_url": client_url,
            "payload": {
                "summary": desc,
                "source": source,
                "severity": severity,
                "component": component,
                "group": group,
                "class": class_type,
                "custom_details": custom_details
            }
        }

    # Deal with check mode
    if module.check_mode:
        result['api_version'] = api_version
        result['payload'] = dict(data)
        result['changed'] = True
        module.exit_json(**result)

    # Now for the real thing: (non-check mode)
    response, info = fetch_url(module, url, method='post',
                               headers=headers, data=json.dumps(data))

    if response is not None:
        body = json.loads(response.read())

    # Handle v1 API response
    if api_version == 'v1':
        if info['status'] != 200:
            if info['status'] == 403:
                module.fail_json(msg="failed to {0}. Reason: {1}"
                                 .format(event_action, '403 Rate Limited'),
                                 url=url, headers=headers, data=json.dumps(data))
            else:
                module.fail_json(msg="failed to {0}. Reason: {1} Body: {2}"
                                 .format(event_action, info['msg'], info['body']),
                                 url=url, headers=headers, data=json.dumps(data))
    # Handle v2 API response
    if api_version == 'v2':
        if info['status'] != 202:
            if info['status'] == 429:
                module.fail_json(msg="failed to {0}. Reason: {1}"
                                 .format(event_action, '429 Too Many Requests'),
                                 url=url, headers=headers, data=json.dumps(data))
            else:
                module.fail_json(msg="failed to {0}. Reason: {1} Body: {2}"
                                 .format(event_action, info['msg'], info['body']),
                                 url=url, headers=headers, data=json.dumps(data))

    result['api_version'] = api_version
    result['payload'] = dict(data)
    result['status'] = info['status']
    result['response'] = dict(body)
    module.exit_json(**result)


def main():
    run_module()

if __name__ == '__main__':
    main()
