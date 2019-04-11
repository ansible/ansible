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
module: fmgr_device_config
version_added: "2.8"
notes:
    - Full Documentation at U(https://ftnt-ansible-docs.readthedocs.io/en/latest/).
author:
    - Luke Weighall (@lweighall)
    - Andrew Welsh (@Ghilli3)
    - Jim Huber (@p4r4n0y1ng)
short_description: Edit device configurations
description:
  - Edit device configurations from FortiManager Device Manager using JSON RPC API.

options:
  adom:
    description:
      - The ADOM the configuration should belong to.
    required: false
    default: root

  device_unique_name:
    description:
      - The unique device's name that you are editing. A.K.A. Friendly name of the device in FortiManager.
    required: True

  device_hostname:
    description:
      - The device's new hostname.
    required: false

  install_config:
    description:
      - Tells FMGR to attempt to install the config after making it.
    required: false
    default: disable

  interface:
    description:
      - The interface/port number you are editing.
    required: false

  interface_ip:
    description:
      - The IP and subnet of the interface/port you are editing.
    required: false

  interface_allow_access:
    description:
      - Specify what protocols are allowed on the interface, comma-separated list (see examples).
    required: false
'''

EXAMPLES = '''
- name: CHANGE HOSTNAME
  fmgr_device_config:
    device_hostname: "ChangedbyAnsible"
    device_unique_name: "FGT1"

- name: EDIT INTERFACE INFORMATION
  fmgr_device_config:
    adom: "root"
    device_unique_name: "FGT2"
    interface: "port3"
    interface_ip: "10.1.1.1/24"
    interface_allow_access: "ping, telnet, https"

- name: INSTALL CONFIG
  fmgr_device_config:
    adom: "root"
    device_unique_name: "FGT1"
    install_config: "enable"
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
from ansible.module_utils.network.fortimanager.common import DEFAULT_RESULT_OBJ
from ansible.module_utils.network.fortimanager.common import FAIL_SOCKET_MSG
from ansible.module_utils.network.fortimanager.common import FMGRMethods


def update_device_hostname(fmgr, paramgram):
    """
    :param fmgr: The fmgr object instance from fortimanager.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict
    :return: The response from the FortiManager
    :rtype: dict
    """
    datagram = {
        "hostname": paramgram["device_hostname"]
    }

    url = "pm/config/device/{device_name}/global/system/global".format(device_name=paramgram["device_unique_name"])
    response = fmgr.process_request(url, datagram, FMGRMethods.UPDATE)
    return response


def update_device_interface(fmgr, paramgram):
    """
    :param fmgr: The fmgr object instance from fortimanager.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict
    :return: The response from the FortiManager
    :rtype: dict
    """
    access_list = list()
    allow_access_list = paramgram["interface_allow_access"].replace(' ', '')
    access_list = allow_access_list.split(',')

    datagram = {
        "allowaccess": access_list,
        "ip": paramgram["interface_ip"]
    }

    url = "/pm/config/device/{device_name}/global/system/interface" \
          "/{interface}".format(device_name=paramgram["device_unique_name"], interface=paramgram["interface"])
    response = fmgr.process_request(url, datagram, FMGRMethods.UPDATE)
    return response


def exec_config(fmgr, paramgram):
    """
    :param fmgr: The fmgr object instance from fortimanager.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict
    :return: The response from the FortiManager
    :rtype: dict
    """
    datagram = {
        "scope": {
            "name": paramgram["device_unique_name"]
        },
        "adom": paramgram["adom"],
        "flags": "none"
    }

    url = "/securityconsole/install/device"
    response = fmgr.process_request(url, datagram, FMGRMethods.EXEC)
    return response


def main():
    argument_spec = dict(
        adom=dict(required=False, type="str", default="root"),
        device_unique_name=dict(required=True, type="str"),
        device_hostname=dict(required=False, type="str"),
        interface=dict(required=False, type="str"),
        interface_ip=dict(required=False, type="str"),
        interface_allow_access=dict(required=False, type="str"),
        install_config=dict(required=False, type="str", default="disable"),
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False, )
    paramgram = {
        "device_unique_name": module.params["device_unique_name"],
        "device_hostname": module.params["device_hostname"],
        "interface": module.params["interface"],
        "interface_ip": module.params["interface_ip"],
        "interface_allow_access": module.params["interface_allow_access"],
        "install_config": module.params["install_config"],
        "adom": module.params["adom"]
    }
    module.paramgram = paramgram
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
        if paramgram["device_hostname"] is not None:
            results = update_device_hostname(fmgr, paramgram)
            fmgr.govern_response(module=module, results=results,
                                 ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))

        if paramgram["interface_ip"] is not None or paramgram["interface_allow_access"] is not None:
            results = update_device_interface(fmgr, paramgram)
            fmgr.govern_response(module=module, results=results,
                                 ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))

        if paramgram["install_config"] == "enable":
            results = exec_config(fmgr, paramgram)
            fmgr.govern_response(module=module, results=results,
                                 ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))

    except Exception as err:
        raise FMGBaseException(err)

    return module.exit_json(**results[1])


if __name__ == "__main__":
    main()
