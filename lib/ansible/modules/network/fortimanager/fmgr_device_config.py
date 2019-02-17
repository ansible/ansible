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
  host:
    description:
      - The FortiManager's address.
    required: true
  username:
    description:
      - The username used to authenticate with the FortiManager.
    required: false
  password:
    description:
      - The password associated with the username account.
    required: false

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
      - Specify what protocols are allowed on the interface, comma-sepeareted list (see examples).
    required: false

'''

EXAMPLES = '''
- name: CHANGE HOSTNAME
  fmgr_device_config:
    host: "{{inventory_hostname}}"
    username: "{{ username }}"
    password: "{{ password }}"
    device_hostname: "ChangedbyAnsible"
    device_unique_name: "FGT1"

- name: EDIT INTERFACE INFORMATION
  fmgr_device_config:
    host: "{{inventory_hostname}}"
    username: "{{ username }}"
    password: "{{ password }}"
    adom: "root"
    device_unique_name: "FGT2"
    interface: "port3"
    interface_ip: "10.1.1.1/24"
    interface_allow_access: "ping, telnet, https"

- name: INSTALL CONFIG
  fmgr_device_config:
    host: "{{inventory_hostname}}"
    username: "{{ username }}"
    password: "{{ password }}"
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

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.network.fortimanager.fortimanager import AnsibleFortiManager

# check for pyFMG lib
try:
    from pyFMG.fortimgr import FortiManager
    HAS_PYFMGR = True
except ImportError:
    HAS_PYFMGR = False


def update_device_hostname(fmg, paramgram):
    """
    Change a device's hostname
    """
    datagram = {
        "hostname": paramgram["device_hostname"]
    }

    url = "pm/config/device/{device_name}/global/system/global".format(device_name=paramgram["device_unique_name"])
    response = fmg.update(url, datagram)
    return response


def update_device_interface(fmg, paramgram):
    """
    Update a device interface IP and allow access
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
    response = fmg.update(url, datagram)
    return response


def exec_config(fmg, paramgram):
    """
    Update a device interface IP and allow access
    """
    datagram = {
        "scope": {
            "name": paramgram["device_unique_name"]
        },
        "adom": paramgram["adom"],
        "flags": "none"
    }

    url = "/securityconsole/install/device"
    response = fmg.execute(url, datagram)
    return response


# FUNCTION/METHOD FOR LOGGING OUT AND ANALYZING ERROR CODES
def fmgr_logout(fmg, module, msg="NULL", results=(), good_codes=(0,), logout_on_fail=True, logout_on_success=False):
    """
    THIS METHOD CONTROLS THE LOGOUT AND ERROR REPORTING AFTER AN METHOD OR FUNCTION RUNS
    """

    # VALIDATION ERROR (NO RESULTS, JUST AN EXIT)
    if msg != "NULL" and len(results) == 0:
        try:
            fmg.logout()
        except Exception:
            pass
        module.fail_json(msg=msg)

    # SUBMISSION ERROR
    if len(results) > 0:
        if msg == "NULL":
            try:
                msg = results[1]['status']['message']
            except Exception:
                msg = "No status message returned from pyFMG. Possible that this was a GET with a tuple result."

            if results[0] not in good_codes:
                if logout_on_fail:
                    fmg.logout()
                    module.fail_json(msg=msg, **results[1])
                else:
                    return_msg = msg + " -- LOGOUT ON FAIL IS OFF, MOVING ON"
                    return return_msg
            else:
                if logout_on_success:
                    fmg.logout()
                    module.exit_json(msg=msg, **results[1])
                else:
                    return_msg = msg + " -- LOGOUT ON SUCCESS IS OFF, MOVING ON TO REST OF CODE"
                    return return_msg


def main():
    argument_spec = dict(
        host=dict(required=True, type="str"),
        adom=dict(required=False, type="str", default="root"),
        password=dict(fallback=(env_fallback, ["ANSIBLE_NET_PASSWORD"]), no_log=True),
        username=dict(fallback=(env_fallback, ["ANSIBLE_NET_USERNAME"])),

        device_unique_name=dict(required=True, type="str"),
        device_hostname=dict(required=False, type="str"),
        interface=dict(required=False, type="str"),
        interface_ip=dict(required=False, type="str"),
        interface_allow_access=dict(required=False, type="str"),
        install_config=dict(required=False, type="str", default="disable"),
    )

    module = AnsibleModule(argument_spec, supports_check_mode=True,)

    # handle params passed via provider and insure they are represented as the data type expected by fortimanager
    paramgram = {
        "device_unique_name": module.params["device_unique_name"],
        "device_hostname": module.params["device_hostname"],
        "interface": module.params["interface"],
        "interface_ip": module.params["interface_ip"],
        "interface_allow_access": module.params["interface_allow_access"],
        "install_config": module.params["install_config"],
        "adom": module.params["adom"]
    }

    # check if params are set
    if module.params["host"] is None or module.params["username"] is None or module.params["password"] is None:
        module.fail_json(msg="Host and username are required for connection")

    # CHECK IF LOGIN FAILED
    fmg = AnsibleFortiManager(module, module.params["host"], module.params["username"], module.params["password"])
    response = fmg.login()
    if response[1]['status']['code'] != 0:
        module.fail_json(msg="Connection to FortiManager Failed")
    else:

        # START SESSION LOGIC

        # if the device_hostname isn't null, then attempt the api call via method call, store results in variable
        if paramgram["device_hostname"] is not None:
            # add device
            results = update_device_hostname(fmg, paramgram)
            if results[0] != 0:
                fmgr_logout(fmg, module, msg="Failed to set Hostname", results=results, good_codes=[0])

        if paramgram["interface_ip"] is not None or paramgram["interface_allow_access"] is not None:
            results = update_device_interface(fmg, paramgram)
            if results[0] != 0:
                fmgr_logout(fmg, module, msg="Failed to Update Device Interface", results=results, good_codes=[0])

        if paramgram["install_config"] == "enable":
            # attempt to install the config
            results = exec_config(fmg, paramgram)
            if results[0] != 0:
                fmgr_logout(fmg, module, msg="Failed to Update Device Interface", results=results, good_codes=[0])

    # logout, build in check for future logging capabilities
    fmg.logout()
    return module.exit_json(**results[1])


if __name__ == "__main__":
    main()
