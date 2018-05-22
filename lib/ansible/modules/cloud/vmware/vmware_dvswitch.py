#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2015, Joseph Callen <jcallen () csc.com>
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
module: vmware_dvswitch
short_description: Create or remove a distributed vSwitch
description:
    - This module can be used to create, remove a distributed vSwitch.
version_added: 2.0
author:
- Joseph Callen (@jcpowermac)
- Abhijeet Kasurde (@Akasurde)
notes:
    - Tested on vSphere 6.5
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
    datacenter_name:
      description:
      - The name of the datacenter that will contain the distributed vSwitch.
      required: True
    switch_name:
      description:
      - The name of the distribute vSwitch to create or remove.
      required: True
    switch_version:
      description:
      - The version of the distributed vSwitch to create.
      - Can be 6.5.0, 6.0.0, 5.5.0, 5.1.0, 5.0.0 with a vCenter running vSphere 6.5.
      - Needed if you have a vCenter version greater than ESXi version to join DVS. If not specified version=version of vCenter.
      - Required only if C(state) is set to C(present).
      version_added: 2.5
      choices: ['5.0.0', '5.1.0', '5.5.0', '6.0.0', '6.5.0']
    mtu:
      description:
      - The switch maximum transmission unit.
      - Required parameter for C(state) both C(present) and C(absent), before Ansible 2.6 version.
      - Required only if C(state) is set to C(present), for Ansible 2.6 and onwards.
      - Accepts value between 1280 to 9000 (both inclusive).
    uplink_quantity:
      description:
      - Quantity of uplink per ESXi host added to the distributed vSwitch.
      - Required parameter for C(state) both C(present) and C(absent), before Ansible 2.6 version.
      - Required only if C(state) is set to C(present), for Ansible 2.6 and onwards.
    discovery_proto:
      description:
      - Link discovery protocol between Cisco and Link Layer discovery.
      - Required parameter for C(state) both C(present) and C(absent), before Ansible 2.6 version.
      - Required only if C(state) is set to C(present), for Ansible 2.6 and onwards.
      choices: ['cdp', 'lldp']
    discovery_operation:
      description:
      - Select the discovery operation.
      - Required parameter for C(state) both C(present) and C(absent), before Ansible 2.6 version.
      - Required only if C(state) is set to C(present), for Ansible 2.6 and onwards.
      choices: ['both', 'none', 'advertise', 'listen']
    state:
      description:
      - If set to C(present) and distributed vSwitch does not exists then distributed vSwitch is created.
      - If set to C(absent) and distributed vSwitch exists then distributed vSwitch is deleted.
      - Update distributed vSwitch is not supported.
      default: 'present'
      choices: ['present', 'absent']
    vendor:
      description:
      - Name of the vendor.
      default: 'VMware, Inc.'
      version_added: 2.8
extends_documentation_fragment: vmware.documentation
'''
EXAMPLES = '''
- name: Create dvswitch
  vmware_dvswitch:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter_name: '{{ datacenter }}'
    switch_name: dvSwitch
    switch_version: 6.0.0
    mtu: 9000
    uplink_quantity: 2
    discovery_proto: lldp
    discovery_operation: both
    state: present
  delegate_to: localhost

- name: Delete dvswitch
  vmware_dvswitch:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter_name: '{{ datacenter }}'
    validate_certs: False
    switch_name: dvSwitch
    state: absent
  delegate_to: localhost
'''

RETURN = r""" #
"""

try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.vmware import (PyVmomi, find_datacenter_by_name, TaskError,
                                         find_dvs_by_name, vmware_argument_spec, wait_for_task)


class VMwareDVSwitch(PyVmomi):

    def __init__(self, module):
        super(VMwareDVSwitch, self).__init__(module)
        self.dvs = None
        self.switch_name = self.module.params['switch_name']
        self.switch_version = self.module.params['switch_version']
        self.datacenter_name = self.module.params['datacenter_name']
        self.mtu = self.module.params['mtu']
        self.uplink_quantity = self.module.params['uplink_quantity']
        self.discovery_proto = self.module.params['discovery_proto']
        self.discovery_operation = self.module.params['discovery_operation']
        self.state = self.module.params['state']

    def process_state(self):
        dvs_states = {
            'absent': {
                'present': self.state_destroy_dvs,
                'absent': self.state_exit_unchanged,
            },
            'present': {
                'update': self.state_update_dvs,
                'present': self.state_exit_unchanged,
                'absent': self.state_create_dvs,
            }
        }

        try:
            dvs_states[self.state][self.check_dvs_configuration()]()
        except vmodl.RuntimeFault as runtime_fault:
            self.module.fail_json(msg=to_native(runtime_fault.msg))
        except vmodl.MethodFault as method_fault:
            self.module.fail_json(msg=to_native(method_fault.msg))
        except Exception as e:
            self.module.fail_json(msg=to_native(e))

    def create_dvswitch(self, network_folder):
        result = None
        changed = False

        # Sanity
        if not (1280 <= self.mtu <= 9000):
            self.module.fail_json(msg="MTU value should be between 1280 and 9000"
                                      " (both inclusive), provided %d." % self.mtu)

        spec = vim.DistributedVirtualSwitch.CreateSpec()
        spec.configSpec = vim.dvs.VmwareDistributedVirtualSwitch.ConfigSpec()
        spec.configSpec.uplinkPortPolicy = vim.DistributedVirtualSwitch.NameArrayUplinkPortPolicy()
        spec.configSpec.linkDiscoveryProtocolConfig = vim.host.LinkDiscoveryProtocolConfig()

        spec.configSpec.name = self.switch_name
        spec.configSpec.maxMtu = self.mtu
        spec.configSpec.linkDiscoveryProtocolConfig.protocol = self.discovery_proto
        spec.configSpec.linkDiscoveryProtocolConfig.operation = self.discovery_operation
        spec.productInfo = vim.dvs.ProductSpec()
        spec.productInfo.name = "DVS"
        spec.productInfo.vendor = self.module.params.get('vendor')
        spec.productInfo.version = self.switch_version

        for count in range(1, self.uplink_quantity + 1):
            spec.configSpec.uplinkPortPolicy.uplinkPortName.append("uplink%d" % count)

        task = network_folder.CreateDVS_Task(spec)
        try:
            changed, result = wait_for_task(task)
        except TaskError as invalid_argument:
            self.module.fail_json(msg="Failed to create distributed virtual"
                                      " switch due to : %s" % to_native(invalid_argument))
        return changed, result

    def state_exit_unchanged(self):
        self.module.exit_json(changed=False)

    def state_destroy_dvs(self):
        task = self.dvs.Destroy_Task()
        changed, result = wait_for_task(task)
        self.module.exit_json(changed=changed, result=to_native(result))

    def state_update_dvs(self):
        self.module.exit_json(changed=False, msg="Currently not implemented.")

    def state_create_dvs(self):
        changed = True
        result = None

        if not self.module.check_mode:
            dc = find_datacenter_by_name(self.content, self.datacenter_name)
            if dc is None:
                self.module.fail_json(msg="Failed to find datacenter %s" % self.datacenter_name)
            changed, result = self.create_dvswitch(dc.networkFolder)

        self.module.exit_json(changed=changed, result=to_native(result))

    def check_dvs_configuration(self):
        self.dvs = find_dvs_by_name(self.content, self.switch_name)
        if self.dvs is None:
            return 'absent'
        else:
            return 'present'


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        dict(
            datacenter_name=dict(required=True),
            switch_name=dict(required=True),
            mtu=dict(type='int'),
            switch_version=dict(choices=['5.0.0', '5.1.0', '5.5.0', '6.0.0', '6.5.0']),
            uplink_quantity=dict(type='int'),
            discovery_proto=dict(choices=['cdp', 'lldp']),
            discovery_operation=dict(choices=['both', 'none', 'advertise', 'listen']),
            state=dict(default='present', choices=['present', 'absent']),
            vendor=dict(default='VMware, Inc.'),
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=[
            ('state', 'present',
             ['mtu', 'uplink_quantity', 'discovery_proto', 'discovery_operation']),
        ],
        supports_check_mode=True,
    )

    vmware_dvswitch = VMwareDVSwitch(module)
    vmware_dvswitch.process_state()


if __name__ == '__main__':
    main()
