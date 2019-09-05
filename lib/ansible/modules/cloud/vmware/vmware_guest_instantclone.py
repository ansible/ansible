#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: vmware_guest_instantclone
short_description: Manages virtual machines instant clones in vCenter
description:
    - This module can be used to create instant clones of a given virtual machine.
    - All parameters and VMware object names are case sensitive.
version_added: 2.9
author:
    - Dakota Clark (@PDQDakota) <dakota.clark@pdq.com>
notes:
    - Tested on vSphere 6.7
    - For best results, freeze the source VM before use
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
   state:
    description:
    - Whether a given clone should be present or absent from the vSphere instance.
    default: present
    choices: [ present, absent ]
    required: True
    type: str
   name:
    description:
    - Name of the new instant clone VM.
    required: True
    type: str
   source_vm:
    description:
    - Name of the source VM to clone from, for best results ensure it is in a frozen state.
    required: True
    type: str
   customvalues:
    description:
    - A Key / Value list of custom configuration parameters.
    required: False
    type: list
extends_documentation_fragment: vmware.documentation
'''
EXAMPLES = r'''
'''

RETURN = r'''
'''

HAS_PYVMOMI = False
try:
    from pyVmomi import vim, vmodl, VmomiSupport
    HAS_PYVMOMI = True
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.network import is_mac
from ansible.module_utils._text import to_text, to_native
from ansible.module_utils.vmware import (find_obj, gather_vm_facts, vmware_argument_spec,
                                         set_vm_power_state, PyVmomi, wait_for_task, TaskError)


class PyVmomiHelper(PyVmomi):
    def __init__(self, module):
        super(PyVmomiHelper, self).__init__(module)

    def deploy_instantclone(self, vm):
        vm_state = gather_vm_facts(self.content, vm)
        # An instant clone requires the base VM to be running, fail if it is not
        if vm_state['hw_power_status'] != 'poweredOn':
            self.module.module.fail_json(msg='Unable to instant clone a VM in a "%s" state. It must be powered on.' % vm_state['hw_power_status'])
        if vm_state['instant_clone_frozen'] is None:
            self.module.module.fail_json(msg='Unable to determine if VM is in a frozen state. Is vSphere running 6.7 or later?')

        # Build VM config dict
        config = []
        # If customvalues is not empty, fill config
        if len(self.module.params['customvalues']) != 0:
            for kv in self.module.params['customvalues']:
                if 'key' not in kv or 'value' not in kv:
                    self.module.module.exit_json(msg="The parameter customvalues items required both 'key' and 'value' fields.")
                ov = vim.OptionValue()
                ov.key = kv['key']
                ov.value = kv['value']
                config.append(ov)

        # Begin building the spec
        instantclone_spec = vim.VirtualMachineInstantCloneSpec()
        location_spec = vim.VirtualMachineRelocateSpec()
        instantclone_spec.config = config
        instantclone_spec.name = self.module.params['clone_name']

        if vm_state['instant_clone_frozen'] is False:
            # VM is not frozen, need to do prep work for instant clone
            vm_network_adapters = []
            devices = vm.config.hardware.device
            for device in devices:
                if isinstance(device, vim.VirtualEthernetCard):
                    vm_network_adapters.append(device)

            for vm_network_adapter in vm_network_adapters:
                # Standard network switch
                if isinstance(vm_network_adapter.backing, vim.VirtualEthernetCardNetworkBackingInfo):
                    network_id = vm_network_adapter.backing.network
                    device_spec = vim.VirtualDeviceConfigSpec()
                    device_spec.operation = 'edit'
                    device_spec.device = vm_network_adapter
                    device_spec.device.backing = vim.VirtualEthernetCardNetworkBackingInfo()
                    device_spec.device.backing.deviceName = network_id
                    connectable = vim.VirtualDeviceConnectInfo()
                    connectable.migrateConnect = 'disconnect'
                    device_spec.device.connectable = connectable
                    location_spec.deviceChange.append(device_spec)
                # Distributed network switch
                elif isinstance(vm_network_adapter.backing, vim.VirtualEthernetCardDistributedVirtualPortBackingInfo):
                    network_id = vm_network_adapter.backing.port
                    # If the port key isn't cleared the VM clone will fail as the port is in use by the running source VM.
                    network_id.portKey = None
                    device_spec = vim.VirtualDeviceConfigSpec()
                    device_spec.operation = 'edit'
                    device_spec.device = vm_network_adapter
                    device_spec.device.backing = vim.VirtualEthernetCardDistributedVirtualPortBackingInfo()
                    device_spec.device.backing.port = network_id
                    connectable = vim.VirtualDeviceConnectInfo()
                    connectable.migrateConnect = 'disconnect'
                    device_spec.device.connectable = connectable
                    location_spec.deviceChange.append(device_spec)
                else:
                    self.module.module.exit_json(msg='Unknown network backing type of %s only Virtual Distributed switches and Standard swtiches are supported.'
                                                 % vm_network_adapter.__class__.__name__.split('.')[-1])

            # Finalize the spec for a non-frozen VM
            instantclone_spec.location = location_spec

        else:
            # VM is frozen, can clone without prep work
            # Finalize the spec for a frozen VM
            instantclone_spec.location = location_spec

        task = vm.InstantClone_Task(instantclone_spec)
        wait_for_task(task)

        if task.info.state == 'error':
            kwargs = {
                'changed': False,
                'failed': True,
                'msg': task.info.error.msg,
                'clone_method': 'InstantClone_Task'
            }
            return kwargs

        clone = task.info.result
        vm_facts = gather_vm_facts(self.content, clone)
        return {
            'changed': True,
            'failed': False,
            'instance': vm_facts,
            'clone_method': 'InstantClone_Task'
        }


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        name=dict(type='str'),
        name_match=dict(type='str', choices=['first', 'last'], default='first'),
        uuid=dict(type='str'),
        moid=dict(type='str'),
        use_instance_uuid=dict(type='bool', default=False),
        folder=dict(type='str'),
        datacenter=dict(required=True, type='str'),
        clone_name=dict(required=True, type='str'),
        customvalues=dict(type='list', default=[]),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_one_of=[
            ['name', 'uuid', 'moid']
        ],
    )

    result = {'failed': False, 'changed': False}

    if module.params['folder']:
        # FindByInventoryPath() does not require an absolute path
        # so we should leave the input folder path unmodified
        module.params['folder'] = module.params['folder'].rstrip('/')

    pyv = PyVmomiHelper(module)
    vm = pyv.get_vm()

    if not vm:
        vm_id = (module.params.get('uuid') or module.params.get('name') or module.params.get('moid'))
        module.fail_json(msg="Unable to find any VM with the identifier: %s" % vm_id)

    if not module.params['clone_name']:
        module.fail_json(msg='Please specify a name for the new instant clone using the clone_name parameter.')

    if module.check_mode:
        result.update(
            changed=True,
            desired_operation='instantclone_vm',
        )
        module.exit_json(**result)

    result = pyv.deploy_instantclone(vm)

    if result['failed']:
        module.fail_json(**result)
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()
