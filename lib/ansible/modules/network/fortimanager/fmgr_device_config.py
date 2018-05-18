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
version_added: "2.6"
author:
    - Luke Weighall (@lweighall)
    - Andrew Welsh (@Ghilli3)
    - Jim Huber (@p4r4n0y1ng)
short_description: Edit device configurations
description:
  - Edit device configurations from FortiManager Device Manager using jsonrpc API.

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

  device_unique_name:
    description:
      - The unique device's name that you are editing. A.K.A. Friendly name of device in FortiManager
    required: True
  device_hostname:
    description:
      - The device's new hostname
    required: false

  install_config:
    description:
      - Tells FMGR to attempt to install the config after making it.
    required: false
  interface:
    description:
      - The interface/port number you are editing
    required: false
  interface_ip:
    description:
      - The IP and subnet of the interface/port you are editing
    required: false
  interface_allow_access:
    description:
      - Specify what protocols are allowed on the interface, comma-sepeareted list (see examples)
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


def update_device_hostname(fmg, device_name, hostname):
    """
    Change a device's hostname
    """
    datagram = {
        "hostname": hostname
    }

    url = "pm/config/device/{device_name}/global/system/global".format(device_name=device_name)
    response = fmg.update(url, datagram)
    return response


def update_device_interface(fmg, device_name, interface, ip, allow_access_list, adom):
    """
    Update a device interface IP and allow access
    """
    access_list = list()
    allow_access_list = allow_access_list.replace(' ', '')
    access_list = allow_access_list.split(',')

    datagram = {
        "allowaccess": access_list,
        "ip": ip
    }

    url = "/pm/config/device/{device_name}/global/system/interface" \
          "/{interface}".format(device_name=device_name, interface=interface)
    response = fmg.update(url, datagram)
    return response


def exec_config(fmg, device_unique_name, adom):
    """
    Update a device interface IP and allow access
    """
    datagram = {
        "scope": {
            "name": device_unique_name
        },
        "adom": adom,
        "flags": "none"
    }

    url = "/securityconsole/install/device"
    response = fmg.execute(url, datagram)
    return response


def main():
    argument_spec = dict(
        host=dict(required=True, type="str"),
        adom=dict(required=False, type="str"),
        password=dict(fallback=(env_fallback, ["ANSIBLE_NET_PASSWORD"]), no_log=True),
        username=dict(fallback=(env_fallback, ["ANSIBLE_NET_USERNAME"])),

        device_unique_name=dict(required=True, type="str"),
        device_hostname=dict(required=False, type="str"),
        interface=dict(required=False, type="str"),
        interface_ip=dict(required=False, type="str"),
        interface_allow_access=dict(required=False, type="str"),
        install_config=dict(required=False, type="str"),
    )

    module = AnsibleModule(argument_spec, supports_check_mode=True,)

    # handle params passed via provider and insure they are represented as the data type expected by fortimanager
    adom = module.params["adom"]
    # if adom is empty, set to root
    if adom is None:
        adom = "root"

    device_unique_name = module.params["device_unique_name"]
    device_hostname = module.params["device_hostname"]
    interface = module.params["interface"]
    interface_ip = module.params["interface_ip"]
    interface_allow_access = module.params["interface_allow_access"]
    install_config = module.params["install_config"]

    if install_config is None:
        install_config = "disable"

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

        # if the device_hostname isn't null, then attempt the api call via method call, store results in variable
        if device_hostname is not None:
            # add device
            results = update_device_hostname(fmg, device_unique_name, device_hostname)
            if not results[0] == 0:
                module.fail_json(msg="Failed to Set Hostname", **results[1])

        if interface_ip is not None or interface_allow_access is not None:
            results = update_device_interface(fmg, device_unique_name, interface, interface_ip, interface_allow_access, adom)
            if not results[0] == 0:
                module.fail_json(msg="Failed to Update Device Interface", **results[1])

        if install_config == "enable":
            # attempt to install the config
            results = exec_config(fmg, device_unique_name, adom)
            if not results[0] == 0:
                module.fail_json(msg="Failed to Execute Install", **results[1])

    # logout, build in check for future logging capabilities
    fmg.logout()

    return module.exit_json(**results[1])


if __name__ == "__main__":
    main()
