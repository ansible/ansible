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
version_added: "2.6"
author: Andrew Welsh, Luke Weighall
short_description: Add or remove device
description:
  - Add or remove a device or list of devices from FortiManager Device Manager using jsonrpc API

options:
  adom:
    description:
      - The ADOM the configuration should belong to.
    required: true
  host:
    description:
      - The FortiManager's Address.
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
      - The IP of the device being added to FortiManager.
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
  type: string
"""

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.network.fortimanager.fortimanager import AnsibleFortiManager

# check for pyFMG lib
try:
    from pyFMG.fortimgr import FortiManager
    HAS_PYFMGR = True
except ImportError:
    HAS_PYFMGR = False


def discover_device(fmg, device_ip, device_username, device_password):
    """
    This method is used to discover devices before adding them to FMGR
    """

    datagram = {
        "odd_request_form": "True",
        "device": {"adm_usr": device_username, "adm_pass": device_password, "ip": device_ip}
    }

    url = '/dvm/cmd/discover/device/'
    response = fmg.execute(url, datagram)
    return response


def add_device(fmg, device_ip, device_username, device_password, device_unique_name, device_serial, adom):
    """
    This method is used to add devices to the FMGR
    """

    datagram = {
        "adom": adom,
        "flags": ["create_task", "nonblocking"],
        "odd_request_form": "True",
        "device": {"adm_usr": device_username, "adm_pass": device_password, "ip": device_ip,
                   "name": device_unique_name, "sn": device_serial, "mgmt_mode": "fmgfaz", "flags": 24}
    }

    url = '/dvm/cmd/add/device/'
    response = fmg.execute(url, datagram)
    return response


def delete_device(fmg, dev_name, adom):
    """
    This method deletes a device from the FMGR
    """
    datagram = {
        "adom": adom,
        "flags": ["create_task", "nonblocking"],
        "odd_request_form": "True",
        "device": dev_name,
    }

    url = '/dvm/cmd/del/device/'
    response = fmg.execute(url, datagram)
    return response


def main():
    argument_spec = dict(
        adom=dict(required=False, type="str"),
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
    adom = module.params["adom"]
    if adom is None:
        adom = "root"
    state = module.params["state"]
    if state is None:
        state = "present"

    device_ip = module.params["device_ip"]
    device_username = module.params["device_username"]
    device_password = module.params["device_password"]
    device_unique_name = module.params["device_unique_name"]
    device_serial = module.params["device_serial"]

    # validate required arguments are passed; not used in argument_spec to allow params to be called from provider
    # check if params are set
    if module.params["host"] is None or module.params["username"] is None:
        module.fail_json(msg="Host and username are required for connection")

    # CHECK IF LOGIN FAILED
    fmg = AnsibleFortiManager(module, module.params["host"], module.params["username"], module.params["password"])
    response = fmg.login()
    if "FortiManager instance connnected" not in str(response):
        module.fail_json(msg="Connection to FortiManager Failed")
    else:
        # START SESSION LOGIC

        if state == "present":
            # add device
            results = discover_device(fmg, device_ip, device_username, device_password)
            if not results[0] == 0:
                if results[0] == -20042:
                    module.fail_json(msg="Couldn't contact device on network", **results[1])
                else:
                    module.fail_json(msg="Discovering Device Failed", **results[1])

            if results[0] == 0:
                results = add_device(fmg, device_ip, device_username, device_password, device_unique_name, device_serial, adom)
                if not results[0] == 0 and not results[0] == -20010:
                    module.fail_json(msg="Adding Device Failed", **results[1])
        if state == "absent":
            # remove device
            results = delete_device(fmg, device_unique_name, adom)
            if not results[0] == 0:
                module.fail_json(msg="Deleting Device Failed", **results[1])

    # logout
    fmg.logout()
    # results is returned as a tuple
    return module.exit_json(**results[1])


if __name__ == "__main__":
    main()
