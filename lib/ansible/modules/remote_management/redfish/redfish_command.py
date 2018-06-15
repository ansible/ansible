#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2017-2018 Dell EMC Inc.
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: redfish_command
version_added: "2.7"
short_description: Manages Out-Of-Band controllers using Redfish APIs
description:
  - Builds Redfish URIs locally and sends them to remote OOB controllers to
    perform an action.
options:
  category:
    required: true
    description:
      - Action category to execute on server
    choices: ["Inventory", "Accounts", "System", "Update", "Manager", "Chassis"]
  command:
    required: true
    description:
      - Command to execute on server
  baseuri:
    required: true
    description:
      - Base URI of OOB controller
  user:
    required: true
    description:
      - User for authentication with OOB controller
  password:
    required: true
    description:
      - Password for authentication with OOB controller
  userid:
    required: false
    description:
      - ID of user to add/delete/modify
  username:
    required: false
    description:
      - name of user to add/delete/modify
  userpswd:
    required: false
    description:
      - password of user to add/delete/modify
  userrole:
    required: false
    description:
      - role of user to add/delete/modify
  bootdevice:
    required: false
    description:
      - bootdevice when setting boot configuration

author: "Jose Delarosa (github: jose-delarosa)"
'''

EXAMPLES = '''
  - name: Set one-time boot device to {{ bootdevice }}
    redfish_command:
      category: System
      command: SetOneTimeBoot
      bootdevice: "{{ bootdevice }}"
      baseuri: "{{ baseuri }}"
      user: "{{ user }}"
      password: "{{ password }}"

  - name: Turn system power on
    redfish_command:
      category: System
      command: PowerOn
      baseuri: "{{ baseuri }}"
      user: "{{ user }}"
      password: "{{ password }}"

  - name: Add user
    redfish_command:
      category: Accounts
      command: AddUser
      baseuri: "{{ baseuri }}"
      user: "{{ user }}"
      password: "{{ password }}"
      userid: "{{ userid }}"
      username: "{{ username }}"
      userpswd: "{{ userpswd }}"
      userrole: "{{ userrole }}"

  - name: Enable user
    redfish_command:
      category: Accounts
      command: EnableUser
      baseuri: "{{ baseuri }}"
      user: "{{ user }}"
      password: "{{ password }}"
      userid: "{{ userid }}"
'''

RETURN = '''
result:
    description: different results depending on task
    returned: always
    type: dict
    sample: BIOS Attributes set as pending values
'''

import os
import json
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.redfish_utils import RedfishUtils


def main():
    result = {}
    module = AnsibleModule(
        argument_spec=dict(
            category=dict(required=True, choices=["Inventory", "Accounts", "System", "Update", "Manager", "Chassis"]),
            command=dict(required=True),
            baseuri=dict(required=True),
            user=dict(required=True),
            password=dict(required=True, no_log=True),
            userid=dict(),
            username=dict(),
            userpswd=dict(no_log=True),
            userrole=dict(),
            bootdevice=dict(),
        ),
        supports_check_mode=False
    )

    category = module.params['category']
    command = module.params['command']
    bootdevice = module.params['bootdevice']

    # admin credentials used for authentication
    creds = {'user': module.params['user'],
             'pswd': module.params['password']}

    # user to add/modify/delete
    user = {'userid': module.params['userid'],
            'username': module.params['username'],
            'userpswd': module.params['userpswd'],
            'userrole': module.params['userrole']}

    # Build root URI
    root_uri = "https://" + module.params['baseuri']
    rf_uri = "/redfish/v1"
    rf_utils = RedfishUtils(creds, root_uri)

    # Organize by Categories / Commands
    if category == "Accounts":
        # execute only if we find an Account service resource
        result = rf_utils._find_accountservice_resource(rf_uri)
        if result['ret'] is False:
            module.fail_json(msg=result['msg'])

        if command == "AddUser":
            result = rf_utils.add_user(user)
        elif command == "EnableUser":
            result = rf_utils.enable_user(user)
        elif command == "DeleteUser":
            result = rf_utils.delete_user(user)
        elif command == "DisableUser":
            result = rf_utils.disable_user(user)
        elif command == "UpdateUserRole":
            result = rf_utils.update_user_role(user)
        elif command == "UpdateUserPassword":
            result = rf_utils.update_user_password(user)
        else:
            result = {'ret': False, 'msg': 'Invalid Command'}

    elif category == "System":
        # execute only if we find a System resource
        result = rf_utils._find_systems_resource(rf_uri)
        if result['ret'] is False:
            module.fail_json(msg=result['msg'])

        if command == "PowerOn" or command == "PowerForceOff" \
                or command == "PowerGracefulRestart" \
                or command == "PowerGracefulShutdown":
            result = rf_utils.manage_system_power(command)
        elif command == "SetOneTimeBoot":
            result = rf_utils.set_one_time_boot_device(bootdevice)
        elif command == "CreateBiosConfigJob":
            # execute only if we find a Managers resource
            result = rf_utils._find_managers_resource(rf_uri)
            if result['ret'] is False:
                module.fail_json(msg=result['msg'])
            result = rf_utils.create_bios_config_job()
        else:
            result = {'ret': False, 'msg': 'Invalid Command'}

    elif category == "Manager":
        # execute only if we find a Manager service resource
        result = rf_utils._find_managers_resource(rf_uri)
        if result['ret'] is False:
            module.fail_json(msg=result['msg'])

        if command == "GracefulRestart":
            result = rf_utils.restart_manager_gracefully()
        elif command == "ClearLogs":
            result = rf_utils.clear_logs()
        else:
            result = {'ret': False, 'msg': 'Invalid Command'}

    else:
        result = {'ret': False, 'msg': 'Invalid Category'}

    # Return data back or fail with proper message
    if result['ret'] is True:
        del result['ret']
        module.exit_json(result=result)
    else:
        module.fail_json(msg=result['msg'])

if __name__ == '__main__':
    main()
