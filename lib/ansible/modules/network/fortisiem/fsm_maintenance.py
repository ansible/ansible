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
module: fsm_maintenance
version_added: "2.8"
author: Luke Weighall (@lweighall)
short_description: Creates and Deletes maintenance calendar objects.
description:
  - Creates and Deletes maintenance calendar objects.

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

  input_xml_file:
    description:
      - If defined, all other options are ignored. The XML in the file path specified is strictly used.
    required: false

  mode:
    description:
      - Defines which operation to use (add or delete).
    required: false
    default: "add"
    choices: ["add", "delete"]
    
  name:
    description:
      - Friendly Name of Schedule Entry.
    required: true

  description:
    description:
      - Description of the Schedule Entry.
    required: false

  devices:
    description:
      - Comma seperated list of IP addresses to put into maintenance mode.
    required: false

  groups:
    description:
      - Comma seperated list of Group Names to put into maintenance mode.
    required: false

  fire_incidents:
    description:
      - Decides whether or not to fire incidents for devices during the maintenance mode.
    required: false
    type: bool

  time_zone_id:
    description:
      - The linux string version of the timezone.
      - i.e. America/Los Angeles
    required: false

  start_hour:
    description:
      - The 24-hour format hour of when the maintenance period should begin.
    required: true

  start_min:
    description:
      - The xx digit version of minutes when the maintenance period should begin..
    required: true

  duration:
    description:
      - The duration in minutes the maintenance period should last.
    required: true

  time_zone:
    description:
      - The integer value of the relative timezone to GMT.
      - i.e. -8 for NA/Pacific or -5 for NA/EastCoast or 0 for GMT
    required: true

  start_date:
    description:
      - The start date of the maintenance period in YYYY-MM-DD format.
    required: true

  end_date:
    description:
      - The end date of the maintenance period in YYYY-MM-DD format.
      - Optional if end_date_open = True
    required: false

  end_date_open:
    description:
      - If no end_date is required then specify as true.
      - When true then end_date is ignored.
    required: false
    default: False
    type: bool    
'''


EXAMPLES = '''
  

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
        input_xml_file=dict(required=False, type="str"),
        mode=dict(required=False, type="str", default="add", choices=["add", "delete"]),
        name=dict(required=False, type="str"),
        description=dict(required=False, type="str"),
        devices=dict(required=False, type="str"),
        groups=dict(required=False, type="str"),
        fire_incidents=dict(required=False, type="bool"),
        time_zone_id=dict(required=False, type="str"),
        start_hour=dict(required=False, type="str"),
        start_min=dict(required=False, type="str"),
        duration=dict(required=False, type="str"),
        time_zone=dict(required=False, type="str"),
        start_date=dict(required=False, type="str"),
        end_date=dict(required=False, type="str"),
        end_date_open=dict(required=False, type="bool"),

    )

    module = AnsibleModule(argument_spec, supports_check_mode=False)

    paramgram = {
        "host": module.params["host"],
        "username": module.params["username"],
        "password": module.params["password"],
        "export_json_to_screen": module.params["export_json_to_screen"],
        "export_json_to_file_path": module.params["export_json_to_file_path"],
        "export_xml_to_file_path": module.params["export_xml_to_file_path"],
        "export_csv_to_file_path": module.params["export_csv_to_file_path"],
        "ignore_ssl_errors": module.params["ignore_ssl_errors"],
        "input_xml_file": module.params["input_xml_file"],
        "mode": module.params["mode"],
        "name": module.params["name"],
        "description": module.params["description"],
        "devices": module.params["devices"],
        "groups": module.params["groups"],
        "fire_incidents": module.params["fire_incidents"],
        "time_zone_id": module.params["time_zone_id"],
        "start_hour": module.params["start_hour"],
        "start_min": module.params["start_min"],
        "duration": module.params["duration"],
        "time_zone": module.params["time_zone"],
        "start_date": module.params["start_date"],
        "end_date": module.params["end_date"],
        "end_date_open": module.params["end_date_open"],

        "uri": None,
        "input_xml": None,
    }

    if not paramgram["end_date_open"]:
        paramgram["end_date_open"] = False
    module.paramgram = paramgram

    # TRY TO INIT THE CONNECTION SOCKET PATH AND FortiManagerHandler OBJECT AND TOOLS
    fsm = None
    try:
        fsm = FortiSIEMHandler(module)
    except BaseException as err:
        raise FSMBaseException("Couldn't load FortiSIEM Handler from mod_utils.")

    #pydevd.settrace('10.0.0.151', port=54654, stdoutToServer=True, stderrToServer=True)
    # EXECUTE THE MODULE OPERATION
    if paramgram["mode"] == "add":
        paramgram["uri"] = FSMEndpoints.SET_MAINTENANCE
        try:
            if paramgram["input_xml_file"]:
                paramgram["input_xml"] = fsm.get_report_source_from_file_path(paramgram["input_xml_file"])
            else:
                paramgram["input_xml"] = fsm.create_maint_payload()
            results = fsm.handle_simple_payload_request(paramgram["input_xml"])
        except BaseException as err:
            raise FSMBaseException(err)
    elif paramgram["mode"] == "delete":
        paramgram["uri"] = FSMEndpoints.DEL_MAINTENANCE
        try:
            if paramgram["input_xml_file"]:
                paramgram["input_xml"] = fsm.get_report_source_from_file_path(paramgram["input_xml_file"])
            else:
                paramgram["input_xml"] = fsm.create_maint_payload()
            results = fsm.handle_simple_payload_request(paramgram["input_xml"])
        except BaseException as err:
            raise FSMBaseException(err)


    # EXIT USING GOVERN_RESPONSE()
    fsm.govern_response(module=module, results=results, changed=False, good_codes=[200,204,],
                        ansible_facts=fsm.construct_ansible_facts(results["json_results"],
                                                                  module.params,
                                                                  paramgram))

    return module.exit_json(DEFAULT_EXIT_MSG)


if __name__ == "__main__":
    main()
