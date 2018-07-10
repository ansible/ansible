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
    - "Justin Johns"
    - "Bruce Pennypacker"
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
            - PagerDuty unique subdomain.
        required: true
    user:
        description:
            - PagerDuty user ID.
        required: true
    passwd:
        description:
            - PagerDuty user password.
        required: true
    token:
        description:
            - A pagerduty token, generated on the pagerduty site. Can be used instead of
              user/passwd combination.
        required: true
        version_added: '1.8'
    requester_id:
        description:
            - ID of user making the request. Only needed when using a token and creating a maintenance_window.
        required: true
        version_added: '1.8'
    service:
        description:
            - A comma separated list of PagerDuty service IDs.
        aliases: [ services ]
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
# List ongoing maintenance windows using a user/passwd
- pagerduty:
    name: companyabc
    user: example@example.com
    passwd: password123
    state: ongoing

# List ongoing maintenance windows using a token
- pagerduty:
    name: companyabc
    token: xxxxxxxxxxxxxx
    state: ongoing

# Create a 1 hour maintenance window for service FOO123, using a user/passwd
- pagerduty:
    name: companyabc
    user: example@example.com
    passwd: password123
    state: running
    service: FOO123

# Create a 5 minute maintenance window for service FOO123, using a token
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
    passwd: password123
    state: running
    service: FOO123
    hours: 4
    desc: deployment
  register: pd_window

# Delete the previous maintenance window
- pagerduty:
    name: companyabc
    user: example@example.com
    passwd: password123
    state: absent
    service: '{{ pd_window.result.maintenance_window.id }}'
'''

import datetime
import json
import base64

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_bytes


def auth_header(user, passwd, token):
    if token:
        return "Token token=%s" % token

    auth = base64.b64encode(to_bytes('%s:%s' % (user, passwd)).replace('\n', ''))
    return "Basic %s" % auth


def ongoing(module, name, user, passwd, token):
    url = "https://" + name + ".pagerduty.com/api/v1/maintenance_windows/ongoing"
    headers = {"Authorization": auth_header(user, passwd, token)}

    response, info = fetch_url(module, url, headers=headers)
    if info['status'] != 200:
        module.fail_json(msg="failed to lookup the ongoing window: %s" % info['msg'])

    try:
        json_out = json.loads(response.read())
    except:
        json_out = ""

    return False, json_out, False


def create(module, name, user, passwd, token, requester_id, service, hours, minutes, desc):
    now = datetime.datetime.utcnow()
    later = now + datetime.timedelta(hours=int(hours), minutes=int(minutes))
    start = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    end = later.strftime("%Y-%m-%dT%H:%M:%SZ")

    url = "https://" + name + ".pagerduty.com/api/v1/maintenance_windows"
    headers = {
        'Authorization': auth_header(user, passwd, token),
        'Content-Type': 'application/json',
    }
    request_data = {'maintenance_window': {'start_time': start, 'end_time': end, 'description': desc, 'service_ids': service}}

    if requester_id:
        request_data['requester_id'] = requester_id
    else:
        if token:
            module.fail_json(msg="requester_id is required when using a token")

    data = json.dumps(request_data)
    response, info = fetch_url(module, url, data=data, headers=headers, method='POST')
    if info['status'] != 201:
        module.fail_json(msg="failed to create the window: %s" % info['msg'])

    try:
        json_out = json.loads(response.read())
    except:
        json_out = ""

    return False, json_out, True


def absent(module, name, user, passwd, token, requester_id, service):
    url = "https://" + name + ".pagerduty.com/api/v1/maintenance_windows/" + service[0]
    headers = {
        'Authorization': auth_header(user, passwd, token),
        'Content-Type': 'application/json',
    }
    request_data = {}

    if requester_id:
        request_data['requester_id'] = requester_id
    else:
        if token:
            module.fail_json(msg="requester_id is required when using a token")

    data = json.dumps(request_data)
    response, info = fetch_url(module, url, data=data, headers=headers, method='DELETE')
    if info['status'] != 204:
        module.fail_json(msg="failed to delete the window: %s" % info['msg'])

    try:
        json_out = json.loads(response.read())
    except:
        json_out = ""

    return False, json_out, True


def main():

    module = AnsibleModule(
        argument_spec=dict(
            state=dict(required=True, choices=['running', 'started', 'ongoing', 'absent']),
            name=dict(required=True),
            user=dict(required=False),
            passwd=dict(required=False, no_log=True),
            token=dict(required=False, no_log=True),
            service=dict(required=False, type='list', aliases=["services"]),
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
    passwd = module.params['passwd']
    token = module.params['token']
    service = module.params['service']
    hours = module.params['hours']
    minutes = module.params['minutes']
    token = module.params['token']
    desc = module.params['desc']
    requester_id = module.params['requester_id']

    if not token and not (user or passwd):
        module.fail_json(msg="neither user and passwd nor token specified")

    if state == "running" or state == "started":
        if not service:
            module.fail_json(msg="service not specified")
        (rc, out, changed) = create(module, name, user, passwd, token, requester_id, service, hours, minutes, desc)
        if rc == 0:
            changed = True

    if state == "ongoing":
        (rc, out, changed) = ongoing(module, name, user, passwd, token)

    if state == "absent":
        (rc, out, changed) = absent(module, name, user, passwd, token, requester_id, service)

    if rc != 0:
        module.fail_json(msg="failed", result=out)

    module.exit_json(msg="success", result=out, changed=changed)


if __name__ == '__main__':
    main()
