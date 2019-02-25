#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2018, Ansible Project
# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
#
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
module: vmware_guest_boot_manager
short_description: Manage boot options for the given virtual machine
description:
    - This module can be used to manage boot options for the given virtual machine.
version_added: 2.7
author:
    - Abhijeet Kasurde (@Akasurde) <akasurde@redhat.com>
notes:
    - Tested on vSphere 6.5
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
   name:
     description:
     - Name of the VM to work with.
     - This is required if C(uuid) parameter is not supplied.
   uuid:
     description:
     - UUID of the instance to manage if known, this is VMware's BIOS UUID by default.
     - This is required if C(name) parameter is not supplied.
   use_instance_uuid:
     description:
     - Whether to use the VMWare instance UUID rather than the BIOS UUID.
     default: no
     type: bool
     version_added: '2.8'
   boot_order:
     description:
     - List of the boot devices.
     default: []
   name_match:
     description:
     - If multiple virtual machines matching the name, use the first or last found.
     default: 'first'
     choices: ['first', 'last']
   boot_delay:
     description:
     - Delay in milliseconds before starting the boot sequence.
     default: 0
   enter_bios_setup:
     description:
     - If set to C(True), the virtual machine automatically enters BIOS setup the next time it boots.
     - The virtual machine resets this flag, so that the machine boots proceeds normally.
     type: 'bool'
     default: False
   boot_retry_enabled:
     description:
     - If set to C(True), the virtual machine that fails to boot, will try to boot again after C(boot_retry_delay) is expired.
     - If set to C(False), the virtual machine waits indefinitely for user intervention.
     type: 'bool'
     default: False
   boot_retry_delay:
     description:
     - Specify the time in milliseconds between virtual machine boot failure and subsequent attempt to boot again.
     - If set, will automatically set C(boot_retry_enabled) to C(True) as this parameter is required.
     default: 0
   boot_firmware:
     description:
     - Choose which firmware should be used to boot the virtual machine.
     choices: ["bios", "efi"]
   secure_boot_enabled:
     description:
     - Choose if EFI secure boot should be enabled.  EFI secure boot can only be enabled with boot_firmware = efi
     type: 'bool'
     default: False
     version_added: '2.8'
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Change virtual machine's boot order and related parameters
  vmware_guest_boot_manager:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    name: testvm
    boot_delay: 2000
    enter_bios_setup: True
    boot_retry_enabled: True
    boot_retry_delay: 22300
    boot_firmware: bios
    secure_boot_enabled: False
    boot_order:
      - floppy
      - cdrom
      - ethernet
      - disk
  delegate_to: localhost
  register: vm_boot_order
'''

RETURN = r"""
vm_boot_status:
    description: metadata about boot order of virtual machine
    returned: always
    type: dict
    sample: {
        "current_boot_order": [
            "floppy",
            "disk",
            "ethernet",
            "cdrom"
        ],
        "current_boot_delay": 2000,
        "current_boot_retry_delay": 22300,
        "current_boot_retry_enabled": true,
        "current_enter_bios_setup": true,
        "current_boot_firmware": "bios",
        "current_secure_boot_enabled": false,
        "previous_boot_delay": 10,
        "previous_boot_retry_delay": 10000,
        "previous_boot_retry_enabled": true,
        "previous_enter_bios_setup": false,
        "previous_boot_firmware": "efi",
        "previous_secure_boot_enabled": true,
        "previous_boot_order": [
            "ethernet",
            "cdrom",
            "floppy",
            "disk"
        ],
    }
"""


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec, find_vm_by_id, wait_for_task, TaskError

try:
    from pyVmomi import vim
except ImportError:
    pass


class VmBootManager(PyVmomi):
    def __init__(self, module):
        super(VmBootManager, self).__init__(module)
        self.name = self.params['name']
        self.uuid = self.params['uuid']
        self.use_instance_uuid = self.params['use_instance_uuid']
        self.vm = None

    def _get_vm(self):
        vms = []

        if self.uuid:
            if self.use_instance_uuid:
                vm_obj = find_vm_by_id(self.content, vm_id=self.uuid, vm_id_type="instance_uuid")
            else:
                vm_obj = find_vm_by_id(self.content, vm_id=self.uuid, vm_id_type="uuid")
            if vm_obj is None:
                self.module.fail_json(msg="Failed to find the virtual machine with UUID : %s" % self.uuid)
            vms = [vm_obj]

        elif self.name:
            objects = self.get_managed_objects_properties(vim_type=vim.VirtualMachine, properties=['name'])
            for temp_vm_object in objects:
                if temp_vm_object.obj.name == self.name:
                    vms.append(temp_vm_object.obj)

        if vms:
            if self.params.get('name_match') == 'first':
                self.vm = vms[0]
            elif self.params.get('name_match') == 'last':
                self.vm = vms[-1]
        else:
            self.module.fail_json(msg="Failed to find virtual machine using %s" % (self.name or self.uuid))

    @staticmethod
    def humanize_boot_order(boot_order):
        results = []
        for device in boot_order:
            if isinstance(device, vim.vm.BootOptions.BootableCdromDevice):
                results.append('cdrom')
            elif isinstance(device, vim.vm.BootOptions.BootableDiskDevice):
                results.append('disk')
            elif isinstance(device, vim.vm.BootOptions.BootableEthernetDevice):
                results.append('ethernet')
            elif isinstance(device, vim.vm.BootOptions.BootableFloppyDevice):
                results.append('floppy')
        return results

    def ensure(self):
        self._get_vm()

        valid_device_strings = ['cdrom', 'disk', 'ethernet', 'floppy']

        boot_order_list = []
        for device_order in self.params.get('boot_order'):
            if device_order not in valid_device_strings:
                self.module.fail_json(msg="Invalid device found [%s], please specify device from ['%s']" % (device_order,
                                                                                                            "', '".join(valid_device_strings)))
            if device_order == 'cdrom':
                first_cdrom = [device for device in self.vm.config.hardware.device if isinstance(device, vim.vm.device.VirtualCdrom)]
                if first_cdrom:
                    boot_order_list.append(vim.vm.BootOptions.BootableCdromDevice())
            elif device_order == 'disk':
                first_hdd = [device for device in self.vm.config.hardware.device if isinstance(device, vim.vm.device.VirtualDisk)]
                if first_hdd:
                    boot_order_list.append(vim.vm.BootOptions.BootableDiskDevice(deviceKey=first_hdd[0].key))
            elif device_order == 'ethernet':
                first_ether = [device for device in self.vm.config.hardware.device if isinstance(device, vim.vm.device.VirtualEthernetCard)]
                if first_ether:
                    boot_order_list.append(vim.vm.BootOptions.BootableEthernetDevice(deviceKey=first_ether[0].key))
            elif device_order == 'floppy':
                first_floppy = [device for device in self.vm.config.hardware.device if isinstance(device, vim.vm.device.VirtualFloppy)]
                if first_floppy:
                    boot_order_list.append(vim.vm.BootOptions.BootableFloppyDevice())

        change_needed = False
        kwargs = dict()
        if len(boot_order_list) != len(self.vm.config.bootOptions.bootOrder):
            kwargs.update({'bootOrder': boot_order_list})
            change_needed = True
        else:
            for i in range(0, len(boot_order_list)):
                boot_device_type = type(boot_order_list[i])
                vm_boot_device_type = type(self.vm.config.bootOptions.bootOrder[i])
                if boot_device_type != vm_boot_device_type:
                    kwargs.update({'bootOrder': boot_order_list})
                    change_needed = True

        if self.vm.config.bootOptions.bootDelay != self.params.get('boot_delay'):
            kwargs.update({'bootDelay': self.params.get('boot_delay')})
            change_needed = True

        if self.vm.config.bootOptions.enterBIOSSetup != self.params.get('enter_bios_setup'):
            kwargs.update({'enterBIOSSetup': self.params.get('enter_bios_setup')})
            change_needed = True

        if self.vm.config.bootOptions.bootRetryEnabled != self.params.get('boot_retry_enabled'):
            kwargs.update({'bootRetryEnabled': self.params.get('boot_retry_enabled')})
            change_needed = True

        if self.vm.config.bootOptions.bootRetryDelay != self.params.get('boot_retry_delay'):
            if not self.vm.config.bootOptions.bootRetryEnabled:
                kwargs.update({'bootRetryEnabled': True})
            kwargs.update({'bootRetryDelay': self.params.get('boot_retry_delay')})
            change_needed = True

        boot_firmware_required = False
        if self.vm.config.firmware != self.params.get('boot_firmware'):
            change_needed = True
            boot_firmware_required = True

        if self.vm.config.bootOptions.efiSecureBootEnabled != self.params.get('secure_boot_enabled'):
            if self.params.get('secure_boot_enabled') and self.params.get('boot_firmware') == "bios":
                self.module.fail_json(msg="EFI secure boot cannot be enabled when boot_firmware = bios, but both are specified")

            # If the user is not specifying boot_firmware, make sure they aren't trying to enable it on a
            # system with boot_firmware already set to 'bios'
            if self.params.get('secure_boot_enabled') and \
               self.params.get('boot_firmware') is None and \
               self.vm.config.firmware == 'bios':
                self.module.fail_json(msg="EFI secure boot cannot be enabled when boot_firmware = bios.  VM's boot_firmware currently set to bios")

            kwargs.update({'efiSecureBootEnabled': self.params.get('secure_boot_enabled')})
            change_needed = True

        changed = False
        results = dict(
            previous_boot_order=self.humanize_boot_order(self.vm.config.bootOptions.bootOrder),
            previous_boot_delay=self.vm.config.bootOptions.bootDelay,
            previous_enter_bios_setup=self.vm.config.bootOptions.enterBIOSSetup,
            previous_boot_retry_enabled=self.vm.config.bootOptions.bootRetryEnabled,
            previous_boot_retry_delay=self.vm.config.bootOptions.bootRetryDelay,
            previous_boot_firmware=self.vm.config.firmware,
            previous_secure_boot_enabled=self.vm.config.bootOptions.efiSecureBootEnabled,
            current_boot_order=[],
        )

        if change_needed:
            vm_conf = vim.vm.ConfigSpec()
            vm_conf.bootOptions = vim.vm.BootOptions(**kwargs)
            if boot_firmware_required:
                vm_conf.firmware = self.params.get('boot_firmware')
            task = self.vm.ReconfigVM_Task(vm_conf)

            try:
                changed, result = wait_for_task(task)
            except TaskError as e:
                self.module.fail_json(msg="Failed to perform reconfigure virtual"
                                          " machine %s for boot order due to: %s" % (self.name or self.uuid,
                                                                                     to_native(e)))

        results.update(
            {
                'current_boot_order': self.humanize_boot_order(self.vm.config.bootOptions.bootOrder),
                'current_boot_delay': self.vm.config.bootOptions.bootDelay,
                'current_enter_bios_setup': self.vm.config.bootOptions.enterBIOSSetup,
                'current_boot_retry_enabled': self.vm.config.bootOptions.bootRetryEnabled,
                'current_boot_retry_delay': self.vm.config.bootOptions.bootRetryDelay,
                'current_boot_firmware': self.vm.config.firmware,
                'current_secure_boot_enabled': self.vm.config.bootOptions.efiSecureBootEnabled,
            }
        )

        self.module.exit_json(changed=changed, vm_boot_status=results)


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        name=dict(type='str'),
        uuid=dict(type='str'),
        use_instance_uuid=dict(type='bool', default=False),
        boot_order=dict(
            type='list',
            default=[],
        ),
        name_match=dict(
            choices=['first', 'last'],
            default='first'
        ),
        boot_delay=dict(
            type='int',
            default=0,
        ),
        enter_bios_setup=dict(
            type='bool',
            default=False,
        ),
        boot_retry_enabled=dict(
            type='bool',
            default=False,
        ),
        boot_retry_delay=dict(
            type='int',
            default=0,
        ),
        secure_boot_enabled=dict(
            type='bool',
            default=False,
        ),
        boot_firmware=dict(
            type='str',
            choices=['efi', 'bios'],
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[
            ['name', 'uuid']
        ],
        mutually_exclusive=[
            ['name', 'uuid']
        ],
    )

    pyv = VmBootManager(module)
    pyv.ensure()


if __name__ == '__main__':
    main()
