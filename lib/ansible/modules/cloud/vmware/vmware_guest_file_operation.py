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
short_description: Files operation in a VMware guest operating system without network
description:
    - Module allows user to copy and fetch file and create,delete directory in the guest operating system.
version_added: "2.5"
author:
  - Stéphane Travassac (@stravassac)
notes:
    - Tested on vSphere 6
    - Only the first match against vm_id is used, even if there are multiple matches
requirements:
    - "python >= 2.6"
    - PyVmomi
    - requests
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
            - The user to login in to the virtual machine.
        required: True
    vm_password:
        description:
            - The password used to login-in to the virtual machine.
        required: True
    directory:
        description:
            - Create or delete directory
            - 'Valid attributes are:'
            - '  path: directory path to create or remove'
            - '  operation: Valid values are create, delete'
            - '  recurse (boolean): Not required, default (false)'
        required: False
    file_copy:
        description:
            - Copy file to vm networkless
            - 'Valid attributes are:'
            - '  src: file source absolute or relative'
            - '  dest: file destination, path must be exist'
            - '  overwrite: False or True (not required, default False)'
        required: False
    fetch_file:
        description:
            - Get file from vm networkless
            - 'Valid attributes are:'
            - '  src: The file on the remote system to fetch. This I(must) be a file, not a directory'
            - '  dest: file destination on localhost, path must be exist'
        required: False

'''

EXAMPLES = '''
- name: Create directory inside a vm
  vmware_guest_file_operation:
    hostname: myVSphere
    username: myUsername
    password: mySecret
    datacenter: myDatacenter
    validate_certs: True
    folder: /vm
    vm_id: NameOfVM
    vm_username: root
    vm_password: superSecret
    directory:
      path: "/test"
      operation: create
      recurse: no
  delegate_to: localhost

- name: copy file to vm
  vmware_guest_file_operation:
    hostname: myVSphere
    username: myUsername
    password: mySecret
    datacenter: myDatacenter
    validate_certs: True
    folder: /vm
    vm_id: NameOfVM
    vm_username: root
    vm_password: superSecret
    copy:
        src: "files/test.zip"
        dest: "/root/test.zip"
        overwrite: False
  delegate_to: localhost

- name: fetch file from vm
  vmware_guest_file_operation:
    hostname: myVSphere
    username: myUsername
    password: mySecret
    datacenter: myDatacenter
    validate_certs: True
    folder: /vm
    vm_id: NameOfVM
    vm_username: root
    vm_password: superSecret
    fetch:
        src: "/root/test.zip"
        dest: "files/test.zip"
  delegate_to: localhost
'''

RETURN = r'''
'''

try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

import os
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils import urls
from ansible.module_utils._text import to_bytes, to_native
from ansible.module_utils.vmware import (connect_to_api, find_cluster_by_name, find_datacenter_by_name,
                                         find_vm_by_id, HAS_PYVMOMI, vmware_argument_spec, PyVmomi)


def directory(module, content, vm):
    operations_permit = ['create', 'delete']
    vm_username = module.params['vm_username']
    vm_password = module.params['vm_password']

    if "path" not in module.params["directory"]:
        module.fail_json(msg="directory.path is mandatory")
    if "operation" not in module.params["directory"]:
        module.fail_json(msg="directory.operation is mandatory")
    if "recurse" not in module.params["directory"]:
        recurse = False
    else:
        recurse = bool(module.params['directory']['recurse'])
    operation = module.params["directory"]['operation']
    path = module.params["directory"]['path']
    if operation not in operations_permit:
        module.fail_json(msg="directory.operation valid values are create, delete")

    creds = vim.vm.guest.NamePasswordAuthentication(username=vm_username, password=vm_password)
    file_manager = content.guestOperationsManager.fileManager
    if operation == "create":
        try:
            file_manager.MakeDirectoryInGuest(vm=vm, auth=creds, directoryPath=path,
                                              createParentDirectories=recurse)
        except Exception as e:
            module.fail_json(msg=e)

    if operation == "delete":
        try:
            file_manager.DeleteDirectoryInGuest(vm=vm, auth=creds, directoryPath=path,
                                                recursive=recurse)
        except Exception as e:
            module.fail_json(changed=False, msg=e)

    return True


def fetch(module, content, vm):
    vm_username = module.params['vm_username']
    vm_password = module.params['vm_password']

    if "src" not in module.params["fetch"]:
        module.fail_json(msg="fetch.src is mandatory")
    if "dest" not in module.params["fetch"]:
        module.fail_json(msg="fetch.dest is mandatory")

    dest = module.params["fetch"]['dest']
    src = module.params['fetch']['src']

    creds = vim.vm.guest.NamePasswordAuthentication(username=vm_username, password=vm_password)
    file_manager = content.guestOperationsManager.fileManager

    try:
        fileTransferInfo = file_manager.InitiateFileTransferFromGuest(vm=vm, auth=creds,
                                                                      guestFilePath=src)
    except Exception as e:
        module.fail_json(changed=False, msg=e)

    url = fileTransferInfo.url
    resp, info = urls.fetch_url(module, url, method="GET")
    with open(dest, "wb") as local_file:
        local_file.write(resp.read())

    return True


def copy(module, content, vm):
    vm_username = module.params['vm_username']
    vm_password = module.params['vm_password']

    if "src" not in module.params["copy"]:
        module.fail_json(msg="copy.src is mandatory")
    if "dest" not in module.params["copy"]:
        module.fail_json(msg="copy.dest is mandatory")
    if "overwrite" in module.params["copy"]:
        overwrite = module.params["copy"]["overwrite"]
    else:
        overwrite = False

    dest = module.params["copy"]['dest']
    src = module.params['copy']['src']
    b_src = to_bytes(src, errors='surrogate_or_strict')
    if not os.path.exists(b_src):
        module.fail_json(msg="Source %s not found" % (src))
    if not os.access(b_src, os.R_OK):
        module.fail_json(msg="Source %s not readable" % (src))
    if os.path.isdir(b_src):
        module.fail_json(msg="copy does not support copy of directory: %s" % (src))

    data = None
    with open(b_src, "r") as local_file:
        data = local_file.read()
    file_size = os.path.getsize(b_src)

    creds = vim.vm.guest.NamePasswordAuthentication(username=vm_username, password=vm_password)
    file_attributes = vim.vm.guest.FileManager.FileAttributes()
    file_manager = content.guestOperationsManager.fileManager
    try:
        url = file_manager.InitiateFileTransferToGuest(vm=vm, auth=creds, guestFilePath=dest,
                                                       fileAttributes=file_attributes, overwrite=overwrite,
                                                       fileSize=file_size)
    except Exception as e:
        module.fail_json(changed=False, msg=e)

    resp, info = urls.fetch_url(module, url, data=data, method="PUT")

    status_code = info["status"]
    if status_code != 200:
        raise Exception('initiateFileTransferToGuest : problem during file transfer')
    return True


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(datacenter=dict(type='str'),
                              cluster=dict(type='str'),
                              folder=dict(type='str'),
                              vm_id=dict(type='str', required=True),
                              vm_id_type=dict(default='vm_name', type='str',
                                              choices=['inventory_path', 'uuid', 'dns_name', 'vm_name']),
                              vm_username=dict(type='str', required=True),
                              vm_password=dict(type='str', no_log=True, required=True),
                              directory=dict(type='dict', default={}),
                              copy=dict(type='dict', default={}),
                              fetch=dict(type='dict', default={})
                              ))

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=False,
                           required_if=[['vm_id_type', 'inventory_path', ['folder']]],
                           )

    if not HAS_PYVMOMI:
        module.fail_json(changed=False, msg='pyvmomi is required for this module')

    if module.params['vm_id_type'] == 'vm_name' and not module.params['folder']:
        raise Exception('Folder is required parameter when vm_id_type is inventory_path')

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
        vm = find_vm_by_id(content, vm_id=module.params['vm_id'], vm_id_type=module.params['vm_id_type'],
                           datacenter=datacenter, cluster=cluster)

    if not vm:
        module.fail_json(msg='Unable to find virtual machine.')

    try:
        if len(module.params['directory']) > 0:
            msg = directory(module, content, vm)
        if len(module.params['copy']) > 0:
            msg = copy(module, content, vm)
        if len(module.params['fetch']) > 0:
            msg = fetch(module, content, vm)
        module.exit_json(changed=True, uuid=vm.summary.config.uuid, msg=msg)
    except vmodl.RuntimeFault as runtime_fault:
        module.fail_json(changed=False, msg=runtime_fault.msg)
    except vmodl.MethodFault as method_fault:
        module.fail_json(changed=False, msg=method_fault.msg)
    except Exception as e:
        module.fail_json(changed=False, msg=to_native(e))


if __name__ == '__main__':
    main()
