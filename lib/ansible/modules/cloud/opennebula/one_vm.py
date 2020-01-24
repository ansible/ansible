#!/usr/bin/python
# -*- coding: utf-8 -*-

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

"""
(c) 2017, Milan Ilic <milani@nordeus.com>
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

You should have received a copy of the GNU General Public License
along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
"""

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: one_vm
short_description: Creates or terminates OpenNebula instances
description:
  - Manages OpenNebula instances
version_added: "2.6"
requirements:
  - pyone
options:
  api_url:
    description:
      - URL of the OpenNebula RPC server.
      - It is recommended to use HTTPS so that the username/password are not
      - transferred over the network unencrypted.
      - If not set then the value of the C(ONE_URL) environment variable is used.
  api_username:
    description:
      - Name of the user to login into the OpenNebula RPC server. If not set
      - then the value of the C(ONE_USERNAME) environment variable is used.
  api_password:
    description:
      - Password of the user to login into OpenNebula RPC server. If not set
      - then the value of the C(ONE_PASSWORD) environment variable is used.
      - if both I(api_username) or I(api_password) are not set, then it will try
      - authenticate with ONE auth file. Default path is "~/.one/one_auth".
      - Set environment variable C(ONE_AUTH) to override this path.
  template_name:
    description:
      - Name of VM template to use to create a new instace
  template_id:
    description:
      - ID of a VM template to use to create a new instance
  vm_start_on_hold:
    description:
      - Set to true to put vm on hold while creating
    default: False
    version_added: '2.9'
  instance_ids:
    description:
      - A list of instance ids used for states':' C(absent), C(running), C(rebooted), C(poweredoff)
    aliases: ['ids']
  state:
    description:
      - C(present) - create instances from a template specified with C(template_id)/C(template_name).
      - C(running) - run instances
      - C(poweredoff) - power-off instances
      - C(rebooted) - reboot instances
      - C(absent) - terminate instances
    choices: ["present", "absent", "running", "rebooted", "poweredoff"]
    default: present
  hard:
    description:
      - Reboot, power-off or terminate instances C(hard)
    default: no
    type: bool
  wait:
    description:
      - Wait for the instance to reach its desired state before returning. Keep
      - in mind if you are waiting for instance to be in running state it
      - doesn't mean that you will be able to SSH on that machine only that
      - boot process have started on that instance, see 'wait_for' example for
      - details.
    default: yes
    type: bool
  wait_timeout:
    description:
      - How long before wait gives up, in seconds
    default: 300
  attributes:
    description:
      - A dictionary of key/value attributes to add to new instances, or for
      - setting C(state) of instances with these attributes.
      - Keys are case insensitive and OpenNebula automatically converts them to upper case.
      - Be aware C(NAME) is a special attribute which sets the name of the VM when it's deployed.
      - C(#) character(s) can be appended to the C(NAME) and the module will automatically add
      - indexes to the names of VMs.
      - For example':' C(NAME':' foo-###) would create VMs with names C(foo-000), C(foo-001),...
      - When used with C(count_attributes) and C(exact_count) the module will
      - match the base name without the index part.
    default: {}
  labels:
    description:
      - A list of labels to associate with new instances, or for setting
      - C(state) of instances with these labels.
    default: []
  count_attributes:
    description:
      - A dictionary of key/value attributes that can only be used with
      - C(exact_count) to determine how many nodes based on a specific
      - attributes criteria should be deployed. This can be expressed in
      - multiple ways and is shown in the EXAMPLES section.
  count_labels:
    description:
      - A list of labels that can only be used with C(exact_count) to determine
      - how many nodes based on a specific labels criteria should be deployed.
      - This can be expressed in multiple ways and is shown in the EXAMPLES
      - section.
  count:
    description:
      - Number of instances to launch
    default: 1
  exact_count:
    description:
      - Indicates how many instances that match C(count_attributes) and
      - C(count_labels) parameters should be deployed. Instances are either
      - created or terminated based on this value.
      - NOTE':' Instances with the least IDs will be terminated first.
  mode:
    description:
      - Set permission mode of the instance in octet format, e.g. C(600) to give owner C(use) and C(manage) and nothing to group and others.
  owner_id:
    description:
      - ID of the user which will be set as the owner of the instance
  group_id:
    description:
      - ID of the group which will be set as the group of the instance
  memory:
    description:
      - The size of the memory for new instances (in MB, GB, ...)
  disk_size:
    description:
      - The size of the disk created for new instances (in MB, GB, TB,...).
      - NOTE':' If The Template hats Multiple Disks the Order of the Sizes is
      - matched against the order specified in C(template_id)/C(template_name).
  cpu:
    description:
      - Percentage of CPU divided by 100 required for the new instance. Half a
      - processor is written 0.5.
  vcpu:
    description:
      - Number of CPUs (cores) new VM will have.
  networks:
    description:
      - A list of dictionaries with network parameters. See examples for more details.
    default: []
  disk_saveas:
    description:
      - Creates an image from a VM disk.
      - It is a dictionary where you have to specify C(name) of the new image.
      - Optionally you can specify C(disk_id) of the disk you want to save. By default C(disk_id) is 0.
      - I(NOTE)':' This operation will only be performed on the first VM (if more than one VM ID is passed)
      - and the VM has to be in the C(poweredoff) state.
      - Also this operation will fail if an image with specified C(name) already exists.
  persistent:
    description:
      - Create a private persistent copy of the template plus any image defined in DISK, and instantiate that copy.
    default: NO
    type: bool
    version_added: '2.10'
  datastore_id:
    description:
      - Name of Datastore to use to create a new instace
    version_added: '2.10'
  datastore_name:
    description:
      - Name of Datastore to use to create a new instace
    version_added: '2.10'
author:
    - "Milan Ilic (@ilicmilan)"
    - "Jan Meerkamp (@meerkampdvv)"
'''


EXAMPLES = '''
# Create a new instance
- one_vm:
    template_id: 90
  register: result

# Print VM properties
- debug:
    msg: result

# Deploy a new VM on hold
- one_vm:
    template_name: 'app1_template'
    vm_start_on_hold: 'True'

# Deploy a new VM and set its name to 'foo'
- one_vm:
    template_name: 'app1_template'
    attributes:
      name: foo

# Deploy a new VM and set its group_id and mode
- one_vm:
    template_id: 90
    group_id: 16
    mode: 660

# Deploy a new VM  as persistent
- one_vm:
    template_id: 90
    persistent: yes

# Change VM's permissions to 640
- one_vm:
    instance_ids: 5
    mode: 640

# Deploy 2 new instances and set memory, vcpu, disk_size and 3 networks
- one_vm:
    template_id: 15
    disk_size: 35.2 GB
    memory: 4 GB
    vcpu: 4
    count: 2
    networks:
      - NETWORK_ID: 27
      - NETWORK: "default-network"
        NETWORK_UNAME: "app-user"
        SECURITY_GROUPS: "120,124"
      - NETWORK_ID: 27
        SECURITY_GROUPS: "10"

# Deploy a new instance which uses a Template with two Disks
- one_vm:
    template_id: 42
    disk_size:
      - 35.2 GB
      - 50 GB
    memory: 4 GB
    vcpu: 4
    count: 1
    networks:
      - NETWORK_ID: 27

# Deploy an new instance with attribute 'bar: bar1' and set its name to 'foo'
- one_vm:
    template_id: 53
    attributes:
      name: foo
      bar: bar1

# Enforce that 2 instances with attributes 'foo1: app1' and 'foo2: app2' are deployed
- one_vm:
    template_id: 53
    attributes:
      foo1: app1
      foo2: app2
    exact_count: 2
    count_attributes:
      foo1: app1
      foo2: app2

# Enforce that 4 instances with an attribute 'bar' are deployed
- one_vm:
    template_id: 53
    attributes:
      name: app
      bar: bar2
    exact_count: 4
    count_attributes:
      bar:

# Deploy 2 new instances with attribute 'foo: bar' and labels 'app1' and 'app2' and names in format 'fooapp-##'
# Names will be: fooapp-00 and fooapp-01
- one_vm:
    template_id: 53
    attributes:
      name: fooapp-##
      foo: bar
    labels:
      - app1
      - app2
    count: 2

# Deploy 2 new instances with attribute 'app: app1' and names in format 'fooapp-###'
# Names will be: fooapp-002 and fooapp-003
- one_vm:
    template_id: 53
    attributes:
      name: fooapp-###
      app: app1
    count: 2

# Reboot all instances with name in format 'fooapp-#'
# Instances 'fooapp-00', 'fooapp-01', 'fooapp-002' and 'fooapp-003' will be rebooted
- one_vm:
    attributes:
      name: fooapp-#
    state: rebooted

# Enforce that only 1 instance with name in format 'fooapp-#' is deployed
# The task will delete oldest instances, so only the 'fooapp-003' will remain
- one_vm:
    template_id: 53
    exact_count: 1
    count_attributes:
      name: fooapp-#

# Deploy an new instance with a network
- one_vm:
    template_id: 53
    networks:
      - NETWORK_ID: 27
  register: vm

# Wait for SSH to come up
- wait_for_connection:
  delegate_to: '{{ vm.instances[0].networks[0].ip }}'

# Terminate VMs by ids
- one_vm:
    instance_ids:
      - 153
      - 160
    state: absent

# Reboot all VMs that have labels 'foo' and 'app1'
- one_vm:
    labels:
      - foo
      - app1
    state: rebooted

# Fetch all VMs that have name 'foo' and attribute 'app: bar'
- one_vm:
    attributes:
      name: foo
      app: bar
  register: results

# Deploy 2 new instances with labels 'foo1' and 'foo2'
- one_vm:
    template_name: app_template
    labels:
      - foo1
      - foo2
    count: 2

# Enforce that only 1 instance with label 'foo1' will be running
- one_vm:
    template_name: app_template
    labels:
      - foo1
    exact_count: 1
    count_labels:
      - foo1

# Terminate all instances that have attribute foo
- one_vm:
    template_id: 53
    exact_count: 0
    count_attributes:
      foo:

# Power-off the VM and save VM's disk with id=0 to the image with name 'foo-image'
- one_vm:
    instance_ids: 351
    state: poweredoff
    disk_saveas:
      name: foo-image

# Save VM's disk with id=1 to the image with name 'bar-image'
- one_vm:
    instance_ids: 351
    disk_saveas:
      name: bar-image
      disk_id: 1
'''

RETURN = '''
instances_ids:
    description: a list of instances ids whose state is changed or which are fetched with C(instance_ids) option.
    type: list
    returned: success
    sample: [ 1234, 1235 ]
instances:
    description: a list of instances info whose state is changed or which are fetched with C(instance_ids) option.
    type: complex
    returned: success
    contains:
        vm_id:
            description: vm id
            type: int
            sample: 153
        vm_name:
            description: vm name
            type: str
            sample: foo
        template_id:
            description: vm's template id
            type: int
            sample: 153
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
            sample: app-user
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
        disk_size:
            description: The size of the disk in MB
            type: str
            sample: 20480 MB
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
tagged_instances:
    description:
        - A list of instances info based on a specific attributes and/or
        - labels that are specified with C(count_attributes) and C(count_labels)
        - options.
    type: complex
    returned: success
    contains:
        vm_id:
            description: vm id
            type: int
            sample: 153
        vm_name:
            description: vm name
            type: str
            sample: foo
        template_id:
            description: vm's template id
            type: int
            sample: 153
        group_id:
            description: vm's group id
            type: int
            sample: 1
        group_name:
            description: vm's group name
            type: str
            sample: one-users
        owner_id:
            description: vm's user id
            type: int
            sample: 143
        owner_name:
            description: vm's user name
            type: str
            sample: app-user
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
        disk_size:
            description: The size of the disk in MB
            type: list
            sample: [
                        "20480 MB",
                        "10240 MB"
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


def get_template(module, client, predicate):

    pool = client.templatepool.info(-2, -1, -1, -1)
    # Filter -2 means fetch all templates user can Use
    found = 0
    found_template = None
    template_name = ''

    for template in pool.VMTEMPLATE:
        if predicate(template):
            found = found + 1
            found_template = template
            template_name = template.NAME

    if found == 0:
        return None
    elif found > 1:
        module.fail_json(msg='There are more templates with name: ' + template_name)
    return found_template


def get_template_by_name(module, client, template_name):
    return get_template(module, client, lambda template: (template.NAME == template_name))


def get_template_by_id(module, client, template_id):
    return get_template(module, client, lambda template: (template.ID == template_id))


def get_template_id(module, client, requested_id, requested_name):
    template = get_template_by_id(module, client, requested_id) if requested_id is not None else get_template_by_name(module, client, requested_name)
    if template:
        return template.ID
    else:
        return None


def get_datastore(module, client, predicate):
    pool = client.datastorepool.info()
    found = 0
    found_datastore = None
    datastore_name = ''

    for datastore in pool.DATASTORE:
        if predicate(datastore):
            found = found + 1
            found_datastore = datastore
            datastore_name = datastore.NAME

    if found == 0:
        return None
    elif found > 1:
        module.fail_json(msg='There are more datastores with name: ' + datastore_name)
    return found_datastore


def get_datastore_by_name(module, client, datastore_name):
    return get_datastore(module, client, lambda datastore: (datastore.NAME == datastore_name))


def get_datastore_by_id(module, client, datastore_id):
    return get_datastore(module, client, lambda datastore: (datastore.ID == datastore_id))


def get_datastore_id(module, client, requested_id, requested_name):
    datastore = get_datastore_by_id(module, client, requested_id) if requested_id else get_datastore_by_name(module, client, requested_name)
    if datastore:
        return datastore.ID
    else:
        return None


def get_vm_by_id(client, vm_id):
    try:
        vm = client.vm.info(int(vm_id))
    except BaseException:
        return None
    return vm


def get_vms_by_ids(module, client, state, ids):
    vms = []

    for vm_id in ids:
        vm = get_vm_by_id(client, vm_id)
        if vm is None and state != 'absent':
            module.fail_json(msg='There is no VM with id=' + str(vm_id))
        vms.append(vm)

    return vms


def get_vm_info(client, vm):

    vm = client.vm.info(vm.ID)

    networks_info = []

    disk_size = []
    if 'DISK' in vm.TEMPLATE:
        if isinstance(vm.TEMPLATE['DISK'], list):
            for disk in vm.TEMPLATE['DISK']:
                disk_size.append(disk['SIZE'] + ' MB')
        else:
            disk_size.append(vm.TEMPLATE['DISK']['SIZE'] + ' MB')

    if 'NIC' in vm.TEMPLATE:
        if isinstance(vm.TEMPLATE['NIC'], list):
            for nic in vm.TEMPLATE['NIC']:
                networks_info.append({'ip': nic['IP'], 'mac': nic['MAC'], 'name': nic['NETWORK'], 'security_groups': nic['SECURITY_GROUPS']})
        else:
            networks_info.append(
                {'ip': vm.TEMPLATE['NIC']['IP'], 'mac': vm.TEMPLATE['NIC']['MAC'],
                    'name': vm.TEMPLATE['NIC']['NETWORK'], 'security_groups': vm.TEMPLATE['NIC']['SECURITY_GROUPS']})
    import time

    current_time = time.localtime()
    vm_start_time = time.localtime(vm.STIME)

    vm_uptime = time.mktime(current_time) - time.mktime(vm_start_time)
    vm_uptime /= (60 * 60)

    permissions_str = parse_vm_permissions(client, vm)

    # LCM_STATE is VM's sub-state that is relevant only when STATE is ACTIVE
    vm_lcm_state = None
    if vm.STATE == VM_STATES.index('ACTIVE'):
        vm_lcm_state = LCM_STATES[vm.LCM_STATE]

    vm_labels, vm_attributes = get_vm_labels_and_attributes_dict(client, vm.ID)

    info = {
        'template_id': int(vm.TEMPLATE['TEMPLATE_ID']),
        'vm_id': vm.ID,
        'vm_name': vm.NAME,
        'state': VM_STATES[vm.STATE],
        'lcm_state': vm_lcm_state,
        'owner_name': vm.UNAME,
        'owner_id': vm.UID,
        'networks': networks_info,
        'disk_size': disk_size,
        'memory': vm.TEMPLATE['MEMORY'] + ' MB',
        'vcpu': vm.TEMPLATE['VCPU'],
        'cpu': vm.TEMPLATE['CPU'],
        'group_name': vm.GNAME,
        'group_id': vm.GID,
        'uptime_h': int(vm_uptime),
        'attributes': vm_attributes,
        'mode': permissions_str,
        'labels': vm_labels
    }

    return info


def parse_vm_permissions(client, vm):
    vm_PERMISSIONS = client.vm.info(vm.ID).PERMISSIONS

    owner_octal = int(vm_PERMISSIONS.OWNER_U) * 4 + int(vm_PERMISSIONS.OWNER_M) * 2 + int(vm_PERMISSIONS.OWNER_A)
    group_octal = int(vm_PERMISSIONS.GROUP_U) * 4 + int(vm_PERMISSIONS.GROUP_M) * 2 + int(vm_PERMISSIONS.GROUP_A)
    other_octal = int(vm_PERMISSIONS.OTHER_U) * 4 + int(vm_PERMISSIONS.OTHER_M) * 2 + int(vm_PERMISSIONS.OTHER_A)

    permissions = str(owner_octal) + str(group_octal) + str(other_octal)

    return permissions


def set_vm_permissions(module, client, vms, permissions):
    changed = False

    for vm in vms:
        vm = client.vm.info(vm.ID)
        old_permissions = parse_vm_permissions(client, vm)
        changed = changed or old_permissions != permissions

        if not module.check_mode and old_permissions != permissions:
            permissions_str = bin(int(permissions, base=8))[2:]  # 600 -> 110000000
            mode_bits = [int(d) for d in permissions_str]
            try:
                client.vm.chmod(
                    vm.ID, mode_bits[0], mode_bits[1], mode_bits[2], mode_bits[3], mode_bits[4], mode_bits[5], mode_bits[6], mode_bits[7], mode_bits[8])
            except pyone.OneAuthorizationException:
                module.fail_json(msg="Permissions changing is unsuccessful, but instances are present if you deployed them.")

    return changed


def set_vm_ownership(module, client, vms, owner_id, group_id):
    changed = False

    for vm in vms:
        vm = client.vm.info(vm.ID)
        if owner_id is None:
            owner_id = vm.UID
        if group_id is None:
            group_id = vm.GID

        changed = changed or owner_id != vm.UID or group_id != vm.GID

        if not module.check_mode and (owner_id != vm.UID or group_id != vm.GID):
            try:
                client.vm.chown(vm.ID, owner_id, group_id)
            except pyone.OneAuthorizationException:
                module.fail_json(msg="Ownership changing is unsuccessful, but instances are present if you deployed them.")

    return changed


def get_size_in_MB(module, size_str):

    SYMBOLS = ['B', 'KB', 'MB', 'GB', 'TB']

    s = size_str
    init = size_str
    num = ""
    while s and s[0:1].isdigit() or s[0:1] == '.':
        num += s[0]
        s = s[1:]
    num = float(num)
    symbol = s.strip()

    if symbol not in SYMBOLS:
        module.fail_json(msg="Cannot interpret %r %r %d" % (init, symbol, num))

    prefix = {'B': 1}

    for i, s in enumerate(SYMBOLS[1:]):
        prefix[s] = 1 << (i + 1) * 10

    size_in_bytes = int(num * prefix[symbol])
    size_in_MB = size_in_bytes / (1024 * 1024)

    return size_in_MB


def create_disk_str(module, client, template_id, disk_size_list):

    if not disk_size_list:
        return ''

    template = client.template.info(template_id)
    if isinstance(template.TEMPLATE['DISK'], list):
        # check if the number of disks is correct
        if len(template.TEMPLATE['DISK']) != len(disk_size_list):
            module.fail_json(msg='This template has ' + str(len(template.TEMPLATE['DISK'])) + ' disks but you defined ' + str(len(disk_size_list)))
        result = ''
        index = 0
        for DISKS in template.TEMPLATE['DISK']:
            disk = {}
            diskresult = ''
            # Get all info about existed disk e.g. IMAGE_ID,...
            for key, value in DISKS.items():
                disk[key] = value
            # copy disk attributes if it is not the size attribute
            diskresult += 'DISK = [' + ','.join('{key}="{val}"'.format(key=key, val=val) for key, val in disk.items() if key != 'SIZE')
            # Set the Disk Size
            diskresult += ', SIZE=' + str(int(get_size_in_MB(module, disk_size_list[index]))) + ']\n'
            result += diskresult
            index += 1
    else:
        if len(disk_size_list) > 1:
            module.fail_json(msg='This template has one disk but you defined ' + str(len(disk_size_list)))
        disk = {}
        # Get all info about existed disk e.g. IMAGE_ID,...
        for key, value in template.TEMPLATE['DISK'].items():
            disk[key] = value
        # copy disk attributes if it is not the size attribute
        result = 'DISK = [' + ','.join('{key}="{val}"'.format(key=key, val=val) for key, val in disk.items() if key != 'SIZE')
        # Set the Disk Size
        result += ', SIZE=' + str(int(get_size_in_MB(module, disk_size_list[0]))) + ']\n'

    return result


def create_attributes_str(attributes_dict, labels_list):

    attributes_str = ''

    if labels_list:
        attributes_str += 'LABELS="' + ','.join('{label}'.format(label=label) for label in labels_list) + '"\n'
    if attributes_dict:
        attributes_str += '\n'.join('{key}="{val}"'.format(key=key.upper(), val=val) for key, val in attributes_dict.items()) + '\n'

    return attributes_str


def create_nics_str(network_attrs_list):
    nics_str = ''

    for network in network_attrs_list:
        # Packing key-value dict in string with format key="value", key="value"
        network_str = ','.join('{key}="{val}"'.format(key=key, val=val) for key, val in network.items())
        nics_str = nics_str + 'NIC = [' + network_str + ']\n'

    return nics_str


def create_vm(module, client, template_id, attributes_dict, labels_list, disk_size, network_attrs_list, vm_start_on_hold, vm_persistent):

    if attributes_dict:
        vm_name = attributes_dict.get('NAME', '')

    disk_str = create_disk_str(module, client, template_id, disk_size)
    vm_extra_template_str = create_attributes_str(attributes_dict, labels_list) + create_nics_str(network_attrs_list) + disk_str
    try:
        vm_id = client.template.instantiate(template_id, vm_name, vm_start_on_hold, vm_extra_template_str, vm_persistent)
    except pyone.OneException as e:
        module.fail_json(msg=str(e))
    vm = get_vm_by_id(client, vm_id)

    return get_vm_info(client, vm)


def generate_next_index(vm_filled_indexes_list, num_sign_cnt):
    counter = 0
    cnt_str = str(counter).zfill(num_sign_cnt)

    while cnt_str in vm_filled_indexes_list:
        counter = counter + 1
        cnt_str = str(counter).zfill(num_sign_cnt)

    return cnt_str


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


def get_all_vms_by_attributes(client, attributes_dict, labels_list):
    pool = client.vmpool.info(-2, -1, -1, -1).VM
    vm_list = []
    name = ''
    if attributes_dict:
        name = attributes_dict.pop('NAME', '')

    if name != '':
        base_name = name[:len(name) - name.count('#')]
        # Check does the name have indexed format
        with_hash = name.endswith('#')

        for vm in pool:
            if vm.NAME.startswith(base_name):
                if with_hash and vm.NAME[len(base_name):].isdigit():
                    # If the name has indexed format and after base_name it has only digits it'll be matched
                    vm_list.append(vm)
                elif not with_hash and vm.NAME == name:
                    # If the name is not indexed it has to be same
                    vm_list.append(vm)
        pool = vm_list

    import copy

    vm_list = copy.copy(pool)

    for vm in pool:
        remove_list = []
        vm_labels_list, vm_attributes_dict = get_vm_labels_and_attributes_dict(client, vm.ID)

        if attributes_dict and len(attributes_dict) > 0:
            for key, val in attributes_dict.items():
                if key in vm_attributes_dict:
                    if val and vm_attributes_dict[key] != val:
                        remove_list.append(vm)
                        break
                else:
                    remove_list.append(vm)
                    break
        vm_list = list(set(vm_list).difference(set(remove_list)))

        remove_list = []
        if labels_list and len(labels_list) > 0:
            for label in labels_list:
                if label not in vm_labels_list:
                    remove_list.append(vm)
                    break
        vm_list = list(set(vm_list).difference(set(remove_list)))

    return vm_list


def create_count_of_vms(
        module, client, template_id, count, attributes_dict, labels_list, disk_size, network_attrs_list, wait, wait_timeout, vm_start_on_hold, vm_persistent):
    new_vms_list = []

    vm_name = ''
    if attributes_dict:
        vm_name = attributes_dict.get('NAME', '')

    if module.check_mode:
        return True, [], []

    # Create list of used indexes
    vm_filled_indexes_list = None
    num_sign_cnt = vm_name.count('#')
    if vm_name != '' and num_sign_cnt > 0:
        vm_list = get_all_vms_by_attributes(client, {'NAME': vm_name}, None)
        base_name = vm_name[:len(vm_name) - num_sign_cnt]
        vm_name = base_name
        # Make list which contains used indexes in format ['000', '001',...]
        vm_filled_indexes_list = list((vm.NAME[len(base_name):].zfill(num_sign_cnt)) for vm in vm_list)

    while count > 0:
        new_vm_name = vm_name
        # Create indexed name
        if vm_filled_indexes_list is not None:
            next_index = generate_next_index(vm_filled_indexes_list, num_sign_cnt)
            vm_filled_indexes_list.append(next_index)
            new_vm_name += next_index
        # Update NAME value in the attributes in case there is index
        attributes_dict['NAME'] = new_vm_name
        new_vm_dict = create_vm(module, client, template_id, attributes_dict, labels_list, disk_size, network_attrs_list, vm_start_on_hold, vm_persistent)
        new_vm_id = new_vm_dict.get('vm_id')
        new_vm = get_vm_by_id(client, new_vm_id)
        new_vms_list.append(new_vm)
        count -= 1

    if vm_start_on_hold:
        if wait:
            for vm in new_vms_list:
                wait_for_hold(module, client, vm, wait_timeout)
    else:
        if wait:
            for vm in new_vms_list:
                wait_for_running(module, client, vm, wait_timeout)

    return True, new_vms_list, []


def create_exact_count_of_vms(module, client, template_id, exact_count, attributes_dict, count_attributes_dict,
                              labels_list, count_labels_list, disk_size, network_attrs_list, hard, wait, wait_timeout, vm_start_on_hold, vm_persistent):

    vm_list = get_all_vms_by_attributes(client, count_attributes_dict, count_labels_list)

    vm_count_diff = exact_count - len(vm_list)
    changed = vm_count_diff != 0

    new_vms_list = []
    instances_list = []
    tagged_instances_list = vm_list

    if module.check_mode:
        return changed, instances_list, tagged_instances_list

    if vm_count_diff > 0:
        # Add more VMs
        changed, instances_list, tagged_instances = create_count_of_vms(module, client, template_id, vm_count_diff, attributes_dict,
                                                                        labels_list, disk_size, network_attrs_list, wait, wait_timeout,
                                                                        vm_start_on_hold, vm_persistent)

        tagged_instances_list += instances_list
    elif vm_count_diff < 0:
        # Delete surplus VMs
        old_vms_list = []

        while vm_count_diff < 0:
            old_vm = vm_list.pop(0)
            old_vms_list.append(old_vm)
            terminate_vm(module, client, old_vm, hard)
            vm_count_diff += 1

        if wait:
            for vm in old_vms_list:
                wait_for_done(module, client, vm, wait_timeout)

        instances_list = old_vms_list
        # store only the remaining instances
        old_vms_set = set(old_vms_list)
        tagged_instances_list = [vm for vm in vm_list if vm not in old_vms_set]

    return changed, instances_list, tagged_instances_list


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


def wait_for_done(module, client, vm, wait_timeout):
    return wait_for_state(module, client, vm, wait_timeout, lambda state, lcm_state: (state in [VM_STATES.index('DONE')]))


def wait_for_hold(module, client, vm, wait_timeout):
    return wait_for_state(module, client, vm, wait_timeout, lambda state, lcm_state: (state in [VM_STATES.index('HOLD')]))


def wait_for_poweroff(module, client, vm, wait_timeout):
    return wait_for_state(module, client, vm, wait_timeout, lambda state, lcm_state: (state in [VM_STATES.index('POWEROFF')]))


def terminate_vm(module, client, vm, hard=False):
    changed = False

    if not vm:
        return changed

    changed = True

    if not module.check_mode:
        if hard:
            client.vm.action('terminate-hard', vm.ID)
        else:
            client.vm.action('terminate', vm.ID)

    return changed


def terminate_vms(module, client, vms, hard):
    changed = False

    for vm in vms:
        changed = terminate_vm(module, client, vm, hard) or changed

    return changed


def poweroff_vm(module, client, vm, hard):
    vm = client.vm.info(vm.ID)
    changed = False

    lcm_state = vm.LCM_STATE
    state = vm.STATE

    if lcm_state not in [LCM_STATES.index('SHUTDOWN'), LCM_STATES.index('SHUTDOWN_POWEROFF')] and state not in [VM_STATES.index('POWEROFF')]:
        changed = True

    if changed and not module.check_mode:
        if not hard:
            client.vm.action('poweroff', vm.ID)
        else:
            client.vm.action('poweroff-hard', vm.ID)

    return changed


def poweroff_vms(module, client, vms, hard):
    changed = False

    for vm in vms:
        changed = poweroff_vm(module, client, vm, hard) or changed

    return changed


def reboot_vms(module, client, vms, wait_timeout, hard):

    if not module.check_mode:
        # Firstly, power-off all instances
        for vm in vms:
            vm = client.vm.info(vm.ID)
            lcm_state = vm.LCM_STATE
            state = vm.STATE
            if lcm_state not in [LCM_STATES.index('SHUTDOWN_POWEROFF')] and state not in [VM_STATES.index('POWEROFF')]:
                poweroff_vm(module, client, vm, hard)

        # Wait for all to be power-off
        for vm in vms:
            wait_for_poweroff(module, client, vm, wait_timeout)

        for vm in vms:
            resume_vm(module, client, vm)

    return True


def resume_vm(module, client, vm):
    vm = client.vm.info(vm.ID)
    changed = False

    lcm_state = vm.LCM_STATE
    if lcm_state == LCM_STATES.index('SHUTDOWN_POWEROFF'):
        module.fail_json(msg="Cannot perform action 'resume' because this action is not available " +
                         "for LCM_STATE: 'SHUTDOWN_POWEROFF'. Wait for the VM to shutdown properly")
    if lcm_state not in [LCM_STATES.index('RUNNING')]:
        changed = True

    if changed and not module.check_mode:
        client.vm.action('resume', vm.ID)

    return changed


def resume_vms(module, client, vms):
    changed = False

    for vm in vms:
        changed = resume_vm(module, client, vm) or changed

    return changed


def check_name_attribute(module, attributes):
    if attributes.get("NAME"):
        import re
        if re.match(r'^[^#]+#*$', attributes.get("NAME")) is None:
            module.fail_json(msg="Ilegal 'NAME' attribute: '" + attributes.get("NAME") +
                             "' .Signs '#' are allowed only at the end of the name and the name cannot contain only '#'.")


TEMPLATE_RESTRICTED_ATTRIBUTES = ["CPU", "VCPU", "OS", "FEATURES", "MEMORY", "DISK", "NIC", "INPUT", "GRAPHICS",
                                  "CONTEXT", "CREATED_BY", "CPU_COST", "DISK_COST", "MEMORY_COST",
                                  "TEMPLATE_ID", "VMID", "AUTOMATIC_DS_REQUIREMENTS", "DEPLOY_FOLDER", "LABELS"]


def check_attributes(module, attributes):
    for key in attributes.keys():
        if key in TEMPLATE_RESTRICTED_ATTRIBUTES:
            module.fail_json(msg='Restricted attribute `' + key + '` cannot be used when filtering VMs.')
    # Check the format of the name attribute
    check_name_attribute(module, attributes)


def disk_save_as(module, client, vm, disk_saveas, wait_timeout):
    if not disk_saveas.get('name'):
        module.fail_json(msg="Key 'name' is required for 'disk_saveas' option")

    image_name = disk_saveas.get('name')
    disk_id = disk_saveas.get('disk_id', 0)

    if not module.check_mode:
        if vm.STATE != VM_STATES.index('POWEROFF'):
            module.fail_json(msg="'disksaveas' option can be used only when the VM is in 'POWEROFF' state")
        try:
            client.vm.disksaveas(vm.ID, disk_id, image_name, 'OS', -1)
        except pyone.OneException as e:
            module.fail_json(msg=str(e))
        wait_for_poweroff(module, client, vm, wait_timeout)  # wait for VM to leave the hotplug_saveas_poweroff state


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
                with open(authfile, "r") as fp:
                    authstring = fp.read().rstrip()
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
        "instance_ids": {"required": False, "aliases": ['ids'], "type": "list"},
        "template_name": {"required": False, "type": "str"},
        "template_id": {"required": False, "type": "int"},
        "vm_start_on_hold": {"default": False, "type": "bool"},
        "state": {
            "default": "present",
            "choices": ['present', 'absent', 'rebooted', 'poweredoff', 'running'],
            "type": "str"
        },
        "mode": {"required": False, "type": "str"},
        "owner_id": {"required": False, "type": "int"},
        "group_id": {"required": False, "type": "int"},
        "wait": {"default": True, "type": "bool"},
        "wait_timeout": {"default": 300, "type": "int"},
        "hard": {"default": False, "type": "bool"},
        "memory": {"required": False, "type": "str"},
        "cpu": {"required": False, "type": "float"},
        "vcpu": {"required": False, "type": "int"},
        "disk_size": {"required": False, "type": "list"},
        "datastore_name": {"required": False, "type": "str"},
        "datastore_id": {"required": False, "type": "int"},
        "networks": {"default": [], "type": "list"},
        "count": {"default": 1, "type": "int"},
        "exact_count": {"required": False, "type": "int"},
        "attributes": {"default": {}, "type": "dict"},
        "count_attributes": {"required": False, "type": "dict"},
        "labels": {"default": [], "type": "list"},
        "count_labels": {"required": False, "type": "list"},
        "disk_saveas": {"type": "dict"},
        "persistent": {"default": False, "type": "bool"}
    }

    module = AnsibleModule(argument_spec=fields,
                           mutually_exclusive=[
                               ['template_id', 'template_name', 'instance_ids'],
                               ['template_id', 'template_name', 'disk_saveas'],
                               ['instance_ids', 'count_attributes', 'count'],
                               ['instance_ids', 'count_labels', 'count'],
                               ['instance_ids', 'exact_count'],
                               ['instance_ids', 'attributes'],
                               ['instance_ids', 'labels'],
                               ['disk_saveas', 'attributes'],
                               ['disk_saveas', 'labels'],
                               ['exact_count', 'count'],
                               ['count', 'hard'],
                               ['instance_ids', 'cpu'], ['instance_ids', 'vcpu'],
                               ['instance_ids', 'memory'], ['instance_ids', 'disk_size'],
                               ['instance_ids', 'networks'],
                               ['persistent', 'disk_size']
                           ],
                           supports_check_mode=True)

    if not HAS_PYONE:
        module.fail_json(msg='This module requires pyone to work!')

    auth = get_connection_info(module)
    params = module.params
    instance_ids = params.get('instance_ids')
    requested_template_name = params.get('template_name')
    requested_template_id = params.get('template_id')
    put_vm_on_hold = params.get('vm_start_on_hold')
    state = params.get('state')
    permissions = params.get('mode')
    owner_id = params.get('owner_id')
    group_id = params.get('group_id')
    wait = params.get('wait')
    wait_timeout = params.get('wait_timeout')
    hard = params.get('hard')
    memory = params.get('memory')
    cpu = params.get('cpu')
    vcpu = params.get('vcpu')
    disk_size = params.get('disk_size')
    requested_datastore_id = params.get('datastore_id')
    requested_datastore_name = params.get('datastore_name')
    networks = params.get('networks')
    count = params.get('count')
    exact_count = params.get('exact_count')
    attributes = params.get('attributes')
    count_attributes = params.get('count_attributes')
    labels = params.get('labels')
    count_labels = params.get('count_labels')
    disk_saveas = params.get('disk_saveas')
    persistent = params.get('persistent')

    if not (auth.username and auth.password):
        module.warn("Credentials missing")
    else:
        one_client = pyone.OneServer(auth.url, session=auth.username + ':' + auth.password)

    if attributes:
        attributes = dict((key.upper(), value) for key, value in attributes.items())
        check_attributes(module, attributes)

    if count_attributes:
        count_attributes = dict((key.upper(), value) for key, value in count_attributes.items())
        if not attributes:
            import copy
            module.warn('When you pass `count_attributes` without `attributes` option when deploying, `attributes` option will have same values implicitly.')
            attributes = copy.copy(count_attributes)
        check_attributes(module, count_attributes)

    if count_labels and not labels:
        module.warn('When you pass `count_labels` without `labels` option when deploying, `labels` option will have same values implicitly.')
        labels = count_labels

    # Fetch template
    template_id = None
    if requested_template_id is not None or requested_template_name:
        template_id = get_template_id(module, one_client, requested_template_id, requested_template_name)
        if template_id is None:
            if requested_template_id is not None:
                module.fail_json(msg='There is no template with template_id: ' + str(requested_template_id))
            elif requested_template_name:
                module.fail_json(msg="There is no template with name: " + requested_template_name)

    # Fetch datastore
    datastore_id = None
    if requested_datastore_id or requested_datastore_name:
        datastore_id = get_datastore_id(module, one_client, requested_datastore_id, requested_datastore_name)
        if datastore_id is None:
            if requested_datastore_id:
                module.fail_json(msg='There is no datastore with datastore_id: ' + str(requested_datastore_id))
            elif requested_datastore_name:
                module.fail_json(msg="There is no datastore with name: " + requested_datastore_name)
        else:
            attributes['SCHED_DS_REQUIREMENTS'] = 'ID=' + str(datastore_id)

    if exact_count and template_id is None:
        module.fail_json(msg='Option `exact_count` needs template_id or template_name')

    if exact_count is not None and not (count_attributes or count_labels):
        module.fail_json(msg='Either `count_attributes` or `count_labels` has to be specified with option `exact_count`.')
    if (count_attributes or count_labels) and exact_count is None:
        module.fail_json(msg='Option `exact_count` has to be specified when either `count_attributes` or `count_labels` is used.')
    if template_id is not None and state != 'present':
        module.fail_json(msg="Only state 'present' is valid for the template")

    if memory:
        attributes['MEMORY'] = str(int(get_size_in_MB(module, memory)))
    if cpu:
        attributes['CPU'] = str(cpu)
    if vcpu:
        attributes['VCPU'] = str(vcpu)

    if exact_count is not None and state != 'present':
        module.fail_json(msg='The `exact_count` option is valid only for the `present` state')
    if exact_count is not None and exact_count < 0:
        module.fail_json(msg='`exact_count` cannot be less than 0')
    if count <= 0:
        module.fail_json(msg='`count` has to be greater than 0')

    if permissions is not None:
        import re
        if re.match("^[0-7]{3}$", permissions) is None:
            module.fail_json(msg="Option `mode` has to have exactly 3 digits and be in the octet format e.g. 600")

    if exact_count is not None:
        # Deploy an exact count of VMs
        changed, instances_list, tagged_instances_list = create_exact_count_of_vms(module, one_client, template_id, exact_count, attributes,
                                                                                   count_attributes, labels, count_labels, disk_size,
                                                                                   networks, hard, wait, wait_timeout, put_vm_on_hold, persistent)
        vms = tagged_instances_list
    elif template_id is not None and state == 'present':
        # Deploy count VMs
        changed, instances_list, tagged_instances_list = create_count_of_vms(module, one_client, template_id, count,
                                                                             attributes, labels, disk_size, networks, wait, wait_timeout,
                                                                             put_vm_on_hold, persistent)
        # instances_list - new instances
        # tagged_instances_list - all instances with specified `count_attributes` and `count_labels`
        vms = instances_list
    else:
        # Fetch data of instances, or change their state
        if not (instance_ids or attributes or labels):
            module.fail_json(msg="At least one of `instance_ids`,`attributes`,`labels` must be passed!")

        if memory or cpu or vcpu or disk_size or networks:
            module.fail_json(msg="Parameters as `memory`, `cpu`, `vcpu`, `disk_size` and `networks` you can only set when deploying a VM!")

        if hard and state not in ['rebooted', 'poweredoff', 'absent', 'present']:
            module.fail_json(msg="The 'hard' option can be used only for one of these states: 'rebooted', 'poweredoff', 'absent' and 'present'")

        vms = []
        tagged = False
        changed = False

        if instance_ids:
            vms = get_vms_by_ids(module, one_client, state, instance_ids)
        else:
            tagged = True
            vms = get_all_vms_by_attributes(one_client, attributes, labels)

        if len(vms) == 0 and state != 'absent' and state != 'present':
            module.fail_json(msg='There are no instances with specified `instance_ids`, `attributes` and/or `labels`')

        if len(vms) == 0 and state == 'present' and not tagged:
            module.fail_json(msg='There are no instances with specified `instance_ids`.')

        if tagged and state == 'absent':
            module.fail_json(msg='Option `instance_ids` is required when state is `absent`.')

        if state == 'absent':
            changed = terminate_vms(module, one_client, vms, hard)
        elif state == 'rebooted':
            changed = reboot_vms(module, one_client, vms, wait_timeout, hard)
        elif state == 'poweredoff':
            changed = poweroff_vms(module, one_client, vms, hard)
        elif state == 'running':
            changed = resume_vms(module, one_client, vms)

        instances_list = vms
        tagged_instances_list = []

    if permissions is not None:
        changed = set_vm_permissions(module, one_client, vms, permissions) or changed

    if owner_id is not None or group_id is not None:
        changed = set_vm_ownership(module, one_client, vms, owner_id, group_id) or changed

    if wait and not module.check_mode and state != 'present':
        wait_for = {
            'absent': wait_for_done,
            'rebooted': wait_for_running,
            'poweredoff': wait_for_poweroff,
            'running': wait_for_running
        }
        for vm in vms:
            if vm is not None:
                wait_for[state](module, one_client, vm, wait_timeout)

    if disk_saveas is not None:
        if len(vms) == 0:
            module.fail_json(msg="There is no VM whose disk will be saved.")
        disk_save_as(module, one_client, vms[0], disk_saveas, wait_timeout)
        changed = True

    # instances - a list of instances info whose state is changed or which are fetched with C(instance_ids) option
    instances = list(get_vm_info(one_client, vm) for vm in instances_list if vm is not None)
    instances_ids = list(vm.ID for vm in instances_list if vm is not None)
    # tagged_instances - A list of instances info based on a specific attributes and/or labels that are specified with C(count_attributes) and C(count_labels)
    tagged_instances = list(get_vm_info(one_client, vm) for vm in tagged_instances_list if vm is not None)

    result = {'changed': changed, 'instances': instances, 'instances_ids': instances_ids, 'tagged_instances': tagged_instances}

    module.exit_json(**result)


if __name__ == '__main__':
    main()
