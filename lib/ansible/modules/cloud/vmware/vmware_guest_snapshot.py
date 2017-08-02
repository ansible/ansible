#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This module is also sponsored by E.T.A.I. (www.etai.fr)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: vmware_guest_snapshot
short_description: Manages virtual machines snapshots in vcenter
description:
    - Create virtual machines snapshots
version_added: 2.3
author:
    - James Tanner (@jctanner) <tanner.jc@gmail.com>
    - Loic Blot (@nerzhul) <loic.blot@unix-experience.fr>
notes:
    - Tested on vSphere 5.5
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
   state:
        description:
            - Manage snapshots attached to a specific virtual machine.
        required: True
        choices: ['present', 'absent', 'revert', 'remove_all']
   name:
        description:
            - Name of the VM to work with
            - This is required if uuid is not supplied.
   name_match:
        description:
            - If multiple VMs matching the name, use the first or last found
        default: 'first'
        choices: ['first', 'last']
   uuid:
        description:
            - UUID of the instance to manage if known, this is VMware's unique identifier.
            - This is required if name is not supplied.
   folder:
        description:
            - Destination folder, absolute or relative path to find an existing guest.
            - This is required if name is supplied.
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
            - '   folder: vm/folder2'
            - '   folder: folder2'
        default: /vm
   datacenter:
        description:
            - Destination datacenter for the deploy operation
        required: True
   snapshot_name:
        description:
        - Sets the snapshot name to manage.
        - This param is required only if state is not C(remove_all)
   description:
        description:
        - Define an arbitrary description to attach to snapshot.
   quiesce:
        description:
            - If set to C(true) and virtual machine is powered on, it will quiesce the
              file system in virtual machine.
            - Note that VMWare Tools are required for this flag.
            - If virtual machine is powered off or VMware Tools are not available, then
              this flag is set to C(false).
            - If virtual machine does not provide capability to take quiesce snapshot, then
              this flag is set to C(false).
        required: False
        version_added: "2.4"
   memory_dump:
        description:
            - If set to C(true), memory dump of virtual machine is also included in snapshot.
            - Note that memory snapshots take time and resources, this will take longer time to create.
            - If virtual machine does not provide capability to take memory snapshot, then
              this flag is set to C(false).
        required: False
        version_added: "2.4"
   remove_children:
        description:
            - If set to C(true) and state is set to C(absent), then entire snapshot subtree is set
              for removal.
        required: False
        version_added: "2.4"
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
  - name: Create snapshot
    vmware_guest_snapshot:
      hostname: 192.168.1.209
      username: administrator@vsphere.local
      password: vmware
      name: dummy_vm
      state: present
      snapshot_name: snap1
      description: snap1_description
    delegate_to: localhost

  - name: Remove a snapshot
    vmware_guest_snapshot:
      hostname: 192.168.1.209
      username: administrator@vsphere.local
      password: vmware
      name: dummy_vm
      state: remove
      snapshot_name: snap1
    delegate_to: localhost

  - name: Revert to a snapshot
    vmware_guest_snapshot:
      hostname: 192.168.1.209
      username: administrator@vsphere.local
      password: vmware
      name: dummy_vm
      state: revert
      snapshot_name: snap1
    delegate_to: localhost

  - name: Remove all snapshots of a VM
    vmware_guest_snapshot:
      hostname: 192.168.1.209
      username: administrator@vsphere.local
      password: vmware
      name: dummy_vm
      state: remove_all
    delegate_to: localhost

  - name: Take snapshot of a VM using quiesce and memory flag on
    vmware_guest_snapshot:
      hostname: 192.168.1.209
      username: administrator@vsphere.local
      password: vmware
      name: dummy_vm
      state: present
      snapshot_name: dummy_vm_snap_0001
      quiesce: True
      memory_dump: True
    delegate_to: localhost

  - name: Remove a snapshot and snapshot subtree
    vmware_guest_snapshot:
      hostname: 192.168.1.209
      username: administrator@vsphere.local
      password: vmware
      name: dummy_vm
      state: remove
      remove_children: True
      snapshot_name: snap1
    delegate_to: localhost
'''

RETURN = """
instance:
    description: metadata about the new virtualmachine
    returned: always
    type: dict
    sample: None
"""

import time

HAS_PYVMOMI = False
try:
    import pyVmomi
    from pyVmomi import vim

    HAS_PYVMOMI = True
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.vmware import connect_to_api, vmware_argument_spec, find_vm_by_id


class PyVmomiHelper(object):
    def __init__(self, module):
        if not HAS_PYVMOMI:
            module.fail_json(msg='pyvmomi module required')

        self.module = module
        self.params = module.params
        self.content = connect_to_api(self.module)

    def getvm(self, name=None, uuid=None, folder=None):
        vm = None
        match_first = False
        if uuid:
            vm = find_vm_by_id(self.content, uuid, vm_id_type="uuid")
        elif folder and name:
            if self.params['name_match'] == 'first':
                match_first = True
            vm = find_vm_by_id(self.content, vm_id=name, vm_id_type="inventory_path", folder=folder, match_first=match_first)
        return vm

    @staticmethod
    def wait_for_task(task):
        # https://www.vmware.com/support/developer/vc-sdk/visdk25pubs/ReferenceGuide/vim.Task.html
        # https://www.vmware.com/support/developer/vc-sdk/visdk25pubs/ReferenceGuide/vim.TaskInfo.html
        # https://github.com/virtdevninja/pyvmomi-community-samples/blob/master/samples/tools/tasks.py
        while task.info.state not in ['success', 'error']:
            time.sleep(1)

    def get_snapshots_by_name_recursively(self, snapshots, snapname):
        snap_obj = []
        for snapshot in snapshots:
            if snapshot.name == snapname:
                snap_obj.append(snapshot)
            else:
                snap_obj = snap_obj + self.get_snapshots_by_name_recursively(snapshot.childSnapshotList, snapname)
        return snap_obj

    def snapshot_vm(self, vm):
        memory_dump = False
        quiesce = False
        # Check if Virtual Machine provides capabilities for Quiesce and Memory
        # Snapshots
        if vm.capability.quiescedSnapshotsSupported:
            quiesce = self.module.params['quiesce']
        if vm.capability.memorySnapshotsSupported:
            memory_dump = self.module.params['memory_dump']

        task = None
        try:
            task = vm.CreateSnapshot(self.module.params["snapshot_name"],
                                     self.module.params["description"],
                                     memory_dump,
                                     quiesce)
        except vim.fault.RestrictedVersion as exc:
            self.module.fail_json(msg="Failed to take snapshot due to VMware Licence: %s" % to_native(exc.msg))
        except Exception as exc:
            self.module.fail_json(msg="Failed to create snapshot of VM %s due to %s" % (self.module.params['name'], to_native(exc.msg)))

        return task

    def remove_or_revert_snapshot(self, vm):
        if vm.snapshot is None:
            self.module.exit_json(msg="VM - %s doesn't have any snapshots" % self.module.params["name"])

        snap_obj = self.get_snapshots_by_name_recursively(vm.snapshot.rootSnapshotList,
                                                          self.module.params["snapshot_name"])
        task = None
        if len(snap_obj) == 1:
            snap_obj = snap_obj[0].snapshot
            if self.module.params["state"] == "absent":
                # Remove subtree depending upon the user input
                remove_children = self.module.params.get('remove_children', False)
                task = snap_obj.RemoveSnapshot_Task(remove_children)
            elif self.module.params["state"] == "revert":
                task = snap_obj.RevertToSnapshot_Task()
        else:
            self.module.exit_json(
                msg="Couldn't find any snapshots with specified name: %s on VM: %s" %
                    (self.module.params["snapshot_name"], self.module.params["name"]))

        return task

    def apply_snapshot_op(self, vm):
        result = {}
        if self.module.params["state"] == "present":
            task = self.snapshot_vm(vm)
        elif self.module.params["state"] in ["absent", "revert"]:
            task = self.remove_or_revert_snapshot(vm)
        elif self.module.params["state"] == "remove_all":
            task = vm.RemoveAllSnapshots()
        else:
            # This should not happen
            assert False

        if task:
            self.wait_for_task(task)
            if task.info.state == 'error':
                result = {'changed': False, 'failed': True, 'msg': task.info.error.msg}
            else:
                result = {'changed': True, 'failed': False}

        return result


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        state=dict(default='present', choices=['present', 'absent', 'revert', 'remove_all']),
        name=dict(required=True, type='str'),
        name_match=dict(type='str', choices=['first', 'last'], default='first'),
        uuid=dict(type='str'),
        folder=dict(type='str', default='/vm'),
        datacenter=dict(required=True, type='str'),
        snapshot_name=dict(type='str'),
        description=dict(type='str', default=''),
        quiesce=dict(type='bool', default=False),
        memory_dump=dict(type='bool', default=False),
        remove_children=dict(type='bool', default=False),
    )
    module = AnsibleModule(argument_spec=argument_spec, required_one_of=[['name', 'uuid']])

    # FindByInventoryPath() does not require an absolute path
    # so we should leave the input folder path unmodified
    module.params['folder'] = module.params['folder'].rstrip('/')

    pyv = PyVmomiHelper(module)
    # Check if the VM exists before continuing
    vm = pyv.getvm(name=module.params['name'],
                   folder=module.params['folder'],
                   uuid=module.params['uuid'])

    if not vm:
        # If UUID is set, getvm select UUID, show error message accordingly.
        if module.params['uuid'] is not None:
            module.fail_json(msg="Unable to manage snapshots for non-existing VM %(uuid)s" % module.params)
        else:
            module.fail_json(msg="Unable to manage snapshots for non-existing VM %(name)s" % module.params)

    if not module.params['snapshot_name'] and module.params['state'] != 'remove_all':
        module.fail_json(msg="snapshot_name param is required when state is '%(state)s'" % module.params)

    result = pyv.apply_snapshot_op(vm)

    if 'failed' not in result:
        result['failed'] = False

    if result['failed']:
        module.fail_json(**result)
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()
