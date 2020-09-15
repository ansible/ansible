#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Ansible Project
# Copyright: (c) 2019, Pavan Bidkar <pbidkar@vmware.com>
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
module: vmware_content_deploy_template
short_description: Deploy Virtual Machine from template stored in content library.
description:
- Module to deploy virtual machine from template in content library.
- Content Library feature is introduced in vSphere 6.0 version, so this module is not supported in the earlier versions of vSphere.
- All variables and VMware object names are case sensitive.
version_added: '2.9'
author:
- Pavan Bidkar (@pgbidkar)
notes:
- Tested on vSphere 6.7 U3
requirements:
- python >= 2.6
- PyVmomi
- vSphere Automation SDK
options:
    template:
      description:
      - The name of template from which VM to be deployed.
      type: str
      required: True
      aliases: ['template_src']
    name:
      description:
      - The name of the VM to be deployed.
      type: str
      required: True
      aliases: ['vm_name']
    datacenter:
      description:
      - Name of the datacenter, where VM to be deployed.
      type: str
      required: True
    datastore:
      description:
      - Name of the datastore to store deployed VM and disk.
      type: str
      required: True
    folder:
      description:
      - Name of the folder in datacenter in which to place deployed VM.
      type: str
      required: True
    host:
      description:
      - Name of the ESX Host in datacenter in which to place deployed VM.
      type: str
      required: True
    resource_pool:
      description:
      - Name of the resourcepool in datacenter in which to place deployed VM.
      type: str
      required: False
    cluster:
      description:
      - Name of the cluster in datacenter in which to place deployed VM.
      type: str
      required: False
    state:
      description:
      - The state of Virtual Machine deployed from template in content library.
      - If set to C(present) and VM does not exists, then VM is created.
      - If set to C(present) and VM exists, no action is taken.
      - If set to C(poweredon) and VM does not exists, then VM is created with powered on state.
      - If set to C(poweredon) and VM exists, no action is taken.
      type: str
      required: False
      default: 'present'
      choices: [ 'present', 'poweredon' ]
extends_documentation_fragment: vmware_rest_client.documentation
'''

EXAMPLES = r'''
- name: Deploy Virtual Machine from template in content library
  vmware_content_deploy_template:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    template: rhel_test_template
    datastore: Shared_NFS_Volume
    folder: vm
    datacenter: Sample_DC_1
    name: Sample_VM
    resource_pool: test_rp
    validate_certs: False
    state: present
  delegate_to: localhost

- name: Deploy Virtual Machine from template in content library with PowerON State
  vmware_content_deploy_template:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    template: rhel_test_template
    datastore: Shared_NFS_Volume
    folder: vm
    datacenter: Sample_DC_1
    name: Sample_VM
    resource_pool: test_rp
    validate_certs: False
    state: poweredon
  delegate_to: localhost
'''

RETURN = r'''
vm_deploy_info:
  description: Virtual machine deployment message and vm_id
  returned: on success
  type: dict
  sample: {
        "msg": "Deployed Virtual Machine 'Sample_VM'.",
        "vm_id": "vm-1009"
    }
'''

import uuid
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware_rest_client import VmwareRestClient
from ansible.module_utils.vmware import PyVmomi
from ansible.module_utils._text import to_native

HAS_VAUTOMATION_PYTHON_SDK = False
try:
    from com.vmware.vcenter.vm_template_client import LibraryItems
    HAS_VAUTOMATION_PYTHON_SDK = True
except ImportError:
    pass


class VmwareContentDeployTemplate(VmwareRestClient):
    def __init__(self, module):
        """Constructor."""
        super(VmwareContentDeployTemplate, self).__init__(module)
        self.template_service = self.api_client.vcenter.vm_template.LibraryItems
        self.template_name = self.params.get('template')
        self.vm_name = self.params.get('name')
        self.datacenter = self.params.get('datacenter')
        self.datastore = self.params.get('datastore')
        self.folder = self.params.get('folder')
        self.resourcepool = self.params.get('resource_pool')
        self.cluster = self.params.get('cluster')
        self.host = self.params.get('host')

    def deploy_vm_from_template(self, power_on=False):
        # Find the datacenter by the given datacenter name
        self.datacenter_id = self.get_datacenter_by_name(datacenter_name=self.datacenter)
        if not self.datacenter_id:
            self.module.fail_json(msg="Failed to find the datacenter %s" % self.datacenter)
        # Find the datastore by the given datastore name
        self.datastore_id = self.get_datastore_by_name(self.datacenter, self.datastore)
        if not self.datastore_id:
            self.module.fail_json(msg="Failed to find the datastore %s" % self.datastore)
        # Find the LibraryItem (Template) by the given LibraryItem name
        self.library_item_id = self.get_library_item_by_name(self.template_name)
        if not self.library_item_id:
            self.module.fail_json(msg="Failed to find the library Item %s" % self.template_name)
        # Find the folder by the given folder name
        self.folder_id = self.get_folder_by_name(self.datacenter, self.folder)
        if not self.folder_id:
            self.module.fail_json(msg="Failed to find the folder %s" % self.folder)
        # Find the Host by given HostName
        self.host_id = self.get_host_by_name(self.datacenter, self.host)
        if not self.host_id:
            self.module.fail_json(msg="Failed to find the Host %s" % self.host)
        # Find the resourcepool by the given resourcepool name
        self.resourcepool_id = None
        if self.resourcepool:
            self.resourcepool_id = self.get_resource_pool_by_name(self.datacenter, self.resourcepool)
            if not self.resourcepool_id:
                self.module.fail_json(msg="Failed to find the resource_pool %s" % self.resourcepool)
        # Find the Cluster by the given Cluster name
        self.cluster_id = None
        if self.cluster:
            self.cluster_id = self.get_cluster_by_name(self.datacenter, self.cluster)
            if not self.cluster_id:
                self.module.fail_json(msg="Failed to find the Cluster %s" % self.cluster)
        # Create VM placement specs
        self.placement_spec = LibraryItems.DeployPlacementSpec(folder=self.folder_id,
                                                               host=self.host_id
                                                               )
        if self.resourcepool_id or self.cluster_id:
            self.placement_spec.resource_pool = self.resourcepool_id
            self.placement_spec.cluster = self.cluster_id
        self.vm_home_storage_spec = LibraryItems.DeploySpecVmHomeStorage(datastore=to_native(self.datastore_id))
        self.disk_storage_spec = LibraryItems.DeploySpecDiskStorage(datastore=to_native(self.datastore_id))
        self.deploy_spec = LibraryItems.DeploySpec(name=self.vm_name,
                                                   placement=self.placement_spec,
                                                   vm_home_storage=self.vm_home_storage_spec,
                                                   disk_storage=self.disk_storage_spec,
                                                   powered_on=power_on
                                                   )
        vm_id = self.template_service.deploy(self.library_item_id, self.deploy_spec)
        if vm_id:
            self.module.exit_json(
                changed=True,
                vm_deploy_info=dict(
                    msg="Deployed Virtual Machine '%s'." % self.vm_name,
                    vm_id=vm_id,
                )
            )
        self.module.exit_json(changed=False,
                              vm_deploy_info=dict(msg="Virtual Machine deployment failed", vm_id=''))


def main():
    argument_spec = VmwareRestClient.vmware_client_argument_spec()
    argument_spec.update(
        state=dict(type='str', default='present',
                   choices=['present', 'poweredon']),
        template=dict(type='str', aliases=['template_src'], required=True),
        name=dict(type='str', required=True, aliases=['vm_name']),
        datacenter=dict(type='str', required=True),
        datastore=dict(type='str', required=True),
        folder=dict(type='str', required=True),
        host=dict(type='str', required=True),
        resource_pool=dict(type='str', required=False),
        cluster=dict(type='str', required=False),
    )
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)
    result = {'failed': False, 'changed': False}
    pyv = PyVmomi(module=module)
    vm = pyv.get_vm()
    if vm:
        module.exit_json(
            changed=False,
            vm_deploy_info=dict(
                msg="Virtual Machine '%s' already Exists." % module.params['name'],
                vm_id=vm._moId,
            )
        )
    vmware_contentlib_create = VmwareContentDeployTemplate(module)
    if module.params['state'] in ['present']:
        if module.check_mode:
            result.update(
                vm_name=module.params['name'],
                changed=True,
                desired_operation='Create VM with PowerOff State',
            )
            module.exit_json(**result)
        vmware_contentlib_create.deploy_vm_from_template()
    if module.params['state'] == 'poweredon':
        if module.check_mode:
            result.update(
                vm_name=module.params['name'],
                changed=True,
                desired_operation='Create VM with PowerON State',
            )
            module.exit_json(**result)
        vmware_contentlib_create.deploy_vm_from_template(power_on=True)


if __name__ == '__main__':
    main()
