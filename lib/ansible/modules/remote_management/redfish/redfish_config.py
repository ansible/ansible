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
module: redfish_config
version_added: "2.7"
short_description: Manages Out-Of-Band controllers using Redfish APIs
description:
  - Builds Redfish URIs locally and sends them to remote OOB controllers to
    set or update a configuration attribute.
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
  bios_attr_name:
    required: false
    description:
      - name of BIOS attribute to update
  bios_attr_value:
    required: false
    description:
      - value of BIOS attribute to update to
  mgr_attr_name:
    required: false
    description:
      - name of Manager attribute to update
  mgr_attr_value:
    required: false
    description:
      - value of Manager attribute to update to

author: "Jose Delarosa (github: jose-delarosa)"
'''

EXAMPLES = '''
  - name: Enable PXE Boot for NIC1
    redfish_config:
      category: System
      command: SetBiosAttributes
      bios_attr_name: PxeDev1EnDis
      bios_attr_value: Enabled
      baseuri: "{{ baseuri }}"
      user: "{{ user }}"
      password: "{{ password }}"

  - name: Set BIOS default settings
    redfish_config:
      category: System
      command: SetBiosDefaultSettings
      baseuri: "{{ baseuri }}"
      user: "{{ user }}"
      password: "{{ password }}"

  - name: Set Manager Timezone to {{ timezone }}
    redfish_config:
      category: Manager
      command: SetManagerAttributes
      mgr_attr_name: Time.1.Timezone
      mgr_attr_value: "{{ timezone }}"
      baseuri: "{{ baseuri }}"
      user: "{{ user}}"
      password: "{{ password }}"
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
            mgr_attr_name=dict(),
            mgr_attr_value=dict(),
            bios_attr_name=dict(),
            bios_attr_value=dict(),
        ),
        supports_check_mode=False
    )

    category = module.params['category']
    command = module.params['command']

    # admin credentials used for authentication
    creds = {'user': module.params['user'],
             'pswd': module.params['password']}

    # Manager attributes to update
    mgr_attributes = {'mgr_attr_name': module.params['mgr_attr_name'],
                      'mgr_attr_value': module.params['mgr_attr_value']}
    # BIOS attributes to update
    bios_attributes = {'bios_attr_name': module.params['bios_attr_name'],
                       'bios_attr_value': module.params['bios_attr_value']}

    # Build root URI
    root_uri = "https://" + module.params['baseuri']
    rf_uri = "/redfish/v1"
    rf_utils = RedfishUtils(creds, root_uri)

    # Organize by Categories / Commands
    if category == "System":
        # execute only if we find a System resource
        result = rf_utils._find_systems_resource(rf_uri)
        if result['ret'] is False:
            module.fail_json(msg=result['msg'])

        if command == "SetBiosDefaultSettings":
            result = rf_utils.set_bios_default_settings()
        elif command == "SetBiosAttributes":
            result = rf_utils.set_bios_attributes(bios_attributes)
        else:
            result = {'ret': False, 'msg': 'Invalid Command'}

    elif category == "Manager":
        # execute only if we find a Manager service resource
        result = rf_utils._find_managers_resource(rf_uri)
        if result['ret'] is False:
            module.fail_json(msg=result['msg'])

        if command == "SetManagerAttributes":
            result = rf_utils.set_manager_attributes(mgr_attributes)
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
