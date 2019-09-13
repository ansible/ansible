#!/usr/bin/python
# -*- coding: utf-8 -*-

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

"""
(c) 2017, Milan Ilic <milani@nordeus.com>

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
  - python-oca
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
      - NOTE':' This option can be used only if the VM template specified with
      - C(template_id)/C(template_name) has exactly one disk.
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
author:
    - "Milan Ilic (@ilicmilan)"
'''


EXAMPLES = '''
# Create a new instance
- one_vm:
    template_id: 90
  register: result

# Print VM properties
- debug:
    msg: result

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
    state: powered-off
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
'''


try:
    import oca
    HAS_OCA = True
except ImportError:
    HAS_OCA = False

from ansible.module_utils.basic import AnsibleModule
import os


def get_template(module, client, predicate):
    pool = oca.VmTemplatePool(client)
    # Filter -2 means fetch all templates user can Use
    pool.info(filter=-2)
    found = 0
    found_template = None
    template_name = ''

    for template in pool:
        if predicate(template):
            found = found + 1
            found_template = template
            template_name = template.name

    if found == 0:
        return None
    elif found > 1:
        module.fail_json(msg='There are more templates with name: ' + template_name)
    return found_template


def get_template_by_name(module, client, template_name):
    return get_template(module, client, lambda template: (template.name == template_name))


def get_template_by_id(module, client, template_id):
    return get_template(module, client, lambda template: (template.id == template_id))


def get_template_id(module, client, requested_id, requested_name):
    template = get_template_by_id(module, client, requested_id) if requested_id else get_template_by_name(module, client, requested_name)
    if template:
        return template.id
    else:
        return None


def get_vm_by_id(client, vm_id):
    pool = oca.VirtualMachinePool(client)
    # Retrieves information for all or part of the vms pool
    # -4: Vms belonging to the user's primary group
    # -3: Vms belonging to the user
    # -2: All vms user can Use
    # -1: Vms belonging to the user and any of his groups - default
    # >= 0: UID User's vms
    pool.info(filter=-2, range_start=int(vm_id), range_end=int(vm_id))

    if len(pool) == 1:
        return pool[0]
    else:
        return None


def get_vms_by_ids(module, client, state, ids):
    vms = []

    for vm_id in ids:
        vm = get_vm_by_id(client, vm_id)
        if vm is None and state != 'absent':
            module.fail_json(msg='There is no VM with id=' + str(vm_id))
        vms.append(vm)

    return vms


def get_vm_info(client, vm):
    vm.info()

    networks_info = []

    disk_size = ''
    if hasattr(vm.template, 'disks'):
        disk_size = vm.template.disks[0].size + ' MB'

    if hasattr(vm.template, 'nics'):
        for nic in vm.template.nics:
            networks_info.append({'ip': nic.ip, 'mac': nic.mac, 'name': nic.network, 'security_groups': nic.security_groups})
    import time

    current_time = time.localtime()
    vm_start_time = time.localtime(vm.stime)

    vm_uptime = time.mktime(current_time) - time.mktime(vm_start_time)
    vm_uptime /= (60 * 60)

    permissions_str = parse_vm_permissions(client, vm)

    # LCM_STATE is VM's sub-state that is relevant only when STATE is ACTIVE
    vm_lcm_state = None
    if vm.state == VM_STATES.index('ACTIVE'):
        vm_lcm_state = LCM_STATES[vm.lcm_state]

    vm_labels, vm_attributes = get_vm_labels_and_attributes_dict(client, vm.id)
    info = {
        'template_id': int(vm.template.template_id),
        'vm_id': vm.id,
        'vm_name': vm.name,
        'state': VM_STATES[vm.state],
        'lcm_state': vm_lcm_state,
        'owner_name': vm.uname,
        'owner_id': vm.uid,
        'networks': networks_info,
        'disk_size': disk_size,
        'memory': vm.template.memory + ' MB',
        'vcpu': vm.template.vcpu,
        'cpu': vm.template.cpu,
        'group_name': vm.gname,
        'group_id': vm.gid,
        'uptime_h': int(vm_uptime),
        'attributes': vm_attributes,
        'mode': permissions_str,
        'labels': vm_labels
    }

    return info


def parse_vm_permissions(client, vm):

    import xml.etree.ElementTree as ET
    vm_XML = client.call('vm.info', vm.id)
    root = ET.fromstring(vm_XML)

    perm_dict = {}

    root = root.find('PERMISSIONS')

    for child in root:
        perm_dict[child.tag] = child.text

    '''
    This is the structure of the 'PERMISSIONS' dictionary:

   "PERMISSIONS": {
                      "OWNER_U": "1",
                      "OWNER_M": "1",
                      "OWNER_A": "0",
                      "GROUP_U": "0",
                      "GROUP_M": "0",
                      "GROUP_A": "0",
                      "OTHER_U": "0",
                      "OTHER_M": "0",
                      "OTHER_A": "0"
                    }
    '''

    owner_octal = int(perm_dict["OWNER_U"]) * 4 + int(perm_dict["OWNER_M"]) * 2 + int(perm_dict["OWNER_A"])
    group_octal = int(perm_dict["GROUP_U"]) * 4 + int(perm_dict["GROUP_M"]) * 2 + int(perm_dict["GROUP_A"])
    other_octal = int(perm_dict["OTHER_U"]) * 4 + int(perm_dict["OTHER_M"]) * 2 + int(perm_dict["OTHER_A"])

    permissions = str(owner_octal) + str(group_octal) + str(other_octal)

    return permissions


def set_vm_permissions(module, client, vms, permissions):
    changed = False

    for vm in vms:
        vm.info()
        print(vm.id)
        old_permissions = parse_vm_permissions(client, vm)
        changed = changed or old_permissions != permissions

        if not module.check_mode and old_permissions != permissions:
            permissions_str = bin(int(permissions, base=8))[2:]  # 600 -> 110000000
            mode_bits = [int(d) for d in permissions_str]
            try:
                client.call('vm.chmod', vm.id, mode_bits[0], mode_bits[1], mode_bits[2], mode_bits[3],
                            mode_bits[4], mode_bits[5], mode_bits[6], mode_bits[7], mode_bits[8])
            except oca.OpenNebulaException:
                module.fail_json(msg="Permissions changing is unsuccessful, but instances are present if you deployed them.")

    return changed


def set_vm_ownership(module, client, vms, owner_id, group_id):
    changed = False

    for vm in vms:
        vm.info()
        if owner_id is None:
            owner_id = vm.uid
        if group_id is None:
            group_id = vm.gid

        changed = changed or owner_id != vm.uid or group_id != vm.gid

        if not module.check_mode and (owner_id != vm.uid or group_id != vm.gid):
            try:
                client.call('vm.chown', vm.id, owner_id, group_id)
            except oca.OpenNebulaException:
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


def create_disk_str(module, client, template_id, disk_size_str):

    if not disk_size_str:
        return ''

    import xml.etree.ElementTree as ET

    template_XML = client.call('template.info', template_id)
    root = ET.fromstring(template_XML)

    disks_num = 0
    disk = None

    for child in root.find('TEMPLATE').findall('DISK'):
        disks_num += 1
        root = child

    if disks_num != 1:
        module.fail_json(msg='You can pass disk_size only if template has exact one disk. This template has ' + str(disks_num) + ' disks.')

    disk = {}
    # Get all info about existed disk e.g. IMAGE_ID,...
    for child in root:
        disk[child.tag] = child.text

    result = 'DISK = [' + ','.join('{key}="{val}"'.format(key=key, val=val) for key, val in disk.items() if key != 'SIZE')
    result += ', SIZE=' + str(int(get_size_in_MB(module, disk_size_str))) + ']\n'

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


def create_vm(module, client, template_id, attributes_dict, labels_list, disk_size, network_attrs_list):

    if attributes_dict:
        vm_name = attributes_dict.get('NAME', '')

    disk_str = create_disk_str(module, client, template_id, disk_size)
    vm_extra_template_str = create_attributes_str(attributes_dict, labels_list) + create_nics_str(network_attrs_list) + disk_str
    vm_id = client.call('template.instantiate', template_id, vm_name, False, vm_extra_template_str)
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
    import xml.etree.ElementTree as ET
    vm_XML = client.call('vm.info', vm_id)
    root = ET.fromstring(vm_XML)

    attrs_dict = {}
    labels_list = []

    root = root.find('USER_TEMPLATE')

    for child in root:
        if child.tag != 'LABELS':
            attrs_dict[child.tag] = child.text
        else:
            if child.text is not None:
                labels_list = child.text.split(',')

    return labels_list, attrs_dict


def get_all_vms_by_attributes(client, attributes_dict, labels_list):
    pool = oca.VirtualMachinePool(client)
    # Retrieves information for all or part of the vms pool
    # -4: Vms belonging to the user's primary group
    # -3: Vms belonging to the user
    # -2: All vms user can Use
    # -1: Vms belonging to the user and any of his groups - default
    # >= 0: UID User's vms
    pool.info(filter=-2)
    vm_list = []
    name = ''
    if attributes_dict:
        name = attributes_dict.pop('NAME', '')

    if name != '':
        base_name = name[:len(name) - name.count('#')]
        # Check does the name have indexed format
        with_hash = name.endswith('#')

        for vm in pool:
            if vm.name.startswith(base_name):
                if with_hash and vm.name[len(base_name):].isdigit():
                    # If the name has indexed format and after base_name it has only digits it'll be matched
                    vm_list.append(vm)
                elif not with_hash and vm.name == name:
                    # If the name is not indexed it has to be same
                    vm_list.append(vm)
        pool = vm_list

    import copy

    vm_list = copy.copy(pool)

    for vm in pool:
        vm_labels_list, vm_attributes_dict = get_vm_labels_and_attributes_dict(client, vm.id)

        if attributes_dict and len(attributes_dict) > 0:
            for key, val in attributes_dict.items():
                if key in vm_attributes_dict:
                    if val and vm_attributes_dict[key] != val and vm in vm_list:
                        vm_list.remove(vm)
                        break
                else:
                    if vm in vm_list:
                        vm_list.remove(vm)
                    break
        if labels_list and len(labels_list) > 0:
            for label in labels_list:
                if label not in vm_labels_list and vm in vm_list:
                    vm_list.remove(vm)
                    break

    return vm_list


def create_count_of_vms(module, client, template_id, count, attributes_dict, labels_list, disk_size, network_attrs_list, wait, wait_timeout):
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
        vm_filled_indexes_list = list((vm.name[len(base_name):].zfill(num_sign_cnt)) for vm in vm_list)

    while count > 0:
        new_vm_name = vm_name
        # Create indexed name
        if vm_filled_indexes_list is not None:
            next_index = generate_next_index(vm_filled_indexes_list, num_sign_cnt)
            vm_filled_indexes_list.append(next_index)
            new_vm_name += next_index
        # Update NAME value in the attributes in case there is index
        attributes_dict['NAME'] = new_vm_name
        new_vm_dict = create_vm(module, client, template_id, attributes_dict, labels_list, disk_size, network_attrs_list)
        new_vm_id = new_vm_dict.get('vm_id')
        new_vm = get_vm_by_id(client, new_vm_id)
        new_vms_list.append(new_vm)
        count -= 1

    if wait:
        for vm in new_vms_list:
            wait_for_running(module, vm, wait_timeout)

    return True, new_vms_list, []


def create_exact_count_of_vms(module, client, template_id, exact_count, attributes_dict, count_attributes_dict,
                              labels_list, count_labels_list, disk_size, network_attrs_list, hard, wait, wait_timeout):

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
                                                                        labels_list, disk_size, network_attrs_list, wait, wait_timeout)

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
                wait_for_done(module, vm, wait_timeout)

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


def wait_for_state(module, vm, wait_timeout, state_predicate):
    import time
    start_time = time.time()

    while (time.time() - start_time) < wait_timeout:
        vm.info()
        state = vm.state
        lcm_state = vm.lcm_state

        if state_predicate(state, lcm_state):
            return vm
        elif state not in [VM_STATES.index('INIT'), VM_STATES.index('PENDING'), VM_STATES.index('HOLD'),
                           VM_STATES.index('ACTIVE'), VM_STATES.index('POWEROFF')]:
            module.fail_json(msg='Action is unsuccessful. VM state: ' + VM_STATES[state])

        time.sleep(1)

    module.fail_json(msg="Wait timeout has expired!")


def wait_for_running(module, vm, wait_timeout):
    return wait_for_state(module, vm, wait_timeout, lambda state,
                          lcm_state: (state in [VM_STATES.index('ACTIVE')] and lcm_state in [LCM_STATES.index('RUNNING')]))


def wait_for_done(module, vm, wait_timeout):
    return wait_for_state(module, vm, wait_timeout, lambda state, lcm_state: (state in [VM_STATES.index('DONE')]))


def wait_for_poweroff(module, vm, wait_timeout):
    return wait_for_state(module, vm, wait_timeout, lambda state, lcm_state: (state in [VM_STATES.index('POWEROFF')]))


def terminate_vm(module, client, vm, hard=False):
    changed = False

    if not vm:
        return changed

    changed = True

    if not module.check_mode:
        if hard:
            client.call('vm.action', 'terminate-hard', vm.id)
        else:
            client.call('vm.action', 'terminate', vm.id)

    return changed


def terminate_vms(module, client, vms, hard):
    changed = False

    for vm in vms:
        changed = terminate_vm(module, client, vm, hard) or changed

    return changed


def poweroff_vm(module, vm, hard):
    vm.info()
    changed = False

    lcm_state = vm.lcm_state
    state = vm.state

    if lcm_state not in [LCM_STATES.index('SHUTDOWN'), LCM_STATES.index('SHUTDOWN_POWEROFF')] and state not in [VM_STATES.index('POWEROFF')]:
        changed = True

    if changed and not module.check_mode:
        if not hard:
            vm.poweroff()
        else:
            vm.poweroff_hard()

    return changed


def poweroff_vms(module, client, vms, hard):
    changed = False

    for vm in vms:
        changed = poweroff_vm(module, vm, hard) or changed

    return changed


def reboot_vms(module, client, vms, wait_timeout, hard):

    if not module.check_mode:
        # Firstly, power-off all instances
        for vm in vms:
            vm.info()
            lcm_state = vm.lcm_state
            state = vm.state
            if lcm_state not in [LCM_STATES.index('SHUTDOWN_POWEROFF')] and state not in [VM_STATES.index('POWEROFF')]:
                poweroff_vm(module, vm, hard)

        # Wait for all to be power-off
        for vm in vms:
            wait_for_poweroff(module, vm, wait_timeout)

        for vm in vms:
            resume_vm(module, vm)

    return True


def resume_vm(module, vm):
    vm.info()
    changed = False

    lcm_state = vm.lcm_state
    if lcm_state == LCM_STATES.index('SHUTDOWN_POWEROFF'):
        module.fail_json(msg="Cannot perform action 'resume' because this action is not available " +
                         "for LCM_STATE: 'SHUTDOWN_POWEROFF'. Wait for the VM to shutdown properly")
    if lcm_state not in [LCM_STATES.index('RUNNING')]:
        changed = True

    if changed and not module.check_mode:
        vm.resume()

    return changed


def resume_vms(module, client, vms):
    changed = False

    for vm in vms:
        changed = resume_vm(module, vm) or changed

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
        if vm.state != VM_STATES.index('POWEROFF'):
            module.fail_json(msg="'disksaveas' option can be used only when the VM is in 'POWEROFF' state")
        client.call('vm.disksaveas', vm.id, disk_id, image_name, 'OS', -1)
        wait_for_poweroff(module, vm, wait_timeout)  # wait for VM to leave the hotplug_saveas_poweroff state


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
        "disk_size": {"required": False, "type": "str"},
        "networks": {"default": [], "type": "list"},
        "count": {"default": 1, "type": "int"},
        "exact_count": {"required": False, "type": "int"},
        "attributes": {"default": {}, "type": "dict"},
        "count_attributes": {"required": False, "type": "dict"},
        "labels": {"default": [], "type": "list"},
        "count_labels": {"required": False, "type": "list"},
        "disk_saveas": {"type": "dict"}
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
                               ['instance_ids', 'networks']
                           ],
                           supports_check_mode=True)

    if not HAS_OCA:
        module.fail_json(msg='This module requires python-oca to work!')

    auth = get_connection_info(module)
    params = module.params
    instance_ids = params.get('instance_ids')
    requested_template_name = params.get('template_name')
    requested_template_id = params.get('template_id')
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
    networks = params.get('networks')
    count = params.get('count')
    exact_count = params.get('exact_count')
    attributes = params.get('attributes')
    count_attributes = params.get('count_attributes')
    labels = params.get('labels')
    count_labels = params.get('count_labels')
    disk_saveas = params.get('disk_saveas')

    if not (auth.username and auth.password):
        client = oca.Client(None, auth.url)
    else:
        client = oca.Client(auth.username + ':' + auth.password, auth.url)

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
    if requested_template_id or requested_template_name:
        template_id = get_template_id(module, client, requested_template_id, requested_template_name)
        if template_id is None:
            if requested_template_id:
                module.fail_json(msg='There is no template with template_id: ' + str(requested_template_id))
            elif requested_template_name:
                module.fail_json(msg="There is no template with name: " + requested_template_name)

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
        changed, instances_list, tagged_instances_list = create_exact_count_of_vms(module, client, template_id, exact_count, attributes,
                                                                                   count_attributes, labels, count_labels, disk_size,
                                                                                   networks, hard, wait, wait_timeout)
        vms = tagged_instances_list
    elif template_id is not None and state == 'present':
        # Deploy count VMs
        changed, instances_list, tagged_instances_list = create_count_of_vms(module, client, template_id, count,
                                                                             attributes, labels, disk_size, networks, wait, wait_timeout)
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
            vms = get_vms_by_ids(module, client, state, instance_ids)
        else:
            tagged = True
            vms = get_all_vms_by_attributes(client, attributes, labels)

        if len(vms) == 0 and state != 'absent' and state != 'present':
            module.fail_json(msg='There are no instances with specified `instance_ids`, `attributes` and/or `labels`')

        if len(vms) == 0 and state == 'present' and not tagged:
            module.fail_json(msg='There are no instances with specified `instance_ids`.')

        if tagged and state == 'absent':
            module.fail_json(msg='Option `instance_ids` is required when state is `absent`.')

        if state == 'absent':
            changed = terminate_vms(module, client, vms, hard)
        elif state == 'rebooted':
            changed = reboot_vms(module, client, vms, wait_timeout, hard)
        elif state == 'poweredoff':
            changed = poweroff_vms(module, client, vms, hard)
        elif state == 'running':
            changed = resume_vms(module, client, vms)

        instances_list = vms
        tagged_instances_list = []

    if permissions is not None:
        changed = set_vm_permissions(module, client, vms, permissions) or changed

    if owner_id is not None or group_id is not None:
        changed = set_vm_ownership(module, client, vms, owner_id, group_id) or changed

    if wait and not module.check_mode and state != 'present':
        wait_for = {
            'absent': wait_for_done,
            'rebooted': wait_for_running,
            'poweredoff': wait_for_poweroff,
            'running': wait_for_running
        }
        for vm in vms:
            if vm is not None:
                wait_for[state](module, vm, wait_timeout)

    if disk_saveas is not None:
        if len(vms) == 0:
            module.fail_json(msg="There is no VM whose disk will be saved.")
        disk_save_as(module, client, vms[0], disk_saveas, wait_timeout)
        changed = True

    # instances - a list of instances info whose state is changed or which are fetched with C(instance_ids) option
    instances = list(get_vm_info(client, vm) for vm in instances_list if vm is not None)
    instances_ids = list(vm.id for vm in instances_list if vm is not None)
    # tagged_instances - A list of instances info based on a specific attributes and/or labels that are specified with C(count_attributes) and C(count_labels)
    tagged_instances = list(get_vm_info(client, vm) for vm in tagged_instances_list if vm is not None)

    result = {'changed': changed, 'instances': instances, 'instances_ids': instances_ids, 'tagged_instances': tagged_instances}

    module.exit_json(**result)


if __name__ == '__main__':
    main()
