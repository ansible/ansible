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
description: "On HPE 3PAR - Export volume to host. - Export volumeset to host.
 - Export volume to hostset. - Export volumeset to hostset. - Unexport volume
 to host. - Unexport volumeset to host. - Unexport volume to hostset. -
 Unexport volumeset to hostset."
module: hpe3par_vlun
options:
  autolun:
    default: false
    description:
      - "States whether the lun number should be autosigned."
    required: false
    type: bool
  card_port:
    description:
      - "Port number on the FC card."
    required: false
  host_name:
    description:
      - "Name of the host to which the volume or VV set is to be exported."
    required: false
  host_set_name:
    description:
      - "Name of the host set to which the volume or VV set is to be exported.
       \nRequired with action export_volume_to_hostset,
       unexport_volume_to_hostset, export_volumeset_to_hostset,
       unexport_volumeset_to_hostset\n"
    required: false
  lunid:
    description:
      - "LUN ID."
    required: false
  node_val:
    description:
      - "System node."
    required: false
  slot:
    description:
      - "PCI bus slot in the node."
    required: false
  state:
    choices:
      - export_volume_to_host
      - unexport_volume_to_host
      - export_volumeset_to_host
      - unexport_volumeset_to_host
      - export_volume_to_hostset
      - unexport_volume_to_hostset
      - export_volumeset_to_hostset
      - unexport_volumeset_to_hostset
    description:
      - "Whether the specified export should exist or not."
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
  volume_name:
    description:
      - "Name of the volume to export."
    required: true
  volume_set_name:
    description:
      - "Name of the VV set to export.\nRequired with action
       export_volumeset_to_host, unexport_volumeset_to_host,
       export_volumeset_to_hostset, unexport_volumeset_to_hostset\n"
    required: false
requirements:
  - "3PAR OS - 3.2.2 MU6, 3.3.1 MU1"
  - "Ansible - 2.4"
  - "hpe3par_sdk 1.0.0"
  - "WSAPI service should be enabled on the 3PAR storage array."
short_description: "Manage HPE 3PAR VLUN"
version_added: "2.4"
'''

EXAMPLES = r'''
    - name: Create VLUN
      hpe3par_vlun:
        storage_system_ip="{{ storage_system_ip }}"
        storage_system_username="{{ storage_system_username }}"
        storage_system_password="{{ storage_system_password }}"
        state=export_volume_to_host
        volume_name="{{ volume_name }}"
        host_name="{{ host_name }}"
        lunid="{{ lunid }}"
        autolun="{{ autolun }}"

    - name: Create VLUN
      hpe3par_vlun:
        storage_system_ip="{{ storage_system_ip }}"
        storage_system_username="{{ storage_system_username }}"
        storage_system_password="{{ storage_system_password }}"
        state=export_volume_to_hostset
        volume_name="{{ vlun_volume_name }}"
        host_set_name="{{ hostset_name }}"
        lunid="{{ lunid }}"
        autolun="{{ autolun }}"

    - name: Create VLUN
      hpe3par_vlun:
        storage_system_ip="{{ storage_system_ip }}"
        storage_system_username="{{ storage_system_username }}"
        storage_system_password="{{ storage_system_password }}"
        state=export_volumeset_to_host
        volume_set_name="{{ volumeset_name }}"
        host_name="{{ vlun_host_name }}"
        lunid="{{ lunid }}"
        autolun="{{ autolun }}"

    - name: Create VLUN
      hpe3par_vlun:
        storage_system_ip="{{ storage_system_ip }}"
        storage_system_username="{{ storage_system_username }}"
        storage_system_password="{{ storage_system_password }}"
        state=export_volumeset_to_hostset
        volume_set_name="{{ volumeset_name }}"
        host_set_name="{{ hostset_name }}"
        lunid="{{ lunid }}"
        autolun="{{ autolun }}"

    - name: Delete VLUN
      hpe3par_vlun:
        storage_system_ip="{{ storage_system_ip }}"
        storage_system_username="{{ storage_system_username }}"
        storage_system_password="{{ storage_system_password }}"
        state=unexport_volume_to_host
        volume_name="{{ volume_name }}"
        host_name="{{ host_name }}"
        lunid="{{ lunid }}"
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
from hpe3par_sdk import client


def export_volume_to_host(
        client_obj,
        storage_system_username,
        storage_system_password,
        volume_name,
        lunid,
        host_name,
        node_val,
        slot,
        card_port,
        autolun):
    try:
        if (host_name is None and node_val is None and slot is None and
                card_port is None):
            return (
                False,
                False,
                'Attribute host_name or port positions or both need to be \
specified to create a vlun',
                {})

        if host_name is None and (
                node_val is None or slot is None or card_port is None):
            return (
                False,
                False,
                'Node, Slot and Port need to be specified to create a vlun',
                {})

        client_obj.login(storage_system_username, storage_system_password)
        port_pos = None

        if node_val is not None and slot is not None and card_port is not None:
            port_pos = {'node': node_val, 'slot': slot, 'cardPort': card_port}
        if not client_obj.vlunExists(
                volume_name,
                lunid,
                host_name,
                port_pos):
            client_obj.createVLUN(
                volume_name,
                lunid,
                host_name,
                port_pos,
                None,
                None,
                autolun)
        else:
            return (True, False, "VLUN already present", {})
    except Exception as e:
        return (False, False, "VLUN creation failed | %s" % e, {})
    finally:
        client_obj.logout()
    return (True, True, "Created VLUN successfully.", {})


def unexport_volume_to_host(
        client_obj,
        storage_system_username,
        storage_system_password,
        volume_name,
        lunid,
        host_name,
        node_val,
        slot,
        card_port):
    try:
        client_obj.login(storage_system_username, storage_system_password)
        port_pos = None

        if host_name is None and (
                node_val is None or slot is None or card_port is None):
            return (
                False,
                False,
                'Node, Slot and Port or host name need to be specified to \
unexport a vlun',
                {})
        if client_obj.vlunExists(volume_name, lunid, host_name, port_pos):
            client_obj.deleteVLUN(volume_name, lunid, host_name, port_pos)
        else:
            return (True, False, "VLUN does not exist", {})
    except Exception as e:
        return (False, False, "VLUN deletion failed | %s" % e, {})
    finally:
        client_obj.logout()
    return (True, True, "Deleted VLUN successfully.", {})


def export_volume_to_hostset(
        client_obj,
        storage_system_username,
        storage_system_password,
        volume_name,
        lunid,
        host_set_name,
        node_val,
        slot,
        card_port,
        autolun):
    try:
        if volume_name is None:
            return (
                False,
                False,
                'Attribute volume name is required for vlun creation',
                {})

        if host_set_name is None:
            return (
                False,
                False,
                'Attribute hostset_name is required to export a vlun',
                {})
        else:
            host_set_name = 'set:' + host_set_name

        client_obj.login(storage_system_username, storage_system_password)
        port_pos = None

        if node_val is not None and slot is not None and card_port is not None:
            port_pos = {'node': node_val, 'slot': slot, 'cardPort': card_port}

        if (not autolun and not client_obj.vlunExists(
                volume_name, lunid, host_set_name, port_pos)) or autolun:
            client_obj.createVLUN(
                volume_name,
                lunid,
                host_set_name,
                port_pos,
                None,
                None,
                autolun)
        else:
            return (True, False, "VLUN already present", {})

    except Exception as e:
        return (False, False, "VLUN creation failed | %s" % e, {})
    finally:
        client_obj.logout()
    return (True, True, "Created VLUN successfully.", {})


def unexport_volume_to_hostset(
        client_obj,
        storage_system_username,
        storage_system_password,
        volume_name,
        lunid,
        host_set_name,
        node_val,
        slot,
        card_port):
    try:
        client_obj.login(storage_system_username, storage_system_password)

        if host_set_name is None and (
                node_val is None or slot is None or card_port is None):
            return (
                False,
                False,
                'Node, Slot and Port or host name need to be specified to \
unexport a vlun',
                {})

        if host_set_name is None:
            return (
                False,
                False,
                'Attribute hostset_name is required to unexport a vlun',
                {})
        else:
            host_set_name = 'set:' + host_set_name

        port_pos = None

        if client_obj.vlunExists(volume_name, lunid, host_set_name, port_pos):
            client_obj.deleteVLUN(volume_name, lunid, host_set_name, port_pos)
        else:
            return (True, False, "VLUN does not exist", {})
    except Exception as e:
        return (False, False, "VLUN deletion failed | %s" % e, {})
    finally:
        client_obj.logout()
    return (True, True, "Deleted VLUN successfully.", {})


def export_volumeset_to_host(
        client_obj,
        storage_system_username,
        storage_system_password,
        volume_set_name,
        lunid,
        host_name,
        node_val,
        slot,
        card_port,
        autolun):
    try:
        if volume_set_name is None:
            return (
                False,
                False,
                'Attribute volumeset name is required for vlun creation',
                {})

        if (host_name is None and node_val is None and slot is None and
                card_port is None):
            return (
                False,
                False,
                'Attribute host_name or port positions or both need to be \
specified to create a vlun',
                {})

        if host_name is None and (
                node_val is None or slot is None or card_port is None):
            return (
                False,
                False,
                'All port positions (node,slot,cardport) are required to \
create a vlun',
                {})

        if volume_set_name:
            volume_set_name = 'set:' + volume_set_name

        client_obj.login(storage_system_username, storage_system_password)
        port_pos = None

        if node_val is not None and slot is not None and card_port is not None:
            port_pos = {'node': node_val, 'slot': slot, 'cardPort': card_port}

        if (not autolun and not client_obj.vlunExists(
                volume_set_name, lunid, host_name, port_pos)) or autolun:
            client_obj.createVLUN(
                volume_set_name,
                lunid,
                host_name,
                port_pos,
                None,
                None,
                autolun)
        else:
            return (True, False, "VLUN already present", {})

    except Exception as e:
        return (False, False, "VLUN creation failed | %s" % e, {})
    finally:
        client_obj.logout()
    return (True, True, "Created VLUN successfully.", {})


def unexport_volumeset_to_host(
        client_obj,
        storage_system_username,
        storage_system_password,
        volume_set_name,
        lunid,
        host_name,
        node_val,
        slot,
        card_port):
    try:
        client_obj.login(storage_system_username, storage_system_password)

        if host_name is None and (
                node_val is None or slot is None or card_port is None):
            return (
                False,
                False,
                'Node, Slot and Port or host name need to be specified to \
unexport a vlun',
                {})

        if volume_set_name is None:
            return (
                False,
                False,
                'Attribute volume_set_name is required to unexport a vlun',
                {})
        else:
            volume_set_name = 'set:' + volume_set_name

        port_pos = None

        if client_obj.vlunExists(volume_set_name, lunid, host_name, port_pos):
            client_obj.deleteVLUN(volume_set_name, lunid, host_name, port_pos)
        else:
            return (True, False, "VLUN does not exist", {})
    except Exception as e:
        return (False, False, "VLUN deletion failed | %s" % e, {})
    finally:
        client_obj.logout()
    return (True, True, "Deleted VLUN successfully.", {})


def export_volumeset_to_hostset(
        client_obj,
        storage_system_username,
        storage_system_password,
        volume_set_name,
        lunid,
        host_set_name,
        node_val,
        slot,
        card_port,
        autolun):
    try:
        if volume_set_name is None:
            return (
                False,
                False,
                'Attribute volumeset name is required for vlun creation',
                {})

        if host_set_name is None:
            return (
                False,
                False,
                'Attribute hostset name is required for vlun creation',
                {})

        if volume_set_name is not None and host_set_name is not None:
            volume_set_name = 'set:' + volume_set_name
            host_set_name = 'set:' + host_set_name
        else:
            return (
                False,
                False,
                'Attribute hostset_name and volumeset_name is required to \
export a vlun',
                {})

        client_obj.login(storage_system_username, storage_system_password)
        port_pos = None

        if node_val is not None and slot is not None and card_port is not None:
            port_pos = {'node': node_val, 'slot': slot, 'cardPort': card_port}

        if (not autolun and not client_obj.vlunExists(
                volume_set_name, lunid, host_set_name, port_pos)) or autolun:
            client_obj.createVLUN(
                volume_set_name,
                lunid,
                host_set_name,
                port_pos,
                None,
                None,
                autolun)
        else:
            return (True, False, "VLUN already present", {})

    except Exception as e:
        return (False, False, "VLUN creation failed | %s" % e, {})
    finally:
        client_obj.logout()
    return (True, True, "Created VLUN successfully.", {})


def unexport_volumeset_to_hostset(
        client_obj,
        storage_system_username,
        storage_system_password,
        volume_set_name,
        lunid,
        host_set_name,
        node_val,
        slot,
        card_port):
    try:
        client_obj.login(storage_system_username, storage_system_password)

        if host_set_name is None and (
                node_val is None or slot is None or card_port is None):
            return (
                False,
                False,
                'Node, Slot and Port or host set name need to be specified to \
unexport a vlun',
                {})

        if volume_set_name is not None and host_set_name is not None:
            volume_set_name = 'set:' + volume_set_name
            host_set_name = 'set:' + host_set_name
        else:
            return (
                False,
                False,
                'Attribute hostset_name and volumeset_name is required to \
unexport a vlun',
                {})

        port_pos = None

        if client_obj.vlunExists(
                volume_set_name,
                lunid,
                host_set_name,
                port_pos):
            client_obj.deleteVLUN(
                volume_set_name, lunid, host_set_name, port_pos)
        else:
            return (True, False, "VLUN does not exist", {})
    except Exception as e:
        return (False, False, "VLUN deletion failed | %s" % e, {})
    finally:
        client_obj.logout()
    return (True, True, "Deleted VLUN successfully.", {})


def main():

    fields = {
        "state": {
            "required": True,
            "choices": [
                'export_volume_to_host',
                'unexport_volume_to_host',
                'export_volumeset_to_host',
                'unexport_volumeset_to_host',
                'export_volume_to_hostset',
                'unexport_volume_to_hostset',
                'export_volumeset_to_hostset',
                'unexport_volumeset_to_hostset'],
            "type": 'str'},
        "storage_system_ip": {
            "required": True,
            "type": "str"},
        "storage_system_name": {
            "type": "str"},
        "storage_system_username": {
            "required": True,
            "type": "str",
            "no_log": True},
        "storage_system_password": {
            "required": True,
            "type": "str",
            "no_log": True},
        "volume_name": {
            "required": False,
            "type": "str"},
        "volume_set_name": {
            "required": False,
            "type": "str"},
        "lunid": {
            "type": "int"},
        "autolun": {
            "type": "bool",
            "default": False},
        "host_name": {
            "type": "str"},
        "host_set_name": {
            "required": False,
            "type": "str"},
        "node_val": {
            "type": "int"},
        "slot": {
            "type": "int"},
        "card_port": {
            "type": "int"}}

    module = AnsibleModule(argument_spec=fields)

    storage_system_ip = module.params["storage_system_ip"]
    storage_system_username = module.params["storage_system_username"]
    storage_system_password = module.params["storage_system_password"]

    volume_name = module.params["volume_name"]
    volume_set_name = module.params["volume_set_name"]
    lunid = module.params["lunid"]
    host_name = module.params["host_name"]
    host_set_name = module.params["host_set_name"]
    node_val = module.params["node_val"]
    slot = module.params["slot"]
    card_port = module.params["card_port"]
    autolun = module.params["autolun"]

    wsapi_url = 'https://%s:8080/api/v1' % storage_system_ip
    client_obj = client.HPE3ParClient(wsapi_url)

    # States
    if module.params["state"] == "export_volume_to_host":
        return_status, changed, msg, issue_attr_dict = export_volume_to_host(
            client_obj, storage_system_username, storage_system_password,
            volume_name, lunid, host_name, node_val, slot, card_port, autolun)
    elif module.params["state"] == "unexport_volume_to_host":
        return_status, changed, msg, issue_attr_dict = unexport_volume_to_host(
            client_obj, storage_system_username, storage_system_password,
            volume_name, lunid, host_name, node_val, slot, card_port)
    elif module.params["state"] == "export_volumeset_to_hostset":
        return_status, changed, msg, issue_attr_dict = (
            export_volumeset_to_hostset(client_obj, storage_system_username,
                                        storage_system_password,
                                        volume_set_name, lunid, host_set_name,
                                        node_val, slot, card_port,
                                        autolun))
    elif module.params["state"] == "unexport_volumeset_to_hostset":
        return_status, changed, msg, issue_attr_dict = (
            unexport_volumeset_to_hostset(client_obj, storage_system_username,
                                          storage_system_password,
                                          volume_set_name, lunid,
                                          host_set_name, node_val, slot,
                                          card_port))
    elif module.params["state"] == "export_volumeset_to_host":
        return_status, changed, msg, issue_attr_dict = (
            export_volumeset_to_host(client_obj, storage_system_username,
                                     storage_system_password,
                                     volume_set_name, lunid, host_name,
                                     node_val, slot, card_port, autolun))
    elif module.params["state"] == "unexport_volumeset_to_host":
        return_status, changed, msg, issue_attr_dict = (
            unexport_volumeset_to_host(client_obj, storage_system_username,
                                       storage_system_password,
                                       volume_set_name, lunid, host_name,
                                       node_val, slot, card_port))
    elif module.params["state"] == "export_volume_to_hostset":
        return_status, changed, msg, issue_attr_dict = (
            export_volume_to_hostset(client_obj, storage_system_username,
                                     storage_system_password,
                                     volume_name, lunid, host_set_name,
                                     node_val, slot, card_port, autolun))
    elif module.params["state"] == "unexport_volume_to_hostset":
        return_status, changed, msg, issue_attr_dict = (
            unexport_volume_to_hostset(client_obj, storage_system_username,
                                       storage_system_password,
                                       volume_name, lunid, host_set_name,
                                       node_val, slot, card_port))

    if return_status:
        if issue_attr_dict:
            module.exit_json(changed=changed, msg=msg, issue=issue_attr_dict)
        else:
            module.exit_json(changed=changed, msg=msg)
    else:
        module.fail_json(msg=msg)


if __name__ == '__main__':
    main()
