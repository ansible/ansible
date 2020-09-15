#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Joseph Callen <jcallen () csc.com>
# Copyright: (c) 2018, Ansible Project
# Copyright: (c) 2018, Fedor Vompe <f.vompe () comptek.ru>
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
module: vmware_vm_info
short_description: Return basic info pertaining to a VMware machine guest
description:
- Return basic information pertaining to a vSphere or ESXi virtual machine guest.
- Cluster name as fact is added in version 2.7.
- This module was called C(vmware_vm_facts) before Ansible 2.9. The usage did not change.
version_added: '2.0'
author:
- Joseph Callen (@jcpowermac)
- Abhijeet Kasurde (@Akasurde)
- Fedor Vompe (@sumkincpp)
notes:
- Tested on ESXi 6.7, vSphere 5.5 and vSphere 6.5
- From 2.8 and onwards, information are returned as list of dict instead of dict.
requirements:
- python >= 2.6
- PyVmomi
options:
    vm_type:
      description:
      - If set to C(vm), then information are gathered for virtual machines only.
      - If set to C(template), then information are gathered for virtual machine templates only.
      - If set to C(all), then information are gathered for all virtual machines and virtual machine templates.
      required: False
      default: 'all'
      choices: [ all, vm, template ]
      version_added: 2.5
      type: str
    show_attribute:
      description:
      - Attributes related to VM guest shown in information only when this is set C(true).
      default: no
      type: bool
      version_added: 2.8
    folder:
      description:
        - Specify a folder location of VMs to gather information from.
        - 'Examples:'
        - '   folder: /ha-datacenter/vm'
        - '   folder: ha-datacenter/vm'
        - '   folder: /datacenter1/vm'
        - '   folder: datacenter1/vm'
        - '   folder: /datacenter1/vm/folder1'
        - '   folder: datacenter1/vm/folder1'
        - '   folder: /folder1/datacenter1/vm'
        - '   folder: folder1/datacenter1/vm'
        - '   folder: /folder1/datacenter1/vm/folder2'
      type: str
      version_added: 2.9
    show_tag:
      description:
        - Tags related to virtual machine are shown if set to C(True).
      default: False
      type: bool
      version_added: 2.9
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Gather all registered virtual machines
  vmware_vm_info:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
  delegate_to: localhost
  register: vminfo

- debug:
    var: vminfo.virtual_machines

- name: Gather only registered virtual machine templates
  vmware_vm_info:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    vm_type: template
  delegate_to: localhost
  register: template_info

- debug:
    var: template_info.virtual_machines

- name: Gather only registered virtual machines
  vmware_vm_info:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    vm_type: vm
  delegate_to: localhost
  register: vm_info

- debug:
    var: vm_info.virtual_machines

- name: Get UUID from given VM Name
  block:
    - name: Get virtual machine info
      vmware_vm_info:
        hostname: '{{ vcenter_hostname }}'
        username: '{{ vcenter_username }}'
        password: '{{ vcenter_password }}'
        folder: "/datacenter/vm/folder"
      delegate_to: localhost
      register: vm_info

    - debug:
        msg: "{{ item.uuid }}"
      with_items:
        - "{{ vm_info.virtual_machines | json_query(query) }}"
      vars:
        query: "[?guest_name=='DC0_H0_VM0']"

- name: Get Tags from given VM Name
  block:
    - name: Get virtual machine info
      vmware_vm_info:
        hostname: '{{ vcenter_hostname }}'
        username: '{{ vcenter_username }}'
        password: '{{ vcenter_password }}'
        folder: "/datacenter/vm/folder"
      delegate_to: localhost
      register: vm_info

    - debug:
        msg: "{{ item.tags }}"
      with_items:
        - "{{ vm_info.virtual_machines | json_query(query) }}"
      vars:
        query: "[?guest_name=='DC0_H0_VM0']"
'''

RETURN = r'''
virtual_machines:
  description: list of dictionary of virtual machines and their information
  returned: success
  type: list
  sample: [
    {
        "guest_name": "ubuntu_t",
        "cluster": null,
        "esxi_hostname": "10.76.33.226",
        "guest_fullname": "Ubuntu Linux (64-bit)",
        "ip_address": "",
        "mac_address": [
            "00:50:56:87:a5:9a"
        ],
        "power_state": "poweredOff",
        "uuid": "4207072c-edd8-3bd5-64dc-903fd3a0db04",
        "vm_network": {
            "00:50:56:87:a5:9a": {
              "ipv4": [
                "10.76.33.228"
              ],
              "ipv6": []
            }
        },
        "attributes": {
            "job": "backup-prepare"
        },
        "tags": [
            {
                "category_id": "urn:vmomi:InventoryServiceCategory:b316cc45-f1a9-4277-811d-56c7e7975203:GLOBAL",
                "category_name": "cat_0001",
                "description": "",
                "id": "urn:vmomi:InventoryServiceTag:43737ec0-b832-4abf-abb1-fd2448ce3b26:GLOBAL",
                "name": "tag_0001"
            }
        ]
    }
  ]
'''

try:
    from pyVmomi import vim
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import PyVmomi, get_all_objs, vmware_argument_spec, _get_vm_prop
from ansible.module_utils.vmware_rest_client import VmwareRestClient


class VmwareVmInfo(PyVmomi):
    def __init__(self, module):
        super(VmwareVmInfo, self).__init__(module)

    def get_tag_info(self, vm_dynamic_obj):
        vmware_client = VmwareRestClient(self.module)
        return vmware_client.get_tags_for_vm(vm_mid=vm_dynamic_obj._moId)

    def get_vm_attributes(self, vm):
        return dict((x.name, v.value) for x in self.custom_field_mgr
                    for v in vm.customValue if x.key == v.key)

    # https://github.com/vmware/pyvmomi-community-samples/blob/master/samples/getallvms.py
    def get_all_virtual_machines(self):
        """
        Get all virtual machines and related configurations information
        """
        folder = self.params.get('folder')
        folder_obj = None
        if folder:
            folder_obj = self.content.searchIndex.FindByInventoryPath(folder)
            if not folder_obj:
                self.module.fail_json(msg="Failed to find folder specified by %(folder)s" % self.params)

        virtual_machines = get_all_objs(self.content, [vim.VirtualMachine], folder=folder_obj)
        _virtual_machines = []

        for vm in virtual_machines:
            _ip_address = ""
            summary = vm.summary
            if summary.guest is not None:
                _ip_address = summary.guest.ipAddress
                if _ip_address is None:
                    _ip_address = ""
            _mac_address = []
            all_devices = _get_vm_prop(vm, ('config', 'hardware', 'device'))
            if all_devices:
                for dev in all_devices:
                    if isinstance(dev, vim.vm.device.VirtualEthernetCard):
                        _mac_address.append(dev.macAddress)

            net_dict = {}
            vmnet = _get_vm_prop(vm, ('guest', 'net'))
            if vmnet:
                for device in vmnet:
                    net_dict[device.macAddress] = dict()
                    net_dict[device.macAddress]['ipv4'] = []
                    net_dict[device.macAddress]['ipv6'] = []
                    for ip_addr in device.ipAddress:
                        if "::" in ip_addr:
                            net_dict[device.macAddress]['ipv6'].append(ip_addr)
                        else:
                            net_dict[device.macAddress]['ipv4'].append(ip_addr)

            esxi_hostname = None
            esxi_parent = None
            if summary.runtime.host:
                esxi_hostname = summary.runtime.host.summary.config.name
                esxi_parent = summary.runtime.host.parent

            cluster_name = None
            if esxi_parent and isinstance(esxi_parent, vim.ClusterComputeResource):
                cluster_name = summary.runtime.host.parent.name

            vm_attributes = dict()
            if self.module.params.get('show_attribute'):
                vm_attributes = self.get_vm_attributes(vm)

            vm_tags = list()
            if self.module.params.get('show_tag'):
                vm_tags = self.get_tag_info(vm)

            virtual_machine = {
                "guest_name": summary.config.name,
                "guest_fullname": summary.config.guestFullName,
                "power_state": summary.runtime.powerState,
                "ip_address": _ip_address,  # Kept for backward compatibility
                "mac_address": _mac_address,  # Kept for backward compatibility
                "uuid": summary.config.uuid,
                "vm_network": net_dict,
                "esxi_hostname": esxi_hostname,
                "cluster": cluster_name,
                "attributes": vm_attributes,
                "tags": vm_tags
            }

            vm_type = self.module.params.get('vm_type')
            is_template = _get_vm_prop(vm, ('config', 'template'))
            if vm_type == 'vm' and not is_template:
                _virtual_machines.append(virtual_machine)
            elif vm_type == 'template' and is_template:
                _virtual_machines.append(virtual_machine)
            elif vm_type == 'all':
                _virtual_machines.append(virtual_machine)
        return _virtual_machines


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        vm_type=dict(type='str', choices=['vm', 'all', 'template'], default='all'),
        show_attribute=dict(type='bool', default='no'),
        show_tag=dict(type='bool', default=False),
        folder=dict(type='str'),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )
    if module._name == 'vmware_vm_facts':
        module.deprecate("The 'vmware_vm_facts' module has been renamed to 'vmware_vm_info'", version='2.13')

    vmware_vm_info = VmwareVmInfo(module)
    _virtual_machines = vmware_vm_info.get_all_virtual_machines()

    module.exit_json(changed=False, virtual_machines=_virtual_machines)


if __name__ == '__main__':
    main()
