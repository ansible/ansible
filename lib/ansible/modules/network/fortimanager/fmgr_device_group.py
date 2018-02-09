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
module: fmgr_device_group
version_added: "2.6"
author: Luke Weighall, Andrew Welsh
short_description: Alter FortiManager device groups
description:
  - Add or edit device groups and assign devices to device groups FortiManager Device Manager using jsonrpc API

options:
  adom:
    description:
      - The ADOM the configuration should belong to.
    required: true

  vdom:
    description:
      - The VDOM of on the Fortigate you want to add, must match the device in FMGR. Usually root.
    required: true

  host:
    description:
      - The FortiManager's Address.
    required: true

  username:
    description:
      - The username to log into the FortiManager
    required: true
  password:
    description:
      - The password associated with the username account.
    required: false

  state:
    description:
      - The desired state of the specified object.
      - absent will delete the object if it exists. If grp_members is defined, only members are deleted.
      - present will create the configuration if needed.
      - To delete a grp_name, you must omit the grp_members field in the playbook task while setting to absent
    required: true
    default: present

    choices: ["absent", "present"]
  grp_name:
    description:
      - The name of the device group.
    required: false

  grp_desc:
    description:
      - The description of the device group.
    required: false

  grp_members:
    description:
      - A comma separated list of device names or device groups to be added as members to the device group.
      - If Group Members are defined, and state="absent", only group members will be removed.
      - If you want to delete a group itself, you must omit this parameter from the task in playbook
      - Otherwise module assumes
    required: false

'''


EXAMPLES = '''
- name: CREATE DEVICE GROUP
  fmgr_device_group:
    host: "{{inventory_hostname}}"
    username: "{{ username }}"
    password: "{{ password }}"
    grp_name: "TestGroup"
    grp_desc: "CreatedbyAnsible"
    adom: "ansible"
    state: "present"

- name: CREATE DEVICE GROUP 2
  fmgr_device_group:
    host: "{{inventory_hostname}}"
    username: "{{ username }}"
    password: "{{ password }}"
    grp_name: "AnsibleGroup"
    grp_desc: "CreatedbyAnsible"
    adom: "ansible"
    state: "present"

- name: ADD DEVICES TO DEVICE GROUP
  fmgr_device_group:
    host: "{{inventory_hostname}}"
    username: "{{ username }}"
    password: "{{ password }}"
    state: "present"
    grp_name: "TestGroup"
    grp_members: "FGT1,FGT2"
    adom: "ansible"
    vdom: "root"

- name: REMOVE DEVICES TO DEVICE GROUP
  fmgr_device_group:
    host: "{{inventory_hostname}}"
    username: "{{ username }}"
    password: "{{ password }}"
    state: "absent"
    grp_name: "TestGroup"
    grp_members: "FGT1,FGT2"
    adom: "ansible"

- name: DELETE DEVICE GROUP
  fmgr_device_group:
    host: "{{inventory_hostname}}"
    username: "{{ username }}"
    password: "{{ password }}"
    grp_name: "AnsibleGroup"
    grp_desc: "CreatedbyAnsible"
    state: "absent"
    adom: "ansible"
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


def get_groups(fmg, adom):
    """
    This method is used GET the HA PEERS of a FortiManager Node
    """

    datagram = {
        "method": "get"
    }

    url = '/dvmdb/adom/{adom}/group'.format(adom=adom)
    response = fmg.get(url, datagram)
    return response


def add_device_group(fmg, grp_name, grp_desc, adom):
    """
    This method is used to add device groups
    """

    datagram = {
        "name": grp_name,
        "desc": grp_desc,
        "os_type": "fos"
    }

    url = '/dvmdb/adom/{adom}/group'.format(adom=adom)
    response = fmg.add(url, datagram)
    return response


def delete_device_group(fmg, grp_name, adom):
    """
    This method is used to add devices to the FMGR
    """

    datagram = {
        "adom": adom,
        "name": grp_name
    }

    url = '/dvmdb/adom/{adom}/group/{grp_name}'.format(adom=adom, grp_name=grp_name)
    response = fmg.delete(url, datagram)
    return response


def add_group_member(fmg, grp_name, device_member_list, adom, vdom):
    """
    This method is used to update device groups add members
    """
    response = None
    device_member_list = device_member_list.replace(' ', '')
    device_member_list = device_member_list.split(',')

    for dev_name in device_member_list:
        datagram = {'name': dev_name, 'vdom': vdom}

        url = '/dvmdb/adom/{adom}/group/{grp_name}/object member'.format(adom=adom, grp_name=grp_name)
        response = fmg.add(url, datagram)

    return response


def delete_group_member(fmg, grp_name, device_member_list, adom, vdom):
    """
    This method is used to update device groups and delete members
    """
    response = None
    device_member_list = device_member_list.replace(' ', '')
    device_member_list = device_member_list.split(',')

    for dev_name in device_member_list:
        datagram = {
            'name': dev_name,
            'vdom': vdom
        }

        url = '/dvmdb/adom/{adom}/group/{grp_name}/object member'.format(adom=adom, grp_name=grp_name)
        response = fmg.delete(url, datagram)

    return response


def main():
    argument_spec = dict(
        adom=dict(required=False, type="str"),
        vdom=dict(required=False, type="str"),
        host=dict(required=True, type="str"),
        username=dict(fallback=(env_fallback, ["ANSIBLE_NET_USERNAME"])),
        password=dict(fallback=(env_fallback, ["ANSIBLE_NET_PASSWORD"]), no_log=True),
        state=dict(choices=["absent", "param_absent", "present"], type="str"),
        grp_desc=dict(required=False, type="str"),
        grp_name=dict(required=True, type="str"),
        grp_members=dict(required=False, type="str"),
    )

    module = AnsibleModule(argument_spec, supports_check_mode=True, )

    # handle params passed via provider and insure they are represented as the data type expected by fortimanager

    state = module.params["state"]
    grp_name = module.params["grp_name"]
    grp_desc = module.params["grp_desc"]
    grp_members = module.params["grp_members"]
    adom = module.params["adom"]
    vdom = module.params["vdom"]
    # if adom is empty, set to root
    if adom is None:
        adom = "root"
    # if vdom is empty, set to root
    if vdom is None:
        vdom = "root"
    # if state is empty make it "present"
    if state is None:
        state = "present"

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

        # PROCESS THE GROUP ADDS FIRST
        if grp_name is not None and state == "present":
            # add device group
            results = add_device_group(fmg, grp_name, grp_desc, adom)
            if not results[0] == 0 and not results[0] == -2:
                module.fail_json(msg="Failed to Add Device Group", **results[1])

        # PROCESS THE GROUP MEMBER ADDS
        if grp_members is not None and state == "present":
            # assign devices to device group
            results = add_group_member(fmg, grp_name, grp_members, adom, vdom)
            if not results[0] == 0 and not results[0] == -2:
                module.fail_json(msg="Failed to Add Group Member(s)", **results[1])

        # PROCESS THE GROUP MEMBER DELETES
        if grp_members is not None and state == "absent":
            # remove devices grom a group
            results = delete_group_member(fmg, grp_name, grp_members, adom, vdom)
            if not results[0] == 0:
                module.fail_json(msg="Failed to Delete Group Member(s)", **results[1])

        # PROCESS THE GROUP DELETES, ONLY IF GRP_MEMBERS IS NOT NULL TOO
        if grp_name is not None and state == "absent" and grp_members is None:
            # delete device group
            results = delete_device_group(fmg, grp_name, adom)

            if not results[0] == 0:
                module.fail_json(msg="Failed to Delete Device Group", **results[1])

    # RETURN THE RESULTS
    return module.exit_json(**results[1])


if __name__ == "__main__":
    main()
