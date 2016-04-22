#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Author: Artūras 'arturaz' Šlajus <x11@arturaz.net>
#
# This module is proudly sponsored by iGeolise (www.igeolise.com) and
# Tiny Lab Productions (www.tinylabproductions.com).
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
---
module: datadog_event
short_description: Posts events to DataDog  service
description:
- "Allows to post events to DataDog (www.datadoghq.com) service."
- "Uses http://docs.datadoghq.com/api/#events API."
version_added: "1.3"
author: "Artūras `arturaz` Šlajus (@arturaz)"
notes: []
requirements: []
options:
    api_key:
        description: ["Your DataDog API key."]
        required: true
        default: null
    title:
        description: ["The event title."]
        required: true
        default: null
    text:
        description: ["The body of the event."]
        required: true
        default: null
    date_happened:
        description:
        - POSIX timestamp of the event.
        - Default value is now.
        required: false
        default: now
    priority:
        description: ["The priority of the event."]
        required: false
        default: normal
        choices: [normal, low]
    tags:
        description: ["Comma separated list of tags to apply to the event."]
        required: false
        default: null
    alert_type:
        description: ["Type of alert."]
        required: false
        default: info
        choices: ['error', 'warning', 'info', 'success']
    aggregation_key:
        description: ["An arbitrary string to use for aggregation."]
        required: false
        default: null
    validate_certs:
        description:
            - If C(no), SSL certificates will not be validated. This should only be used
              on personally controlled sites using self-signed certificates.
        required: false
        default: 'yes'
        choices: ['yes', 'no']
        version_added: 1.5.1
'''

EXAMPLES = '''
# Post an event with low priority
datadog_event: title="Testing from ansible" text="Test!" priority="low"
               api_key="6873258723457823548234234234"
# Post an event with several tags
datadog_event: title="Testing from ansible" text="Test!"
               api_key="6873258723457823548234234234"
               tags=aa,bb,#host:{{ inventory_hostname }}
'''

def main():
    module = AnsibleModule(
        argument_spec=dict(
            api_key=dict(required=True, no_log=True),
            title=dict(required=True),
            text=dict(required=True),
            date_happened=dict(required=False, default=None, type='int'),
            priority=dict(
                required=False, default='normal', choices=['normal', 'low']
            ),
            tags=dict(required=False, default=None, type='list'),
            alert_type=dict(
                required=False, default='info',
                choices=['error', 'warning', 'info', 'success']
            ),
            aggregation_key=dict(required=False, default=None),
            source_type_name=dict(
                required=False, default='my apps',
                choices=['nagios', 'hudson', 'jenkins', 'user', 'my apps',
                         'feed', 'chef', 'puppet', 'git', 'bitbucket', 'fabric',
                         'capistrano']
            ),
            validate_certs = dict(default='yes', type='bool'),
        )
    )

    post_event(module)

def post_event(module):
    uri = "https://app.datadoghq.com/api/v1/events?api_key=%s" % module.params['api_key']

    body = dict(
        title=module.params['title'],
        text=module.params['text'],
        priority=module.params['priority'],
        alert_type=module.params['alert_type']
    )
    if module.params['date_happened'] != None:
        body['date_happened'] = module.params['date_happened']
    if module.params['tags'] != None:
        body['tags'] = module.params['tags']
    if module.params['aggregation_key'] != None:
        body['aggregation_key'] = module.params['aggregation_key']
    if module.params['source_type_name'] != None:
        body['source_type_name'] = module.params['source_type_name']

    json_body = module.jsonify(body)
    headers = {"Content-Type": "application/json"}

    (response, info) = fetch_url(module, uri, data=json_body, headers=headers)
    if info['status'] == 202:
        response_body = response.read()
        response_json = module.from_json(response_body)
        if response_json['status'] == 'ok':
            module.exit_json(changed=True)
        else:
            module.fail_json(msg=response)
    else:
        module.fail_json(**info)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
if __name__ == '__main__':
    main()
