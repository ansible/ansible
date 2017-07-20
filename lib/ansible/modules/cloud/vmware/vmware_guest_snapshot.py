#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This module is also sponsored by E.T.A.I. (www.etai.fr)
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
        required: True
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
            - Define instance folder location.
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

import os
import time

# import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import connect_to_api
from ansible.module_utils._text import to_native

try:
    import json
except ImportError:
    import simplejson as json

HAS_PYVMOMI = False
try:
    import pyVmomi
    from pyVmomi import vim

    HAS_PYVMOMI = True
except ImportError:
    pass


class PyVmomiHelper(object):
    def __init__(self, module):
        if not HAS_PYVMOMI:
            module.fail_json(msg='pyvmomi module required')

        self.module = module
        self.params = module.params
        self.si = None
        self.content = connect_to_api(self.module)
        self.change_detected = False

    def getvm(self, name=None, uuid=None, folder=None):

        # https://www.vmware.com/support/developer/vc-sdk/visdk2xpubs/ReferenceGuide/vim.SearchIndex.html
        # self.si.content.searchIndex.FindByInventoryPath('DC1/vm/test_folder')

        vm = None

        if uuid:
            vm = self.content.searchIndex.FindByUuid(uuid=uuid, vmSearch=True)
        elif folder:
            # Build the absolute folder path to pass into the search method
            if not self.params['folder'].startswith('/'):
                self.module.fail_json(msg="Folder %(folder)s needs to be an absolute path, starting with '/'." % self.params)
            searchpath = '%(datacenter)s%(folder)s' % self.params

            # get all objects for this path ...
            f_obj = self.content.searchIndex.FindByInventoryPath(searchpath)
            if f_obj:
                if isinstance(f_obj, vim.Datacenter):
                    f_obj = f_obj.vmFolder
                for c_obj in f_obj.childEntity:
                    if not isinstance(c_obj, vim.VirtualMachine):
                        continue
                    if c_obj.name == name:
                        vm = c_obj
                        if self.params['name_match'] == 'first':
                            break

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
    module = AnsibleModule(
        argument_spec=dict(
            hostname=dict(
                type='str',
                default=os.environ.get('VMWARE_HOST')
            ),
            username=dict(
                type='str',
                default=os.environ.get('VMWARE_USER')
            ),
            password=dict(
                type='str', no_log=True,
                default=os.environ.get('VMWARE_PASSWORD')
            ),
            state=dict(
                required=False,
                choices=['present', 'absent', 'revert', 'remove_all'],
                default='present'),
            validate_certs=dict(required=False, type='bool', default=True),
            name=dict(required=True, type='str'),
            name_match=dict(required=False, type='str', default='first'),
            uuid=dict(required=False, type='str'),
            folder=dict(required=False, type='str', default='/vm'),
            datacenter=dict(required=True, type='str'),
            snapshot_name=dict(required=False, type='str'),
            description=dict(required=False, type='str', default=''),
            quiesce=dict(type='bool', default=False),
            memory_dump=dict(type='bool', default=False),
            remove_children=dict(type='bool', default=False),
        ),
    )

    # Prepend /vm if it was missing from the folder path, also strip trailing slashes
    if not module.params['folder'].startswith('/vm') and module.params['folder'].startswith('/'):
        module.params['folder'] = '/vm%(folder)s' % module.params
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
