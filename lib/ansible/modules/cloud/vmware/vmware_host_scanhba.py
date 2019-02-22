#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Ansible Project
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
module: vmware_host_scanhba
short_description: Rescan host HBA's and optionally refresh the storage system
description:
- This module can force a rescan of the hosts HBA subsystem which is needed when wanting to mount a new datastore.
- You could use this before using vmware_host_datastore to mount a new datastore to ensure your device/volume is ready.
- You can also optionally force a Refresh of the Storage System in vCenter/ESXi Web Client.
- All parameters and VMware object names are case sensitive.
- You can supply an esxi_hostname or a cluster_name
version_added: '2.8'
author:
- Michael Eaton (@michaeldeaton)
notes:
- Tested on vSphere 6.0
requirements:
- python >= 2.6
- PyVmomi
options:
  esxi_hostname:
    description:
    - ESXi hostname to Rescan the storage subsystem on.
    required: false
  cluster_name:
    description:
    - Cluster name to Rescan the storage subsystem on (this will run the rescan task on each host in the cluster).
    required: false
  refresh_storage:
    description:
    - Refresh the storage system in vCenter/ESXi Web Client for each host found
    required: false
    default: false
    type: bool
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Recan HBA's for a given ESXi host and refresh storage system objects
  vmware_host_scanhba:
      hostname: '{{ vcenter_hostname }}'
      username: '{{ vcenter_username }}'
      password: '{{ vcenter_password }}'
      esxi_hostname: '{{ inventory_hostname }}'
      refresh_storage: true
  delegate_to: localhost

- name: Rescan HBA's for a given cluster - all found hosts will be scanned
  vmware_host_scanhba:
      hostname: '{{ vcenter_hostname }}'
      username: '{{ vcenter_username }}'
      password: '{{ vcenter_password }}'
      esxi_hostname: '{{ inventory_hostname }}'
      refresh_storage: true
  delegate_to: localhost

- name: Recan HBA's for a given ESXi host and don't refresh storage system objects
  vmware_host_scanhba:
      hostname: '{{ vcenter_hostname }}'
      username: '{{ vcenter_username }}'
      password: '{{ vcenter_password }}'
      esxi_hostname: '{{ inventory_hostname }}'
  delegate_to: localhost
'''

RETURN = r'''
result:
    description: return confirmation of requested host and updated / refreshed storage system
    returned: always
    type: dict
    sample: {
        "esxi01.example.com": {
            "rescaned_hba": "true",
            "refreshed_storage": "true"
        }
    }
'''

try:
    from pyVmomi import vim
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import vmware_argument_spec, PyVmomi, find_obj
from ansible.module_utils._text import to_native


class VmwareHbaScan(PyVmomi):
    def __init__(self, module):
        super(VmwareHbaScan, self).__init__(module)

    def scan(self):
        esxi_host_name = self.params.get('esxi_hostname', None)
        cluster_name = self.params.get('cluster_name', None)
        refresh_storage = self.params.get('refresh_storage', bool)
        hosts = self.get_all_host_objs(cluster_name=cluster_name, esxi_host_name=esxi_host_name)
        results = dict(changed=True, result=dict())

        if not hosts:
            self.module.fail_json(msg="Failed to find any hosts.")

        for host in hosts:
            results['result'][host.name] = dict()
            host.configManager.storageSystem.RescanAllHba()
            if refresh_storage is True:
                host.configManager.storageSystem.RefreshStorageSystem()

            results['result'][host.name]['rescaned_hba'] = True
            results['result'][host.name]['refreshed_storage'] = refresh_storage

        self.module.exit_json(**results)


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        esxi_hostname=dict(type='str', required=False),
        cluster_name=dict(type='str', required=False),
        refresh_storage=dict(type='bool', default=False, required=False)
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[
            ['cluster_name', 'esxi_hostname'],
        ],
        supports_check_mode=False
    )

    hbascan = VmwareHbaScan(module)
    hbascan.scan()


if __name__ == '__main__':
    main()
