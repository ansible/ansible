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


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
author: "Farhan Nomani (nomani@hpe.com)"
description: "On HPE 3PAR - Create Snapshot. - Delete Snapshot. - Modify
 Snapshot."
module: hpe3par_snapshot
options:
  allow_remote_copy_parent:
    description:
      - "Allows the promote operation to proceed even if the RW parent volume
       is currently in a Remote Copy volume group, if that group has not been
       started. If the Remote Copy group has been started, this command
       fails.\n"
    required: false
    type: bool
  base_volume_name:
    description:
      - "Specifies the source volume.\nRequired with action present\n"
    required: false
  expiration_hours:
    default: 0
    description:
      - "Specifies the relative time from the current time that the volume
       expires. Value is a positive integer and in the range of 1 to 43,800
       hours, or 1825 days.\n"
    required: false
  expiration_time:
    description:
      - "Specifies the relative time from the current time that the volume
       expires. Value is a positive integer and in the range of 1 to 43,800
       hours, or 1825 days.\n"
    required: false
  expiration_unit:
    choices:
      - Hours
      - Days
    default: Hours
    description:
      - "Unit of Expiration Time."
    required: false
  new_name:
    description:
      - "New name of the volume."
    required: false
  priority:
    choices:
      - HIGH
      - MEDIUM
      - LOW
    description:
      - "Does not apply to online promote operation or to stop promote
       operation."
    required: false
  read_only:
    description:
      - "Specifies that the copied volume is read-only. false(default) The
       volume is read/write.\n"
    required: false
    type: bool
  retention_hours:
    default: 0
    description:
      - "Specifies the relative time from the current time that the volume
       expires. Value is a positive integer and in the range of 1 to 43,800
       hours, or 1825 days.\n"
    required: false
  retention_time:
    description:
      - "Specifies the relative time from the current time that the volume will
       expire. Value is a positive integer and in the range of 1 to 43,800
       hours, or 1825 days.\n"
    required: false
  retention_unit:
    choices:
      - Hours
      - Days
    default: Hours
    description:
      - "Unit of Retention Time."
    required: false
  rm_exp_time:
    description:
      - "Enables (false) or disables (true) resetting the expiration time. If
       false, and expiration time value is a positive number, then set."
    required: false
    type: bool
  snapshot_name:
    description:
      - "Specifies a snapshot volume name."
    required: true
  state:
    choices:
      - present
      - absent
      - modify
      - restore_offline
      - restore_online
    description:
      - "Whether the specified Snapshot should exist or not. State also
       provides actions to modify and restore snapshots.\n"
    required: true
  storage_system_ip:
    description:
      - "The storage system IP address."
    required: true
  storage_system_password:
    description:
      - "The storage system password."
    required: true
  storage_system_username:
    description:
      - "The storage system user name."
    required: true
requirements:
  - "3PAR OS - 3.2.2 MU6, 3.3.1 MU1"
  - "Ansible - 2.4"
  - "hpe3par_sdk 1.0.0"
  - "WSAPI service should be enabled on the 3PAR storage array."
short_description: "Manage HPE 3PAR Snapshots"
version_added: "2.4"
'''

EXAMPLES = r'''
    - name: Create Volume snasphot my_ansible_snapshot
      hpe3par_snapshot:
        storage_system_ip="{{ storage_system_ip }}"
        storage_system_username="{{ storage_system_username }}"
        storage_system_password="{{ storage_system_password }}"
        state=present
        snapshot_name="{{ snapshot_name }}"
        base_volume_name="{{ base_volume_name }}"
        read_only=False

    - name: Restore offline Volume snasphot my_ansible_snapshot
      hpe3par_snapshot:
        storage_system_ip="{{ storage_system_ip }}"
        storage_system_username="{{ storage_system_username }}"
        storage_system_password="{{ storage_system_password }}"
        state=restore_offline
        snapshot_name="{{ snapshot_name }}"
        priority="MEDIUM"

    - name: Restore offline Volume snasphot my_ansible_snapshot
      hpe3par_snapshot:
        storage_system_ip="{{ storage_system_ip }}"
        storage_system_username="{{ storage_system_username }}"
        storage_system_password="{{ storage_system_password }}"
        state=restore_online
        snapshot_name="{{ snapshot_name }}"

    - name: Modify/rename snasphot my_ansible_snapshot to
    my_ansible_snapshot_renamed
      hpe3par_snapshot:
        storage_system_ip="{{ storage_system_ip }}"
        storage_system_username="{{ storage_system_username }}"
        storage_system_password="{{ storage_system_password }}"
        state=modify
        snapshot_name="{{ snapshot_name }}"
        new_name="{{ new_name }}"

    - name: Delete snasphot my_ansible_snapshot_renamed
      hpe3par_snapshot:
        storage_system_ip="{{ storage_system_ip }}"
        storage_system_username="{{ storage_system_username }}"
        storage_system_password="{{ storage_system_password }}"
        state=absent
        snapshot_name="{{ snapshot_name }}"
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
from hpe3par_sdk import client


def convert_to_hours(time, unit):
    hours = 0
    if unit == 'Days':
        hours = time * 24
    elif unit == 'Hours':
        hours = time
    return hours


def create_snapshot(
        client_obj,
        storage_system_username,
        storage_system_password,
        snapshot_name,
        base_volume_name,
        read_only,
        expiration_time,
        retention_time,
        expiration_unit,
        retention_unit):
    if storage_system_username is None or storage_system_password is None:
        return (
            False,
            False,
            "Snapshot create failed. Storage system username or password is \
null",
            {})
    if snapshot_name is None:
        return (
            False,
            False,
            "Snapshot create failed. Snapshot name is null",
            {})
    if len(snapshot_name) < 1 or len(snapshot_name) > 31:
        return (False, False, "Snapshot create failed. Snapshot name must be atleast 1 character and more than 31 characters", {})
    if base_volume_name is None:
        return (
            False,
            False,
            "Snapshot create failed. Base volume name is null",
            {})
    if len(base_volume_name) < 1 or len(base_volume_name) > 31:
        return (False, False, "Snapshot create failed. Base volume name must be atleast 1 character and more than 31 characters", {})
    try:
        client_obj.login(storage_system_username, storage_system_password)
        if not client_obj.volumeExists(snapshot_name):
            optional = {
                'readOnly': read_only,
                'expirationHours': convert_to_hours(
                    expiration_time,
                    expiration_unit),
                'retentionHours': convert_to_hours(
                    retention_time,
                    retention_unit)}
            client_obj.createSnapshot(
                snapshot_name, base_volume_name, optional)
        else:
            return (True, False, "Volume/Snapshot already present", {})
    except Exception as e:
        return (False, False, "Snapshot creation failed | %s" % (e), {})
    finally:
        client_obj.logout()
    return (
        True,
        True,
        "Created Snapshot %s successfully." %
        snapshot_name,
        {})


def modify_snapshot(
        client_obj,
        storage_system_username,
        storage_system_password,
        snapshot_name,
        new_name,
        expiration_hours,
        retention_hours,
        rm_exp_time):
    if storage_system_username is None or storage_system_password is None:
        return (
            False,
            False,
            "Modify snapshot failed. Storage system username or password is \
null",
            {})
    if snapshot_name is None:
        return (
            False,
            False,
            "Modify snapshot failed. Snapshot name is null",
            {})
    if len(snapshot_name) < 1 or len(snapshot_name) > 31:
        return (False, False, "Snapshot create failed. Snapshot name must be atleast 1 character and more than 31 characters", {})
    try:
        client_obj.login(storage_system_username, storage_system_password)
        volume_mods = {
            'expirationHours': expiration_hours,
            'newName': new_name,
            'retentionHours': retention_hours,
            'rmExpTime': rm_exp_time}
        client_obj.modifyVolume(snapshot_name, volume_mods)
    except Exception as e:
        return (False, False, "Modify Snapshot failed | %s" % e, {})
    finally:
        client_obj.logout()
    return (True, True, "Modified Snapshot %s successfully." % snapshot_name,
            {})


def delete_snapshot(
        client_obj,
        storage_system_username,
        storage_system_password,
        snapshot_name):
    if storage_system_username is None or storage_system_password is None:
        return (
            False,
            False,
            "Snapshot delete failed. Storage system username or password is \
null",
            {})
    if snapshot_name is None:
        return (
            False,
            False,
            "Snapshot delete failed. Snapshot name is null",
            {})
    if len(snapshot_name) < 1 or len(snapshot_name) > 31:
        return (False, False, "Snapshot create failed. Snapshot name must be atleast 1 character and more than 31 characters", {})
    try:
        client_obj.login(storage_system_username, storage_system_password)
        if client_obj.volumeExists(snapshot_name):
            client_obj.deleteVolume(snapshot_name)
        else:
            return (True, False, "Volume/Snapshot does not exist", {})
    except Exception as e:
        return (False, False, "Snapshot delete failed | %s" % (e), {})
    finally:
        client_obj.logout()
    return (
        True,
        True,
        "Deleted Snapshot %s successfully." %
        snapshot_name,
        {})


def restore_snapshot_offline(
        client_obj,
        storage_system_username,
        storage_system_password,
        snapshot_name,
        priority,
        allow_remote_copy_parent):
    if storage_system_username is None or storage_system_password is None:
        return (
            False,
            False,
            "Offline snapshot restore failed. Storage system username or \
password is null",
            {})
    if snapshot_name is None:
        return (
            False,
            False,
            "Offline snapshot restore failed. Snapshot name is null",
            {})
    if len(snapshot_name) < 1 or len(snapshot_name) > 31:
        return (False, False, "Snapshot create failed. Snapshot name must be atleast 1 character and more than 31 characters", {})
    try:
        client_obj.login(storage_system_username, storage_system_password)
        optional = {
            'online': False,
            'allowRemoteCopyParent': allow_remote_copy_parent,
            'priority': getattr(
                client.HPE3ParClient.TaskPriority,
                priority)}
        client_obj.promoteVirtualCopy(snapshot_name, optional)
    except Exception as e:
        return (False, False, "Offline snapshot restore failed | %s" % (e), {})
    finally:
        client_obj.logout()
    return (
        True,
        True,
        "Restored offline snapshot %s successfully." %
        snapshot_name,
        {})


def restore_snapshot_online(
        client_obj,
        storage_system_username,
        storage_system_password,
        snapshot_name,
        allow_remote_copy_parent):
    if storage_system_username is None or storage_system_password is None:
        return (
            False,
            False,
            "Online snapshot restore failed. Storage system username or \
password is null",
            {})
    if snapshot_name is None:
        return (
            False,
            False,
            "Online snapshot restore failed. Snapshot name is null",
            {})
    if len(snapshot_name) < 1 or len(snapshot_name) > 31:
        return (False, False, "Snapshot create failed. Snapshot name must be atleast 1 character and more than 31 characters", {})
    try:
        client_obj.login(storage_system_username, storage_system_password)
        optional = {'online': True,
                    'allowRemoteCopyParent': allow_remote_copy_parent
                    }
        client_obj.promoteVirtualCopy(snapshot_name, optional)
    except Exception as e:
        return (False, False, "Online snapshot restore failed | %s" % (e), {})
    finally:
        client_obj.logout()
    return (
        True,
        True,
        "Restored online Snapshot %s successfully." %
        snapshot_name,
        {})


def main():

    fields = {
        "state": {
            "required": True,
            "choices": ['present', 'absent', 'modify', 'restore_offline',
                        'restore_online'],
            "type": 'str'
        },
        "storage_system_ip": {
            "required": True,
            "type": "str"
        },
        "storage_system_name": {
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
        "snapshot_name": {
            "required": True,
            "type": "str"
        },
        "base_volume_name": {
            "type": "str"
        },
        "read_only": {
            "type": "bool"
        },
        "expiration_time": {
            "type": "int",
        },
        "retention_time": {
            "type": "int"
        },
        "expiration_unit": {
            "type": "str",
            "choices": ['Hours', 'Days'],
            "default": 'Hours'
        },
        "retention_unit": {
            "type": "str",
            "choices": ['Hours', 'Days'],
            "default": 'Hours'
        },
        "expiration_hours": {
            "type": "int",
            "default": 0
        },
        "retention_hours": {
            "type": "int",
            "default": 0
        },
        "priority": {
            "type": "str",
            "choices": ['HIGH', 'MEDIUM', 'LOW'],
        },
        "allow_remote_copy_parent": {
            "type": "bool"
        },
        "new_name": {
            "type": "str"
        },
        "rm_exp_time": {
            "type": "bool"
        }
    }

    module = AnsibleModule(argument_spec=fields)

    storage_system_ip = module.params["storage_system_ip"]
    storage_system_username = module.params["storage_system_username"]
    storage_system_password = module.params["storage_system_password"]
    snapshot_name = module.params["snapshot_name"]
    base_volume_name = module.params["base_volume_name"]
    read_only = module.params["read_only"]
    expiration_time = module.params["expiration_time"]
    retention_time = module.params["retention_time"]
    expiration_unit = module.params["expiration_unit"]
    retention_unit = module.params["retention_unit"]
    expiration_hours = module.params["expiration_hours"]
    retention_hours = module.params["retention_hours"]
    priority = module.params["priority"]
    allow_remote_copy_parent = module.params["allow_remote_copy_parent"]
    new_name = module.params["new_name"]
    rm_exp_time = module.params["rm_exp_time"]

    wsapi_url = 'https://%s:8080/api/v1' % storage_system_ip
    client_obj = client.HPE3ParClient(wsapi_url)

    # States
    if module.params["state"] == "present":
        return_status, changed, msg, issue_attr_dict = create_snapshot(
            client_obj, storage_system_username, storage_system_password,
            snapshot_name, base_volume_name, read_only, expiration_time,
            retention_time, expiration_unit, retention_unit)
    elif module.params["state"] == "modify":
        return_status, changed, msg, issue_attr_dict = modify_snapshot(
            client_obj, storage_system_username, storage_system_password,
            snapshot_name, new_name, expiration_hours, retention_hours,
            rm_exp_time)
    elif module.params["state"] == "absent":
        return_status, changed, msg, issue_attr_dict = delete_snapshot(
            client_obj, storage_system_username, storage_system_password,
            snapshot_name)
    elif module.params["state"] == "restore_offline":
        return_status, changed, msg, issue_attr_dict = (
            restore_snapshot_offline(client_obj, storage_system_username,
                                     storage_system_password,
                                     snapshot_name, priority,
                                     allow_remote_copy_parent))
    elif module.params["state"] == "restore_online":
        return_status, changed, msg, issue_attr_dict = restore_snapshot_online(
            client_obj, storage_system_username, storage_system_password,
            snapshot_name, allow_remote_copy_parent)

    if return_status:
        if issue_attr_dict:
            module.exit_json(changed=changed, msg=msg, issue=issue_attr_dict)
        else:
            module.exit_json(changed=changed, msg=msg)
    else:
        module.fail_json(msg=msg)


if __name__ == '__main__':
    main()
