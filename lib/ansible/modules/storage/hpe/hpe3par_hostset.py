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
description: "On HPE 3PAR - Create Host Set. - Add Hosts to Host Set. - Remove
 Hosts from Host Set."
module: hpe3par_hostset
options:
  domain:
    description:
      - "The domain in which the VV set or host set will be created."
    required: false
  hostset_name:
    description:
      - "Name of the host set to be created."
    required: true
  setmembers:
    description:
      - "The host to be added to the set.\nRequired with action
       add_hosts, remove_hosts\n"
    required: false
  state:
    description:
      - "Whether the specified Host Set should exist or not. State also
       provides actions to add or remove hosts from host set choices:
       ['present', 'absent', 'add_hosts', 'remove_hosts']\n"
    required: true
extends_documentation_fragment: hpe3par
short_description: "Manage HPE 3PAR Host Set"
version_added: "2.4"
'''

EXAMPLES = r'''
    - name: Create hostset "{{ hostsetset_name }}"
      hpe3par_hostset:
        storage_system_ip="{{ storage_system_ip }}"
        storage_system_username="{{ storage_system_username }}"
        storage_system_password="{{ storage_system_password }}"
        state=present
        hostset_name="{{ hostset_name }}"
        setmembers="{{ add_host_setmembers }}"

    - name: Add hosts to Hostset "{{ hostsetset_name }}"
      hpe3par_hostset:
        storage_system_ip="{{ storage_system_ip }}"
        storage_system_username="{{ storage_system_username }}"
        storage_system_password="{{ storage_system_password }}"
        state=add_hosts
        hostset_name="{{ hostset_name }}"
        setmembers="{{ add_host_setmembers2 }}"

    - name: Remove hosts from Hostset "{{ hostsetset_name }}"
      hpe3par_hostset:
        storage_system_ip="{{ storage_system_ip }}"
        storage_system_username="{{ storage_system_username }}"
        storage_system_password="{{ storage_system_password }}"
        state=remove_hosts
        hostset_name="{{ hostset_name }}"
        setmembers="{{ remove_host_setmembers }}"

    - name: Delete Hostset "{{ hostset_name }}"
      hpe3par_hostset:
        storage_system_ip="{{ storage_system_ip }}"
        storage_system_username="{{ storage_system_username }}"
        storage_system_password="{{ storage_system_password }}"
        state=absent
        hostset_name="{{ hostset_name }}"
'''

RETURN = r'''
'''


from ansible.module_utils.basic import AnsibleModule
from hpe3par_sdk import client


def create_hostset(
        client_obj,
        storage_system_username,
        storage_system_password,
        hostset_name,
        domain,
        setmembers):
    if storage_system_username is None or storage_system_password is None:
        return (
            False,
            False,
            "Hostset create failed. Storage system username or password is \
null",
            {})
    if hostset_name is None:
        return (
            False,
            False,
            "Hostset create failed. Hostset name is null",
            {})
    if len(hostset_name) < 1 or len(hostset_name) > 31:
        return (False, False, "Hostset create failed. Hostset name must be atleast 1 character and more than 31 characters", {})
    try:
        client_obj.login(storage_system_username, storage_system_password)
        if not client_obj.hostSetExists(hostset_name):
            client_obj.createHostSet(hostset_name, domain, None, setmembers)
        else:
            return (True, False, "Hostset already present", {})
    except Exception as e:
        return (False, False, "Hostset creation failed | %s" % (e), {})
    finally:
        client_obj.logout()
    return (True, True, "Created Hostset %s successfully." % hostset_name, {})


def delete_hostset(
        client_obj,
        storage_system_username,
        storage_system_password,
        hostset_name):
    if storage_system_username is None or storage_system_password is None:
        return (
            False,
            False,
            "Hostset delete failed. Storage system username or password is \
null",
            {})
    if hostset_name is None:
        return (
            False,
            False,
            "Hostset delete failed. Hostset name is null",
            {})
    if len(hostset_name) < 1 or len(hostset_name) > 31:
        return (False, False, "Hostset create failed. Hostset name must be atleast 1 character and more than 31 characters", {})
    try:
        client_obj.login(storage_system_username, storage_system_password)
        if client_obj.hostSetExists(hostset_name):
            client_obj.deleteHostSet(hostset_name)
        else:
            return (True, False, "Hostset does not exist", {})
    except Exception as e:
        return (False, False, "Hostset delete failed | %s" % (e), {})
    finally:
        client_obj.logout()
    return (True, True, "Deleted Hostset %s successfully." % hostset_name, {})


def add_hosts(
        client_obj,
        storage_system_username,
        storage_system_password,
        hostset_name,
        setmembers):
    if storage_system_username is None or storage_system_password is None:
        return (
            False,
            False,
            "Add host to hostset failed. Storage system username or password \
is null",
            {})
    if hostset_name is None:
        return (
            False,
            False,
            "Add host to hostset failed. Hostset name is null",
            {})
    if len(hostset_name) < 1 or len(hostset_name) > 31:
        return (False, False, "Hostset create failed. Hostset name must be atleast 1 character and more than 31 characters", {})
    if setmembers is None:
        return (
            False,
            False,
            "setmembers delete failed. Setmembers is null",
            {})
    try:
        client_obj.login(storage_system_username, storage_system_password)
        if client_obj.hostSetExists(hostset_name):
            existing_set_members = client_obj.getHostSet(
                hostset_name).setmembers
            if existing_set_members is not None:
                new_set_members = list(
                    set(setmembers) - set(existing_set_members))
            else:
                new_set_members = setmembers
            if new_set_members is not None and new_set_members:
                client_obj.addHostsToHostSet(hostset_name, new_set_members)
            else:
                return (
                    True,
                    False,
                    "No new members to add to the Host set %s. Nothing to \
do." % hostset_name,
                    {})
        else:
            return (False, False, "Hostset does not exist", {})
    except Exception as e:
        return (False, False, "Add hosts to hostset failed | %s" % e, {})
    finally:
        client_obj.logout()
    return (True, True, "Added hosts successfully.", {})


def remove_hosts(
        client_obj,
        storage_system_username,
        storage_system_password,
        hostset_name,
        setmembers):
    if storage_system_username is None or storage_system_password is None:
        return (
            False,
            False,
            "Remove host from hostset failed. Storage system username or \
password is null",
            {})
    if hostset_name is None:
        return (
            False,
            False,
            "Remove host from hostset failed. Hostset name is null",
            {})
    if len(hostset_name) < 1 or len(hostset_name) > 31:
        return (False, False, "Hostset create failed. Hostset name must be atleast 1 character and more than 31 characters", {})
    if setmembers is None:
        return (
            False,
            False,
            "setmembers delete failed. Setmembers is null",
            {})
    try:
        client_obj.login(storage_system_username, storage_system_password)
        if client_obj.hostSetExists(hostset_name):
            existing_set_members = client_obj.getHostSet(
                hostset_name).setmembers
            if existing_set_members is not None:
                set_members = list(set(setmembers) & set(existing_set_members))
            else:
                set_members = setmembers
            if set_members is not None and set_members:
                client_obj.removeHostsFromHostSet(hostset_name, set_members)
            else:
                return (
                    True,
                    False,
                    "No members to remove to the Host set %s. Nothing to do." %
                    hostset_name,
                    {})
        else:
            return (True, False, "Hostset does not exist", {})
    except Exception as e:
        return (False, False, "Remove hosts from hostset failed | %s" % e, {})
    finally:
        client_obj.logout()
    return (True, True, "Removed hosts successfully.", {})


def main():
    fields = {
        "state": {
            "required": True,
            "choices": ['present', 'absent', 'add_hosts', 'remove_hosts'],
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
        "hostset_name": {
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
    hostset_name = module.params["hostset_name"]
    domain = module.params["domain"]
    setmembers = module.params["setmembers"]

    wsapi_url = 'https://%s:8080/api/v1' % storage_system_ip
    client_obj = client.HPE3ParClient(wsapi_url)

    # States
    if module.params["state"] == "present":
        return_status, changed, msg, issue_attr_dict = create_hostset(
            client_obj, storage_system_username, storage_system_password,
            hostset_name, domain, setmembers)
    elif module.params["state"] == "absent":
        return_status, changed, msg, issue_attr_dict = delete_hostset(
            client_obj, storage_system_username, storage_system_password,
            hostset_name)
    elif module.params["state"] == "add_hosts":
        return_status, changed, msg, issue_attr_dict = add_hosts(
            client_obj, storage_system_username, storage_system_password,
            hostset_name, setmembers)
    elif module.params["state"] == "remove_hosts":
        return_status, changed, msg, issue_attr_dict = remove_hosts(
            client_obj, storage_system_username, storage_system_password,
            hostset_name, setmembers)

    if return_status:
        if issue_attr_dict:
            module.exit_json(changed=changed, msg=msg, issue=issue_attr_dict)
        else:
            module.exit_json(changed=changed, msg=msg)
    else:
        module.fail_json(msg=msg)


if __name__ == '__main__':
    main()
