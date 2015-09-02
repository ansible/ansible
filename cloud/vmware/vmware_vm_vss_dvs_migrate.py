#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Joseph Callen <jcallen () csc.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: vmware_vm_vss_dvs_migrate
short_description: Migrates a virtual machine from a standard vswitch to distributed
description:
    - Migrates a virtual machine from a standard vswitch to distributed
version_added: 2.0
author: "Joseph Callen (@jcpowermac)"
notes:
    - Tested on vSphere 5.5
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
    hostname:
        description:
            - The hostname or IP address of the vSphere vCenter API server
        required: True
    username:
        description:
            - The username of the vSphere vCenter
        required: True
        aliases: ['user', 'admin']
    password:
        description:
            - The password of the vSphere vCenter
        required: True
        aliases: ['pass', 'pwd']
    vm_name:
        description:
            - Name of the virtual machine to migrate to a dvSwitch
        required: True
    dvportgroup_name:
        description:
            - Name of the portgroup to migrate to the virtual machine to
        required: True
'''

EXAMPLES = '''
- name: Migrate VCSA to vDS
  local_action:
    module: vmware_vm_vss_dvs_migrate
    hostname: vcenter_ip_or_hostname
    username: vcenter_username
    password: vcenter_password
    vm_name: virtual_machine_name
    dvportgroup_name: distributed_portgroup_name
'''

try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False


def _find_dvspg_by_name(content, pg_name):

    vmware_distributed_port_group = get_all_objs(content, [vim.dvs.DistributedVirtualPortgroup])
    for dvspg in vmware_distributed_port_group:
        if dvspg.name == pg_name:
            return dvspg
    return None


def find_vm_by_name(content, vm_name):

    virtual_machines = get_all_objs(content, [vim.VirtualMachine])
    for vm in virtual_machines:
        if vm.name == vm_name:
            return vm
    return None


def migrate_network_adapter_vds(module):
    vm_name = module.params['vm_name']
    dvportgroup_name = module.params['dvportgroup_name']
    content = module.params['content']

    vm_configspec = vim.vm.ConfigSpec()
    nic = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
    port = vim.dvs.PortConnection()
    devicespec = vim.vm.device.VirtualDeviceSpec()

    pg = _find_dvspg_by_name(content, dvportgroup_name)

    if pg is None:
        module.fail_json(msg="The standard portgroup was not found")

    vm = find_vm_by_name(content, vm_name)
    if vm is None:
        module.fail_json(msg="The virtual machine was not found")

    dvswitch = pg.config.distributedVirtualSwitch
    port.switchUuid = dvswitch.uuid
    port.portgroupKey = pg.key
    nic.port = port

    for device in vm.config.hardware.device:
        if isinstance(device, vim.vm.device.VirtualEthernetCard):
            devicespec.device = device
            devicespec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
            devicespec.device.backing = nic
            vm_configspec.deviceChange.append(devicespec)

    task = vm.ReconfigVM_Task(vm_configspec)
    changed, result = wait_for_task(task)
    module.exit_json(changed=changed, result=result)


def state_exit_unchanged(module):
    module.exit_json(changed=False)


def check_vm_network_state(module):
    vm_name = module.params['vm_name']
    try:
        content = connect_to_api(module)
        module.params['content'] = content
        vm = find_vm_by_name(content, vm_name)
        module.params['vm'] = vm
        if vm is None:
            module.fail_json(msg="A virtual machine with name %s does not exist" % vm_name)
        for device in vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualEthernetCard):
                if isinstance(device.backing, vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo):
                    return 'present'
        return 'absent'
    except vmodl.RuntimeFault as runtime_fault:
        module.fail_json(msg=runtime_fault.msg)
    except vmodl.MethodFault as method_fault:
        module.fail_json(msg=method_fault.msg)


def main():

    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(vm_name=dict(required=True, type='str'),
                              dvportgroup_name=dict(required=True, type='str')))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)
    if not HAS_PYVMOMI:
        module.fail_json(msg='pyvmomi is required for this module')

    vm_nic_states = {
        'absent': migrate_network_adapter_vds,
        'present': state_exit_unchanged,
    }

    vm_nic_states[check_vm_network_state(module)](module)

from ansible.module_utils.vmware import *
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()