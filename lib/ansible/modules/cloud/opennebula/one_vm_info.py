#!/usr/bin/python
# -*- coding: utf-8 -*-

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

"""
(c) 2019, Jan Meerkamp <meerkamp@dvv.de>

This file is part of Ansible

Ansible is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Ansible is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a clone of the GNU General Public License
along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
"""

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: one_vm_info
short_description: Gather information on OpenNebula VMs
description:
  - Gather information on OpenNebula VMs.
version_added: "2.10"
requirements:
  - pyone
options:
  ids:
    type: list
    elements: int
    description:
      - A list of VM ids whose infos you want to gather.
    aliases: ['id']
  name:
    type: str
    description:
      - A C(name) of the VM whose infos will be gathered.
      - If the C(name) begins with '~' the C(name) will be used as regex pattern
      - which restricts the list of VMs (whose infos will be returned) whose names match specified regex.
      - Also, if the C(name) begins with '~*' case-insensitive matching will be performed.
      - See examples for more details.

extends_documentation_fragment: opennebula

author:
    - "Jan Meerkamp (@meerkampdvv)"
'''

EXAMPLES = '''
# Gather infos about all VMs
- one_vm_info:
  register: result

# Print all images infos
- debug:
    var: result

# Gather infos about an VM using ID
- one_vm_info:
    ids:
      - 123

# Gather infos about an VM using the name
- one_vm_info:
    name: 'foo-VM'
  register: foo_VM

# Gather infos about all VMs whose name matches regex 'app-vm-.*'
- one_vm_info:
    name: '~app-vm-.*'
  register: app_vm

# Gather infos about all VMs whose name matches regex 'foo-vm-.*' ignoring cases
- one_vm_info:
    name: '~*foo-vm-.*'
  register: foo_vm
'''

RETURN = '''
vms:
    description: A list of vm info
    type: complex
    returned: success
    contains:
        id:
            description: vm id
            type: int
            sample: 153
        name:
            description: vm name
            type: str
            sample: app1
        group_id:
            description: vm's group id
            type: int
            sample: 1
        group_name:
            description: vm's group name
            type: str
            sample: one-users
        owner_id:
            description: vm's owner id
            type: int
            sample: 143
        owner_name:
            description: vm's owner name
            type: str
            sample: ansible-test
        mode:
            description: vm's mode
            type: str
            returned: success
            sample: 660
        state:
            description: state of an instance
            type: str
            sample: ACTIVE
        lcm_state:
            description: lcm state of an instance that is only relevant when the state is ACTIVE
            type: str
            sample: RUNNING
        cpu:
            description: Percentage of CPU divided by 100
            type: float
            sample: 0.2
        vcpu:
            description: Number of CPUs (cores)
            type: int
            sample: 2
        memory:
            description: The size of the memory in MB
            type: str
            sample: 4096 MB
        disks:
            description: The size of the disk in MB and ID
            type: list
            sample: [
                        {
                            "DISK_ID": "0",
                            "SIZE": "35840 MB"
                        },
                        {
                            "DISK_ID": "3",
                            "SIZE": "10240 MB"
                        }
                    ]
        networks:
            description: a list of dictionaries with info about IP, NAME, MAC, SECURITY_GROUPS for each NIC
            type: list
            sample: [
                        {
                            "ip": "10.120.5.33",
                            "mac": "02:00:0a:78:05:21",
                            "name": "default-test-private",
                            "security_groups": "0,10"
                        },
                        {
                            "ip": "10.120.5.34",
                            "mac": "02:00:0a:78:05:22",
                            "name": "default-test-private",
                            "security_groups": "0"
                        }
                    ]
        uptime_h:
            description: Uptime of the instance in hours
            type: int
            sample: 35
        labels:
            description: A list of string labels that are associated with the instance
            type: list
            sample: [
                        "foo",
                        "spec-label"
                    ]
        attributes:
            description: A dictionary of key/values attributes that are associated with the instance
            type: dict
            sample: {
                        "HYPERVISOR": "kvm",
                        "LOGO": "images/logos/centos.png",
                        "TE_GALAXY": "bar",
                        "USER_INPUTS": null
                    }
'''

from ansible.module_utils.opennebula import OpenNebulaModule
from ansible.module_utils.basic import AnsibleModule
import os
import time


def get_vm_info(one, vm):

    try:
        from pyone import VM_STATE, LCM_STATE
    except ImportError:
        one.fail("pyone is required for this module")

    # get additional info
    vm = one.one.vm.info(vm.ID)
    # get Uptime
    current_time = time.localtime()
    vm_start_time = time.localtime(vm.STIME)
    vm_uptime = time.mktime(current_time) - time.mktime(vm_start_time)
    vm_uptime /= (60 * 60)

    vm_labels, vm_attributes = one.get_vm_labels_and_attributes_dict(vm.ID)

    # get disk info
    disks = []
    if 'DISK' in vm.TEMPLATE:
        if isinstance(vm.TEMPLATE['DISK'], list):
            for disk in vm.TEMPLATE['DISK']:
                disk_entry = dict()
                disk_entry['SIZE'] = disk['SIZE'] + ' MB'
                disk_entry['DISK_ID'] = disk['DISK_ID']
                disks.append(disk_entry)
        else:
            disk_entry = dict()
            disk_entry['SIZE'] = vm.TEMPLATE['DISK']['SIZE'] + ' MB'
            disk_entry['DISK_ID'] = vm.TEMPLATE['DISK']['DISK_ID']
            disks.append(disk_entry)

    # get network info
    networks_info = []
    if 'NIC' in vm.TEMPLATE:
        if isinstance(vm.TEMPLATE['NIC'], list):
            for nic in vm.TEMPLATE['NIC']:
                networks_info.append({'ip': nic['IP'], 'mac': nic['MAC'], 'name': nic['NETWORK'], 'security_groups': nic['SECURITY_GROUPS']})
        else:
            networks_info.append(
                {'ip': vm.TEMPLATE['NIC']['IP'], 'mac': vm.TEMPLATE['NIC']['MAC'],
                    'name': vm.TEMPLATE['NIC']['NETWORK'], 'security_groups': vm.TEMPLATE['NIC']['SECURITY_GROUPS']})

    info = {
        'id': vm.ID,
        'name': vm.NAME,
        'state': VM_STATE(vm.STATE).name,
        'user_name': vm.UNAME,
        'user_id': vm.UID,
        'group_name': vm.GNAME,
        'group_id': vm.GID,
        'lcm_state': LCM_STATE(vm.LCM_STATE).name,
        'uptime_h': int(vm_uptime),
        'mode': one.parse_vm_permissions(vm),
        'cpu': vm.TEMPLATE['CPU'],
        'memory': vm.TEMPLATE['MEMORY'] + ' MB',
        'disks': disks,
        'networks': networks_info,
        'labels': vm_labels,
        'attributes': vm_attributes
    }

    if "VCPU" in vm.TEMPLATE:
        info["VCPU"] = vm.TEMPLATE['VCPU']

    return info


def main():
    fields = {
        "ids": {"required": False, "aliases": ['id'], "type": "list"},
        "name": {"required": False, "type": "str"}
    }

    mutually_exclusive = [['ids', 'name']]

    one = OpenNebulaModule(argument_spec=fields, supports_check_mode=True, mutually_exclusive=mutually_exclusive)

    # ensure that all ids are int.
    str_ids = one.module.params.get('ids')
    ids = []
    for str_id in str_ids:
        ids.append(int(str_id))

    name = one.module.params.get('name')

    result = {'vms': []}
    vms = []

    if ids:
        vms = one.get_vms_by_ids(ids)
    elif name:
        vms = one.get_vms_by_name(name)
    else:
        vms = one.get_all_vms().VM

    for vm in vms:
        result['vms'].append(get_vm_info(one, vm))

    one.module.exit_json(**result)


if __name__ == '__main__':
    main()
