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
module: vmware_datastore_host
short_description: Add/remove datastore on ESXi host
description:
- This module can be used to mount/umount on datastore on ESXi host.
- Currently, this module only support NFS datastore type but it's planned to add vmfs support.
version_added: '1.0'
author:
- Ludovic Rivallain <ludovic.rivallain@gmail.com>
notes:
- Tested on vSphere 6.0, 6.5
requirements:
- python >= 2.6
- PyVmomi
options:
  datacenter_name:
    description:
    - Name of the datacenter to add the host.
    required: yes
  datastore_name:
    description:
    - Name of the datastore to add/remove.
    required: yes
  datastore_type:
    description:
    - Type of the datastore to configure (nfs/vmfs).
    - required: yes
  nfs_server:
    description:
    - NFS host serving nfs datastore.
    - Required for nfs datastore type
    - Unused for others types
  nfs_path:
    description:
    - Resource path on NFS host.
    - Required for nfs datastore type
    - Unused for others types
  nfs_ro:
    description:
    - ReadOnly or ReadWrite mount.
    - Required for nfs datastore type
    - Unused for others types
    default: False
  esxi_hostname:
    description:
    - ESXi hostname to mount the datastore.
    required: yes
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
  vmware_datastore_host:
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
  vmware_datastore_host:
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
  vmware_datastore_host:
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
from ansible.module_utils.vmware import connect_to_api, vmware_argument_spec


class VMwareDatastoreHost(object):
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
        self.esxi = self.get_esx_view()


    def process_state(self):
        try:
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
            ds_states[self.state][self.check_datastore_host_state()]()

        except vmodl.RuntimeFault as runtime_fault:
            self.module.fail_json(msg=runtime_fault.msg)
        except vmodl.MethodFault as method_fault:
            self.module.fail_json(msg=method_fault.msg)
        except Exception as e:
            self.module.fail_json(msg=str(e))


    def state_exit_unchanged(self):
        self.module.exit_json(changed=False)


    def get_esx_view(self):
        object_view = self.content.viewManager.CreateContainerView(self.content.rootFolder,
                                                                   [vim.HostSystem],
                                                                   True)
        host_list = object_view.view
        object_view.Destroy()

        for host in host_list:
            if host.name == self.esxi_hostname:
                return host
        self.module.fail_json(msg="No ESXi found with name %s" % self.esxi_hostname)


    def get_ds_view(self):
        object_view = self.content.viewManager.CreateContainerView(self.content.rootFolder,
                                                                   [vim.Datastore],
                                                                   True)
        ds_list = object_view.view
        object_view.Destroy()

        for ds in ds_list:
            if ds.name == self.datastore_name:
                return ds
        self.module.fail_json(msg="No datastore found with name %s" % self.datastore_name)


    def check_datastore_host_state(self):
        storage_system = self.esxi.configManager.storageSystem
        host_file_sys_vol_mount_info = storage_system.fileSystemVolumeInfo.mountInfo
        datastore_dict = {}
        for host_mount_info in host_file_sys_vol_mount_info:
            if host_mount_info.volume.name == self.datastore_name:
                return 'present'
        return 'absent'


    def umount_datastore_host(self):
        ds = self.get_ds_view()
        error_message_umount = "Cannot umount datastore %s from host %s" % (self.datastore_name, self.esxi_hostname)
        try:
            self.esxi.configManager.datastoreSystem.RemoveDatastore(ds)
        except vim.fault.NotFound:
            self.module.fail_json(msg=error_message_umount + ": NotFound")
        except vim.fault.HostConfigFault:
            self.module.fail_json(msg=error_message_umount + ": HostConfigFault")
        except vim.fault.ResourceInUse:
            self.module.fail_json(msg=error_message_umount + ": ResourceInUse")
        except Exception as e:
            self.module.fail_json(msg=error_message_umount + ": " + str(e))
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
            mnt_specs.accessMode="readOnly"
        else:
            mnt_specs.accessMode="readWrite"
        error_message_mount = "Cannot mount datastore %s on host %s" % (self.datastore_name, self.esxi_hostname)
        try:
            ds = self.esxi.configManager.datastoreSystem.CreateNasDatastore(mnt_specs)
            if not ds:
                self.module.fail_json(msg=error_message_mount)
        except vim.fault.DuplicateName:
            self.module.fail_json(msg=error_message_mount + ": A datastore with the same name already exists")
        except vim.fault.AlreadyExists:
            self.module.fail_json(msg=error_message_mount + ": The local path already exists on the host, or the remote path is already mounted on the host")
        except vim.fault.HostConfigFault:
            self.module.fail_json(msg=error_message_mount + ": Unable to mount the NAS volume")
        except vmodl.fault.InvalidArgument:
            self.module.fail_json(msg=error_message_mount + ": The datastore name is invalid, or the spec is invalid")
        except vim.fault.NoVirtualNic:
            self.module.fail_json(msg=error_message_mount + ": VMkernel TCPIP stack is not configured for NFS data")
        except vim.fault.NoGateway:
            self.module.fail_json(msg=error_message_mount + ": VMkernel gateway is not configured")
        except Exception as e:
            self.module.fail_json(msg=error_message_mount + ": " + str(e))
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
        except vim.fault.NotFound:
            self.module.fail_json(msg=error_message_mount + ": Device is not found")
        except vim.fault.HostConfigFault:
            self.module.fail_json(msg=error_message_mount + ": Unable to format the VMFS volume or gather information about the created volume")
        except vim.fault.DuplicateName:
            self.module.fail_json(msg=error_message_mount + ": A datastore with the same name already exists")
        except vmodl.fault.InvalidArgument:
            self.module.fail_json(msg=error_message_mount + ": The datastore name is invalid, or the spec is invalid")
        except Exception as e:
            self.module.fail_json(msg=error_message_mount + ": " + str(e))
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
    )

    # more complex required_if
    if module.params['state'] == 'present':
        if module.params['datastore_type'] == 'nfs' and \
           not (module.params['nfs_server'] and module.params['nfs_path']):
            msg = "Missing nfs_server or nfs_path with datastore_type = nfs"
            module.fail_json(msg=msg)

        if module.params['datastore_type'] == 'vmfs' and \
           not module.params['vmfs_device_name']:
            msg = "Missing vmfs_device_name with datastore_type = vmfs"
            module.fail_json(msg=msg)

    if not HAS_PYVMOMI:
        module.fail_json(msg='pyvmomi is required for this module')

    vmware_datastore_host = VMwareDatastoreHost(module)
    vmware_datastore_host.process_state()


if __name__ == '__main__':
    main()
