#!/usr/bin/python

DOCUMENTATION = '''

module: uptimerobot
short_description: Pause and start Uptime Robot monitoring
description:
    - This module will let you start and pause Uptime Robot Monitoring
author: Nate Kingsley
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

import json
import urllib
import urllib2
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

def checkID(params):

	data = urllib.urlencode(params)

	full_uri = API_BASE + API_ACTIONS['status'] + data

	req = urllib2.urlopen(full_uri)

	result = req.read()

	jsonresult = json.loads(result)

	req.close()

	return jsonresult


def startMonitor(params):

	params['monitorStatus'] = 1

	data = urllib.urlencode(params)

	full_uri = API_BASE + API_ACTIONS['editMonitor'] + data

	req = urllib2.urlopen(full_uri)

	result = req.read()

	jsonresult = json.loads(result)

	req.close()

	return jsonresult['stat']


def pauseMonitor(params):

	params['monitorStatus'] = 0

	data = urllib.urlencode(params)

	full_uri = API_BASE + API_ACTIONS['editMonitor'] + data

	req = urllib2.urlopen(full_uri)

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

	check_result = checkID(params)

	if check_result['stat'] != "ok":
		module.fail_json(
			msg="failed",
			result=check_result['message']
		)

	if module.params['state'] == 'started':
		monitor_result = startMonitor(params)
	else:
		monitor_result = pauseMonitor(params)



	module.exit_json(
		msg="success",
		result=monitor_result
	) 


from ansible.module_utils.basic import *
main()
