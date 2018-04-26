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
description: "On HPE 3PAR - Create Volume Set. - Add Volumes to Volume Set. -
 Remove Volumes from Volume Set."
module: hpe3par_volumeset
options:
  domain:
    description:
      - "The domain in which the VV set or host set will be created."
    required: false
  setmembers:
    description:
      - "The virtual volume to be added to the set.\nRequired with action
       add_volumes, remove_volumes\n"
    required: false
  state:
    choices:
      - present
      - absent
      - add_volumes
      - remove_volumes
    description:
      - "Whether the specified Volume Set should exist or not. State also
       provides actions to add or remove volumes from volume set\n"
    required: true
  volumeset_name:
    description:
      - "Name of the volume set to be created."
    required: true
extends_documentation_fragment: hpe3par
short_description: "Manage HPE 3PAR Volume Set"
version_added: "2.4"
'''

EXAMPLES = r'''
    - name: Create volume set "{{ volumeset_name }}"
      hpe3par_volumeset:
        storage_system_ip="{{ storage_system_ip }}"
        storage_system_username="{{ storage_system_username }}"
        storage_system_password="{{ storage_system_password }}"
        state=present
        volumeset_name="{{ volumeset_name }}"
        setmembers="{{ add_vol_setmembers }}"

    - name: Add volumes to Volumeset "{{ volumeset_name }}"
      hpe3par_volumeset:
        storage_system_ip="{{ storage_system_ip }}"
        storage_system_username="{{ storage_system_username }}"
        storage_system_password="{{ storage_system_password }}"
        state=add_volumes
        volumeset_name="{{ volumeset_name }}"
        setmembers="{{ add_vol_setmembers2 }}"

    - name: Remove volumes from Volumeset "{{ volumeset_name }}"
      hpe3par_volumeset:
        storage_system_ip="{{ storage_system_ip }}"
        storage_system_username="{{ storage_system_username }}"
        storage_system_password="{{ storage_system_password }}"
        state=remove_volumes
        volumeset_name="{{ volumeset_name }}"
        setmembers="{{ remove_vol_setmembers }}"

    - name: Delete Volumeset "{{ volumeset_name }}"
      hpe3par_volumeset:
        storage_system_ip="{{ storage_system_ip }}"
        storage_system_username="{{ storage_system_username }}"
        storage_system_password="{{ storage_system_password }}"
        state=absent
        volumeset_name="{{ volumeset_name }}"
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
from hpe3par_sdk import client


def create_volumeset(
        client_obj,
        storage_system_username,
        storage_system_password,
        volumeset_name,
        domain,
        setmembers):
    if storage_system_username is None or storage_system_password is None:
        return (
            False,
            False,
            "volumeset create failed. Storage system username or password is \
null",
            {})
    if volumeset_name is None:
        return (
            False,
            False,
            "volumeset create failed. volumeset name is null",
            {})
    if len(volumeset_name) < 1 or len(volumeset_name) > 31:
        return (False, False, "Volume Set create failed. Volume Set name must be atleast 1 character and more than 31 characters", {})
    try:
        client_obj.login(storage_system_username, storage_system_password)
        if not client_obj.volumeSetExists(volumeset_name):
            client_obj.createVolumeSet(
                volumeset_name, domain, None, setmembers)
        else:
            return (True, False, "volumeset already present", {})
    except Exception as e:
        return (False, False, "volumeset creation failed | %s" % (e), {})
    finally:
        client_obj.logout()
    return (
        True,
        True,
        "Created volumeset %s successfully." %
        volumeset_name,
        {})


def delete_volumeset(
        client_obj,
        storage_system_username,
        storage_system_password,
        volumeset_name):
    if storage_system_username is None or storage_system_password is None:
        return (
            False,
            False,
            "volumeset delete failed. Storage system username or password is \
null",
            {})
    if volumeset_name is None:
        return (
            False,
            False,
            "volumeset delete failed. volumeset name is null",
            {})
    if len(volumeset_name) < 1 or len(volumeset_name) > 31:
        return (False, False, "Volume Set create failed. Volume Set name must be atleast 1 character and more than 31 characters", {})
    try:
        client_obj.login(storage_system_username, storage_system_password)
        if client_obj.volumeSetExists(volumeset_name):
            client_obj.deleteVolumeSet(volumeset_name)
        else:
            return (True, False, "volumeset does not exist", {})
    except Exception as e:
        return (False, False, "volumeset delete failed | %s" % (e), {})
    finally:
        client_obj.logout()
    return (
        True,
        True,
        "Deleted volumeset %s successfully." %
        volumeset_name,
        {})


def add_volumes(
        client_obj,
        storage_system_username,
        storage_system_password,
        volumeset_name,
        setmembers):
    if storage_system_username is None or storage_system_password is None:
        return (
            False,
            False,
            "Add volume to volumeset failed. Storage system username or \
password is null",
            {})
    if volumeset_name is None:
        return (
            False,
            False,
            "Add volume to volumeset failed. Volumeset name is null",
            {})
    if len(volumeset_name) < 1 or len(volumeset_name) > 31:
        return (False, False, "Volume Set create failed. Volume Set name must be atleast 1 character and more than 31 characters", {})
    if setmembers is None:
        return (
            False,
            False,
            "Add volume to volumeset failed. Setmembers is null",
            {})
    try:
        client_obj.login(storage_system_username, storage_system_password)
        if client_obj.volumeSetExists(volumeset_name):
            existing_set_members = client_obj.getVolumeSet(
                volumeset_name).setmembers
            if existing_set_members is not None:
                new_set_members = list(
                    set(setmembers) - set(existing_set_members))
            else:
                new_set_members = setmembers
            if new_set_members is not None and new_set_members:
                client_obj.addVolumesToVolumeSet(
                    volumeset_name, new_set_members)
            else:
                return (
                    True,
                    False,
                    "No new members to add to the Volume set %s#. Nothing to \
do." %
                    volumeset_name,
                    {})
        else:
            return (False, False, "Volumeset does not exist", {})
    except Exception as e:
        return (False, False, "Add volumes to volumeset failed | %s" % (e), {})
    finally:
        client_obj.logout()
    return (True, True, "Added volumes successfully.", {})


def remove_volumes(
        client_obj,
        storage_system_username,
        storage_system_password,
        volumeset_name,
        setmembers):
    if storage_system_username is None or storage_system_password is None:
        return (
            False,
            False,
            "Remove volume(s) from Volumeset failed. Storage system username \
or password is null",
            {})
    if volumeset_name is None:
        return (
            False,
            False,
            "Remove volume(s) from Volumeset failed. Volumeset name is null",
            {})
    if len(volumeset_name) < 1 or len(volumeset_name) > 31:
        return (False, False, "Volume Set create failed. Volume Set name must be atleast 1 character and more than 31 characters", {})
    if setmembers is None:
        return (
            False,
            False,
            "Remove volume(s) from Volumeset failed. Setmembers is null",
            {})
    try:
        client_obj.login(storage_system_username, storage_system_password)
        if client_obj.volumeSetExists(volumeset_name):
            existing_set_members = client_obj.getVolumeSet(
                volumeset_name).setmembers
            if existing_set_members is not None:
                set_members = list(set(existing_set_members) & set(setmembers))
            else:
                set_members = setmembers
            if set_members is not None and set_members:
                client_obj.removeVolumesFromVolumeSet(
                    volumeset_name, set_members)
            else:
                return (
                    True,
                    False,
                    "No members to remove to the Volume set %s. Nothing to \
do." %
                    volumeset_name,
                    {})
        else:
            return (True, False, "Volumeset does not exist", {})
    except Exception as e:
        return (
            False,
            False,
            "Remove volumes from volumeset failed | %s" %
            e,
            {})
    finally:
        client_obj.logout()
    return (True, True, "Removed volumes successfully.", {})


def main():
    fields = {
        "state": {
            "required": True,
            "choices": ['present', 'absent', 'add_volumes', 'remove_volumes'],
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
        "volumeset_name": {
            "required": True,
            "type": "str"
        },
        "domain": {
            "type": "str"
        },
        "setmembers": {
            "type": "list"
        }
    }
    module = AnsibleModule(argument_spec=fields)

    storage_system_ip = module.params["storage_system_ip"]
    storage_system_username = module.params["storage_system_username"]
    storage_system_password = module.params["storage_system_password"]
    volumeset_name = module.params["volumeset_name"]
    domain = module.params["domain"]
    setmembers = module.params["setmembers"]

    wsapi_url = 'https://%s:8080/api/v1' % storage_system_ip
    client_obj = client.HPE3ParClient(wsapi_url)

    # States
    if module.params["state"] == "present":
        return_status, changed, msg, issue_attr_dict = create_volumeset(
            client_obj, storage_system_username, storage_system_password,
            volumeset_name, domain, setmembers)
    elif module.params["state"] == "absent":
        return_status, changed, msg, issue_attr_dict = delete_volumeset(
            client_obj, storage_system_username, storage_system_password,
            volumeset_name)
    elif module.params["state"] == "add_volumes":
        return_status, changed, msg, issue_attr_dict = add_volumes(
            client_obj, storage_system_username, storage_system_password,
            volumeset_name, setmembers)
    elif module.params["state"] == "remove_volumes":
        return_status, changed, msg, issue_attr_dict = remove_volumes(
            client_obj, storage_system_username, storage_system_password,
            volumeset_name, setmembers)

    if return_status:
        if issue_attr_dict:
            module.exit_json(changed=changed, msg=msg, issue=issue_attr_dict)
        else:
            module.exit_json(changed=changed, msg=msg)
    else:
        module.fail_json(msg=msg)


if __name__ == '__main__':
    main()
