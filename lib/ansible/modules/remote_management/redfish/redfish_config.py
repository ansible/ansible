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
  - Manages BIOS configuration settings.
  - Manages OOB controller configuration settings.
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
    default: 'null'
  bios_attr_value:
    required: false
    description:
      - value of BIOS attribute to update
    default: 'null'
  mgr_attr_name:
    required: false
    description:
      - name of Manager attribute to update
    default: 'null'
  mgr_attr_value:
    required: false
    description:
      - value of Manager attribute to update
    default: 'null'

author: "Jose Delarosa (github: jose-delarosa)"
'''

EXAMPLES = '''
  - name: Set BootMode to UEFI
    redfish_config:
      category: Systems
      command: SetBiosAttributes
      bios_attr_name: BootMode
      bios_attr_value: Uefi
      baseuri: "{{ baseuri }}"
      user: "{{ user }}"
      password: "{{ password }}"

  - name: Set BootMode to Legacy BIOS
    redfish_config:
      category: Systems
      command: SetBiosAttributes
      bios_attr_name: BootMode
      bios_attr_value: Bios
      baseuri: "{{ baseuri }}"
      user: "{{ user }}"
      password: "{{ password }}"

  - name: Enable PXE Boot for NIC1
    redfish_config:
      category: Systems
      command: SetBiosAttributes
      bios_attr_name: PxeDev1EnDis
      bios_attr_value: Enabled
      baseuri: "{{ baseuri }}"
      user: "{{ user }}"
      password: "{{ password }}"

  - name: Set BIOS default settings
    redfish_config:
      category: Systems
      command: SetBiosDefaultSettings
      baseuri: "{{ baseuri }}"
      user: "{{ user }}"
      password: "{{ password }}"

  - name: Enable NTP in the OOB Controller
    redfish_config:
      category: Manager
      command: SetManagerAttributes
      mgr_attr_name: NTPConfigGroup.1.NTPEnable
      mgr_attr_value: Enabled
      baseuri: "{{ baseuri }}"
      user: "{{ user}}"
      password: "{{ password }}"

  - name: Set NTP server 1 to {{ ntpserver1 }} in the OOB Controller
    redfish_config:
      category: Manager
      command: SetManagerAttributes
      mgr_attr_name: NTPConfigGroup.1.NTP1
      mgr_attr_value: "{{ ntpserver1 }}"
      baseuri: "{{ baseuri }}"
      user: "{{ user}}"
      password: "{{ password }}"

  - name: Set Timezone to {{ timezone }} in the OOB Controller
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
msg:
    description: Message with action result or error description
    returned: always
    type: string
    sample: "Action was successful"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.redfish_utils import RedfishUtils
from ansible.module_utils._text import to_native


# More will be added as module features are expanded
CATEGORY_COMMANDS_ALL = {
    "Systems": ["SetBiosDefaultSettings", "SetBiosAttributes"],
    "Manager": ["SetManagerAttributes"],
}


def main():
    result = {}
    module = AnsibleModule(
        argument_spec=dict(
            category=dict(required=True),
            command=dict(required=True, type='list'),
            baseuri=dict(required=True),
            user=dict(required=True),
            password=dict(required=True, no_log=True),
            mgr_attr_name=dict(default='null'),
            mgr_attr_value=dict(default='null'),
            bios_attr_name=dict(default='null'),
            bios_attr_value=dict(default='null'),
        ),
        supports_check_mode=False
    )

    category = module.params['category']
    command_list = module.params['command']

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
    rf_uri = "/redfish/v1/"
    rf_utils = RedfishUtils(creds, root_uri)

    # Check that Category is valid
    if category not in CATEGORY_COMMANDS_ALL:
        module.fail_json(msg=to_native("Invalid Category '%s'. Valid Categories = %s" % (category, CATEGORY_COMMANDS_ALL.keys())))

    # Check that all commands are valid
    for cmd in command_list:
        # Fail if even one command given is invalid
        if cmd not in CATEGORY_COMMANDS_ALL[category]:
            module.fail_json(msg=to_native("Invalid Command '%s'. Valid Commands = %s" % (cmd, CATEGORY_COMMANDS_ALL[category])))

    # Organize by Categories / Commands
    if category == "Systems":
        # execute only if we find a System resource
        result = rf_utils._find_systems_resource(rf_uri)
        if result['ret'] is False:
            module.fail_json(msg=to_native(result['msg']))

        for command in command_list:
            if command == "SetBiosDefaultSettings":
                result = rf_utils.set_bios_default_settings()
            elif command == "SetBiosAttributes":
                result = rf_utils.set_bios_attributes(bios_attributes)

    elif category == "Manager":
        # execute only if we find a Manager service resource
        result = rf_utils._find_managers_resource(rf_uri)
        if result['ret'] is False:
            module.fail_json(msg=to_native(result['msg']))

        for command in command_list:
            if command == "SetManagerAttributes":
                module.deprecate(msg='The SetManagerAttributes command in '
                                     'module redfish_config is deprecated. '
                                     'Use an OEM Redfish module instead.',
                                 version='2.8')
                result = rf_utils.set_manager_attributes(mgr_attributes)

    # Return data back or fail with proper message
    if result['ret'] is True:
        module.exit_json(changed=result['changed'], msg=to_native(result['msg']))
    else:
        module.fail_json(msg=to_native(result['msg']))


if __name__ == '__main__':
    main()
