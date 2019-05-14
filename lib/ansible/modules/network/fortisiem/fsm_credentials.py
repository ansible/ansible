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
<<<<<<< HEAD

=======
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
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
module: fsm_credentials
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
short_description: Adds or Updates Credentials in FortiSIEM.
description:
  - Adds or Updates Credentials in FortiSIEM.

options:
  host:
    description:
      - The FortiSIEM's FQDN or IP Address.
    required: true
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD

=======
    
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
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
<<<<<<< HEAD
<<<<<<< HEAD

=======
    
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
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
<<<<<<< HEAD
<<<<<<< HEAD

=======
    
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
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
<<<<<<< HEAD
<<<<<<< HEAD

=======
    
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
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
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD

  mode:
    description:
      - Defines the HTTP method used in the playbook.
      - When updating friendly_name is the primary key.
    required: false
    default: "add"
    choices: ["add", "update", "get"]

=======
    
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
  mode:
    description:
      - Defines the HTTP method used in the playbook.
      - When updating friendly_name is the primary key.
    required: false
    default: "add"
<<<<<<< HEAD
    options: ["add", "update", "get"]
    
>>>>>>> Full FSM Commit
=======
    choices: ["add", "update", "get"]

>>>>>>> Full FSM Commit. Ready for shippable tests.
=======
    
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
  mode:
    description:
      - Defines the HTTP method used in the playbook.
      - When updating friendly_name is the primary key.
    required: false
    default: "add"
<<<<<<< HEAD
    options: ["add", "update", "get"]
    
>>>>>>> Full FSM Commit
=======
    choices: ["add", "update", "get"]

>>>>>>> Full FSM Commit. Ready for shippable tests.
  input_xml_file:
    description:
      - If defined, all other options are ignored. The XML in the file path specified is strictly used.
    required: false
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD

=======
    
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
=======
    
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
  access_protocol:
    description:
      - Defines the access protocol in use. Also plays a large role in included/excluded parameters.
    required: true
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
    choices:
=======
    choices: 
>>>>>>> Full FSM Commit
=======
    choices:
>>>>>>> Full FSM Commit. Ready for shippable tests.
=======
    choices: 
>>>>>>> Full FSM Commit
=======
    choices:
>>>>>>> Full FSM Commit. Ready for shippable tests.
      - ftp
      - ftp_over_ssl
      - imap
      - imap_over_ssl
      - jdbc
      - jmx
      - pop3
      - pop3_over_ssl
      - smtp
      - smtp_over_ssl
      - smtp_over_tls
      - ssh
      - telnet
      - vm_sdk

  ip_range:
    description:
      - The IP range(s) you want to map x.x.x.x or x.x.x.x-x.x.x.x, comma seperated.
      - Used in "add" and "map" modes
    required: false

  access_id:
    description:
      - The Access_ID of the credential you want to map.
      - Only used when mode is "map"
    required: false
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD

=======
    
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
=======
    
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
  friendly_name:
    description:
      - Specifies the friendly name specified for the credential.
      - Required when mode equals get.
    required: false

  description:
    description:
      - Specifies the description for the credential
    required: false
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD

=======
    
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
=======
    
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
  pull_interval:
    description:
      - Specifies the pull interval for any monitors created as a result of this credential..
    required: false
    default: 5
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD

=======
    
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
=======
    
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
  cred_username:
    description:
      - Specifies the username for the credential.
    required: false

  cred_password:
    description:
      - Specifies the password for the credential.
    required: false

  super_password:
    description:
      - Specifies the super or config password for the credential. Only required for devices that require elevation.
    required: false

  port:
    description:
      - Specifies port number.
    required: false

'''

<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
=======

>>>>>>> Full FSM Commit
=======
>>>>>>> Full FSM Commit. Ready for shippable tests.
=======

>>>>>>> Full FSM Commit
=======
>>>>>>> Full FSM Commit. Ready for shippable tests.
EXAMPLES = '''
- name: ADD AN SSH CREDENTIAL
  fsm_credentials:
    host: "10.0.0.15"
    username: "super/api_user"
    password: "Fortinet!1"
    ignore_ssl_errors: "enable"
    cred_username: "fortinet"
    cred_password: "fortinet123!"
    access_protocol: "ssh"
    friendly_name: "AnsibleTestSSHCred"
    mode: "add"
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD

=======
    
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
=======
    
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
- name: ADD AN SSH CREDENTIAL FOR ELEVATED DEVICE
  fsm_credentials:
    host: "10.0.0.15"
    username: "super/api_user"
    password: "Fortinet!1"
    ignore_ssl_errors: "enable"
    cred_username: "fortinet"
    cred_password: "fortinet123!"
    super_username: "fortinet_super"
    super_password: "fortinet321!"
    access_protocol: "ssh"
    friendly_name: "AnsibleTestCiscoCred"
    mode: "add"
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
    ip_range: "10.0.254.1-10.0.254.255"

=======
    
>>>>>>> Full FSM Commit
=======
    ip_range: "10.0.254.1-10.0.254.255"

>>>>>>> Full FSM Commit. Ready for shippable tests.
=======
    
>>>>>>> Full FSM Commit
=======
    ip_range: "10.0.254.1-10.0.254.255"

>>>>>>> Full FSM Commit. Ready for shippable tests.
- name: ADD AN VM_SDK CREDENTIAL
  fsm_credentials:
    host: "10.0.0.15"
    username: "super/api_user"
    password: "Fortinet!1"
    ignore_ssl_errors: "enable"
    cred_username: "fortinet"
    cred_password: "fortinet123!"
    access_protocol: "vm_sdk"
    friendly_name: "AnsibleTestVMSDKCred"
    mode: "add"

<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> Full FSM Commit. Ready for shippable tests.
=======
>>>>>>> Full FSM Commit. Ready for shippable tests.
- name: MSP UPDATE AN SSH CREDENTIAL
  fsm_credentials:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    ignore_ssl_errors: "enable"
    cred_username: "fortinet"
    cred_password: "fortinet123!123"
    access_protocol: "ssh"
    description: "AnsibleTestSSHCredUPDATE"
    mode: "update"
    friendly_name: "AnsibleTestSSHCred"
    ip_range: "10.7.220.100"

<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> Full FSM Commit
=======
>>>>>>> Full FSM Commit. Ready for shippable tests.
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

        mode=dict(required=False, type="str",
                  choices=["add", "update", "get"], default="get"),
        ip_range=dict(required=False, type="str"),
        access_id=dict(required=False, type="str"),
        input_xml_file=dict(required=False, type="str"),
        access_protocol=dict(required=False, type="str", choices=['ftp', 'ftp_over_ssl',
                                                                  'imap', 'imap_over_ssl', 'jdbc', 'jmx', 'kafka_api',
                                                                  'pop3', 'pop3_over_ssl', 'smtp', 'smtp_over_ssl',
                                                                  'smtp_over_tls', 'ssh', 'telnet', 'vm_sdk']),
        friendly_name=dict(required=False, type="str"),
        description=dict(required=False, type="str"),
        pull_interval=dict(required=False, type="str", default="5"),
        cred_username=dict(required=False, type="str"),
        cred_password=dict(required=False, type="str", no_log=True),
        super_password=dict(required=False, type="str", no_log=True),
        port=dict(required=False, type="str"),
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
        "ip_range": module.params["ip_range"],
        "access_id": module.params["access_id"],
        "password_type": "Manual",
        "input_xml_file": module.params["input_xml_file"],
        "access_protocol": module.params["access_protocol"],
        "friendly_name": module.params["friendly_name"],
        "description": module.params["description"],
        "pull_interval": module.params["pull_interval"],
        "cred_username": module.params["cred_username"],
        "cred_password": module.params["cred_password"],
        "super_password": module.params["super_password"],
        "port": module.params["port"],
    }

    # DETERMINE THE MODE AND ADD THE CORRECT DATA TO THE PARAMGRAM
    if paramgram["mode"] in ["add", "update"]:
        paramgram["uri"] = FSMEndpoints.SET_CREDS
    elif paramgram["mode"] == "get":
        paramgram["uri"] = FSMEndpoints.GET_CREDS

    if paramgram["uri"] is None:
        raise FSMBaseException("Base URI couldn't be constructed. Check options.")

    if not paramgram["port"]:
        if paramgram["access_protocol"] == "ftp":
            paramgram["port"] = "21"
        if paramgram["access_protocol"] == "ftp_over_ssl":
            paramgram["port"] = "990"
        if paramgram["access_protocol"] == "imap":
            paramgram["port"] = "143"
        if paramgram["access_protocol"] == "imap_over_ssl":
            paramgram["port"] = "993"
        if paramgram["access_protocol"] == "jdbc":
            paramgram["port"] = "1433"
        if paramgram["access_protocol"] == "jmx":
            paramgram["port"] = "0"
        if paramgram["access_protocol"] == "pop3":
            paramgram["port"] = "110"
        if paramgram["access_protocol"] == "pop3_over_ssl":
            paramgram["port"] = "995"
        if paramgram["access_protocol"] == "smtp":
            paramgram["port"] = "25"
        if paramgram["access_protocol"] == "smtp_over_ssl":
            paramgram["port"] = "465"
        if paramgram["access_protocol"] == "smtp_over_tls":
            paramgram["port"] = "465"
        if paramgram["access_protocol"] == "ssh":
            paramgram["port"] = "22"
        if paramgram["access_protocol"] == "telnet":
            paramgram["port"] = "23"
        if paramgram["access_protocol"] == "vm_sdk":
            paramgram["port"] = None

    module.paramgram = paramgram

    # TRY TO INIT THE CONNECTION SOCKET PATH AND FortiManagerHandler OBJECT AND TOOLS
    fsm = None
<<<<<<< HEAD
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
=======
    results = DEFAULT_EXIT_MSG
    try:
        fsm = FortiSIEMHandler(module)
    except BaseException as err:
        raise FSMBaseException("Couldn't load FortiSIEM Handler from mod_utils. Error: " + str(err))
>>>>>>> Full FSM Commit. Ready for shippable tests.

    # EXECUTE THE MODULE OPERATION
    if paramgram["mode"] in ["add", "update"]:
        if paramgram["input_xml_file"]:
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
            paramgram["input_xml"] = fsm.get_file_contents(paramgram["input_xml_file"])
=======
            paramgram["input_xml"] = fsm.get_report_source_from_file_path(paramgram["input_xml_file"])
>>>>>>> Full FSM Commit
=======
            paramgram["input_xml"] = fsm.get_file_contents(paramgram["input_xml_file"])
>>>>>>> Full FSM Commit. Ready for shippable tests.
=======
            paramgram["input_xml"] = fsm.get_report_source_from_file_path(paramgram["input_xml_file"])
>>>>>>> Full FSM Commit
=======
            paramgram["input_xml"] = fsm.get_file_contents(paramgram["input_xml_file"])
>>>>>>> Full FSM Commit. Ready for shippable tests.
            try:
                results = fsm.handle_simple_payload_request(paramgram["input_xml"])
            except BaseException as err:
                raise FSMBaseException(err)
        else:
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
            paramgram["input_xml"] = fsm._xml.create_credential_payload()

=======
            paramgram["input_xml"] = fsm.create_credential_payload()
            #pydevd.settrace('10.0.0.151', port=54654, stdoutToServer=True, stderrToServer=True)
>>>>>>> Full FSM Commit
=======
            paramgram["input_xml"] = fsm._xml.create_credential_payload()

>>>>>>> Full FSM Commit. Ready for shippable tests.
=======
            paramgram["input_xml"] = fsm.create_credential_payload()
            #pydevd.settrace('10.0.0.151', port=54654, stdoutToServer=True, stderrToServer=True)
>>>>>>> Full FSM Commit
=======
            paramgram["input_xml"] = fsm._xml.create_credential_payload()

>>>>>>> Full FSM Commit. Ready for shippable tests.
            try:
                results = fsm.handle_simple_payload_request(paramgram["input_xml"])
            except BaseException as err:
                raise FSMBaseException(err)
    elif paramgram["mode"] == "get":
        try:
            results = fsm.handle_simple_request()
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
=======
            #pydevd.settrace('10.0.0.151', port=54654, stdoutToServer=True, stderrToServer=True)
>>>>>>> Full FSM Commit
=======
>>>>>>> Full FSM Commit. Ready for shippable tests.
=======
            #pydevd.settrace('10.0.0.151', port=54654, stdoutToServer=True, stderrToServer=True)
>>>>>>> Full FSM Commit
=======
>>>>>>> Full FSM Commit. Ready for shippable tests.
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
=======
    return module.exit_json(msg=results)
>>>>>>> Full FSM Commit. Ready for shippable tests.


if __name__ == "__main__":
    main()
