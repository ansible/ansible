#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: vmware_guest_find
short_description: Find the folder path(s) for a virtual machine by name or UUID
description:
    - Find the folder path(s) for a virtual machine by name or UUID
version_added: 2.4
author:
    - James Tanner <tanner.jc@gmail.com>
    - Abhijeet Kasurde <akasurde@redhat.com>
notes:
    - Tested on vSphere 6.5
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
   name:
        description:
            - Name of the VM to work with.
            - This is required if uuid is not supplied.
   uuid:
        description:
            - UUID of the instance to manage if known, this is VMware's BIOS UUID.
            - This is required if name is not supplied.
   datacenter:
        description:
            - Destination datacenter for the find operation.
            - Deprecated in 2.5, will be removed in 2.9 release.
        required: True
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: Find Guest's Folder using name
  vmware_guest_find:
    hostname: 192.168.1.209
    username: administrator@vsphere.local
    password: vmware
    validate_certs: no
    name: testvm
  register: vm_folder

- name: Find Guest's Folder using UUID
  vmware_guest_find:
    hostname: 192.168.1.209
    username: administrator@vsphere.local
    password: vmware
    validate_certs: no
    uuid: 38c4c89c-b3d7-4ae6-ae4e-43c5118eae49
  register: vm_folder
'''

RETURN = r"""
folders:
    description: List of folders for user specified virtual machine
    returned: on success
    type: list
"""


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.vmware import PyVmomi, get_all_objs, vmware_argument_spec


try:
    import pyVmomi
    from pyVmomi import vim
except ImportError:
    pass


class PyVmomiHelper(PyVmomi):
    def __init__(self, module):
        super(PyVmomiHelper, self).__init__(module)
        self.datacenter = None
        self.folders = None
        self.name = self.params['name']
        self.uuid = self.params['uuid']

    def getvm_folder_paths(self):
        results = []

        # compare the folder path of each VM against the search path
        vmList = get_all_objs(self.content, [vim.VirtualMachine])
        for item in vmList.items():
            vobj = item[0]
            if not isinstance(vobj.parent, vim.Folder):
                continue
            # Match by name or uuid
            if vobj.config.name == self.name or vobj.config.uuid == self.uuid:
                folderpath = self.get_vm_path(self.content, vobj)
                results.append(folderpath)
        return results


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        name=dict(type='str'),
        uuid=dict(type='str'),
        datacenter=dict(removed_in_version=2.9, type='str', required=True)
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=[['name', 'uuid']])

    pyv = PyVmomiHelper(module)
    # Check if the VM exists before continuing
    folders = pyv.getvm_folder_paths()

    # VM already exists
    if folders:
        try:
            module.exit_json(folders=folders)
        except Exception as exc:
            module.fail_json(msg="Folder enumeration failed with exception %s" % to_native(exc))
    else:
        module.fail_json(msg="Unable to find folders for virtual machine %s" % (module.params.get('name') or
                                                                                module.params.get('uuid')))


if __name__ == '__main__':
    main()
