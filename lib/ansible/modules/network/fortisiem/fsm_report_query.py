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
module: fsm_report_query
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
short_description: Allows the submission of reports and return of data
description:
  - Allows a user to submit report XML, or pick from a report in the library by name, and to get the data returned.

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

  export_xml_to_file_path:
    description:
      - When populated, an attempt to write XML to file is made.
      - An error will be thrown if this fails.
    required: false
    default: None

  export_csv_to_file_path:
    description:
      - When populated, an attempt to write CSV to file is made.
      - An error will be thrown if this fails.
    required: false
    default: None

  report_name:
    description:
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
      - Exact name match of a report in the CMDB that has been saved.
=======
      - Exact name match of a report in the CMDB that has been saved. 
>>>>>>> Full FSM Commit
=======
      - Exact name match of a report in the CMDB that has been saved.
>>>>>>> Full FSM Commit. Ready for shippable tests.
=======
      - Exact name match of a report in the CMDB that has been saved. 
>>>>>>> Full FSM Commit
      - Ansible will fetch XML from FortiSIEM before running.
    required: false

  report_string:
    description:
      - Specifies ad-hoc xml to be used if typed manually in playbook.
    required: false

  report_file_path:
    description:
      - Specifies PATH to File containing report XML.
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
  report_relative_mins:
    description:
      - Number of minutes of history to include in current report. Overrides any time filters in XML file path.
      - Mutually exclusive with report_absolute_ options.
    required: false

  report_absolute_begin_date:
    description:
      - Changes report time to begin date in MM/DD/YYYY format Overrides any time filters in XML file path.
      - Mutually exclusive with report_relative_mins
    required: false
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD

  report_absolute_begin_time:
    description:
      - Changes report time to begin time in 24h military format Overrides any time filters in XML file path.
      - Includes seconds, so there are six digits. First two are hours, second two are mins, third two are seconds.
      - Also accepts seconds in six-digit military. i.e. 103030
    required: false

=======
  
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
  report_absolute_begin_time:
    description:
      - Changes report time to begin time in 24h military format Overrides any time filters in XML file path.
      - Includes seconds, so there are six digits. First two are hours, second two are mins, third two are seconds.
      - Also accepts seconds in six-digit military. i.e. 103030
    required: false
<<<<<<< HEAD
  
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
=======
  
  report_absolute_begin_time:
    description:
      - Changes report time to begin time in 24h military format Overrides any time filters in XML file path.
      - Also accepts seconds in six-digit military. i.e. 103030
    required: false
  
>>>>>>> Full FSM Commit
  report_absolute_end_date:
    description:
      - Changes report time to end date in MM/DD/YYYY format Overrides any time filters in XML file path.
    required: false
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD

  report_absolute_end_time:
    description:
      - Changes report time to end time in 24h military format Overrides any time filters in XML file path.
      - Includes seconds, so there are six digits. First two are hours, second two are mins, third two are seconds.
=======
=======
>>>>>>> Full FSM Commit
  
  report_absolute_end_time:
    description:
      - Changes report time to end time in 24h military format Overrides any time filters in XML file path.
<<<<<<< HEAD
>>>>>>> Full FSM Commit
=======

  report_absolute_end_time:
    description:
      - Changes report time to end time in 24h military format Overrides any time filters in XML file path.
      - Includes seconds, so there are six digits. First two are hours, second two are mins, third two are seconds.
>>>>>>> Full FSM Commit. Ready for shippable tests.
=======
>>>>>>> Full FSM Commit
      - Also accepts seconds in six-digit military. i.e. 103030
    required: false

'''

EXAMPLES = '''
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> Full FSM Commit. Ready for shippable tests.
- name: SUBMIT REPORT
  fsm_report_query:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    ignore_ssl_errors: "enable"
    report_file_path: "/root/top_fortisiem_events_by_count.xml"
    export_json_to_file_path: "/root/report.json"
    export_xml_to_file_path: "/root/report.xml"
    export_csv_to_file_path: "/root/report.csv"

- name: GET REPORT WITH RELATIVE TIME DEFINED
  fsm_report_query:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    ignore_ssl_errors: "enable"
    report_file_path: "/root/top_fortisiem_events_by_count.xml"
    report_relative_mins: "60"

- name: GET REPORT WITH ABSOLUTE TIME DEFINED
  fsm_report_query:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    ignore_ssl_errors: "enable"
    report_file_path: "/root/top_fortisiem_events_by_count.xml"
    report_absolute_begin_date: "04/17/2019"
    report_absolute_begin_time: "060000"
    report_absolute_end_date: "04/17/2019"
    report_absolute_end_time: "070000"
<<<<<<< HEAD
=======

>>>>>>> Full FSM Commit
=======
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
from ansible.module_utils.network.fortisiem.common import FSMEndpoints
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

        report_name=dict(required=False, type="str"),
        report_string=dict(required=False, type="str"),
        report_file_path=dict(required=False, type="str"),
        report_relative_mins=dict(required=False, type="int"),
        report_absolute_begin_date=dict(required=False, type="str"),
        report_absolute_begin_time=dict(required=False, type="str"),
        report_absolute_end_date=dict(required=False, type="str"),
        report_absolute_end_time=dict(required=False, type="str"),

    )

    mututally_exclusive = [['report_name', 'report_string', 'report_file_pat'],
                           ['report_relative_mins', 'report_absolute_begin_date'],
                           ['report_relative_mins', 'report_absolute_begin_time'],
                           ['report_relative_mins', 'report_absolute_end_date'],
                           ['report_relative_mins', 'report_absolute_end_time'],
                           ]

    module = AnsibleModule(argument_spec, supports_check_mode=False, mutually_exclusive=mututally_exclusive)

    paramgram = {
        "host": module.params["host"],
        "username": module.params["username"],
        "password": module.params["password"],
        "export_json_to_screen": module.params["export_json_to_screen"],
        "export_json_to_file_path": module.params["export_json_to_file_path"],
        "export_xml_to_file_path": module.params["export_xml_to_file_path"],
        "export_csv_to_file_path": module.params["export_csv_to_file_path"],
        "ignore_ssl_errors": module.params["ignore_ssl_errors"],

        "report_name": module.params["report_name"],
        "report_string": module.params["report_string"],
        "report_file_path": module.params["report_file_path"],
        "report_relative_mins": module.params["report_relative_mins"],
        "report_absolute_begin_date": module.params["report_absolute_begin_date"],
        "report_absolute_begin_time": module.params["report_absolute_begin_time"],
        "report_absolute_end_date": module.params["report_absolute_end_date"],
        "report_absolute_end_time": module.params["report_absolute_end_time"],
        "uri": FSMEndpoints.PUT_SUBMIT_REPORT,
        "input_xml": None,
        "queryId": None
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
=======
=======
>>>>>>> Full FSM Commit
    try:
        fsm = FortiSIEMHandler(module)
    except BaseException as err:
        raise FSMBaseException("Couldn't load FortiSIEM Handler from mod_utils.")

    # TODO: FUTURE CODE
    # if paramgram["report_name"]:
    #     # CODE TO GO GET THE REPORT XML VIA QUERY
    #     paramgram["input_xml"] = fsm.get_report_source_from_api(paramgram["report_name"])
<<<<<<< HEAD
>>>>>>> Full FSM Commit
=======
    results = DEFAULT_EXIT_MSG
    try:
        fsm = FortiSIEMHandler(module)
    except BaseException as err:
        raise FSMBaseException("Couldn't load FortiSIEM Handler from mod_utils. Error: " + str(err))
>>>>>>> Full FSM Commit. Ready for shippable tests.
=======
>>>>>>> Full FSM Commit

    if paramgram["report_string"]:
        paramgram["input_xml"] = paramgram["report_string"]
    if paramgram["report_file_path"]:
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
        paramgram["input_xml"] = fsm.get_file_contents(paramgram["report_file_path"])

    # IF REPORT TIME PARAMETERS HAVE BEEN SET, THEN PROCESS THOSE, AND EDIT THE REPORT XML
    if paramgram["report_relative_mins"]:
        new_xml = fsm.replace_fsm_report_timestamp_relative()
        paramgram["input_xml"] = new_xml
    elif paramgram["report_absolute_begin_date"] and paramgram["report_absolute_begin_time"] \
            and paramgram["report_absolute_end_date"] and paramgram["report_absolute_end_time"]:
=======
        paramgram["input_xml"] = fsm.get_report_source_from_file_path(paramgram["report_file_path"])
=======
        paramgram["input_xml"] = fsm.get_file_contents(paramgram["report_file_path"])
>>>>>>> Full FSM Commit. Ready for shippable tests.

    # IF REPORT TIME PARAMETERS HAVE BEEN SET, THEN PROCESS THOSE, AND EDIT THE REPORT XML
    if paramgram["report_relative_mins"]:
        new_xml = fsm.replace_fsm_report_timestamp_relative()
        paramgram["input_xml"] = new_xml
    elif paramgram["report_absolute_begin_date"] and paramgram["report_absolute_begin_time"] \
<<<<<<< HEAD
        and paramgram["report_absolute_end_date"] and paramgram["report_absolute_end_time"]:
>>>>>>> Full FSM Commit
=======
            and paramgram["report_absolute_end_date"] and paramgram["report_absolute_end_time"]:
>>>>>>> Full FSM Commit. Ready for shippable tests.
=======
        paramgram["input_xml"] = fsm.get_report_source_from_file_path(paramgram["report_file_path"])

    # IF REPORT TIME PARAMETERS HAVE BEEN SET, THEN PROCESS THOSE, AND EDIT THE REPORT XML
    if paramgram["report_relative_mins"]:
        # current_timestamp = fsm.get_current_datetime()
        # end_epoch = fsm.convert_timestamp_to_epoch(current_timestamp)
        # start_epoch = fsm.get_relative_epoch(paramgram["report_relative_mins"])
        new_xml = fsm.replace_fsm_report_timestamp_relative()
        paramgram["input_xml"] = new_xml
    elif paramgram["report_absolute_begin_date"] and paramgram["report_absolute_begin_time"] \
        and paramgram["report_absolute_end_date"] and paramgram["report_absolute_end_time"]:
>>>>>>> Full FSM Commit
        new_xml = fsm.replace_fsm_report_timestamp_absolute()
        paramgram["input_xml"] = new_xml

    # CHECK IF INPUT XML IS ACTUALLY VALID XML
    try:
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
        fsm._tools.validate_xml(paramgram["input_xml"])
    except BaseException as err:
        raise FSMBaseException("XML Report Provided was unable to be parsed. "
                               "Please double check source XML. Error: " + str(err))
=======
        fsm.validate_xml(paramgram["input_xml"])
    except BaseException as err:
        raise FSMBaseException("XML Report Provided was unable to be parsed. Please double check source XML.")
>>>>>>> Full FSM Commit
=======
        fsm._tools.validate_xml(paramgram["input_xml"])
    except BaseException as err:
        raise FSMBaseException("XML Report Provided was unable to be parsed. "
                               "Please double check source XML. Error: " + str(err))
>>>>>>> Full FSM Commit. Ready for shippable tests.
=======
        fsm.validate_xml(paramgram["input_xml"])
    except BaseException as err:
        raise FSMBaseException("XML Report Provided was unable to be parsed. Please double check source XML.")
>>>>>>> Full FSM Commit
    # EXECUTE MODULE OPERATION
    try:
        results = fsm.handle_report_submission()
    except BaseException as err:
        raise FSMBaseException(err)
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD

=======
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
=======
>>>>>>> Full FSM Commit
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
