#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 Tim Rightnour <thegarbledone@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: vmware_register
short_description: Register or un-register a VM with VMware
version_added: 2.5
description:
  - Registers a VM or template file with VMware as a new VM/template respectively
  - Can also be used to un-register a VM/template (identical to remove from inventory)
author: Tim Rightnour
requirements:
  - python >= 2.6
  - PyVmomi
notes:
  - When registering a VM, either C(esxi_hostname), C(resource_pool) or
  - C(resource_pool_cluster_root) and C(cluster) are required
  - Tested on vSphere 5.5 and 6.0
options:
  state:
    description: Desired state of VM/template
    required: True
    choices: ['present', 'absent']
  name:
    description: Name to register the VM/template with
    required: True
  is_template:
    description: Register this file as a template
    default: False
    type: bool
  path:
    description: The path to the file on the datastore to register
    required: True
  folder:
    description: The folder in VMware to register the VM/template under
    required: True
  datacenter:
    description: The datacenter to register the VM/template in
    required: True
  datastore:
    description: The datastore the file to register is located in
    required: True
  esxi_hostname:
    description: The esxi host to register the VM/template against
  cluster:
    description:
      - The cluster to locate a resource_pool from
      - Required when C(resource_pool_cluster_root) is True
  resource_pool_cluster_root:
    description: Force the VM/template into the root resource pool of the cluster
    type: bool
  resource_pool:
    description: The resource pool to register the VM/template in

extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Register a template
  vsphere_register:
    state: present
    name: My_Template
    is_template: True
    path: templates/template.vmxt
    folder: My_Templates/Template
    datacenter: dc_1
    datastore: ds_1
    hostname: vsphere.host.com
    username: administrator@vsphere.local
    password: vmware
    validate_certs: false
  delegate_to: localhost

- name: Delete VM from inventory
  vsphere_register:
    state: absent
    name: vm_guest_name
    path: vm/vm_guest_name/vm_guest_name.vmdk
    folder: Databases/Production
    datacenter: dc_1
    datastore: prod_ds
    hostname: vsphere.host.com
    username: administrator@vsphere.local
    password: vmware
    validate_certs: false
  delegate_to: localhost

- name: Register a VM to a specific esxi host
  vsphere_register:
    state: present
    name: new_db_host
    is_template: True
    path: vm/new_db_host/new_db_host.vmdk
    folder: Databases/Production
    datacenter: dc_1
    datastore: ds_1
    esxi_hostname: prod_db_esxi.my.com
    hostname: vsphere.host.com
    username: administrator@vsphere.local
    password: vmware
    validate_certs: false
  delegate_to: localhost
'''

RETURN = r'''
instance:
    description: metadata about the new virtualmachine
    returned: always
    type: dict
    sample: None
'''

try:
    import pyVmomi
    from pyVmomi import vim
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.vmware import (connect_to_api, gather_vm_facts, get_all_objs,
                                         compile_folder_path_for_object, serialize_spec,
                                         find_vm_by_name, vmware_argument_spec,
                                         wait_for_task, HAS_PYVMOMI, find_cluster_by_name,
                                         find_hostsystem_by_name, find_datacenter_by_name,
                                         find_datastore_by_name, find_obj)


class PyVmomiCache(object):
    """ This class caches references to objects which are requested multiples times but not modified """
    def __init__(self, content, dc_name=None):
        self.content = content
        self.dc_name = dc_name
        self.clusters = {}
        self.parent_datacenters = {}

    def find_obj(self, content, types, name, confine_to_datacenter=True):
        """ Wrapper around find_obj to set datacenter context """
        result = find_obj(content, types, name)
        if result and confine_to_datacenter:
            if self.get_parent_datacenter(result).name != self.dc_name:
                result = None
                objects = self.get_all_objs(content, types, confine_to_datacenter=True)
                for obj in objects:
                    if name is None or obj.name == name:
                        return obj
        return result

    def get_all_objs(self, content, types, confine_to_datacenter=True):
        """ Wrapper around get_all_objs to set datacenter context """
        objects = get_all_objs(content, types)
        if confine_to_datacenter:
            if hasattr(objects, 'items'):
                # resource pools come back as a dictionary
                for k, v in objects.items():
                    parent_dc = self.get_parent_datacenter(k)
                    if parent_dc.name != self.dc_name:
                        objects.pop(k, None)
            else:
                # everything else should be a list
                objects = [x for x in objects if self.get_parent_datacenter(x).name == self.dc_name]

        return objects

    def get_parent_datacenter(self, obj):
        """ Walk the parent tree to find the objects datacenter """
        if isinstance(obj, vim.Datacenter):
            return obj
        if obj in self.parent_datacenters:
            return self.parent_datacenters[obj]
        datacenter = None
        while True:
            if not hasattr(obj, 'parent'):
                break
            obj = obj.parent
            if isinstance(obj, vim.Datacenter):
                datacenter = obj
                break
        self.parent_datacenters[obj] = datacenter
        return datacenter


class PyVmomiHelper(object):
    def __init__(self, module):
        if not HAS_PYVMOMI:
            module.fail_json(msg='pyvmomi module required')

        self.module = module
        self.params = module.params
        self.content = connect_to_api(self.module)
        self.current_vm_obj = None
        self.cache = PyVmomiCache(self.content, dc_name=self.params['datacenter'])

    def getvm(self, name=None, folder=None):
        vm = None
        vm = find_vm_by_name(self.content, vm_name=name, folder=folder)
        if vm:
            self.current_vm_obj = vm

        return vm

    def select_host(self, datastore_name):
        # given a datastore, find an attached host (just pick the first one)
        datastore = find_datastore_by_name(self.content, datastore_name)
        for host_mount in datastore.host:
            return host_mount.key

    def fobj_from_folder_path(self, dc, folder):
        datacenter = find_datacenter_by_name(self.content, dc)
        if datacenter is None:
            self.module.fail_json(msg='No datacenter named %s was found' % dc)
        # Prepend / if it was missing from the folder path, also strip trailing slashes
        if not folder.startswith('/'):
            folder = '/%s' % folder
        folder = folder.rstrip('/')

        dcpath = compile_folder_path_for_object(datacenter)

        # Check for full path first in case it was already supplied
        if folder.startswith(dcpath + dc + '/vm') or folder.startswith(dcpath + '/' + dc + '/vm'):
            fullpath = folder
        elif (folder.startswith('/vm/') or folder == '/vm'):
            fullpath = "%s/%s%s" % (dcpath, dc, folder)
        elif (folder.startswith('/')):
            fullpath = "%s/%s/vm%s" % (dcpath, dc, folder)
        else:
            fullpath = "%s/%s/vm/%s" % (dcpath, dc, folder)

        f_obj = self.content.searchIndex.FindByInventoryPath(fullpath)

        return f_obj

    def obj_has_parent(self, obj, parent):
        assert obj is not None and parent is not None
        current_parent = obj

        while True:
            if current_parent.name == parent.name:
                return True

            try:
                current_parent = current_parent.parent
                if current_parent is None:
                    return False
            except:
                return False

    def select_resource_pool_by_name(self, resource_pool_name):
        resource_pool = self.cache.find_obj(self.content, [vim.ResourcePool], resource_pool_name)
        if resource_pool is None:
            self.module.fail_json(msg='Could not find resource_pool "%s"' % resource_pool_name)
        return resource_pool

    def select_resource_pool_by_host(self, host):
        resource_pools = self.cache.get_all_objs(self.content, [vim.ResourcePool])
        for rp in resource_pools.items():
            if not rp[0]:
                continue

            if not hasattr(rp[0], 'parent') or not rp[0].parent:
                continue

            # Find resource pool on host
            if self.obj_has_parent(rp[0].parent, host.parent):
                # If no resource_pool selected or it's the selected pool, return it
                if self.module.params['resource_pool'] is None or rp[0].name == self.module.params['resource_pool']:
                    return rp[0]

        if self.module.params['resource_pool'] is not None:
            self.module.fail_json(msg="Could not find resource_pool %s for selected host %s"
                                  % (self.module.params['resource_pool'], host.name))
        else:
            self.module.fail_json(msg="Failed to find a resource group for %s" % host.name)

    def get_resource_pool(self):
        resource_pool = None
        if self.params['esxi_hostname']:
            host = self.select_host(self.params['datastore'])
            resource_pool = self.select_resource_pool_by_host(host)
        elif self.params['resource_pool_cluster_root']:
            if self.params['cluster'] is None:
                self.module.fail_json(msg='resource_pool_cluster_root requires a cluster name')
            else:
                rp_cluster = find_cluster_by_name(self.content, self.params['cluster'])
                if not rp_cluster:
                    self.module.fail_json(msg="Failed to find a cluster named %(cluster)s" % self.params)
                resource_pool = rp_cluster.resourcePool
        else:
            resource_pool = self.select_resource_pool_by_name(self.params['resource_pool'])

        if resource_pool is None:
            self.module.fail_json(msg='Unable to find resource pool, need esxi_hostname, resource_pool, or cluster and resource_pool_cluster_root')

        return resource_pool

    def register_vm(self, template=False):

        result = dict(
            changed=False,
            failed=False,
        )

        f_obj = self.fobj_from_folder_path(dc=self.params['datacenter'], folder=self.params['folder'])
        # abort if no strategy was successful
        if f_obj is None:
            self.module.fail_json(msg='No folder matched the path: %(folder)s' % self.params)
        destfolder = f_obj

        if self.params['esxi_hostname'] is None:
            esxhost = self.select_host(self.params['datastore'])
        else:
            esxhost = find_hostsystem_by_name(self.content, self.params['esxi_hostname'])

        if template:
            task = destfolder.RegisterVM_Task("[%s] %s" % (self.params['datastore'], self.params['path']), self.params['name'], asTemplate=True, host=esxhost)
        else:
            # Now we need a resource pool
            resource_pool = self.get_resource_pool()
            # Now finally register the VM
            task = destfolder.RegisterVM_Task("[%s] %s" % (self.params['datastore'], self.params['path']),
                                              self.params['name'], asTemplate=False, host=esxhost, pool=resource_pool)

        if task:
            try:
                wait_for_task(task)
            except:
                pass
            if task.info.state == 'error':
                result['failed'] = True
                result['msg'] = str(task.info.error.msg)
            else:
                result['changed'] = True

        return result


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        state=dict(type='str', default='present', choices=['present', 'absent']),
        name=dict(type='str', required=True),
        is_template=dict(type='bool', default=False),
        path=dict(type='str', required=True),
        folder=dict(type='str', required=True),
        datacenter=dict(type='str', required=True),
        datastore=dict(type='str', required=True),
        esxi_hostname=dict(type='str'),
        cluster=dict(type='str'),
        resource_pool=dict(type='str'),
        resource_pool_cluster_root=dict(type='bool'),
    )

    # No check mode support, because I don't know how to tell if an image file is registered or not
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=False,
                           mutually_exclusive=[
                               ['cluster', 'esxi_hostname'],
                           ],
                           required_together=[
                               ['cluster', 'resource_pool_cluster_root']
                           ],
                           )

    result = {'failed': False, 'changed': False}

    # FindByInventoryPath() does not require an absolute path
    # so we should leave the input folder path unmodified
    module.params['folder'] = module.params['folder'].rstrip('/')

    pyv = PyVmomiHelper(module)

    # Check if the VM exists before continuing

    f_obj = pyv.fobj_from_folder_path(dc=module.params['datacenter'], folder=module.params['folder'])
    if f_obj is None:
        module.fail_json(msg='No folder matched the path: %(folder)s' % module.params)

    vm = pyv.getvm(name=module.params['name'], folder=f_obj)
    # The object exists
    if vm:
        if module.params['state'] == 'absent':
            # Unregister the vm
            try:
                vm.UnregisterVM()
            except vim.fault.TaskInProgress:
                module.fail_json(msg="vm is busy, cannot unregister")
            except vim.fault.InvalidPowerState:
                module.fail_json(msg="Cannot unregister a VM which is powered on")
            except Exception as e:
                module.fail_json(msg=to_native(e))
            result['changed'] = True
            module.exit_json(**result)
        else:
            module.exit_json(**result)
    else:
        result = pyv.register_vm(template=module.params['is_template'])

    if result['failed']:
        module.fail_json(**result)
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()
