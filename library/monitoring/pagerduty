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
    desc:
        description:
            - Short description of maintenance window.
        required: false
        default: Created by Ansible
        choices: []
        aliases: []
notes:
    - This module does not yet have support to end maintenance windows.
'''

EXAMPLES='''
# List ongoing maintenance windows.
- pagerduty: name=companyabc user=example@example.com passwd=password123 state=ongoing

# Create a 1 hour maintenance window for service FOO123.
- pagerduty: name=companyabc
             user=example@example.com
             passwd=password123
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

import json
import datetime
import urllib2
import base64


def ongoing(name, user, passwd):

    url = "https://" + name + ".pagerduty.com/api/v1/maintenance_windows/ongoing"
    auth = base64.encodestring('%s:%s' % (user, passwd)).replace('\n', '')

    req = urllib2.Request(url)
    req.add_header("Authorization", "Basic %s" % auth)
    res = urllib2.urlopen(req)
    out = res.read()

    return False, out


def create(name, user, passwd, service, hours, desc):

    now = datetime.datetime.utcnow()
    later = now + datetime.timedelta(hours=int(hours))
    start = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    end = later.strftime("%Y-%m-%dT%H:%M:%SZ")

    url = "https://" + name + ".pagerduty.com/api/v1/maintenance_windows"
    auth = base64.encodestring('%s:%s' % (user, passwd)).replace('\n', '')
    data = json.dumps({'maintenance_window': {'start_time': start, 'end_time': end, 'description': desc, 'service_ids': [service]}})

    req = urllib2.Request(url, data)
    req.add_header("Authorization", "Basic %s" % auth)
    req.add_header('Content-Type', 'application/json')
    res = urllib2.urlopen(req)
    out = res.read()

    return False, out


def main():

    module = AnsibleModule(
        argument_spec=dict(
        state=dict(required=True, choices=['running', 'started', 'ongoing']),
        name=dict(required=True),
        user=dict(required=True),
        passwd=dict(required=True),
        service=dict(required=False),
        hours=dict(default='1', required=False),
        desc=dict(default='Created by Ansible', required=False)
        )
    )

    state = module.params['state']
    name = module.params['name']
    user = module.params['user']
    passwd = module.params['passwd']
    service = module.params['service']
    hours = module.params['hours']
    desc = module.params['desc']

    if state == "running" or state == "started":
        if not service:
            module.fail_json(msg="service not specified")
        (rc, out) = create(name, user, passwd, service, hours, desc)

    if state == "ongoing":
        (rc, out) = ongoing(name, user, passwd)

    if rc != 0:
        module.fail_json(msg="failed", result=out)

    module.exit_json(msg="success", result=out)

# include magic from lib/ansible/module_common.py
#<<INCLUDE_ANSIBLE_MODULE_COMMON>>
main()
