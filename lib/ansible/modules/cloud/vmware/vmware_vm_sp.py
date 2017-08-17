#!/usr/bin/python
# -*- coding: utf-8 -*-

# Prasanna Nanda <pnanda@cloudsimple.com>

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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: vmware_vm_sp
short_description: VM Storage Profile Utilities
description:
    - Attach/Detach a Storage Profile to a VM
version_added: 2.4
author:
    - Prasanna Nanda <pnanda@cloudsimple.com>
notes:
    - Tested on vSphere 6.5
requirements:
    - "python >= 2.7"
    - PyVmomi
options:
    vmname:
        description:
            - Name of the VM to which Storage Profile will be attached/detached/check
        required: True
    profilename:
        description:
            - Name of the Storage Profile which will be attached/detached
        required: True
    action:
        description:
            - Valid values are attach/detach/check
        required: True
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
  - name: Attach/Detach a VM to a Storage Profile or Check Compliance
    vmware_vm_sp:
      hostname: A vCenter host
      username: vCenter username
      password: vCenter password
      vmname: Name of the VM to which Storage Profile will be attached/detached/check
      profilename: Name of the Storage Profile which will be attached/detached/check
      action: attach|detach|check
'''

RETURN = ''' # '''

try:
    from pyVmomi import vim, pbm, vmodl
    from pyVim.connect import SoapStubAdapter
    from pyVim.connect import SmartConnect, Disconnect
    from ansible.module_utils.spbm_client import SPBMClient
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False

import time
from ansible.module_utils.vmware import vmware_argument_spec, find_vm_by_name, find_datastore_by_name, wait_for_task, connect_to_api
import ssl
import atexit
from ansible.module_utils.basic import AnsibleModule


class vmware_vm_sp(object):
    def __init__(self, module):
        self.module = module
        self.vmname = module.params['vmname']
        self.profilename = module.params['profilename']
        self.action = module.params['action']
        self.profile = None
        try:
            si, content = connect_to_api(module=module, disconnect_atexit=True, return_service_instance=True)
            self.spbmclient = SPBMClient(vc_si=si, hostname=module.params['hostname'])
            self.content = content
        except vmodl.RuntimeFault as runtime_fault:
            module.fail_json(msg=runtime_fault.msg)
        except vmodl.MethodFault as method_fault:
            module.fail_json(msg=method_fault.msg)
        except Exception as e:
            module.fail_json(msg=str(e))

    def attach_sp_to_vm(self):
        profiles = self.spbmclient.get_profiles()
        if not profiles:
            self.module.fail_json(changed=False, msg="Could not retrieve Storage Profile Information from vCenter")
        else:
            for profile in profiles:
                if self.module.params['profilename'] == profile.name:
                    self.profile = profile
                    break
            if self.profile is None:
                self.module.fail_json(changed=False, msg="Did not find Storage Profile {} in vCenter".format(self.profilename))
            vm = find_vm_by_name(content=self.content, vm_name=self.vmname)
            if vm is None:
                self.module.fail_json(changed=False, msg="Did not find VM {} in vCenter".format(self.vmname))
            # For attaching a storage Profile to a VM, you need to attach the
            # profile to VM Home and individual disks.
            disks = []
            devices = vm.config.hardware.device
            for device in devices:
                if device:
                    if device and isinstance(device, vim.vm.device.VirtualDisk):
                        disks.append(device)
            device_change = []
            for disk in disks:
                profile = vim.VirtualMachineDefinedProfileSpec(profileId=self.profile.profileId.uniqueId)
                device_change.append(vim.VirtualDeviceConfigSpec(device=disk, operation=vim.VirtualDeviceConfigSpecOperation.edit, profile=[profile]))
            profile = vim.VirtualMachineDefinedProfileSpec(profileId=self.profile.profileId.uniqueId)
            vmSpec = vim.VirtualMachineConfigSpec(vmProfile=[profile], deviceChange=device_change)
            state, error = wait_for_task(vm.ReconfigVM_Task(spec=vmSpec))
            if state:
                self.module.exit_json(changed=True, msg="Attached Profile {} to VM {}".format(self.profilename, self.vmname))
            else:
                self.module.fail_json(changed=False, msg="Failed to attach Profile {} to VM {}. Error {}".format(self.profilename, self.vmname, error))

    def reset_sp_vm(self):
        profiles = self.spbmclient.get_profiles()
        if not profiles:
            self.module.fail_json(changed=False, msg="Could not retrieve Storage Profile Information from vCenter")
        else:
            vm = find_vm_by_name(content=self.content, vm_name=self.vmname)
            if vm is None:
                self.module.fail_json(changed=False, msg="Did not find VM {} in vCenter".format(self.vmname))

            # Find Where VM Home is Residing
            vmPathName = vm.config.files.vmPathName
            vmx_datastore = vmPathName.partition(']')[0].replace('[', '')
            vmx_profile = self.spbmclient.get_ds_default_profile(find_datastore_by_name(content=self.content, datastore_name=vmx_datastore))

            disks = []
            devices = vm.config.hardware.device
            for device in devices:
                if device:
                    if device and isinstance(device, vim.vm.device.VirtualDisk):
                        disks.append(device)
            device_change = []
            for disk in disks:
                datastore_profile = self.spbmclient.get_ds_default_profile(disk.backing.datastore)
                profile = vim.VirtualMachineDefinedProfileSpec(profileId=datastore_profile.uniqueId)
                device_change.append(vim.VirtualDeviceConfigSpec(device=disk, operation=vim.VirtualDeviceConfigSpecOperation.edit, profile=[profile]))
            profile = vim.VirtualMachineDefinedProfileSpec(profileId=vmx_profile.uniqueId)
            vmSpec = vim.VirtualMachineConfigSpec(vmProfile=[profile], deviceChange=device_change)
            state, error = wait_for_task(vm.ReconfigVM_Task(spec=vmSpec))
            if state:
                self.module.exit_json(changed=True, msg="Detached Profile {} from VM {}".format(self.profilename, self.vmname))
            else:
                self.module.fail_json(changed=False, msg="Failed to Detach Profile from VM {}. Error {}".format(self.vmname, error))

    def check_compliance_vm(self):
            profiles = self.spbmclient.get_profiles()
            if not profiles:
                self.module.fail_json(changed=False, msg="Could not retrieve Storage Profile Information from vCenter")
            vm = find_vm_by_name(content=self.content, vm_name=self.vmname)
            if vm is None:
                self.module.fail_json(changed=False, msg="Did not find VM {} in vCenter".format(self.vmname))
            compliance_status = self.spbmclient.check_compliance_vm(vm)
            if compliance_status is None:
                self.module.fail_json(changed=False, msg="Failed to find compliance status for VM {}".format(self.vmname))
            else:
                self.module.exit_json(changed=False, compliance_status=compliance_status)


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(vmname=dict(required=True, type='str'),
                         profilename=dict(required=False, type='str'),
                         action=dict(default='attach', choices=['attach', 'check', 'detach'], type='str')))
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)
    if not HAS_PYVMOMI:
        module.fail_json(msg="pyvmomi is required for this module")
    spbm = vmware_vm_sp(module)
    if module.params['action'] == 'attach':
        spbm.attach_sp_to_vm()
    if module.params['action'] == 'check':
        spbm.check_compliance_vm()
    if module.params['action'] == 'detach':
        spbm.reset_sp_vm()

if __name__ == '__main__':
    main()
