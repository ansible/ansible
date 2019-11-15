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
module: uptimerobot
short_description: Create, remove, pause and start monitors in Uptimerobot
description:
    - This module lets you create, remove, pause and start monitors in Uptimerobot
author:
- "Nate Kingsley (@nate-kingsley)"
- "Ninjiner (@Ninjiner)"
version_added: "1.9"
requirements:
    - Valid Uptime Robot API Key
options:
    state:
        description:
            - Define whether or not the monitor should be running or paused.
        required: true
        choices: [ "started", "paused", "created", "absent", "present" ]
    url:
        description:
            - URL to be checked.
        required: true
        version_added: '2.10'
    name:
        description:
            - The friendly name of the monitor.
        required: true
        version_added: '2.10'
    check_type:
        description:
            - The kind of check, that will be performed on the url.
        choices: [ "http", "dns" ]
        version_added: '2.10'
    monitorid:
        description:
            - ID of the monitor to check.
        required: false
    apikey:
        description:
            - Uptime Robot API key.
        required: true
notes:
    - Support for further functionalities, which the api provides has not yet been implemented.
    - created and absent are added in version 2.10
'''

EXAMPLES = '''
# Pause the monitor with an ID of 12345.
- uptimerobot:
    name: My domain
    url: https://www.my-domain.com
    apikey: 12345-1234512345
    state: paused

# Create an http checking monitor for https://www.my-domain.com
- uptimerobot:
    state: created
    url: https://www.my-domain.com
    name: My domain
    check_type: http
    apikey: 12345-1234512345
'''

import json
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import Request
from ansible.module_utils._text import to_text

API_BASE = "https://api.uptimerobot.com/v2/"

API_FORMAT = 'json'
API_NOJSONCALLBACK = 1
CHANGED_STATE = False
SUPPORTS_CHECK_MODE = False


class UptimeRobot:
    def __init__(self, params, api_methods):
        self.headers = {}
        self.headers['Content-Type'] = "application/json"
        self.uri = ''
        self.api_methods = api_methods
        self.params = params
        self.params = self.check_dict(self.params)
        for k, v in self.params.items():
            if k == 'type':
                if v == 'dns':
                    self.params[k] = 2
                else:
                    self.params[k] = 1
        self.body = json.dumps(self.params)
        for state, method in self.api_methods.items():
            if state == self.params['status']:
                self.api_method = method

    def get_monitor_id(self, fname):
        monitors = self.get_monitors()
        for m_dict in monitors['monitors']:
            if m_dict['friendly_name'] == fname:
                mid = m_dict['id']
                return mid

    def get_monitors(self):
        self.body = {}
        self.body['api_key'] = self.params['api_key']
        self.body = json.dumps(self.body)
        self.uri = API_BASE + "getMonitors"
        state = self.api_call()
        return state

    def api_call(self):
        req = Request()
        state = req.post(url=self.uri, data=self.body, headers=self.headers)
        json_response = json.loads(to_text(state.read(), errors='surrogate_or_strict'))
        return json_response

    def api_request(self):
        self.uri = API_BASE + self.api_method
        state = self.api_call()
        return state, self.api_method

    def check_dict(self, dictionary):
        tmp = {}
        for k, v in dictionary.items():
            if v != '':
                tmp[k] = v
        if dictionary['status'] != 'created':
            tmp['id'] = self.get_monitor_id(dictionary['friendly_name'])
        dictionary.clear()
        return tmp


def main():
    result = dict(
        changed=False,
        original_message='',
        message=''
    )

    api_methods = dict(
        started='editMonitor',
        present='newMonitor',
        paused='editMonitor',
        absent='deleteMonitor',
        created='newMonitor'
    )

    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            url=dict(required=True),
            check_type=dict(required=False, choices=['http', 'dns']),
            state=dict(required=True, choices=['started', 'paused', 'absent', 'created', 'present']),
            apikey=dict(required=True, no_log=True),
            monitorid=dict(required=False)
        ),
        supports_check_mode=SUPPORTS_CHECK_MODE
    )

    params = dict(
        api_key=module.params['apikey'],
        monitorID=module.params['monitorid'],
        friendly_name=module.params['name'],
        url=module.params['url'],
        type=module.params['check_type'],
        status=module.params['state'],
        format=API_FORMAT,
        noJsonCallback=API_NOJSONCALLBACK
    )

    uprobot = UptimeRobot(params, api_methods)
    state, api_method = uprobot.api_request()
    result['message'] = state['stat']
    result['original_message'] = state
    if result['message'] != 'ok':
        module.fail_json(msg='Could not perform action {0}'.format(api_method))

    module.exit_json(**result)


if __name__ == '__main__':
    main()
