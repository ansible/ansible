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
version_added: "2.8"
notes:
    - Full Documentation at U(https://ftnt-ansible-docs.readthedocs.io/en/latest/).
author:
    - Luke Weighall (@lweighall)
    - Andrew Welsh (@Ghilli3)
    - Jim Huber (@p4r4n0y1ng)
short_description: Manages FortiManager Firewall Policies Packages.
description:
  -  Manages FortiManager Firewall Policies Packages. Policy Packages contain one or more Firewall Policies/Rules and
     are distritbuted via FortiManager to Fortigates.
  -  This module controls the creation/edit/delete/assign of these packages.

options:
  adom:
    description:
      - The ADOM the configuration should belong to.
    required: false
    default: root

  mode:
    description:
      - Sets one of three modes for managing the object.
    choices: ['add', 'set', 'delete']
    default: add

  name:
    description:
      - Name of the FortiManager package or folder.
    required: True

  object_type:
    description:
      - Are we managing packages or folders, or installing packages?
    required: True
    choices: ['pkg','folder','install']

  package_folder:
    description:
      - Name of the folder you want to put the package into.
    required: false

  central_nat:
    description:
      - Central NAT setting.
    required: false
    choices: ['enable', 'disable']
    default: disable

  fwpolicy_implicit_log:
    description:
      - Implicit Log setting for all IPv4 policies in package.
    required: false
    choices: ['enable', 'disable']
    default: disable

  fwpolicy6_implicit_log:
    description:
      - Implicit Log setting for all IPv6 policies in package.
    required: false
    choices: ['enable', 'disable']
    default: disable

  inspection_mode:
    description:
      - Inspection mode setting for the policies flow or proxy.
    required: false
    choices: ['flow', 'proxy']
    default: flow

  ngfw_mode:
    description:
      - NGFW mode setting for the policies flow or proxy.
    required: false
    choices: ['profile-based', 'policy-based']
    default: profile-based

  ssl_ssh_profile:
    description:
      - if policy-based ngfw-mode, refer to firewall ssl-ssh-profile.
    required: false

  scope_members:
    description:
      - The devices or scope that you want to assign this policy package to.
    required: false

  scope_members_vdom:
    description:
      - The members VDOM you want to assign the package to.
    required: false
    default: root

  parent_folder:
    description:
      - The parent folder name you want to add this object under.
    required: false

'''


EXAMPLES = '''
- name: CREATE BASIC POLICY PACKAGE
  fmgr_fwpol_package:
    adom: "ansible"
    mode: "add"
    name: "testPackage"
    object_type: "pkg"

- name: ADD PACKAGE WITH TARGETS
  fmgr_fwpol_package:
    mode: "add"
    adom: "ansible"
    name: "ansibleTestPackage1"
    object_type: "pkg"
    inspection_mode: "flow"
    ngfw_mode: "profile-based"
    scope_members: "seattle-fgt02, seattle-fgt03"

- name: ADD FOLDER
  fmgr_fwpol_package:
    mode: "add"
    adom: "ansible"
    name: "ansibleTestFolder1"
    object_type: "folder"

- name: ADD PACKAGE INTO PARENT FOLDER
  fmgr_fwpol_package:
    mode: "set"
    adom: "ansible"
    name: "ansibleTestPackage2"
    object_type: "pkg"
    parent_folder: "ansibleTestFolder1"

- name: ADD FOLDER INTO PARENT FOLDER
  fmgr_fwpol_package:
    mode: "set"
    adom: "ansible"
    name: "ansibleTestFolder2"
    object_type: "folder"
    parent_folder: "ansibleTestFolder1"

- name: INSTALL PACKAGE
  fmgr_fwpol_package:
    mode: "set"
    adom: "ansible"
    name: "ansibleTestPackage1"
    object_type: "install"
    scope_members: "seattle-fgt03, seattle-fgt02"

- name: REMOVE PACKAGE
  fmgr_fwpol_package:
    mode: "delete"
    adom: "ansible"
    name: "ansibleTestPackage1"
    object_type: "pkg"

- name: REMOVE NESTED PACKAGE
  fmgr_fwpol_package:
    mode: "delete"
    adom: "ansible"
    name: "ansibleTestPackage2"
    object_type: "pkg"
    parent_folder: "ansibleTestFolder1"

- name: REMOVE NESTED FOLDER
  fmgr_fwpol_package:
    mode: "delete"
    adom: "ansible"
    name: "ansibleTestFolder2"
    object_type: "folder"
    parent_folder: "ansibleTestFolder1"

- name: REMOVE FOLDER
  fmgr_fwpol_package:
    mode: "delete"
    adom: "ansible"
    name: "ansibleTestFolder1"
    object_type: "folder"
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


def fmgr_fwpol_package(fmgr, paramgram):
    """
    This function will create FMGR Firewall Policy Packages, or delete them. It is also capable of assigning packages.
    This function DOES NOT install the package. See the function fmgr_fwpol_package_install()

    :param fmgr: The fmgr object instance from fmgr_utils.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict

    :return: The response from the FortiManager
    :rtype: dict
    """
    if paramgram["mode"] in ['set', 'add']:
        url = '/pm/pkg/adom/{adom}'.format(adom=paramgram["adom"])
        members_list = []

        # CHECK FOR SCOPE MEMBERS AND CREATE THAT DICT
        if paramgram["scope_members"] is not None:
            members = FMGRCommon.split_comma_strings_into_lists(paramgram["scope_members"])
            for member in members:
                scope_dict = {
                    "name": member,
                    "vdom": paramgram["scope_members_vdom"],
                }
                members_list.append(scope_dict)

        # IF PARENT FOLDER IS NOT DEFINED
        if paramgram["parent_folder"] is None:
            datagram = {
                "type": paramgram["object_type"],
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

    response = fmgr.process_request(url, datagram, paramgram["mode"])
    return response


def fmgr_fwpol_package_folder(fmgr, paramgram):
    """
    This function will create folders for firewall packages. It can create down to two levels deep.
    We haven't yet tested for any more layers below two levels.
    parent_folders for multiple levels may need to defined as "level1/level2/level3" for the URL parameters and such.

    :param fmgr: The fmgr object instance from fmgr_utils.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict

    :return: The response from the FortiManager
    :rtype: dict
    """
    if paramgram["mode"] in ['set', 'add']:
        url = '/pm/pkg/adom/{adom}'.format(adom=paramgram["adom"])
        # IF PARENT FOLDER IS NOT DEFINED
        if paramgram["parent_folder"] is None:
            datagram = {
                "type": paramgram["object_type"],
                "name": paramgram["name"],
            }

        # IF PARENT FOLDER IS DEFINED
        if paramgram["parent_folder"] is not None:
            datagram = {
                "type": paramgram["object_type"],
                "name": paramgram["parent_folder"],
                "subobj": [{
                    "name": paramgram["name"],
                    "type": paramgram["object_type"],

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

    response = fmgr.process_request(url, datagram, paramgram["mode"])
    return response


def fmgr_fwpol_package_install(fmgr, paramgram):
    """
    This method/function installs FMGR FW Policy Packages to the scope members defined in the playbook.

    :param fmgr: The fmgr object instance from fmgr_utils.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict

    :return: The response from the FortiManager
    :rtype: dict
    """
    # INIT BLANK MEMBERS LIST
    members_list = []
    # USE THE PARSE CSV FUNCTION TO GET A LIST FORMAT OF THE MEMBERS
    members = FMGRCommon.split_comma_strings_into_lists(paramgram["scope_members"])
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
    response = fmgr.process_request(url, datagram, FMGRMethods.EXEC)
    return response


def main():
    argument_spec = dict(
        adom=dict(required=False, type="str", default="root"),
        mode=dict(choices=["add", "set", "delete"], type="str", default="add"),

        name=dict(required=False, type="str"),
        object_type=dict(required=True, type="str", choices=['pkg', 'folder', 'install']),
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

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False, )
    # MODULE DATAGRAM
    paramgram = {
        "adom": module.params["adom"],
        "name": module.params["name"],
        "mode": module.params["mode"],
        "object_type": module.params["object_type"],
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
        if paramgram["object_type"] == "pkg":
            results = fmgr_fwpol_package(fmgr, paramgram)
            fmgr.govern_response(module=module, results=results,
                                 ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))
    except Exception as err:
        raise FMGBaseException(err)

    try:
        # IF THE object_type IS FOLDER LETS RUN THAT METHOD
        if paramgram["object_type"] == "folder":
            results = fmgr_fwpol_package_folder(fmgr, paramgram)
            fmgr.govern_response(module=module, results=results,
                                 ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))
    except Exception as err:
        raise FMGBaseException(err)

    try:
        # IF THE object_type IS INSTALL AND NEEDED PARAMETERS ARE DEFINED INSTALL THE PACKAGE
        if paramgram["scope_members"] is not None and paramgram["name"] is not None and\
                paramgram["object_type"] == "install":
            results = fmgr_fwpol_package_install(fmgr, paramgram)
            fmgr.govern_response(module=module, results=results,
                                 ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))
    except Exception as err:
        raise FMGBaseException(err)

    return module.exit_json(**results[1])


if __name__ == "__main__":
    main()
