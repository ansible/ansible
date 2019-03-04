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
module: fmgr_device
version_added: "2.8"
notes:
    - Full Documentation at U(https://ftnt-ansible-docs.readthedocs.io/en/latest/).
author:
    - Luke Weighall (@lweighall)
    - Andrew Welsh (@Ghilli3)
    - Jim Huber (@p4r4n0y1ng)
short_description: Add or remove device from FortiManager.
description:
  - Add or remove a device or list of devices from FortiManager Device Manager using JSON RPC API.

options:
  adom:
    description:
      - The ADOM the configuration should belong to.
    required: true
    default: root

  mode:
    description:
      - The desired mode of the specified object.
    required: false
    default: add
    choices: ["add", "delete"]

  blind_add:
    description:
      - When adding a device, module will check if it exists, and skip if it does.
      - If enabled, this option will stop the module from checking if it already exists, and blindly add the device.
    required: false
    default: "disable"
    choices: ["enable", "disable"]

  device_username:
    description:
      - The username of the device being added to FortiManager.
    required: false

  device_password:
    description:
      - The password of the device being added to FortiManager.
    required: false

  device_ip:
    description:
      - The IP of the device being added to FortiManager. Supports both IPv4 and IPv6.
    required: false

  device_unique_name:
    description:
      - The desired "friendly" name of the device being added to FortiManager.
    required: false

  device_serial:
    description:
      - The serial number of the device being added to FortiManager.
    required: false
'''

EXAMPLES = '''
- name: DISCOVER AND ADD DEVICE FGT1
  fmgr_device:
    adom: "root"
    device_username: "admin"
    device_password: "admin"
    device_ip: "10.10.24.201"
    device_unique_name: "FGT1"
    device_serial: "FGVM000000117994"
    mode: "add"
    blind_add: "enable"

- name: DISCOVER AND ADD DEVICE FGT2
  fmgr_device:
    adom: "root"
    device_username: "admin"
    device_password: "admin"
    device_ip: "10.10.24.202"
    device_unique_name: "FGT2"
    device_serial: "FGVM000000117992"
    mode: "delete"
'''

RETURN = """
api_result:
  description: full API response, includes status code and message
  returned: always
  type: str
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.fortimanager.fortimanager import FortiManagerHandler
from ansible.module_utils.network.fortimanager.common import FMGBaseException
from ansible.module_utils.network.fortimanager.common import FMGRCommon
from ansible.module_utils.network.fortimanager.common import FMGRMethods
from ansible.module_utils.network.fortimanager.common import DEFAULT_RESULT_OBJ
from ansible.module_utils.network.fortimanager.common import FAIL_SOCKET_MSG


def discover_device(fmgr, paramgram):
    """
    This method is used to discover devices before adding them to FMGR

    :param fmgr: The fmgr object instance from fmgr_utils.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict

    :return: The response from the FortiManager
    :rtype: dict
    """

    datagram = {
        "odd_request_form": "True",
        "device": {"adm_usr": paramgram["device_username"],
                   "adm_pass": paramgram["device_password"],
                   "ip": paramgram["device_ip"]}
    }

    url = '/dvm/cmd/discover/device/'

    response = fmgr.process_request(url, datagram, FMGRMethods.EXEC)
    return response


def add_device(fmgr, paramgram):
    """
    This method is used to add devices to the FMGR

    :param fmgr: The fmgr object instance from fmgr_utils.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict

    :return: The response from the FortiManager
    :rtype: dict
    """

    datagram = {
        "adom": paramgram["adom"],
        "flags": ["create_task", "nonblocking"],
        "odd_request_form": "True",
        "device": {"adm_usr": paramgram["device_username"], "adm_pass": paramgram["device_password"],
                   "ip": paramgram["device_ip"], "name": paramgram["device_unique_name"],
                   "sn": paramgram["device_serial"], "mgmt_mode": "fmgfaz", "flags": 24}
    }

    url = '/dvm/cmd/add/device/'
    response = fmgr.process_request(url, datagram, FMGRMethods.EXEC)
    return response


def delete_device(fmgr, paramgram):
    """
    This method deletes a device from the FMGR

    :param fmgr: The fmgr object instance from fmgr_utils.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict

    :return: The response from the FortiManager
    :rtype: dict
    """
    datagram = {
        "adom": paramgram["adom"],
        "flags": ["create_task", "nonblocking"],
        "device": paramgram["device_unique_name"],
    }

    url = '/dvm/cmd/del/device/'
    response = fmgr.process_request(url, datagram, FMGRMethods.EXEC)
    return response


def get_device(fmgr, paramgram):
    """
    This method attempts to find the firewall on FortiManager to see if it already exists.

    :param fmgr: The fmgr object instance from fmgr_utils.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict

    :return: The response from the FortiManager
    :rtype: dict
    """
    datagram = {
        "adom": paramgram["adom"],
        "filter": ["name", "==", paramgram["device_unique_name"]],
    }

    url = '/dvmdb/adom/{adom}/device/{name}'.format(adom=paramgram["adom"],
                                                    name=paramgram["device_unique_name"])
    response = fmgr.process_request(url, datagram, FMGRMethods.GET)
    return response


def main():
    argument_spec = dict(
        adom=dict(required=False, type="str", default="root"),
        mode=dict(choices=["add", "delete"], type="str", default="add"),
        blind_add=dict(choices=["enable", "disable"], type="str", default="disable"),
        device_ip=dict(required=False, type="str"),
        device_username=dict(required=False, type="str"),
        device_password=dict(required=False, type="str", no_log=True),
        device_unique_name=dict(required=True, type="str"),
        device_serial=dict(required=False, type="str")
    )

    # BUILD MODULE OBJECT SO WE CAN BUILD THE PARAMGRAM
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False, )

    # BUILD THE PARAMGRAM
    paramgram = {
        "device_ip": module.params["device_ip"],
        "device_username": module.params["device_username"],
        "device_password": module.params["device_password"],
        "device_unique_name": module.params["device_unique_name"],
        "device_serial": module.params["device_serial"],
        "adom": module.params["adom"],
        "mode": module.params["mode"]
    }

    # INSERT THE PARAMGRAM INTO THE MODULE SO WHEN WE PASS IT TO MOD_UTILS.FortiManagerHandler IT HAS THAT INFO
    module.paramgram = paramgram

    # TRY TO INIT THE CONNECTION SOCKET PATH AND FortiManagerHandler OBJECT AND TOOLS
    fmgr = None
    if module._socket_path:
        connection = Connection(module._socket_path)
        fmgr = FortiManagerHandler(connection, module)
        fmgr.tools = FMGRCommon()
    else:
        module.fail_json(**FAIL_SOCKET_MSG)

    # BEGIN MODULE-SPECIFIC LOGIC -- THINGS NEED TO HAPPEN DEPENDING ON THE ENDPOINT AND OPERATION
    results = DEFAULT_RESULT_OBJ
    try:
        if paramgram["mode"] == "add":
            # CHECK IF DEVICE EXISTS
            if module.params["blind_add"] == "disable":
                exists_results = get_device(fmgr, paramgram)
                fmgr.govern_response(module=module, results=exists_results, good_codes=(0, -3), changed=False,
                                     ansible_facts=fmgr.construct_ansible_facts(exists_results,
                                                                                module.params, paramgram))

            discover_results = discover_device(fmgr, paramgram)
            fmgr.govern_response(module=module, results=discover_results, stop_on_success=False,
                                 ansible_facts=fmgr.construct_ansible_facts(discover_results,
                                                                            module.params, paramgram))

            if discover_results[0] == 0:
                results = add_device(fmgr, paramgram)
                fmgr.govern_response(module=module, results=discover_results, stop_on_success=True,
                                     changed_if_success=True,
                                     ansible_facts=fmgr.construct_ansible_facts(discover_results,
                                                                                module.params, paramgram))

        if paramgram["mode"] == "delete":
            results = delete_device(fmgr, paramgram)
            fmgr.govern_response(module=module, results=results,
                                 ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))

    except Exception as err:
        raise FMGBaseException(err)

    return module.exit_json(**results[1])


if __name__ == "__main__":
    main()
