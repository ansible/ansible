#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
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
module: vcenter_folder
short_description: Manage folders on given datacenter
description:
- This module can be used to create, delete, move and rename folder on then given datacenter.
version_added: '2.5'
author:
- Abhijeet Kasurde (@Akasurde)
notes:
- Tested on vSphere 6.5
requirements:
- python >= 2.6
- PyVmomi
options:
  datacenter:
    description:
    - Name of the datacenter.
    required: True
  folder_name:
    description:
    - Name of folder to be managed.
    - This is case sensitive parameter.
    - Folder name should be under 80 characters. This is a VMware restriction.
    required: True
  parent_folder:
    description:
    - Name of the parent folder under which new folder needs to be created.
    - This is case sensitive parameter.
    - Please specify unique folder name as there is no way to detect duplicate names.
    - "If user wants to create a folder under '/DC0/vm/vm_folder', this value will be 'vm_folder'."
    required: False
  folder_type:
    description:
    - This is type of folder.
    - "If set to C(vm), then 'VM and Template Folder' is created under datacenter."
    - "If set to C(host), then 'Host and Cluster Folder' is created under datacenter."
    - "If set to C(datastore), then 'Storage Folder' is created under datacenter."
    - "If set to C(network), then 'Network Folder' is created under datacenter."
    - This parameter is required, if C(state) is set to C(present) and parent_folder is absent.
    - This option is ignored, if C(parent_folder) is set.
    default: vm
    required: False
    choices: [ datastore, host, network, vm ]
  state:
    description:
    - State of folder.
    - If set to C(present) without parent folder parameter, then folder with C(folder_type) is created.
    - If set to C(present) with parent folder parameter,  then folder in created under parent folder. C(folder_type) is ignored.
    - If set to C(absent), then folder is unregistered and destroyed.
    default: present
    choices: [ present, absent ]
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Create a VM folder on given datacenter
  vcenter_folder:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter: datacenter_name
    folder_name: sample_vm_folder
    folder_type: vm
    state: present
  register: vm_folder_creation_result

- name: Create a datastore folder on given datacenter
  vcenter_folder:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter: datacenter_name
    folder_name: sample_datastore_folder
    folder_type: datastore
    state: present
  register: datastore_folder_creation_result

- name: Create a sub folder under VM folder on given datacenter
  vcenter_folder:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter: datacenter_name
    folder_name: sample_sub_folder
    parent_folder: vm_folder
    state: present
  register: sub_folder_creation_result

- name: Delete a VM folder on given datacenter
  vcenter_folder:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter: datacenter_name
    folder_name: sample_vm_folder
    folder_type: vm
    state: absent
  register: vm_folder_deletion_result

'''

RETURN = r'''
result:
    description:
    - string stating about result
    returned: success
    type: string
    sample: "Folder 'sub_network_folder' of type 'vm' created under vm_folder successfully."
'''

try:
    from pyVmomi import vim, vmodl
except ImportError as e:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import vmware_argument_spec, PyVmomi, find_datacenter_by_name, wait_for_task, get_all_objs
from ansible.module_utils._text import to_native


class VmwareFolderManager(PyVmomi):
    def __init__(self, module):
        super(VmwareFolderManager, self).__init__(module)
        datacenter_name = self.params.get('datacenter', None)
        self.datacenter_obj = find_datacenter_by_name(self.content, datacenter_name=datacenter_name)
        if self.datacenter_obj is None:
            self.module.fail_json(msg="Failed to find datacenter %s" % datacenter_name)

    def ensure(self):
        """
        Function to manage internal state management
        Returns:

        """
        state = self.module.params.get('state')
        folder_type = self.module.params.get('folder_type')
        folder_name = self.module.params.get('folder_name')
        parent_folder = self.module.params.get('parent_folder', None)
        results = dict(changed=False, result=dict())
        if state == 'present':
            # Create a new folder
            try:
                if parent_folder:
                    folder = self.get_folder_by_name(folder_name=parent_folder)
                    if folder and not self.get_folder_by_name(folder_name=folder_name, parent_folder=folder):
                        folder.CreateFolder(folder_name)
                        results['changed'] = True
                        results['result'] = "Folder '%s' of type '%s' created under %s" \
                                            " successfully." % (folder_name, folder_type, parent_folder)
                    elif folder is None:
                        self.module.fail_json(msg="Failed to find the parent folder %s"
                                                  " for folder %s" % (parent_folder, folder_name))
                else:
                    datacenter_folder_type = {
                        'vm': self.datacenter_obj.vmFolder,
                        'host': self.datacenter_obj.hostFolder,
                        'datastore': self.datacenter_obj.datastoreFolder,
                        'network': self.datacenter_obj.networkFolder,
                    }
                    datacenter_folder_type[folder_type].CreateFolder(folder_name)
                    results['changed'] = True
                    results['result'] = "Folder '%s' of type '%s' created successfully" % (folder_name, folder_type)
            except vim.fault.DuplicateName as duplicate_name:
                # To be consistent with the other vmware modules, We decided to accept this error
                # and the playbook should simply carry on with other tasks.
                # User will have to take care of this exception
                # https://github.com/ansible/ansible/issues/35388#issuecomment-362283078
                results['changed'] = False
                results['result'] = "Failed to create folder as another object has same name" \
                                    " in the same target folder : %s" % to_native(duplicate_name.msg)
            except vim.fault.InvalidName as invalid_name:
                self.module.fail_json(msg="Failed to create folder as folder name is not a valid "
                                          "entity name : %s" % to_native(invalid_name.msg))
            except Exception as general_exc:
                self.module.fail_json(msg="Failed to create folder due to generic"
                                          " exception : %s " % to_native(general_exc))
            self.module.exit_json(**results)
        elif state == 'absent':
            folder_obj = self.get_folder_by_name(folder_name=folder_name)
            if folder_obj:
                try:
                    task = folder_obj.UnregisterAndDestroy()
                    results['changed'], results['result'] = wait_for_task(task=task)
                except vim.fault.ConcurrentAccess as concurrent_access:
                    self.module.fail_json(msg="Failed to remove folder as another client"
                                              " modified folder before this operation : %s" % to_native(concurrent_access.msg))
                except vim.fault.InvalidState as invalid_state:
                    self.module.fail_json(msg="Failed to remove folder as folder is in"
                                              " invalid state" % to_native(invalid_state.msg))
                except Exception as e:
                    self.module.fail_json(msg="Failed to remove folder due to generic"
                                              " exception %s " % to_native(e))
            self.module.exit_json(**results)

    def get_folder_by_name(self, folder_name, parent_folder=None):
        """
        Function to get managed object of folder by name
        Returns: Managed object of folder by name

        """
        folder_objs = get_all_objs(self.content, [vim.Folder], parent_folder)
        for folder in folder_objs:
            if folder.name == folder_name:
                return folder

        return None


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        datacenter=dict(type='str', required=True),
        folder_name=dict(type='str', required=True),
        parent_folder=dict(type='str', required=False),
        state=dict(type='str',
                   choices=['present', 'absent'],
                   default='present'),
        folder_type=dict(type='str',
                         default='vm',
                         choices=['datastore', 'host', 'network', 'vm'],
                         required=False),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=False,
    )

    if len(module.params.get('folder_name')) > 79:
        module.fail_json(msg="Failed to manage folder as folder_name can only contain 80 characters.")

    vcenter_folder_mgr = VmwareFolderManager(module)
    vcenter_folder_mgr.ensure()


if __name__ == "__main__":
    main()
