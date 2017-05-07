#!/usr/bin/python
# -*- coding: utf-8 -*-
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
            - Name of the VM to work with
        required: True
   uuid:
        description:
            - UUID of the instance to manage if known, this is VMware's uid.
            - This is required if name is not supplied.
   datacenter:
        description:
            - Destination datacenter for the deploy operation
        required: True
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: Gather VM facts
  vmware_guest_find:
    hostname: 192.168.1.209
    username: administrator@vsphere.local
    password: vmware
    validate_certs: no
    name: testvm
'''

RETURN = """
"""

import os

# import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils.vmware import connect_to_api, gather_vm_facts
from ansible.module_utils.vmware import get_all_objs


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

    def getvm_folder_paths(self, name=None, uuid=None, folder=None):

        results = []

        if not self.folders:
            self.getfolders()

        # compare the folder path of each VM against the search path
        vmList = get_all_objs(self.content, [vim.VirtualMachine])
        for item in vmList.items():
            vobj = item[0]
            if not isinstance(vobj.parent, vim.Folder):
                continue
            # Match by name
            if vobj.config.name == name:
                folderpath = self.compile_folder_path_for_object(vobj)
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

    @staticmethod
    def compile_folder_path_for_object(vobj):
        """ make a /vm/foo/bar/baz like folder path for an object """

        paths = []
        if isinstance(vobj, vim.Folder):
            paths.append(vobj.name)

        thisobj = vobj
        while hasattr(thisobj, 'parent'):
            thisobj = thisobj.parent
            if isinstance(thisobj, vim.Folder):
                paths.append(thisobj.name)
        paths.reverse()
        if paths[0] == 'Datacenters':
            paths.remove('Datacenters')
        return '/' + '/'.join(paths)

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
            validate_certs=dict(required=False, type='bool', default=True),
            name=dict(required=True, type='str'),
            uuid=dict(required=False, type='str'),
            datacenter=dict(required=True, type='str'),
        ),
    )

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
        except Exception:
            e = get_exception()
            module.fail_json(msg="Folder enumeration failed with exception %s" % e)
    else:
        module.fail_json(msg="Unable to find folders for VM %(name)s" % module.params)

if __name__ == '__main__':
    main()
