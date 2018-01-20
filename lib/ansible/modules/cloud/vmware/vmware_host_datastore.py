#!/usr/bin/python

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: vmware_host_datastore
short_description: Add/remove datastore on ESXi host
description:
- This module can be used to mount/umount on datastore on ESXi host.
- This module only support NFS/VMFS datastores.
- For VMFS datastore, available device must already be connected on host.
version_added: '2.5'
author:
- Ludovic Rivallain <ludovic.rivallain@gmail.com> @lrivallain
notes:
- Tested on vSphere 6.0, 6.5
requirements:
- python >= 2.6
- PyVmomi
options:
  datacenter_name:
    description:
    - Name of the datacenter to add the datastore.
    required: true
  datastore_name:
    description:
    - Name of the datastore to add/remove.
    required: true
  datastore_type:
    description:
    - Type of the datastore to configure (nfs/vmfs).
    required: true
  nfs_server:
    description:
    - NFS host serving nfs datastore.
    - Required if datastore type is "nfs" and state is "present", else unused.
  nfs_path:
    description:
    - Resource path on NFS host.
    - Required if datastore type is "nfs" and state is "present", else unused.
  nfs_ro:
    description:
    - ReadOnly or ReadWrite mount.
    - Unsed if datastore type is not "nfs" and state is not "present".
    default: False
  vmfs_device_name:
    description:
    - Name a the device to use as VMFS datastore.
    - Required for vmfs datastore type and state is "present", else unused.
  vmfs_version:
    description:
    - VMFS version to use for datastore creation.
    - Unsed if datastore type is not "vmfs" and state is not "present".
  esxi_hostname:
    description:.
    - ESXi hostname to mount the datastore.
    required: true
  state:
    description:
    - "present: Mount datastore on host if it's absent else do nothing."
    - "absent: Umount datastore if it's present else do nothing."
    default: present
    choices:
    - present
    - absent
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Mount VMFS datastores to ESXi
  vmware_host_datastore:
      hostname: '{{ vcenter_hostname }}'
      username: '{{ vcenter_user }}'
      password: '{{ vcenter_pass }}'
      datacenter_name: '{{ datacenter }}'
      datastore_name: '{{ item.name }}'
      datastore_type: '{{ item.type }}'
      vmfs_device_name: 'naa.XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
      vmfs_version: 6
      esxi_hostname: '{{ inventory_hostname }}'
      state: present
  delegate_to: localhost

- name: Mount NFS datastores to ESXi
  vmware_host_datastore:
      hostname: '{{ vcenter_hostname }}'
      username: '{{ vcenter_user }}'
      password: '{{ vcenter_pass }}'
      datacenter_name: '{{ datacenter }}'
      datastore_name: '{{ item.name }}'
      datastore_type: '{{ item.type }}'
      nfs_server: '{{ item.server }}'
      nfs_path: '{{ item.path }}'
      nfs_ro: no
      esxi_hostname: '{{ inventory_hostname }}'
      state: present
  delegate_to: localhost
  with_items:
      - { 'name': 'NasDS_vol01', 'server': 'nas01', 'path': '/mnt/vol01', 'type': 'nfs'}
      - { 'name': 'NasDS_vol02', 'server': 'nas01', 'path': '/mnt/vol02', 'type': 'nfs'}

- name: Remove/Umount Datastores from ESXi
  vmware_host_datastore:
      hostname: '{{ vcenter_hostname }}'
      username: '{{ vcenter_user }}'
      password: '{{ vcenter_pass }}'
      datacenter_name: '{{ datacenter }}'
      datastore_name: NasDS_vol01
      esxi_hostname: '{{ inventory_hostname }}'
      state: absent
  delegate_to: localhost
'''

RETURN = r'''
'''

try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import connect_to_api, vmware_argument_spec, PyVmomi, find_datastore_by_name
from ansible.module_utils._text import to_native


class VMwareHostDatastore(PyVmomi):
    def __init__(self, module):
        self.module = module
        self.datacenter_name = module.params['datacenter_name']
        self.datastore_name = module.params['datastore_name']
        self.datastore_type = module.params['datastore_type']
        self.nfs_server = module.params['nfs_server']
        self.nfs_path = module.params['nfs_path']
        self.nfs_ro = module.params['nfs_ro']
        self.vmfs_device_name = module.params['vmfs_device_name']
        self.vmfs_version = module.params['vmfs_version']
        self.esxi_hostname = module.params['esxi_hostname']
        self.state = module.params['state']
        self.content = connect_to_api(module)
        self.esxi = self.find_hostsystem_by_name(self.esxi_hostname)

    def process_state(self):
        ds_states = {
            'absent': {
                'present': self.umount_datastore_host,
                'absent': self.state_exit_unchanged,
            },
            'present': {
                'present': self.state_exit_unchanged,
                'absent': self.mount_datastore_host,
            }
        }
        try:
            ds_states[self.state][self.check_datastore_host_state()]()

        except (vmodl.RuntimeFault, vmodl.MethodFault) as vmodl_fault:
            self.module.fail_json(msg=vmodl_fault.msg)
        except Exception as e:
            self.module.fail_json(msg=str(e))

    def state_exit_unchanged(self):
        self.module.exit_json(changed=False)

    def check_datastore_host_state(self):
        storage_system = self.esxi.configManager.storageSystem
        host_file_sys_vol_mount_info = storage_system.fileSystemVolumeInfo.mountInfo
        for host_mount_info in host_file_sys_vol_mount_info:
            if host_mount_info.volume.name == self.datastore_name:
                return 'present'
        return 'absent'

    def umount_datastore_host(self):
        ds = find_datastore_by_name(self.content, self.datastore_name)
        if not ds:
            self.module.fail_json(msg="No datastore found with name %s" % self.datastore_name)
        error_message_umount = "Cannot umount datastore %s from host %s" % (self.datastore_name, self.esxi_hostname)
        try:
            self.esxi.configManager.datastoreSystem.RemoveDatastore(ds)
        except (vim.fault.NotFound, vim.fault.HostConfigFault, vim.fault.ResourceInUse) as fault:
            self.module.fail_json(msg="%s: %s" % (error_message_umount, to_native(fault.msg)))
        except Exception as e:
            self.module.fail_json(msg="%s: %s" % (error_message_umount, str(e)))
        self.module.exit_json(changed=True, result="datastore %s on host %s" % (self.datastore_name, self.esxi_hostname))

    def mount_datastore_host(self):
        if self.datastore_type == 'nfs':
            self.mount_nfs_datastore_host()
        if self.datastore_type == 'vmfs':
            self.mount_vmfs_datastore_host()

    def mount_nfs_datastore_host(self):
        mnt_specs = vim.host.NasVolume.Specification()
        mnt_specs.remoteHost = self.nfs_server
        mnt_specs.remotePath = self.nfs_path
        mnt_specs.localPath = self.datastore_name
        if self.nfs_ro:
            mnt_specs.accessMode = "readOnly"
        else:
            mnt_specs.accessMode = "readWrite"
        error_message_mount = "Cannot mount datastore %s on host %s" % (self.datastore_name, self.esxi_hostname)
        try:
            ds = self.esxi.configManager.datastoreSystem.CreateNasDatastore(mnt_specs)
            if not ds:
                self.module.fail_json(msg=error_message_mount)
        except (vim.fault.NotFound, vim.fault.DuplicateName,
                vim.fault.AlreadyExists, vim.fault.HostConfigFault,
                vmodl.fault.InvalidArgument, vim.fault.NoVirtualNic,
                vim.fault.NoGateway) as fault:
            self.module.fail_json(msg="%s: %s" % (error_message_mount, to_native(fault.msg)))
        except Exception as e:
            self.module.fail_json(msg="%s : %s" % (error_message_mount, str(e)))
        self.module.exit_json(changed=True, result="datastore %s on host %s" % (self.datastore_name, self.esxi_hostname))

    def mount_vmfs_datastore_host(self):
        ds_path = "/vmfs/devices/disks/" + str(self.vmfs_device_name)
        host_ds_system = self.esxi.configManager.datastoreSystem
        ds_system = vim.host.DatastoreSystem
        error_message_mount = "Cannot mount datastore %s on host %s" % (self.datastore_name, self.esxi_hostname)
        try:
            vmfs_ds_options = ds_system.QueryVmfsDatastoreCreateOptions(host_ds_system,
                                                                        ds_path,
                                                                        self.vmfs_version)
            vmfs_ds_options[0].spec.vmfs.volumeName = self.datastore_name
            ds = ds_system.CreateVmfsDatastore(host_ds_system,
                                               vmfs_ds_options[0].spec)
        except (vim.fault.NotFound, vim.fault.DuplicateName,
                vim.fault.HostConfigFault, vmodl.fault.InvalidArgument) as fault:
            self.module.fail_json(msg="%s : %s" % (error_message_mount, to_native(fault.msg)))
        except Exception as e:
            self.module.fail_json(msg="%s : %s" % (error_message_mount, str(e)))
        self.module.exit_json(changed=True, result="datastore %s on host %s" % (self.datastore_name, self.esxi_hostname))


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        datacenter_name=dict(type='str', required=True),
        datastore_name=dict(type='str', required=True),
        datastore_type=dict(type='str', choices=['nfs', 'vmfs']),
        nfs_server=dict(type='str'),
        nfs_path=dict(type='str'),
        nfs_ro=dict(type='bool', default=False),
        vmfs_device_name=dict(type='str'),
        vmfs_version=dict(type='int'),
        esxi_hostname=dict(type='str', required=True),
        state=dict(type='str', default='present', choices=['absent', 'present'])
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_together=[
            [ 'nfs_server', 'nfs_path' ]
        ]
    )

    # more complex required_if
    if module.params['state'] == 'present':
        if module.params['datastore_type'] == 'nfs' and not module.params['nfs_server']:
            msg = "Missing nfs_server with datastore_type = nfs"
            module.fail_json(msg=msg)

        if module.params['datastore_type'] == 'vmfs' and not module.params['vmfs_device_name']:
            msg = "Missing vmfs_device_name with datastore_type = vmfs"
            module.fail_json(msg=msg)

    if not HAS_PYVMOMI:
        module.fail_json(msg='pyvmomi is required for this module')

    vmware_host_datastore = VMwareHostDatastore(module)
    vmware_host_datastore.process_state()


if __name__ == '__main__':
    main()
