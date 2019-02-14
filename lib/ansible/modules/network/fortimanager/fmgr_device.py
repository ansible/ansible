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
author:
    - Luke Weighall (@lweighall)
    - Andrew Welsh (@Ghilli3)
    - Jim Huber (@p4r4n0y1ng)
short_description: Add or remove device
description:
  - Add or remove a device or list of devices from FortiManager Device Manager using JSON RPC API.

options:
  adom:
    description:
      - The ADOM the configuration should belong to.
    required: true
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
  state:
    description:
      - The desired state of the specified object.
      - absent will delete the object if it exists.
      - present will create the configuration if needed.
    required: false
    default: present
    choices: ["absent", "present"]

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
    host: "{{inventory_hostname}}"
    username: "{{ username }}"
    password: "{{ password }}"
    adom: "root"
    device_username: "admin"
    device_password: "admin"
    device_ip: "10.10.24.201"
    device_unique_name: "FGT1"
    device_serial: "FGVM000000117994"
    state: "present"

- name: DISCOVER AND ADD DEVICE FGT2
  fmgr_device:
    host: "{{inventory_hostname}}"
    username: "{{ username }}"
    password: "{{ password }}"
    adom: "root"
    device_username: "admin"
    device_password: "admin"
    device_ip: "10.10.24.202"
    device_unique_name: "FGT2"
    device_serial: "FGVM000000117992"
    state: "absent"
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


def discover_device(fmg, paramgram):
    """
    This method is used to discover devices before adding them to FMGR
    """

    datagram = {
        "odd_request_form": "True",
        "device": {"adm_usr": paramgram["device_username"],
                   "adm_pass": paramgram["device_password"],
                   "ip": paramgram["device_ip"]}
    }

    url = '/dvm/cmd/discover/device/'
    response = fmg.execute(url, datagram)
    return response


def add_device(fmg, paramgram):
    """
    This method is used to add devices to the FMGR
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
    response = fmg.execute(url, datagram)
    return response


def delete_device(fmg, paramgram):
    """
    This method deletes a device from the FMGR
    """
    datagram = {
        "adom": paramgram["adom"],
        "flags": ["create_task", "nonblocking"],
        "odd_request_form": "True",
        "device": paramgram["device_unique_name"],
    }

    url = '/dvm/cmd/del/device/'
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
        adom=dict(required=False, type="str", default="root"),
        host=dict(required=True, type="str"),
        username=dict(fallback=(env_fallback, ["ANSIBLE_NET_USERNAME"])),
        password=dict(fallback=(env_fallback, ["ANSIBLE_NET_PASSWORD"]), no_log=True),
        state=dict(choices=["absent", "present"], type="str", default="present"),

        device_ip=dict(required=False, type="str"),
        device_username=dict(required=False, type="str"),
        device_password=dict(required=False, type="str", no_log=True),
        device_unique_name=dict(required=True, type="str"),
        device_serial=dict(required=False, type="str")
    )

    module = AnsibleModule(argument_spec, supports_check_mode=True,)

    # handle params passed via provider and insure they are represented as the data type expected by fortimanagerd
    paramgram = {
        "device_ip": module.params["device_ip"],
        "device_username": module.params["device_username"],
        "device_password": module.params["device_password"],
        "device_unique_name": module.params["device_unique_name"],
        "device_serial": module.params["device_serial"],
        "adom": module.params["adom"],
        "state": module.params["state"]
    }

    # validate required arguments are passed; not used in argument_spec to allow params to be called from provider
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
        results = (-100000, {"msg": "Nothing Happened."})
        if paramgram["state"] == "present":
            # add device
            results = discover_device(fmg, paramgram)
            if results[0] != 0:
                if results[0] == -20042:
                    fmgr_logout(fmg, module, msg="Couldn't contact device on network", results=results, good_codes=[0])
                else:
                    fmgr_logout(fmg, module, msg="Discovering Device Failed", results=results, good_codes=[0])

            if results[0] == 0:
                results = add_device(fmg, paramgram)
                if results[0] != 0 and results[0] != -20010:
                    fmgr_logout(fmg, module, msg="Adding Device Failed", results=results, good_codes=[0])

        if paramgram["state"] == "absent":
            # remove device
            results = delete_device(fmg, paramgram)
            if results[0] != 0:
                fmgr_logout(fmg, module, msg="Deleting Device Failed", results=results, good_codes=[0])

    fmg.logout()
    return module.exit_json(**results[1])


if __name__ == "__main__":
    main()
