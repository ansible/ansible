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
version_added: "2.8"
notes:
    - Full Documentation at U(https://ftnt-ansible-docs.readthedocs.io/en/latest/).
author:
    - Luke Weighall (@lweighall)
    - Andrew Welsh (@Ghilli3)
    - Jim Huber (@p4r4n0y1ng)
short_description: Alter FortiManager device groups.
description:
  - Add or edit device groups and assign devices to device groups FortiManager Device Manager using JSON RPC API.

options:
  adom:
    description:
      - The ADOM the configuration should belong to.
    required: false
    default: root

  vdom:
    description:
      - The VDOM of the Fortigate you want to add, must match the device in FMGR. Usually root.
    required: false
    default: root

  mode:
    description:
      - Sets one of three modes for managing the object.
      - Allows use of soft-adds instead of overwriting existing values
    choices: ['add', 'set', 'delete', 'update']
    required: false
    default: add

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
      - If Group Members are defined, and mode="delete", only group members will be removed.
      - If you want to delete a group itself, you must omit this parameter from the task in playbook.
    required: false

'''


EXAMPLES = '''
- name: CREATE DEVICE GROUP
  fmgr_device_group:
    grp_name: "TestGroup"
    grp_desc: "CreatedbyAnsible"
    adom: "ansible"
    mode: "add"

- name: CREATE DEVICE GROUP 2
  fmgr_device_group:
    grp_name: "AnsibleGroup"
    grp_desc: "CreatedbyAnsible"
    adom: "ansible"
    mode: "add"

- name: ADD DEVICES TO DEVICE GROUP
  fmgr_device_group:
    mode: "add"
    grp_name: "TestGroup"
    grp_members: "FGT1,FGT2"
    adom: "ansible"
    vdom: "root"

- name: REMOVE DEVICES TO DEVICE GROUP
  fmgr_device_group:
    mode: "delete"
    grp_name: "TestGroup"
    grp_members: "FGT1,FGT2"
    adom: "ansible"

- name: DELETE DEVICE GROUP
  fmgr_device_group:
    grp_name: "AnsibleGroup"
    grp_desc: "CreatedbyAnsible"
    mode: "delete"
    adom: "ansible"
'''

RETURN = """
api_result:
  description: full API response, includes status code and message
  returned: always
  type: str
"""

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.fortimanager.fortimanager import FortiManagerHandler
from ansible.module_utils.network.fortimanager.common import FMGBaseException
from ansible.module_utils.network.fortimanager.common import FMGRCommon
from ansible.module_utils.network.fortimanager.common import FMGRMethods
from ansible.module_utils.network.fortimanager.common import DEFAULT_RESULT_OBJ
from ansible.module_utils.network.fortimanager.common import FAIL_SOCKET_MSG


def get_groups(fmgr, paramgram):
    """
    :param fmgr: The fmgr object instance from fortimanager.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict
    :return: The response from the FortiManager
    :rtype: dict
    """

    datagram = {
        "method": "get"
    }

    url = '/dvmdb/adom/{adom}/group'.format(adom=paramgram["adom"])
    response = fmgr.process_request(url, datagram, FMGRMethods.GET)
    return response


def add_device_group(fmgr, paramgram):
    """
    :param fmgr: The fmgr object instance from fortimanager.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict
    :return: The response from the FortiManager
    :rtype: dict
    """
    # INIT A BASIC OBJECTS
    response = DEFAULT_RESULT_OBJ
    url = ""
    mode = paramgram["mode"]

    datagram = {
        "name": paramgram["grp_name"],
        "desc": paramgram["grp_desc"],
        "os_type": "fos"
    }

    url = '/dvmdb/adom/{adom}/group'.format(adom=paramgram["adom"])

    # IF MODE = SET -- USE THE 'SET' API CALL MODE
    if mode == "set":
        response = fmgr.process_request(url, datagram, FMGRMethods.SET)
    # IF MODE = UPDATE -- USER THE 'UPDATE' API CALL MODE
    elif mode == "update":
        response = fmgr.process_request(url, datagram, FMGRMethods.UPDATE)
    # IF MODE = ADD  -- USE THE 'ADD' API CALL MODE
    elif mode == "add":
        response = fmgr.process_request(url, datagram, FMGRMethods.ADD)

    return response


def delete_device_group(fmgr, paramgram):
    """
    :param fmgr: The fmgr object instance from fortimanager.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict
    :return: The response from the FortiManager
    :rtype: dict
    """
    # INIT A BASIC OBJECTS
    response = DEFAULT_RESULT_OBJ
    url = ""

    datagram = {
        "adom": paramgram["adom"],
        "name": paramgram["grp_name"]
    }

    url = '/dvmdb/adom/{adom}/group/{grp_name}'.format(adom=paramgram["adom"], grp_name=paramgram["grp_name"])
    response = fmgr.process_request(url, datagram, FMGRMethods.DELETE)
    return response


def add_group_member(fmgr, paramgram):
    """
    :param fmgr: The fmgr object instance from fortimanager.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict
    :return: The response from the FortiManager
    :rtype: dict
    """
    # INIT A BASIC OBJECTS
    response = DEFAULT_RESULT_OBJ
    url = ""
    device_member_list = paramgram["grp_members"].replace(' ', '')
    device_member_list = device_member_list.split(',')

    for dev_name in device_member_list:
        datagram = {'name': dev_name, 'vdom': paramgram["vdom"]}

        url = '/dvmdb/adom/{adom}/group/{grp_name}/object member'.format(adom=paramgram["adom"],
                                                                         grp_name=paramgram["grp_name"])
        response = fmgr.process_request(url, datagram, FMGRMethods.ADD)

    return response


def delete_group_member(fmgr, paramgram):
    """
    :param fmgr: The fmgr object instance from fortimanager.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict
    :return: The response from the FortiManager
    :rtype: dict
    """
    # INIT A BASIC OBJECTS
    response = DEFAULT_RESULT_OBJ
    url = ""
    device_member_list = paramgram["grp_members"].replace(' ', '')
    device_member_list = device_member_list.split(',')

    for dev_name in device_member_list:
        datagram = {'name': dev_name, 'vdom': paramgram["vdom"]}

        url = '/dvmdb/adom/{adom}/group/{grp_name}/object member'.format(adom=paramgram["adom"],
                                                                         grp_name=paramgram["grp_name"])
        response = fmgr.process_request(url, datagram, FMGRMethods.DELETE)

    return response


def main():
    argument_spec = dict(
        adom=dict(required=False, type="str", default="root"),
        vdom=dict(required=False, type="str", default="root"),
        mode=dict(choices=["add", "set", "delete", "update"], type="str", default="add"),
        grp_desc=dict(required=False, type="str"),
        grp_name=dict(required=True, type="str"),
        grp_members=dict(required=False, type="str"),
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False, )
    paramgram = {
        "mode": module.params["mode"],
        "grp_name": module.params["grp_name"],
        "grp_desc": module.params["grp_desc"],
        "grp_members": module.params["grp_members"],
        "adom": module.params["adom"],
        "vdom": module.params["vdom"]
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
        # PROCESS THE GROUP ADDS FIRST
        if paramgram["grp_name"] is not None and paramgram["mode"] in ["add", "set", "update"]:
            # add device group
            results = add_device_group(fmgr, paramgram)
            fmgr.govern_response(module=module, results=results,
                                 ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))

        # PROCESS THE GROUP MEMBER ADDS
        if paramgram["grp_members"] is not None and paramgram["mode"] in ["add", "set", "update"]:
            # assign devices to device group
            results = add_group_member(fmgr, paramgram)
            fmgr.govern_response(module=module, results=results,
                                 ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))

        # PROCESS THE GROUP MEMBER DELETES
        if paramgram["grp_members"] is not None and paramgram["mode"] == "delete":
            # remove devices grom a group
            results = delete_group_member(fmgr, paramgram)
            fmgr.govern_response(module=module, results=results,
                                 ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))

        # PROCESS THE GROUP DELETES, ONLY IF GRP_MEMBERS IS NOT NULL TOO
        if paramgram["grp_name"] is not None and paramgram["mode"] == "delete" and paramgram["grp_members"] is None:
            # delete device group
            results = delete_device_group(fmgr, paramgram)
            fmgr.govern_response(module=module, results=results,
                                 ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))
    except Exception as err:
        raise FMGBaseException(err)

    return module.exit_json(**results[1])


if __name__ == "__main__":
    main()
