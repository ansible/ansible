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
module: fsm_verify_device_ip
<<<<<<< HEAD
version_added: "2.9"
=======
version_added: "2.8"
>>>>>>> Full FSM Commit
author: Luke Weighall (@lweighall)
short_description: Checks for the existence of a device in the FortiSIEM System.
description:
  - Allows a user to submit an IP address, and will return CMDB status, log status, and more.
  - A small report regarding its logs, and monitors, are returned.

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
    choices: ["enable", "disable"]
=======
    options: ["enable", "disable"]
>>>>>>> Full FSM Commit
=======
    choices: ["enable", "disable"]
>>>>>>> Full FSM Commit. Ready for shippable tests.

  export_json_to_screen:
    description:
      - When enabled this will print the JSON results to screen.
    required: false
    default: "enable"
<<<<<<< HEAD
<<<<<<< HEAD
    choices: ["enable", "disable"]
=======
    options: ["enable, "disable"]
>>>>>>> Full FSM Commit
=======
    choices: ["enable", "disable"]
>>>>>>> Full FSM Commit. Ready for shippable tests.

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

  ip_to_verify:
    description:
      - The IP Address you would like to verify is "in" the FortiSIEM system.
    required: true

  ip_list_to_verify:
    description:
      - A LIST of ip addresses or host names to verify in the FortiSIEM system.
      - i.e. ['10.0.0.5', '10.0.0.254']
    required: false
    type: list

  ip_list_file_path:
    description:
      - A line break-separated list of IP addresses or host names to check, stored in a file.
      - Defines file path
    required: false
<<<<<<< HEAD
<<<<<<< HEAD

=======
    
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
  append_results_to_file:
    description:
      - File path you want to keep appending test results to, specifically the IP, score, and verified status
    required: false
'''

EXAMPLES = '''
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> Full FSM Commit. Ready for shippable tests.
- name: VERIFY A DEVICE
  fsm_verify_device_ip:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    ignore_ssl_errors: "enable"
    ip_to_verify: "10.0.0.5"
    export_json_to_file_path: "/root/deviceExists.json"
    append_results_to_file: "/root/verification.csv"

- name: TEST VERIFY A DEVICE THAT DOESN'T EXIST
  fsm_verify_device_ip:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    ignore_ssl_errors: "enable"
    ip_to_verify: "10.0.0.45"
    export_json_to_file_path: "/root/deviceNoExist.json"
    append_results_to_file: "/root/verification.csv"
    export_json_to_screen: "enable"

- name: VERIFY A DEVICE FROM A LIST
  fsm_verify_device_ip:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    ignore_ssl_errors: "enable"
    ip_list_to_verify: ["10.0.0.5", "10.0.0.10", "10.0.0.254"]
    export_json_to_file_path: "/root/deviceExistsList.json"
    append_results_to_file: "/root/verificationList.csv"

- name: VERIFY A DEVICE LIST FROM FILE
  fsm_verify_device_ip:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    ignore_ssl_errors: "enable"
    ip_list_file_path: "/root/verify_list.txt"
    export_json_to_file_path: "/root/deviceExists.json"
    append_results_to_file: "/root/verificationList.csv"
<<<<<<< HEAD
=======
>>>>>>> Full FSM Commit
=======
>>>>>>> Full FSM Commit. Ready for shippable tests.

'''

RETURN = """
api_result:
  description: full API response, includes status code and message
  returned: always
<<<<<<< HEAD
<<<<<<< HEAD
  type: str
=======
  type: string
>>>>>>> Full FSM Commit
=======
  type: str
>>>>>>> Full FSM Commit. Ready for shippable tests.
"""

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.network.fortisiem.common import FSMEndpoints
from ansible.module_utils.network.fortisiem.common import FSMBaseException
from ansible.module_utils.network.fortisiem.common import DEFAULT_EXIT_MSG
from ansible.module_utils.network.fortisiem.fortisiem import FortiSIEMHandler
<<<<<<< HEAD
<<<<<<< HEAD
from ansible.module_utils.network.fortisiem.fsm_xml_generators import FSMXMLGenerators


def fsm_verify_single_device(fsm, paramgram):
    """
    Function runs a list of queries, and formats the results, and then judges the device based on a number
    of factors. The result is a score, basic status, and data-entities included.

    Only works on a single IP at a time. Must be put into an external loop for a list.

    :param fsm: the FSMHandlerObject class object created in this module
    :param paramgram: the paramgram generated by the module.

    :return: dict
    """
    # LOAD UP THE XML REQUIRED AND REPLACE TOKENS
    paramgram["input_xml"] = FSMXMLGenerators.RPT_ALL_DEVICES_EVENT_TYPE_COUNTS.replace('<IP_TO_VERIFY>',
                                                                                        str(paramgram["ip_to_verify"]))
=======
from ansible.module_utils.network.fortisiem.common import RPT_ALL_DEVICES_EVENT_TYPE_COUNTS
=======
from ansible.module_utils.network.fortisiem.fsm_xml_generators import FSMXMLGenerators
>>>>>>> Full FSM Commit. Ready for shippable tests.


def fsm_verify_single_device(fsm, paramgram):
    """
    Function runs a list of queries, and formats the results, and then judges the device based on a number
    of factors. The result is a score, basic status, and data-entities included.

    Only works on a single IP at a time. Must be put into an external loop for a list.

    :param fsm: the FSMHandlerObject class object created in this module
    :param paramgram: the paramgram generated by the module.

    :return: dict
    """
    # LOAD UP THE XML REQUIRED AND REPLACE TOKENS
<<<<<<< HEAD
    paramgram["input_xml"] = RPT_ALL_DEVICES_EVENT_TYPE_COUNTS.replace('<IP_TO_VERIFY>', str(paramgram["ip_to_verify"]))
>>>>>>> Full FSM Commit
=======
    paramgram["input_xml"] = FSMXMLGenerators.RPT_ALL_DEVICES_EVENT_TYPE_COUNTS.replace('<IP_TO_VERIFY>',
                                                                                        str(paramgram["ip_to_verify"]))
>>>>>>> Full FSM Commit. Ready for shippable tests.

    # QUERY FOR EVENTS
    events = None
    try:
        events = fsm.handle_report_submission()
<<<<<<< HEAD
<<<<<<< HEAD
    except BaseException:
=======
    except BaseException as err:
        # raise FSMBaseException(err)
>>>>>>> Full FSM Commit
=======
    except BaseException:
>>>>>>> Full FSM Commit. Ready for shippable tests.
        pass

    # QUERY FOR SINGLE CMDB STATUS
    paramgram["input_xml"] = None
    paramgram["uri"] = FSMEndpoints.GET_CMDB_DETAILED_SINGLE + paramgram["ip_to_verify"] + "&loadDepend=true"
    cmdb = None
    try:
        cmdb = fsm.handle_simple_request()
<<<<<<< HEAD
<<<<<<< HEAD
    except BaseException:
=======
    except BaseException as err:
        # raise FSMBaseException(err)
>>>>>>> Full FSM Commit
=======
    except BaseException:
>>>>>>> Full FSM Commit. Ready for shippable tests.
        pass

    # QUERY FOR MONITORS
    paramgram["uri"] = FSMEndpoints.GET_MONITORED_DEVICES
    monitors = None
    try:
        monitors = fsm.handle_simple_request()
<<<<<<< HEAD
<<<<<<< HEAD
        monitors = fsm._tools.get_monitors_info_for_specific_ip(monitors, paramgram["ip_to_verify"])
    except BaseException:
=======
        monitors = fsm.get_monitors_info_for_specific_ip(monitors, paramgram["ip_to_verify"])
    except BaseException as err:
        # raise FSMBaseException(err)
>>>>>>> Full FSM Commit
=======
        monitors = fsm._tools.get_monitors_info_for_specific_ip(monitors, paramgram["ip_to_verify"])
    except BaseException:
>>>>>>> Full FSM Commit. Ready for shippable tests.
        pass

    # CONCAT ALL THREE RESULTS INTO A SINGLE RESULTS DICT
    results = fsm.format_verify_judge_device_results(paramgram["ip_to_verify"], cmdb, events, monitors)

    return results


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

        ip_to_verify=dict(required=False, type="str"),
        ip_list_to_verify=dict(required=False, type="list"),
        ip_list_file_path=dict(required=False, type="str"),
        append_results_to_file=dict(required=False, type="str")
    )

    mutually_exclusive = ['ip_to_verify', 'ip_list_to_verify', 'ip_list_file_path']

    module = AnsibleModule(argument_spec, supports_check_mode=False, mutually_exclusive=mutually_exclusive, )

    paramgram = {
        "host": module.params["host"],
        "username": module.params["username"],
        "password": module.params["password"],
        "export_json_to_screen": module.params["export_json_to_screen"],
        "export_json_to_file_path": module.params["export_json_to_file_path"],
        "export_xml_to_file_path": module.params["export_xml_to_file_path"],
        "export_csv_to_file_path": module.params["export_csv_to_file_path"],
        "ignore_ssl_errors": module.params["ignore_ssl_errors"],

        "ip_to_verify": module.params["ip_to_verify"],
        "ip_list_to_verify": module.params["ip_list_to_verify"],
        "ip_list_file_path": module.params["ip_list_file_path"],
        "append_results_to_file": module.params["append_results_to_file"],
        "uri": FSMEndpoints.PUT_SUBMIT_REPORT,
        "input_xml": None,
        "queryId": None
    }

    module.paramgram = paramgram

    # TRY TO INIT THE CONNECTION SOCKET PATH AND FortiManagerHandler OBJECT AND TOOLS
    fsm = None
<<<<<<< HEAD
<<<<<<< HEAD
    results = DEFAULT_EXIT_MSG
    results_list = list()
    try:
        fsm = FortiSIEMHandler(module)
    except BaseException as err:
        raise FSMBaseException("Couldn't load FortiSIEM Handler from mod_utils. Error: " + str(err))
=======
    try:
        fsm = FortiSIEMHandler(module)
    except BaseException as err:
        raise FSMBaseException("Couldn't load FortiSIEM Handler from mod_utils.")

    #pydevd.settrace('10.0.0.151', port=54654, stdoutToServer=True, stderrToServer=True)
>>>>>>> Full FSM Commit
=======
    results = DEFAULT_EXIT_MSG
    results_list = list()
    try:
        fsm = FortiSIEMHandler(module)
    except BaseException as err:
        raise FSMBaseException("Couldn't load FortiSIEM Handler from mod_utils. Error: " + str(err))
>>>>>>> Full FSM Commit. Ready for shippable tests.

    if paramgram["ip_to_verify"]:
        results = fsm_verify_single_device(fsm, paramgram)

    if paramgram["ip_list_file_path"] or paramgram["ip_list_to_verify"]:
        if paramgram["ip_list_to_verify"]:
            if isinstance(paramgram["ip_list_to_verify"], list):
<<<<<<< HEAD
<<<<<<< HEAD
=======
                results_list = list()
>>>>>>> Full FSM Commit
=======
>>>>>>> Full FSM Commit. Ready for shippable tests.
                for ip in paramgram["ip_list_to_verify"]:
                    if ip != "" and ip is not None:
                        paramgram["ip_to_verify"] = str(ip)
                        results_add = fsm_verify_single_device(fsm, paramgram)
                        results_list.append(results_add)

        if paramgram["ip_list_file_path"]:
            results_list = list()
<<<<<<< HEAD
<<<<<<< HEAD
            ip_list = fsm.get_file_contents(paramgram["ip_list_file_path"])
=======
            ip_list = fsm.get_report_source_from_file_path(paramgram["ip_list_file_path"])
>>>>>>> Full FSM Commit
=======
            ip_list = fsm.get_file_contents(paramgram["ip_list_file_path"])
>>>>>>> Full FSM Commit. Ready for shippable tests.
            parsed_ip_list = ip_list.split("\n")
            for ip in parsed_ip_list:
                if ip != "" and ip is not None:
                    paramgram["ip_to_verify"] = str(ip)
                    results_add = fsm_verify_single_device(fsm, paramgram)
                    results_list.append(results_add)

        results = {
            "rc": 200,
            "json_results": {"all_results": results_list},
            "xml_results": {"all_results": results_list},
        }

    # WRITE TO THE FILE IF SPECIFIED
<<<<<<< HEAD
<<<<<<< HEAD
=======

>>>>>>> Full FSM Commit
=======
>>>>>>> Full FSM Commit. Ready for shippable tests.
    try:
        if paramgram["append_results_to_file"]:
            try:
                if results["json_results"]["all_results"]:
                    for result in results["json_results"]["all_results"]:
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> Full FSM Commit. Ready for shippable tests.
                        fsm._tools.append_file_with_device_results(result, paramgram["append_results_to_file"])
            except BaseException:
                try:
                    fsm._tools.append_file_with_device_results(results,
                                                               paramgram["append_results_to_file"])
                except BaseException as err:
                    raise FSMBaseException(msg="An issue happened writing the results to a file. Error: " + str(err))
<<<<<<< HEAD
    except BaseException as err:
        raise FSMBaseException(msg="An issue happened writing the results to a file. Error: " + str(err))
=======
                        fsm.append_file_with_device_results(result, paramgram["append_results_to_file"])
            except BaseException as err:
                raise FSMBaseException(err)
            try:
                if not results["json_results"]["all_results"]:
                    fsm.append_file_with_device_results(results["json_results"], paramgram["append_results_to_file"])
            except BaseException as err:
                raise FSMBaseException(err)
    except BaseException as err:
        raise FSMBaseException(err)
>>>>>>> Full FSM Commit
=======
    except BaseException as err:
        raise FSMBaseException(msg="An issue happened writing the results to a file. Error: " + str(err))
>>>>>>> Full FSM Commit. Ready for shippable tests.

    # EXIT USING GOVERN_RESPONSE()
    fsm.govern_response(module=module, results=results, changed=False,
                        ansible_facts=fsm.construct_ansible_facts(results["json_results"],
                                                                  module.params,
                                                                  paramgram))

<<<<<<< HEAD
<<<<<<< HEAD
    return module.exit_json(msg=results)
=======

    return module.exit_json(msg=DEFAULT_EXIT_MSG)
>>>>>>> Full FSM Commit
=======
    return module.exit_json(msg=results)
>>>>>>> Full FSM Commit. Ready for shippable tests.


if __name__ == "__main__":
    main()
