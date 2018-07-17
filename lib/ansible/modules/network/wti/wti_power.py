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
# Module to execute WTI Power Commands on WTI OOB and PDU devices.
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
module: wti_power
version_added: "2.7"
author: "Western Telematic Inc. (@wtinetworkgear)"
short_description: Get Power and Current data from WTI OOB/Combo and PDU devices
description:
    - "Get Power and Current data from WTI OOB/Combo and PDU devices"
options:
  wti_action:
    description:
      - This is the Action to send the module.
    required: true
    choices: [ "getpower", "getcurrent" ]
  wti_url:
    description:
      - This is the URL of the WTI device  to send the module.
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
  startdate:
    description:
      - Start date of the range to look for power data
    required: false
  enddate:
    description:
      - End date of the range to look for power data
    required: false
"""

EXAMPLES = """
# Get Power data
- name: Get Power data for a given WTI device
  wti_status:
    wti_action: "getpower"
    wti_url: "{{ansible_host}}"
    wti_username: "{{ansible_user}}"
    wti_password: "{{ansible_pw}}"

# Get Current data
- name: Get Current data for a given WTI device
  wti_status:
    wti_action: "getcurrent"
    wti_url: "{{ansible_host}}"
    wti_username: "{{ansible_user}}"
    wti_password: "{{ansible_pw}}"

# Get Power data for a date range
- name: Get Power data for a given WTI device given a certain date range
  wti_status:
    wti_action: "getpower"
    wti_url: "{{ansible_host}}"
    wti_username: "{{ansible_user}}"
    wti_password: "{{ansible_pw}}"
    startdate: "07-10-2018"
    enddate: "07-18-2018"
"""

RETURN = """
data:
    description: The output JSON returned from the commands sent
    returned: always
    type: str
"""

try:
    from ansible.module_utils.network.wti.wti_common import request
    from ansible.module_utils.basic import AnsibleModule
except ImportError as exc:
    IMPORT_ERROR = "Error importing module prerequisites: %s" % exc

def run_module():
    StartDate = EndDate = None
    additional = ""
    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = dict(
        wti_action=dict(choices=['getpower', 'getcurrent'], required=True),
        wti_url=dict(type='str', required=True),
        wti_username=dict(type='str', required=True),
        wti_password=dict(type='str', required=True, no_log=True),
        startdate=dict(type='str', required=False, default=None),
        enddate=dict(type='str', required=False, default=None),
        use_https=dict(type='bool', default=True)
    )

    result = dict(
        changed=False,
        data=''
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    if module.check_mode:
        return result

    if module.params["startdate"] is not None and (len(module.params["startdate"]) > 0):
        StartDate = module.params["startdate"]

        if module.params["enddate"] is not None and (len(module.params["enddate"]) > 0):
            EndDate = module.params["enddate"]

            additional = "?startdate="+StartDate+"&enddate="+EndDate

    if module.params['use_https'] is True:
        protocol = "https://"
    else:
        protocol = "http://"

    if (module.params['wti_action'] == 'getpower'):
        result['data'] = request(module, protocol+module.params['wti_url']+"/api/v2/config/power"+additional, module.params['wti_username'], module.params['wti_password'], 8)
    elif (module.params['wti_action'] == 'getcurrent'):
        result['data'] = request(module, protocol+module.params['wti_url']+"/api/v2/config/current"+additional, module.params['wti_username'], module.params['wti_password'], 8)
    else:
        module.fail_json(msg='Power command not recognized.', **result)

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
