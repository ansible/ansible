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
description: "On HPE 3PAR - Create Volume. - Delete Volume. - Modify Volume.
 - Grow Volume - Grow Volume to certain size - Change Snap CPG - Change User
 CPG - Convert Provisioning TypeError - Set Snap CPG"
module: hpe3par_volume
options:
  compression:
    default: false
    description:
      - "Specifes whether the compression is on or off."
    required: false
    type: bool
  cpg:
    description:
      - "Specifies the name of the CPG from which the volume user space will be
       allocated.\nRequired with action present, change_user_cpg\n"
    required: false
  expiration_hours:
    default: 0
    description:
      - "Remaining time, in hours, before the volume expires."
    required: false
  keep_vv:
    description:
      - "Name of the new volume where the original logical disks are saved."
    required: false
  new_name:
    description:
      - "Specifies the new name for the volume."
    required: false
  retention_hours:
    default: 0
    description:
      - "Sets the number of hours to retain the volume."
    required: false
  rm_exp_time:
    default: 0
    description:
      - "Enables false or disables true resetting the expiration time. If
       false, and expiration time value is a positive. number, then set.\n"
    required: false
    type: bool
  rm_ss_spc_alloc_limit:
    default: false
    description:
      - "Enables false or disables true removing the snapshot space allocation
       limit. If false, and limit value is 0, setting  ignored.If false, and
       limit value is a positive number, then set.\n"
    required: false
    type: bool
  rm_ss_spc_alloc_warning:
    default: false
    description:
      - "Enables false or disables true removing the snapshot space allocation
       warning. If false, and warning value is a positive number, then set.\n"
    required: false
    type: bool
  rm_usr_spc_alloc_limit:
    default: false
    description:
      - "Enables false or disables true the allocation limit. If false, and
       limit value is a positive number, then set.\n"
    required: false
    type: bool
  rm_usr_spc_alloc_warning:
    default: false
    description:
      - "Enables false or disables true removing the user space allocation
       warning. If false, and warning value is a positive number, then set.\n"
    required: false
    type: bool
  size:
    description:
      - "Specifies the size of the volume.\nRequired with action present, grow,
       grow_to_size\n"
    required: false
  size_unit:
    choices:
      - MiB
      - GiB
      - TiB
    default: MiB
    description:
      - "Specifies the unit of the volume size.\nRequired with action present,
       grow, grow_to_size\n"
    required: false
  snap_cpg:
    description:
      - "Specifies the name of the CPG from which the snapshot space will be
       allocated.\nRequired with action change_snap_cpg\n"
    required: false
  ss_spc_alloc_limit_pct:
    default: 0
    description:
      - "Prevents the snapshot space of  the virtual volume from growing beyond
       the indicated percentage of the virtual volume size.\n"
    required: false
  ss_spc_alloc_warning_pct:
    default: 0
    description:
      - "Generates a warning alert when the reserved snapshot space of the
       virtual volume exceeds the indicated percentage of the virtual volume
       size.\n"
    required: false
  state:
    choices:
      - present
      - absent
      - modify
      - grow
      - grow_to_size
      - change_snap_cpg
      - change_user_cpg
      - convert_type
      - set_snap_cpg
    description:
      - "Whether the specified Volume should exist or not. State also provides
       actions to modify volume properties.\n"
    required: true
  type:
    choices:
      - thin
      - thin_dedupe
      - full
    default: thin
    description:
      - "Specifies the type of the volume.\nRequired with action convert_type"
    required: false
  usr_spc_alloc_limit_pct:
    default: 0
    description:
      - "Prevents the user space of the TPVV from growing beyond the indicated
       percentage of the virtual volume size. After reaching this limit, any
       new writes to the virtual volume will fail.\n"
    required: false
  usr_spc_alloc_warning_pct:
    default: 0
    description:
      - "Generates a warning alert when the user data space of the TPVV exceeds
       the specified percentage of the virtual volume size.\n"
    required: false
  volume_name:
    description:
      - "Name of the Virtual Volume."
    required: true
  wait_for_task_to_end:
    default: false
    description:
      - "Setting to true makes the resource to wait until a task asynchronous
       operation, for ex convert type ends.\n"
    required: false
    type: bool
extends_documentation_fragment: hpe3par
short_description: "Manage HPE 3PAR Volume"
version_added: "2.4"
'''

EXAMPLES = r'''
    - name: Create Volume "{{ volume_name }}"
      hpe3par_volume:
        storage_system_ip="{{ storage_system_ip }}"
        storage_system_username="{{ storage_system_username }}"
        storage_system_password="{{ storage_system_password }}"
        state=present
        volume_name="{{ volume_name }}"
        cpg="{{ cpg }}"
        size="{{ size }}"
        snap_cpg="{{ snap_cpg }}"

    - name: Change provisioning type of Volume "{{ volume_name }}" to
    "{{ type }}"
      hpe3par_volume:
        storage_system_ip="{{ storage_system_ip }}"
        storage_system_username="{{ storage_system_username }}"
        storage_system_password="{{ storage_system_password }}"
        state=convert_type
        volume_name="{{ volume_name }}"
        type="{{ type }}"
        cpg="{{ cpg }}"
        wait_for_task_to_end="{{ wait_for_task_to_end }}"

    - name: Set Snap CPG of Volume "{{ volume_name }}" to "{{ snap_cpg }}"
      hpe3par_volume:
        storage_system_ip="{{ storage_system_ip }}"
        storage_system_username="{{ storage_system_username }}"
        storage_system_password="{{ storage_system_password }}"
        state=set_snap_cpg
        volume_name="{{ volume_name }}"
        snap_cpg="{{ snap_cpg }}"

    - name: Change snap CPG of Volume "{{ volume_name }}" to "{{ snap_cpg }}"
      hpe3par_volume:
        storage_system_ip="{{ storage_system_ip }}"
        storage_system_username="{{ storage_system_username }}"
        storage_system_password="{{ storage_system_password }}"
        state=change_snap_cpg
        volume_name="{{ volume_name }}"
        snap_cpg="{{ snap_cpg }}"
        wait_for_task_to_end="{{ wait_for_task_to_end }}"

    - name: Grow Volume "{{ volume_name }} by "{{ size }}" {{ size_unit }}"
      hpe3par_volume:
        storage_system_ip="{{ storage_system_ip }}"
        storage_system_username="{{ storage_system_username }}"
        storage_system_password="{{ storage_system_password }}"
        state=grow
        volume_name="{{ volume_name }}"
        size="{{ size }}"
        size_unit="{{ size_unit }}"

    - name: Grow Volume "{{ volume_name }} to "{{ size }}" {{ size_unit }}"
      hpe3par_volume:
        storage_system_ip="{{ storage_system_ip }}"
        storage_system_username="{{ storage_system_username }}"
        storage_system_password="{{ storage_system_password }}"
        state=grow_to_size
        volume_name="{{ volume_name }}"
        size="{{ size }}"
        size_unit="{{ size_unit }}"

    - name: Rename Volume "{{ volume_name }} to {{ new_name }}"
      hpe3par_volume:
        storage_system_ip="{{ storage_system_ip }}"
        storage_system_username="{{ storage_system_username }}"
        storage_system_password="{{ storage_system_password }}"
        state=modify
        volume_name="{{ volume_name }}"
        new_name="{{ new_name }}"

    - name: Delete Volume "{{ volume_name }}"
      hpe3par_volume:
        storage_system_ip="{{ storage_system_ip }}"
        storage_system_username="{{ storage_system_username }}"
        storage_system_password="{{ storage_system_password }}"
        state=absent
        volume_name="{{ new_name }}"
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
from hpe3par_sdk import client
APP_TYPE = "ansible-3par-client"


def convert_to_binary_multiple(size, size_unit):
    size_mib = 0
    if size_unit == 'GiB':
        size_mib = size * 1024
    elif size_unit == 'TiB':
        size_mib = size * 1048576
    elif size_unit == 'MiB':
        size_mib = size
    return int(size_mib)


def get_volume_type(volume_type):
    enum_type = ''
    if volume_type == 'thin':
        enum_type = ['TPVV', 1]
    elif volume_type == 'thin_dedupe':
        enum_type = ['TDVV', 3]
    elif volume_type == 'full':
        enum_type = ['FPVV', 2]
    return enum_type


def create_volume(
        client_obj,
        storage_system_username,
        storage_system_password,
        volume_name,
        cpg,
        size,
        size_unit,
        type,
        compression,
        snap_cpg):
    if storage_system_username is None or storage_system_password is None:
        return (
            False,
            False,
            "Volume creation failed. Storage system username or password is \
null",
            {})
    if volume_name is None:
        return (
            False,
            False,
            "Volume creation failed. Volume name is null",
            {})
    if len(volume_name) < 1 or len(volume_name) > 31:
        return (False, False, "Volume create failed. Volume name must be atleast 1 character and more than 31 characters", {})
    if cpg is None:
        return (False, False, "Volume creation failed. Cpg is null", {})
    if size is None:
        return (
            False,
            False,
            "Volume creation failed. Volume size is null",
            {})
    if size_unit is None:
        return (
            False,
            False,
            "Volume creation failed. Volume size_unit is null",
            {})
    try:
        client_obj.login(storage_system_username, storage_system_password)
        if not client_obj.volumeExists(volume_name):
            tpvv = False
            tdvv = False
            if type == 'thin':
                tpvv = True
            elif type == 'thin_dedupe':
                tdvv = True
            size_in_mib = convert_to_binary_multiple(
                size, size_unit)
            optional = {'tpvv': tpvv, 'tdvv': tdvv, 'snapCPG': snap_cpg,
                        'compression': compression,
                        'objectKeyValues': [
                            {'key': 'type', 'value': 'ansible-3par-client'}]}
            client_obj.createVolume(volume_name, cpg, size_in_mib, optional)
        else:
            return (True, False, "Volume already present", {})
    except Exception as e:
        return (False, False, "Volume creation failed | %s" % e, {})
    finally:
        client_obj.logout()
    return (True, True, "Created volume %s successfully." % volume_name, {})


def delete_volume(
        client_obj,
        storage_system_username,
        storage_system_password,
        volume_name):
    if storage_system_username is None or storage_system_password is None:
        return (
            False,
            False,
            "Volume delete failed. Storage system username or password is \
null",
            {})
    if volume_name is None:
        return (False, False, "Volume delete failed. Volume name is null", {})
    if len(volume_name) < 1 or len(volume_name) > 31:
        return (False, False, "Volume create failed. Volume name must be atleast 1 character and more than 31 characters", {})
    try:
        client_obj.login(storage_system_username, storage_system_password)
        if client_obj.volumeExists(volume_name):
            client_obj.deleteVolume(volume_name)
        else:
            return (True, False, "Volume does not exist", {})
    except Exception as e:
        return (False, False, "Volume delete failed | %s" % e, {})
    finally:
        client_obj.logout()
    return (True, True, "Deleted volume %s successfully." % volume_name, {})


def grow(
        client_obj,
        storage_system_username,
        storage_system_password,
        volume_name,
        size,
        size_unit):
    if storage_system_username is None or storage_system_password is None:
        return (
            False,
            False,
            "Grow volume failed. Storage system username or password is null",
            {})
    if volume_name is None:
        return (False, False, "Grow volume failed. Volume name is null", {})
    if len(volume_name) < 1 or len(volume_name) > 31:
        return (False, False, "Volume create failed. Volume name must be atleast 1 character and more than 31 characters", {})
    if size is None:
        return (False, False, "Grow volume failed. Volume size is null", {})
    if size_unit is None:
        return (
            False,
            False,
            "Grow volume failed. Volume size_unit is null",
            {})
    try:
        client_obj.login(storage_system_username, storage_system_password)
        size_mib = convert_to_binary_multiple(size, size_unit)
        client_obj.growVolume(volume_name, size_mib)
    except Exception as e:
        return (False, False, "Grow volume failed | %s" % e, {})
    finally:
        client_obj.logout()
    return (
        True, True, "Grown volume %s by %s %s successfully." %
        (volume_name, size, size_unit), {})


def grow_to_size(
        client_obj,
        storage_system_username,
        storage_system_password,
        volume_name,
        size,
        size_unit):
    if storage_system_username is None or storage_system_password is None:
        return (
            False,
            False,
            "Grow_to_size volume failed. Storage system username or password \
is null",
            {})
    if volume_name is None:
        return (
            False,
            False,
            "Grow_to_size volume failed. Volume name is null",
            {})
    if len(volume_name) < 1 or len(volume_name) > 31:
        return (False, False, "Volume create failed. Volume name must be atleast 1 character and more than 31 characters", {})
    if size is None:
        return (
            False,
            False,
            "Grow_to_size volume failed. Volume size is null",
            {})
    if size_unit is None:
        return (
            False,
            False,
            "Grow_to_size volume failed. Volume size_unit is null",
            {})
    try:
        client_obj.login(
            storage_system_username, storage_system_password)
        if client_obj.volumeExists(
                volume_name):
            if client_obj.getVolume(
                    volume_name).size_mib < convert_to_binary_multiple(
                    size, size_unit):
                client_obj.growVolume(volume_name, convert_to_binary_multiple(
                    size, size_unit) - client_obj.getVolume(
                    volume_name).size_mib)
            else:
                return (
                    True,
                    False,
                    "Volume size already >= %s %s" % (size, size_unit),
                    {})
        else:
            return (
                False,
                False,
                "Volume does not exist",
                {})
    except Exception as e:
        return (False, False, "Volume Grow To Size failed | %s" % e, {})
    finally:
        client_obj.logout()
    return (
        True, True, "Grown volume %s to %s %s successfully." %
        (volume_name, size, size_unit), {})


def change_snap_cpg(
        client_obj,
        storage_system_username,
        storage_system_password,
        volume_name,
        snap_cpg,
        wait_for_task_to_end):
    if storage_system_username is None or storage_system_password is None:
        return (
            False,
            False,
            "Change snap CPG failed. Storage system username or password is \
null",
            {})
    if volume_name is None:
        return (
            False,
            False,
            "Change snap CPG failed. Volume name is null",
            {})
    if len(volume_name) < 1 or len(volume_name) > 31:
        return (False, False, "Volume create failed. Volume name must be atleast 1 character and more than 31 characters", {})
    if snap_cpg is None:
        return (False, False, "Change snap CPG failed. Snap CPG is null", {})
    try:
        client_obj.login(storage_system_username, storage_system_password)
        if client_obj.volumeExists(volume_name):
            if client_obj.getVolume(volume_name).snap_cpg != snap_cpg:
                snp_cpg = 2
                task = client_obj.tuneVolume(
                    volume_name, snp_cpg, {
                        'snapCPG': snap_cpg})
                if wait_for_task_to_end:
                    client_obj.waitForTaskToEnd(task.task_id)
            else:
                return (True, False, "Snap CPG already set to %s" % snap_cpg,
                        {})
        else:
            return (False, False, "Volume does not exist", {})
    except Exception as e:
        return (False, False, "Change snap CPG failed | %s" % e, {})
    finally:
        client_obj.logout()
    return (True, True, "Changed snap CPG to %s successfully." % snap_cpg, {})


def change_user_cpg(
        client_obj,
        storage_system_username,
        storage_system_password,
        volume_name,
        cpg,
        wait_for_task_to_end):
    if storage_system_username is None or storage_system_password is None:
        return (
            False,
            False,
            "Change user CPG failed. Storage system username or password is \
null",
            {})
    if volume_name is None:
        return (
            False,
            False,
            "Change user CPG failed. Volume name is null",
            {})
    if len(volume_name) < 1 or len(volume_name) > 31:
        return (False, False, "Volume create failed. Volume name must be atleast 1 character and more than 31 characters", {})
    if cpg is None:
        return (False, False, "Change user CPG failed. Snap CPG is null", {})
    try:
        client_obj.login(storage_system_username, storage_system_password)
        if client_obj.volumeExists(volume_name):
            if client_obj.getVolume(volume_name).user_cpg != cpg:
                usr_cpg = 1
                task = client_obj.tuneVolume(
                    volume_name, usr_cpg, {'userCPG': cpg})
                if wait_for_task_to_end:
                    client_obj.waitForTaskToEnd(task.task_id)
            else:
                return (True, False, "user CPG already set to %s" % cpg, {})
        else:
            return (False, False, "Volume does not exist", {})
    except Exception as e:
        return (False, False, "Change user CPG failed | %s" % e, {})
    finally:
        client_obj.logout()
    return (True, True, "Changed user CPG to %s successfully." % cpg, {})


def convert_type(
        client_obj,
        storage_system_username,
        storage_system_password,
        volume_name,
        cpg,
        type,
        wait_for_task_to_end,
        keep_vv,
        compression):
    if storage_system_username is None or storage_system_password is None:
        return (
            False,
            False,
            "Convert volume type failed. Storage system username or password \
is null",
            {})
    if volume_name is None:
        return (
            False,
            False,
            "Convert volume type failed. Volume name is null",
            {})
    if len(volume_name) < 1 or len(volume_name) > 31:
        return (False, False, "Volume create failed. Volume name must be atleast 1 character and more than 31 characters", {})
    if cpg is None:
        return (
            False,
            False,
            "Convert volume type failed. Snap CPG is null",
            {})
    if type is None:
        return (
            False,
            False,
            "Convert volume type failed. Volume type is null",
            {})
    try:
        client_obj.login(storage_system_username, storage_system_password)
        provisioning_type = client_obj.getVolume(volume_name).provisioning_type
        if provisioning_type == 1:
            volume_type = 'FPVV'
        elif provisioning_type == 2:
            volume_type = 'TPVV'
        elif provisioning_type == 6:
            volume_type = 'TDVV'
        else:
            volume_type = 'UNKNOWN'

        if client_obj.volumeExists(volume_name):
            if (volume_type != get_volume_type(type)[0] or
                    volume_type == 'UNKNOWN'):
                new_vol_type = get_volume_type(type)[1]
                usr_cpg = 1
                optional = {'userCPG': cpg,
                            'conversionOperation': new_vol_type,
                            'keepVV': keep_vv
                            }

                task = client_obj.tuneVolume(volume_name,
                                             usr_cpg,
                                             optional)
                if wait_for_task_to_end:
                    client_obj.waitForTaskToEnd(task.task_id)
            else:
                return (
                    True,
                    False,
                    "Provisioning type already set to %s" %
                    type,
                    {})
        else:
            return (
                False,
                False,
                "Volume does not exist",
                {})
    except Exception as e:
        return (False, False, "Provisioning type change failed | %s" % e, {})
    finally:
        client_obj.logout()
    return (
        True,
        True,
        "Provisioning type changed to %s successfully." %
        type,
        {})


def modify_volume(
        client_obj,
        storage_system_username,
        storage_system_password,
        volume_name,
        new_name,
        expiration_hours,
        retention_hours,
        ss_spc_alloc_warning_pct,
        ss_spc_alloc_limit_pct,
        usr_spc_alloc_warning_pct,
        usr_spc_alloc_limit_pct,
        rm_ss_spc_alloc_warning,
        rm_usr_spc_alloc_warning,
        rm_exp_time,
        rm_usr_spc_alloc_limit,
        rm_ss_spc_alloc_limit,
        user_cpg,
        snap_cpg):
    if storage_system_username is None or storage_system_password is None:
        return (
            False,
            False,
            "Modify volume type failed. Storage system username or password \
is null",
            {})
    if volume_name is None:
        return (
            False,
            False,
            "Modify volume type failed. Volume name is null",
            {})
    if len(volume_name) < 1 or len(volume_name) > 31:
        return (False, False, "Volume create failed. Volume name must be atleast 1 character and more than 31 characters", {})
    try:
        client_obj.login(storage_system_username, storage_system_password)
        volume_mods = {
            'expirationHours': expiration_hours,
            'newName': new_name,
            'retentionHours': retention_hours,
            'ssSpcAllocWarningPct': ss_spc_alloc_warning_pct,
            'ssSpcAllocLimitPct': ss_spc_alloc_limit_pct,
            'usrSpcAllocWarningPct': usr_spc_alloc_warning_pct,
            'usrSpcAllocLimitPct': usr_spc_alloc_limit_pct,
            'rmSsSpcAllocWarning': rm_ss_spc_alloc_warning,
            'rmUsrSpcAllocWarning': rm_usr_spc_alloc_warning,
            'rmExpTime': rm_exp_time,
            'rmSsSpcAllocLimit': rm_ss_spc_alloc_limit,
            'rmUsrSpcAllocLimit': rm_usr_spc_alloc_limit,
            'userCPG': user_cpg,
            'snapCPG': snap_cpg}
        client_obj.modifyVolume(volume_name, volume_mods, APP_TYPE)
    except Exception as e:
        return (False, False, "Modify Volume failed | %s" % e, {})
    finally:
        client_obj.logout()
    return (True, True, "Modified Volume %s successfully." % volume_name, {})


def main():

    fields = {
        "state": {
            "required": True,
            "choices": ['present',
                        'absent',
                        'modify',
                        'grow',
                        'grow_to_size',
                        'change_snap_cpg',
                        'change_user_cpg',
                        'convert_type',
                        'set_snap_cpg'
                        ],
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
        "volume_name": {
            "required": True,
            "type": "str"
        },
        "cpg": {
            "type": "str",
            "default": None
        },
        "size": {
            "type": "float",
            "default": None
        },
        "size_unit": {
            "choices": ['MiB', 'GiB', 'TiB'],
            "type": 'str',
            "default": 'MiB'
        },
        "snap_cpg": {
            "type": "str"
        },
        "wait_for_task_to_end": {
            "type": "bool",
            "default": False
        },
        "new_name": {
            "type": "str",
        },
        "expiration_hours": {
            "type": "int",
            "default": 0
        },
        "retention_hours": {
            "type": "int",
            "default": 0
        },
        "ss_spc_alloc_warning_pct": {
            "type": "int",
            "default": 0
        },
        "ss_spc_alloc_limit_pct": {
            "type": "int",
            "default": 0
        },
        "usr_spc_alloc_warning_pct": {
            "required": False,
            "type": "int",
            "default": 0
        },
        "usr_spc_alloc_limit_pct": {
            "type": "int",
            "default": 0
        },
        "rm_ss_spc_alloc_warning": {
            "type": "bool",
            "default": False
        },
        "rm_usr_spc_alloc_warning": {
            "type": "bool",
            "default": False
        },
        "rm_exp_time": {
            "type": "bool",
            "default": False
        },
        "rm_usr_spc_alloc_limit": {
            "type": "bool",
            "default": False
        },
        "rm_ss_spc_alloc_limit": {
            "type": "bool",
            "default": False
        },
        "compression": {
            "type": "bool",
            "default": False
        },
        "type": {
            "choices": ['thin', 'thin_dedupe', 'full'],
            "type": "str",
        },
        "keep_vv": {
            "type": "str",
        }
    }

    module = AnsibleModule(argument_spec=fields)

    storage_system_ip = module.params["storage_system_ip"]
    storage_system_username = module.params["storage_system_username"]
    storage_system_password = module.params["storage_system_password"]

    volume_name = module.params["volume_name"]
    size = module.params["size"]
    size_unit = module.params["size_unit"]
    cpg = module.params["cpg"]
    compression = module.params["compression"]
    snap_cpg = module.params["snap_cpg"]
    wait_for_task_to_end = module.params["wait_for_task_to_end"]

    new_name = module.params["new_name"]
    expiration_hours = module.params["expiration_hours"]
    retention_hours = module.params["retention_hours"]
    ss_spc_alloc_warning_pct = module.params["ss_spc_alloc_warning_pct"]
    ss_spc_alloc_limit_pct = module.params["ss_spc_alloc_limit_pct"]
    usr_spc_alloc_warning_pct = module.params["usr_spc_alloc_warning_pct"]
    usr_spc_alloc_limit_pct = module.params["usr_spc_alloc_limit_pct"]
    rm_ss_spc_alloc_warning = module.params["rm_ss_spc_alloc_warning"]
    rm_usr_spc_alloc_warning = module.params["rm_usr_spc_alloc_warning"]
    rm_exp_time = module.params["rm_exp_time"]
    rm_usr_spc_alloc_limit = module.params["rm_usr_spc_alloc_limit"]
    rm_ss_spc_alloc_limit = module.params["rm_ss_spc_alloc_limit"]
    compression = module.params["compression"]
    keep_vv = module.params["keep_vv"]
    type = module.params["type"]

    wsapi_url = 'https://%s:8080/api/v1' % storage_system_ip
    client_obj = client.HPE3ParClient(wsapi_url)

    # States
    if module.params["state"] == "present":
        return_status, changed, msg, issue_attr_dict = create_volume(
            client_obj, storage_system_username, storage_system_password,
            volume_name, cpg, size, size_unit, type, compression, snap_cpg)
    elif module.params["state"] == "absent":
        return_status, changed, msg, issue_attr_dict = delete_volume(
            client_obj, storage_system_username, storage_system_password,
            volume_name)
    elif module.params["state"] == "grow":
        return_status, changed, msg, issue_attr_dict = grow(
            client_obj, storage_system_username, storage_system_password,
            volume_name, size, size_unit)
    elif module.params["state"] == "grow_to_size":
        return_status, changed, msg, issue_attr_dict = grow_to_size(
            client_obj, storage_system_username, storage_system_password,
            volume_name, size, size_unit)
    elif module.params["state"] == "change_snap_cpg":
        return_status, changed, msg, issue_attr_dict = change_snap_cpg(
            client_obj, storage_system_username, storage_system_password,
            volume_name, snap_cpg, wait_for_task_to_end)
    elif module.params["state"] == "change_user_cpg":
        return_status, changed, msg, issue_attr_dict = change_user_cpg(
            client_obj, storage_system_username, storage_system_password,
            volume_name, cpg, wait_for_task_to_end)
    elif module.params["state"] == "convert_type":
        return_status, changed, msg, issue_attr_dict = convert_type(
            client_obj, storage_system_username, storage_system_password,
            volume_name, cpg, type, wait_for_task_to_end, keep_vv, compression)
    elif module.params["state"] == "modify":
        return_status, changed, msg, issue_attr_dict = (
            modify_volume(client_obj, storage_system_username,
                          storage_system_password, volume_name,
                          new_name, expiration_hours, retention_hours,
                          ss_spc_alloc_warning_pct, ss_spc_alloc_limit_pct,
                          usr_spc_alloc_warning_pct, usr_spc_alloc_limit_pct,
                          rm_ss_spc_alloc_warning, rm_usr_spc_alloc_warning,
                          rm_exp_time, rm_usr_spc_alloc_limit,
                          rm_ss_spc_alloc_limit, None, None))
    elif module.params["state"] == "set_snap_cpg":
        return_status, changed, msg, issue_attr_dict = modify_volume(
            client_obj, storage_system_username, storage_system_password,
            volume_name, None, None, None, None, None, None, None, None, None,
            None, None, None, None, snap_cpg)

    if return_status:
        if issue_attr_dict:
            module.exit_json(changed=changed, msg=msg, issue=issue_attr_dict)
        else:
            module.exit_json(changed=changed, msg=msg)
    else:
        module.fail_json(msg=msg)


if __name__ == '__main__':
    main()
