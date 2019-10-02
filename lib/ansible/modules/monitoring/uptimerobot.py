#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = '''
module: uptimerobot
short_description: Create, remove, pause and start monitors in Uptimerobot
description:
    - This module will let you create, remove, pause and start monitors in Uptimerobot
author: "Ninjiner (@ninjiner)"
version_added: "2.8"
requirements:
    - Valid Uptime Robot API Key
    - https://pypi.org/project/uptimerobotpy/
options:
    state:
        description:
            - Define whether or not the monitor should be running or paused.
        required: true
        choices: [ "started", "paused", "present", "absent" ]
    url:
        description:
            - Url to be checked
        required: true
    name:
        description:
            - The friendly name of the monitor
        required: true
    check_type:
        description:
            - The kind of check, that will be performed on the url.
        required: true
        choices: [ "http", "dns" ]
    monitorid:
        description:
            - ID of the monitor to check.
        required: true
    apikey:
        description:
            - Uptime Robot API key.
        required: true
notes:
    - Support for further wit functionalities, which the api provides has not yet been implemented.
'''

EXAMPLES = '''
# Pause the monitor with an ID of 12345.
- uptimerobot:
    monitorid: 12345
    apikey: 12345-1234512345
    state: paused

# Create an http checking monitor for https://www.my-domain.com
- uptimerobot:
    state: present
    url: https://www.my-domain.com
    name: My domain
    check_type: http
    apikey: 12345-1234512345
'''

from ansible.module_utils.basic import AnsibleModule
from uptimerobotpy import UptimeRobot
from requests import HTTPError
import sys

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

API_FORMAT = 'json'
API_NOJSONCALLBACK = 1
CHANGED_STATE = False
SUPPORTS_CHECK_MODE = False


def get_monitor_id(up_robot, gn):
    monitors = up_robot.get_all_monitors()
    for m_dict in monitors['monitors']:
        if m_dict['friendly_name'] == gn:
            return m_dict['id']


def main():
    result = dict(
        changed=False,
        original_message='',
        message=''
    )

    module = AnsibleModule(
        argument_spec=dict(
            apikey=dict(required=True, no_log=True),
            name=dict(required=True),
            url=dict(required=True),
            check_type=dict(required=True, choices=['http', 'dns']),
            state=dict(required=True, choices=['started', 'paused', 'present', 'absent']),
            monitorid=dict(required=False),
        ),
        supports_check_mode=SUPPORTS_CHECK_MODE
    )

    params = dict(
        apikey=module.params['apikey'],
        name=module.params['name'],
        url=module.params['url'],
        check_type=module.params['check_type'],
        state=module.params['state'],
        monitorid=module.params['monitorid'],
        format=API_FORMAT,
        noJsonCallback=API_NOJSONCALLBACK
    )
    try:
        up_robot = UptimeRobot(api_key=module.params['apikey'])
    except KeyError:
        sys.exit("Problem with API-Key")
    except HTTPError:
        sys.exit("Cannot reach uptimerobot API endpoint")

    if params['state'] != 'present':
        mid = get_monitor_id(up_robot, module.params['name'])
    else:
        mid = False

    if params['check_type'] == 'http':
        check_type = '1'
    elif params['check_type'] == 'dns':
        check_type = '2'
    else:
        check_type = '1'

    if params['state'] == 'present':
        up_robot.new_monitor(module.params['name'], module.params['url'], check_type)
        result['message'] = 'Monitor is present'
    elif params['state'] == 'absent':
        up_robot.delete_monitor(mid)
        result['message'] = 'Monitor has been removed'
    elif params['state'] == 'started':
        up_robot.edit_monitor(mid, status=module.params['state'])
        result['message'] = 'Monitor is running'
    elif params['state'] == 'paused':
        up_robot.edit_monitor(mid, status=module.params['state'])
        result['message'] = 'Monitor is paused'
        pass

    if get_monitor_id(up_robot, module.params['name']) is None and params['state'] is not 'absent':
        module.fail_json(msg='Could not perform action')
    elif get_monitor_id(up_robot, module.params['name']) is not None and params['state'] is 'absent':
        module.fail_json(msg='Could not delete monitor')

    result['original_message'] = params['url']

    module.exit_json(**result)


if __name__ == "__main__":
    main()
