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
short_description: Pause and start Uptime Robot monitoring
description:
    - This module will let you start and pause Uptime Robot Monitoring
author: "Nate Kingsley (@nate-kingsley)"
version_added: "1.9"
requirements:
    - Valid Uptime Robot API Key
options:
    state:
        description:
            - Define whether or not the monitor should be running or paused.
        required: true
        default: null
        choices: [ "started", "paused", "new", "reset", "delete"]
        aliases: []
    monitorid:
        description:
            - ID of the monitor to check.
        required: true
        default: null
        choices: []
        aliases: []
    apikey:
        description:
            - Uptime Robot API key.
        required: true
        default: null
        choices: []
        aliases: []
notes:
    - Support for adding and removing monitors and alert contacts has not yet been implemented.
'''

EXAMPLES = '''
# Pause the monitor with an ID of 12345.
- uptimerobot:
    monitorid: 12345
    apikey: 12345-1234512345
    state: paused

# Start the monitor with an ID of 12345.
- uptimerobot:
    monitorid: 12345
    apikey: 12345-1234512345
    state: started
'''

import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves.urllib.parse import urlencode
from ansible.module_utils.urls import fetch_url

API_BASE = "https://api.uptimerobot.com/"

API_ACTIONS = dict(
    status='getMonitors?',
    editMonitor='editMonitor?',
    newMonitor='newMonitor?',
    resetMonitor='resetMonitor?',
    deleteMonitor='deleteMonitor?'
)

API_FORMAT = 'json'
API_NOJSONCALLBACK = 1
CHANGED_STATE = False
SUPPORTS_CHECK_MODE = False


def checkID(module, params):

    data = urlencode(params)
    full_uri = API_BASE + API_ACTIONS['status'] + data
    req, info = fetch_url(module, full_uri)
    result = req.read()
    jsonresult = json.loads(result)
    req.close()
    return jsonresult


def startMonitor(module, params):

    params['monitorStatus'] = 1
    data = urlencode(params)
    full_uri = API_BASE + API_ACTIONS['editMonitor'] + data
    req, info = fetch_url(module, full_uri)
    result = req.read()
    jsonresult = json.loads(result)
    req.close()
    return jsonresult['stat']


def pauseMonitor(module, params):

    params['monitorStatus'] = 0
    data = urlencode(params)
    full_uri = API_BASE + API_ACTIONS['editMonitor'] + data
    req, info = fetch_url(module, full_uri)
    result = req.read()
    jsonresult = json.loads(result)
    req.close()
    return jsonresult['stat']


def newMonitor(module, params):
    params['monitorStatus'] = 1
    data = urlencode(params)
    full_uri = API_BASE + API_ACTIONS['newMonitor'] + data
    req, info = fetch_url(module, full_uri)
    result = req.read()
    jsonresult = json.load(result)
    req.close()
    return jsonresult['monitor']['id']


def resetMonitor(module, params):
    params['monitorStatus'] = 1
    data = urlencode(params)
    full_uri = API_BASE + API_ACTIONS['deleteMonitor'] + data
    req, info = fetch_url(module, full_uri)
    result = req.read()
    jsonresult = json.load(result)
    req.close()
    return jsonresult['stat']


def deleteMonitor(module, params):
    params['monitorStatus'] = 1
    data = urlencode(params)
    full_uri = API_BASE + API_ACTIONS['resetMonitor'] + data
    req, info = fetch_url(module, full_uri)
    result = req.read()
    jsonresult = json.load(result)
    req.close()
    return jsonresult['stat'], jsonresult['monitor']['id']


def editMonitor(module, params):
    params['monitorStatus'] = 1
    data = urlencode(params)
    full_uri = API_BASE + API_ACTIONS['editMonitor'] + data
    req, info = fetch_url(module, full_uri)
    result = req.read()
    jsonresult = json.load(result)
    req.close()
    return jsonresult['stat']


def main():

    module = AnsibleModule(
        argument_spec=dict(
            state=dict(required=True, choices=['started', 'paused']),
            apikey=dict(required=True),
            monitorid=dict(required=True)
        ),
        supports_check_mode=SUPPORTS_CHECK_MODE
    )

    params = dict(
        apiKey=module.params['apikey'],
        monitors=module.params['monitorid'],
        monitorID=module.params['monitorid'],
        format=API_FORMAT,
        noJsonCallback=API_NOJSONCALLBACK
    )

    check_result = checkID(module, params)

    if check_result['stat'] != "ok":
        module.fail_json(
            msg="failed",
            result=check_result['message']
        )

    if module.params['state'] == 'started':
        monitor_result = startMonitor(module, params)
    elif module.params['state'] == 'pause':
        monitor_result = pauseMonitor(module, params)
    elif module.params['state'] == 'new':
        monitor_result = newMonitor(module, params)
    elif module.params['state'] == 'delete':
        monitor_result = deleteMonitor(module, params)
    elif module.params['state'] == 'reset':
        monitor_result = resetMonitor(module, params)
    elif module.params['state'] == 'edit':
        monitor_result = editMonitor(module, params)

    module.exit_json(
        msg="success",
        result=monitor_result
    )


if __name__ == '__main__':
    main()
