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
        choices: [ "started", "paused" ]
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
- uptimerobot: monitorid=12345
           apikey=12345-1234512345
           state=paused

# Start the monitor with an ID of 12345.
- uptimerobot: monitorid=12345
           apikey=12345-1234512345
           state=started

'''

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        # Let snippet from module_utils/basic.py return a proper error in this case
        pass

import urllib
import time

API_BASE = "http://api.uptimerobot.com/"

API_ACTIONS = dict(
    status='getMonitors?',
    editMonitor='editMonitor?'
)

API_FORMAT = 'json'
API_NOJSONCALLBACK = 1
CHANGED_STATE = False
SUPPORTS_CHECK_MODE = False


def checkID(module, params):

    data = urllib.urlencode(params)
    full_uri = API_BASE + API_ACTIONS['status'] + data
    req, info = fetch_url(module, full_uri)
    result = req.read()
    jsonresult = json.loads(result)
    req.close()
    return jsonresult


def startMonitor(module, params):

    params['monitorStatus'] = 1
    data = urllib.urlencode(params)
    full_uri = API_BASE + API_ACTIONS['editMonitor'] + data
    req, info = fetch_url(module, full_uri)
    result = req.read()
    jsonresult = json.loads(result)
    req.close()
    return jsonresult['stat']


def pauseMonitor(module, params):

    params['monitorStatus'] = 0
    data = urllib.urlencode(params)
    full_uri = API_BASE + API_ACTIONS['editMonitor'] + data
    req, info = fetch_url(module, full_uri)
    result = req.read()
    jsonresult = json.loads(result)
    req.close()
    return jsonresult['stat']


def main():

    module = AnsibleModule(
        argument_spec = dict(
            state     = dict(required=True, choices=['started', 'paused']),
            apikey      = dict(required=True),
            monitorid   = dict(required=True)
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
    else:
        monitor_result = pauseMonitor(module, params)

    module.exit_json(
        msg="success",
        result=monitor_result
    )


from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
if __name__ == '__main__':
    main()
