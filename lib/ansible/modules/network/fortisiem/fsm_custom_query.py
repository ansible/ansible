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
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD

=======
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
=======
>>>>>>> Full FSM Commit
__metaclass__ = type

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community"
}

DOCUMENTATION = '''
---
module: fsm_custom_query
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
version_added: "2.9"
=======
version_added: "2.8"
>>>>>>> Full FSM Commit
=======
version_added: "2.9"
>>>>>>> Bug Fixes according to shippable... re-running
=======
version_added: "2.8"
>>>>>>> Full FSM Commit
author: Luke Weighall (@lweighall)
short_description: Get a list of devices from the FortiSIEM CMDB
description:
  - Gets a short description of each device in the FortiSIEM CMDB and returns the data

options:
  host:
    description:
      - The FortiSIEM's FQDN or IP Address.
    required: true
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD

=======
    
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
=======
    
>>>>>>> Full FSM Commit
  username:
    description:
      - The username used to authenticate with the FortiManager.
      - organization/username format. The Organization is important, and will only return data from specified Org.
    required: false
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD

=======
    
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
=======
    
>>>>>>> Full FSM Commit
  password:
    description:
      - The password associated with the username account.
    required: false
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD

=======
    
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
=======
    
>>>>>>> Full FSM Commit
  ignore_ssl_errors:
    description:
      - When Enabled this will instruct the HTTP Libraries to ignore any ssl validation errors.
    required: false
    default: "enable"
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
    choices: ["enable", "disable"]
=======
    options: ["enable", "disable"]
>>>>>>> Full FSM Commit
=======
    choices: ["enable", "disable"]
>>>>>>> Full FSM Commit. Ready for shippable tests.
=======
    options: ["enable", "disable"]
>>>>>>> Full FSM Commit

  export_json_to_screen:
    description:
      - When enabled this will print the JSON results to screen.
    required: false
    default: "enable"
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
    choices: ["enable", "disable"]
=======
    options: ["enable, "disable"]
>>>>>>> Full FSM Commit
=======
    choices: ["enable", "disable"]
>>>>>>> Full FSM Commit. Ready for shippable tests.
=======
    options: ["enable, "disable"]
>>>>>>> Full FSM Commit

  export_json_to_file_path:
    description:
      - When populated, an attempt to write JSON dictionary to file is made.
      - An error will be thrown if this fails.
    required: false
    default: None
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD

=======
    
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
=======
    
>>>>>>> Full FSM Commit
  export_xml_to_file_path:
    description:
      - When populated, an attempt to write XML to file is made.
      - An error will be thrown if this fails.
    required: false
    default: None
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD

  mode:
    description:
      - Handles how the query is formatted.
    required: false
    default: "get"
    choices: ["get", "set", "update", "delete", "add"]

=======
    
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
  mode:
    description:
      - Handles how the query is formatted.
    required: false
    default: "get"
<<<<<<< HEAD
    options: ["get", "set", "update", "delete", "add"]
    
>>>>>>> Full FSM Commit
=======
    choices: ["get", "set", "update", "delete", "add"]

>>>>>>> Full FSM Commit. Ready for shippable tests.
=======
    
  mode:
    description:
      - Handles how the query is formatted. 
    required: false
    default: "get"
    options: ["get", "set", "update", "delete", "add"]
    
>>>>>>> Full FSM Commit
  uri:
    description:
      - Custom URI to query.
    required: false
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD

=======
    
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
=======
    
>>>>>>> Full FSM Commit
  payload_file:
    description:
      - Specifies the file path to a custom XML payload file.
    required: false
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD

'''

EXAMPLES = '''
- name: SIMPLE CUSTOM QUERY FOR ORGANIZATIONS
  fsm_custom_query:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    ignore_ssl_errors: "enable"
    mode: "get"
    export_json_to_screen: "enable"
    export_json_to_file_path: "/root/custom_query1.json"
    export_xml_to_file_path: "/root/custom_query1.xml"
    uri: "/phoenix/rest/config/Domain"
=======
    
'''
=======
>>>>>>> Full FSM Commit. Ready for shippable tests.

'''

EXAMPLES = '''
- name: SIMPLE CUSTOM QUERY FOR ORGANIZATIONS
  fsm_custom_query:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    ignore_ssl_errors: "enable"
<<<<<<< HEAD
=======
    
'''


EXAMPLES = '''
- name: 
  fsm_custom_query:
    host: "10.0.0.15"
    username: "super/api_user"
    password: "Fortinet!1"
    ignore_ssl_errors: "enable"
>>>>>>> Full FSM Commit

- name: 
  fsm_custom_query:
    host: "10.0.0.15"
    username: "super/api_user"
    password: "Fortinet!1"
    ignore_ssl_errors: "enable"


- name: 
  fsm_custom_query:
    host: "10.0.0.15"
    username: "super/api_user"
    password: "Fortinet!1"
    ignore_ssl_errors: "enable"

  

<<<<<<< HEAD
>>>>>>> Full FSM Commit
=======
    mode: "get"
    export_json_to_screen: "enable"
    export_json_to_file_path: "/root/custom_query1.json"
    export_xml_to_file_path: "/root/custom_query1.xml"
    uri: "/phoenix/rest/config/Domain"
>>>>>>> Full FSM Commit. Ready for shippable tests.
=======
>>>>>>> Full FSM Commit
'''

RETURN = """
api_result:
  description: full API response, includes status code and message
  returned: always
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
  type: str
=======
  type: string
>>>>>>> Full FSM Commit
=======
  type: str
>>>>>>> Full FSM Commit. Ready for shippable tests.
=======
  type: string
>>>>>>> Full FSM Commit
"""

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.network.fortisiem.common import FSMBaseException
from ansible.module_utils.network.fortisiem.common import DEFAULT_EXIT_MSG
from ansible.module_utils.network.fortisiem.fortisiem import FortiSIEMHandler

<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
=======
import pydevd
>>>>>>> Full FSM Commit
=======
>>>>>>> Full FSM Commit. Ready for shippable tests.
=======
import pydevd
>>>>>>> Full FSM Commit

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
                  choices=["get", "set", "update", "delete", "add"], default="get"),
        uri=dict(required=True, type="str"),
        payload_file=dict(required=False, type="str", default=None)
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
        "uri": module.params["uri"],
        "payload_file": module.params["payload_file"],
        "input_xml": None

    }

    module.paramgram = paramgram

    # TRY TO INIT THE CONNECTION SOCKET PATH AND FortiManagerHandler OBJECT AND TOOLS
    fsm = None
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
    results = DEFAULT_EXIT_MSG
    try:
        fsm = FortiSIEMHandler(module)
    except BaseException as err:
        raise FSMBaseException("Couldn't load FortiSIEM Handler from mod_utils. Error: " + str(err))

    if paramgram["payload_file"]:
        paramgram["input_xml"] = fsm.get_file_contents(paramgram["payload_file"])
=======
=======
    results = DEFAULT_EXIT_MSG
>>>>>>> Full FSM Commit. Ready for shippable tests.
    try:
        fsm = FortiSIEMHandler(module)
    except BaseException as err:
        raise FSMBaseException("Couldn't load FortiSIEM Handler from mod_utils. Error: " + str(err))

    if paramgram["payload_file"]:
<<<<<<< HEAD
        paramgram["input_xml"] = fsm.get_report_source_from_file_path(paramgram["payload_file"])
>>>>>>> Full FSM Commit
=======
        paramgram["input_xml"] = fsm.get_file_contents(paramgram["payload_file"])
>>>>>>> Full FSM Commit. Ready for shippable tests.
=======
    try:
        fsm = FortiSIEMHandler(module)
    except BaseException as err:
        raise FSMBaseException("Couldn't load FortiSIEM Handler from mod_utils.")

    if paramgram["payload_file"]:
        paramgram["input_xml"] = fsm.get_report_source_from_file_path(paramgram["payload_file"])
>>>>>>> Full FSM Commit
        try:
            results = fsm.handle_simple_payload_request(paramgram["input_xml"])
        except BaseException as err:
            raise FSMBaseException(err)
    else:
        try:
            results = fsm.handle_simple_request()
        except BaseException as err:
            raise FSMBaseException(err)

    # EXIT USING GOVERN_RESPONSE()
    fsm.govern_response(module=module, results=results, changed=False,
                        ansible_facts=fsm.construct_ansible_facts(results["json_results"],
                                                                  module.params,
                                                                  paramgram))

<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
    return module.exit_json(msg=results)
=======
    return module.exit_json(DEFAULT_EXIT_MSG)
>>>>>>> Full FSM Commit
=======
    return module.exit_json(msg=results)
>>>>>>> Full FSM Commit. Ready for shippable tests.
=======
    return module.exit_json(DEFAULT_EXIT_MSG)
>>>>>>> Full FSM Commit


if __name__ == "__main__":
    main()
