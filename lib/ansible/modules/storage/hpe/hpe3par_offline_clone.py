#!/usr/bin/python

# (C) Copyright 2018 Hewlett Packard Enterprise Development LP
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of version 3 of the GNU General Public License as
# published by the Free Software Foundation.  Alternatively, at your
# choice, you may also redistribute it and/or modify it under the terms
# of the Apache License, version 2.0, available at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <https://www.gnu.org/licenses/>

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
author: "Farhan Nomani (nomani@hpe.com)"
description: "On HPE 3PAR - Create Offline Clone. - Delete Clone. - Resync
 Clone. - Stop Cloning."
module: hpe3par_offline_clone
options:
  base_volume_name:
    description:
      - "Specifies the source volume.\nRequired with action present, absent,
       stop\n"
    required: false
  clone_name:
    description:
      - "Specifies the destination volume."
    required: true
  dest_cpg:
    description:
      - "Specifies the destination CPG for an online copy."
    required: false
  priority:
    choices:
      - HIGH
      - MEDIUM
      - LOW
    default: MEDIUM
    description:
      - "Priority of action."
    required: false
  save_snapshot:
    description:
      - "Enables (true) or disables (false) saving the the snapshot of the
       source volume after completing the copy of the volume.\n"
    required: false
    type: bool
  skip_zero:
    description:
      - "Enables (true) or disables (false) copying only allocated portions of
       the source VV from a thin provisioned source."
    required: false
    type: bool
  state:
    choices:
      - present
      - absent
      - resync
      - stop
    description:
      - "Whether the specified Clone should exist or not. State also provides
       actions to resync and stop clone\n"
    required: true
extends_documentation_fragment: hpe3par
short_description: "Manage HPE 3PAR Offline Clone"
version_added: "2.4"
'''

EXAMPLES = r'''
    - name: Create Clone {{ clone_name }}
      hpe3par_offline_clone:
        storage_system_ip="{{ storage_system_ip }}"
        storage_system_username="{{ storage_system_username }}"
        storage_system_password="{{ storage_system_password }}"
        state=present
        clone_name={{ clone_name }}
        base_volume_name="{{ volume_name }}"
        dest_cpg="{{ cpg }}"
        priority="MEDIUM"

    - name: Stop Clone {{ clone_name }}
      hpe3par_offline_clone:
        storage_system_ip="{{ storage_system_ip }}"
        storage_system_username="{{ storage_system_username }}"
        storage_system_password="{{ storage_system_password }}"
        state=stop
        clone_name={{ clone_name }}
        base_volume_name="{{ volume_name }}"

    - name: Delete clone {{ clone_name }}
      hpe3par_offline_clone:
        storage_system_ip="{{ storage_system_ip }}"
        storage_system_username="{{ storage_system_username }}"
        storage_system_password="{{ storage_system_password }}"
        state=absent
        clone_name={{ clone_name }}
        base_volume_name="{{ volume_name }}"
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
from hpe3par_sdk import client


def create_offline_clone(
        client_obj,
        storage_system_ip,
        storage_system_username,
        storage_system_password,
        clone_name,
        base_volume_name,
        dest_cpg,
        skip_zero,
        save_snapshot,
        priority):
    if storage_system_username is None or storage_system_password is None:
        return (
            False,
            False,
            "Offline clone create failed. Storage system username or password \
is null",
            {})
    if clone_name is None:
        return (
            False,
            False,
            "Offline clone create failed. Clone name is null",
            {})
    if len(clone_name) < 1 or len(clone_name) > 31:
        return (False, False, "Clone create failed. Clone name must be atleast 1 character and more than 31 characters", {})
    if base_volume_name is None:
        return (
            False,
            False,
            "Offline clone create failed. Base volume name is null",
            {})
    if len(base_volume_name) < 1 or len(base_volume_name) > 31:
        return (False, False, "Clone create failed. Base volume name must be atleast 1 character and more than 31 characters", {})
    try:
        client_obj.login(storage_system_username, storage_system_password)
        client_obj.setSSHOptions(
            storage_system_ip,
            storage_system_username,
            storage_system_password)
        if not client_obj.onlinePhysicalCopyExists(
                base_volume_name,
                clone_name) and not client_obj.offlinePhysicalCopyExists(
                    base_volume_name,
                    clone_name):
            optional = {
                'online': False,
                'saveSnapshot': save_snapshot,
                'priority': getattr(
                    client.HPE3ParClient.TaskPriority,
                    priority)}
            if skip_zero:
                optional['skipZero'] = skip_zero
            client_obj.copyVolume(
                base_volume_name,
                clone_name,
                dest_cpg,
                optional)
        else:
            return (
                True,
                False,
                "Clone already exists / creation in progress. Nothing to do.",
                {})
    except Exception as e:
        return (False, False, "Offline Clone creation failed | %s" % (e), {})
    finally:
        client_obj.logout()
    return (
        True,
        True,
        "Created Offline Clone %s successfully." %
        clone_name,
        {})


def resync_clone(
        client_obj,
        storage_system_username,
        storage_system_password,
        clone_name):
    if storage_system_username is None or storage_system_password is None:
        return (
            False,
            False,
            "Offline clone resync failed. Storage system username or password \
is null",
            {})
    if clone_name is None:
        return (
            False,
            False,
            "Offline clone resync failed. Clone name is null",
            {})
    if len(clone_name) < 1 or len(clone_name) > 31:
        return (False, False, "Clone create failed. Clone name must be atleast 1 character and more than 31 characters", {})
    try:
        client_obj.login(storage_system_username, storage_system_password)
        client_obj.resyncPhysicalCopy(clone_name)
    except Exception as e:
        return (False, False, "Offline clone resync failed | %s" % e, {})
    finally:
        client_obj.logout()
    return (
        True,
        True,
        "Resync-ed Offline Clone %s successfully." %
        clone_name,
        {})


def stop_clone(
        client_obj,
        storage_system_ip,
        storage_system_username,
        storage_system_password,
        clone_name,
        base_volume_name):
    if storage_system_username is None or storage_system_password is None:
        return (
            False,
            False,
            "Offline clone stop failed. Storage system username or password \
is null",
            {})
    if clone_name is None:
        return (
            False,
            False,
            "Offline clone stop failed. Clone name is null",
            {})
    if len(clone_name) < 1 or len(clone_name) > 31:
        return (False, False, "Clone create failed. Clone name must be atleast 1 character and more than 31 characters", {})
    if base_volume_name is None:
        return (
            False,
            False,
            "Offline clone stop failed. Base volume name is null",
            {})
    if len(base_volume_name) < 1 or len(base_volume_name) > 31:
        return (False, False, "Clone create failed. Base volume name must be atleast 1 character and more than 31 characters", {})
    try:
        client_obj.login(storage_system_username, storage_system_password)
        client_obj.setSSHOptions(
            storage_system_ip,
            storage_system_username,
            storage_system_password)
        if client_obj.volumeExists(
            clone_name) and client_obj.offlinePhysicalCopyExists(
                base_volume_name, clone_name):
            client_obj.stopOfflinePhysicalCopy(clone_name)
        else:
            return (True, False, "Offline Cloning not in progress", {})
    except Exception as e:
        return (False, False, "Offline Clone stop failed | %s" % (e), {})
    finally:
        client_obj.logout()
    return (
        True,
        True,
        "Stopped Offline Clone %s successfully." %
        clone_name,
        {})


def delete_clone(
        client_obj,
        storage_system_ip,
        storage_system_username,
        storage_system_password,
        clone_name,
        base_volume_name):
    if storage_system_username is None or storage_system_password is None:
        return (
            False,
            False,
            "Offline clone delete failed. Storage system username or password \
is null",
            {})
    if clone_name is None:
        return (
            False,
            False,
            "Offline clone delete failed. Clone name is null",
            {})
    if len(clone_name) < 1 or len(clone_name) > 31:
        return (False, False, "Clone create failed. Clone name must be atleast 1 character and more than 31 characters", {})
    if base_volume_name is None:
        return (
            False,
            False,
            "Offline clone delete failed. Base volume name is null",
            {})
    if len(base_volume_name) < 1 or len(base_volume_name) > 31:
        return (False, False, "Clone create failed. Base volume name must be atleast 1 character and more than 31 characters", {})
    try:
        client_obj.login(storage_system_username, storage_system_password)
        client_obj.setSSHOptions(
            storage_system_ip,
            storage_system_username,
            storage_system_password)
        if client_obj.volumeExists(
                clone_name) and not client_obj.onlinePhysicalCopyExists(
                base_volume_name,
                clone_name) and not client_obj.offlinePhysicalCopyExists(
                base_volume_name, clone_name):
            client_obj.deleteVolume(clone_name)
        else:
            return (
                False,
                False,
                "Clone/Volume is busy. Cannot be deleted",
                {})
    except Exception as e:
        return (False, False, "Offline Clone delete failed | %s" % (e), {})
    finally:
        client_obj.logout()
    return (
        True,
        True,
        "Deleted Offline Clone %s successfully." %
        clone_name,
        {})


def main():

    fields = {
        "state": {
            "required": True,
            "choices": ['present', 'absent', 'resync', 'stop'],
            "type": 'str'
        },
        "storage_system_ip": {
            "required": True,
            "type": "str"
        },
        "storage_system_username": {
            "required": True,
            "type": "str",
            "no_log": True
        },
        "storage_system_password": {
            "required": True,
            "type": "str",
            "no_log": True
        },
        "clone_name": {
            "required": True,
            "type": "str"
        },
        "base_volume_name": {
            "required": False,
            "type": "str"
        },
        "dest_cpg": {
            "required": False,
            "type": "str",
        },
        "save_snapshot": {
            "required": False,
            "type": "bool",
        },
        "priority": {
            "required": False,
            "type": "str",
            "choices": ['HIGH', 'MEDIUM', 'LOW'],
            "default": "MEDIUM"
        },
        "skip_zero": {
            "required": False,
            "type": "bool",
        }
    }

    module = AnsibleModule(argument_spec=fields)

    storage_system_ip = module.params["storage_system_ip"]
    storage_system_username = module.params["storage_system_username"]
    storage_system_password = module.params["storage_system_password"]
    clone_name = module.params["clone_name"]
    base_volume_name = module.params["base_volume_name"]
    dest_cpg = module.params["dest_cpg"]
    save_snapshot = module.params["save_snapshot"]
    priority = module.params["priority"]
    skip_zero = module.params["skip_zero"]

    wsapi_url = 'https://%s:8080/api/v1' % storage_system_ip
    client_obj = client.HPE3ParClient(wsapi_url)

    # States
    if module.params["state"] == "present":
        return_status, changed, msg, issue_attr_dict = create_offline_clone(
            client_obj, storage_system_ip, storage_system_username,
            storage_system_password, clone_name, base_volume_name, dest_cpg,
            skip_zero, save_snapshot, priority)
    elif module.params["state"] == "absent":
        return_status, changed, msg, issue_attr_dict = delete_clone(
            client_obj, storage_system_ip, storage_system_username,
            storage_system_password, clone_name, base_volume_name)
    elif module.params["state"] == "resync":
        return_status, changed, msg, issue_attr_dict = resync_clone(
            client_obj, storage_system_username, storage_system_password,
            clone_name)
    elif module.params["state"] == "stop":
        return_status, changed, msg, issue_attr_dict = stop_clone(
            client_obj, storage_system_ip, storage_system_username,
            storage_system_password, clone_name, base_volume_name)
    if return_status:
        if issue_attr_dict:
            module.exit_json(changed=changed, msg=msg, issue=issue_attr_dict)
        else:
            module.exit_json(changed=changed, msg=msg)
    else:
        module.fail_json(msg=msg)


if __name__ == '__main__':
    main()
