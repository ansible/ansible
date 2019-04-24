#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright, (c) 2019, Ansible Project
# Copyright, (c) 2019, Moshe Immerman
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: vmware_guest_search
short_description: Search for VM's by name
description:
    -  Search for VM's by name
version_added: 2.9
author:
    - Moshe Immerman (@moshloop) <moshe.immerman@gmail.com>
notes:
    - Tested on vSphere 6.5+
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
    name:
        description:
            - Name of the VM to search for.
        required: True
    datacenter:
        description:
            - Datacenter name where to search.
        required: True
    recursive:
        description:
            - Search for VM's recursively through all folders.
        default: False
        required: False
        type: bool
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: Search for all VM's starting with "base-vm"
  vmware_guest_search:
    hostname: '{{ vcenter_server }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter: '{{ vcenter_datacenter }}'
    validate_certs: no
    name: base-vm
  delegate_to: localhost
  register: facts
'''

RETURN = """
vms:
    description: A list of virtual machine names that start with the provided name
    returned: always
    type: list
    sample: {
        vms: ["vm1", "vm2", "vm3"]
    }
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec, find_datacenter_by_name


class PyVmomiHelper(PyVmomi):

    def __init__(self, module):
        super(PyVmomiHelper, self).__init__(module)

    def find_vms(self, folder, searchpath, recursive, vms):
        for vm in folder.childEntity:
            if vm.name.startswith(searchpath):
                vms.append(vm.name)
            if recursive and hasattr(vm, 'childEntity'):
                self.find_vms(vm, searchpath, recursive, vms)

    def find_folder(self, root, searchpath):
        """ Walk inventory objects one position of the searchpath at a time """
        # split the searchpath so we can iterate through it
        paths = [x.replace('/', '') for x in searchpath.split('/')]
        paths_total = len(paths) - 1
        position = 0

        # recursive walk while looking for next element in searchpath

        while root and position <= paths_total:
            change = False
            if hasattr(root, 'childEntity'):
                for child in root.childEntity:
                    if child.name == paths[position]:
                        root = child
                        position += 1
                        change = True
                        break
            elif isinstance(root, vim.Datacenter):
                if hasattr(root, 'vmFolder'):
                    if root.vmFolder.name == paths[position]:
                        root = root.vmFolder
                        position += 1
                        change = True
            else:
                root = None

            if not change:
                root = None

        return root


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        name=dict(type='str', required=True),
        datacenter=dict(type='str', required=True),
        recursive=dict(type='bool', default=False)
    )
    module = AnsibleModule(argument_spec=argument_spec)
    try:
        pyv = PyVmomiHelper(module)
        dc = find_datacenter_by_name(pyv.content, module.params['datacenter'])
        if dc is None:
            module.fail_json(msg="Failed to find the datacenter %s" % module.params['datacenter'])
        folder = dc.vmFolder
        name = module.params['name']
        if "/" in name:
            paths = name.split("/")
            paths.pop()
            paths = "/".join(paths)
            name = name.split("/").pop()
            folder = pyv.find_folder(dc.vmFolder, paths)
            if folder is None:
                module.fail_json(msg="Unable to find folder: %s" % paths)
        vms = []
        pyv.find_vms(folder, name, module.params['recursive'], vms)
        module.exit_json(vms=vms)
    except Exception as exc:
        module.fail_json(msg="Fact gather failed with exception %s" % to_text(exc))


if __name__ == '__main__':
    main()
