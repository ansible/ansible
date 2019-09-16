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
module: redfish_info
version_added: "2.7"
short_description: Manages Out-Of-Band controllers using Redfish APIs
description:
  - Builds Redfish URIs locally and sends them to remote OOB controllers to
    get information back.
  - Information retrieved is placed in a location specified by the user.
  - This module was called C(redfish_facts) before Ansible 2.9, returning C(ansible_facts).
    Note that the M(redfish_info) module no longer returns C(ansible_facts)!
options:
  category:
    required: false
    description:
      - List of categories to execute on OOB controller
    default: ['Systems']
    type: list
  command:
    required: false
    description:
      - List of commands to execute on OOB controller
    type: list
  baseuri:
    required: true
    description:
      - Base URI of OOB controller
    type: str
  username:
    required: true
    description:
      - User for authentication with OOB controller
    type: str
    version_added: "2.8"
  password:
    required: true
    description:
      - Password for authentication with OOB controller
    type: str
  timeout:
    description:
      - Timeout in seconds for URL requests to OOB controller
    default: 10
    type: int
    version_added: '2.8'

author: "Jose Delarosa (@jose-delarosa)"
'''

EXAMPLES = '''
  - name: Get CPU inventory
    redfish_info:
      category: Systems
      command: GetCpuInventory
      baseuri: "{{ baseuri }}"
      username: "{{ username }}"
      password: "{{ password }}"
    register: result
  - debug:
      msg: "{{ result.redfish_facts.cpu.entries | to_nice_json }}"

  - name: Get CPU model
    redfish_info:
      category: Systems
      command: GetCpuInventory
      baseuri: "{{ baseuri }}"
      username: "{{ username }}"
      password: "{{ password }}"
    register: result
  - debug:
      msg: "{{ result.redfish_facts.cpu.entries.0.Model }}"

  - name: Get memory inventory
    redfish_info:
      category: Systems
      command: GetMemoryInventory
      baseuri: "{{ baseuri }}"
      username: "{{ username }}"
      password: "{{ password }}"
    register: result

  - name: Get fan inventory with a timeout of 20 seconds
    redfish_info:
      category: Chassis
      command: GetFanInventory
      baseuri: "{{ baseuri }}"
      username: "{{ username }}"
      password: "{{ password }}"
      timeout: 20
    register: result

  - name: Get Virtual Media information
    redfish_info:
      category: Manager
      command: GetVirtualMedia
      baseuri: "{{ baseuri }}"
      username: "{{ username }}"
      password: "{{ password }}"
    register: result
  - debug:
      msg: "{{ result.redfish_facts.virtual_media.entries | to_nice_json }}"

  - name: Get Volume Inventory
    redfish_info:
      category: Systems
      command: GetVolumeInventory
      baseuri: "{{ baseuri }}"
      username: "{{ username }}"
      password: "{{ password }}"
    register: result
  - debug:
      msg: "{{ result.redfish_facts.volume.entries | to_nice_json }}"

  - name: Get Session information
    redfish_info:
      category: Sessions
      command: GetSessions
      baseuri: "{{ baseuri }}"
      username: "{{ username }}"
      password: "{{ password }}"
    register: result
  - debug:
      msg: "{{ result.redfish_facts.session.entries | to_nice_json }}"

  - name: Get default inventory information
    redfish_info:
      baseuri: "{{ baseuri }}"
      username: "{{ username }}"
      password: "{{ password }}"
    register: result
  - debug:
      msg: "{{ result.redfish_facts | to_nice_json }}"

  - name: Get several inventories
    redfish_info:
      category: Systems
      command: GetNicInventory,GetBiosAttributes
      baseuri: "{{ baseuri }}"
      username: "{{ username }}"
      password: "{{ password }}"

  - name: Get default system inventory and user information
    redfish_info:
      category: Systems,Accounts
      baseuri: "{{ baseuri }}"
      username: "{{ username }}"
      password: "{{ password }}"

  - name: Get default system, user and firmware information
    redfish_info:
      category: ["Systems", "Accounts", "Update"]
      baseuri: "{{ baseuri }}"
      username: "{{ username }}"
      password: "{{ password }}"

  - name: Get Manager NIC inventory information
    redfish_info:
      category: Manager
      command: GetManagerNicInventory
      baseuri: "{{ baseuri }}"
      username: "{{ username }}"
      password: "{{ password }}"

  - name: Get boot override information
    redfish_info:
      category: Systems
      command: GetBootOverride
      baseuri: "{{ baseuri }}"
      username: "{{ username }}"
      password: "{{ password }}"

  - name: Get chassis inventory
    redfish_info:
      category: Chassis
      command: GetChassisInventory
      baseuri: "{{ baseuri }}"
      username: "{{ username }}"
      password: "{{ password }}"

  - name: Get all information available in the Manager category
    redfish_info:
      category: Manager
      command: all
      baseuri: "{{ baseuri }}"
      username: "{{ username }}"
      password: "{{ password }}"

  - name: Get firmware update capability information
    redfish_info:
      category: Update
      command: GetFirmwareUpdateCapabilities
      baseuri: "{{ baseuri }}"
      username: "{{ username }}"
      password: "{{ password }}"

  - name: Get all information available in all categories
    redfish_info:
      category: all
      command: all
      baseuri: "{{ baseuri }}"
      username: "{{ username }}"
      password: "{{ password }}"
'''

RETURN = '''
result:
    description: different results depending on task
    returned: always
    type: dict
    sample: List of CPUs on system
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.redfish_utils import RedfishUtils

CATEGORY_COMMANDS_ALL = {
    "Systems": ["GetSystemInventory", "GetPsuInventory", "GetCpuInventory",
                "GetMemoryInventory", "GetNicInventory",
                "GetStorageControllerInventory", "GetDiskInventory", "GetVolumeInventory",
                "GetBiosAttributes", "GetBootOrder", "GetBootOverride"],
    "Chassis": ["GetFanInventory", "GetPsuInventory", "GetChassisPower", "GetChassisThermals", "GetChassisInventory"],
    "Accounts": ["ListUsers"],
    "Sessions": ["GetSessions"],
    "Update": ["GetFirmwareInventory", "GetFirmwareUpdateCapabilities"],
    "Manager": ["GetManagerNicInventory", "GetVirtualMedia", "GetLogs"],
}

CATEGORY_COMMANDS_DEFAULT = {
    "Systems": "GetSystemInventory",
    "Chassis": "GetFanInventory",
    "Accounts": "ListUsers",
    "Update": "GetFirmwareInventory",
    "Sessions": "GetSessions",
    "Manager": "GetManagerNicInventory"
}


def main():
    result = {}
    category_list = []
    module = AnsibleModule(
        argument_spec=dict(
            category=dict(type='list', default=['Systems']),
            command=dict(type='list'),
            baseuri=dict(required=True),
            username=dict(required=True),
            password=dict(required=True, no_log=True),
            timeout=dict(type='int', default=10)
        ),
        supports_check_mode=False
    )
    is_old_facts = module._name == 'redfish_facts'
    if is_old_facts:
        module.deprecate("The 'redfish_facts' module has been renamed to 'redfish_info', "
                         "and the renamed one no longer returns ansible_facts", version='2.13')

    # admin credentials used for authentication
    creds = {'user': module.params['username'],
             'pswd': module.params['password']}

    # timeout
    timeout = module.params['timeout']

    # Build root URI
    root_uri = "https://" + module.params['baseuri']
    rf_utils = RedfishUtils(creds, root_uri, timeout, module)

    # Build Category list
    if "all" in module.params['category']:
        for entry in CATEGORY_COMMANDS_ALL:
            category_list.append(entry)
    else:
        # one or more categories specified
        category_list = module.params['category']

    for category in category_list:
        command_list = []
        # Build Command list for each Category
        if category in CATEGORY_COMMANDS_ALL:
            if not module.params['command']:
                # True if we don't specify a command --> use default
                command_list.append(CATEGORY_COMMANDS_DEFAULT[category])
            elif "all" in module.params['command']:
                for entry in range(len(CATEGORY_COMMANDS_ALL[category])):
                    command_list.append(CATEGORY_COMMANDS_ALL[category][entry])
            # one or more commands
            else:
                command_list = module.params['command']
                # Verify that all commands are valid
                for cmd in command_list:
                    # Fail if even one command given is invalid
                    if cmd not in CATEGORY_COMMANDS_ALL[category]:
                        module.fail_json(msg="Invalid Command: %s" % cmd)
        else:
            # Fail if even one category given is invalid
            module.fail_json(msg="Invalid Category: %s" % category)

        # Organize by Categories / Commands
        if category == "Systems":
            # execute only if we find a Systems resource
            resource = rf_utils._find_systems_resource()
            if resource['ret'] is False:
                module.fail_json(msg=resource['msg'])

            for command in command_list:
                if command == "GetSystemInventory":
                    result["system"] = rf_utils.get_multi_system_inventory()
                elif command == "GetCpuInventory":
                    result["cpu"] = rf_utils.get_multi_cpu_inventory()
                elif command == "GetMemoryInventory":
                    result["memory"] = rf_utils.get_multi_memory_inventory()
                elif command == "GetNicInventory":
                    result["nic"] = rf_utils.get_multi_nic_inventory(category)
                elif command == "GetStorageControllerInventory":
                    result["storage_controller"] = rf_utils.get_multi_storage_controller_inventory()
                elif command == "GetDiskInventory":
                    result["disk"] = rf_utils.get_multi_disk_inventory()
                elif command == "GetVolumeInventory":
                    result["volume"] = rf_utils.get_multi_volume_inventory()
                elif command == "GetBiosAttributes":
                    result["bios_attribute"] = rf_utils.get_multi_bios_attributes()
                elif command == "GetBootOrder":
                    result["boot_order"] = rf_utils.get_multi_boot_order()
                elif command == "GetBootOverride":
                    result["boot_override"] = rf_utils.get_multi_boot_override()

        elif category == "Chassis":
            # execute only if we find Chassis resource
            resource = rf_utils._find_chassis_resource()
            if resource['ret'] is False:
                module.fail_json(msg=resource['msg'])

            for command in command_list:
                if command == "GetFanInventory":
                    result["fan"] = rf_utils.get_fan_inventory()
                elif command == "GetPsuInventory":
                    result["psu"] = rf_utils.get_psu_inventory()
                elif command == "GetChassisThermals":
                    result["thermals"] = rf_utils.get_chassis_thermals()
                elif command == "GetChassisPower":
                    result["chassis_power"] = rf_utils.get_chassis_power()
                elif command == "GetChassisInventory":
                    result["chassis"] = rf_utils.get_chassis_inventory()

        elif category == "Accounts":
            # execute only if we find an Account service resource
            resource = rf_utils._find_accountservice_resource()
            if resource['ret'] is False:
                module.fail_json(msg=resource['msg'])

            for command in command_list:
                if command == "ListUsers":
                    result["user"] = rf_utils.list_users()

        elif category == "Update":
            # execute only if we find UpdateService resources
            resource = rf_utils._find_updateservice_resource()
            if resource['ret'] is False:
                module.fail_json(msg=resource['msg'])

            for command in command_list:
                if command == "GetFirmwareInventory":
                    result["firmware"] = rf_utils.get_firmware_inventory()
                elif command == "GetFirmwareUpdateCapabilities":
                    result["firmware_update_capabilities"] = rf_utils.get_firmware_update_capabilities()

        elif category == "Sessions":
            # execute only if we find SessionService resources
            resource = rf_utils._find_sessionservice_resource()
            if resource['ret'] is False:
                module.fail_json(msg=resource['msg'])

            for command in command_list:
                if command == "GetSessions":
                    result["session"] = rf_utils.get_sessions()

        elif category == "Manager":
            # execute only if we find a Manager service resource
            resource = rf_utils._find_managers_resource()
            if resource['ret'] is False:
                module.fail_json(msg=resource['msg'])

            for command in command_list:
                if command == "GetManagerNicInventory":
                    result["manager_nics"] = rf_utils.get_multi_nic_inventory(category)
                elif command == "GetVirtualMedia":
                    result["virtual_media"] = rf_utils.get_multi_virtualmedia()
                elif command == "GetLogs":
                    result["log"] = rf_utils.get_logs()

    # Return data back
    if is_old_facts:
        module.exit_json(ansible_facts=dict(redfish_facts=result))
    else:
        module.exit_json(redfish_facts=result)


if __name__ == '__main__':
    main()
