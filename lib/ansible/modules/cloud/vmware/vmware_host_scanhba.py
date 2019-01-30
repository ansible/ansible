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
- You could use this before using M(vmware_host_datastore) to mount a new datastore to ensure your device/volume is ready.
- You can also optionally force refresh operation on the Storage System in vCenter/ESXi Web Client.
- All parameters and VMware object names are case sensitive.
version_added: '2.8'
author:
- Michael Eaton (@if-meaton)
notes:
- Tested on vSphere 6.0
requirements:
- python >= 2.6
- PyVmomi
options:
  esxi_hostname:
    description:
    - ESXi hostname to Rescan the storage subsystem on.
    required: true
  refresh_storage:
    description:
    - Refresh the storage system in vCenter/ESXi Web Client.
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
        refresh_storage = self.params.get('refresh_storage', bool)
        host = find_obj(self.content, [vim.HostSystem], name=esxi_host_name)

        if host is None:
          self.module.fail_json(msg="Unable to find host system %s in the given configuration." % esxi_host_name)

        host.configManager.storageSystem.RescanAllHba()
        if refresh_storage is True:
            host.configManager.storageSystem.RefreshStorageSystem()

        return_data = dict()

        return_data[host.name] = dict(
          rescaned_hba="true",
          refreshed_storage=refresh_storage
          )

        self.module.exit_json(changed=True, result=return_data)


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        esxi_hostname=dict(type='str', required=True),
        refresh_storage=dict(type='bool', default=False, required=False)
    )
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=False)

    hbascan = VmwareHbaScan(module)
    hbascan.scan()


if __name__ == '__main__':
    main()
