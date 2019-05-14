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

=======
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
__metaclass__ = type

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community"
}

DOCUMENTATION = '''
---
module: fsm_discovery
<<<<<<< HEAD
version_added: "2.9"
=======
version_added: "2.8"
>>>>>>> Full FSM Commit
author: Luke Weighall (@lweighall)
short_description: Submits and Queries for Discovery Tasks.
description:
  - Able to submit ad-hoc discoveries and query for the results of any task ID that was a discovery.

options:
  host:
    description:
      - The FortiSIEM's FQDN or IP Address.
    required: true
<<<<<<< HEAD
<<<<<<< HEAD

=======
    
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
  username:
    description:
      - The username used to authenticate with the FortiManager.
      - organization/username format. The Organization is important, and will only return data from specified Org.
    required: false
<<<<<<< HEAD
<<<<<<< HEAD

=======
    
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
  password:
    description:
      - The password associated with the username account.
    required: false
<<<<<<< HEAD
<<<<<<< HEAD

=======
    
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
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
<<<<<<< HEAD
<<<<<<< HEAD

=======
    
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
  export_xml_to_file_path:
    description:
      - When populated, an attempt to write XML to file is made.
      - An error will be thrown if this fails.
    required: false
    default: None

  wait_to_finish:
    description:
      - When enabled, the module will WAIT until the discovery actually finishes.
        This may or may not be desired depending on how big the discovery range is.
      - When disabled, the module will simply submit the discovery and exit.
        You'll have to record the task ID that was exported, and re-run the module with type = status.
    required: false
    default: "enable"
    choices: ["enable", "disable"]

  type:
    description:
      - Discovery type to use in FortiSIEM.
    required: true
<<<<<<< HEAD
<<<<<<< HEAD
    choices: ["RangeScan", "SmartScan", "L2Scan", "status"]

=======
    options: ["RangeScan", "SmartScan", "L2Scan", "status"]
    
>>>>>>> Full FSM Commit
=======
    choices: ["RangeScan", "SmartScan", "L2Scan", "status"]

>>>>>>> Full FSM Commit. Ready for shippable tests.
  root_ip:
    description:
      - Specifies the IP of a device to use as the "root" scanning device. Usually a router or switch.
      - Ignored unless "SmartScan" is set for mode
    required: false
<<<<<<< HEAD
<<<<<<< HEAD

  include_range:
    description:
      - Specifies the IP ranges to specify, in comma seperated format.
    required: false

  exclude_range:
    description:
      - Specifies the IP ranges to specify, in comma seperated format.
    required: false

=======
    
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
  include_range:
    description:
      - Specifies the IP ranges to specify, in comma seperated format.
    required: false

  exclude_range:
    description:
      - Specifies the IP ranges to specify, in comma seperated format.
    required: false
<<<<<<< HEAD
    
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
  no_ping:
    description:
      - Tells FortiSIEM not to attempt to ping a device before attempting to discover it.
      - Useful when ICMP is blocked on target devices.
    required: false
    default: false
    type: bool
<<<<<<< HEAD
<<<<<<< HEAD

=======
    
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
  only_ping:
    description:
      - Tells FortiSIEM to only discover devices with ICMP pings.
    required: false
    default: false
    type: bool
<<<<<<< HEAD
<<<<<<< HEAD

=======
    
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
  task_id:
    description:
      - Tells the module which task ID to query for when type = status.
    required: false
    type: int
<<<<<<< HEAD
<<<<<<< HEAD

=======
    
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
  delta:
    description:
      - Only discovers new devices.
    required: false
    default: false
    type: bool
<<<<<<< HEAD
<<<<<<< HEAD

=======
    
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
  vm_off:
    description:
      - Doesn't discover VMs.
    required: false
    default: false
    type: bool
<<<<<<< HEAD
<<<<<<< HEAD

=======
    
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
  vm_templates:
    description:
      - Discover VM templates.
    required: false
    default: false
    type: bool
<<<<<<< HEAD
<<<<<<< HEAD

=======
    
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
  discover_routes:
    description:
      - Discovers routes and follows those in smart scans.
    required: false
    default: true
    type: bool
<<<<<<< HEAD
<<<<<<< HEAD

=======
    
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
  winexe_based:
    description:
      - Discovers windows boxes with winExe.
    required: false
    default: false
    type: bool
<<<<<<< HEAD
<<<<<<< HEAD

=======
    
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
  unmanaged:
    description:
      - Sets newly discovered devices to unmanaged.
    required: false
    default: false
    type: bool
<<<<<<< HEAD
<<<<<<< HEAD

=======
    
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
  monitor_win_events:
    description:
      - Turns on or off Windows Event log mointor for newly discovered devices.
    required: false
    default: true
    type: bool
<<<<<<< HEAD
<<<<<<< HEAD

=======
    
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
  monitor_win_patches:
    description:
      - Turns on or off Windows Patching logging.
    required: false
    default: true
    type: bool
<<<<<<< HEAD
<<<<<<< HEAD

=======
    
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
  monitor_installed_sw:
    description:
      - Turns on or off Windows Installed Software monitoring.
    required: false
    default: true
    type: bool
<<<<<<< HEAD
<<<<<<< HEAD

=======
    
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
  name_resolution_dns_first:
    description:
      - Specifies to use DNS for name resolution first, and then SNMP/NETBIOS/SSH.
      - When false, uses SNMP/NETBIOS/SSH first, then DNS
    required: false
    default: true
    type: bool
<<<<<<< HEAD
<<<<<<< HEAD

'''

EXAMPLES = '''
- name: SUBMIT RANGE SCAN FOR SINGLE DEVICE
  fsm_discovery:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    ignore_ssl_errors: "enable"
    export_json_to_screen: "enable"
    export_json_to_file_path: "/root/range_scan.json"
    export_xml_to_file_path: "/root/range_scan.xml"
    type: "RangeScan"
    include_range: "10.0.0.254"

- name: SUBMIT RANGE SCAN FOR SINGLE DEVICE AND WAIT FOR FINISH WITH MANY OPTIONS
  fsm_discovery:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    ignore_ssl_errors: "enable"
    export_json_to_screen: "enable"
    export_json_to_file_path: "/root/range_scan2.json"
    export_xml_to_file_path: "/root/range_scan2.xml"
    type: "RangeScan"
    include_range: "10.0.0.5-10.0.0.20"
    wait_to_finish: True
    only_ping: False
    vm_off: True
    unmanaged: True
    delta: True
    name_resolution_dns_first: False
    winexe_based: True
    vm_templates: True
    discover_routes: True
    monitor_win_events: False
    monitor_win_patches: False
    monitor_installed_sw: False

- name: SUBMIT RANGE SCAN FOR SINGLE DEVICE AND WAIT FOR FINISH WITH NO PING
  fsm_discovery:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    ignore_ssl_errors: "enable"
    export_json_to_screen: "enable"
    export_json_to_file_path: "/root/json_test_out.json"
    export_xml_to_file_path: "/root/xml_test_out.xml"
    type: "RangeScan"
    include_range: "10.0.0.5-10.0.0.50"
    wait_to_finish: True
    no_ping: True


- name: SUBMIT RANGE SCAN FOR RANGE OF DEVICES
  fsm_discovery:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    ignore_ssl_errors: "enable"
    export_json_to_screen: "enable"
    export_json_to_file_path: "/root/json_test_out.json"
    export_xml_to_file_path: "/root/xml_test_out.xml"
    type: "RangeScan"
    include_range: "10.0.0.1-10.0.0.10"
    exclude_range: "10.0.0.5-10.0.0.6"

- name: SUBMIT SMART SCAN
  fsm_discovery:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    ignore_ssl_errors: "enable"
    export_json_to_screen: "enable"
    export_json_to_file_path: "/root/json_test_out.json"
    export_xml_to_file_path: "/root/xml_test_out.xml"
    type: "SmartScan"
    root_ip: "10.0.0.254"

- name: SUBMIT L2SCAN
  fsm_discovery:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    ignore_ssl_errors: "enable"
    export_json_to_screen: "enable"
    export_json_to_file_path: "/root/json_test_out.json"
    export_xml_to_file_path: "/root/xml_test_out.xml"
    type: "L2Scan"
    include_range: "10.0.0.1-10.0.0.254"
=======
    
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
'''

EXAMPLES = '''
- name: SUBMIT RANGE SCAN FOR SINGLE DEVICE
  fsm_discovery:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    ignore_ssl_errors: "enable"
    export_json_to_screen: "enable"
    export_json_to_file_path: "/root/range_scan.json"
    export_xml_to_file_path: "/root/range_scan.xml"
    type: "RangeScan"
    include_range: "10.0.0.254"

- name: SUBMIT RANGE SCAN FOR SINGLE DEVICE AND WAIT FOR FINISH WITH MANY OPTIONS
  fsm_discovery:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    ignore_ssl_errors: "enable"
    export_json_to_screen: "enable"
    export_json_to_file_path: "/root/range_scan2.json"
    export_xml_to_file_path: "/root/range_scan2.xml"
    type: "RangeScan"
    include_range: "10.0.0.5-10.0.0.20"
    wait_to_finish: True
    only_ping: False
    vm_off: True
    unmanaged: True
    delta: True
    name_resolution_dns_first: False
    winexe_based: True
    vm_templates: True
    discover_routes: True
    monitor_win_events: False
    monitor_win_patches: False
    monitor_installed_sw: False

- name: SUBMIT RANGE SCAN FOR SINGLE DEVICE AND WAIT FOR FINISH WITH NO PING
  fsm_discovery:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    ignore_ssl_errors: "enable"
    export_json_to_screen: "enable"
    export_json_to_file_path: "/root/json_test_out.json"
    export_xml_to_file_path: "/root/xml_test_out.xml"
    type: "RangeScan"
    include_range: "10.0.0.5-10.0.0.50"
    wait_to_finish: True
    no_ping: True


- name: SUBMIT RANGE SCAN FOR RANGE OF DEVICES
  fsm_discovery:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    ignore_ssl_errors: "enable"
    export_json_to_screen: "enable"
    export_json_to_file_path: "/root/json_test_out.json"
    export_xml_to_file_path: "/root/xml_test_out.xml"
    type: "RangeScan"
    include_range: "10.0.0.1-10.0.0.10"
    exclude_range: "10.0.0.5-10.0.0.6"

- name: SUBMIT SMART SCAN
  fsm_discovery:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    ignore_ssl_errors: "enable"
    export_json_to_screen: "enable"
    export_json_to_file_path: "/root/json_test_out.json"
    export_xml_to_file_path: "/root/xml_test_out.xml"
    type: "SmartScan"
    root_ip: "10.0.0.254"

<<<<<<< HEAD
>>>>>>> Full FSM Commit
=======
- name: SUBMIT L2SCAN
  fsm_discovery:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    ignore_ssl_errors: "enable"
    export_json_to_screen: "enable"
    export_json_to_file_path: "/root/json_test_out.json"
    export_xml_to_file_path: "/root/xml_test_out.xml"
    type: "L2Scan"
    include_range: "10.0.0.1-10.0.0.254"
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
import time
from ansible.module_utils.network.fortisiem.common import FSMEndpoints
from ansible.module_utils.network.fortisiem.common import FSMBaseException
from ansible.module_utils.network.fortisiem.common import DEFAULT_EXIT_MSG
from ansible.module_utils.network.fortisiem.fortisiem import FortiSIEMHandler

<<<<<<< HEAD
<<<<<<< HEAD
=======
import pydevd
>>>>>>> Full FSM Commit
=======
>>>>>>> Full FSM Commit. Ready for shippable tests.

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

        wait_to_finish=dict(required=False, type="bool", default="false"),
        type=dict(required=True, type="str",
                  choices=["RangeScan", "SmartScan", "L2Scan", "status"]),
        root_ip=dict(required=False, type="str"),
        include_range=dict(required=False, type="str"),
        exclude_range=dict(required=False, type="str"),
        no_ping=dict(required=False, type="bool", default="false"),
        only_ping=dict(required=False, type="bool", default="false"),
        task_id=dict(required=False, type="int"),
        delta=dict(required=False, type="bool", default="false"),
        vm_off=dict(required=False, type="bool", default="false"),
        vm_templates=dict(required=False, type="bool", default="false"),
        discover_routes=dict(required=False, type="bool", default="true"),
        winexe_based=dict(required=False, type="bool", default="false"),
        unmanaged=dict(required=False, type="bool", default="false"),
        monitor_win_events=dict(required=False, type="bool", default="true"),
        monitor_win_patches=dict(required=False, type="bool", default="true"),
        monitor_installed_sw=dict(required=False, type="bool", default="true"),
        name_resolution_dns_first=dict(required=False, type="bool", default="true"),
    )

    required_if = [
        ['type', 'SmartScan', ['root_ip']],
        ['type', 'RangeScan', ['include_range']],
        ['type', 'L2Scan', ['include_range']],
        ['type', 'status', ['task_id']],
    ]

    module = AnsibleModule(argument_spec, supports_check_mode=False, required_if=required_if)

    paramgram = {
        "host": module.params["host"],
        "username": module.params["username"],
        "password": module.params["password"],
        "export_json_to_screen": module.params["export_json_to_screen"],
        "export_json_to_file_path": module.params["export_json_to_file_path"],
        "export_xml_to_file_path": module.params["export_xml_to_file_path"],
        "export_csv_to_file_path": module.params["export_csv_to_file_path"],
        "ignore_ssl_errors": module.params["ignore_ssl_errors"],

        "type": module.params["type"],
        "wait_to_finish": module.params["wait_to_finish"],
        "root_ip": module.params["root_ip"],
        "include_range": module.params["include_range"],
        "exclude_range": module.params["exclude_range"],
        "no_ping": module.params["no_ping"],
        "only_ping": module.params["only_ping"],
        "task_id": module.params["task_id"],
        "delta": module.params["delta"],
        "vm_off": module.params["vm_off"],
        "vm_templates": module.params["vm_templates"],
        "discover_routes": module.params["discover_routes"],
        "winexe_based": module.params["winexe_based"],
        "unmanaged": module.params["unmanaged"],
        "monitor_win_events": module.params["monitor_win_events"],
        "monitor_win_patches": module.params["monitor_win_patches"],
        "monitor_installed_sw": module.params["monitor_installed_sw"],
        "name_resolution_dns_first": module.params["name_resolution_dns_first"],

        "uri": FSMEndpoints.SET_DISCOVERY,
        "input_xml": None
    }

    module.paramgram = paramgram

    # TRY TO INIT THE CONNECTION SOCKET PATH AND FortiManagerHandler OBJECT AND TOOLS
    fsm = None
<<<<<<< HEAD
<<<<<<< HEAD
    results = DEFAULT_EXIT_MSG
    try:
        fsm = FortiSIEMHandler(module)
    except BaseException as err:
        raise FSMBaseException("Couldn't load FortiSIEM Handler from mod_utils. Error: " + str(err))
=======
    try:
        fsm = FortiSIEMHandler(module)
    except BaseException as err:
        raise FSMBaseException("Couldn't load FortiSIEM Handler from mod_utils.")
>>>>>>> Full FSM Commit
=======
    results = DEFAULT_EXIT_MSG
    try:
        fsm = FortiSIEMHandler(module)
    except BaseException as err:
        raise FSMBaseException("Couldn't load FortiSIEM Handler from mod_utils. Error: " + str(err))
>>>>>>> Full FSM Commit. Ready for shippable tests.

    # EXECUTE THE MODULE OPERATION
    # SEND THE DISCOVERY XML PAYLOAD
    if paramgram["type"] != "status":
<<<<<<< HEAD
<<<<<<< HEAD
        paramgram["input_xml"] = fsm._xml.create_discover_payload()
=======
        paramgram["input_xml"] = fsm.create_discover_payload()
        #pydevd.settrace('10.0.0.151', port=54654, stdoutToServer=True, stderrToServer=True)
>>>>>>> Full FSM Commit
=======
        paramgram["input_xml"] = fsm._xml.create_discover_payload()
>>>>>>> Full FSM Commit. Ready for shippable tests.
        try:
            results = fsm.handle_simple_payload_request(paramgram["input_xml"])
        except BaseException as err:
            raise FSMBaseException(err)

        # REFACTOR THE GENERIC RESPONSE BECAUSE IT WASN'T STRUCTURED BY FORTISIEM IN AN XML RESPONSE
        # RECORD THE TASK ID
        try:
            paramgram["task_id"] = results["json_results"]["fsm_response"]
            del results["json_results"]["fsm_response"]
            results["json_results"]["task_id"] = paramgram["task_id"]
            results["xml_results"] = "<task_id>" + str(paramgram["task_id"]) + "</task_id>"
        except BaseException as err:
            raise FSMBaseException(msg="Couldn't extract discovery task ID from response! Error: " + str(err))

    # START THE STATUS CHECKING PORTION
    if paramgram["type"] == "status" or paramgram["wait_to_finish"]:
        if not paramgram["task_id"]:
            raise FSMBaseException(msg="fsm_discovery was called to status "
                                       "or wait_to_finish but the task ID was empty")
        if paramgram["task_id"]:
            paramgram["uri"] = FSMEndpoints.GET_DISCOVERY + str(paramgram["task_id"])
            module.paramgram = paramgram
            try:
                results = fsm.handle_simple_request()
            except BaseException as err:
                raise FSMBaseException(msg="Failed to get status of task ID: " +
                                           str(paramgram["task_id"]) + " - Error: " + str(err))

            # PROCESS WAIT TO FINISH!
            if paramgram["wait_to_finish"]:
<<<<<<< HEAD
<<<<<<< HEAD
=======
                #pydevd.settrace('10.0.0.151', port=54654, stdoutToServer=True, stderrToServer=True)
>>>>>>> Full FSM Commit
=======
>>>>>>> Full FSM Commit. Ready for shippable tests.
                try:
                    task_status_result = results["json_results"]["fsm_response"].split(":")

                    # SLEEP FOR 5 SECOND INTERVALS AND KEEP CHECKING UNTIL PROGRESS IS 100%
                    while task_status_result[1] != "Done":
                        time.sleep(5)
                        try:
                            results = fsm.handle_simple_request()
                        except BaseException as err:
                            raise FSMBaseException(msg="Failed to get status of task ID: " +
                                                       str(paramgram["task_id"]) + " - Error: " + str(err))
                        try:
                            if results["json_results"]["taskResults"]:
                                task_status_result = [str(paramgram["task_id"]), "Done"]
<<<<<<< HEAD
<<<<<<< HEAD
                        except BaseException:
=======
                        except:
>>>>>>> Full FSM Commit
=======
                        except BaseException:
>>>>>>> Full FSM Commit. Ready for shippable tests.
                            try:
                                task_status_result = results["json_results"]["fsm_response"].split(":")
                            except BaseException as err:
                                raise FSMBaseException(err)
<<<<<<< HEAD
<<<<<<< HEAD
                except BaseException:
=======
                except BaseException as err:
>>>>>>> Full FSM Commit
=======
                except BaseException:
>>>>>>> Full FSM Commit. Ready for shippable tests.
                    try:
                        if results["json_results"]["taskResults"]:
                            pass
                    except BaseException as err:
<<<<<<< HEAD
<<<<<<< HEAD
                        raise FSMBaseException(msg="Something happened while looping "
                                                   "for the status. Error: " + str(err))
=======
                        raise FSMBaseException(msg="Something happened while looping for the status. Error: " + str(err))
>>>>>>> Full FSM Commit
=======
                        raise FSMBaseException(msg="Something happened while looping "
                                                   "for the status. Error: " + str(err))
>>>>>>> Full FSM Commit. Ready for shippable tests.
                    pass

    # EXIT USING GOVERN_RESPONSE()
    fsm.govern_response(module=module, results=results, changed=False,
                        ansible_facts=fsm.construct_ansible_facts(results["json_results"],
                                                                  module.params,
                                                                  paramgram))

<<<<<<< HEAD
<<<<<<< HEAD
    return module.exit_json(msg=results)
=======
    return module.exit_json(DEFAULT_EXIT_MSG)
>>>>>>> Full FSM Commit
=======
    return module.exit_json(msg=results)
>>>>>>> Full FSM Commit. Ready for shippable tests.


if __name__ == "__main__":
    main()
