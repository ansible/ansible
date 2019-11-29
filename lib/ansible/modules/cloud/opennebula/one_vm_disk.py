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
  api_url:
    type: str
    description:
      - URL of the OpenNebula RPC server.
      - It is recommended to use HTTPS so that the username/password are not
      - transferred over the network unencrypted.
      - If not set then the value of the C(ONE_URL) environment variable is used.
  api_username:
    type: str
    description:
      - Name of the user to login into the OpenNebula RPC server. If not set
      - then the value of the C(ONE_USERNAME) environment variable is used.
  api_password:
    type: str
    description:
      - Password of the user to login into OpenNebula RPC server. If not set
      - then the value of the C(ONE_PASSWORD) environment variable is used.
      - if both I(api_username) or I(api_password) are not set, then it will try
      - authenticate with ONE auth file. Default path is "~/.one/one_auth".
      - Set environment variable C(ONE_AUTH) to override this path.
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
  wait_timeout:
    description:
      - timeout for adding a disk.
    type: int
    default: 300
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

try:
    import pyone
    HAS_PYONE = True
except ImportError:
    HAS_PYONE = False

from ansible.module_utils.basic import AnsibleModule
import os
import time


def get_all_vms(client):
    pool = client.vmpool.info(-2, -1, -1, -1)
    # Filter -2 means fetch all vms user has

    return pool


def parse_vm_permissions(client, vm):
    vm_PERMISSIONS = client.vm.info(vm.ID).PERMISSIONS

    owner_octal = int(vm_PERMISSIONS.OWNER_U) * 4 + int(vm_PERMISSIONS.OWNER_M) * 2 + int(vm_PERMISSIONS.OWNER_A)
    group_octal = int(vm_PERMISSIONS.GROUP_U) * 4 + int(vm_PERMISSIONS.GROUP_M) * 2 + int(vm_PERMISSIONS.GROUP_A)
    other_octal = int(vm_PERMISSIONS.OTHER_U) * 4 + int(vm_PERMISSIONS.OTHER_M) * 2 + int(vm_PERMISSIONS.OTHER_A)

    permissions = str(owner_octal) + str(group_octal) + str(other_octal)

    return permissions


def get_vm_labels_and_attributes_dict(client, vm_id):
    vm_USER_TEMPLATE = client.vm.info(vm_id).USER_TEMPLATE

    attrs_dict = {}
    labels_list = []

    for key, value in vm_USER_TEMPLATE.items():
        if key != 'LABELS':
            attrs_dict[key] = value
        else:
            if key is not None:
                labels_list = value.split(',')

    return labels_list, attrs_dict


VM_STATES = ['INIT', 'PENDING', 'HOLD', 'ACTIVE', 'STOPPED', 'SUSPENDED', 'DONE', '', 'POWEROFF', 'UNDEPLOYED', 'CLONING', 'CLONING_FAILURE']
LCM_STATES = ['LCM_INIT', 'PROLOG', 'BOOT', 'RUNNING', 'MIGRATE', 'SAVE_STOP',
              'SAVE_SUSPEND', 'SAVE_MIGRATE', 'PROLOG_MIGRATE', 'PROLOG_RESUME',
              'EPILOG_STOP', 'EPILOG', 'SHUTDOWN', 'STATE13', 'STATE14', 'CLEANUP_RESUBMIT', 'UNKNOWN', 'HOTPLUG', 'SHUTDOWN_POWEROFF',
              'BOOT_UNKNOWN', 'BOOT_POWEROFF', 'BOOT_SUSPENDED', 'BOOT_STOPPED', 'CLEANUP_DELETE', 'HOTPLUG_SNAPSHOT', 'HOTPLUG_NIC',
              'HOTPLUG_SAVEAS', 'HOTPLUG_SAVEAS_POWEROFF', 'HOTPULG_SAVEAS_SUSPENDED', 'SHUTDOWN_UNDEPLOY']


def wait_for_state(module, client, vm, wait_timeout, state_predicate):
    import time
    start_time = time.time()

    while (time.time() - start_time) < wait_timeout:
        vm = client.vm.info(vm.ID)
        state = vm.STATE
        lcm_state = vm.LCM_STATE

        if state_predicate(state, lcm_state):
            return vm
        elif state not in [VM_STATES.index('INIT'), VM_STATES.index('PENDING'), VM_STATES.index('HOLD'),
                           VM_STATES.index('ACTIVE'), VM_STATES.index('CLONING'), VM_STATES.index('POWEROFF')]:
            module.fail_json(msg='Action is unsuccessful. VM state: ' + VM_STATES[state])

        time.sleep(1)

    module.fail_json(msg="Wait timeout has expired!")


def wait_for_running(module, client, vm, wait_timeout):
    return wait_for_state(module, client, vm, wait_timeout, lambda state,
                          lcm_state: (state in [VM_STATES.index('ACTIVE')] and lcm_state in [LCM_STATES.index('RUNNING')]))


def get_vm_info(client, vm):
    # get additional
    vm = client.vm.info(vm.ID)
    # get Uptime
    current_time = time.localtime()
    vm_start_time = time.localtime(vm.STIME)
    vm_uptime = time.mktime(current_time) - time.mktime(vm_start_time)
    vm_uptime /= (60 * 60)

    vm_labels, vm_attributes = get_vm_labels_and_attributes_dict(client, vm.ID)

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
        'disks': disks
    }
    return info


def get_vms_by_ids(module, client, ids):
    vms = []
    pool = get_all_vms(client)

    for vm in pool.VM:
        if str(vm.ID) in ids:
            vms.append(vm)
            ids.remove(str(vm.ID))
            if len(ids) == 0:
                break

    if len(ids) > 0:
        module.fail_json(msg='There is no VM(s) with id(s)=' + ', '.join('{id}'.format(id=str(vm_id)) for vm_id in ids))

    return vms


def get_vms_by_name(module, client, name_pattern):

    vms = []
    pattern = None

    pool = get_all_vms(client)

    if name_pattern.startswith('~'):
        import re
        if name_pattern[1] == '*':
            pattern = re.compile(name_pattern[2:], re.IGNORECASE)
        else:
            pattern = re.compile(name_pattern[1:])

    for vm in pool.VM:
        if pattern is not None:
            if pattern.match(vm.NAME):
                vms.append(vm)
        elif name_pattern == vm.NAME:
            vms.append(vm)
            break

    # if the specific name is indicated
    if pattern is None and len(vms) == 0:
        module.fail_json(msg="There is no VM with name=" + name_pattern)

    return vms


def get_connection_info(module):

    url = module.params.get('api_url')
    username = module.params.get('api_username')
    password = module.params.get('api_password')

    if not url:
        url = os.environ.get('ONE_URL')

    if not username:
        username = os.environ.get('ONE_USERNAME')

    if not password:
        password = os.environ.get('ONE_PASSWORD')

    if not username:
        if not password:
            authfile = os.environ.get('ONE_AUTH')
            if authfile is None:
                authfile = os.path.join(os.environ.get("HOME"), ".one", "one_auth")
            try:
                authstring = open(authfile, "r").read().rstrip()
                username = authstring.split(":")[0]
                password = authstring.split(":")[1]
            except (OSError, IOError):
                module.fail_json(msg=("Could not find or read ONE_AUTH file at '%s'" % authfile))
            except Exception:
                module.fail_json(msg=("Error occurs when read ONE_AUTH file at '%s'" % authfile))
    if not url:
        module.fail_json(msg="Opennebula API url (api_url) is not specified")
    from collections import namedtuple

    auth_params = namedtuple('auth', ('url', 'username', 'password'))

    return auth_params(url=url, username=username, password=password)


def create_disk_str(client, disk, vm):
    vm_info = client.vm.info(vm.ID)
    disk_str = 'DISK=['
    disk_str += ','.join('{key}="{val}"'.format(key=key, val=val) for key, val in disk.items())
    disk_str += ']'
    return disk_str


def get_disk_by_id(client, vm, disk):
    vm_info = client.vm.info(vm.ID)
    if 'DISK' in vm_info.TEMPLATE:
        if isinstance(vm_info.TEMPLATE['DISK'], list):
            for vm_info_disk in vm_info.TEMPLATE['DISK']:
                if int(vm_info_disk['DISK_ID']) == int(disk['DISK_ID']):
                    return vm_info_disk
        else:
            if int(vm_info.TEMPLATE['DISK']['DISK_ID']) == int(disk['DISK_ID']):
                return vm_info.TEMPLATE['DISK']


def vm_set_disks(module, client, vm, disks, wait_timeout):
    result = dict()
    disk_change = False
    vm_info = client.vm.info(vm.ID)
    for disk in disks:
        # catch context disk ID
        if int(disk['DISK_ID']) == int(vm_info.TEMPLATE['CONTEXT']['DISK_ID']):
            module.fail_json(msg='Disk ID: ' + str(disk['DISK_ID']) + ' is used by CONTEXT and connot be used.')
        vm_disk = get_disk_by_id(client, vm, disk)
        if disk['state'] == 'present':
            if vm_disk:
                if int(disk['SIZE']) < int(vm_disk['SIZE']):
                    module.fail_json(msg="Given disk size at disk ID [%s] is smaller than found (%s < %s)."
                                         " Reducing disks is not allowed." % (disk['DISK_ID'],
                                                                              disk['SIZE'],
                                                                              vm_disk['SIZE']))
                if int(disk['SIZE']) > int(vm_disk['SIZE']):
                    client.vm.diskresize(vm.ID, int(disk['DISK_ID']), str(disk['SIZE']))
                    wait_for_running(module, client, vm, wait_timeout)
                    disk_change = True
                    result[disk['DISK_ID']] = "Disk size increased."
                if int(disk['SIZE']) == int(vm_disk['SIZE']):
                    result[disk['DISK_ID']] = "Disk already exists."
            else:
                disk_str = create_disk_str(client, disk, vm)
                client.vm.attach(vm.ID, disk_str)
                wait_for_running(module, client, vm, wait_timeout)
                disk_change = True
                result[disk['DISK_ID']] = "Disk created."
        elif disk['state'] == 'absent':
            if vm_disk:
                client.vm.detach(vm.ID, disk['DISK_ID'])
                wait_for_running(module, client, vm, wait_timeout)
                disk_change = True
                result[disk['DISK_ID']] = "Disk deleted."
            else:
                result[disk['DISK_ID']] = "Disk not found."
    return disk_change, result


def main():
    fields = {
        "api_url": {"required": False, "type": "str"},
        "api_username": {"required": False, "type": "str"},
        "api_password": {"required": False, "type": "str", "no_log": True},
        "ids": {"required": False, "aliases": ['id'], "type": "list"},
        "name": {"required": False, "type": "str"},
        "disks": {
            "default": "[]",
            "type": "list"
        },
        "wait_timeout": {"default": 300, "type": "int"}
    }

    module = AnsibleModule(argument_spec=fields,
                           mutually_exclusive=[['ids', 'name']],
                           supports_check_mode=True)
    if not HAS_PYONE:
        module.fail_json(msg='This module requires pyone to work!')

    auth = get_connection_info(module)
    params = module.params
    ids = params.get('ids')
    name = params.get('name')
    disks = params.get('disks')
    wait_timeout = params.get('wait_timeout')
    client = pyone.OneServer(auth.url, session=auth.username + ':' + auth.password)

    results = {'vms': []}
    vms = []

    if ids:
        vms = get_vms_by_ids(module, client, ids)
    elif name:
        vms = get_vms_by_name(module, client, name)

    for vm in vms:
        result = dict()
        result = get_vm_info(client, vm)
        results['changed'], result['disk_changes'] = vm_set_disks(module, client, vm, disks, wait_timeout)
        results['vms'].append(result)

    module.exit_json(**results)


if __name__ == '__main__':
    main()
