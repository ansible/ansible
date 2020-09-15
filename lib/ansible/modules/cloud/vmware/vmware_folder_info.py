#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, David Hewitt <davidmhewitt@gmail.com>
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
module: vmware_folder_info
short_description: Provides information about folders in a datacenter
description:
- The module can be used to gather a hierarchical view of the folders that exist within a datacenter
version_added: 2.9
author:
- David Hewitt (@davidmhewitt)
notes:
- Tested on vSphere 6.5
requirements:
- python >= 2.6
- PyVmomi
options:
  datacenter:
    description:
    - Name of the datacenter.
    required: true
    type: str
    aliases: ['datacenter_name']
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Provide information about vCenter folders
  vmware_folder_info:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter: datacenter_name
  delegate_to: localhost
  register: vcenter_folder_info
'''

RETURN = r'''
folder_info:
    description:
    - dict about folders
    returned: success
    type: str
    sample:
        {
            "datastoreFolders": {
                "path": "/DC01/datastore",
                "subfolders": {
                    "Local Datastores": {
                        "path": "/DC01/datastore/Local Datastores",
                        "subfolders": {}
                    }
                }
            },
            "hostFolders": {
                "path": "/DC01/host",
                "subfolders": {}
            },
            "networkFolders": {
                "path": "/DC01/network",
                "subfolders": {}
            },
            "vmFolders": {
                "path": "/DC01/vm",
                "subfolders": {
                    "Core Infrastructure Servers": {
                        "path": "/DC01/vm/Core Infrastructure Servers",
                        "subfolders": {
                            "Staging Network Services": {
                                "path": "/DC01/vm/Core Infrastructure Servers/Staging Network Services",
                                "subfolders": {}
                            },
                            "VMware": {
                                "path": "/DC01/vm/Core Infrastructure Servers/VMware",
                                "subfolders": {}
                            }
                        }
                    }
                }
            }
        }
'''

try:
    from pyVmomi import vim
except ImportError as import_err:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import vmware_argument_spec, PyVmomi


class VmwareFolderInfoManager(PyVmomi):
    def __init__(self, module):
        super(VmwareFolderInfoManager, self).__init__(module)
        self.dc_name = self.params['datacenter']

    def gather_folder_info(self):
        datacenter = self.find_datacenter_by_name(self.dc_name)
        if datacenter is None:
            self.module.fail_json(msg="Failed to find the datacenter %s" % self.dc_name)

        folder_trees = {}
        folder_trees['vmFolders'] = self.build_folder_tree(datacenter.vmFolder, "/%s/vm" % self.dc_name)
        folder_trees['hostFolders'] = self.build_folder_tree(datacenter.hostFolder, "/%s/host" % self.dc_name)
        folder_trees['networkFolders'] = self.build_folder_tree(datacenter.networkFolder, "/%s/network" % self.dc_name)
        folder_trees['datastoreFolders'] = self.build_folder_tree(datacenter.datastoreFolder, "/%s/datastore" % self.dc_name)

        self.module.exit_json(
            changed=False,
            folder_info=folder_trees
        )

    def build_folder_tree(self, folder, path):
        tree = {
            'path': path,
            'subfolders': {}
        }

        children = None
        if hasattr(folder, 'childEntity'):
            children = folder.childEntity

        if children:
            for child in children:
                if child == folder:
                    continue
                if isinstance(child, vim.Folder):
                    ctree = self.build_folder_tree(child, "%s/%s" % (path, child.name))
                    tree['subfolders'][child.name] = dict.copy(ctree)
        return tree


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        datacenter=dict(type='str', required=True, aliases=['datacenter_name'])
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    vmware_folder_info_mgr = VmwareFolderInfoManager(module)
    vmware_folder_info_mgr.gather_folder_info()


if __name__ == "__main__":
    main()
