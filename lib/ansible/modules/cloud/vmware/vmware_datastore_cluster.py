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
      required: True
    datastore_cluster_name:
      description:
      - The name of the datastore cluster.
      required: True
    state:
      description:
      - If the datastore cluster should be present or absent.
      choices: [ present, absent ]
      default: present
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: Create datastore cluster
  vmware_datastore_cluster:
    hostname: vCenter
    username: root
    password: vmware
    datacenter_name: "datacenter"
    datastore_cluster_name: datacluster0
    state: present


- name: Delete datastore cluster
  vmware_datastore_cluster:
    hostname: vCenter
    username: root
    password: vmware
    datacenter_name: "datacenter"
    datastore_cluster_name: datacluster0
    state: absent
'''

RETURN = """
result:
    description: information about datastore cluster operation
    returned: always
    type: string
    sample: "Datastore cluster 'DSC2' created successfully."
"""

try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec, wait_for_task
from ansible.module_utils._text import to_native


class VMwareDatastoreClusterManager(PyVmomi):
    def __init__(self, module):
        super(VMwareDatastoreClusterManager, self).__init__(module)
        datacenter_name = self.params.get('datacenter_name')
        self.datacenter_obj = self.find_datacenter_by_name(datacenter_name)
        if not self.datacenter_obj:
            self.module.fail_json(msg="Failed to find datacenter '%s' required"
                                      " for managing datastore cluster." % datacenter_name)
        self.datastore_cluster_name = self.params.get('datastore_cluster_name')
        self.datastore_cluster_obj = self.find_datastore_cluster_by_name(self.datastore_cluster_name)

    def ensure(self):
        """
        Function to manage internal state of datastore cluster

        """
        results = dict(changed=False, result='')
        state = self.module.params.get('state')

        if self.datastore_cluster_obj:
            if state == 'present':
                results['result'] = "Datastore cluster '%s' already available." % self.datastore_cluster_name
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
                        self.datacenter_obj.datastoreFolder.CreateStoragePod(name=self.datastore_cluster_name)
                    except Exception as generic_exc:
                        self.module.fail_json(msg="Failed to create datstore cluster"
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
            datacenter_name=dict(type='str', required=True),
            datastore_cluster_name=dict(type='str', required=True),
            state=dict(default='present', choices=['present', 'absent'], type='str'),
        )
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    datastore_cluster_mgr = VMwareDatastoreClusterManager(module)
    datastore_cluster_mgr.ensure()


if __name__ == '__main__':
    main()
