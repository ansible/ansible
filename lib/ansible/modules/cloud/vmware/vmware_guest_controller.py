#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Ansible Project
# Copyright: (c) 2019, VMware, Inc. All Rights Reserved.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


DOCUMENTATION = '''
---
module: vmware_guest_controller
short_description: Manage disk or USB controllers related to virtual machine in given vCenter infrastructure
description:
    - This module can be used to add, remove disk controllers or USB controllers belonging to given virtual machine.
    - All parameters and VMware object names are case sensitive.
version_added: '2.10'
author:
    - Diane Wang (@Tomorrow9) <dianew@vmware.com>
notes:
    - Tested on vSphere 6.0, 6.5 and 6.7
requirements:
    - "python >= 2.7"
    - PyVmomi
options:
   name:
     description:
     - Name of the virtual machine.
     - This is a required parameter, if parameter C(uuid) or C(moid) is not supplied.
     type: str
   uuid:
     description:
     - UUID of the instance to gather facts if known, this is VMware's unique identifier.
     - This is a required parameter, if parameter C(name) or C(moid) is not supplied.
     type: str
   moid:
     description:
     - Managed Object ID of the instance to manage if known, this is a unique identifier only within a single vCenter instance.
     - This is required if C(name) or C(uuid) is not supplied.
     type: str
   folder:
     description:
     - Destination folder, absolute or relative path to find an existing guest.
     - This is a required parameter, only if multiple VMs are found with same name.
     - The folder should include the datacenter. ESX's datacenter is ha-datacenter
     - 'Examples:'
     - '   folder: /ha-datacenter/vm'
     - '   folder: ha-datacenter/vm'
     - '   folder: /datacenter1/vm'
     - '   folder: datacenter1/vm'
     - '   folder: /datacenter1/vm/folder1'
     - '   folder: datacenter1/vm/folder1'
     - '   folder: /folder1/datacenter1/vm'
     - '   folder: folder1/datacenter1/vm'
     - '   folder: /folder1/datacenter1/vm/folder2'
     type: str
   datacenter:
     description:
     - The datacenter name to which virtual machine belongs to.
     default: ha-datacenter
     type: str
   use_instance_uuid:
     description:
     - Whether to use the VMware instance UUID rather than the BIOS UUID.
     default: no
     type: bool
   controllers:
     description:
     - A list of disk or USB controllers to add or remove.
     - Total 4 disk controllers with the same type are allowed per VM.
     - Total 2 USB controllers are allowed per VM, 1 USB 2.0 and 1 USB 3.0 or 3.1.
     - For specific guest OS, supported controller types please refer to VMware Compatibility Guide.
     suboptions:
       controller_number:
         description:
         - Disk controller bus number. When C(state) is set to C(absent), this parameter is required.
         - When C(type) set to C(usb2) or C(usb3), this parameter is not required.
         type: int
         choices:
           - 0
           - 1
           - 2
           - 3
       type:
         description:
         - Type of disk or USB controller.
         - From vSphere 6.5 and virtual machine with hardware version 13, C(nvme) controller starts to be supported.
         required: true
         type: str
         choices:
           - buslogic
           - lsilogic
           - lsilogicsas
           - paravirtual
           - sata
           - nvme
           - usb2
           - usb3
       state:
         description:
         - Add new controller or remove specified existing controller.
         - If C(state) is set to C(absent), the specified controller will be removed from virtual machine when there is no disk or device attaching to it.
         - If specified controller is removed or not exist, no action will be taken only warning message.
         - If C(state) is set to C(present), new controller with specified type will be added.
         - If the number of controller with specified controller type reaches it's maximum, no action will be taken only warning message.
         required: true
         type: str
         choices:
           - present
           - absent
     type: list
   gather_disk_controller_facts:
     description:
     - Whether to collect existing disk and USB controllers facts only.
     - When this parameter is set to C(True), C(controllers) parameter will be ignored.
     type: bool
   sleep_time:
     description:
     - 'The sleep time in seconds after VM reconfigure task completes, used when not get the updated VM controller
       facts after VM reconfiguration.'
     - This parameter is not required. Maximum value is 600.
     default: 10
     type: int
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: Add disk and USB 3.0 controllers for virtual machine located by name
  vmware_guest_controller:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter_name }}"
    validate_certs: no
    name: test_VM
    controllers:
      - state: present
        type: sata
      - state: present
        type: nvme
      - state: present
        type: usb3
  delegate_to: localhost
  register: disk_controller_facts

- name: Remove disk controllers and USB 2.0 from virtual machine located by moid
  vmware_guest_controller:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter_name }}"
    validate_certs: no
    moid: vm-33
    controllers:
      - state: absent
        controller_number: 1
        type: sata
      - state: absent
        controller_number: 0
        type: nvme
      - state: absent
        type: usb2
  delegate_to: localhost
  register: disk_controller_facts
'''

RETURN = """
disk_controller_status:
    description: metadata about the virtual machine's existing disk controllers or after adding or removing operation
    returned: always
    type: dict
    sample: {
        "nvme": {
            "0": {
                "controller_busnumber": 0,
                "controller_controllerkey": 100,
                "controller_devicekey": 31000,
                "controller_disks_devicekey": [],
                "controller_label": "NVME controller 0",
                "controller_summary": "NVME controller 0",
                "controller_unitnumber": 30
            }
        },
        "sata": {
            "0": {
                "controller_busnumber": 0,
                "controller_controllerkey": 100,
                "controller_devicekey": 15000,
                "controller_disks_devicekey": [
                    16000,
                    16001
                ],
                "controller_label": "SATA controller 0",
                "controller_summary": "AHCI",
                "controller_unitnumber": 24
            }
        },
        "scsi": {
            "0": {
                "controller_busnumber": 0,
                "controller_controllerkey": 100,
                "controller_devicekey": 1000,
                "controller_disks_devicekey": [
                    2000
                ],
                "controller_label": "SCSI controller 0",
                "controller_summary": "LSI Logic SAS",
                "controller_unitnumber": 3
            },
            "1": {
                "controller_busnumber": 1,
                "controller_controllerkey": 100,
                "controller_devicekey": 1001,
                "controller_disks_devicekey": [],
                "controller_label": "SCSI controller 1",
                "controller_summary": "VMware paravirtual SCSI",
                "controller_unitnumber": 4
            }
        },
        "usb2": {
            "0": {
                "controller_busnumber": 0,
                "controller_controllerkey": 100,
                "controller_devicekey": 7000,
                "controller_disks_devicekey": [],
                "controller_label": "USB Controller",
                "controller_summary": "Auto connect Disabled",
                "controller_unitnumber": 22
            }
        }
    }
"""

try:
    from pyVmomi import vim
except ImportError:
    pass

from random import randint
import time
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec, wait_for_task


class PyVmomiHelper(PyVmomi):
    def __init__(self, module):
        super(PyVmomiHelper, self).__init__(module)
        self.sleep_time = 10
        self.scsi_device_type = dict(lsilogic=vim.vm.device.VirtualLsiLogicController,
                                     paravirtual=vim.vm.device.ParaVirtualSCSIController,
                                     buslogic=vim.vm.device.VirtualBusLogicController,
                                     lsilogicsas=vim.vm.device.VirtualLsiLogicSASController)
        self.sata_device_type = vim.vm.device.VirtualAHCIController
        self.nvme_device_type = vim.vm.device.VirtualNVMEController
        self.usb_device_type = dict(usb2=vim.vm.device.VirtualUSBController,
                                    usb3=vim.vm.device.VirtualUSBXHCIController)
        self.controller_types = dict(self.scsi_device_type, sata=self.sata_device_type, nvme=self.nvme_device_type)
        self.controller_types.update(self.usb_device_type)
        self.config_spec = vim.vm.ConfigSpec()
        self.config_spec.deviceChange = []
        self.change_detected = False
        self.disk_ctl_bus_num_list = dict(sata=list(range(0, 4)),
                                          nvme=list(range(0, 4)),
                                          scsi=list(range(0, 4)))

    def get_unused_ctl_bus_number(self):
        """
        Get gid of occupied bus numbers of each type of disk controller, update the available bus number list
        """
        for device in self.current_vm_obj.config.hardware.device:
            if isinstance(device, self.sata_device_type):
                if len(self.disk_ctl_bus_num_list['sata']) != 0:
                    self.disk_ctl_bus_num_list['sata'].remove(device.busNumber)
            if isinstance(device, self.nvme_device_type):
                if len(self.disk_ctl_bus_num_list['nvme']) != 0:
                    self.disk_ctl_bus_num_list['nvme'].remove(device.busNumber)
            if isinstance(device, tuple(self.scsi_device_type.values())):
                if len(self.disk_ctl_bus_num_list['scsi']) != 0:
                    self.disk_ctl_bus_num_list['scsi'].remove(device.busNumber)

    def check_ctl_disk_exist(self, ctl_type=None, bus_number=None):
        """
        Check if controller of specified type exists and if there is disk attaching to it
        Return: Specified controller device, True or False of attaching disks
        """
        ctl_specified = None
        disks_attached_exist = False
        if ctl_type is None:
            return ctl_specified, disks_attached_exist

        for device in self.current_vm_obj.config.hardware.device:
            if isinstance(device, self.controller_types.get(ctl_type)):
                if bus_number is not None and device.busNumber != bus_number:
                    continue
                ctl_specified = device
                if len(device.device) != 0:
                    disks_attached_exist = True
                break

        return ctl_specified, disks_attached_exist

    def create_controller(self, ctl_type, bus_number=0):
        """
        Create new disk or USB controller with specified type
        Args:
            ctl_type: controller type
            bus_number: disk controller bus number

        Return: Virtual device spec for virtual controller
        """
        disk_ctl = vim.vm.device.VirtualDeviceSpec()
        disk_ctl.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        if ctl_type == 'sata':
            disk_ctl.device = self.sata_device_type()
            disk_ctl.device.key = -randint(15000, 19999)
        elif ctl_type == 'nvme':
            disk_ctl.device = self.nvme_device_type()
            disk_ctl.device.key = -randint(31000, 39999)
        elif ctl_type in self.scsi_device_type.keys():
            disk_ctl.device = self.scsi_device_type.get(ctl_type)()
            disk_ctl.device.key = -randint(1000, 6999)
            disk_ctl.device.hotAddRemove = True
            disk_ctl.device.sharedBus = 'noSharing'
            disk_ctl.device.scsiCtlrUnitNumber = 7
        elif ctl_type in self.usb_device_type.keys():
            disk_ctl.device = self.usb_device_type.get(ctl_type)()
            if ctl_type == 'usb2':
                disk_ctl.device.key = 7000
            elif ctl_type == 'usb3':
                disk_ctl.device.key = 14000

        disk_ctl.device.deviceInfo = vim.Description()
        disk_ctl.device.busNumber = bus_number

        return disk_ctl

    def gather_disk_controller_facts(self):
        """
        Gather existing controller facts

        Return: A dictionary of each type controller facts
        """
        disk_ctl_facts = dict(
            scsi=dict(),
            sata=dict(),
            nvme=dict(),
            usb2=dict(),
            usb3=dict()
        )
        for device in self.current_vm_obj.config.hardware.device:
            ctl_facts_dict = dict()
            if isinstance(device, tuple(self.controller_types.values())):
                ctl_facts_dict[device.busNumber] = dict(
                    controller_summary=device.deviceInfo.summary,
                    controller_label=device.deviceInfo.label,
                    controller_busnumber=device.busNumber,
                    controller_controllerkey=device.controllerKey,
                    controller_devicekey=device.key,
                    controller_unitnumber=device.unitNumber,
                    controller_disks_devicekey=device.device,
                )
                if isinstance(device, tuple(self.scsi_device_type.values())):
                    disk_ctl_facts['scsi'].update(ctl_facts_dict)
                if isinstance(device, self.nvme_device_type):
                    disk_ctl_facts['nvme'].update(ctl_facts_dict)
                if isinstance(device, self.sata_device_type):
                    disk_ctl_facts['sata'].update(ctl_facts_dict)
                if isinstance(device, self.usb_device_type.get('usb2')):
                    disk_ctl_facts['usb2'].update(ctl_facts_dict)
                if isinstance(device, self.usb_device_type.get('usb3')):
                    disk_ctl_facts['usb3'].update(ctl_facts_dict)

        return disk_ctl_facts

    def sanitize_disk_controller_config(self):
        """
        Check correctness of controller configuration provided by user

        Return: A list of dictionary with checked controller configured
        """
        if not self.params.get('controllers'):
            self.module.exit_json(changed=False, msg="No controller provided for virtual"
                                                     " machine '%s' for management." % self.current_vm_obj.name)
        if 10 != self.params.get('sleep_time') <= 300:
            self.sleep_time = self.params.get('sleep_time')
        exec_get_unused_ctl_bus_number = False
        controller_config = self.params.get('controllers')
        for ctl_config in controller_config:
            if ctl_config:
                if ctl_config['type'] not in self.usb_device_type.keys():
                    if ctl_config['state'] == 'absent' and ctl_config.get('controller_number') is None:
                        self.module.fail_json(msg="Disk controller number is required when removing it.")
                    if ctl_config['state'] == 'present' and not exec_get_unused_ctl_bus_number:
                        self.get_unused_ctl_bus_number()
                        exec_get_unused_ctl_bus_number = True
                # starts from hardware version 13 nvme controller supported
                if ctl_config['state'] == 'present' and ctl_config['type'] == 'nvme':
                    vm_hwv = int(self.current_vm_obj.config.version.split('-')[1])
                    if vm_hwv < 13:
                        self.module.fail_json(msg="Can not create new NVMe disk controller due to VM hardware version"
                                                  " is '%s', not >= 13." % vm_hwv)
        if exec_get_unused_ctl_bus_number:
            for ctl_config in controller_config:
                if ctl_config and ctl_config['state'] == 'present' and ctl_config['type'] not in self.usb_device_type.keys():
                    if ctl_config['type'] in self.scsi_device_type.keys():
                        if len(self.disk_ctl_bus_num_list['scsi']) != 0:
                            ctl_config['controller_number'] = self.disk_ctl_bus_num_list['scsi'].pop(0)
                        else:
                            ctl_config['controller_number'] = None
                    elif ctl_config['type'] == 'sata' or ctl_config['type'] == 'nvme':
                        if len(self.disk_ctl_bus_num_list.get(ctl_config['type'])) != 0:
                            ctl_config['controller_number'] = self.disk_ctl_bus_num_list.get(ctl_config['type']).pop(0)
                        else:
                            ctl_config['controller_number'] = None

        return controller_config

    def configure_disk_controllers(self):
        """
        Do disk controller management, add or remove

        Return: Operation result
        """
        if self.params['gather_disk_controller_facts']:
            results = {'changed': False, 'failed': False, 'disk_controller_data': self.gather_disk_controller_facts()}
            return results

        controller_config = self.sanitize_disk_controller_config()
        for disk_ctl_config in controller_config:
            if disk_ctl_config and disk_ctl_config['state'] == 'present':
                # create new USB controller, bus number is 0
                if disk_ctl_config['type'] in self.usb_device_type.keys():
                    usb_exists, has_disks_attached = self.check_ctl_disk_exist(disk_ctl_config['type'])
                    if usb_exists:
                        self.module.warn("'%s' USB controller already exists, can not add more." % disk_ctl_config['type'])
                    else:
                        disk_controller_new = self.create_controller(disk_ctl_config['type'])
                        self.config_spec.deviceChange.append(disk_controller_new)
                        self.change_detected = True
                # create other disk controller
                else:
                    if disk_ctl_config.get('controller_number') is not None:
                        disk_controller_new = self.create_controller(disk_ctl_config['type'], disk_ctl_config.get('controller_number'))
                        self.config_spec.deviceChange.append(disk_controller_new)
                        self.change_detected = True
                    else:
                        if disk_ctl_config['type'] in self.scsi_device_type.keys():
                            self.module.warn("Already 4 SCSI controllers, can not add new '%s' controller." % disk_ctl_config['type'])
                        else:
                            self.module.warn("Already 4 '%s' controllers, can not add new one." % disk_ctl_config['type'])
            elif disk_ctl_config and disk_ctl_config['state'] == 'absent':
                existing_ctl, has_disks_attached = self.check_ctl_disk_exist(disk_ctl_config['type'], disk_ctl_config.get('controller_number'))
                if existing_ctl is not None:
                    if not has_disks_attached:
                        ctl_spec = vim.vm.device.VirtualDeviceSpec()
                        ctl_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.remove
                        ctl_spec.device = existing_ctl
                        self.config_spec.deviceChange.append(ctl_spec)
                        self.change_detected = True
                    else:
                        self.module.warn("Can not remove specified controller, type '%s', bus number '%s',"
                                         " there are disks attaching to it." % (disk_ctl_config['type'], disk_ctl_config.get('controller_number')))
                else:
                    self.module.warn("Not find specified controller to remove, type '%s', bus number '%s'."
                                     % (disk_ctl_config['type'], disk_ctl_config.get('controller_number')))

        try:
            task = self.current_vm_obj.ReconfigVM_Task(spec=self.config_spec)
            wait_for_task(task)
        except vim.fault.InvalidDeviceSpec as e:
            self.module.fail_json(msg="Failed to configure controller on given virtual machine due to invalid"
                                      " device spec : %s" % to_native(e.msg),
                                  details="Please check ESXi server logs for more details.")
        except vim.fault.RestrictedVersion as e:
            self.module.fail_json(msg="Failed to reconfigure virtual machine due to"
                                      " product versioning restrictions: %s" % to_native(e.msg))
        if task.info.state == 'error':
            results = {'changed': self.change_detected, 'failed': True, 'msg': task.info.error.msg}
        else:
            if self.change_detected:
                time.sleep(self.sleep_time)
            results = {'changed': self.change_detected, 'failed': False, 'disk_controller_data': self.gather_disk_controller_facts()}

        return results


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        name=dict(type='str'),
        uuid=dict(type='str'),
        moid=dict(type='str'),
        folder=dict(type='str'),
        datacenter=dict(type='str', default='ha-datacenter'),
        controllers=dict(
            type='list',
            elements='dict',
            required=False,
            options=dict(
                state=dict(type='str', choices=['present', 'absent'], required=True),
                controller_number=dict(type='int', choices=[0, 1, 2, 3], required=False),
                type=dict(
                    type='str',
                    choices=['sata', 'nvme', 'lsilogic', 'buslogic', 'lsilogicsas', 'paravirtual', 'usb2', 'usb3'],
                    required=True,
                ),
            ),
        ),
        use_instance_uuid=dict(type='bool', default=False),
        gather_disk_controller_facts=dict(type='bool', default=False),
        sleep_time=dict(type='int', default=10),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[
            ['name', 'uuid', 'moid']
        ]
    )

    if module.params['folder']:
        # FindByInventoryPath() does not require an absolute path
        # so we should leave the input folder path unmodified
        module.params['folder'] = module.params['folder'].rstrip('/')

    pyv = PyVmomiHelper(module)
    # Check if the VM exists before continuing
    vm = pyv.get_vm()

    if not vm:
        # We unable to find the virtual machine user specified
        # Bail out
        vm_id = (module.params.get('name') or module.params.get('uuid') or module.params.get('moid'))
        module.fail_json(msg="Unable to manage disk or USB controllers for non-existing virtual machine '%s'." % vm_id)

    # VM exists
    result = pyv.configure_disk_controllers()
    if result['failed']:
        module.fail_json(**result)
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()
