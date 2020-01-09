#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2018, Ansible Project
# Copyright (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
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
module: vmware_datastore_cluster
short_description: Manage VMware vSphere datastore clusters
description:
    - This module can be used to add and delete datastore cluster in given VMware environment.
    - All parameters and VMware object values are case sensitive.
version_added: 2.6
author:
-  Abhijeet Kasurde (@Akasurde)
notes:
    - Tested on vSphere 6.0, 6.5
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
    datacenter_name:
      description:
      - The name of the datacenter.
      - You must specify either a C(datacenter_name) or a C(folder).
      - Mutually exclusive with C(folder) parameter.
      required: False
      aliases: [ datacenter ]
      type: str
    datastore_cluster_name:
      description:
      - The name of the datastore cluster.
      required: True
      type: str
    state:
      description:
      - If the datastore cluster should be present or absent.
      choices: [ present, absent ]
      default: present
      type: str
    folder:
      description:
      - Destination folder, absolute path to place datastore cluster in.
      - The folder should include the datacenter.
      - This parameter is case sensitive.
      - You must specify either a C(folder) or a C(datacenter_name).
      - 'Examples:'
      - '   folder: /datacenter1/datastore'
      - '   folder: datacenter1/datastore'
      - '   folder: /datacenter1/datastore/folder1'
      - '   folder: datacenter1/datastore/folder1'
      - '   folder: /folder1/datacenter1/datastore'
      - '   folder: folder1/datacenter1/datastore'
      - '   folder: /folder1/datacenter1/datastore/folder2'
      required: False
      version_added: '2.9'
      type: str
    enable_sdrs:
      description:
      - Whether or not storage DRS is enabled.
      default: False
      type: bool
      required: False
      version_added: '2.10'
    automation_level:
      description:
      - Run SDRS automated or manually.
      choices: [ automated, manual ]
      default: manual
      type: str
      required: False
      version_added: '2.10'
    keep_vmdks_together:
      description:
      - Specifies whether or not each VM in this datastore cluster should have its virtual disks on the same datastore by default.
      default: True
      type: bool
      required: False
      version_added: '2.10'
    loadbalance_interval:
      description:
      - Specify the interval in minutes that storage DRS runs to load balance among datastores.
      default: 480
      type: int
      required: False
      version_added: '2.10'
    enable_io_loadbalance:
      description:
      - Whether or not storage DRS takes into account storage I/O workload when making load balancing and initial placement recommendations.
      default: False
      type: bool
      required: False
      version_added: '2.10'
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: Create datastore cluster and enable SDRS
  vmware_datastore_cluster:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter_name: '{{ datacenter_name }}'
    datastore_cluster_name: '{{ datastore_cluster_name }}'
    enable_sdrs: True
    state: present
  delegate_to: localhost

- name: Create datastore cluster using folder
  vmware_datastore_cluster:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    folder: '/{{ datacenter_name }}/datastore/ds_folder'
    datastore_cluster_name: '{{ datastore_cluster_name }}'
    state: present
  delegate_to: localhost

- name: Delete datastore cluster
  vmware_datastore_cluster:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter_name: '{{ datacenter_name }}'
    datastore_cluster_name: '{{ datastore_cluster_name }}'
    state: absent
  delegate_to: localhost
'''

RETURN = """
result:
    description: information about datastore cluster operation
    returned: always
    type: str
    sample: "Datastore cluster 'DSC2' created successfully."
"""

try:
    from pyVmomi import vim
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec, wait_for_task
from ansible.module_utils._text import to_native


class VMwareDatastoreClusterManager(PyVmomi):
    def __init__(self, module):
        super(VMwareDatastoreClusterManager, self).__init__(module)
        folder = self.params['folder']
        if folder:
            self.folder_obj = self.content.searchIndex.FindByInventoryPath(folder)
            if not self.folder_obj:
                self.module.fail_json(msg="Failed to find the folder specified by %(folder)s" % self.params)
        else:
            datacenter_name = self.params.get('datacenter_name')
            datacenter_obj = self.find_datacenter_by_name(datacenter_name)
            if not datacenter_obj:
                self.module.fail_json(msg="Failed to find datacenter '%s' required"
                                          " for managing datastore cluster." % datacenter_name)
            self.folder_obj = datacenter_obj.datastoreFolder

        self.datastore_cluster_name = self.params.get('datastore_cluster_name')
        self.datastore_cluster_obj = self.find_datastore_cluster_by_name(self.datastore_cluster_name)

    def ensure(self):
        """
        Manage internal state of datastore cluster

        """
        results = dict(changed=False, result='')
        state = self.module.params.get('state')
        enable_sdrs = self.params.get('enable_sdrs')
        automation_level = self.params.get('automation_level')
        keep_vmdks_together = self.params.get('keep_vmdks_together')
        enable_io_loadbalance = self.params.get('enable_io_loadbalance')
        loadbalance_interval = self.params.get('loadbalance_interval')

        if self.datastore_cluster_obj:
            if state == 'present':
                results['result'] = "Datastore cluster '%s' already available." % self.datastore_cluster_name
                sdrs_spec = vim.storageDrs.ConfigSpec()
                sdrs_spec.podConfigSpec = None
                if enable_sdrs != self.datastore_cluster_obj.podStorageDrsEntry.storageDrsConfig.podConfig.enabled:
                    if not sdrs_spec.podConfigSpec:
                        sdrs_spec.podConfigSpec = vim.storageDrs.PodConfigSpec()
                    sdrs_spec.podConfigSpec.enabled = enable_sdrs
                    results['result'] = results['result'] + " Changed SDRS to '%s'." % enable_sdrs
                if automation_level != self.datastore_cluster_obj.podStorageDrsEntry.storageDrsConfig.podConfig.defaultVmBehavior:
                    if not sdrs_spec.podConfigSpec:
                        sdrs_spec.podConfigSpec = vim.storageDrs.PodConfigSpec()
                    sdrs_spec.podConfigSpec.defaultVmBehavior = automation_level
                    results['result'] = results['result'] + " Changed automation level to '%s'." % automation_level
                if keep_vmdks_together != self.datastore_cluster_obj.podStorageDrsEntry.storageDrsConfig.podConfig.defaultIntraVmAffinity:
                    if not sdrs_spec.podConfigSpec:
                        sdrs_spec.podConfigSpec = vim.storageDrs.PodConfigSpec()
                    sdrs_spec.podConfigSpec.defaultIntraVmAffinity = keep_vmdks_together
                    results['result'] = results['result'] + " Changed VMDK affinity to '%s'." % keep_vmdks_together
                if enable_io_loadbalance != self.datastore_cluster_obj.podStorageDrsEntry.storageDrsConfig.podConfig.ioLoadBalanceEnabled:
                    if not sdrs_spec.podConfigSpec:
                        sdrs_spec.podConfigSpec = vim.storageDrs.PodConfigSpec()
                    sdrs_spec.podConfigSpec.ioLoadBalanceEnabled = enable_io_loadbalance
                    results['result'] = results['result'] + " Changed I/O workload balancing to '%s'." % enable_io_loadbalance
                if loadbalance_interval != self.datastore_cluster_obj.podStorageDrsEntry.storageDrsConfig.podConfig.loadBalanceInterval:
                    if not sdrs_spec.podConfigSpec:
                        sdrs_spec.podConfigSpec = vim.storageDrs.PodConfigSpec()
                    sdrs_spec.podConfigSpec.loadBalanceInterval = loadbalance_interval
                    results['result'] = results['result'] + " Changed load balance interval to '%s' minutes." % loadbalance_interval
                if sdrs_spec.podConfigSpec:
                    if not self.module.check_mode:
                        try:
                            task = self.content.storageResourceManager.ConfigureStorageDrsForPod_Task(pod=self.datastore_cluster_obj,
                                                                                                      spec=sdrs_spec, modify=True)
                            changed, result = wait_for_task(task)
                        except Exception as generic_exc:
                            self.module.fail_json(msg="Failed to configure datastore cluster"
                                                      " '%s' due to %s" % (self.datastore_cluster_name,
                                                                           to_native(generic_exc)))
                    else:
                        changed = True
                    results['changed'] = changed
            elif state == 'absent':
                # Delete datastore cluster
                if not self.module.check_mode:
                    task = self.datastore_cluster_obj.Destroy_Task()
                    changed, result = wait_for_task(task)
                else:
                    changed = True
                if changed:
                    results['result'] = "Datastore cluster '%s' deleted successfully." % self.datastore_cluster_name
                    results['changed'] = changed
                else:
                    self.module.fail_json(msg="Failed to delete datastore cluster '%s'." % self.datastore_cluster_name)
        else:
            if state == 'present':
                # Create datastore cluster
                if not self.module.check_mode:
                    try:
                        self.datastore_cluster_obj = self.folder_obj.CreateStoragePod(name=self.datastore_cluster_name)
                    except Exception as generic_exc:
                        self.module.fail_json(msg="Failed to create datastore cluster"
                                                  " '%s' due to %s" % (self.datastore_cluster_name,
                                                                       to_native(generic_exc)))
                    try:
                        sdrs_spec = vim.storageDrs.ConfigSpec()
                        sdrs_spec.podConfigSpec = vim.storageDrs.PodConfigSpec()
                        sdrs_spec.podConfigSpec.enabled = enable_sdrs
                        sdrs_spec.podConfigSpec.defaultVmBehavior = automation_level
                        sdrs_spec.podConfigSpec.defaultIntraVmAffinity = keep_vmdks_together
                        sdrs_spec.podConfigSpec.ioLoadBalanceEnabled = enable_io_loadbalance
                        sdrs_spec.podConfigSpec.loadBalanceInterval = loadbalance_interval
                        task = self.content.storageResourceManager.ConfigureStorageDrsForPod_Task(pod=self.datastore_cluster_obj, spec=sdrs_spec, modify=True)
                        changed, result = wait_for_task(task)
                    except Exception as generic_exc:
                        self.module.fail_json(msg="Failed to configure datastore cluster"
                                                  " '%s' due to %s" % (self.datastore_cluster_name,
                                                                       to_native(generic_exc)))
                results['changed'] = True
                results['result'] = "Datastore cluster '%s' created successfully." % self.datastore_cluster_name
            elif state == 'absent':
                results['result'] = "Datastore cluster '%s' not available or already deleted." % self.datastore_cluster_name
        self.module.exit_json(**results)


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        dict(
            datacenter_name=dict(type='str', required=False, aliases=['datacenter']),
            datastore_cluster_name=dict(type='str', required=True),
            state=dict(default='present', choices=['present', 'absent'], type='str'),
            folder=dict(type='str', required=False),
            enable_sdrs=dict(type='bool', default=False, required=False),
            keep_vmdks_together=dict(type='bool', default=True, required=False),
            automation_level=dict(type='str', choices=['automated', 'manual'], default='manual'),
            enable_io_loadbalance=dict(type='bool', default=False, required=False),
            loadbalance_interval=dict(type='int', default=480, required=False)
        )
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[
            ['datacenter_name', 'folder'],
        ],
        required_one_of=[
            ['datacenter_name', 'folder'],
        ]
    )

    datastore_cluster_mgr = VMwareDatastoreClusterManager(module)
    datastore_cluster_mgr.ensure()


if __name__ == '__main__':
    main()
