#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Ansible Project
# This module is also sponsored by E.T.A.I. (www.etai.fr)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: vmware_guest_snapshot
short_description: Manages virtual machines snapshots in vCenter
description:
    - This module can be used to create, delete and update snapshot(s) of the given virtual machine.
    - All parameters and VMware object names are case sensitive.
version_added: 2.3
author:
    - Loic Blot (@nerzhul) <loic.blot@unix-experience.fr>
notes:
    - Tested on vSphere 5.5, 6.0 and 6.5
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
   state:
     description:
     - Manage snapshot(s) attached to a specific virtual machine.
     - If set to C(present) and snapshot absent, then will create a new snapshot with the given name.
     - If set to C(present) and snapshot present, then no changes are made.
     - If set to C(absent) and snapshot present, then snapshot with the given name is removed.
     - If set to C(absent) and snapshot absent, then no changes are made.
     - If set to C(revert) and snapshot present, then virtual machine state is reverted to the given snapshot.
     - If set to C(revert) and snapshot absent, then no changes are made.
     - If set to C(remove_all) and snapshot(s) present, then all snapshot(s) will be removed.
     - If set to C(remove_all) and snapshot(s) absent, then no changes are made.
     required: True
     choices: ['present', 'absent', 'revert', 'remove_all']
     default: 'present'
   name:
     description:
     - Name of the virtual machine to work with.
     - This is required parameter, if C(uuid) is not supplied.
   name_match:
     description:
     - If multiple VMs matching the name, use the first or last found.
     default: 'first'
     choices: ['first', 'last']
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
   folder:
     description:
     - Destination folder, absolute or relative path to find an existing guest.
     - This is required parameter, if C(name) is supplied.
     - The folder should include the datacenter. ESX's datacenter is ha-datacenter.
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
   datacenter:
     description:
     - Destination datacenter for the deploy operation.
     required: True
   snapshot_name:
     description:
     - Sets the snapshot name to manage.
     - This param is required only if state is not C(remove_all)
   description:
     description:
     - Define an arbitrary description to attach to snapshot.
     default: ''
   quiesce:
     description:
     - If set to C(true) and virtual machine is powered on, it will quiesce the file system in virtual machine.
     - Note that VMWare Tools are required for this flag.
     - If virtual machine is powered off or VMware Tools are not available, then this flag is set to C(false).
     - If virtual machine does not provide capability to take quiesce snapshot, then this flag is set to C(false).
     required: False
     version_added: "2.4"
     type: bool
     default: False
   memory_dump:
     description:
     - If set to C(true), memory dump of virtual machine is also included in snapshot.
     - Note that memory snapshots take time and resources, this will take longer time to create.
     - If virtual machine does not provide capability to take memory snapshot, then this flag is set to C(false).
     required: False
     version_added: "2.4"
     type: bool
     default: False
   remove_children:
     description:
     - If set to C(true) and state is set to C(absent), then entire snapshot subtree is set for removal.
     required: False
     version_added: "2.4"
     type: bool
     default: False
   new_snapshot_name:
     description:
     - Value to rename the existing snapshot to.
     version_added: "2.5"
   new_description:
     description:
     - Value to change the description of an existing snapshot to.
     version_added: "2.5"
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
  - name: Create a snapshot
    vmware_guest_snapshot:
      hostname: "{{ vcenter_hostname }}"
      username: "{{ vcenter_username }}"
      password: "{{ vcenter_password }}"
      datacenter: "{{ datacenter_name }}"
      folder: "/{{ datacenter_name }}/vm/"
      name: "{{ guest_name }}"
      state: present
      snapshot_name: snap1
      description: snap1_description
    delegate_to: localhost

  - name: Remove a snapshot
    vmware_guest_snapshot:
      hostname: "{{ vcenter_hostname }}"
      username: "{{ vcenter_username }}"
      password: "{{ vcenter_password }}"
      datacenter: "{{ datacenter_name }}"
      folder: "/{{ datacenter_name }}/vm/"
      name: "{{ guest_name }}"
      state: absent
      snapshot_name: snap1
    delegate_to: localhost

  - name: Revert to a snapshot
    vmware_guest_snapshot:
      hostname: "{{ vcenter_hostname }}"
      username: "{{ vcenter_username }}"
      password: "{{ vcenter_password }}"
      datacenter: "{{ datacenter_name }}"
      folder: "/{{ datacenter_name }}/vm/"
      name: "{{ guest_name }}"
      state: revert
      snapshot_name: snap1
    delegate_to: localhost

  - name: Remove all snapshots of a VM
    vmware_guest_snapshot:
      hostname: "{{ vcenter_hostname }}"
      username: "{{ vcenter_username }}"
      password: "{{ vcenter_password }}"
      datacenter: "{{ datacenter_name }}"
      folder: "/{{ datacenter_name }}/vm/"
      name: "{{ guest_name }}"
      state: remove_all
    delegate_to: localhost

  - name: Take snapshot of a VM using quiesce and memory flag on
    vmware_guest_snapshot:
      hostname: "{{ vcenter_hostname }}"
      username: "{{ vcenter_username }}"
      password: "{{ vcenter_password }}"
      datacenter: "{{ datacenter_name }}"
      folder: "/{{ datacenter_name }}/vm/"
      name: "{{ guest_name }}"
      state: present
      snapshot_name: dummy_vm_snap_0001
      quiesce: yes
      memory_dump: yes
    delegate_to: localhost

  - name: Remove a snapshot and snapshot subtree
    vmware_guest_snapshot:
      hostname: "{{ vcenter_hostname }}"
      username: "{{ vcenter_username }}"
      password: "{{ vcenter_password }}"
      datacenter: "{{ datacenter_name }}"
      folder: "/{{ datacenter_name }}/vm/"
      name: "{{ guest_name }}"
      state: absent
      remove_children: yes
      snapshot_name: snap1
    delegate_to: localhost

  - name: Rename a snapshot
    vmware_guest_snapshot:
      hostname: "{{ vcenter_hostname }}"
      username: "{{ vcenter_username }}"
      password: "{{ vcenter_password }}"
      datacenter: "{{ datacenter_name }}"
      folder: "/{{ datacenter_name }}/vm/"
      name: "{{ guest_name }}"
      state: present
      snapshot_name: current_snap_name
      new_snapshot_name: im_renamed
      new_description: "{{ new_snapshot_description }}"
    delegate_to: localhost
'''

RETURN = """
snapshot_results:
    description: metadata about the virtual machine snapshots
    returned: always
    type: dict
    sample: {
      "current_snapshot": {
          "creation_time": "2019-04-09T14:40:26.617427+00:00",
          "description": "Snapshot 4 example",
          "id": 4,
          "name": "snapshot4",
          "state": "poweredOff"
      },
      "snapshots": [
          {
              "creation_time": "2019-04-09T14:38:24.667543+00:00",
              "description": "Snapshot 3 example",
              "id": 3,
              "name": "snapshot3",
              "state": "poweredOff"
          },
          {
              "creation_time": "2019-04-09T14:40:26.617427+00:00",
              "description": "Snapshot 4 example",
              "id": 4,
              "name": "snapshot4",
              "state": "poweredOff"
          }
      ]
    }
"""

import time
try:
    from pyVmomi import vim
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.vmware import PyVmomi, list_snapshots, vmware_argument_spec


class PyVmomiHelper(PyVmomi):
    def __init__(self, module):
        super(PyVmomiHelper, self).__init__(module)

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
        # Check if there is a latest snapshot already present as specified by user
        if vm.snapshot is not None:
            snap_obj = self.get_snapshots_by_name_recursively(vm.snapshot.rootSnapshotList,
                                                              self.module.params["snapshot_name"])
            if snap_obj:
                # Snapshot already exists, do not anything.
                self.module.exit_json(changed=False,
                                      msg="Snapshot named [%(snapshot_name)s] already exists and is current." % self.module.params)
        # Check if Virtual Machine provides capabilities for Quiesce and Memory Snapshots
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
            self.module.fail_json(msg="Failed to take snapshot due to VMware Licence"
                                      " restriction : %s" % to_native(exc.msg))
        except Exception as exc:
            self.module.fail_json(msg="Failed to create snapshot of virtual machine"
                                      " %s due to %s" % (self.module.params['name'], to_native(exc)))
        return task

    def rename_snapshot(self, vm):
        if vm.snapshot is None:
            self.module.fail_json(msg="virtual machine - %s doesn't have any"
                                      " snapshots" % (self.module.params.get('uuid') or self.module.params.get('name')))

        snap_obj = self.get_snapshots_by_name_recursively(vm.snapshot.rootSnapshotList,
                                                          self.module.params["snapshot_name"])
        task = None
        if len(snap_obj) == 1:
            snap_obj = snap_obj[0].snapshot
            if self.module.params["new_snapshot_name"] and self.module.params["new_description"]:
                task = snap_obj.RenameSnapshot(name=self.module.params["new_snapshot_name"],
                                               description=self.module.params["new_description"])
            elif self.module.params["new_snapshot_name"]:
                task = snap_obj.RenameSnapshot(name=self.module.params["new_snapshot_name"])
            else:
                task = snap_obj.RenameSnapshot(description=self.module.params["new_description"])
        else:
            self.module.exit_json(
                msg="Couldn't find any snapshots with specified name: %s on VM: %s" %
                    (self.module.params["snapshot_name"],
                     self.module.params.get('uuid') or self.module.params.get('name')))
        return task

    def remove_or_revert_snapshot(self, vm):
        if vm.snapshot is None:
            vm_name = (self.module.params.get('uuid') or self.module.params.get('name'))
            if self.module.params.get('state') == 'revert':
                self.module.fail_json(msg="virtual machine - %s does not"
                                          " have any snapshots to revert to." % vm_name)
            self.module.exit_json(msg="virtual machine - %s doesn't have any"
                                      " snapshots to remove." % vm_name)

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
            self.module.exit_json(msg="Couldn't find any snapshots with"
                                      " specified name: %s on VM: %s" % (self.module.params["snapshot_name"],
                                                                         self.module.params.get('uuid') or self.module.params.get('name')))

        return task

    def apply_snapshot_op(self, vm):
        result = {}
        if self.module.params["state"] == "present":
            if self.module.params["new_snapshot_name"] or self.module.params["new_description"]:
                self.rename_snapshot(vm)
                result = {'changed': True, 'failed': False, 'renamed': True}
                task = None
            else:
                task = self.snapshot_vm(vm)
        elif self.module.params["state"] in ["absent", "revert"]:
            task = self.remove_or_revert_snapshot(vm)
        elif self.module.params["state"] == "remove_all":
            task = vm.RemoveAllSnapshots()
        else:
            # This should not happen
            raise AssertionError()

        if task:
            self.wait_for_task(task)
            if task.info.state == 'error':
                result = {'changed': False, 'failed': True, 'msg': task.info.error.msg}
            else:
                result = {'changed': True, 'failed': False, 'snapshot_results': list_snapshots(vm)}

        return result


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        state=dict(default='present', choices=['present', 'absent', 'revert', 'remove_all']),
        name=dict(type='str'),
        name_match=dict(type='str', choices=['first', 'last'], default='first'),
        uuid=dict(type='str'),
        use_instance_uuid=dict(type='bool', default=False),
        folder=dict(type='str'),
        datacenter=dict(required=True, type='str'),
        snapshot_name=dict(type='str'),
        description=dict(type='str', default=''),
        quiesce=dict(type='bool', default=False),
        memory_dump=dict(type='bool', default=False),
        remove_children=dict(type='bool', default=False),
        new_snapshot_name=dict(type='str'),
        new_description=dict(type='str'),
    )
    module = AnsibleModule(argument_spec=argument_spec,
                           required_together=[['name', 'folder']],
                           required_one_of=[['name', 'uuid']],
                           )

    if module.params['folder']:
        # FindByInventoryPath() does not require an absolute path
        # so we should leave the input folder path unmodified
        module.params['folder'] = module.params['folder'].rstrip('/')

    pyv = PyVmomiHelper(module)
    # Check if the VM exists before continuing
    vm = pyv.get_vm()

    if not vm:
        # If UUID is set, getvm select UUID, show error message accordingly.
        module.fail_json(msg="Unable to manage snapshots for non-existing VM %s" % (module.params.get('uuid') or
                                                                                    module.params.get('name')))

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
