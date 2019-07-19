#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Stéphane Travassac <stravassac@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: vmware_guest_file_operation
short_description: Files operation in a VMware guest operating system without network
description:
    - Module to copy a file to a VM, fetch a file from a VM and create or delete a directory in the guest OS.
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
            - Destination folder, absolute path to find an existing guest or create the new guest.
            - The folder should include the datacenter. ESX's datacenter is ha-datacenter
            - Used only if C(vm_id_type) is C(inventory_path).
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
            - 'instance_uuid'
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
            - Create or delete a directory.
            - Can be used to create temp directory inside guest using mktemp operation.
            - mktemp sets variable C(dir) in the result with the name of the new directory.
            - mktemp operation option is added in version 2.8
            - 'Valid attributes are:'
            - '  operation (str): Valid values are: create, delete, mktemp'
            - '  path (str): directory path (required for create or remove)'
            - '  prefix (str): temporary directory prefix (required for mktemp)'
            - '  suffix (str): temporary directory suffix (required for mktemp)'
            - '  recurse (boolean): Not required, default (false)'
        required: False
    copy:
        description:
            - Copy file to vm without requiring network.
            - 'Valid attributes are:'
            - '  src: file source absolute or relative'
            - '  dest: file destination, path must be exist'
            - '  overwrite: False or True (not required, default False)'
        required: False
    fetch:
        description:
            - Get file from virtual machine without requiring network.
            - 'Valid attributes are:'
            - '  src: The file on the remote system to fetch. This I(must) be a file, not a directory'
            - '  dest: file destination on localhost, path must be exist'
        required: False
        version_added: 2.5

extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: Create directory inside a vm
  vmware_guest_file_operation:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter_name }}"
    validate_certs: no
    vm_id: "{{ guest_name }}"
    vm_username: "{{ guest_username }}"
    vm_password: "{{ guest_userpassword }}"
    directory:
      path: "/test"
      operation: create
      recurse: no
  delegate_to: localhost

- name: copy file to vm
  vmware_guest_file_operation:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter_name }}"
    vm_id: "{{ guest_name }}"
    vm_username: "{{ guest_username }}"
    vm_password: "{{ guest_userpassword }}"
    copy:
        src: "files/test.zip"
        dest: "/root/test.zip"
        overwrite: False
  delegate_to: localhost

- name: fetch file from vm
  vmware_guest_file_operation:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    datacenter: "{{ datacenter_name }}"
    vm_id: "{{ guest_name }}"
    vm_username: "{{ guest_username }}"
    vm_password: "{{ guest_userpassword }}"
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
from ansible.module_utils.vmware import (PyVmomi, find_cluster_by_name, find_datacenter_by_name,
                                         find_vm_by_id, vmware_argument_spec)


class VmwareGuestFileManager(PyVmomi):
    def __init__(self, module):
        super(VmwareGuestFileManager, self).__init__(module)
        datacenter_name = module.params['datacenter']
        cluster_name = module.params['cluster']
        folder = module.params['folder']

        datacenter = None
        if datacenter_name:
            datacenter = find_datacenter_by_name(self.content, datacenter_name)
            if not datacenter:
                module.fail_json(msg="Unable to find %(datacenter)s datacenter" % module.params)

        cluster = None
        if cluster_name:
            cluster = find_cluster_by_name(self.content, cluster_name, datacenter)
            if not cluster:
                module.fail_json(msg="Unable to find %(cluster)s cluster" % module.params)

        if module.params['vm_id_type'] == 'inventory_path':
            vm = find_vm_by_id(self.content, vm_id=module.params['vm_id'], vm_id_type="inventory_path", folder=folder)
        else:
            vm = find_vm_by_id(self.content,
                               vm_id=module.params['vm_id'],
                               vm_id_type=module.params['vm_id_type'],
                               datacenter=datacenter,
                               cluster=cluster)

        if not vm:
            module.fail_json(msg='Unable to find virtual machine.')

        self.vm = vm
        try:
            result = dict(changed=False)
            if module.params['directory']:
                result = self.directory()
            if module.params['copy']:
                result = self.copy()
            if module.params['fetch']:
                result = self.fetch()
            module.exit_json(**result)
        except vmodl.RuntimeFault as runtime_fault:
            module.fail_json(msg=to_native(runtime_fault.msg))
        except vmodl.MethodFault as method_fault:
            module.fail_json(msg=to_native(method_fault.msg))
        except Exception as e:
            module.fail_json(msg=to_native(e))

    def directory(self):
        result = dict(changed=True, uuid=self.vm.summary.config.uuid)
        vm_username = self.module.params['vm_username']
        vm_password = self.module.params['vm_password']

        recurse = bool(self.module.params['directory']['recurse'])
        operation = self.module.params['directory']['operation']
        path = self.module.params['directory']['path']
        prefix = self.module.params['directory']['prefix']
        suffix = self.module.params['directory']['suffix']
        creds = vim.vm.guest.NamePasswordAuthentication(username=vm_username, password=vm_password)
        file_manager = self.content.guestOperationsManager.fileManager
        if operation in ("create", "mktemp"):
            try:
                if operation == "create":
                    file_manager.MakeDirectoryInGuest(vm=self.vm,
                                                      auth=creds,
                                                      directoryPath=path,
                                                      createParentDirectories=recurse)
                else:
                    newdir = file_manager.CreateTemporaryDirectoryInGuest(vm=self.vm, auth=creds,
                                                                          prefix=prefix, suffix=suffix)
                    result['dir'] = newdir
            except vim.fault.FileAlreadyExists as file_already_exists:
                result['changed'] = False
                result['msg'] = "Guest directory %s already exist: %s" % (path,
                                                                          to_native(file_already_exists.msg))
            except vim.fault.GuestPermissionDenied as permission_denied:
                self.module.fail_json(msg="Permission denied for path %s : %s" % (path,
                                                                                  to_native(permission_denied.msg)),
                                      uuid=self.vm.summary.config.uuid)
            except vim.fault.InvalidGuestLogin as invalid_guest_login:
                self.module.fail_json(msg="Invalid guest login for user %s : %s" % (vm_username,
                                                                                    to_native(invalid_guest_login.msg)),
                                      uuid=self.vm.summary.config.uuid)
            # other exceptions
            except Exception as e:
                self.module.fail_json(msg="Failed to Create directory into VM VMware exception : %s" % to_native(e),
                                      uuid=self.vm.summary.config.uuid)

        if operation == "delete":
            try:
                file_manager.DeleteDirectoryInGuest(vm=self.vm, auth=creds, directoryPath=path,
                                                    recursive=recurse)
            except vim.fault.FileNotFound as file_not_found:
                result['changed'] = False
                result['msg'] = "Guest directory %s not exists %s" % (path,
                                                                      to_native(file_not_found.msg))
            except vim.fault.FileFault as e:
                self.module.fail_json(msg="FileFault : %s" % e.msg,
                                      uuid=self.vm.summary.config.uuid)
            except vim.fault.GuestPermissionDenied as permission_denied:
                self.module.fail_json(msg="Permission denied for path %s : %s" % (path,
                                                                                  to_native(permission_denied.msg)),
                                      uuid=self.vm.summary.config.uuid)
            except vim.fault.InvalidGuestLogin as invalid_guest_login:
                self.module.fail_json(msg="Invalid guest login for user %s : %s" % (vm_username,
                                                                                    to_native(invalid_guest_login.msg)),
                                      uuid=self.vm.summary.config.uuid)
            # other exceptions
            except Exception as e:
                self.module.fail_json(msg="Failed to Delete directory into Vm VMware exception : %s" % to_native(e),
                                      uuid=self.vm.summary.config.uuid)

        return result

    def fetch(self):
        result = dict(changed=True, uuid=self.vm.summary.config.uuid)
        vm_username = self.module.params['vm_username']
        vm_password = self.module.params['vm_password']
        hostname = self.module.params['hostname']
        dest = self.module.params["fetch"]['dest']
        src = self.module.params['fetch']['src']
        creds = vim.vm.guest.NamePasswordAuthentication(username=vm_username, password=vm_password)
        file_manager = self.content.guestOperationsManager.fileManager

        try:
            fileTransferInfo = file_manager.InitiateFileTransferFromGuest(vm=self.vm, auth=creds,
                                                                          guestFilePath=src)
            url = fileTransferInfo.url
            url = url.replace("*", hostname)
            resp, info = urls.fetch_url(self.module, url, method="GET")
            try:
                with open(dest, "wb") as local_file:
                    local_file.write(resp.read())
            except Exception as e:
                self.module.fail_json(msg="local file write exception : %s" % to_native(e),
                                      uuid=self.vm.summary.config.uuid)
        except vim.fault.FileNotFound as file_not_found:
            self.module.fail_json(msg="Guest file %s does not exist : %s" % (src, to_native(file_not_found.msg)),
                                  uuid=self.vm.summary.config.uuid)
        except vim.fault.FileFault as e:
            self.module.fail_json(msg="FileFault : %s" % to_native(e.msg),
                                  uuid=self.vm.summary.config.uuid)
        except vim.fault.GuestPermissionDenied:
            self.module.fail_json(msg="Permission denied to fetch file %s" % src,
                                  uuid=self.vm.summary.config.uuid)
        except vim.fault.InvalidGuestLogin:
            self.module.fail_json(msg="Invalid guest login for user %s" % vm_username,
                                  uuid=self.vm.summary.config.uuid)
        # other exceptions
        except Exception as e:
            self.module.fail_json(msg="Failed to Fetch file from Vm VMware exception : %s" % to_native(e),
                                  uuid=self.vm.summary.config.uuid)

        return result

    def copy(self):
        result = dict(changed=True, uuid=self.vm.summary.config.uuid)
        vm_username = self.module.params['vm_username']
        vm_password = self.module.params['vm_password']
        hostname = self.module.params['hostname']
        overwrite = self.module.params["copy"]["overwrite"]
        dest = self.module.params["copy"]['dest']
        src = self.module.params['copy']['src']
        b_src = to_bytes(src, errors='surrogate_or_strict')

        if not os.path.exists(b_src):
            self.module.fail_json(msg="Source %s not found" % src)
        if not os.access(b_src, os.R_OK):
            self.module.fail_json(msg="Source %s not readable" % src)
        if os.path.isdir(b_src):
            self.module.fail_json(msg="copy does not support copy of directory: %s" % src)

        data = None
        with open(b_src, "r") as local_file:
            data = local_file.read()
        file_size = os.path.getsize(b_src)

        creds = vim.vm.guest.NamePasswordAuthentication(username=vm_username, password=vm_password)
        file_attributes = vim.vm.guest.FileManager.FileAttributes()
        file_manager = self.content.guestOperationsManager.fileManager
        try:
            url = file_manager.InitiateFileTransferToGuest(vm=self.vm, auth=creds, guestFilePath=dest,
                                                           fileAttributes=file_attributes, overwrite=overwrite,
                                                           fileSize=file_size)
            url = url.replace("*", hostname)
            resp, info = urls.fetch_url(self.module, url, data=data, method="PUT")

            status_code = info["status"]
            if status_code != 200:
                self.module.fail_json(msg='problem during file transfer, http message:%s' % info,
                                      uuid=self.vm.summary.config.uuid)
        except vim.fault.FileAlreadyExists:
            result['changed'] = False
            result['msg'] = "Guest file %s already exists" % dest
            return result
        except vim.fault.FileFault as e:
            self.module.fail_json(msg="FileFault:%s" % to_native(e.msg),
                                  uuid=self.vm.summary.config.uuid)
        except vim.fault.GuestPermissionDenied as permission_denied:
            self.module.fail_json(msg="Permission denied to copy file into "
                                      "destination %s : %s" % (dest, to_native(permission_denied.msg)),
                                  uuid=self.vm.summary.config.uuid)
        except vim.fault.InvalidGuestLogin as invalid_guest_login:
            self.module.fail_json(msg="Invalid guest login for user"
                                      " %s : %s" % (vm_username, to_native(invalid_guest_login.msg)))
        # other exceptions
        except Exception as e:
            self.module.fail_json(msg="Failed to Copy file to Vm VMware exception : %s" % to_native(e),
                                  uuid=self.vm.summary.config.uuid)
        return result


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(
        datacenter=dict(type='str'),
        cluster=dict(type='str'),
        folder=dict(type='str'),
        vm_id=dict(type='str', required=True),
        vm_id_type=dict(
            default='vm_name',
            type='str',
            choices=['inventory_path', 'uuid', 'instance_uuid', 'dns_name', 'vm_name']),
        vm_username=dict(type='str', required=True),
        vm_password=dict(type='str', no_log=True, required=True),
        directory=dict(
            type='dict',
            default=None,
            options=dict(
                operation=dict(required=True, type='str', choices=['create', 'delete', 'mktemp']),
                path=dict(required=False, type='str'),
                prefix=dict(required=False, type='str'),
                suffix=dict(required=False, type='str'),
                recurse=dict(required=False, type='bool', default=False)
            )
        ),
        copy=dict(
            type='dict',
            default=None,
            options=dict(src=dict(required=True, type='str'),
                         dest=dict(required=True, type='str'),
                         overwrite=dict(required=False, type='bool', default=False)
                         )
        ),
        fetch=dict(
            type='dict',
            default=None,
            options=dict(
                src=dict(required=True, type='str'),
                dest=dict(required=True, type='str'),
            )
        )
    )
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False,
                           required_if=[['vm_id_type', 'inventory_path', ['folder']]],
                           mutually_exclusive=[['directory', 'copy', 'fetch']],
                           required_one_of=[['directory', 'copy', 'fetch']],
                           )

    if module.params['directory']:
        if module.params['directory']['operation'] in ('create', 'delete') and not module.params['directory']['path']:
            module.fail_json(msg='directory.path is required when operation is "create" or "delete"')
        if module.params['directory']['operation'] == 'mktemp' and not (module.params['directory']['prefix'] and module.params['directory']['suffix']):
            module.fail_json(msg='directory.prefix and directory.suffix are required when operation is "mktemp"')

    if module.params['vm_id_type'] == 'inventory_path' and not module.params['folder']:
        module.fail_json(msg='Folder is required parameter when vm_id_type is inventory_path')

    vmware_guest_file_manager = VmwareGuestFileManager(module)


if __name__ == '__main__':
    main()
