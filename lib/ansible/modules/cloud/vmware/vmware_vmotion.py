#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Bede Carroll <bc+github () bedecarroll.com>

# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
# Copyright: (c) 2018, Ansible Project
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: vmware_vmotion
short_description: Move a virtual machine using vMotion, and/or its vmdks using storage vMotion.
description:
    - Using VMware vCenter, move a virtual machine using vMotion to a different
      host, and/or its vmdks to another datastore using storage vMotion.
version_added: 2.2
author:
- Bede Carroll (@bedecarroll)
- Olivier Boukili (@oboukili)
notes:
    - Tested on vSphere 6.0
requirements:
    - "python >= 2.6"
    - pyVmomi
options:
    vm_name:
      description:
      - Name of the VM to perform a vMotion on.
      - This is required parameter, if C(vm_uuid) is not set.
      - Version 2.6 onwards, this parameter is not a required parameter, unlike the previous versions.
      aliases: ['vm']
      type: str
    vm_uuid:
      description:
      - UUID of the virtual machine to perform a vMotion operation on.
      - This is a required parameter, if C(vm_name) or C(moid) is not set.
      aliases: ['uuid']
      version_added: 2.7
      type: str
    moid:
      description:
      - Managed Object ID of the instance to manage if known, this is a unique identifier only within a single vCenter instance.
      - This is required if C(vm_name) or C(vm_uuid) is not supplied.
      version_added: '2.9'
      type: str
    use_instance_uuid:
      description:
      - Whether to use the VMware instance UUID rather than the BIOS UUID.
      default: no
      type: bool
      version_added: '2.8'
    destination_host:
      description:
      - Name of the destination host the virtual machine should be running on.
      - Version 2.6 onwards, this parameter is not a required parameter, unlike the previous versions.
      aliases: ['destination']
      type: str
    destination_datastore:
      description:
      - "Name of the destination datastore the virtual machine's vmdk should be moved on."
      aliases: ['datastore']
      version_added: 2.7
      type: str
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: Perform vMotion of virtual machine
  vmware_vmotion:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    validate_certs: no
    vm_name: 'vm_name_as_per_vcenter'
    destination_host: 'destination_host_as_per_vcenter'
  delegate_to: localhost

- name: Perform vMotion of virtual machine
  vmware_vmotion:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    validate_certs: no
    moid: vm-42
    destination_host: 'destination_host_as_per_vcenter'
  delegate_to: localhost

- name: Perform storage vMotion of of virtual machine
  vmware_vmotion:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    validate_certs: no
    vm_name: 'vm_name_as_per_vcenter'
    destination_datastore: 'destination_datastore_as_per_vcenter'
  delegate_to: localhost

- name: Perform storage vMotion and host vMotion of virtual machine
  vmware_vmotion:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    validate_certs: no
    vm_name: 'vm_name_as_per_vcenter'
    destination_host: 'destination_host_as_per_vcenter'
    destination_datastore: 'destination_datastore_as_per_vcenter'
  delegate_to: localhost
'''

RETURN = '''
running_host:
    description: List the host the virtual machine is registered to
    returned: changed or success
    type: str
    sample: 'host1.example.com'
'''

try:
    from pyVmomi import vim, VmomiSupport
except ImportError:
    pass

from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import (PyVmomi, find_hostsystem_by_name,
                                         find_vm_by_id, find_datastore_by_name,
                                         vmware_argument_spec, wait_for_task, TaskError)


class VmotionManager(PyVmomi):
    def __init__(self, module):
        super(VmotionManager, self).__init__(module)
        self.vm = None
        self.vm_uuid = self.params.get('vm_uuid', None)
        self.use_instance_uuid = self.params.get('use_instance_uuid', False)
        self.vm_name = self.params.get('vm_name', None)
        self.moid = self.params.get('moid') or None
        result = dict()

        self.get_vm()
        if self.vm is None:
            vm_id = self.vm_uuid or self.vm_name or self.moid
            self.module.fail_json(msg="Failed to find the virtual machine with %s" % vm_id)

        # Get Destination Host System if specified by user
        dest_host_name = self.params.get('destination_host', None)
        self.host_object = None
        if dest_host_name is not None:
            self.host_object = find_hostsystem_by_name(content=self.content,
                                                       hostname=dest_host_name)

        # Get Destination Datastore if specified by user
        dest_datastore = self.params.get('destination_datastore', None)
        self.datastore_object = None
        if dest_datastore is not None:
            self.datastore_object = find_datastore_by_name(content=self.content,
                                                           datastore_name=dest_datastore)

        # At-least one of datastore, host system is required to migrate
        if self.datastore_object is None and self.host_object is None:
            self.module.fail_json(msg="Unable to find destination datastore"
                                      " and destination host system.")

        # Check if datastore is required, this check is required if destination
        # and source host system does not share same datastore.
        host_datastore_required = []
        for vm_datastore in self.vm.datastore:
            if self.host_object and vm_datastore not in self.host_object.datastore:
                host_datastore_required.append(True)
            else:
                host_datastore_required.append(False)

        if any(host_datastore_required) and dest_datastore is None:
            msg = "Destination host system does not share" \
                  " datastore ['%s'] with source host system ['%s'] on which" \
                  " virtual machine is located.  Please specify destination_datastore" \
                  " to rectify this problem." % ("', '".join([ds.name for ds in self.host_object.datastore]),
                                                 "', '".join([ds.name for ds in self.vm.datastore]))

            self.module.fail_json(msg=msg)

        storage_vmotion_needed = True
        change_required = True

        if self.host_object and self.datastore_object:
            # We have both host system and datastore object
            if not self.datastore_object.summary.accessible:
                # Datastore is not accessible
                self.module.fail_json(msg='Destination datastore %s is'
                                          ' not accessible.' % dest_datastore)

            if self.datastore_object not in self.host_object.datastore:
                # Datastore is not associated with host system
                self.module.fail_json(msg="Destination datastore %s provided"
                                          " is not associated with destination"
                                          " host system %s. Please specify"
                                          " datastore value ['%s'] associated with"
                                          " the given host system." % (dest_datastore,
                                                                       dest_host_name,
                                                                       "', '".join([ds.name for ds in self.host_object.datastore])))

            if self.vm.runtime.host.name == dest_host_name and dest_datastore in [ds.name for ds in self.vm.datastore]:
                change_required = False

        if self.host_object and self.datastore_object is None:
            if self.vm.runtime.host.name == dest_host_name:
                # VM is already located on same host
                change_required = False

            storage_vmotion_needed = False

        elif self.datastore_object and self.host_object is None:
            if self.datastore_object in self.vm.datastore:
                # VM is already located on same datastore
                change_required = False

            if not self.datastore_object.summary.accessible:
                # Datastore is not accessible
                self.module.fail_json(msg='Destination datastore %s is'
                                          ' not accessible.' % dest_datastore)

        if module.check_mode:
            result['running_host'] = module.params['destination_host']
            result['changed'] = True
            module.exit_json(**result)

        if change_required:
            # Migrate VM and get Task object back
            task_object = self.migrate_vm()
            # Wait for task to complete
            try:
                wait_for_task(task_object)
            except TaskError as task_error:
                self.module.fail_json(msg=to_native(task_error))
            # If task was a success the VM has moved, update running_host and complete module
            if task_object.info.state == vim.TaskInfo.State.success:
                # The storage layout is not automatically refreshed, so we trigger it to get coherent module return values
                if storage_vmotion_needed:
                    self.vm.RefreshStorageInfo()
                result['running_host'] = module.params['destination_host']
                result['changed'] = True
                module.exit_json(**result)
            else:
                msg = 'Unable to migrate virtual machine due to an error, please check vCenter'
                if task_object.info.error is not None:
                    msg += " : %s" % task_object.info.error
                module.fail_json(msg=msg)
        else:
            try:
                host = self.vm.summary.runtime.host
                result['running_host'] = host.summary.config.name
            except vim.fault.NoPermission:
                result['running_host'] = 'NA'
            result['changed'] = False
            module.exit_json(**result)

    def migrate_vm(self):
        """
        Migrate virtual machine and return the task.
        """
        relocate_spec = vim.vm.RelocateSpec(host=self.host_object,
                                            datastore=self.datastore_object)
        task_object = self.vm.Relocate(relocate_spec)
        return task_object

    def get_vm(self):
        """
        Find unique virtual machine either by UUID or Name.
        Returns: virtual machine object if found, else None.

        """
        vms = []
        if self.vm_uuid:
            if not self.use_instance_uuid:
                vm_obj = find_vm_by_id(self.content, vm_id=self.params['vm_uuid'], vm_id_type="uuid")
            elif self.use_instance_uuid:
                vm_obj = find_vm_by_id(self.content, vm_id=self.params['vm_uuid'], vm_id_type="instance_uuid")
            vms = [vm_obj]
        elif self.vm_name:
            objects = self.get_managed_objects_properties(vim_type=vim.VirtualMachine, properties=['name'])
            for temp_vm_object in objects:
                if len(temp_vm_object.propSet) != 1:
                    continue
                if temp_vm_object.obj.name == self.vm_name:
                    vms.append(temp_vm_object.obj)
                    break
        elif self.moid:
            vm_obj = VmomiSupport.templateOf('VirtualMachine')(self.moid, self.si._stub)
            if vm_obj:
                vms.append(vm_obj)

        if len(vms) > 1:
            self.module.fail_json(msg="Multiple virtual machines with same name %s found."
                                      " Please specify vm_uuid instead of vm_name." % self.vm_name)

        self.vm = vms[0]


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        dict(
            vm_name=dict(aliases=['vm']),
            vm_uuid=dict(aliases=['uuid']),
            moid=dict(type='str'),
            use_instance_uuid=dict(type='bool', default=False),
            destination_host=dict(aliases=['destination']),
            destination_datastore=dict(aliases=['datastore'])
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_one_of=[
            ['destination_host', 'destination_datastore'],
            ['vm_uuid', 'vm_name', 'moid'],
        ],
        mutually_exclusive=[
            ['vm_uuid', 'vm_name', 'moid'],
        ],
    )

    vmotion_manager = VmotionManager(module)


if __name__ == '__main__':
    main()
