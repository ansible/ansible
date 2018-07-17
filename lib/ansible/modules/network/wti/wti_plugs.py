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
# Module to execute WTI Plug Commands on WTI OOB and PDU devices.
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
module: wti_plugs
version_added: "2.7"
author: "Western Telematic Inc. (@wtinetworkgear)"
short_description: Get and Set Plug actions on WTI OOB and PDU devices
description:
    - "Get and Set Plug actions on WTI OOB and PDU devices"
options:
  wti_action:
    description:
      - This is the Action to send the module.
    required: true
    choices: [ "getplug", "setplug" ]
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
  plug_id:
    description:
      - This is the plug number or the plug name that is to be manipulated
        For the plugget command, the plug_id 'all' will return the status of all the plugs ther
        user has rights to access.
    required: true
  plug_state:
    description:
      - This is what action to take on the plug.
    required: false
    choices: [ "on", "off", "boot", "default" ]
"""

EXAMPLES = """
# Get Plug status for all ports
- name: Get the Plug status for all ports of a WTI device
  wti_user:
    wti_action: "getplug"
    wti_url: "{{ansible_host}}"
    wti_username: "{{ansible_user}}"
    wti_password: "{{ansible_pw}}"
    plug_id: "all"

# Get Plug status for ports 1 and 2
- name: Get the Plug status for the given ports of a WTI device
  wti_user:
    wti_action: "getplug"
    wti_url: "{{ansible_host}}"
    wti_username: "{{ansible_user}}"
    wti_password: "{{ansible_pw}}"
    plug_id: "1,2"

# Reboot plugs 3 and 4
- name: Reboot Plugs 3 and 4 on a given WTI device
  wti_user:
    wti_action: "setplug"
    wti_url: "{{ansible_host}}"
    wti_username: "{{ansible_user}}"
    wti_password: "{{ansible_pw}}"
    plug_id: "3,4"
    plug_state: "boot"
"""

RETURN = """
data:
    description: The output JSON returned from the commands sent
    returned: always
    type: str
"""

from ansible.module_utils.network.wti.wti_common import request
from ansible.module_utils.basic import AnsibleModule

def assemble_json(wtimodule):

    if wtimodule.params["plug_id"] is not None and (len(wtimodule.params["plug_id"]) > 0):
        cszTemp = ""
        plugspassed = wtimodule.params["plug_id"].split(",")

        for val in plugspassed:
            if (val.isdigit() == True):
                cszTemp = cszTemp + '{"plug": "'+val+'"'
            else:
                cszTemp = cszTemp + '{"plugname": "'+val+'"'

            if wtimodule.params["plug_state"] is not None:
                cszTemp = cszTemp + ',"state": "'+str(wtimodule.params["plug_state"])+'"'

            cszTemp = cszTemp + '}'

        return cszTemp
    else:
        wtimodule.fail_json(msg='serial_port not defined.', **result)

def run_module():
    cszTemp = ""

    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = dict(
        name=dict(type='str', required=False),
        wti_action=dict(choices=['getplug', 'setplug'], required=True),
        wti_url=dict(type='str', required=True),
        wti_username=dict(type='str', required=True),
        wti_password=dict(type='str', required=True, no_log=True),
        plug_id=dict(type='str', required=True, default=None),
        plug_state=dict(choices=['on', 'off', 'boot', 'default'],required=False),
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

    if (module.params['wti_action'] == 'getplug'):
        additional = ""
        if (module.params['plug_id'].lower() != 'all'):
            additional = "?plug="+module.params['plug_id']
        result['data'] = request(module, protocol+module.params['wti_url']+"/api/v2/config/powerplug"+additional, module.params['wti_username'], module.params['wti_password'], 8)
    elif (module.params['wti_action'] == 'setplug'):
        cszTemp = assemble_json(module)
        result['data'] = request(module, protocol+module.params['wti_url']+"/api/v2/config/powerplug", module.params['wti_username'], module.params['wti_password'], 8, cszTemp, 'POST')
        result['changed'] = True
    else:
        module.fail_json(msg='Plug command not recognized.', **result)

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
