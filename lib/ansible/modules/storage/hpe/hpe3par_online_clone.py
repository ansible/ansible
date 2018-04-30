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
description: "On HPE 3PAR - Create Online Clone. - Delete Clone. - Resync
 Clone."
module: hpe3par_online_clone
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
  compression:
    description:
      - "Enables (true) or disables (false) compression of the created volume.
       Only tpvv or tdvv are compressed."
    required: false
    type: bool
  dest_cpg:
    description:
      - "Specifies the destination CPG for an online copy."
    required: false
  snap_cpg:
    description:
      - "Specifies the snapshot CPG for an online copy."
    required: false
  state:
    choices:
      - present
      - absent
      - resync
    description:
      - "Whether the specified Clone should exist or not. State also provides
       actions to resync clone\n"
    required: true
  tdvv:
    description:
      - "Enables (true) or disables (false) whether the online copy is a TDVV."
    required: false
    type: bool
  tpvv:
    description:
      - "Enables (true) or disables (false) whether the online copy is a TPVV."
    required: false
    type: bool
extends_documentation_fragment: hpe3par
short_description: "Manage HPE 3PAR Online Clone"
version_added: "2.4"
'''

EXAMPLES = r'''
    - name: Create Clone clone_volume_ansible
      hpe3par_online_clone:
        storage_system_ip="{{ storage_system_ip }}"
        storage_system_username="{{ storage_system_username }}"
        storage_system_password="{{ storage_system_password }}"
        state=present
        clone_name="clone_volume_ansible"
        base_volume_name="{{ volume_name }}"
        dest_cpg="{{ cpg }}"
        tpvv=False
        tdvv=False
        compression=False
        snap_cpg="{{ cpg }}"

    - name: sleep for 100 seconds and continue with play
      wait_for:
        timeout=100

    - name: Delete clone "clone_volume_ansible"
      hpe3par_online_clone:
        storage_system_ip="{{ storage_system_ip }}"
        storage_system_username="{{ storage_system_username }}"
        storage_system_password="{{ storage_system_password }}"
        state=absent
        clone_name="clone_volume_ansible"
        base_volume_name="{{ volume_name }}"
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
from hpe3par_sdk import client


def create_online_clone(
        client_obj,
        storage_system_username,
        storage_system_password,
        base_volume_name,
        clone_name,
        dest_cpg,
        tpvv,
        tdvv,
        snap_cpg,
        compression):
    if storage_system_username is None or storage_system_password is None:
        return (
            False,
            False,
            "Online clone create failed. Storage system username or password \
is null",
            {})
    if clone_name is None:
        return (
            False,
            False,
            "Online clone create failed. Clone name is null",
            {})
    if len(clone_name) < 1 or len(clone_name) > 31:
        return (False, False, "Clone create failed. Clone name must be atleast 1 character and more than 31 characters", {})
    if base_volume_name is None:
        return (
            False,
            False,
            "Online clone create failed. Base volume name is null",
            {})
    if len(base_volume_name) < 1 or len(base_volume_name) > 31:
        return (False, False, "Clone create failed. Base volume name must be atleast 1 character and more than 31 characters", {})
    try:
        client_obj.login(storage_system_username, storage_system_password)
        if not client_obj.volumeExists(clone_name):
            optional = {'online': True,
                        'tpvv': tpvv,
                        'tdvv': tdvv,
                        'snapCPG': snap_cpg
                        }
            if compression:
                optional['compression'] = compression
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
        return (False, False, "Online Clone creation failed | %s" % (e), {})
    finally:
        client_obj.logout()
    return (
        True,
        True,
        "Created Online Clone %s successfully." %
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
            "Online clone resync failed. Storage system username or password \
is null",
            {})
    if clone_name is None:
        return (
            False,
            False,
            "Online clone resync failed. Clone name is null",
            {})
    if len(clone_name) < 1 or len(clone_name) > 31:
        return (False, False, "Clone create failed. Clone name must be atleast 1 character and more than 31 characters", {})
    try:
        client_obj.login(storage_system_username, storage_system_password)
        client_obj.resyncPhysicalCopy(clone_name)
    except Exception as e:
        return (False, False, "Online clone resync failed | %s" % e, {})
    finally:
        client_obj.logout()
    return (
        True,
        True,
        "Resync-ed Online Clone %s successfully." %
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
            "Online clone delete failed. Storage system username or password \
is null",
            {})
    if clone_name is None:
        return (
            False,
            False,
            "Online clone delete failed. Clone name is null",
            {})
    if len(clone_name) < 1 or len(clone_name) > 31:
        return (False, False, "Clone create failed. Clone name must be atleast 1 character and more than 31 characters", {})
    if base_volume_name is None:
        return (
            False,
            False,
            "Online clone delete failed. Base volume name is null",
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
        return (False, False, "Online Clone delete failed | %s" % (e), {})
    finally:
        client_obj.logout()
    return (
        True,
        True,
        "Deleted Online Clone %s successfully." %
        clone_name,
        {})


def main():

    fields = {
        "state": {
            "required": True,
            "choices": ['present', 'absent', 'resync'],
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
        "tpvv": {
            "required": False,
            "type": "bool",
        },
        "tdvv": {
            "required": False,
            "type": "bool",
        },
        "snap_cpg": {
            "required": False,
            "type": "str",
        },
        "compression": {
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
    tpvv = module.params["tpvv"]
    tdvv = module.params["tdvv"]
    snap_cpg = module.params["snap_cpg"]
    compression = module.params["compression"]

    wsapi_url = 'https://%s:8080/api/v1' % storage_system_ip
    client_obj = client.HPE3ParClient(wsapi_url)

    # States
    if module.params["state"] == "present":
        return_status, changed, msg, issue_attr_dict = create_online_clone(
            client_obj, storage_system_username, storage_system_password,
            base_volume_name, clone_name, dest_cpg, tpvv, tdvv, snap_cpg,
            compression)
    elif module.params["state"] == "absent":
        return_status, changed, msg, issue_attr_dict = delete_clone(
            client_obj, storage_system_ip, storage_system_username,
            storage_system_password, clone_name, base_volume_name)
    elif module.params["state"] == "resync":
        return_status, changed, msg, issue_attr_dict = resync_clone(
            client_obj, storage_system_ip, storage_system_username,
            storage_system_password, clone_name)

    if return_status:
        if issue_attr_dict:
            module.exit_json(changed=changed, msg=msg, issue=issue_attr_dict)
        else:
            module.exit_json(changed=changed, msg=msg)
    else:
        module.fail_json(msg=msg)


if __name__ == '__main__':
    main()
