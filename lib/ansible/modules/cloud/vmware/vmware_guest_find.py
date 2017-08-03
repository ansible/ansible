#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: vmware_guest_find
short_description: Find the folder path(s) for a VM by name or UUID
description:
    - Find the folder path(s) for a VM by name or UUID
version_added: 2.4
author:
    - James Tanner <tanner.jc@gmail.com>
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
            - Destination datacenter for the deploy operation.
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

RETURN = """
"""

import os

HAS_PYVMOMI = False
try:
    import pyVmomi
    from pyVmomi import vim

    HAS_PYVMOMI = True
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.vmware import (connect_to_api, gather_vm_facts, get_all_objs,
                                         compile_folder_path_for_object, vmware_argument_spec)


class PyVmomiHelper(object):
    def __init__(self, module):
        if not HAS_PYVMOMI:
            module.fail_json(msg='pyvmomi module required')

        self.datacenter = None
        self.folders = None
        self.foldermap = {
            'fvim_by_path': {},
            'path_by_fvim': {},
            'path_by_vvim': {},
            'paths': {},
            'uuids': {}
        }
        self.module = module
        self.params = module.params
        self.content = connect_to_api(self.module)

    def getvm_folder_paths(self, name=None, uuid=None):

        results = []

        if not self.folders:
            self.getfolders()

        # compare the folder path of each VM against the search path
        vmList = get_all_objs(self.content, [vim.VirtualMachine])
        for item in vmList.items():
            vobj = item[0]
            if not isinstance(vobj.parent, vim.Folder):
                continue
            # Match by name or uuid
            if vobj.config.name == name or vobj.config.uuid == uuid:
                folderpath = compile_folder_path_for_object(vobj)
                results.append(folderpath)

        return results

    def gather_facts(self, vm):
        return gather_vm_facts(self.content, vm)

    def _build_folder_tree(self, folder):

        tree = {'virtualmachines': [],
                'subfolders': {},
                'vimobj': folder,
                'name': folder.name}

        children = None
        if hasattr(folder, 'childEntity'):
            children = folder.childEntity

        if children:
            for child in children:
                if child == folder or child in tree:
                    continue
                if isinstance(child, vim.Folder):
                    ctree = self._build_folder_tree(child)
                    tree['subfolders'][child] = dict.copy(ctree)
                elif isinstance(child, vim.VirtualMachine):
                    tree['virtualmachines'].append(child)
        else:
            if isinstance(folder, vim.VirtualMachine):
                return folder
        return tree

    def _build_folder_map(self, folder, inpath='/'):

        """ Build a searchable index for vms+uuids+folders """
        if isinstance(folder, tuple):
            folder = folder[1]

        thispath = os.path.join(inpath, folder['name'])

        if thispath not in self.foldermap['paths']:
            self.foldermap['paths'][thispath] = []

        # store object by path and store path by object
        self.foldermap['fvim_by_path'][thispath] = folder['vimobj']
        self.foldermap['path_by_fvim'][folder['vimobj']] = thispath

        for item in folder.items():
            k = item[0]
            v = item[1]

            if k == 'name':
                pass
            elif k == 'subfolders':
                for x in v.items():
                    self._build_folder_map(x, inpath=thispath)
            elif k == 'virtualmachines':
                for x in v:
                    # Apparently x.config can be None on corrupted VMs
                    if x.config is None:
                        continue
                    self.foldermap['uuids'][x.config.uuid] = x.config.name
                    self.foldermap['paths'][thispath].append(x.config.uuid)

                    if x not in self.foldermap['path_by_vvim']:
                        self.foldermap['path_by_vvim'][x] = thispath

    def getfolders(self):
        if not self.datacenter:
            self.get_datacenter()
        self.folders = self._build_folder_tree(self.datacenter.vmFolder)
        self._build_folder_map(self.folders)

    def get_datacenter(self):
        self.datacenter = get_obj(
            self.content,
            [vim.Datacenter],
            self.params['datacenter']
        )


def get_obj(content, vimtype, name):
    """
    Return an object by name, if name is None the
    first found object is returned
    """
    obj = None
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vimtype, True)
    for c in container.view:
        if name:
            if c.name == name:
                obj = c
                break
        else:
            obj = c
            break

    container.Destroy()
    return obj


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        name=dict(type='str'),
        uuid=dict(type='str'),
        datacenter=dict(type='str', required=True)
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=[['name', 'uuid']])
    pyv = PyVmomiHelper(module)
    # Check if the VM exists before continuing
    folders = pyv.getvm_folder_paths(
        name=module.params['name'],
        uuid=module.params['uuid']
    )

    # VM already exists
    if folders:
        try:
            module.exit_json(folders=folders)
        except Exception as exc:
            module.fail_json(msg="Folder enumeration failed with exception %s" % to_native(exc))
    else:
        msg = "Unable to find folders for VM "
        if module.params['name']:
            msg += "%(name)s" % module.params
        elif module.params['uuid']:
            msg += "%(uuid)s" % module.params
        module.fail_json(msg=msg)


if __name__ == '__main__':
    main()
