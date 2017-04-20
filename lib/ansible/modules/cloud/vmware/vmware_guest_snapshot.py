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

  - name: Remove a snapshot
    vmware_guest_snapshot:
      hostname: 192.168.1.209
      username: administrator@vsphere.local
      password: vmware
      name: dummy_vm
      state: remove
      snapshot_name: snap1

  - name: Revert to a snapshot
    vmware_guest_snapshot:
      hostname: 192.168.1.209
      username: administrator@vsphere.local
      password: vmware
      name: dummy_vm
      state: revert
      snapshot_name: snap1

  - name: Remove all snapshots of a VM
    vmware_guest_snapshot:
      hostname: 192.168.1.209
      username: administrator@vsphere.local
      password: vmware
      name: dummy_vm
      state: remove_all
'''

RETURN = """
instance:
    descripton: metadata about the new virtualmachine
    returned: always
    type: dict
    sample: None
"""

import os
import time

# import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils.six import iteritems
from ansible.module_utils.vmware import connect_to_api

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
        dump_memory = False
        quiesce = False
        return vm.CreateSnapshot(self.module.params["snapshot_name"],
                                 self.module.params["description"],
                                 dump_memory,
                                 quiesce)

    def remove_or_revert_snapshot(self, vm):
        if vm.snapshot is None:
            self.module.exit_json(msg="VM - %s doesn't have any snapshots" % self.module.params["name"])

        snap_obj = self.get_snapshots_by_name_recursively(vm.snapshot.rootSnapshotList,
                                                          self.module.params["snapshot_name"])
        task = None
        if len(snap_obj) == 1:
            snap_obj = snap_obj[0].snapshot
            if self.module.params["state"] == "absent":
                task = snap_obj.RemoveSnapshot_Task(True)
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
