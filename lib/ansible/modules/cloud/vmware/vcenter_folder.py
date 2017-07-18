#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Davis Phillips davis.phillips@gmail.com
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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: vmware_folder
short_description: Add/remove folders to/from vCenter
description:
    - This module can be used to add/remove a folder to/from vCenter
version_added: 2.3
author: "Davis Phillips (@dav1x)"
notes:
    - Tested on vSphere 6.5
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
    datacenter:
        description:
            - Name of the datacenter to add the host
        required: True
    cluster:
        description:
            - Name of the cluster to add the host
        required: True
    folder:
        description:
            - Folder name to manage
        required: True
    hostname:
        description:
            - ESXi hostname to manage
        required: True
    username:
        description:
            - ESXi username
        required: True
    password:
        description:
            - ESXi password
        required: True
    state:
        description:
            - Add or remove the folder
        default: 'present'
        choices:
            - 'present'
            - 'absent'
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
# Create a folder 
  - name: Add a folder to vCenter
    vmware_folder:
      hostname: vcsa_host
      username: vcsa_user
      password: vcsa_pass
      datacenter: datacenter
      cluster: cluster
      folder: folder
      state: present
'''

RETURN = """
instance:
    descripton: metadata about the new folder
    returned: always
    type: dict
    sample: None
"""

try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False

from ansible.module_utils.vmware import get_all_objs, connect_to_api, vmware_argument_spec, find_datacenter_by_name, \
    find_cluster_by_name_datacenter, wait_for_task
from ansible.module_utils.basic import AnsibleModule

class VMwareFolder(object):
    def __init__(self, module):
        self.module = module
        self.datacenter = module.params['datacenter']
        self.cluster = module.params['cluster']
        self.folder = module.params['folder']
        self.hostname = module.params['hostname']
        self.username = module.params['username']
        self.password = module.params['password']
        self.state = module.params['state']
        self.dc_obj = None
        self.cluster_obj = None
        self.host_obj = None
        self.folder_obj = None
        self.folder_name = None
        self.folder_expanded = None
        self.folder_full_path = []
        self.content = connect_to_api(module)

    def find_host_by_cluster_datacenter(self):
        self.dc_obj = find_datacenter_by_name(self.content, self.datacenter)
        self.cluster_obj = find_cluster_by_name_datacenter(self.dc_obj, self.cluster)

        for host in self.cluster_obj.host:
            if host.name == self.hostname:
                return host, self.cluster

        return None, self.cluster

    def select_folder(self, host):
        fold_obj = None
        self.folder_expanded = self.folder.split("/")
        last_e = self.folder_expanded.pop()
        fold_obj = self.get_obj([vim.Folder],last_e)
        if fold_obj:
            return fold_obj

    def get_obj(self, vimtype, name, return_all = False):
        obj = list()
        container = self.content.viewManager.CreateContainerView(
            self.content.rootFolder, vimtype, True)

        for c in container.view:
            if name in [c.name, c._GetMoId()]:
                if return_all is False:
                    return c
                    break
                else:
                    obj.append(c)

        if len(obj) > 0:
            return obj
        else:
            # for backwards-compat
            return None

    def process_state(self):
        try:
            folder_states = {
                'absent': {
                    'present': self.state_remove_folder,
                    'absent': self.state_exit_unchanged,
                },
                'present': {
                    'present': self.state_exit_unchanged,
                    'absent': self.state_add_folder,
                }
            }

            folder_states[self.state][self.check_folder_state()]()

        except vmodl.RuntimeFault as runtime_fault:
            self.module.fail_json(msg = runtime_fault.msg)
        except vmodl.MethodFault as method_fault:
            self.module.fail_json(msg = method_fault.msg)
        except Exception as e:
            self.module.fail_json(msg = str(e))

    def state_exit_unchanged(self):
        self.module.exit_json(changed = False)

    def state_remove_folder(self):
        changed = True
        result = None
        self.folder_expanded = self.folder.split("/")
        f = self.folder_expanded.pop()
        task = self.get_obj([vim.Folder],f).Destroy()

        try:
            success, result = wait_for_task(task)

        except:
            self.module.fail_json(msg = "Failed to remove folder '%s' '%s'" % (self.folder,folder))

        self.module.exit_json(changed = changed, result = str(result))

    def state_add_folder(self):
        changed = True
        result = None

        self.dc_obj = find_datacenter_by_name(self.content, self.datacenter)
        self.cluster_obj = find_cluster_by_name_datacenter(self.dc_obj, self.cluster)
        self.folder_expanded = self.folder.split("/")
        index = 0
        for f in self.folder_expanded:
            if not self.get_obj([vim.Folder],f):
                if index == 0:
                #First object gets created on the datacenter
                    task = self.dc_obj.vmFolder.CreateFolder(name=f)
                else:
                    parent_f = self.get_obj([vim.Folder],self.folder_expanded[index - 1])
                    task = parent_f.CreateFolder(name=f)
            index = index + 1

        self.module.exit_json(changed = changed)

    def check_folder_state(self):

        self.host_obj, self.cluster_obj = self.find_host_by_cluster_datacenter()
        self.folder_obj = self.select_folder(self.host_obj)

        if self.folder_obj is None:
            return 'absent'
        else:
            return 'present'


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(datacenter = dict(required = True, type = 'str'),
                              cluster = dict(required = True, type = 'str'),
                              folder = dict(required=True, type='str'),
                              hostname = dict(required = True, type = 'str'),
                              username = dict(required = True, type = 'str'),
                              password = dict(required = True, type = 'str', no_log = True),
                              state = dict(default = 'present', choices = ['present', 'absent'], type = 'str')))

    module = AnsibleModule(argument_spec = argument_spec, supports_check_mode = True)

    if not HAS_PYVMOMI:
        module.fail_json(msg = 'pyvmomi is required for this module')

    vmware_folder = VMwareFolder(module)
    vmware_folder.process_state()


if __name__ == '__main__':
    main()
