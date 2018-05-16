#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Joseph Callen <jcallen () csc.com>
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
module: vmware_vm_facts
short_description: Return basic facts pertaining to a vSphere virtual machine guest
description:
- Return basic facts pertaining to a vSphere virtual machine guest.
version_added: '2.0'
author:
- Joseph Callen (@jcpowermac)
- Abhijeet Kasurde (@Akasurde)
notes:
- Tested on vSphere 5.5 and vSphere 6.5
requirements:
- python >= 2.6
- PyVmomi
options:
    vm_type:
      description:
      - If set to C(vm), then facts are gathered for virtual machines only.
      - If set to C(template), then facts are gathered for virtual machine templates only.
      - If set to C(all), then facts are gathered for all virtual machines and virtual machine templates.
      required: False
      default: 'all'
      choices: [ all, vm, template ]
      version_added: 2.5
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Gather all registered virtual machines
  vmware_vm_facts:
    hostname: esxi_or_vcenter_ip_or_hostname
    username: username
    password: password
  delegate_to: localhost
  register: vmfacts

- debug:
    var: vmfacts.virtual_machines

- name: Gather only registered virtual machine templates
  vmware_vm_facts:
    hostname: esxi_or_vcenter_ip_or_hostname
    username: username
    password: password
    vm_type: template
  delegate_to: localhost
  register: template_facts

- debug:
    var: template_facts.virtual_machines

- name: Gather only registered virtual machines
  vmware_vm_facts:
    hostname: esxi_or_vcenter_ip_or_hostname
    username: username
    password: password
    vm_type: vm
  delegate_to: localhost
  register: vm_facts

- debug:
    var: vm_facts.virtual_machines
'''

RETURN = r'''
virtual_machines:
  description: dictionary of virtual machines and their facts
  returned: success
  type: dict
'''

try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import PyVmomi, get_all_objs, vmware_argument_spec, _get_vm_prop


class VmwareVmFacts(PyVmomi):
    def __init__(self, module):
        super(VmwareVmFacts, self).__init__(module)

    # https://github.com/vmware/pyvmomi-community-samples/blob/master/samples/getallvms.py
    def get_all_virtual_machines(self):
        """
        Function to get all virtual machines and related configurations information
        """
        virtual_machines = get_all_objs(self.content, [vim.VirtualMachine])
        _virtual_machines = {}

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
            if summary.runtime.host:
                esxi_hostname = summary.runtime.host.summary.config.name

            virtual_machine = {
                summary.config.name: {
                    "guest_fullname": summary.config.guestFullName,
                    "power_state": summary.runtime.powerState,
                    "ip_address": _ip_address,  # Kept for backward compatibility
                    "mac_address": _mac_address,  # Kept for backward compatibility
                    "uuid": summary.config.uuid,
                    "vm_network": net_dict,
                    "esxi_hostname": esxi_hostname,
                }
            }

            vm_type = self.module.params.get('vm_type')
            if vm_type == 'vm' and vm.config.template is False:
                _virtual_machines.update(virtual_machine)
            elif vm_type == 'template' and vm.config.template:
                _virtual_machines.update(virtual_machine)
            elif vm_type == 'all':
                _virtual_machines.update(virtual_machine)
        return _virtual_machines


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        vm_type=dict(type='str', choices=['vm', 'all', 'template'], default='all'),
    )
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=False)

    vmware_vm_facts = VmwareVmFacts(module)
    _virtual_machines = vmware_vm_facts.get_all_virtual_machines()

    module.exit_json(changed=False, virtual_machines=_virtual_machines)


if __name__ == '__main__':
    main()
