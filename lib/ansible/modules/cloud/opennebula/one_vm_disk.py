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
module: one_vm_disk
short_description: Manage disks related to OpenNebula VMs
description:
    - This module can be used to add, remove and update Volatile disks to a given virtual machines.
    - This module is destructive in nature, please read documentation carefully before proceeding.
    - Be careful while removing disk specified as this may lead to data loss.
version_added: "2.10"
requirements:
  - pyone
options:
  ids:
    type: list
    description:
      - A list of VM ids whose disks will be modified.
    aliases: ['id']
  name:
    description:
      - A C(name) of the VM whose disks will be modified.
      - If the C(name) begins with '~' the C(name) will be used as regex pattern
      - which restricts the list of VMs (whose facts will be returned) whose names match specified regex.
      - Also, if the C(name) begins with '~*' case-insensitive matching will be performed.
      - See examples for more details.
    type: str
  disks:
    description:
      - A list of disks to add.
      - The virtual disk related information is provided using this list.
      - All values and parameters are case sensitive.
      - For all Valid Values please take a look at the OpenNebula Docu.
      - 'Valid attributes are:'
      - ' - C(SIZE) (integer): Disk storage size in MB.'
      - ' - C(DISK_ID) (integer): Disk ID'
      - '   Keep in mind that the contextualization takes one image ID which can not be used for Disks.'
      - ' - C(TYPE) (string): Valid values are:'
      - '     - C(fs)'
      - '     - C(swap)'
      - ' - C(DEV_PREFIX) (string): Valid values are:'
      - '     - C(sd) SCSI BUS'
      - '     - C(hd) IDE BUS'
      - '     - C(vd) Virtio BUS'
      - ' - C(VCENTER_DISK_TYPE) (string): (VMware only) Valid values are:'
      - '     - C(thin) thin disk'
      - '     - C(eagerzeroedthick) eagerzeroedthick disk'
      - '     - C(thick) thick disk'
      - '     Default: C(thin) thin disk'
      - ' - C(state) (string): State of disk. This is either "absent" or "present".'
      - '   If C(state) is set to C(absent), disk will be removed permanently.'
      - '   If C(state) is set to C(present), disk will be added if not present.'
      - '   If C(state) is set to C(present) and disk exists with different size, disk size is increased.'
      - '   Reducing disk size is not allowed.'
    default: ['[]']
    type: list
extends_documentation_fragment: opennebula
author:
    - "Jan Meerkamp (@meerkampdvv)"
'''

EXAMPLES = '''

# Add one disk with 5GB to the VM id 425
- one_vm_disk:
    id: 425
    disks:
      - SIZE: 5120
        TYPE: fs
        DEV_PREFIX: sd
        DISK_ID: 2
        state: present

# remove the disk with ID 5 from the VM id 425
- one_vm_disk:
    id: 425
    disks:
      - DISK_ID: 5
        state: absent

# Add one disk with 5GB to the VM id 425 and 429
- one_vm_disk:
    id:
      - "425"
      - "429"
    disks:
      - SIZE: 5120
        TYPE: fs
        DEV_PREFIX: sd
        DISK_ID: 2
        state: present

# Add one disk with 5GB to the VM using the name
- one_vm_disk:
    name: 'foo-VM'
    disks:
      - SIZE: 5120
        TYPE: fs
        DEV_PREFIX: sd
        DISK_ID: 2
        state: present

# Add one disk with 5GB to the VM whose name matches regex 'app-vm-.*'
- one_vm_disk:
    name: '~app-vm-.*'
    disks:
      - SIZE: 5120
        TYPE: fs
        DEV_PREFIX: sd
        DISK_ID: 2
        state: present

# Add one disk with 5GB to the VM whose name matches regex 'foo-vm-.*' ignoring cases
- one_vm_disk:
    name: '~*foo-vm-.*'
    disks:
      - SIZE: 5120
        TYPE: fs
        DEV_PREFIX: sd
        DISK_ID: 2
        state: present
'''

RETURN = '''
vms:
    description: A list of vms
    type: list
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
        disks:
            description: The ID and size of the disk in MB
            type: list
            sample: [
                        {
                            "DISK_ID": "0",
                            "SIZE": "35840 MB"
                        },
                        {
                            "DISK_ID": "2",
                            "SIZE": "10240 MB"
                        }
                    ]
        disk_changes:
            description: List of changes
            type: list
            sample: {
                        "2": "Disk already exists.",
                        "3": "Disk size increased.",
                        "4": "Disk deleted.",
                        "5": "Disk not found."
                    }

'''

from ansible.module_utils.opennebula import OpenNebulaModule
from ansible.module_utils.basic import AnsibleModule
import os
import time

VM_STATES = ['INIT', 'PENDING', 'HOLD', 'ACTIVE', 'STOPPED', 'SUSPENDED', 'DONE', '', 'POWEROFF', 'UNDEPLOYED', 'CLONING', 'CLONING_FAILURE']
LCM_STATES = ['LCM_INIT', 'PROLOG', 'BOOT', 'RUNNING', 'MIGRATE', 'SAVE_STOP',
              'SAVE_SUSPEND', 'SAVE_MIGRATE', 'PROLOG_MIGRATE', 'PROLOG_RESUME',
              'EPILOG_STOP', 'EPILOG', 'SHUTDOWN', 'STATE13', 'STATE14', 'CLEANUP_RESUBMIT', 'UNKNOWN', 'HOTPLUG', 'SHUTDOWN_POWEROFF',
              'BOOT_UNKNOWN', 'BOOT_POWEROFF', 'BOOT_SUSPENDED', 'BOOT_STOPPED', 'CLEANUP_DELETE', 'HOTPLUG_SNAPSHOT', 'HOTPLUG_NIC',
              'HOTPLUG_SAVEAS', 'HOTPLUG_SAVEAS_POWEROFF', 'HOTPULG_SAVEAS_SUSPENDED', 'SHUTDOWN_UNDEPLOY']


def wait_for_state(one, vm, wait_timeout, state_predicate):
    import time
    start_time = time.time()

    while (time.time() - start_time) < wait_timeout:
        vm = one.one.vm.info(vm.ID)
        state = vm.STATE
        lcm_state = vm.LCM_STATE

        if state_predicate(state, lcm_state):
            return vm
        elif state not in [VM_STATES.index('INIT'), VM_STATES.index('PENDING'), VM_STATES.index('HOLD'),
                           VM_STATES.index('ACTIVE'), VM_STATES.index('CLONING'), VM_STATES.index('POWEROFF')]:
            one.module.fail_json(msg='Action is unsuccessful. VM state: ' + VM_STATES[state])

        time.sleep(1)

    one.module.fail_json(msg="Wait timeout has expired!")


def wait_for_running(one, vm, wait_timeout):
    return wait_for_state(one, vm, wait_timeout, lambda state,
                          lcm_state: (state in [VM_STATES.index('ACTIVE')] and lcm_state in [LCM_STATES.index('RUNNING')]))


def create_disk_str(one, disk, vm):
    vm_info = one.one.vm.info(vm.ID)
    disk_str = 'DISK=['
    disk_str += ','.join('{key}="{val}"'.format(key=key, val=val) for key, val in disk.items())
    disk_str += ']'
    return disk_str


def get_disk_by_id(one, vm, disk):
    vm_info = one.one.vm.info(vm.ID)
    if 'DISK' in vm_info.TEMPLATE:
        if isinstance(vm_info.TEMPLATE['DISK'], list):
            for vm_info_disk in vm_info.TEMPLATE['DISK']:
                if int(vm_info_disk['DISK_ID']) == int(disk['DISK_ID']):
                    return vm_info_disk
        else:
            if int(vm_info.TEMPLATE['DISK']['DISK_ID']) == int(disk['DISK_ID']):
                return vm_info.TEMPLATE['DISK']


def vm_set_disks(one, vm, disks, wait_timeout):
    result = dict()
    disk_change = False
    vm_info = one.one.vm.info(vm.ID)
    for disk in disks:
        # catch context disk ID
        if int(disk['DISK_ID']) == int(vm_info.TEMPLATE['CONTEXT']['DISK_ID']):
            one.module.fail_json(msg='Disk ID: ' + str(disk['DISK_ID']) + ' is used by CONTEXT and connot be used.')
        vm_disk = get_disk_by_id(one, vm, disk)
        if disk['state'] == 'present':
            if vm_disk:
                if int(disk['SIZE']) < int(vm_disk['SIZE']):
                    one.module.fail_json(msg="Given disk size at disk ID [%s] is smaller than found (%s < %s)."
                                         " Reducing disks is not allowed." % (disk['DISK_ID'],
                                                                              disk['SIZE'],
                                                                              vm_disk['SIZE']))
                if int(disk['SIZE']) > int(vm_disk['SIZE']):
                    one.one.vm.diskresize(vm.ID, int(disk['DISK_ID']), str(disk['SIZE']))
                    wait_for_running(one, vm, wait_timeout)
                    disk_change = True
                    result[disk['DISK_ID']] = "Disk size increased."
                if int(disk['SIZE']) == int(vm_disk['SIZE']):
                    result[disk['DISK_ID']] = "Disk already exists."
            else:
                disk_str = create_disk_str(one, disk, vm)
                one.one.vm.attach(vm.ID, disk_str)
                wait_for_running(one, vm, wait_timeout)
                disk_change = True
                result[disk['DISK_ID']] = "Disk created."
        elif disk['state'] == 'absent':
            if vm_disk:
                one.one.vm.detach(vm.ID, disk['DISK_ID'])
                wait_for_running(one, vm, wait_timeout)
                disk_change = True
                result[disk['DISK_ID']] = "Disk deleted."
            else:
                result[disk['DISK_ID']] = "Disk not found."
    return disk_change, result


def main():
    fields = {
        "ids": {"required": False, "aliases": ['id'], "type": "list"},
        "name": {"required": False, "type": "str"},
        "disks": {
            "default": "[]",
            "type": "list"
        }
    }

    mutually_exclusive = [['ids', 'name']]

    one = OpenNebulaModule(argument_spec=fields, supports_check_mode=True, mutually_exclusive=mutually_exclusive)

    # ensure that all ids are int.
    str_ids = one.module.params.get('ids')
    ids = []
    for str_id in str_ids:
        ids.append(int(str_id))

    name = one.module.params.get('name')
    disks = one.module.params.get('disks')
    wait_timeout = one.module.params.get('wait_timeout')

    results = {'vms': []}
    vms = []

    if ids:
        vms = one.get_vms_by_ids(ids)
    elif name:
        vms = one.get_vms_by_name(name)

    for vm in vms:
        result = dict()
        result = one.get_vm_info(vm)
        results['changed'], result['disk_changes'] = vm_set_disks(one, vm, disks, wait_timeout)
        results['vms'].append(result)

    one.module.exit_json(**results)


if __name__ == '__main__':
    main()
