#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
# Copyright: (c) 2018, Ansible Project
#
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
module: vmware_object_rename
short_description: Rename a vmware object
description:
    - This module can be used to rename a vmware object.
version_added: 2.6
author:
    - Abhijeet Kasurde (@akasurde) <akasurde@redhat.com>
notes:
    - Tested on vSphere 6.5
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
   name:
     description:
     - Name of the object to rename.
     required: True
   new_name:
     description:
     - New name of the object.
     required: True
   object_type:
     description:
     - Type of object to rename.
     required: False
     default: 'VirtualMachine'
     choices: ['VirtualMachine', 'Datacenter', 'ClusterComputeResource',
               'DistributedVirtualSwitch', 'HostSystem', 'Datastore',
               'Network', 'DistributedVirtualPortgroup']
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: Rename Datacenter
  vmware_object_rename:
    hostname: 192.168.1.209
    username: administrator@vsphere.local
    password: vmware
    validate_certs: False
    name: datacenter1
    new_name: datacenter2
    object_type: 'Datacenter'
  delegate_to: localhost

- name: Rename Cluster
  vmware_object_rename:
    hostname: 192.168.1.209
    username: administrator@vsphere.local
    password: vmware
    validate_certs: False
    name: cluster1
    new_name: nw_cluster2
    object_type: 'ClusterComputeResource'
  delegate_to: localhost
'''

RETURN = """ # """

try:
    import pyVmomi
    from pyVmomi import vim
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec, wait_for_task


class VmObjectMgr(PyVmomi):
    def __init__(self, module, object_type):
        super(VmObjectMgr, self).__init__(module)

        old_name = module.params['name']
        new_name = module.params['new_name']

        managed_objects = self.get_managed_objects_properties(vim_type=object_type, properties=['name'])

        objects_list = []
        already_exists = False

        for m_obj in managed_objects:
            if m_obj.obj.name == old_name:
                objects_list.append(m_obj.obj)
            if m_obj.obj.name == new_name:
                already_exists = True

        if len(objects_list) > 1:
            self.module.fail_json(msg="Multiple objects found with the same name %s."
                                      " Please make sure you have unique name to use this feature." % old_name)

        if already_exists:
            self.module.fail_json(msg="Unable to rename object %s as object with"
                                      " same name %s already exists." % (old_name, new_name))

        if module.check_mode:
            self.module.exit_json(changed=True)

        if objects_list:
            desired_obj = objects_list[0]

            task = desired_obj.Rename_Task(new_name)

            wait_for_task(task)

            if task.info.state == 'error':
                self.module.fail_json(msg=to_native(task.info.error.msg))

            self.module.exit_json(changed=True)
        else:
            self.module.exit_json(changed=False)


def main():
    object_types = {
        'Datacenter': vim.Datacenter,
        'VirtualMachine': vim.VirtualMachine,
        'ClusterComputeResource': vim.ClusterComputeResource,
        'DistributedVirtualSwitch': vim.DistributedVirtualSwitch,
        'HostSystem': vim.HostSystem,
        'Datastore': vim.Datastore,
        'Network': vim.Network,
        'DistributedVirtualPortgroup': vim.dvs.DistributedVirtualPortgroup,
    }

    argument_spec = vmware_argument_spec()
    argument_spec.update(
        name=dict(required=True),
        new_name=dict(required=True),
        object_type=dict(choices=list(object_types.keys()), default='VirtualMachine')
    )
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    object_type = object_types[module.params['object_type']]

    pyv = VmObjectMgr(module, object_type=object_type)


if __name__ == '__main__':
    main()
