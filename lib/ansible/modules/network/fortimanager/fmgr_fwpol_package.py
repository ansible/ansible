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
    - Revision Comments April 2nd 2019
        - Couldn't append to installation target list, only send a complete list. We've added modes for adding and
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
          deleting targets for policy packages.
=======
          deleting just targets for policy packages.
>>>>>>> Added notes and documentation
=======
          deleting targets for policy packages.
>>>>>>> Odd error with shippable. Test was cancelled. Edited docs to re-run.
=======
          deleting just targets for policy packages.
>>>>>>> Added notes and documentation
=======
          deleting targets for policy packages.
>>>>>>> Odd error with shippable. Test was cancelled. Edited docs to re-run.
        - Install mode has been added. Scope_members is no longer taken into account when mode = install.
          Only the existing installation targets on the package will be used. Update installation targets before.
        - Nested folders and packages now work properly. Before they were not.
        - When using modes "add" or "set" with object_type = "pkg" the installation targets are STILL OVERWRITTEN with
          what was supplied under scope_members and scope_groups. Use the add_targets or delete_targets mode first.
        - When using "add_targets" or "delete_targets" for changing installation targets, only scope_members or
          scope_groups is considered for changes to the package. To edit the package settings themselves, use "set".
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
    - Revision Comments May 21st 2019
        - Added support to move packages.
=======
>>>>>>> Added notes and documentation
=======
    - Revision Comments May 21st 2019
        - Added support to move packages.
>>>>>>> Fixes to fmgr_fwpol_package
=======
>>>>>>> Added notes and documentation
=======
    - Revision Comments May 21st 2019
        - Added support to move packages.
>>>>>>> Fixes to fmgr_fwpol_package
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
      - Set will overwrite existing installation targets with scope members.
      - Add will append existing installation targets with scope members.
      - Delete will delete the entire named package.
      - Add Targets will only add the specified scope members to installation targets.
      - Delete Targets will only delete the specified scope members from installation targets.
      - Install will install the package to the assigned installation targets listed on existing package.
      - Update your installation targets BEFORE running install task.
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
    choices: ['add', 'set', 'delete', 'move', 'copy', 'add_targets', 'delete_targets', 'install']
=======
    choices: ['add', 'set', 'delete', 'add_targets', 'delete_targets', 'install']
>>>>>>> Fixed issues:
=======
    choices: ['add', 'set', 'delete', 'move', 'copy', 'add_targets', 'delete_targets', 'install']
>>>>>>> Fixes to fmgr_fwpol_package
=======
    choices: ['add', 'set', 'delete', 'add_targets', 'delete_targets', 'install']
>>>>>>> Fixed issues:
=======
    choices: ['add', 'set', 'delete', 'move', 'copy', 'add_targets', 'delete_targets', 'install']
>>>>>>> Fixes to fmgr_fwpol_package
    default: add

  name:
    description:
      - Name of the FortiManager package or folder.
    required: True

  object_type:
    description:
      - Are we managing packages or package folders?
    required: True
    choices: ['pkg','folder']
<<<<<<< HEAD
<<<<<<< HEAD
=======
=======
>>>>>>> Fixed issues:

<<<<<<< HEAD
<<<<<<< HEAD
  package_folder:
    description:
      - Name of the folder you want to put the package into.
      - Nested folders are supported with forwardslashes. i.e. ansibleTestFolder1/ansibleTestFolder2/etc...
      - Do not include leading or trailing forwardslashes. We take care of that for you.
    required: false
>>>>>>> Fixed issues:

=======
>>>>>>> Removed un-used parameter package_folder. Replaced by parent_folder.
=======
>>>>>>> Removed un-used parameter package_folder. Replaced by parent_folder.
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

<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
=======
=======
>>>>>>> Added Append_scope_members list. Defaults to enable, but if you disable it, it will still allow the overwriting of members.
  append_scope_members:
    description:
      - if enabled, ansible will check for existing scope members and add those to the list before setting
      - if disabled, ansible will simply replace the existing scope members with the list provided.
    required: false
    choices: ['enable', 'disable']
    default: 'enable'

<<<<<<< HEAD
>>>>>>> Added Append_scope_members list. Defaults to enable, but if you disable it, it will still allow the overwriting of members.
=======
>>>>>>> Fixed issues:
=======
>>>>>>> Added Append_scope_members list. Defaults to enable, but if you disable it, it will still allow the overwriting of members.
=======
>>>>>>> Fixed issues:
  scope_groups:
    description:
      - List of groups to add to the scope of the fw pol package
    required: false
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
    version_added: 2.9
=======
>>>>>>> Added Append_scope_members list. Defaults to enable, but if you disable it, it will still allow the overwriting of members.
=======
    version_added: 2.9
>>>>>>> Quick fix to version_added for a parameter
=======
>>>>>>> Added Append_scope_members list. Defaults to enable, but if you disable it, it will still allow the overwriting of members.

  scope_members:
    description:
      - The devices or scope that you want to assign this policy package to. Only assign to one VDOM at a time.
    required: false

  scope_members_vdom:
    description:
      - The members VDOM you want to assign the package to. Only assign to one VDOM at a time.
    required: false
    default: root

  parent_folder:
    description:
      - The parent folder name you want to add this object under.
      - Nested folders are supported with forwardslashes. i.e. ansibleTestFolder1/ansibleTestFolder2/etc...
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
      - Do not include leading or trailing forwardslashes.
    required: false
<<<<<<< HEAD
<<<<<<< HEAD

  target_folder:
    description:
      - Only used when mode equals move.
      - Nested folders are supported with forwardslashes. i.e. ansibleTestFolder1/ansibleTestFolder2/etc...
      - Do not include leading or trailing forwardslashes.
=======
      - Do not include leading or trailing forwardslashes. We take care of that for you.
>>>>>>> Removed un-used parameter package_folder. Replaced by parent_folder.
=======
      - Do not include leading or trailing forwardslashes.
>>>>>>> Shippable cancelled for unknown reason. Doc change to restart.
=======
      - Do not include leading or trailing forwardslashes. We take care of that for you.
>>>>>>> Removed un-used parameter package_folder. Replaced by parent_folder.
    required: false
<<<<<<< HEAD
<<<<<<< HEAD
    version_added: 2.9
=======
=======
>>>>>>> Fixes to fmgr_fwpol_package

  target_folder:
    description:
      - Only used when mode equals move.
      - Nested folders are supported with forwardslashes. i.e. ansibleTestFolder1/ansibleTestFolder2/etc...
<<<<<<< HEAD
      - Do not include leading or trailing forwardslashes.
    required: false
<<<<<<< HEAD
>>>>>>> Fixes to fmgr_fwpol_package
=======
    version_added: 2.9
>>>>>>> Version_added fields missing
=======
      - Do not include leading or trailing forwardslashes. We take care of that for you.
    required: false
>>>>>>> Fixes to fmgr_fwpol_package

  target_name:
    description:
      - Only used when mode equals move.
      - Only used when you want to rename the package in its new location.
      - If None, then NAME will be used.
    required: false
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
    version_added: 2.9
=======
>>>>>>> Added Append_scope_members list. Defaults to enable, but if you disable it, it will still allow the overwriting of members.
=======
>>>>>>> Fixes to fmgr_fwpol_package
=======
    version_added: 2.9
>>>>>>> Version_added fields missing
=======
>>>>>>> Added Append_scope_members list. Defaults to enable, but if you disable it, it will still allow the overwriting of members.
=======
>>>>>>> Fixes to fmgr_fwpol_package
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
    mode: "install"
    adom: "ansible"
    name: "ansibleTestPackage1"

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
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> Fixed issues:
=======
>>>>>>> Fixed issues:
        datagram = {
            "type": paramgram["object_type"],
            "name": paramgram["name"],
            "package settings": {
                "central-nat": paramgram["central-nat"],
                "fwpolicy-implicit-log": paramgram["fwpolicy-implicit-log"],
                "fwpolicy6-implicit-log": paramgram["fwpolicy6-implicit-log"],
                "inspection-mode": paramgram["inspection-mode"],
                "ngfw-mode": paramgram["ngfw-mode"],
<<<<<<< HEAD
<<<<<<< HEAD
=======
=======
>>>>>>> Added Append_scope_members list. Defaults to enable, but if you disable it, it will still allow the overwriting of members.

        # IF PARENT FOLDER IS NOT DEFINED
        if paramgram["parent_folder"] is None:
            datagram = {
                "type": paramgram["object_type"],
                "name": paramgram["name"],
                "scope member": paramgram["assign_to_list"],
                "package settings": {
                    "central-nat": paramgram["central-nat"],
                    "fwpolicy-implicit-log": paramgram["fwpolicy-implicit-log"],
                    "fwpolicy6-implicit-log": paramgram["fwpolicy6-implicit-log"],
                    "inspection-mode": paramgram["inspection-mode"],
                    "ngfw-mode": paramgram["ngfw-mode"],
                }
>>>>>>> Added Append_scope_members list. Defaults to enable, but if you disable it, it will still allow the overwriting of members.
=======
>>>>>>> Fixed issues:
=======
>>>>>>> Fixed issues:
            }
        }

        if paramgram["ngfw-mode"] == "policy-based" and paramgram["ssl-ssh-profile"] is not None:
            datagram["package settings"]["ssl-ssh-profile"] = paramgram["ssl-ssh-profile"]

        # SET THE SCOPE MEMBERS ACCORDING TO MODE AND WHAT WAS SUPPLIED
        if len(paramgram["append_members_list"]) > 0:
            datagram["scope member"] = paramgram["append_members_list"]
        elif len(paramgram["append_members_list"]) == 0:
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
            datagram["scope member"] = {}

        # IF PARENT FOLDER IS DEFINED
        if paramgram["parent_folder"] is not None:
<<<<<<< HEAD
            datagram = fmgr_fwpol_package_create_parent_folder_objects(paramgram, datagram)

    # IF MODE IS MOVE
    if paramgram['mode'] in ["move", "copy"]:
        if paramgram["mode"] == "move":
            url = '/securityconsole/package/move'
        elif paramgram["mode"] == "copy":
            url = '/securityconsole/package/clone'
        if paramgram["target_name"]:
            name = paramgram["target_name"]
        else:
            name = paramgram["name"]
        datagram = {
            "adom": paramgram["adom"],
            "dst_name": name,
            "dst_parent": paramgram["target_folder"],
            "pkg": paramgram["name"]
        }
        if paramgram["parent_folder"]:
            datagram["pkg"] = str(paramgram["parent_folder"]) + "/" + str(paramgram["name"])
        else:
            datagram["pkg"] = str(paramgram["name"])

        if paramgram["mode"] == "copy":
            # SET THE SCOPE MEMBERS ACCORDING TO MODE AND WHAT WAS SUPPLIED
            if len(paramgram["append_members_list"]) > 0:
                datagram["scope member"] = paramgram["append_members_list"]
            elif len(paramgram["append_members_list"]) == 0:
                datagram["scope member"] = {}
=======
            datagram = {
                "type": "folder",
                "name": paramgram["parent_folder"],
                "subobj": [{
                    "name": paramgram["name"],
                    "scope member": paramgram["assign_to_list"],
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
>>>>>>> Added Append_scope_members list. Defaults to enable, but if you disable it, it will still allow the overwriting of members.
=======
            datagram["scope member"] = None
=======
            datagram["scope member"] = {}
>>>>>>> Fixes to fmgr_fwpol_package
=======
            datagram["scope member"] = {}
>>>>>>> Fixes to fmgr_fwpol_package

        # IF PARENT FOLDER IS DEFINED
        if paramgram["parent_folder"] is not None:
            datagram = fmgr_fwpol_package_create_parent_folder_objects(paramgram, datagram)
>>>>>>> Fixed issues:

    # IF MODE IS MOVE
    if paramgram['mode'] in ["move", "copy"]:
        if paramgram["mode"] == "move":
            url = '/securityconsole/package/move'
        elif paramgram["mode"] == "copy":
            url = '/securityconsole/package/clone'
        if paramgram["target_name"]:
            name = paramgram["target_name"]
        else:
            name = paramgram["name"]
        datagram = {
            "adom": paramgram["adom"],
            "dst_name": name,
            "dst_parent": paramgram["target_folder"],
            "pkg": paramgram["name"]
        }
        if paramgram["parent_folder"]:
            datagram["pkg"] = str(paramgram["parent_folder"]) + "/" + str(paramgram["name"])
        else:
            datagram["pkg"] = str(paramgram["name"])

        if paramgram["mode"] == "copy":
            # SET THE SCOPE MEMBERS ACCORDING TO MODE AND WHAT WAS SUPPLIED
            if len(paramgram["append_members_list"]) > 0:
                datagram["scope member"] = paramgram["append_members_list"]
            elif len(paramgram["append_members_list"]) == 0:
                datagram["scope member"] = {}
=======
            datagram["scope member"] = None

        # IF PARENT FOLDER IS DEFINED
        if paramgram["parent_folder"] is not None:
            datagram = fmgr_fwpol_package_create_parent_folder_objects(paramgram, datagram)
>>>>>>> Fixed issues:

    # IF MODE IS MOVE
    if paramgram['mode'] in ["move", "copy"]:
        if paramgram["mode"] == "move":
            url = '/securityconsole/package/move'
        elif paramgram["mode"] == "copy":
            url = '/securityconsole/package/clone'
        if paramgram["target_name"]:
            name = paramgram["target_name"]
        else:
            name = paramgram["name"]
        datagram = {
            "adom": paramgram["adom"],
            "dst_name": name,
            "dst_parent": paramgram["target_folder"],
            "pkg": paramgram["name"]
        }
        if paramgram["parent_folder"]:
            datagram["pkg"] = str(paramgram["parent_folder"]) + "/" + str(paramgram["name"])
        else:
            datagram["pkg"] = str(paramgram["name"])

        if paramgram["mode"] == "copy":
            # SET THE SCOPE MEMBERS ACCORDING TO MODE AND WHAT WAS SUPPLIED
            if len(paramgram["append_members_list"]) > 0:
                datagram["scope member"] = paramgram["append_members_list"]
            elif len(paramgram["append_members_list"]) == 0:
                datagram["scope member"] = {}

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

    if paramgram['mode'] in ["move", "copy"]:
        response = fmgr.process_request(url, datagram, FMGRMethods.EXEC)
    else:
        response = fmgr.process_request(url, datagram, paramgram["mode"])
<<<<<<< HEAD
<<<<<<< HEAD
    return response


def fmgr_fwpol_package_edit_targets(fmgr, paramgram):
    """
    This function will append scope targets to an existing policy package.

    :param fmgr: The fmgr object instance from fmgr_utils.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict

    :return: The response from the FortiManager
    :rtype: dict
    """
    # MERGE APPEND AND EXISTING MEMBERS LISTS BASED ON MODE
    method = None
    members_list = None
    if paramgram["mode"] == "add_targets":
        method = FMGRMethods.ADD
        members_list = paramgram["append_members_list"]
        for member in paramgram["existing_members_list"]:
            if member not in members_list:
                members_list.append(member)

    elif paramgram["mode"] == "delete_targets":
        method = FMGRMethods.DELETE
        members_list = list()
        for member in paramgram["append_members_list"]:
            if member in paramgram["existing_members_list"]:
                members_list.append(member)
    datagram = {
        "data": members_list
    }

    if paramgram["parent_folder"] is not None:
        url = '/pm/pkg/adom/{adom}/{parent_folder}/{name}/scope member'.format(adom=paramgram["adom"],
                                                                               name=paramgram["name"],
                                                                               parent_folder=paramgram["parent_folder"])
    elif paramgram["parent_folder"] is None:
        url = '/pm/pkg/adom/{adom}/{name}/scope member'.format(adom=paramgram["adom"],
                                                               name=paramgram["name"])
    response = fmgr.process_request(url, datagram, method)
=======
>>>>>>> Fixes to fmgr_fwpol_package
    return response


def fmgr_fwpol_package_edit_targets(fmgr, paramgram):
    """
    This function will append scope targets to an existing policy package.

    :param fmgr: The fmgr object instance from fmgr_utils.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict

    :return: The response from the FortiManager
    :rtype: dict
    """
    # MERGE APPEND AND EXISTING MEMBERS LISTS BASED ON MODE
    method = None
    members_list = None
    if paramgram["mode"] == "add_targets":
        method = FMGRMethods.ADD
        members_list = paramgram["append_members_list"]
        for member in paramgram["existing_members_list"]:
            if member not in members_list:
                members_list.append(member)

    elif paramgram["mode"] == "delete_targets":
        method = FMGRMethods.DELETE
        members_list = list()
        for member in paramgram["append_members_list"]:
            if member in paramgram["existing_members_list"]:
                members_list.append(member)
    datagram = {
        "data": members_list
    }

    if paramgram["parent_folder"] is not None:
        url = '/pm/pkg/adom/{adom}/{parent_folder}/{name}/scope member'.format(adom=paramgram["adom"],
                                                                               name=paramgram["name"],
                                                                               parent_folder=paramgram["parent_folder"])
    elif paramgram["parent_folder"] is None:
        url = '/pm/pkg/adom/{adom}/{name}/scope member'.format(adom=paramgram["adom"],
                                                               name=paramgram["name"])
    response = fmgr.process_request(url, datagram, method)
=======
>>>>>>> Fixes to fmgr_fwpol_package
    return response


def fmgr_fwpol_package_edit_targets(fmgr, paramgram):
    """
    This function will append scope targets to an existing policy package.

    :param fmgr: The fmgr object instance from fmgr_utils.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict

    :return: The response from the FortiManager
    :rtype: dict
    """
    # MERGE APPEND AND EXISTING MEMBERS LISTS BASED ON MODE
    method = None
    members_list = None
    if paramgram["mode"] == "add_targets":
        method = FMGRMethods.ADD
        members_list = paramgram["append_members_list"]
        for member in paramgram["existing_members_list"]:
            if member not in members_list:
                members_list.append(member)

    elif paramgram["mode"] == "delete_targets":
        method = FMGRMethods.DELETE
        members_list = list()
        for member in paramgram["append_members_list"]:
            if member in paramgram["existing_members_list"]:
                members_list.append(member)
    datagram = {
        "data": members_list
    }

    if paramgram["parent_folder"] is not None:
        url = '/pm/pkg/adom/{adom}/{parent_folder}/{name}/scope member'.format(adom=paramgram["adom"],
                                                                               name=paramgram["name"],
                                                                               parent_folder=paramgram["parent_folder"])
    elif paramgram["parent_folder"] is None:
        url = '/pm/pkg/adom/{adom}/{name}/scope member'.format(adom=paramgram["adom"],
                                                               name=paramgram["name"])
    response = fmgr.process_request(url, datagram, method)
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

        datagram = {
            "type": paramgram["object_type"],
            "name": paramgram["name"],
        }

        # IF PARENT FOLDER IS DEFINED
        if paramgram["parent_folder"] is not None:
            datagram = fmgr_fwpol_package_create_parent_folder_objects(paramgram, datagram)

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
    datagram = {
        "adom": paramgram["adom"],
        "pkg": paramgram["name"],
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
=======
        "scope": paramgram["assign_to_list"]
>>>>>>> Added Append_scope_members list. Defaults to enable, but if you disable it, it will still allow the overwriting of members.
=======
>>>>>>> Fixed issues:
=======
        "scope": paramgram["assign_to_list"]
>>>>>>> Added Append_scope_members list. Defaults to enable, but if you disable it, it will still allow the overwriting of members.
=======
>>>>>>> Fixed issues:
    }
    if paramgram["parent_folder"]:
        new_path = str(paramgram["parent_folder"]) + "/" + str(paramgram["name"])
        datagram["pkg"] = new_path

    # EXECUTE THE INSTALL REQUEST
    url = '/securityconsole/install/package'
    response = fmgr.process_request(url, datagram, FMGRMethods.EXEC)
    return response


def fmgr_fwpol_package_get_details(fmgr, paramgram):
    """
    This method/function will attempt to get existing package details, and append findings to the paramgram.
    If nothing is found, the paramgram additions are simply empty.

    :param fmgr: The fmgr object instance from fmgr_utils.py
    :type fmgr: class object
    :param paramgram: The formatted dictionary of options to process
    :type paramgram: dict

    :return: The response from the FortiManager
    :rtype: dict
    """
    # CHECK FOR SCOPE MEMBERS AND CREATE THAT MEMBERS LIST
    # WE MUST PROPERLY FORMAT THE JSON FOR SCOPE MEMBERS WITH VDOMS
    members_list = list()
    if paramgram["scope_members"] is not None and paramgram["mode"] in ['add', 'set', 'add_targets', 'delete_targets']:
        if isinstance(paramgram["scope_members"], list):
            members = paramgram["scope_members"]
        if isinstance(paramgram["scope_members"], str):
            members = FMGRCommon.split_comma_strings_into_lists(paramgram["scope_members"])
        for member in members:
            scope_dict = {
                "name": member,
                "vdom": paramgram["scope_members_vdom"],
            }
            members_list.append(scope_dict)

    # CHECK FOR SCOPE GROUPS AND ADD THAT TO THE MEMBERS LIST
    # WE MUST PROPERLY FORMAT THE JSON FOR SCOPE GROUPS
    if paramgram["scope_groups"] is not None and paramgram["mode"] in ['add', 'set', 'add_targets', 'delete_targets']:
        if isinstance(paramgram["scope_groups"], list):
            members = paramgram["scope_groups"]
        if isinstance(paramgram["scope_groups"], str):
            members = FMGRCommon.split_comma_strings_into_lists(paramgram["scope_groups"])
        for member in members:
            scope_dict = {
                "name": member
            }
            members_list.append(scope_dict)

    # CHECK FOR AN EXISTING POLICY PACKAGE, AND GET ITS MEMBERS SO WE DON'T OVERWRITE THEM WITH NOTHING
    pol_datagram = {"type": paramgram["object_type"], "name": paramgram["name"]}
    if paramgram["parent_folder"]:
        pol_package_url = '/pm/pkg/adom/{adom}/{folder}/{pkg_name}'.format(adom=paramgram["adom"],
                                                                           pkg_name=paramgram["name"],
                                                                           folder=paramgram["parent_folder"])
    else:
        pol_package_url = '/pm/pkg/adom/{adom}/{pkg_name}'.format(adom=paramgram["adom"],
                                                                  pkg_name=paramgram["name"])
    pol_package = fmgr.process_request(pol_package_url, pol_datagram, FMGRMethods.GET)
    existing_members = None
    package_exists = None
    if len(pol_package) == 2:
        package_exists = True
        try:
            existing_members = pol_package[1]["scope member"]
        except Exception as err:
            existing_members = list()
    else:
        package_exists = False

    # ADD COLLECTED DATA TO PARAMGRAM FOR USE IN METHODS
    paramgram["existing_members_list"] = existing_members
    paramgram["append_members_list"] = members_list
    paramgram["package_exists"] = package_exists

    return paramgram


def fmgr_fwpol_package_create_parent_folder_objects(paramgram, datagram):
    """
    This function/method will take a paramgram with parent folders defined, and create the proper structure
    so that objects are nested correctly.

    :param paramgram: The paramgram used
    :type paramgram: dict
    :param datagram: The datagram, so far, as created by another function.
    :type datagram: dict

    :return: new_datagram
    """
    # SPLIT THE PARENT FOLDER INTO A LIST BASED ON FORWARD SLASHES
    # FORM THE DATAGRAM USING TEMPLATE ABOVE WITH THE PACKAGE NESTED IN A SUBOBJ
    subobj_list = list()
    subobj_list.append(datagram)
    new_datagram = {
        "type": "folder",
        "name": paramgram["parent_folder"],
        "subobj": subobj_list
    }
    parent_folders = paramgram["parent_folder"].split("/")
    # LOOP THROUGH PARENT FOLDERS AND ADD AS MANY SUB OBJECT NESTED DICTS AS REQUIRED
    # WE'RE BUILDING THE SUBOBJ NESTED OBJECT "INSIDE OUT"
    num_of_parents = len(parent_folders)
    if num_of_parents > 1:
        parent_list_position = num_of_parents - 1
        # REPLACE THE EXISTING PARENT FOLDER STRING WITH SLASHES, WITH THE BOTTOM MOST NESTED FOLDER
        new_datagram["name"] = parent_folders[parent_list_position]
        parent_list_position -= 1
        while parent_list_position >= 0:
            new_subobj_list = list()
            new_subobj_list.append(new_datagram)
            new_datagram = {
                "type": "folder",
                "name": parent_folders[parent_list_position],
                "subobj": new_subobj_list
            }
            parent_list_position -= 1
        # SET DATAGRAM TO THE NEWLY NESTED DATAGRAM
    return new_datagram


def main():
    argument_spec = dict(
        adom=dict(required=False, type="str", default="root"),
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
        mode=dict(choices=["add", "set", "delete", "move", "copy", "add_targets", "delete_targets", "install"],
=======
        mode=dict(choices=["add", "set", "delete", "add_targets", "delete_targets", "install"],
>>>>>>> Fixed issues:
=======
        mode=dict(choices=["add", "set", "delete", "move", "copy", "add_targets", "delete_targets", "install"],
>>>>>>> Fixes to fmgr_fwpol_package
=======
        mode=dict(choices=["add", "set", "delete", "add_targets", "delete_targets", "install"],
>>>>>>> Fixed issues:
=======
        mode=dict(choices=["add", "set", "delete", "move", "copy", "add_targets", "delete_targets", "install"],
>>>>>>> Fixes to fmgr_fwpol_package
                  type="str", default="add"),

        name=dict(required=False, type="str"),
        object_type=dict(required=True, type="str", choices=['pkg', 'folder']),
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
=======
=======
>>>>>>> Fixed issues:
        package_folder=dict(required=False, type="str"),
>>>>>>> Fixed issues:
=======
>>>>>>> Removed un-used parameter package_folder. Replaced by parent_folder.
=======
>>>>>>> Removed un-used parameter package_folder. Replaced by parent_folder.
        central_nat=dict(required=False, type="str", default="disable", choices=['enable', 'disable']),
        fwpolicy_implicit_log=dict(required=False, type="str", default="disable", choices=['enable', 'disable']),
        fwpolicy6_implicit_log=dict(required=False, type="str", default="disable", choices=['enable', 'disable']),
        inspection_mode=dict(required=False, type="str", default="flow", choices=['flow', 'proxy']),
        ngfw_mode=dict(required=False, type="str", default="profile-based", choices=['profile-based', 'policy-based']),
        ssl_ssh_profile=dict(required=False, type="str"),
        scope_groups=dict(required=False, type="str"),
        scope_members=dict(required=False, type="str"),
        scope_members_vdom=dict(required=False, type="str", default="root"),
        parent_folder=dict(required=False, type="str"),
        target_folder=dict(required=False, type="str"),
        target_name=dict(required=False, type="str"),

    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False,)
    # MODULE DATAGRAM
    paramgram = {
        "adom": module.params["adom"],
        "name": module.params["name"],
        "mode": module.params["mode"],
        "object_type": module.params["object_type"],
        "central-nat": module.params["central_nat"],
        "fwpolicy-implicit-log": module.params["fwpolicy_implicit_log"],
        "fwpolicy6-implicit-log": module.params["fwpolicy6_implicit_log"],
        "inspection-mode": module.params["inspection_mode"],
        "ngfw-mode": module.params["ngfw_mode"],
        "ssl-ssh-profile": module.params["ssl_ssh_profile"],
        "scope_groups": module.params["scope_groups"],
        "scope_members": module.params["scope_members"],
        "scope_members_vdom": module.params["scope_members_vdom"],
        "parent_folder": module.params["parent_folder"],
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
        "target_folder": module.params["target_folder"],
        "target_name": module.params["target_name"],
        "append_members_list": list(),
        "existing_members_list": list(),
        "package_exists": None,
=======
        "assign_to_list": list()
>>>>>>> Added Append_scope_members list. Defaults to enable, but if you disable it, it will still allow the overwriting of members.
=======
=======
        "target_folder": module.params["target_folder"],
        "target_name": module.params["target_name"],
>>>>>>> Fixes to fmgr_fwpol_package
=======
        "target_folder": module.params["target_folder"],
        "target_name": module.params["target_name"],
>>>>>>> Fixes to fmgr_fwpol_package
        "append_members_list": list(),
        "existing_members_list": list(),
        "package_exists": None,
>>>>>>> Fixed issues:
=======
        "assign_to_list": list()
>>>>>>> Added Append_scope_members list. Defaults to enable, but if you disable it, it will still allow the overwriting of members.
=======
        "append_members_list": list(),
        "existing_members_list": list(),
        "package_exists": None,
>>>>>>> Fixed issues:
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

<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
    # QUERY FORTIMANAGER FOR EXISTING PACKAGE DETAILS AND UPDATE PARAMGRAM
    paramgram = fmgr_fwpol_package_get_details(fmgr, paramgram)
=======
=======
>>>>>>> Added Append_scope_members list. Defaults to enable, but if you disable it, it will still allow the overwriting of members.
    # CHECK FOR SCOPE MEMBERS AND CREATE THAT MEMBERS LIST
    members_list = list()
    if paramgram["scope_members"] is not None and paramgram["mode"] in ['add', 'set']:
        if isinstance(paramgram["scope_members"], list):
            members = paramgram["scope_members"]
        if isinstance(paramgram["scope_members"], str):
            members = FMGRCommon.split_comma_strings_into_lists(paramgram["scope_members"])
        for member in members:
            scope_dict = {
                "name": member,
                "vdom": paramgram["scope_members_vdom"],
            }
            members_list.append(scope_dict)

    # CHECK FOR SCOPE GROUPS AND ADD THAT TO THE MEMBERS LIST
    if paramgram["scope_groups"] is not None and paramgram["mode"] in ['add', 'set']:
        if isinstance(paramgram["scope_groups"], list):
            members = paramgram["scope_groups"]
        if isinstance(paramgram["scope_groups"], str):
            members = FMGRCommon.split_comma_strings_into_lists(paramgram["scope_groups"])
        for member in members:
            scope_dict = {
                "name": member
            }
            members_list.append(scope_dict)
<<<<<<< HEAD
=======
    # QUERY FORTIMANAGER FOR EXISTING PACKAGE DETAILS AND UPDATE PARAMGRAM
    paramgram = fmgr_fwpol_package_get_details(fmgr, paramgram)
>>>>>>> Fixed issues:

    try:
        if paramgram["object_type"] == "pkg" and paramgram["mode"] in ["add", "set", "delete", "move", "copy"]:
            results = fmgr_fwpol_package(fmgr, paramgram)
            fmgr.govern_response(module=module, results=results,
                                 ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))
    except Exception as err:
        raise FMGBaseException(err)

<<<<<<< HEAD
    paramgram["assign_to_list"] = members_list
>>>>>>> Added Append_scope_members list. Defaults to enable, but if you disable it, it will still allow the overwriting of members.
=======
=======
    # QUERY FORTIMANAGER FOR EXISTING PACKAGE DETAILS AND UPDATE PARAMGRAM
    paramgram = fmgr_fwpol_package_get_details(fmgr, paramgram)
>>>>>>> Fixed issues:

    try:
        if paramgram["object_type"] == "pkg" and paramgram["mode"] in ["add", "set", "delete", "move", "copy"]:
            results = fmgr_fwpol_package(fmgr, paramgram)
            fmgr.govern_response(module=module, results=results,
                                 ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))
    except Exception as err:
        raise FMGBaseException(err)

<<<<<<< HEAD
    paramgram["assign_to_list"] = members_list
>>>>>>> Added Append_scope_members list. Defaults to enable, but if you disable it, it will still allow the overwriting of members.

    try:
        if paramgram["object_type"] == "pkg" and paramgram["mode"] in ["add", "set", "delete", "move", "copy"]:
            results = fmgr_fwpol_package(fmgr, paramgram)
=======
    try:
        if paramgram["object_type"] == "pkg" and paramgram["package_exists"] \
                and len(paramgram["append_members_list"]) > 0 \
                and paramgram["mode"] in ['add_targets', 'delete_targets']:
            results = fmgr_fwpol_package_edit_targets(fmgr, paramgram)
>>>>>>> Fixed issues:
            fmgr.govern_response(module=module, results=results,
                                 ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))
    except Exception as err:
        raise FMGBaseException(err)

    try:
=======
    try:
>>>>>>> Fixed issues:
        if paramgram["object_type"] == "pkg" and paramgram["package_exists"] \
                and len(paramgram["append_members_list"]) > 0 \
                and paramgram["mode"] in ['add_targets', 'delete_targets']:
            results = fmgr_fwpol_package_edit_targets(fmgr, paramgram)
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
        if paramgram["name"] is not None and paramgram["object_type"] == "pkg" and paramgram["mode"] == "install":
            results = fmgr_fwpol_package_install(fmgr, paramgram)
            fmgr.govern_response(module=module, results=results,
                                 ansible_facts=fmgr.construct_ansible_facts(results, module.params, paramgram))
    except Exception as err:
        raise FMGBaseException(err)

    return module.exit_json(**results[1])


if __name__ == "__main__":
    main()
