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
description:
  - "Create and delete CPG on HPE 3PAR."
module: hpe3par_cpg
options:
  cpg_name:
    description:
      - "Name of the CPG."
    required: true
  disk_type:
    choices:
      - FC
      - NL
      - SSD
    description:
      - "Specifies that physical disks must have the specified device type."
    required: false
  domain:
    description:
      - "Specifies the name of the domain in which the object will reside."
    required: false
  growth_increment:
    default: -1.0
    description:
      - "Specifies the growth increment the amount of logical disk storage
       created on each auto-grow operation.\n"
    required: false
  growth_increment_unit:
    choices:
      - MiB
      - GiB
      - TiB
    default: GiB
    description:
      - "Unit of growth increment."
    required: false
  growth_limit:
    default: -1.0
    description:
      - "Specifies that the autogrow operation is limited to the specified
       storage amount that sets the growth limit.\n"
    required: false
  growth_limit_unit:
    choices:
      - MiB
      - GiB
      - TiB
    default: GiB
    description:
      - "Unit of growth limit."
    required: false
  growth_warning:
    default: -1.0
    description:
      - "Specifies that the threshold of used logical disk space when exceeded
       results in a warning alert.\n"
    required: false
  growth_warning_unit:
    choices:
      - MiB
      - GiB
      - TiB
    default: GiB
    description:
      - "Unit of growth warning."
    required: false
  high_availability:
    choices:
      - PORT
      - CAGE
      - MAG
    description:
      - "Specifies that the layout must support the failure of one port pair,
       one cage, or one magazine.\n"
    required: false
  raid_type:
    choices:
      - R0
      - R1
      - R5
      - R6
    description:
      - "Specifies the RAID type for the logical disk."
    required: false
  set_size:
    default: -1
    description:
      - "Specifies the set size in the number of chunklets."
    required: false
  state:
    choices:
      - present
      - absent
    description:
      - "Whether the specified CPG should exist or not."
    required: true
extends_documentation_fragment: hpe3par
short_description: "Manage HPE 3PAR CPG"
version_added: "2.4"
'''


EXAMPLES = r'''
    - name: Create CPG "{{ cpg_name }}"
      hpe3par_cpg:
        storage_system_ip="{{ storage_system_ip }}"
        storage_system_username="{{ storage_system_username }}"
        storage_system_password="{{ storage_system_password }}"
        state=present
        cpg_name="{{ cpg_name }}"
        domain="{{ domain }}"
        growth_increment="{{ growth_increment }}"
        growth_increment_unit="{{ growth_increment_unit }}"
        growth_limit="{{ growth_limit }}"
        growth_limit_unit="{{ growth_limit_unit }}"
        growth_warning="{{ growth_warning }}"
        growth_warning_unit="{{ growth_warning_unit }}"
        raid_type="{{ raid_type }}"
        set_size="{{ set_size }}"
        high_availability="{{ high_availability }}"
        disk_type="{{ disk_type }}"

    - name: Delete CPG "{{ cpg_name }}"
      hpe3par_cpg:
        storage_system_ip="{{ storage_system_ip }}"
        storage_system_username="{{ storage_system_username }}"
        storage_system_password="{{ storage_system_password }}"
        state=absent
        cpg_name="{{ cpg_name }}"
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
from hpe3par_sdk import client


def convert_to_binary_multiple(size, size_unit):
    size_mib = 0
    if size_unit == 'GiB':
        size_mib = size * 1024
    elif size_unit == 'TiB':
        size_mib = size * 1048576
    elif size_unit == 'MiB':
        size_mib = size
    return int(size_mib)


def validate_set_size(raid_type, set_size):
    if raid_type is not None or set_size is not None:
        set_size_array = client.HPE3ParClient.RAID_MAP[raid_type]['set_sizes']
        if set_size in set_size_array:
            return True
    return False


def cpg_ldlayout_map(ldlayout_dict):
    if ldlayout_dict['RAIDType'] is not None and ldlayout_dict['RAIDType']:
        ldlayout_dict['RAIDType'] = client.HPE3ParClient.RAID_MAP[
            ldlayout_dict['RAIDType']]['raid_value']
    if ldlayout_dict['HA'] is not None and ldlayout_dict['HA']:
        ldlayout_dict['HA'] = getattr(
            client.HPE3ParClient, ldlayout_dict['HA'])
    return ldlayout_dict


def create_cpg(
        client_obj,
        storage_system_username,
        storage_system_password,
        cpg_name,
        domain,
        growth_increment,
        growth_increment_unit,
        growth_limit,
        growth_limit_unit,
        growth_warning,
        growth_warning_unit,
        raid_type,
        set_size,
        high_availability,
        disk_type):
    if storage_system_username is None or storage_system_password is None:
        return (
            False,
            False,
            "CPG create failed. Storage system username or password is null",
            {})
    if cpg_name is None:
        return (False, False, "CPG create failed. CPG name is null", {})
    if len(cpg_name) < 1 or len(cpg_name) > 31:
        return (False, False, "CPG create failed. CPG name must be atleast 1 character and more than 31 characters", {})
    if not validate_set_size(raid_type, set_size):
        return (False, False, "Set size not part of RAID set", {})
    try:
        validate_set_size(raid_type, set_size)
        client_obj.login(storage_system_username, storage_system_password)
        if not client_obj.cpgExists(cpg_name):
            ld_layout = dict()
            disk_patterns = []
            if disk_type is not None and disk_type:
                disk_type = getattr(client.HPE3ParClient, disk_type)
                disk_patterns = [{'diskType': disk_type}]
            ld_layout = {
                'RAIDType': raid_type,
                'setSize': set_size,
                'HA': high_availability,
                'diskPatterns': disk_patterns}
            ld_layout = cpg_ldlayout_map(ld_layout)
            if growth_increment is not None:
                growth_increment = convert_to_binary_multiple(
                    growth_increment, growth_increment_unit)
            if growth_limit is not None:
                growth_limit = convert_to_binary_multiple(
                    growth_limit, growth_limit_unit)
            if growth_warning is not None:
                growth_warning = convert_to_binary_multiple(
                    growth_warning, growth_warning_unit)
            optional = {
                'domain': domain,
                'growthIncrementMiB': growth_increment,
                'growthLimitMiB': growth_limit,
                'usedLDWarningAlertMiB': growth_warning,
                'LDLayout': ld_layout}
            client_obj.createCPG(cpg_name, optional)
        else:
            return (True, False, "CPG already present", {})
    except Exception as e:
        return (False, False, "CPG creation failed | %s" % (e), {})
    finally:
        client_obj.logout()
    return (True, True, "Created CPG %s successfully." % cpg_name, {})


def delete_cpg(
        client_obj,
        storage_system_username,
        storage_system_password,
        cpg_name):
    if storage_system_username is None or storage_system_password is None:
        return (
            False,
            False,
            "CPG delete failed. Storage system username or password is null",
            {})
    if cpg_name is None:
        return (False, False, "CPG delete failed. CPG name is null", {})
    if len(cpg_name) < 1 or len(cpg_name) > 31:
        return (False, False, "CPG create failed. CPG name must be atleast 1 character and more than 31 characters", {})
    try:
        client_obj.login(storage_system_username, storage_system_password)
        if client_obj.cpgExists(cpg_name):
            client_obj.deleteCPG(cpg_name)
        else:
            return (True, False, "CPG does not exist", {})
    except Exception as e:
        return (False, False, "CPG delete failed | %s" % e, {})
    finally:
        client_obj.logout()
    return (True, True, "Deleted CPG %s successfully." % cpg_name, {})


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
        "cpg_name": {
            "required": True,
            "type": "str"
        },
        "domain": {
            "type": "str"
        },
        "growth_increment": {
            "type": "float",
            "default": -1.0
        },
        "growth_increment_unit": {
            "type": "str",
            "choices": ['TiB', 'GiB', 'MiB'],
            "default": 'GiB'
        },
        "growth_limit": {
            "type": "float",
            "default": -1.0
        },
        "growth_limit_unit": {
            "type": "str",
            "choices": ['TiB', 'GiB', 'MiB'],
            "default": 'GiB'
        },
        "growth_warning": {
            "type": "float",
            "default": -1.0
        },
        "growth_warning_unit": {
            "type": "str",
            "choices": ['TiB', 'GiB', 'MiB'],
            "default": 'GiB'
        },
        "raid_type": {
            "required": False,
            "type": "str",
            "choices": ['R0', 'R1', 'R5', 'R6'],
        },
        "set_size": {
            "required": False,
            "type": "int",
            "default": -1
        },
        "high_availability": {
            "type": "str",
            "choices": ['PORT', 'CAGE', 'MAG'],
        },
        "disk_type": {
            "type": "str",
            "choices": ['FC', 'NL', 'SSD'],
        }
    }

    module = AnsibleModule(argument_spec=fields)

    storage_system_ip = module.params["storage_system_ip"]
    storage_system_username = module.params["storage_system_username"]
    storage_system_password = module.params["storage_system_password"]
    cpg_name = module.params["cpg_name"]
    domain = module.params["domain"]
    growth_increment = module.params["growth_increment"]
    growth_increment_unit = module.params["growth_increment_unit"]
    growth_limit = module.params["growth_limit"]
    growth_limit_unit = module.params["growth_limit_unit"]
    growth_warning = module.params["growth_warning"]
    growth_warning_unit = module.params["growth_warning_unit"]
    raid_type = module.params["raid_type"]
    set_size = module.params["set_size"]
    high_availability = module.params["high_availability"]
    disk_type = module.params["disk_type"]

    wsapi_url = 'https://%s:8080/api/v1' % storage_system_ip
    client_obj = client.HPE3ParClient(wsapi_url)

    # States
    if module.params["state"] == "present":
        return_status, changed, msg, issue_attr_dict = create_cpg(
            client_obj,
            storage_system_username,
            storage_system_password,
            cpg_name,
            domain,
            growth_increment,
            growth_increment_unit,
            growth_limit,
            growth_limit_unit,
            growth_warning,
            growth_warning_unit,
            raid_type,
            set_size,
            high_availability,
            disk_type
        )
    elif module.params["state"] == "absent":
        return_status, changed, msg, issue_attr_dict = delete_cpg(
            client_obj,
            storage_system_username,
            storage_system_password,
            cpg_name
        )

    if return_status:
        if issue_attr_dict:
            module.exit_json(changed=changed, msg=msg, issue=issue_attr_dict)
        else:
            module.exit_json(changed=changed, msg=msg)
    else:
        module.fail_json(msg=msg)


if __name__ == '__main__':
    main()
