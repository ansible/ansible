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
      - A list of VM ids whose facts you want to gather.
    aliases: ['id']
  name:
    type: str
    description:
      - A C(name) of the VM whose facts will be gathered.
      - If the C(name) begins with '~' the C(name) will be used as regex pattern
      - which restricts the list of VMs (whose facts will be returned) whose names match specified regex.
      - Also, if the C(name) begins with '~*' case-insensitive matching will be performed.
      - See examples for more details.
author:
    - "Jan Meerkamp (@meerkampdvv)"
'''

EXAMPLES = '''
# Gather facts about all VMs
- one_vm_info:
  register: result

# Print all images facts
- debug:
    var: result

# Gather facts about an VM using ID
- one_vm_info:
    ids:
      - 123

# Gather facts about an VM using the name
- one_vm_info:
    name: 'foo-VM'
  register: foo_VM

# Gather facts about all VMs whose name matches regex 'app-vm-.*'
- one_vm_info:
    name: '~app-vm-.*'
  register: app_vm

# Gather facts about all VMs whose name matches regex 'foo-vm-.*' ignoring cases
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


def get_vm_info(client, vm):
    # get additional info
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
        'state': VM_STATES[vm.STATE],
        'user_name': vm.UNAME,
        'user_id': vm.UID,
        'group_name': vm.GNAME,
        'group_id': vm.GID,
        'lcm_state': LCM_STATES[vm.LCM_STATE],
        'uptime_h': int(vm_uptime),
        'mode': parse_vm_permissions(client, vm),
        'cpu': vm.TEMPLATE['CPU'],
        'vcpu': vm.TEMPLATE['VCPU'],
        'memory': vm.TEMPLATE['MEMORY'] + ' MB',
        'disks': disks,
        'networks': networks_info,
        'labels': vm_labels,
        'attributes': vm_attributes
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


def main():
    fields = {
        "api_url": {"required": False, "type": "str"},
        "api_username": {"required": False, "type": "str"},
        "api_password": {"required": False, "type": "str", "no_log": True},
        "ids": {"required": False, "aliases": ['id'], "type": "list"},
        "name": {"required": False, "type": "str"},
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
    client = pyone.OneServer(auth.url, session=auth.username + ':' + auth.password)

    result = {'vms': []}
    vms = []

    if ids:
        vms = get_vms_by_ids(module, client, ids)
    elif name:
        vms = get_vms_by_name(module, client, name)
    else:
        vms = get_all_vms(client).VM

    for vm in vms:
        result['vms'].append(get_vm_info(client, vm))

    module.exit_json(**result)


if __name__ == '__main__':
    main()
