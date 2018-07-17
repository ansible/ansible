#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (C) 2018 Red Hat Inc.
# Copyright (C) 2018 Western Telematic Inc.
#
# GNU General Public License v3.0+
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# Module to execute WTI Status Commands on WTI OOB and PDU devices.
# WTI Networking
#
from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = """
---
module: wti_status
version_added: "2.7"
author: "Western Telematic Inc. (@wtinetworkgear)"
short_description: Get various status and parameters from WTI OOB and PDU devices
description:
    - "Get various status and parameters from WTI OOB and PDU devices"
options:
  wti_action:
    description:
      - This is the Action to send the module.
    required: true
    choices: [ "temperature", "firmware", "status", "alarms" ]
  wti_url:
    description:
      - This is the URL of the WTI device to send the module.
    required: true
  wti_username:
    description:
      - This is the Username of the WTI device to send the module.
  wti_password:
    description:
      - This is the Password of the WTI device to send the module.
  use_https:
    description:
      - Designates to use an https connection or http connection.
    required: false
    default: True
    choices: [ True, False ]
"""

EXAMPLES = """
# Get temperature
- name: Get the temperature of a given WTI device
  wti_status:
    wti_action: "temperature"
    wti_url: "{{ansible_host}}"
    wti_username: "{{ansible_user}}"
    wti_password: "{{ansible_pw}}"

# Get firmware version
- name: Get the firmware version of a given WTI device
  wti_status:
    wti_action: "firmware"
    wti_url: "{{ansible_host}}"
    wti_username: "{{ansible_user}}"
    wti_password: "{{ansible_pw}}"

# Get status output
- name: Get the status output from a given WTI device
  wti_status:
    wti_action: "status"
    wti_url: "{{ansible_host}}"
    wti_username: "{{ansible_user}}"
    wti_password: "{{ansible_pw}}"

# Get Alarm output
- name: Get the alarms status of a given WTI device
  wti_status:
    wti_action: "alarms"
    wti_url: "{{ansible_host}}"
    wti_username: "{{ansible_user}}"
    wti_password: "{{ansible_pw}}"
"""

RETURN = """
data:
    description: The output JSON returned from the commands sent
    returned: always
    type: str
"""

from ansible.module_utils.network.wti.wti_common import request
from ansible.module_utils.basic import AnsibleModule

def run_module():
    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = dict(
        name=dict(type='str', required=False),
        wti_action=dict(choices=['temperature', 'firmware', 'status', 'alarms'], required=True),
        wti_url=dict(type='str', required=True),
        wti_username=dict(type='str', required=True),
        wti_password=dict(type='str', required=True, no_log=True),
        use_https=dict(type='bool', default=True)
    )

    result = dict(
        changed=False,
        data=''
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    if module.check_mode:
        return result

    if module.params['use_https'] is True:
        protocol = "https://"
    else:
        protocol = "http://"

    if (module.params['wti_action'] == 'temperature'):
        result['data'] = request(module, protocol+module.params['wti_url']+"/api/v2/status/temperature", module.params['wti_username'], module.params['wti_password'], 8)
    elif (module.params['wti_action'] == 'firmware'):
        result['data'] = request(module, protocol+module.params['wti_url']+"/api/v2/status/firmware", module.params['wti_username'], module.params['wti_password'], 8)
    elif (module.params['wti_action'] == 'status'):
        result['data'] = request(module, protocol+module.params['wti_url']+"/api/v2/status/status", module.params['wti_username'], module.params['wti_password'], 8)
    elif (module.params['wti_action'] == 'alarms'):
        result['data'] = request(module, protocol+module.params['wti_url']+"/api/v2/status/alarms", module.params['wti_username'], module.params['wti_password'], 8)
    else:
        module.fail_json(msg='Status command not recognized.', **result)

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
