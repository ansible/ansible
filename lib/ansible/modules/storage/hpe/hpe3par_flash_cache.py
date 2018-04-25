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
description: "On HPE 3PAR - Create Flash Cache
 - Delete Flash Cache."
module: hpe3par_flash_cache
options:
  domain:
    description:
      - "The domain in which the VV set or host set will be created."
    required: false
  size_in_gib:
    description:
      - "Specifies the node pair size of the Flash Cache on
the system."
    required: true
  mode:
    description:
      - "Simulator 1 Real 2 (default)"
    required: false
  state:
    choices:
      - present
      - absent
    description:
      - "Whether the specified Flash Cache should exist or not."
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
short_description: "Manage HPE 3PAR Flash Cache"
version_added: "2.4"
'''

EXAMPLES = r'''
    - name: Create Flash Cache
      hpe3par_flash_cache:
        storage_system_ip="{{ storage_system_ip }}"
        storage_system_username="{{ storage_system_username }}"
        storage_system_password="{{ storage_system_password }}"
        state=present
        size_in_gib="{{ size_in_gib }}"

    - name: Delete Flash Cache
      hpe3par_flash_cache:
        storage_system_ip="{{ storage_system_ip }}"
        storage_system_username="{{ storage_system_username }}"
        storage_system_password="{{ storage_system_password }}"
        state=absent
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
from hpe3par_sdk import client


def create_flash_cache(
        client_obj,
        storage_system_username,
        storage_system_password,
        size_in_gib,
        mode):
    if storage_system_username is None or storage_system_password is None:
        return (
            False,
            False,
            "Flash Cache creation failed. Storage system username or password \
is null",
            {})
    if size_in_gib is None:
        return (False, False, "Flash Cache creation failed. Size is null", {})
    try:
        client_obj.login(storage_system_username, storage_system_password)
        if not client_obj.flashCacheExists():
            client_obj.createFlashCache(size_in_gib, mode)
        else:
            return (True, False, "Flash Cache already present", {})
    except Exception as e:
        return (False, False, "Flash Cache creation failed | %s" % e, {})
    finally:
        client_obj.logout()
    return (True, True, "Created Flash Cache successfully.", {})


def delete_flash_cache(
        client_obj,
        storage_system_username,
        storage_system_password):
    if storage_system_username is None or storage_system_password is None:
        return (
            False,
            False,
            "Flash Cache deletion failed. Storage system username or password \
is null",
            {})
    try:
        client_obj.login(storage_system_username, storage_system_password)
        if client_obj.flashCacheExists():
            client_obj.deleteFlashCache()
        else:
            return (True, False, "Flash Cache does not exist", {})
    except Exception as e:
        return (False, False, "Flash Cache delete failed | %s" % e, {})
    finally:
        client_obj.logout()
    return (True, True, "Deleted Flash Cache successfully.", {})


def main():

    fields = {
        "state": {
            "required": True,
            "choices": ['present', 'absent'],
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
        "size_in_gib": {
            "type": "int"
        },
        "mode": {
            "type": "int"
        }
    }

    module = AnsibleModule(argument_spec=fields)

    storage_system_ip = module.params["storage_system_ip"]
    storage_system_username = module.params["storage_system_username"]
    storage_system_password = module.params["storage_system_password"]

    size_in_gib = module.params["size_in_gib"]
    mode = module.params["mode"]

    wsapi_url = 'https://%s:8080/api/v1' % storage_system_ip
    client_obj = client.HPE3ParClient(wsapi_url)

    # States
    if module.params["state"] == "present":
        return_status, changed, msg, issue_attr_dict = create_flash_cache(
            client_obj, storage_system_username, storage_system_password,
            size_in_gib, mode)
    elif module.params["state"] == "absent":
        return_status, changed, msg, issue_attr_dict = delete_flash_cache(
            client_obj, storage_system_username, storage_system_password)

    if return_status:
        if issue_attr_dict:
            module.exit_json(changed=changed, msg=msg, issue=issue_attr_dict)
        else:
            module.exit_json(changed=changed, msg=msg)
    else:
        module.fail_json(msg=msg)


if __name__ == '__main__':
    main()
