#!/usr/bin/python
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community"
}

DOCUMENTATION = '''
---
module: fsm_organizations
version_added: "2.8"
author: Luke Weighall (@lweighall)
short_description: Get a list of devices from the FortiSIEM CMDB
description:
  - Gets a short description of each device in the FortiSIEM CMDB and returns the data

options:
  host:
    description:
      - The FortiSIEM's FQDN or IP Address.
    required: true
    
  username:
    description:
      - The username used to authenticate with the FortiManager.
      - organization/username format. The Organization is important, and will only return data from specified Org.
    required: false
    
  password:
    description:
      - The password associated with the username account.
    required: false

  ignore_ssl_errors:
    description:
      - When Enabled this will instruct the HTTP Libraries to ignore any ssl validation errors.
    required: false
    default: "enable"
    options: ["enable", "disable"]

  export_json_to_screen:
    description:
      - When enabled this will print the JSON results to screen.
    required: false
    default: "enable"
    options: ["enable, "disable"]

  export_json_to_file_path:
    description:
      - When populated, an attempt to write JSON dictionary to file is made.
      - An error will be thrown if this fails.
    required: false
    default: None
    
  export_xml_to_file_path:
    description:
      - When populated, an attempt to write XML to file is made.
      - An error will be thrown if this fails.
    required: false
    default: None
    
  mode:
    description:
      - Tells module to get, update or delete organizations.
    required: false
    default: "get"
    options: ["add", "get", "update"]
    
  org_name:
    description:
      - The short-hand camelCase (preferred) name of the organization
    required: false
  
  org_display_name:
    description:
      - The full display name for the organization.
    required: false
  
  org_description:
    description:
      - The description of the organization.
    required: false
  
  org_admin_username:
    description:
      - Organization root admin username to be created.
    required: false
  
  org_admin_password:
    description:
      - Organization root admin password to be used.
    required: false
  
  org_admin_email:
    description:
      - Organization administration email. Either internal, or customer alias. 
    required: false
  
  org_eps:
    description:
      - Events per second limit for organization.
    required: false
  
  org_include_ip_range:
    description:
      - Included IP Range. Typically only used for Orgs without a collector.
    required: false
  
  org_exclude_ip_range:
    description:
      - Excluded IP range. Typically only used for Orgs without a collector.
    required: false
    
  org_collectors:
    description:
      - If specified, other org_collector_ options are ignored. List with JSON dicts format expected.
      - Only name and eps are valid arguments for each dictionary within the list.
      - i.e. [{"name": "collector1", "eps": "200"},{"name":"collector2", "eps": "300"}]
    required: false
  
  org_collector_name:
    description:
      - Organization collector name.
    required: false
  
  org_collector_eps:
    description:
      - Organization collector allowed events per second.
    required: false 
  
    
'''


EXAMPLES = '''
- name: GET LIST OF ORGS
  fsm_organizations:
    host: "10.0.0.15"
    username: "super/api_user"
    password: "Fortinet!1"
    ignore_ssl_errors: "enable"
'''

RETURN = """
api_result:
  description: full API response, includes status code and message
  returned: always
  type: string
"""

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.network.fortisiem.common import FSMEndpoints
from ansible.module_utils.network.fortisiem.common import FSMBaseException
from ansible.module_utils.network.fortisiem.common import DEFAULT_EXIT_MSG
from ansible.module_utils.network.fortisiem.fortisiem import FortiSIEMHandler

import pydevd

def main():
    argument_spec = dict(
        host=dict(required=True, type="str"),
        username=dict(fallback=(env_fallback, ["ANSIBLE_NET_USERNAME"])),
        password=dict(fallback=(env_fallback, ["ANSIBLE_NET_PASSWORD"]), no_log=True),
        ignore_ssl_errors=dict(required=False, type="str", choices=["enable", "disable"], default="enable"),
        export_json_to_screen=dict(required=False, type="str", choices=["enable", "disable"], default="enable"),
        export_json_to_file_path=dict(required=False, type="str"),
        export_xml_to_file_path=dict(required=False, type="str"),
        export_csv_to_file_path=dict(required=False, type="str"),

        mode=dict(required=False, type="str",
                  choices=["get", "update", "add"], default="get"),
        org_name=dict(required=False, type="str"),
        org_display_name=dict(required=False, type="str"),
        org_description=dict(required=False, type="str"),
        org_admin_username=dict(required=False, type="str"),
        org_admin_password=dict(required=False, type="str", no_log=True),
        org_admin_email=dict(required=False, type="str"),
        org_eps=dict(required=False, type="str"),
        org_include_ip_range=dict(required=False, type="str"),
        org_exclude_ip_range=dict(required=False, type="str"),
        org_collectors=dict(required=False, type="list"),
        org_collector_name=dict(required=False, type="str"),
        org_collector_eps=dict(required=False, type="str"),

    )

    module = AnsibleModule(argument_spec, supports_check_mode=False, )

    paramgram = {
        "host": module.params["host"],
        "username": module.params["username"],
        "password": module.params["password"],
        "export_json_to_screen": module.params["export_json_to_screen"],
        "export_json_to_file_path": module.params["export_json_to_file_path"],
        "export_xml_to_file_path": module.params["export_xml_to_file_path"],
        "export_csv_to_file_path": module.params["export_csv_to_file_path"],
        "ignore_ssl_errors": module.params["ignore_ssl_errors"],

        "mode": module.params["mode"],
        "uri": None,
        "input_xml": None,

        "org_name": module.params["org_name"],
        "org_display_name": module.params["org_display_name"],
        "org_description": module.params["org_description"],
        "org_admin_username": module.params["org_admin_username"],
        "org_admin_password": module.params["org_admin_password"],
        "org_admin_email": module.params["org_admin_email"],
        "org_eps": module.params["org_eps"],
        "org_include_ip_range": module.params["org_include_ip_range"],
        "org_exclude_ip_range": module.params["org_exclude_ip_range"],
        "org_collectors": module.params["org_collectors"],
        "org_collector_name": module.params["org_collector_name"],
        "org_collector_eps": module.params["org_collector_eps"],

    }

    # DETERMINE THE MODE AND ADD THE CORRECT DATA TO THE PARAMGRAM
    if paramgram["mode"] == "get":
        paramgram["uri"] = FSMEndpoints.GET_ORGS
    elif paramgram["mode"] == "update":
        paramgram["uri"] = FSMEndpoints.UPDATE_ORGS
    elif paramgram["mode"] == "add":
        paramgram["uri"] = FSMEndpoints.ADD_ORGS

    if paramgram["uri"] is None:
        raise FSMBaseException("Base URI couldn't be constructed. Check options.")

    module.paramgram = paramgram

    # TRY TO INIT THE CONNECTION SOCKET PATH AND FortiManagerHandler OBJECT AND TOOLS
    fsm = None
    try:
        fsm = FortiSIEMHandler(module)
    except BaseException as err:
        raise FSMBaseException("Couldn't load FortiSIEM Handler from mod_utils.")
    # EXECUTE THE MODULE OPERATION
    if paramgram["mode"] in ['get']:
        try:
            results = fsm.handle_simple_request()
        except BaseException as err:
            raise FSMBaseException(err)
    elif paramgram["mode"] in ['update', 'add']:
        try:
            # CREATE PAYLOAD
            paramgram["input_xml"] = fsm.create_org_payload()
            results = fsm.handle_simple_payload_request(payload=paramgram["input_xml"])
        except BaseException as err:
            raise FSMBaseException(err)
    # EXIT USING GOVERN_RESPONSE()
    fsm.govern_response(module=module, results=results, changed=False, good_codes=[200, 204],
                        ansible_facts=fsm.construct_ansible_facts(results["json_results"],
                                                                  module.params,
                                                                  paramgram))

    return module.exit_json(DEFAULT_EXIT_MSG)


if __name__ == "__main__":
    main()
