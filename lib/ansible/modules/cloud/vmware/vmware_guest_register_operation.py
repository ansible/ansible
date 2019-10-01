#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, sky-joker
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
module: vmware_guest_register_operation
short_description: VM inventory registration operation
author:
  - sky-joker (@sky-joker)
version_added: '2.10'
description:
  - This module can register or unregister VMs to the inventory.
requirements:
  - python >= 2.7
  - PyVmomi
options:
  datacenter:
    description:
    - Destination datacenter for the register/unregister operation.
    - This parameter is case sensitive.
    type: str
  cluster:
    description:
    - Specify a cluster name to register VM.
    type: str
  folder:
    description:
    - Description folder, absolute path of the target folder.
    - The folder should include the datacenter. ESX's datacenter is ha-datacenter.
    - This parameter is case sensitive.
    - 'Examples:'
    - '   folder: /ha-datacenter/vm'
    - '   folder: ha-datacenter/vm'
    - '   folder: /datacenter1/vm'
    - '   folder: datacenter1/vm'
    - '   folder: /datacenter1/vm/folder1'
    - '   folder: datacenter1/vm/folder1'
    type: str
  name:
    description:
    - Specify VM name to be registered in the inventory.
    required: True
    type: str
  uuid:
    description:
    - UUID of the virtual machine to manage if known, this is VMware's unique identifier.
    - If virtual machine does not exists, then this parameter is ignored.
    type: str
  esxi_hostname:
    description:
    - The ESXi hostname where the virtual machine will run.
    - This parameter is case sensitive.
    type: str
  template:
    description:
    - Whether to register VM as a template.
    default: False
    type: bool
  path:
    description:
    - Specify the path of vmx file.
    - 'Examples:'
    - '    [datastore1] vm/vm.vmx'
    - '    [datastore1] vm/vm.vmtx'
    type: str
  resource_pool:
    description:
    - Specify a resource pool name to register VM.
    - This parameter is case sensitive.
    - Resource pool should be child of the selected host parent.
    type: str
  state:
    description:
    - Specify the state the virtual machine should be in.
    - if set to C(present), register VM in inventory.
    - if set to C(absent), unregister VM from inventory.
    default: present
    choices: [ present, absent ]
    type: str
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: Register VM to inventory
  vmware_guest_register_operation:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    validate_certs: no
    datacenter: "{{ datacenter }}"
    folder: "/vm"
    esxi_hostname: "{{ esxi_hostname }}"
    name: "{{ vm_name }}"
    template: no
    path: "[datastore1] vm/vm.vmx"
    state: present

- name: Register VM in resource pool
  vmware_guest_register_operation:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    validate_certs: no
    datacenter: "{{ datacenter }}"
    folder: "/vm"
    resource_pool: "{{ resource_pool }}"
    name: "{{ vm_name }}"
    template: no
    path: "[datastore1] vm/vm.vmx"
    state: present

- name: Register VM in Cluster
  vmware_guest_register_operation:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    validate_certs: no
    datacenter: "{{ datacenter }}"
    folder: "/vm"
    cluster: "{{ cluster_name }}"
    name: "{{ vm_name }}"
    template: no
    path: "[datastore1] vm/vm.vmx"
    state: present

- name: UnRegister VM from inventory
  vmware_guest_register_operation:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    validate_certs: no
    datacenter: "{{ datacenter }}"
    folder: "/vm"
    name: "{{ vm_name }}"
    state: absent
'''

RETURN = r'''
'''

try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False

from ansible.module_utils._text import to_native
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec, find_resource_pool_by_name, \
    wait_for_task, compile_folder_path_for_object, find_cluster_by_name
from ansible.module_utils.basic import AnsibleModule


class VMwareGuestRegisterOperation(PyVmomi):
    def __init__(self, module):
        super(VMwareGuestRegisterOperation, self).__init__(module)
        self.datacenter = module.params["datacenter"]
        self.cluster = module.params["cluster"]
        self.folder = module.params["folder"]
        self.name = module.params["name"]
        self.esxi_hostname = module.params["esxi_hostname"]
        self.path = module.params["path"]
        self.template = module.params["template"]
        self.resource_pool = module.params["resource_pool"]
        self.state = module.params["state"]

    def execute(self):
        result = dict(changed=False)

        datacenter = self.find_datacenter_by_name(self.datacenter)
        if not datacenter:
            self.module.fail_json(msg="Cannot find the specified Datacenter: %s" % self.datacenter)

        dcpath = compile_folder_path_for_object(datacenter)
        if not dcpath.endswith("/"):
            dcpath += "/"

        if(self.folder in [None, "", "/"]):
            self.module.fail_json(msg="Please specify folder path other than blank or '/'")
        elif(self.folder.startswith("/vm")):
            fullpath = "%s%s%s" % (dcpath, self.datacenter, self.folder)
        else:
            fullpath = "%s%s" % (dcpath, self.folder)

        folder_obj = self.content.searchIndex.FindByInventoryPath(inventoryPath="%s" % fullpath)
        if not folder_obj:
            details = {
                'datacenter': datacenter.name,
                'datacenter_path': dcpath,
                'folder': self.folder,
                'full_search_path': fullpath,
            }
            self.module.fail_json(msg="No folder %s matched in the search path : %s" % (self.folder, fullpath),
                                  details=details)

        if self.state == "present":
            if self.get_vm():
                self.module.exit_json(**result)

            if self.esxi_hostname:
                host_obj = self.find_hostsystem_by_name(self.esxi_hostname)
                if not host_obj:
                    self.module.fail_json(msg="Cannot find the specified ESXi host: %s" % self.esxi_hostname)
            else:
                host_obj = None

            if self.cluster:
                cluster_obj = find_cluster_by_name(self.content, self.cluster, datacenter)
                if not cluster_obj:
                    self.module.fail_json(msg="Cannot find the specified cluster name: %s" % self.cluster)

                resource_pool_obj = cluster_obj.resourcePool
            elif self.resource_pool:
                resource_pool_obj = find_resource_pool_by_name(self.content, self.resource_pool)
                if not resource_pool_obj:
                    self.module.fail_json(msg="Cannot find the specified resource pool: %s" % self.resource_pool)
            else:
                resource_pool_obj = host_obj.parent.resourcePool

            task = folder_obj.RegisterVM_Task(path=self.path, name=self.name, asTemplate=self.template,
                                              pool=resource_pool_obj, host=host_obj)

            changed = False
            try:
                changed, info = wait_for_task(task)
            except Exception as task_e:
                self.module.fail_json(msg=to_native(task_e))

            result.update(changed=changed)
            self.module.exit_json(**result)

        if self.state == "absent":
            vm_obj = self.get_vm()
            if vm_obj:
                try:
                    vm_obj.UnregisterVM()
                    result.update(changed=True)
                except Exception as exc:
                    self.module.fail_json(msg=to_native(exc))

            self.module.exit_json(**result)


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(datacenter=dict(type="str"),
                         cluster=dict(type="str"),
                         folder=dict(type="str"),
                         name=dict(type="str", required=True),
                         uuid=dict(type="str"),
                         esxi_hostname=dict(type="str"),
                         path=dict(type="str"),
                         template=dict(type="bool", default=False),
                         resource_pool=dict(type="str"),
                         state=dict(type="str", default="present", choices=["present", "absent"]))

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    vmware_guest_register_operation = VMwareGuestRegisterOperation(module)
    vmware_guest_register_operation.execute()


if __name__ == "__main__":
    main()
