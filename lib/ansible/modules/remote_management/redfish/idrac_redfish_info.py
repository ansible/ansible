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
module: idrac_redfish_info
version_added: "2.8"
short_description: Manages servers through iDRAC using Dell Redfish APIs
description:
  - Builds Redfish URIs locally and sends them to remote iDRAC controllers to
    get information back.
  - For use with Dell iDRAC operations that require Redfish OEM extensions
  - This module was called C(idrac_redfish_facts) before Ansible 2.9, returning C(ansible_facts).
    Note that the M(idrac_redfish_info) module no longer returns C(ansible_facts)!
options:
  category:
    required: true
    description:
      - Category to execute on iDRAC controller
    type: str
  command:
    required: true
    description:
      - List of commands to execute on iDRAC controller
    type: list
  baseuri:
    required: true
    description:
      - Base URI of iDRAC controller
    type: str
  username:
    required: true
    description:
      - User for authentication with iDRAC controller
    type: str
  password:
    required: true
    description:
      - Password for authentication with iDRAC controller
    type: str
  timeout:
    description:
      - Timeout in seconds for URL requests to OOB controller
    default: 10
    type: int

author: "Jose Delarosa (@jose-delarosa)"
'''

EXAMPLES = '''
  - name: Get Manager attributes with a default of 20 seconds
    idrac_redfish_command:
      category: Manager
      command: GetManagerAttributes
      baseuri: "{{ baseuri }}"
      username: "{{ username }}"
      password: "{{ password }}"
      timeout: 20
'''

RETURN = '''
msg:
    description: different results depending on task
    returned: always
    type: dict
    sample: List of Manager attributes
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.redfish_utils import RedfishUtils
from ansible.module_utils._text import to_native


class IdracRedfishUtils(RedfishUtils):

    def get_manager_attributes(self):
        result = {}
        manager_attributes = {}
        key = "Attributes"

        response = self.get_request(self.root_uri + self.manager_uri + "/" + key)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        if key not in data:
            return {'ret': False, 'msg': "Key %s not found" % key}

        for attribute in data[key].items():
            manager_attributes[attribute[0]] = attribute[1]
        result["entries"] = manager_attributes
        return result


CATEGORY_COMMANDS_ALL = {
    "Manager": ["GetManagerAttributes"]
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
            timeout=dict(type='int', default=10)
        ),
        supports_check_mode=False
    )
    is_old_facts = module._name == 'idrac_redfish_facts'
    if is_old_facts:
        module.deprecate("The 'idrac_redfish_facts' module has been renamed to 'idrac_redfish_info', "
                         "and the renamed one no longer returns ansible_facts", version='2.13')

    category = module.params['category']
    command_list = module.params['command']

    # admin credentials used for authentication
    creds = {'user': module.params['username'],
             'pswd': module.params['password']}

    # timeout
    timeout = module.params['timeout']

    # Build root URI
    root_uri = "https://" + module.params['baseuri']
    rf_utils = IdracRedfishUtils(creds, root_uri, timeout, module)

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
        result = rf_utils._find_managers_resource()
        if result['ret'] is False:
            module.fail_json(msg=to_native(result['msg']))

        for command in command_list:
            if command == "GetManagerAttributes":
                result = rf_utils.get_manager_attributes()

    # Return data back or fail with proper message
    if result['ret'] is True:
        del result['ret']
        if is_old_facts:
            module.exit_json(ansible_facts=dict(redfish_facts=result))
        else:
            module.exit_json(redfish_facts=result)
    else:
        module.fail_json(msg=to_native(result['msg']))


if __name__ == '__main__':
    main()
