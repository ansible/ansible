#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2019 Dell EMC Inc.
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: idrac_redfish_config
version_added: '2.8'
short_description: Manages servers through iDRAC using Dell Redfish APIs
description:
  - For use with Dell iDRAC operations that require Redfish OEM extensions
  - Builds Redfish URIs locally and sends them to remote iDRAC controllers to
    set or update a configuration attribute.
options:
  category:
    required: true
    type: str
    description:
      - Category to execute on iDRAC
  command:
    required: true
    description:
      - List of commands to execute on iDRAC
  baseuri:
    required: true
    description:
      - Base URI of iDRAC
  username:
    required: true
    description:
      - User for authentication with iDRAC
  password:
    required: true
    description:
      - Password for authentication with iDRAC
  manager_attribute_name:
    required: false
    description:
      - name of iDRAC attribute to update
    default: 'null'
  manager_attribute_value:
    required: false
    description:
      - value of iDRAC attribute to update
    default: 'null'
  timeout:
    description:
      - Timeout in seconds for URL requests to iDRAC controller
    default: 10
    type: int

author: "Jose Delarosa (@jose-delarosa)"
'''

EXAMPLES = '''
  - name: Enable NTP in iDRAC
    idrac_redfish_config:
      category: Manager
      command: SetManagerAttributes
      manager_attribute_name: NTPConfigGroup.1.NTPEnable
      manager_attribute_value: Enabled
      baseuri: "{{ baseuri }}"
      username: "{{ username}}"
      password: "{{ password }}"
  - name: Set NTP server 1 to {{ ntpserver1 }} in iDRAC
    idrac_redfish_config:
      category: Manager
      command: SetManagerAttributes
      manager_attribute_name: NTPConfigGroup.1.NTP1
      manager_attribute_value: "{{ ntpserver1 }}"
      baseuri: "{{ baseuri }}"
      username: "{{ username}}"
      password: "{{ password }}"
  - name: Set Timezone to {{ timezone }} in iDRAC
    idrac_redfish_config:
      category: Manager
      command: SetManagerAttributes
      manager_attribute_name: Time.1.Timezone
      manager_attribute_value: "{{ timezone }}"
      baseuri: "{{ baseuri }}"
      username: "{{ username}}"
      password: "{{ password }}"
'''

RETURN = '''
msg:
    description: Message with action result or error description
    returned: always
    type: str
    sample: "Action was successful"
'''

import json
import re
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.redfish_utils import RedfishUtils
from ansible.module_utils._text import to_native


class IdracRedfishUtils(RedfishUtils):

    def set_manager_attributes(self, attr):
        result = {}
        # Here I'm making the assumption that the key 'Attributes' is part of the URI.
        # It may not, but in the hardware I tested with, getting to the final URI where
        # the Manager Attributes are, appear to be part of a specific OEM extension.
        key = "Attributes"

        # Search for key entry and extract URI from it
        response = self.get_request(self.root_uri + self.manager_uri + "/" + key)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        if key not in data:
            return {'ret': False, 'msg': "Key %s not found" % key}

        # Check if attribute exists
        if attr['mgr_attr_name'] not in data[key]:
            return {'ret': False, 'msg': "Manager attribute %s not found" % attr['mgr_attr_name']}

        # Example: manager_attr = {\"name\":\"value\"}
        # Check if value is a number. If so, convert to int.
        if attr['mgr_attr_value'].isdigit():
            manager_attr = "{\"%s\": %i}" % (attr['mgr_attr_name'], int(attr['mgr_attr_value']))
        else:
            manager_attr = "{\"%s\": \"%s\"}" % (attr['mgr_attr_name'], attr['mgr_attr_value'])

        # Find out if value is already set to what we want. If yes, return
        if data[key][attr['mgr_attr_name']] == attr['mgr_attr_value']:
            return {'ret': True, 'changed': False, 'msg': "Manager attribute already set"}

        payload = {"Attributes": json.loads(manager_attr)}
        response = self.patch_request(self.root_uri + self.manager_uri + "/" + key, payload)
        if response['ret'] is False:
            return response
        return {'ret': True, 'changed': True, 'msg': "Modified Manager attribute %s" % attr['mgr_attr_name']}


CATEGORY_COMMANDS_ALL = {
    "Manager": ["SetManagerAttributes"]
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
            manager_attribute_name=dict(default='null'),
            manager_attribute_value=dict(default='null'),
            timeout=dict(type='int', default=10)
        ),
        supports_check_mode=False
    )

    category = module.params['category']
    command_list = module.params['command']

    # admin credentials used for authentication
    creds = {'user': module.params['username'],
             'pswd': module.params['password']}

    # timeout
    timeout = module.params['timeout']

    # iDRAC attributes to update
    mgr_attributes = {'mgr_attr_name': module.params['manager_attribute_name'],
                      'mgr_attr_value': module.params['manager_attribute_value']}

    # Build root URI
    root_uri = "https://" + module.params['baseuri']
    rf_uri = "/redfish/v1/"
    rf_utils = IdracRedfishUtils(creds, root_uri, timeout)

    # Check that Category is valid
    if category not in CATEGORY_COMMANDS_ALL:
        module.fail_json(msg=to_native("Invalid Category '%s'. Valid Categories = %s" % (category, CATEGORY_COMMANDS_ALL.keys())))

    # Check that all commands are valid
    for cmd in command_list:
        # Fail if even one command given is invalid
        if cmd not in CATEGORY_COMMANDS_ALL[category]:
            module.fail_json(msg=to_native("Invalid Command '%s'. Valid Commands = %s" % (cmd, CATEGORY_COMMANDS_ALL[category])))

    # Organize by Categories / Commands

    if category == "Manager":
        # execute only if we find a Manager resource
        result = rf_utils._find_managers_resource(rf_uri)
        if result['ret'] is False:
            module.fail_json(msg=to_native(result['msg']))

        for command in command_list:
            if command == "SetManagerAttributes":
                result = rf_utils.set_manager_attributes(mgr_attributes)

    # Return data back or fail with proper message
    if result['ret'] is True:
        module.exit_json(changed=result['changed'], msg=to_native(result['msg']))
    else:
        module.fail_json(msg=to_native(result['msg']))


if __name__ == '__main__':
    main()
