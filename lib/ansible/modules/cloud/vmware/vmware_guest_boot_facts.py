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
module: vmware_guest_boot_facts
short_description: Gather facts about boot options for the given virtual machine
description:
    - This module can be used to gather facts aboyt boot options for the given virtual machine.
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
   name_match:
     description:
     - If multiple virtual machines matching the name, use the first or last found.
     default: 'first'
     choices: ['first', 'last']
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Gather facts about virtual machine's boot order and related parameters
  vmware_guest_boot_facts:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    validate_certs: no
    name: "{{ vm_name }}"
  register: vm_boot_order_facts
'''

RETURN = r"""
vm_boot_facts:
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
    }
"""


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec, find_vm_by_id

try:
    from pyVmomi import vim
except ImportError:
    pass


class VmBootFactsManager(PyVmomi):
    def __init__(self, module):
        super(VmBootFactsManager, self).__init__(module)
        self.name = self.params['name']
        self.uuid = self.params['uuid']
        self.use_instance_uuid = self.params['use_instance_uuid']
        self.vm = None

    def _get_vm(self):
        vms = []

        if self.uuid:
            if self.use_instance_uuid:
                vm_obj = find_vm_by_id(self.content, vm_id=self.uuid, vm_id_type="use_instance_uuid")
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

        results = dict()
        if self.vm and self.vm.config:
            results = dict(
                current_boot_order=self.humanize_boot_order(self.vm.config.bootOptions.bootOrder),
                current_boot_delay=self.vm.config.bootOptions.bootDelay,
                current_enter_bios_setup=self.vm.config.bootOptions.enterBIOSSetup,
                current_boot_retry_enabled=self.vm.config.bootOptions.bootRetryEnabled,
                current_boot_retry_delay=self.vm.config.bootOptions.bootRetryDelay,
                current_boot_firmware=self.vm.config.firmware,
                current_secure_boot_enabled=self.vm.config.bootOptions.efiSecureBootEnabled
            )

        self.module.exit_json(changed=False, vm_boot_facts=results)


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        name=dict(type='str'),
        uuid=dict(type='str'),
        use_instance_uuid=dict(type='bool', default=False),
        name_match=dict(
            choices=['first', 'last'],
            default='first'
        ),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[
            ['name', 'uuid']
        ],
        mutually_exclusive=[
            ['name', 'uuid']
        ],
        supports_check_mode=True,
    )

    pyv = VmBootFactsManager(module)
    pyv.ensure()


if __name__ == '__main__':
    main()
