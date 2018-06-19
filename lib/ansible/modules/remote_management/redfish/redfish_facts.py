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
module: redfish_facts
version_added: "2.7"
short_description: Manages Out-Of-Band controllers using Redfish APIs
description:
  - Builds Redfish URIs locally and sends them to remote OOB controllers to
    get information back.
  - Information retrieved is placed in a location specified by the user.
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

author: "Jose Delarosa (github: jose-delarosa)"
'''

EXAMPLES = '''
  - name: Getting system inventory
    redfish_facts:
      category: Inventory
      command: GetSystemInventory
      baseuri: "{{ baseuri }}"
      user: "{{ user }}"
      password: "{{ password }}"

  - name: Get CPU Inventory
    redfish_facts:
      category: Inventory
      command: GetCpuInventory
      baseuri: "{{ baseuri }}"
      user: "{{ user}}"
      password: "{{ password }}"

  - name: Get BIOS attributes
    redfish_facts:
      category: System
      command: GetBiosAttributes
      baseuri: "{{ baseuri }}"
      user: "{{ user }}"
      password: "{{ password }}"

  - name: List all users
    redfish_facts:
      category: Accounts
      command: ListUsers
      baseuri: "{{ baseuri }}"
      user: "{{ user }}"
      password: "{{ password }}"
'''

RETURN = '''
result:
    description: different results depending on task
    returned: always
    type: dict
    sample: List of CPUs on system
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
            command=dict(),
            baseuri=dict(required=True),
            user=dict(required=True),
            password=dict(required=True, no_log=True),
        ),
        supports_check_mode=False
    )

    category = module.params['category']
    command = module.params['command']

    # admin credentials used for authentication
    creds = {'user': module.params['user'],
             'pswd': module.params['password']}

    # Build root URI
    root_uri = "https://" + module.params['baseuri']
    rf_uri = "/redfish/v1"
    rf_utils = RedfishUtils(creds, root_uri)

    # Organize by Categories / Commands
    if category == "Inventory":
        # execute only if we find a System resource
        result = rf_utils._find_systems_resource(rf_uri)
        if result['ret'] is False:
            module.fail_json(msg=result['msg'])

        # Set default value
        if not command:
            command = "GetSystemInventory"

        # General
        if command == "GetSystemInventory":
            result = rf_utils.get_system_inventory()

        # Components
        elif command == "GetPsuInventory":
            result = rf_utils.get_psu_inventory()
        elif command == "GetCpuInventory":
            result = rf_utils.get_cpu_inventory()
        elif command == "GetNicInventory":
            result = rf_utils.get_nic_inventory()

        # Storage
        elif command == "GetStorageControllerInventory":
            result = rf_utils.get_storage_controller_inventory()
        elif command == "GetDiskInventory":
            result = rf_utils.get_disk_inventory()

        # Chassis
        elif command == "GetFanInventory":
            # execute only if we find Chassis resource
            result = rf_utils._find_chassis_resource(rf_uri)
            if result['ret'] is False:
                module.fail_json(msg=result['msg'])
            result = rf_utils.get_fan_inventory()

        else:
            result = {'ret': False, 'msg': 'Invalid Command'}

    elif category == "Accounts":
        # execute only if we find an Account service resource
        result = rf_utils._find_accountservice_resource(rf_uri)
        if result['ret'] is False:
            module.fail_json(msg=result['msg'])

        # Set default value
        if not command:
            command = "ListUsers"

        if command == "ListUsers":
            result = rf_utils.list_users()
        else:
            result = {'ret': False, 'msg': 'Invalid Command'}

    elif category == "System":
        # execute only if we find a System resource
        result = rf_utils._find_systems_resource(rf_uri)
        if result['ret'] is False:
            module.fail_json(msg=result['msg'])

        # Set default value
        if not command:
            command = "GetBiosAttributes"

        if command == "GetBiosAttributes":
            result = rf_utils.get_bios_attributes()
        elif command == "GetBiosBootOrder":
            result = rf_utils.get_bios_boot_order()
        else:
            result = {'ret': False, 'msg': 'Invalid Command'}

    elif category == "Update":
        # execute only if we find UpdateService resources
        result = rf_utils._find_updateservice_resource(rf_uri)
        if result['ret'] is False:
            module.fail_json(msg=result['msg'])

        # Set default value
        if not command:
            command = "GetFirmwareInventory"

        if command == "GetFirmwareInventory":
            result = rf_utils.get_firmware_inventory()
        else:
            result = {'ret': False, 'msg': 'Invalid Command'}

    elif category == "Manager":
        # execute only if we find a Manager service resource
        result = rf_utils._find_managers_resource(rf_uri)
        if result['ret'] is False:
            module.fail_json(msg=result['msg'])

        # Set default value
        if not command:
            command = "GetManagerAttributes"

        if command == "GetManagerAttributes":
            result = rf_utils.get_manager_attributes()
        elif command == "GetLogs":
            result = rf_utils.get_logs()
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
