#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Stéphane Travassac <stravassac () gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: vmware_guest_file_operation
short_description: Files operation in a VMware guest operating system whithout network
description:
    - Module allows user to create,delete file or directory in the guest operating system.
version_added: "2.5"
author:
  - Stéphane Travassac (@stravassac)
notes:
    - Tested on vSphere 6
    - Only the first match against vm_id is used, even if there are multiple matches
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
    datacenter:
        description:
            - The datacenter hosting the virtual machine.
            - If set, it will help to speed up virtual machine search.
    cluster:
        description:
            - The cluster hosting the virtual machine.
            - If set, it will help to speed up virtual machine search.
    folder:
        description:
            - Destination folder, absolute or relative path to find an existing guest or create the new guest.
            - The folder should include the datacenter. ESX's datacenter is ha-datacenter
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
        default: /vm
        version_added: "2.4"
    vm_id:
        description:
            - Name of the virtual machine to work with.
        required: True
    vm_id_type:
        description:
            - The VMware identification method by which the virtual machine will be identified.
        default: vm_name
        choices:
            - 'uuid'
            - 'dns_name'
            - 'inventory_path'
            - 'vm_name'
    vm_username:
        description:
            - The user to login-in to the virtual machine.
        required: True
    vm_password:
        description:
            - The password used to login-in to the virtual machine.
        required: True
    directory:
        description:
            - Create or delete directory
        required: False
'''

EXAMPLES = '''
- name: Create directory inside a vm
  vmware_guest_file_operation:
    hostname: myVSphere
    username: myUsername
    password: mySecret
    datacenter: myDatacenter
    folder: /vm
    vm_id: NameOfVM
    vm_username: root
    vm_password: superSecret
    directory:
      path: "/test"
      state: present
      recurse: no
  delegate_to: localhost
'''

try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import (connect_to_api, find_cluster_by_name, find_datacenter_by_name,
                                         find_vm_by_id, HAS_PYVMOMI, vmware_argument_spec)


# https://github.com/vmware/pyvmomi-community-samples/blob/master/samples/execute_program_in_vm.py
def execute_command(content, vm, params):
    vm_username = params['vm_username']
    vm_password = params['vm_password']
    program_path = params['vm_shell']
    args = params['vm_shell_args']
    env = params['vm_shell_env']
    cwd = params['vm_shell_cwd']

    creds = vim.vm.guest.NamePasswordAuthentication(username=vm_username, password=vm_password)
    cmdspec = vim.vm.guest.ProcessManager.ProgramSpec(arguments=args, envVariables=env, programPath=program_path, workingDirectory=cwd)
    cmdpid = content.guestOperationsManager.processManager.StartProgramInGuest(vm=vm, auth=creds, spec=cmdspec)

    return cmdpid

def directory(content, vm, params):
    vm_username = params['vm_username']
    vm_password = params['vm_password']
        
    if "path" not in params["directory"]:
        self.module.fail_json(msg="directory.path is mandatory")
    if "state" not in params["directory"]:
        self.module.fail_json(msg="directory.state is mandatory")
    if not "recurse" in params["directory"]:
        recurse = False
    else:
        recurse = params["directory"]['recurse']
    state = params["directory"]['state']
    path = params["directory"]['path']

    creds = vim.vm.guest.NamePasswordAuthentication(username=vm_username, password=vm_password)
    file_manager = content.guestOperationsManager.fileManager
    if state == "present":
        file_manager.MakeDirectoryInGuest(vm=vm, auth=creds, directoryPath=path,
                                                    createParentDirectories=recurse)
    if state == "absent":
        file_manager.DeleteDirectoryInGuest(vm=vm, auth=creds, directoryPath=path,
                                                    recursive=recurse)


def file(content, vm, params):
    vm_username = params['vm_username']
    vm_password = params['vm_password']
    vm_path = params['vm_path']
    state = params['vm_state']


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(datacenter=dict(type='str'),
                              cluster=dict(type='str'),
                              folder=dict(type='str', default='/vm'),
                              vm_id=dict(type='str', required=True),
                              vm_id_type=dict(default='vm_name', type='str', choices=['inventory_path', 'uuid', 'dns_name', 'vm_name']),
                              vm_username=dict(type='str', required=True),
                              vm_password=dict(type='str', no_log=True, required=True),
                              directory=dict(type='dict', default={})
                              ))

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=False,
                           required_if=[['vm_id_type', 'inventory_path', ['folder']]],
                           )

    if not HAS_PYVMOMI:
        module.fail_json(changed=False, msg='pyvmomi is required for this module')

    datacenter_name = module.params['datacenter']
    cluster_name = module.params['cluster']
    folder = module.params['folder']
    content = connect_to_api(module)

    datacenter = None
    if datacenter_name:
        datacenter = find_datacenter_by_name(content, datacenter_name)
        if not datacenter:
            module.fail_json(changed=False, msg="Unable to find %(datacenter)s datacenter" % module.params)

    cluster = None
    if cluster_name:
        cluster = find_cluster_by_name(content, cluster_name, datacenter)
        if not cluster:
            module.fail_json(changed=False, msg="Unable to find %(cluster)s cluster" % module.params)

    if module.params['vm_id_type'] == 'inventory_path':
        vm = find_vm_by_id(content, vm_id=module.params['vm_id'], vm_id_type="inventory_path", folder=folder)
    else:
        vm = find_vm_by_id(content, vm_id=module.params['vm_id'], vm_id_type=module.params['vm_id_type'], datacenter=datacenter, cluster=cluster)

    if not vm:
        module.fail_json(msg='Unable to find virtual machine.')

    try:
        if 'directory' in module.params:
            msg = directory(content, vm, module.params)
        module.exit_json(changed=True, uuid=vm.summary.config.uuid, msg=msg)
    except vmodl.RuntimeFault as runtime_fault:
        module.fail_json(changed=False, msg=runtime_fault.msg)
    except vmodl.MethodFault as method_fault:
        module.fail_json(changed=False, msg=method_fault.msg)
    except Exception as e:
        module.fail_json(changed=False, msg=str(e))


if __name__ == '__main__':
    main()
