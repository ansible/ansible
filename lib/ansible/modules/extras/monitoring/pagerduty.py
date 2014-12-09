#!/usr/bin/python

DOCUMENTATION = '''

module: pagerduty
short_description: Create PagerDuty maintenance windows
description:
    - This module will let you create PagerDuty maintenance windows
version_added: "1.2"
author: Justin Johns
requirements:
    - PagerDuty API access
options:
    state:
        description:
            - Create a maintenance window or get a list of ongoing windows.
        required: true
        default: null
        choices: [ "running", "started", "ongoing" ]
        aliases: []
    name:
        description:
            - PagerDuty unique subdomain.
        required: true
        default: null
        choices: []
        aliases: []
    user:
        description:
            - PagerDuty user ID.
        required: true
        default: null
        choices: []
        aliases: []
    passwd:
        description:
            - PagerDuty user password.
        required: true
        default: null
        choices: []
        aliases: []
    token:
        description:
            - A pagerduty token, generated on the pagerduty site. Can be used instead of
              user/passwd combination.
        required: true
        default: null
        choices: []
        aliases: []
        version_added: '1.8'
    requester_id:
        description:
            - ID of user making the request. Only needed when using a token and creating a maintenance_window.
        required: true
        default: null
        choices: []
        aliases: []
        version_added: '1.8'
    service:
        description:
            - PagerDuty service ID.
        required: false
        default: null
        choices: []
        aliases: []
    hours:
        description:
            - Length of maintenance window in hours.
        required: false
        default: 1
        choices: []
        aliases: []
    minutes:
        description:
            - Maintenance window in minutes (this is added to the hours).
        required: false
        default: 0
        choices: []
        aliases: []
        version_added: '1.8'
    desc:
        description:
            - Short description of maintenance window.
        required: false
        default: Created by Ansible
        choices: []
        aliases: []
    validate_certs:
        description:
            - If C(no), SSL certificates will not be validated. This should only be used
              on personally controlled sites using self-signed certificates.
        required: false
        default: 'yes'
        choices: ['yes', 'no']
        version_added: 1.5.1

notes:
    - This module does not yet have support to end maintenance windows.
'''

EXAMPLES='''
# List ongoing maintenance windows using a user/passwd
- pagerduty: name=companyabc user=example@example.com passwd=password123 state=ongoing

# List ongoing maintenance windows using a token
- pagerduty: name=companyabc token=xxxxxxxxxxxxxx state=ongoing

# Create a 1 hour maintenance window for service FOO123, using a user/passwd
- pagerduty: name=companyabc
             user=example@example.com
             passwd=password123
             state=running
             service=FOO123

# Create a 5 minute maintenance window for service FOO123, using a token
- pagerduty: name=companyabc
             token=xxxxxxxxxxxxxx
             hours=0
             minutes=5
             state=running
             service=FOO123


# Create a 4 hour maintenance window for service FOO123 with the description "deployment".
- pagerduty: name=companyabc
             user=example@example.com
             passwd=password123
             state=running
             service=FOO123
             hours=4
             desc=deployment
'''

import datetime
import base64

def auth_header(user, passwd, token):
    if token:
        return "Token token=%s" % token

    auth = base64.encodestring('%s:%s' % (user, passwd)).replace('\n', '')
    return "Basic %s" % auth

def ongoing(module, name, user, passwd, token):
    url = "https://" + name + ".pagerduty.com/api/v1/maintenance_windows/ongoing"
    headers = {"Authorization": auth_header(user, passwd, token)}

    response, info = fetch_url(module, url, headers=headers)
    if info['status'] != 200:
        module.fail_json(msg="failed to lookup the ongoing window: %s" % info['msg'])

    return False, response.read()


def create(module, name, user, passwd, token, requester_id, service, hours, minutes, desc):
    now = datetime.datetime.utcnow()
    later = now + datetime.timedelta(hours=int(hours), minutes=int(minutes))
    start = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    end = later.strftime("%Y-%m-%dT%H:%M:%SZ")

    url = "https://" + name + ".pagerduty.com/api/v1/maintenance_windows"
    headers = {
        'Authorization': auth_header(user, passwd, token),
        'Content-Type' : 'application/json',
    }
    request_data = {'maintenance_window': {'start_time': start, 'end_time': end, 'description': desc, 'service_ids': [service]}}
    if requester_id:
        request_data['requester_id'] = requester_id
    else:
        if token:
            module.fail_json(msg="requester_id is required when using a token")

    data = json.dumps(request_data)
    response, info = fetch_url(module, url, data=data, headers=headers, method='POST')
    if info['status'] != 200:
        module.fail_json(msg="failed to create the window: %s" % info['msg'])

    return False, response.read()


def main():

    module = AnsibleModule(
        argument_spec=dict(
        state=dict(required=True, choices=['running', 'started', 'ongoing']),
        name=dict(required=True),
        user=dict(required=False),
        passwd=dict(required=False),
        token=dict(required=False),
        service=dict(required=False),
        requester_id=dict(required=False),
        hours=dict(default='1', required=False),
        minutes=dict(default='0', required=False),
        desc=dict(default='Created by Ansible', required=False),
        validate_certs = dict(default='yes', type='bool'),
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
    requester_id =  module.params['requester_id']

    if not token and not (user or passwd):
        module.fail_json(msg="neither user and passwd nor token specified")

    if state == "running" or state == "started":
        if not service:
            module.fail_json(msg="service not specified")
        (rc, out) = create(module, name, user, passwd, token, requester_id, service, hours, minutes, desc)

    if state == "ongoing":
        (rc, out) = ongoing(module, name, user, passwd, token)

    if rc != 0:
        module.fail_json(msg="failed", result=out)

    module.exit_json(msg="success", result=out)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *

main()
