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
module: fmgr_fwpol_package
version_added: "2.6"
author:
    - Luke Weighall (@lweighall)
    - Andrew Welsh (@Ghilli3)
    - Jim Huber (@p4r4n0y1ng)
short_description: Manages FortiManager Firewall Policies Packages themselves
description:
  -  Manages FortiManager Firewall Policies IPv4 -- create/delete/clone/assign -- manage groups

options:
  adom:
    description:
      - The ADOM the configuration should belong to.
    required: true
    default: root

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

  mode:
    description:
      - Sets one of three modes for managing the object
    choices: ['add', 'set', 'delete']
    default: add

  name:
    description:
      - Name of the FortiManager package or folder
    required: True

  type:
    description:
      - Are we managing packages or folders, or installing packages?
    required: True
    choices: ['pkg','folder','install']

  package_folder:
    description:
      - Name of the folder you want to put the package into
    required: false

  central_nat:
    description:
      - Central NAT setting
    required: false
    choices: ['enable', 'disable']
    default: disable

  fwpolicy_implicit_log:
    description:
      - Implicit Log setting for all IPv4 policies in package
    required: false
    choices: ['enable', 'disable']
    default: disable

  fwpolicy6_implicit_log:
    description:
      - Implicit Log setting for all IPv6 policies in package
    required: false
    choices: ['enable', 'disable']
    default: disable

  inspection_mode:
    description:
      - Inspection mode setting for the policies flow or proxy
    required: false
    choices: ['flow', 'proxy']
    default: flow

  ngfw_mode:
    description:
      - NGFW mode setting for the policies flow or proxy
    required: false
    choices: ['profile-based', 'policy-based']
    default: profile-based

  ssl_ssh_profile:
    description:
      - if policy-based ngfw-mode, refer to firewall ssl-ssh-profile
    required: false

  scope_members:
    description:
      - The devices or scope that you want to assign this policy package to.
    required: false

  scope_members_vdom:
    description:
      - The members VDOM you want to assign the package to
    required: false
    default: root

  parent_folder:
    description:
      - The parent folder name you want to add this object under
    required: false

'''


EXAMPLES = '''
- name: CREATE BASIC POLICY PACKAGE
  fmgr_fwpol_package:
    host: "{{inventory_hostname}}"
    username: "{{ username }}"
    password: "{{ password }}"
    adom: "ansible"
    mode: "add"
    name: "testPackage"
    type: "pkg"

- name: ADD PACKAGE WITH TARGETS
  fmgr_fwpol_package:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    mode: "add"
    adom: "ansible"
    name: "ansibleTestPackage1"
    type: "pkg"
    inspection_mode: "flow"
    ngfw_mode: "profile-based"
    scope_members: "seattle-fgt02, seattle-fgt03"

- name: ADD FOLDER
  fmgr_fwpol_package:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    mode: "add"
    adom: "ansible"
    name: "ansibleTestFolder1"
    type: "folder"

- name: ADD PACKAGE INTO PARENT FOLDER
  fmgr_fwpol_package:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    mode: "set"
    adom: "ansible"
    name: "ansibleTestPackage2"
    type: "pkg"
    parent_folder: "ansibleTestFolder1"

- name: ADD FOLDER INTO PARENT FOLDER
  fmgr_fwpol_package:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    mode: "set"
    adom: "ansible"
    name: "ansibleTestFolder2"
    type: "folder"
    parent_folder: "ansibleTestFolder1"

- name: INSTALL PACKAGE
  fmgr_fwpol_package:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    mode: "set"
    adom: "ansible"
    name: "ansibleTestPackage1"
    type: "install"
    scope_members: "seattle-fgt03, seattle-fgt02"

- name: REMOVE PACKAGE
  fmgr_fwpol_package:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    mode: "delete"
    adom: "ansible"
    name: "ansibleTestPackage1"
    type: "pkg"

- name: REMOVE NESTED PACKAGE
  fmgr_fwpol_package:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    mode: "delete"
    adom: "ansible"
    name: "ansibleTestPackage2"
    type: "pkg"
    parent_folder: "ansibleTestFolder1"

- name: REMOVE NESTED FOLDER
  fmgr_fwpol_package:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    mode: "delete"
    adom: "ansible"
    name: "ansibleTestFolder2"
    type: "folder"
    parent_folder: "ansibleTestFolder1"

- name: REMOVE FOLDER
  fmgr_fwpol_package:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    mode: "delete"
    adom: "ansible"
    name: "ansibleTestFolder1"
    type: "folder"
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


def parse_csv_str_to_list(input_string):
    """
    This function will take a comma seperated string and turn it into a list, removing any spaces next the commas
    that it finds. This is useful for using csv input from ansible parameters and transforming to API requirements.
    """

    if input_string is not None:
        # CREATE VARIABLE AND REMOVE SPACES AROUND COMMAS
        inputs = input_string
        inputs = inputs.replace(", ", ",")
        inputs = inputs.replace(" ,", ",")
        # INIT THE BASE LIST
        input = []
        # FOR EACH ITEM WE CAN SPLIT VIA COMMA ADD IT TO THE LIST
        for obj in inputs.split(","):
            input.append(obj)
        # RETURN THE LIST
        return input
    else:
        # IF THE INPUT STRING WAS EMPTY RETURN NONE/NULL
        return None


def fmgr_fwpol_package(fmg, paramgram):
    """
    This function will create FMGR Firewall Policy Packages, or delete them. It is also capable of assigning packages.
    This function DOES NOT install the package. See the function fmgr_fwpol_package_install()
    """
    if paramgram["mode"] in ['set', 'add']:
        url = '/pm/pkg/adom/{adom}'.format(adom=paramgram["adom"])
        members_list = []

        # CHECK FOR SCOPE MEMBERS AND CREATE THAT DICT
        if paramgram["scope_members"] is not None:
            members = parse_csv_str_to_list(paramgram["scope_members"])
            for member in members:
                scope_dict = {
                    "name": member,
                    "vdom": paramgram["scope_members_vdom"],
                }
                members_list.append(scope_dict)

        # IF PARENT FOLDER IS NOT DEFINED
        if paramgram["parent_folder"] is None:
            datagram = {
                "type": paramgram["type"],
                "name": paramgram["name"],
                "scope member": members_list,
                "package settings": {
                    "central-nat": paramgram["central-nat"],
                    "fwpolicy-implicit-log": paramgram["fwpolicy-implicit-log"],
                    "fwpolicy6-implicit-log": paramgram["fwpolicy6-implicit-log"],
                    "inspection-mode": paramgram["inspection-mode"],
                    "ngfw-mode": paramgram["ngfw-mode"],
                }
            }

            if paramgram["ngfw-mode"] == "policy-based" and paramgram["ssl-ssh-profile"] is not None:
                datagram["package settings"]["ssl-ssh-profile"] = paramgram["ssl-ssh-profile"]

        # IF PARENT FOLDER IS DEFINED
        if paramgram["parent_folder"] is not None:
            datagram = {
                "type": "folder",
                "name": paramgram["parent_folder"],
                "subobj": [{
                    "name": paramgram["name"],
                    "scope member": members_list,
                    "type": "pkg",
                    "package settings": {
                        "central-nat": paramgram["central-nat"],
                        "fwpolicy-implicit-log": paramgram["fwpolicy-implicit-log"],
                        "fwpolicy6-implicit-log": paramgram["fwpolicy6-implicit-log"],
                        "inspection-mode": paramgram["inspection-mode"],
                        "ngfw-mode": paramgram["ngfw-mode"],
                    }
                }]
            }

    # NORMAL DELETE NO PARENT
    if paramgram["mode"] == "delete" and paramgram["parent_folder"] is None:
        datagram = {
            "name": paramgram["name"]
        }
        # SET DELETE URL
        url = '/pm/pkg/adom/{adom}/{name}'.format(adom=paramgram["adom"], name=paramgram["name"])

    # DELETE WITH PARENT
    if paramgram["mode"] == "delete" and paramgram["parent_folder"] is not None:
        datagram = {
            "name": paramgram["name"]
        }
        # SET DELETE URL
        url = '/pm/pkg/adom/{adom}/{parent_folder}/{name}'.format(adom=paramgram["adom"],
                                                                  name=paramgram["name"],
                                                                  parent_folder=paramgram["parent_folder"])

    if paramgram["mode"] == "set":
        response = fmg.set(url, datagram)
        # return response
        # IF MODE = ADD  -- USE THE 'ADD' API CALL MODE
    if paramgram["mode"] == "add":
        response = fmg.add(url, datagram)
        # return response
        # IF MODE = DELETE  -- USE THE DELETE URL AND API CALL MODE
    if paramgram["mode"] == "delete":
        response = fmg.delete(url, datagram)

    return response


def fmgr_fwpol_package_folder(fmg, paramgram):
    """
    This function will create folders for firewall packages. It can create down to two levels deep.
    We haven't yet tested for any more layers below two levels.
    parent_folders for multiple levels may need to defined as "level1/level2/level3" for the URL parameters and such.
    """
    if paramgram["mode"] in ['set', 'add']:
        url = '/pm/pkg/adom/{adom}'.format(adom=paramgram["adom"])
        # IF PARENT FOLDER IS NOT DEFINED
        if paramgram["parent_folder"] is None:
            datagram = {
                "type": paramgram["type"],
                "name": paramgram["name"],
            }

        # IF PARENT FOLDER IS DEFINED
        if paramgram["parent_folder"] is not None:
            datagram = {
                "type": paramgram["type"],
                "name": paramgram["parent_folder"],
                "subobj": [{
                    "name": paramgram["name"],
                    "type": paramgram["type"],

                }]
            }
    # NORMAL DELETE NO PARENT
    if paramgram["mode"] == "delete" and paramgram["parent_folder"] is None:
        datagram = {
            "name": paramgram["name"]
        }
        # SET DELETE URL
        url = '/pm/pkg/adom/{adom}/{name}'.format(adom=paramgram["adom"], name=paramgram["name"])

    # DELETE WITH PARENT
    if paramgram["mode"] == "delete" and paramgram["parent_folder"] is not None:
        datagram = {
            "name": paramgram["name"]
        }
        # SET DELETE URL
        url = '/pm/pkg/adom/{adom}/{parent_folder}/{name}'.format(adom=paramgram["adom"],
                                                                  name=paramgram["name"],
                                                                  parent_folder=paramgram["parent_folder"])
    # IF MODE = SET  -- USE THE 'SET' API CALL MODE
    if paramgram["mode"] == "set":
        response = fmg.set(url, datagram)
    # IF MODE = ADD  -- USE THE 'ADD' API CALL MODE
    if paramgram["mode"] == "add":
        response = fmg.add(url, datagram)
    # IF MODE = DELETE  -- USE THE DELETE URL AND API CALL MODE
    if paramgram["mode"] == "delete":
        response = fmg.delete(url, datagram)

    return response


def fmgr_fwpol_package_install(fmg, paramgram):
    """
    This method/function installs FMGR FW Policy Packages to the scope members defined in the playbook.
    """
    # INIT BLANK MEMBERS LIST
    members_list = []
    # USE THE PARSE CSV FUNCTION TO GET A LIST FORMAT OF THE MEMBERS
    members = parse_csv_str_to_list(paramgram["scope_members"])
    # USE THAT LIST TO BUILD THE DICTIONARIES NEEDED, AND ADD TO THE BLANK MEMBERS LIST
    for member in members:
        scope_dict = {
            "name": member,
            "vdom": paramgram["scope_members_vdom"],
        }
        members_list.append(scope_dict)
    # THEN FOR THE DATAGRAM, USING THE MEMBERS LIST CREATED ABOVE
    datagram = {
        "adom": paramgram["adom"],
        "pkg": paramgram["name"],
        "scope": members_list
    }
    # EXECUTE THE INSTALL REQUEST
    url = '/securityconsole/install/package'
    response = fmg.execute(url, datagram)
    return response


def main():
    argument_spec = dict(
        adom=dict(required=False, type="str", default="root"),
        host=dict(required=True, type="str"),
        username=dict(fallback=(env_fallback, ["ANSIBLE_NET_USERNAME"])),
        password=dict(fallback=(env_fallback, ["ANSIBLE_NET_PASSWORD"]), no_log=True),
        mode=dict(choices=["add", "set", "delete"], type="str", default="add"),

        name=dict(required=False, type="str"),
        type=dict(required=False, type="str", choices=['pkg', 'folder', 'install']),
        package_folder=dict(required=False, type="str"),
        central_nat=dict(required=False, type="str", default="disable", choices=['enable', 'disable']),
        fwpolicy_implicit_log=dict(required=False, type="str", default="disable", choices=['enable', 'disable']),
        fwpolicy6_implicit_log=dict(required=False, type="str", default="disable", choices=['enable', 'disable']),
        inspection_mode=dict(required=False, type="str", default="flow", choices=['flow', 'proxy']),
        ngfw_mode=dict(required=False, type="str", default="profile-based", choices=['profile-based', 'policy-based']),
        ssl_ssh_profile=dict(required=False, type="str"),
        scope_members=dict(required=False, type="str"),
        scope_members_vdom=dict(required=False, type="str", default="root"),
        parent_folder=dict(required=False, type="str"),

    )

    module = AnsibleModule(argument_spec, supports_check_mode=True, )

    # MODULE DATAGRAM
    paramgram = {
        "adom": module.params["adom"],
        "name": module.params["name"],
        "mode": module.params["mode"],
        "type": module.params["type"],
        "package-folder": module.params["package_folder"],
        "central-nat": module.params["central_nat"],
        "fwpolicy-implicit-log": module.params["fwpolicy_implicit_log"],
        "fwpolicy6-implicit-log": module.params["fwpolicy6_implicit_log"],
        "inspection-mode": module.params["inspection_mode"],
        "ngfw-mode": module.params["ngfw_mode"],
        "ssl-ssh-profile": module.params["ssl_ssh_profile"],
        "scope_members": module.params["scope_members"],
        "scope_members_vdom": module.params["scope_members_vdom"],
        "parent_folder": module.params["parent_folder"],
    }

    # VALIDATE REQUIRED ARGUMENTS ARE PASSED; NOT USED IN ARGUMENT_SPEC TO ALLOW PARAMS TO BE CALLED FROM PROVIDER
    # CHECK IF PARAMS ARE SET
    if module.params["host"] is None or module.params["username"] is None:
        module.fail_json(msg="Host and username are required for connection")

    # CHECK IF LOGIN FAILED
    fmg = AnsibleFortiManager(module, module.params["host"], module.params["username"], module.params["password"])
    response = fmg.login()
    if "FortiManager instance connnected" not in str(response):
        module.fail_json(msg="Connection to FortiManager Failed")
    else:
        # START SESSION LOGIC
        # IF THE TYPE IS PACKAGE LETS RUN THAT METHOD
        if paramgram["type"] == "pkg":
            results = fmgr_fwpol_package(fmg, paramgram)
            if results[0] == 0:
                module.exit_json(msg="Package successfully created/deleted", **results[1])
            else:
                module.fail_json(msg="Failed to create/delete custom package", **results[1])

        # IF THE TYPE IS FOLDER LETS RUN THAT METHOD
        if paramgram["type"] == "folder":
            results = fmgr_fwpol_package_folder(fmg, paramgram)
            if results[0] == 0:
                module.exit_json(msg="Folder successfully created/deleted", **results[1])
            else:
                module.fail_json(msg="Failed to add/remove custom package", **results[1])

        # IF THE TYPE IS INSTALL AND NEEDED PARAMETERS ARE DEFINED INSTALL THE PACKAGE
        if paramgram["scope_members"] is not None and paramgram["name"] is not None and paramgram["type"] == "install":
            results = fmgr_fwpol_package_install(fmg, paramgram)
            if results[0] == 0:
                module.exit_json(msg="Install Task Successfully Created", **results[1])
            else:
                module.fail_json(msg="Failed to create install task!", **results[1])

if __name__ == "__main__":
    main()
