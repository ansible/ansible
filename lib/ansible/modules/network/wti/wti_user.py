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
# Module to execute WTI User Commands on WTI OOB and PDU devices.
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
module: wti_user
version_added: "2.7"
author: "Western Telematic Inc. (@wtinetworkgear)"
short_description: Get various status and parameters from WTI OOB and PDU devices
description:
    - "Get/Add/Edit Delete Users from WTI OOB and PDU devices"
options:
  wti_action:
    description:
      - This is the Action to send the module.
    required: true
    choices: [ "getuser", "adduser", "edituser", "deleteuser" ]
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
  user_name:
    description:
      - This is the User Name that needs to be create/modified/deleted
    required: false
  user_pass:
    description:
      - This is the User Password that needs to be create/modified/deleted
      - If the user is being Created this parameter is required
  user_accesslevel:
    description:
      - This is the access level that needs to be create/modified/deleted
      - 0 View, 1 User, 2 SuperUser, 3 Adminstrator
    required: false
    choices: [ 0, 1, 2, 3 ]
  user_accessssh:
    description:
      - If the user has access to the WTI device via SSH
      - 0 No , 1 Yes
    required: false
    choices: [ 0, 1 ]
  user_accessserial:
    description:
      - If the user has access to the WTI device via Serial ports
      - 0 No , 1 Yes
    required: false
    choices: [ 0, 1 ]
  user_accessweb:
    description:
      - If the user has access to the WTI device via Web
      - 0 No , 1 Yes
    required: false
    choices: [ 0, 1 ]
  user_accessapi:
    description:
      - If the user has access to the WTI device via RESTful APIs
      - 0 No , 1 Yes
    required: false
    choices: [ 0, 1 ]
  user_accessmonitor:
    description:
      - If the user has ability to monitor connection sessions
      - 0 No , 1 Yes
    required: false
    choices: [ 0, 1 ]
  user_accessoutbound:
    description:
      - If the user has ability to initiate Outbound connection
      - 0 No , 1 Yes
    required: false
    choices: [ 0, 1 ]
  user_portaccess:
    description:
      - If AccessLevel is lower than Administrator, which ports the user has access
    required: false
  user_plugaccess:
    description:
      - If AccessLevel is lower than Administrator, which plugs the user has access
    required: false
  user_groupaccess:
    description:
      - If AccessLevel is lower than Administrator, which Groups the user has access
    required: false
  user_callbackphone:
    description:
      - This is the Call Back phone number used for POTS modem connections
    required: false
"""

EXAMPLES = """
# Get User Parameters
- name: Get the User Parameters for the given user of a WTI device
  wti_user:
    wti_action: "edituser"
    wti_url: "{{ansible_host}}"
    wti_username: "{{ansible_user}}"
    wti_password: "{{ansible_pw}}"
    user_name: "userthatexists"

# Create User
- name: Create a User on a given WTI device
  wti_user:
    wti_action: "adduser"
    wti_url: "{{ansible_host}}"
    wti_username: "{{ansible_user}}"
    wti_password: "{{ansible_pw}}"
    user_name: "usernumberone"
    user_pass: "complicatedpassword"
    user_accesslevel: 2
    user_accessssh: 1
    user_accessserial: 1
    user_accessweb: 0
    user_accessapi: 1
    user_accessmonitor: 0
    user_accessoutbound: 0
    user_portaccess: "10011111"
    user_plugaccess: "00000111"
    user_groupaccess:"00000000"

# Edit User
- name: Edit a User on a given WTI device
  wti_user:
    wti_action: "edituser"
    wti_url: "{{ansible_host}}"
    wti_username: "{{ansible_user}}"
    wti_password: "{{ansible_pw}}"
    user_name: "usernumberone"
    user_pass: "newpassword"

# Delete User
- name: Delete a User from a given WTI device
  wti_user:
    wti_action: "edituser"
    wti_url: "{{ansible_host}}"
    wti_username: "{{ansible_user}}"
    wti_password: "{{ansible_pw}}"
    user_name: "usernumberone"

"""

RETURN = """
data:
    description: The output JSON returned from the commands sent
    returned: always
    type: str
"""

from ansible.module_utils.network.wti.wti_common import request
from ansible.module_utils.basic import AnsibleModule

def assemble_json(wtimodule, iAddUser):
    if (len(wtimodule.params["user_name"]) > 0):
        cszTemp = '{"users":'

        cszTemp = cszTemp + '{"username": "'+wtimodule.params["user_name"]+'"'

        # for Adding there must be a password present
        if wtimodule.params["user_pass"] is not None and (len(wtimodule.params["user_pass"]) > 0):
            cszTemp = cszTemp + ',"newpasswd": "'+wtimodule.params["user_pass"]+'"'
        elif iAddUser == 1:
            wtimodule.fail_json(msg='user_pass not defined.', **result)

        if wtimodule.params["user_accesslevel"] is not None:
            if 0 <= wtimodule.params["user_accesslevel"] <= 3:
                cszTemp = cszTemp + ',"accesslevel": '+str(wtimodule.params["user_accesslevel"])+''
        if wtimodule.params["user_portaccess"] is not None:
            cszTemp = cszTemp + ',"portaccess": '+wtimodule.params["user_portaccess"]+''
        if wtimodule.params["user_plugaccess"] is not None:
            cszTemp = cszTemp + ',"plugaccess": '+wtimodule.params["user_plugaccess"]+''
        if wtimodule.params["user_groupaccess"] is not None:
            cszTemp = cszTemp + ',"groupaccess": '+wtimodule.params["user_groupaccess"]+''
        if wtimodule.params["user_accessserial"] is not None:
            if 0 <= wtimodule.params["user_accessserial"] <= 1:
                cszTemp = cszTemp + ',"accessserial": '+str(wtimodule.params["user_accessserial"])+''
        if wtimodule.params["user_accessssh"] is not None:
            if 0 <= wtimodule.params["user_accessserial"] <= 1:
                cszTemp = cszTemp + ',"accessssh": '+str(wtimodule.params["user_accessssh"])+''
        if wtimodule.params["user_accessweb"] is not None:
            if 0 <= wtimodule.params["user_accessweb"] <= 1:
                cszTemp = cszTemp + ',"accessweb": '+str(wtimodule.params["user_accessweb"])+''
        if wtimodule.params["user_accessoutbound"] is not None:
            if 0 <= wtimodule.params["user_accessoutbound"] <= 1:
                cszTemp = cszTemp + ',"accessoutbound": '+str(wtimodule.params["user_accessoutbound"])+''
        if wtimodule.params["user_accessapi"] is not None:
            if 0 <= wtimodule.params["user_accessapi"] <= 1:
                cszTemp = cszTemp + ',"accessapi": '+str(wtimodule.params["user_accessapi"])+''
        if wtimodule.params["user_accessmonitor"] is not None:
            if 0 <= wtimodule.params["user_accessmonitor"] <= 1:
                cszTemp = cszTemp + ',"accessmonitor": '+str(wtimodule.params["user_accessmonitor"])+''
        if wtimodule.params["user_callbackphone"] is not None:
            cszTemp = cszTemp + ',"callbackphone": "'+wtimodule.params["user_callbackphone"]+'"'

        cszTemp = cszTemp + '}'
        cszTemp = cszTemp + '}'
        return cszTemp
    else:
        wtimodule.fail_json(msg='user_name not defined.', **result)

def run_module():
    cszTemp = ""

    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = dict(
        name=dict(type='str', required=False),
        wti_action=dict(choices=['getuser', 'adduser', 'edituser', 'deleteuser'], required=True),
        wti_url=dict(type='str', required=True),
        wti_username=dict(type='str', required=True),
        wti_password=dict(type='str', required=True, no_log=True),
        user_name=dict(type='str', required=True),
        user_pass=dict(type='str', required=False, default=None, no_log=True),
        user_accesslevel=dict(type='int', required=False, default=None),
        user_accessssh=dict(type='int', required=False, default=None),
        user_accessserial=dict(type='int', required=False, default=None),
        user_accessweb=dict(type='int', required=False, default=None),
        user_accessapi=dict(type='int', required=False, default=None),
        user_accessmonitor=dict(type='int', required=False, default=None),
        user_accessoutbound=dict(type='int', required=False, default=None),
        user_portaccess=dict(type='str', required=False, default=None),
        user_plugaccess=dict(type='str', required=False, default=None),
        user_groupaccess=dict(type='str', required=False, default=None),
        user_callbackphone=dict(type='str', required=False, default=None),
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

    if (module.params['wti_action'] == 'getuser'):
        result['data'] = request(module, protocol+module.params['wti_url']+"/api/v2/config/users?username="+module.params['user_name'], module.params['wti_username'], module.params['wti_password'], 8)
    elif (module.params['wti_action'] == 'adduser'):
        cszTemp = assemble_json(module, 1)
        result['data'] = request(module, protocol+module.params['wti_url']+"/api/v2/config/users", module.params['wti_username'], module.params['wti_password'], 8, cszTemp, 'POST')
        result['changed'] = True
    elif (module.params['wti_action'] == 'edituser'):
        cszTemp = assemble_json(module, 0)
        result['data'] = request(module, protocol+module.params['wti_url']+"/api/v2/config/users", module.params['wti_username'], module.params['wti_password'], 8, cszTemp, 'PUT')
        result['changed'] = True
    elif (module.params['wti_action'] == 'deleteuser'):
        result['data'] = request(module, protocol+module.params['wti_url']+"/api/v2/config/users?username="+module.params['user_name'], module.params['wti_username'], module.params['wti_password'], 8, None, 'DELETE')
        result['changed'] = True
    else:
        module.fail_json(msg='User command not recognized.', **result)

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
