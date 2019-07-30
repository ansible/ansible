#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Ansible Project
# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
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
module: vmware_datastore_maintenancemode
short_description: Place a datastore into maintenance mode
description:
    - This module can be used to manage maintenance mode of a datastore.
author:
- "Abhijeet Kasurde (@Akasurde)"
version_added: 2.6
notes:
    - Tested on vSphere 5.5, 6.0 and 6.5
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
    datastore:
      description:
      - Name of datastore to manage.
      - If C(datastore_cluster) or C(cluster_name) are not set, this parameter is required.
      type: str
    datastore_cluster:
      description:
      - Name of the datastore cluster from all child datastores to be managed.
      - If C(datastore) or C(cluster_name) are not set, this parameter is required.
      type: str
    cluster_name:
      description:
      - Name of the cluster where datastore is connected to.
      - If multiple datastores are connected to the given cluster, then all datastores will be managed by C(state).
      - If C(datastore) or C(datastore_cluster) are not set, this parameter is required.
      type: str
    state:
      description:
      - If set to C(present), then enter datastore into maintenance mode.
      - If set to C(present) and datastore is already in maintenance mode, then no action will be taken.
      - If set to C(absent) and datastore is in maintenance mode, then exit maintenance mode.
      - If set to C(absent) and datastore is not in maintenance mode, then no action will be taken.
      choices: [ present, absent ]
      default: present
      required: False
      type: str
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: Enter datastore into Maintenance Mode
  vmware_datastore_maintenancemode:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datastore: '{{ datastore_name }}'
    state: present
  delegate_to: localhost

- name: Enter all datastores under cluster into Maintenance Mode
  vmware_datastore_maintenancemode:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    cluster_name: '{{ cluster_name }}'
    state: present
  delegate_to: localhost

- name: Enter all datastores under datastore cluster into Maintenance Mode
  vmware_datastore_maintenancemode:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datastore_cluster: '{{ datastore_cluster_name }}'
    state: present
  delegate_to: localhost

- name: Exit datastore into Maintenance Mode
  vmware_datastore_maintenancemode:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datastore: '{{ datastore_name }}'
    state: absent
  delegate_to: localhost
'''

RETURN = '''
results:
    description: Action taken for datastore
    returned: always
    type: dict
    sample:
'''

try:
    from pyVmomi import vim
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import (PyVmomi, vmware_argument_spec, wait_for_task,
                                         find_cluster_by_name, get_all_objs)
from ansible.module_utils._text import to_native


class VmwareDatastoreMaintenanceMgr(PyVmomi):
    def __init__(self, module):
        super(VmwareDatastoreMaintenanceMgr, self).__init__(module)
        datastore_name = self.params.get('datastore')
        cluster_name = self.params.get('cluster_name')
        datastore_cluster = self.params.get('datastore_cluster')
        self.datastore_objs = []
        if datastore_name:
            ds = self.find_datastore_by_name(datastore_name=datastore_name)
            if not ds:
                self.module.fail_json(msg='Failed to find datastore "%(datastore)s".' % self.params)
            self.datastore_objs = [ds]
        elif cluster_name:
            cluster = find_cluster_by_name(self.content, cluster_name)
            if not cluster:
                self.module.fail_json(msg='Failed to find cluster "%(cluster_name)s".' % self.params)
            self.datastore_objs = cluster.datastore
        elif datastore_cluster:
            datastore_cluster_obj = get_all_objs(self.content, [vim.StoragePod])
            if not datastore_cluster_obj:
                self.module.fail_json(msg='Failed to find datastore cluster "%(datastore_cluster)s".' % self.params)
            for datastore in datastore_cluster_obj.childEntity:
                self.datastore_objs.append(datastore)
        else:
            self.module.fail_json(msg="Please select one of 'cluster_name', 'datastore' or 'datastore_cluster'.")
        self.state = self.params.get('state')

    def ensure(self):
        datastore_results = dict()
        change_datastore_list = []
        for datastore in self.datastore_objs:
            changed = False
            if self.state == 'present' and datastore.summary.maintenanceMode != 'normal':
                datastore_results[datastore.name] = "Datastore '%s' is already in maintenance mode." % datastore.name
                break
            elif self.state == 'absent' and datastore.summary.maintenanceMode == 'normal':
                datastore_results[datastore.name] = "Datastore '%s' is not in maintenance mode." % datastore.name
                break

            try:
                if self.state == 'present':
                    storage_replacement_result = datastore.DatastoreEnterMaintenanceMode()
                    task = storage_replacement_result.task
                else:
                    task = datastore.DatastoreExitMaintenanceMode_Task()

                success, result = wait_for_task(task)

                if success:
                    changed = True
                    if self.state == 'present':
                        datastore_results[datastore.name] = "Datastore '%s' entered in maintenance mode." % datastore.name
                    else:
                        datastore_results[datastore.name] = "Datastore '%s' exited from maintenance mode." % datastore.name
            except vim.fault.InvalidState as invalid_state:
                if self.state == 'present':
                    msg = "Unable to enter datastore '%s' in" % datastore.name
                else:
                    msg = "Unable to exit datastore '%s' from" % datastore.name
                msg += " maintenance mode due to : %s" % to_native(invalid_state.msg)
                self.module.fail_json(msg=msg)
            except Exception as exc:
                if self.state == 'present':
                    msg = "Unable to enter datastore '%s' in" % datastore.name
                else:
                    msg = "Unable to exit datastore '%s' from" % datastore.name
                msg += " maintenance mode due to generic exception : %s" % to_native(exc)
                self.module.fail_json(msg=msg)
            change_datastore_list.append(changed)

        changed = False
        if any(change_datastore_list):
            changed = True
        self.module.exit_json(changed=changed, results=datastore_results)


def main():
    spec = vmware_argument_spec()
    spec.update(dict(
        datastore=dict(type='str', required=False),
        cluster_name=dict(type='str', required=False),
        datastore_cluster=dict(type='str', required=False),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    ))

    module = AnsibleModule(
        argument_spec=spec,
        required_one_of=[
            ['datastore', 'cluster_name', 'datastore_cluster'],
        ],
    )

    datastore_maintenance_mgr = VmwareDatastoreMaintenanceMgr(module=module)
    datastore_maintenance_mgr.ensure()


if __name__ == '__main__':
    main()
