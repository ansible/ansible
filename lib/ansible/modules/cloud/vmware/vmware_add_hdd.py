#!/usr/bin/python

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
module: vmware_add_hdd
short_description: Add a iscsi hdd to vm on VMware vSphere.
description:
     - Adds an additional iscsi hard drive of a specified size and type to a vm on VMWare vSphere.
options:
  diskSize:
    description:
      - The size of the new disk in GB
    required: false
    default: Resources
  thinDisk:
    description:
      - Specifies if the disk is a thin disk or not.
    required: False
  vm:
    description:
      - The file path to place the VM.
    required: True
extends_documentation_fragment: vmware.documentation
notes:
  - This module should run from a system that can access vSphere directly.
    Either by using local_action, or using delegate_to. This module will not
    be able to find nor place VMs or templates in the root folder.
author: "Caitlin Campbell <cacampbe@redhat.com>"
requirements:
  - "python >= 2.6"
  - pyVmomi
'''


EXAMPLES = '''
# Add a iscsi device to iscsi adapter on vm.
- vvmware_add_hdd:
    hostname: vcenter.mydomain.local
    username: myuser
    password: mypass
    thinDisk: False
    vm: /clients/clienta/clientaVM
    diskSize: 3
'''


try:
    from pyVmomi import vim
    from pyVmomi import vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False

from ansible.module_utils.six import iteritems


def add_disk(module, vm, disk_size, thinDisk):
        spec = vim.vm.ConfigSpec()
        # get all disks on a VM, set unit_number to the next available
        for dev in vm.config.hardware.device:
            if hasattr(dev.backing, 'fileName'):
                unit_number = int(dev.unitNumber) + 1
                # unit_number 7 reserved for scsi controller
                if unit_number == 7:
                    unit_number += 1
                if unit_number >= 16:
                    module.fail_json(msg='A maximum of 16 disk are supported.')
            if isinstance(dev, vim.vm.device.VirtualSCSIController):
                controller = dev
        # add disk here
        dev_changes = []
        new_disk_kb = int(disk_size) * 1024 * 1024
        disk_spec = vim.vm.device.VirtualDeviceSpec()
        disk_spec.fileOperation = "create"
        disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        disk_spec.device = vim.vm.device.VirtualDisk()
        disk_spec.device.backing = vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
        if thinDisk is True:
            disk_spec.device.backing.thinProvisioned = True
        disk_spec.device.backing.diskMode = 'persistent'
        disk_spec.device.unitNumber = unit_number
        disk_spec.device.capacityInKB = new_disk_kb
        disk_spec.device.controllerKey = controller.key
        dev_changes.append(disk_spec)
        spec.deviceChange = dev_changes
        vm.ReconfigVM_Task(spec=spec)

        return unit_number, controller.key


def objwalk(obj, path_elements):
    if hasattr(obj, 'parent'):
        new_obj = getattr(obj, 'parent')
        if new_obj:
            if new_obj.name != 'vm':
                # 'vm' is an invisible folder that exists at the datacenter root so we ignore it
                path_elements.append(new_obj.name)

            objwalk(new_obj, path_elements)

    return path_elements


def get_vm_object(module, conn, path):

    all_vms = get_all_objs(conn, [vim.VirtualMachine])
    matching_vms = []
    path_list = filter(None, path.split('/'))
    name = path_list.pop()

    for vm_obj, label in iteritems(all_vms):
        if label == name:
            matching_vms.append(vm_obj)

    try:
        if len(matching_vms) > 1:

            for vm_obj in matching_vms:
                elements = []
                if set(path_list).issubset(set(objwalk(vm_obj, elements))):
                    return vm_obj

        else:
            return matching_vms[0]

    except TypeError:
        module.fail_json(msg='Could not find VM at %s' % path)


def main():

    argument_spec = vmware_argument_spec()

    argument_spec.update(
        dict(
            thinDisk=dict(required=False, default=True, type='bool'),
            vm=dict(required=True, type='str'),
            diskSize=dict(required=True, type='int'),
        )
    )

    module = AnsibleModule(argument_spec=argument_spec)

    if HAS_PYVMOMI == False:
        module.fail_json(msg='pyvmomi is required for this module')

    hostname = module.params['hostname']
    username = module.params['username']
    password = module.params['password']
    thinDisk = module.params['thinDisk']
    vm = module.params['vm']
    diskSize = module.params['diskSize']
    validate_certs = module.params['validate_certs']

    conn = connect_to_api(module)
    vmToWorkOn = get_vm_object(module, conn, vm)

    try:
        unitNumber, controlerKey = add_disk(module, vmToWorkOn, diskSize, thinDisk)
        module.exit_json(changed=True, vm=vm, diskUnitNumber=unitNumber, controlerKey=controlerKey, isThinDisk=thinDisk)

    except Exception as  e:
        module.fail_json(msg='Could not add disk', err=e.message)



# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.vmware import *
if __name__ == '__main__':
    main()
