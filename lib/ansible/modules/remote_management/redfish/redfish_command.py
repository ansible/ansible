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
  - Manages OOB controller ex. reboot, log management.
  - Manages OOB controller users ex. add, remove, update.
  - Manages system power ex. on, off, graceful and forced reboot.
options:
  category:
    required: true
    description:
      - Category to execute on OOB controller
  command:
    required: true
    description:
      - List of commands to execute on OOB controller
  baseuri:
    required: true
    description:
      - Base URI of OOB controller
  username:
    required: true
    description:
      - User for authentication with OOB controller
    version_added: "2.8"
  password:
    required: true
    description:
      - Password for authentication with OOB controller
  id:
    required: false
    description:
      - ID of user to add/delete/modify
    version_added: "2.8"
  new_username:
    required: false
    description:
      - name of user to add/delete/modify
    version_added: "2.8"
  new_password:
    required: false
    description:
      - password of user to add/delete/modify
    version_added: "2.8"
  roleid:
    required: false
    description:
      - role of user to add/delete/modify
    version_added: "2.8"
  bootdevice:
    required: false
    description:
      - bootdevice when setting boot configuration
  timeout:
    description:
      - Timeout in seconds for URL requests to OOB controller
    default: 10
    type: int
    version_added: '2.8'

author: "Jose Delarosa (@jose-delarosa)"
'''

EXAMPLES = '''
  - name: Restart system power gracefully
    redfish_command:
      category: Systems
      command: PowerGracefulRestart
      baseuri: "{{ baseuri }}"
      username: "{{ username }}"
      password: "{{ password }}"

  - name: Set one-time boot device to {{ bootdevice }}
    redfish_command:
      category: Systems
      command: SetOneTimeBoot
      bootdevice: "{{ bootdevice }}"
      baseuri: "{{ baseuri }}"
      username: "{{ username }}"
      password: "{{ password }}"

  - name: Set chassis indicator LED to blink
    redfish_command:
      category: Chassis
      command: IndicatorLedBlink
      baseuri: "{{ baseuri }}"
      username: "{{ username }}"
      password: "{{ password }}"

  - name: Add and enable user
    redfish_command:
      category: Accounts
      command: AddUser,EnableUser
      baseuri: "{{ baseuri }}"
      username: "{{ username }}"
      password: "{{ password }}"
      id: "{{ id }}"
      new_username: "{{ new_username }}"
      new_password: "{{ new_password }}"
      roleid: "{{ roleid }}"

  - name: Disable and delete user
    redfish_command:
      category: Accounts
      command: ["DisableUser", "DeleteUser"]
      baseuri: "{{ baseuri }}"
      username: "{{ username }}"
      password: "{{ password }}"
      id: "{{ id }}"

  - name: Update user password
    redfish_command:
      category: Accounts
      command: UpdateUserPassword
      baseuri: "{{ baseuri }}"
      username: "{{ username }}"
      password: "{{ password }}"
      id: "{{ id }}"
      new_password: "{{ new_password }}"

  - name: Clear Manager Logs with a timeout of 20 seconds
    redfish_command:
      category: Manager
      command: ClearLogs
      baseuri: "{{ baseuri }}"
      username: "{{ username }}"
      password: "{{ password }}"
      timeout: 20
'''

RETURN = '''
msg:
    description: Message with action result or error description
    returned: always
    type: str
    sample: "Action was successful"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.redfish_utils import RedfishUtils
from ansible.module_utils._text import to_native


# More will be added as module features are expanded
CATEGORY_COMMANDS_ALL = {
    "Systems": ["PowerOn", "PowerForceOff", "PowerGracefulRestart",
                "PowerGracefulShutdown", "PowerReboot", "SetOneTimeBoot"],
    "Chassis": ["IndicatorLedOn", "IndicatorLedOff", "IndicatorLedBlink"],
    "Accounts": ["AddUser", "EnableUser", "DeleteUser", "DisableUser",
                 "UpdateUserRole", "UpdateUserPassword"],
    "Manager": ["GracefulRestart", "ClearLogs"],
}


def main():
    result = {}
    module = AnsibleModule(
        argument_spec=dict(
            category=dict(required=True),
            command=dict(required=True, type='list'),
            baseuri=dict(required=True),
            username=dict(required=True),
            password=dict(required=True, no_log=True),
            id=dict(),
            new_username=dict(),
            new_password=dict(no_log=True),
            roleid=dict(),
            bootdevice=dict(),
            timeout=dict(type='int', default=10)
        ),
        supports_check_mode=False
    )

    category = module.params['category']
    command_list = module.params['command']

    # admin credentials used for authentication
    creds = {'user': module.params['username'],
             'pswd': module.params['password']}

    # user to add/modify/delete
    user = {'userid': module.params['id'],
            'username': module.params['new_username'],
            'userpswd': module.params['new_password'],
            'userrole': module.params['roleid']}

    # timeout
    timeout = module.params['timeout']

    # Build root URI
    root_uri = "https://" + module.params['baseuri']
    rf_uri = "/redfish/v1/"
    rf_utils = RedfishUtils(creds, root_uri, timeout)

    # Check that Category is valid
    if category not in CATEGORY_COMMANDS_ALL:
        module.fail_json(msg=to_native("Invalid Category '%s'. Valid Categories = %s" % (category, CATEGORY_COMMANDS_ALL.keys())))

    # Check that all commands are valid
    for cmd in command_list:
        # Fail if even one command given is invalid
        if cmd not in CATEGORY_COMMANDS_ALL[category]:
            module.fail_json(msg=to_native("Invalid Command '%s'. Valid Commands = %s" % (cmd, CATEGORY_COMMANDS_ALL[category])))

    # Organize by Categories / Commands
    if category == "Accounts":
        ACCOUNTS_COMMANDS = {
            "AddUser": rf_utils.add_user,
            "EnableUser": rf_utils.enable_user,
            "DeleteUser": rf_utils.delete_user,
            "DisableUser": rf_utils.disable_user,
            "UpdateUserRole": rf_utils.update_user_role,
            "UpdateUserPassword": rf_utils.update_user_password
        }

        # execute only if we find an Account service resource
        result = rf_utils._find_accountservice_resource(rf_uri)
        if result['ret'] is False:
            module.fail_json(msg=to_native(result['msg']))

        for command in command_list:
            result = ACCOUNTS_COMMANDS[command](user)

    elif category == "Systems":
        # execute only if we find a System resource
        result = rf_utils._find_systems_resource(rf_uri)
        if result['ret'] is False:
            module.fail_json(msg=to_native(result['msg']))

        for command in command_list:
            if "Power" in command:
                result = rf_utils.manage_system_power(command)
            elif command == "SetOneTimeBoot":
                result = rf_utils.set_one_time_boot_device(module.params['bootdevice'])

    elif category == "Chassis":
        result = rf_utils._find_chassis_resource(rf_uri)
        if result['ret'] is False:
            module.fail_json(msg=to_native(result['msg']))

        led_commands = ["IndicatorLedOn", "IndicatorLedOff", "IndicatorLedBlink"]

        # Check if more than one led_command is present
        num_led_commands = sum([command in led_commands for command in command_list])
        if num_led_commands > 1:
            result = {'ret': False, 'msg': "Only one IndicatorLed command should be sent at a time."}
        else:
            for command in command_list:
                if command in led_commands:
                    result = rf_utils.manage_indicator_led(command)

    elif category == "Manager":
        MANAGER_COMMANDS = {
            "GracefulRestart": rf_utils.restart_manager_gracefully,
            "ClearLogs": rf_utils.clear_logs
        }

        # execute only if we find a Manager service resource
        result = rf_utils._find_managers_resource(rf_uri)
        if result['ret'] is False:
            module.fail_json(msg=to_native(result['msg']))

        for command in command_list:
            result = MANAGER_COMMANDS[command]()

    # Return data back or fail with proper message
    if result['ret'] is True:
        del result['ret']
        module.exit_json(changed=True, msg='Action was successful')
    else:
        module.fail_json(msg=to_native(result['msg']))


if __name__ == '__main__':
    main()
