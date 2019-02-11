#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''

module: pagerduty
short_description: Create PagerDuty maintenance windows
description:
    - This module will let you create PagerDuty maintenance windows
version_added: "1.2"
author:
    - "Andrew Newdigate (@suprememoocow)"
    - "Dylan Silva (@thaumos)"
    - "Justin Johns (!UNKNOWN)"
    - "Bruce Pennypacker (@bpennypacker)"
requirements:
    - PagerDuty API access
options:
    state:
        description:
            - Create a maintenance window or get a list of ongoing windows.
        required: true
        choices: [ "running", "started", "ongoing", "absent" ]
    name:
        description:
            - PagerDuty unique subdomain. Obsolete. It is not used with PagerDuty REST v2 API.
    user:
        description:
            - PagerDuty user ID. Obsolete. Please, use I(token) for authorization.
    token:
        description:
            - A pagerduty token, generated on the pagerduty site. It is used for authorization.
        required: true
        version_added: '1.8'
    requester_id:
        description:
            - ID of user making the request. Only needed when creating a maintenance_window.
        version_added: '1.8'
    service:
        description:
            - A comma separated list of PagerDuty service IDs.
        aliases: [ services ]
    window_id:
        description:
            - ID of maintenance window. Only needed when absent a maintenance_window.
        version_added: "2.7"
    hours:
        description:
            - Length of maintenance window in hours.
        default: 1
    minutes:
        description:
            - Maintenance window in minutes (this is added to the hours).
        default: 0
        version_added: '1.8'
    desc:
        description:
            - Short description of maintenance window.
        default: Created by Ansible
    validate_certs:
        description:
            - If C(no), SSL certificates will not be validated. This should only be used
              on personally controlled sites using self-signed certificates.
        type: bool
        default: 'yes'
        version_added: 1.5.1
'''

EXAMPLES = '''
# List ongoing maintenance windows using a token
- pagerduty:
    name: companyabc
    token: xxxxxxxxxxxxxx
    state: ongoing

# Create a 1 hour maintenance window for service FOO123
- pagerduty:
    name: companyabc
    user: example@example.com
    token: yourtoken
    state: running
    service: FOO123

# Create a 5 minute maintenance window for service FOO123
- pagerduty:
    name: companyabc
    token: xxxxxxxxxxxxxx
    hours: 0
    minutes: 5
    state: running
    service: FOO123


# Create a 4 hour maintenance window for service FOO123 with the description "deployment".
- pagerduty:
    name: companyabc
    user: example@example.com
    state: running
    service: FOO123
    hours: 4
    desc: deployment
  register: pd_window

# Delete the previous maintenance window
- pagerduty:
    name: companyabc
    user: example@example.com
    state: absent
    window_id: '{{ pd_window.result.maintenance_window.id }}'

# Delete a maintenance window from a separate playbook than its creation, and if it is the only existing maintenance window.
- pagerduty:
    requester_id: XXXXXXX
    token: yourtoken
    state: ongoing
  register: pd_window

- pagerduty:
    requester_id: XXXXXXX
    token: yourtoken
    state: absent
    window_id: "{{ pd_window.result.maintenance_windows[0].id }}"

'''

import datetime
import json
import base64

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_bytes


class PagerDutyRequest(object):
    def __init__(self, module, name, user, token):
        self.module = module
        self.name = name
        self.user = user
        self.token = token
        self.headers = {
            'Content-Type': 'application/json',
            "Authorization": self._auth_header(),
            'Accept': 'application/vnd.pagerduty+json;version=2'
        }

    def ongoing(self, http_call=fetch_url):
        url = "https://api.pagerduty.com/maintenance_windows?filter=ongoing"
        headers = dict(self.headers)

        response, info = http_call(self.module, url, headers=headers)
        if info['status'] != 200:
            self.module.fail_json(msg="failed to lookup the ongoing window: %s" % info['msg'])

        json_out = self._read_response(response)

        return False, json_out, False

    def create(self, requester_id, service, hours, minutes, desc, http_call=fetch_url):
        if not requester_id:
            self.module.fail_json(msg="requester_id is required when maintenance window should be created")

        url = 'https://api.pagerduty.com/maintenance_windows'

        headers = dict(self.headers)
        headers.update({'From': requester_id})

        start, end = self._compute_start_end_time(hours, minutes)
        services = self._create_services_payload(service)

        request_data = {'maintenance_window': {'start_time': start, 'end_time': end, 'description': desc, 'services': services}}

        data = json.dumps(request_data)
        response, info = http_call(self.module, url, data=data, headers=headers, method='POST')
        if info['status'] != 201:
            self.module.fail_json(msg="failed to create the window: %s" % info['msg'])

        json_out = self._read_response(response)

        return False, json_out, True

    def _create_services_payload(self, service):
        if (isinstance(service, list)):
            return [{'id': s, 'type': 'service_reference'} for s in service]
        else:
            return [{'id': service, 'type': 'service_reference'}]

    def _compute_start_end_time(self, hours, minutes):
        now = datetime.datetime.utcnow()
        later = now + datetime.timedelta(hours=int(hours), minutes=int(minutes))
        start = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        end = later.strftime("%Y-%m-%dT%H:%M:%SZ")
        return start, end

    def absent(self, window_id, http_call=fetch_url):
        url = "https://api.pagerduty.com/maintenance_windows/" + window_id
        headers = dict(self.headers)

        response, info = http_call(self.module, url, headers=headers, method='DELETE')
        if info['status'] != 204:
            self.module.fail_json(msg="failed to delete the window: %s" % info['msg'])

        json_out = self._read_response(response)

        return False, json_out, True

    def _auth_header(self):
        return "Token token=%s" % self.token

    def _read_response(self, response):
        try:
            return json.loads(response.read())
        except Exception:
            return ""


def main():

    module = AnsibleModule(
        argument_spec=dict(
            state=dict(required=True, choices=['running', 'started', 'ongoing', 'absent']),
            name=dict(required=False),
            user=dict(required=False),
            token=dict(required=True, no_log=True),
            service=dict(required=False, type='list', aliases=["services"]),
            window_id=dict(required=False),
            requester_id=dict(required=False),
            hours=dict(default='1', required=False),
            minutes=dict(default='0', required=False),
            desc=dict(default='Created by Ansible', required=False),
            validate_certs=dict(default='yes', type='bool'),
        )
    )

    state = module.params['state']
    name = module.params['name']
    user = module.params['user']
    service = module.params['service']
    window_id = module.params['window_id']
    hours = module.params['hours']
    minutes = module.params['minutes']
    token = module.params['token']
    desc = module.params['desc']
    requester_id = module.params['requester_id']

    pd = PagerDutyRequest(module, name, user, token)

    if state == "running" or state == "started":
        if not service:
            module.fail_json(msg="service not specified")
        (rc, out, changed) = pd.create(requester_id, service, hours, minutes, desc)
        if rc == 0:
            changed = True

    if state == "ongoing":
        (rc, out, changed) = pd.ongoing()

    if state == "absent":
        (rc, out, changed) = pd.absent(window_id)

    if rc != 0:
        module.fail_json(msg="failed", result=out)

    module.exit_json(msg="success", result=out, changed=changed)


if __name__ == '__main__':
    main()
