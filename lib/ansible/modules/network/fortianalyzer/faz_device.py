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
module: faz_device
version_added: "2.9"
author: Luke Weighall (@lweighall)
short_description: Add or remove device
description:
  - Add or remove a device or list of devices to FortiAnalyzer Device Manager. ADOM Capable.

options:
  adom:
    description:
      - The ADOM the configuration should belong to.
    required: true
    default: root
    type: str

  mode:
    description:
      - Add or delete devices. Or promote unregistered devices that are in the FortiAnalyzer "waiting pool"
    required: false
    default: add
    choices: ["add", "delete", "promote"]
    type: str

  device_username:
    description:
      - The username of the device being added to FortiAnalyzer.
    required: false
    type: str

  device_password:
    description:
      - The password of the device being added to FortiAnalyzer.
    required: false
    type: str

  device_ip:
    description:
      - The IP of the device being added to FortiAnalyzer.
    required: false
    type: str

  device_unique_name:
    description:
      - The desired "friendly" name of the device being added to FortiAnalyzer.
    required: false
    type: str

  device_serial:
    description:
      - The serial number of the device being added to FortiAnalyzer.
    required: false
    type: str

  os_type:
    description:
      - The os type of the device being added (default 0).
    required: true
    choices: ["unknown", "fos", "fsw", "foc", "fml", "faz", "fwb", "fch", "fct", "log", "fmg", "fsa", "fdd", "fac"]
    type: str

  mgmt_mode:
    description:
      - Management Mode of the device you are adding.
    choices: ["unreg", "fmg", "faz", "fmgfaz"]
    required: true
    type: str

  os_minor_vers:
    description:
      - Minor OS rev of the device.
    required: true
    type: str

  os_ver:
    description:
      - Major OS rev of the device
    required: true
    choices: ["unknown", "0.0", "1.0", "2.0", "3.0", "4.0", "5.0", "6.0"]
    type: str

  platform_str:
    description:
      - Required for determine the platform for VM platforms. ie FortiGate-VM64
    required: false
    type: str

  faz_quota:
    description:
      - Specifies the quota for the device in FAZ
    required: False
    type: str
'''

EXAMPLES = '''
- name: DISCOVER AND ADD DEVICE A PHYSICAL FORTIGATE
  faz_device:
    adom: "root"
    device_username: "admin"
    device_password: "admin"
    device_ip: "10.10.24.201"
    device_unique_name: "FGT1"
    device_serial: "FGVM000000117994"
    state: "present"
    mgmt_mode: "faz"
    os_type: "fos"
    os_ver: "5.0"
    minor_rev: 6


- name: DISCOVER AND ADD DEVICE A VIRTUAL FORTIGATE
  faz_device:
    adom: "root"
    device_username: "admin"
    device_password: "admin"
    device_ip: "10.10.24.202"
    device_unique_name: "FGT2"
    mgmt_mode: "faz"
    os_type: "fos"
    os_ver: "5.0"
    minor_rev: 6
    state: "present"
    platform_str: "FortiGate-VM64"

- name: DELETE DEVICE FGT01
  faz_device:
    adom: "root"
    device_unique_name: "ansible-fgt01"
    mode: "delete"

- name: DELETE DEVICE FGT02
  faz_device:
    adom: "root"
    device_unique_name: "ansible-fgt02"
    mode: "delete"

- name: PROMOTE FGT01 IN FAZ BY IP
  faz_device:
    adom: "root"
    device_password: "fortinet"
    device_ip: "10.7.220.151"
    device_username: "ansible"
    mgmt_mode: "faz"
    mode: "promote"


- name: PROMOTE FGT02 IN FAZ
  faz_device:
    adom: "root"
    device_password: "fortinet"
    device_unique_name: "ansible-fgt02"
    device_username: "ansible"
    mgmt_mode: "faz"
    mode: "promote"

'''

RETURN = """
api_result:
  description: full API response, includes status code and message
  returned: always
  type: str
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.fortianalyzer.fortianalyzer import FortiAnalyzerHandler
from ansible.module_utils.network.fortianalyzer.common import FAZBaseException
from ansible.module_utils.network.fortianalyzer.common import FAZCommon
from ansible.module_utils.network.fortianalyzer.common import FAZMethods
from ansible.module_utils.network.fortianalyzer.common import DEFAULT_RESULT_OBJ
from ansible.module_utils.network.fortianalyzer.common import FAIL_SOCKET_MSG


def faz_add_device(faz, paramgram):
    """
    This method is used to add devices to the faz or delete them
    """

    datagram = {
        "adom": paramgram["adom"],
        "device": {"adm_usr": paramgram["device_username"], "adm_pass": paramgram["device_password"],
                   "ip": paramgram["ip"], "name": paramgram["device_unique_name"],
                   "mgmt_mode": paramgram["mgmt_mode"], "os_type": paramgram["os_type"],
                   "mr": paramgram["os_minor_vers"]}
    }

    if paramgram["platform_str"] is not None:
        datagram["device"]["platform_str"] = paramgram["platform_str"]

    if paramgram["sn"] is not None:
        datagram["device"]["sn"] = paramgram["sn"]

    if paramgram["device_action"] is not None:
        datagram["device"]["device_action"] = paramgram["device_action"]

    if paramgram["faz.quota"] is not None:
        datagram["device"]["faz.quota"] = paramgram["faz.quota"]

    url = '/dvm/cmd/add/device/'
    response = faz.process_request(url, datagram, FAZMethods.EXEC)
    return response


def faz_delete_device(faz, paramgram):
    """
    This method deletes a device from the FAZ
    """
    datagram = {
        "adom": paramgram["adom"],
        "device": paramgram["device_unique_name"],
    }

    url = '/dvm/cmd/del/device/'
    response = faz.process_request(url, datagram, FAZMethods.EXEC)
    return response


def faz_get_unknown_devices(faz):
    """
    This method gets devices with an unknown management type field
    """

    faz_filter = ["mgmt_mode", "==", "0"]

    datagram = {
        "filter": faz_filter
    }

    url = "/dvmdb/device"
    response = faz.process_request(url, datagram, FAZMethods.GET)

    return response


def faz_approve_unregistered_device_by_ip(faz, paramgram):
    """
    This method approves unregistered devices by ip.
    """
    # TRY TO FIND DETAILS ON THIS UNREGISTERED DEVICE
    unknown_devices = faz_get_unknown_devices(faz)
    target_device = None
    if unknown_devices[0] == 0:
        for device in unknown_devices[1]:
            if device["ip"] == paramgram["ip"]:
                target_device = device
    else:
        return "No devices are waiting to be registered!"

    # now that we have the target device details...fill out the datagram and make the call to promote it
    if target_device is not None:
        target_device_paramgram = {
            "adom": paramgram["adom"],
            "ip": target_device["ip"],
            "device_username": paramgram["device_username"],
            "device_password": paramgram["device_password"],
            "device_unique_name": paramgram["device_unique_name"],
            "sn": target_device["sn"],
            "os_type": target_device["os_type"],
            "mgmt_mode": paramgram["mgmt_mode"],
            "os_minor_vers": target_device["mr"],
            "os_ver": target_device["os_ver"],
            "platform_str": target_device["platform_str"],
            "faz.quota": target_device["faz.quota"],
            "device_action": paramgram["device_action"]
        }

        add_device = faz_add_device(faz, target_device_paramgram)
        return add_device

    return str("Couldn't find the desired device with ip: " + str(paramgram["device_ip"]))


def faz_approve_unregistered_device_by_name(faz, paramgram):
    # TRY TO FIND DETAILS ON THIS UNREGISTERED DEVICE
    unknown_devices = faz_get_unknown_devices(faz)
    target_device = None
    if unknown_devices[0] == 0:
        for device in unknown_devices[1]:
            if device["name"] == paramgram["device_unique_name"]:
                target_device = device
    else:
        return "No devices are waiting to be registered!"

    # now that we have the target device details...fill out the datagram and make the call to promote it
    if target_device is not None:
        target_device_paramgram = {
            "adom": paramgram["adom"],
            "ip": target_device["ip"],
            "device_username": paramgram["device_username"],
            "device_password": paramgram["device_password"],
            "device_unique_name": paramgram["device_unique_name"],
            "sn": target_device["sn"],
            "os_type": target_device["os_type"],
            "mgmt_mode": paramgram["mgmt_mode"],
            "os_minor_vers": target_device["mr"],
            "os_ver": target_device["os_ver"],
            "platform_str": target_device["platform_str"],
            "faz.quota": target_device["faz.quota"],
            "device_action": paramgram["device_action"]
        }

        add_device = faz_add_device(faz, target_device_paramgram)
        return add_device

    return str("Couldn't find the desired device with name: " + str(paramgram["device_unique_name"]))


def main():
    argument_spec = dict(
        adom=dict(required=False, type="str", default="root"),
        mode=dict(choices=["add", "delete", "promote"], type="str", default="add"),

        device_ip=dict(required=False, type="str"),
        device_username=dict(required=False, type="str"),
        device_password=dict(required=False, type="str", no_log=True),
        device_unique_name=dict(required=False, type="str"),
        device_serial=dict(required=False, type="str"),

        os_type=dict(required=False, type="str", choices=["unknown", "fos", "fsw", "foc", "fml",
                                                          "faz", "fwb", "fch", "fct", "log", "fmg",
                                                          "fsa", "fdd", "fac"]),
        mgmt_mode=dict(required=False, type="str", choices=["unreg", "fmg", "faz", "fmgfaz"]),
        os_minor_vers=dict(required=False, type="str"),
        os_ver=dict(required=False, type="str", choices=["unknown", "0.0", "1.0", "2.0", "3.0", "4.0", "5.0", "6.0"]),
        platform_str=dict(required=False, type="str"),
        faz_quota=dict(required=False, type="str")
    )

    required_if = [
        ['mode', 'delete', ['device_unique_name']],
        ['mode', 'add', ['device_serial', 'device_username',
                         'device_password', 'device_unique_name', 'device_ip', 'mgmt_mode', 'platform_str']]

    ]

    module = AnsibleModule(argument_spec, supports_check_mode=True, required_if=required_if, )

    # START SESSION LOGIC
    paramgram = {
        "adom": module.params["adom"],
        "mode": module.params["mode"],
        "ip": module.params["device_ip"],
        "device_username": module.params["device_username"],
        "device_password": module.params["device_password"],
        "device_unique_name": module.params["device_unique_name"],
        "sn": module.params["device_serial"],
        "os_type": module.params["os_type"],
        "mgmt_mode": module.params["mgmt_mode"],
        "os_minor_vers": module.params["os_minor_vers"],
        "os_ver": module.params["os_ver"],
        "platform_str": module.params["platform_str"],
        "faz.quota": module.params["faz_quota"],
        "device_action": None
    }
    # INSERT THE PARAMGRAM INTO THE MODULE SO WHEN WE PASS IT TO MOD_UTILS.FortiManagerHandler IT HAS THAT INFO

    if paramgram["mode"] == "add":
        paramgram["device_action"] = "add_model"
    elif paramgram["mode"] == "promote":
        paramgram["device_action"] = "promote_unreg"
    module.paramgram = paramgram

    # TRY TO INIT THE CONNECTION SOCKET PATH AND FortiManagerHandler OBJECT AND TOOLS
    faz = None
    if module._socket_path:
        connection = Connection(module._socket_path)
        faz = FortiAnalyzerHandler(connection, module)
        faz.tools = FAZCommon()
    else:
        module.fail_json(**FAIL_SOCKET_MSG)

    # BEGIN MODULE-SPECIFIC LOGIC -- THINGS NEED TO HAPPEN DEPENDING ON THE ENDPOINT AND OPERATION
    results = DEFAULT_RESULT_OBJ

    try:
        if paramgram["mode"] == "add":
            results = faz_add_device(faz, paramgram)
    except BaseException as err:
        raise FAZBaseException(msg="An error occurred trying to add the device. Error: " + str(err))

    try:
        if paramgram["mode"] == "promote":
            if paramgram["ip"] is not None:
                results = faz_approve_unregistered_device_by_ip(faz, paramgram)
            elif paramgram["device_unique_name"] is not None:
                results = faz_approve_unregistered_device_by_name(faz, paramgram)
    except BaseException as err:
        raise FAZBaseException(msg="An error occurred trying to promote the device. Error: " + str(err))

    try:
        if paramgram["mode"] == "delete":
            results = faz_delete_device(faz, paramgram)
    except BaseException as err:
        raise FAZBaseException(msg="An error occurred trying to delete the device. Error: " + str(err))

    # PROCESS RESULTS
    try:
        faz.govern_response(module=module, results=results,
                            ansible_facts=faz.construct_ansible_facts(results, module.params, paramgram))
    except BaseException as err:
        raise FAZBaseException(msg="An error occurred with govern_response(). Error: " + str(err))

    # This should only be hit if faz.govern_response is missed or failed somehow. In fact. It should never be hit.
    # But it's here JIC.
    return module.exit_json(**results[1])


if __name__ == "__main__":
    main()
