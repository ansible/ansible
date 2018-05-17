#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Joseph Callen <jcallen () csc.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: vmware_dvswitch
short_description: Create or remove a distributed vSwitch
description:
    - Create or remove a distributed vSwitch
version_added: 2.0
author:
- Joseph Callen (@jcpowermac)
notes:
    - Tested on vSphere 6.5
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
    datacenter_name:
        description:
            - The name of the datacenter that will contain the dvSwitch
        required: True
    switch_name:
        description:
            - The name of the switch to create or remove
        required: True
    switch_version:
        description:
            - The version of the switch to create. Can be 6.5.0, 6.0.0, 5.5.0, 5.1.0, 5.0.0 with a vcenter running vSphere 6.5
            - Needed if you have a vcenter version > ESXi version to join DVS. If not specified version=version of vcenter
        required: False
        version_added: 2.5
    mtu:
        description:
            - The switch maximum transmission unit
        required: True
    uplink_quantity:
        description:
            - Quantity of uplink per ESXi host added to the switch
        required: True
    discovery_proto:
        description:
            - Link discovery protocol between Cisco and Link Layer discovery
        choices:
            - 'cdp'
            - 'lldp'
        required: True
    discovery_operation:
        description:
            - Select the discovery operation
        choices:
            - 'both'
            - 'none'
            - 'advertise'
            - 'listen'
    state:
        description:
            - Create or remove dvSwitch
        default: 'present'
        choices:
            - 'present'
            - 'absent'
        required: False
extends_documentation_fragment: vmware.documentation
'''
EXAMPLES = '''
- name: Create dvswitch
  local_action:
    module: vmware_dvswitch
    hostname: vcenter_ip_or_hostname
    username: vcenter_username
    password: vcenter_password
    datacenter_name: datacenter
    switch_name: dvSwitch
    switch_version: 6.0.0
    mtu: 9000
    uplink_quantity: 2
    discovery_proto: lldp
    discovery_operation: both
    state: present
'''

try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import (HAS_PYVMOMI,
                                         connect_to_api,
                                         find_datacenter_by_name,
                                         find_dvs_by_name,
                                         vmware_argument_spec,
                                         wait_for_task
                                         )


class VMwareDVSwitch(object):

    def __init__(self, module):
        self.module = module
        self.dvs = None
        self.switch_name = self.module.params['switch_name']
        self.switch_version = self.module.params['switch_version']
        self.datacenter_name = self.module.params['datacenter_name']
        self.mtu = self.module.params['mtu']
        self.uplink_quantity = self.module.params['uplink_quantity']
        self.discovery_proto = self.module.params['discovery_proto']
        self.discovery_operation = self.module.params['discovery_operation']
        self.state = self.module.params['state']
        self.content = connect_to_api(module)

    def process_state(self):
        try:
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
            dvs_states[self.state][self.check_dvs_configuration()]()
        except vmodl.RuntimeFault as runtime_fault:
            self.module.fail_json(msg=runtime_fault.msg)
        except vmodl.MethodFault as method_fault:
            self.module.fail_json(msg=method_fault.msg)
        except Exception as e:
            self.module.fail_json(msg=str(e))

    def create_dvswitch(self, network_folder):
        result = None
        changed = False

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
        spec.productInfo.vendor = "VMware"
        spec.productInfo.version = self.switch_version

        for count in range(1, self.uplink_quantity + 1):
            spec.configSpec.uplinkPortPolicy.uplinkPortName.append("uplink%d" % count)

        task = network_folder.CreateDVS_Task(spec)
        changed, result = wait_for_task(task)
        return changed, result

    def state_exit_unchanged(self):
        self.module.exit_json(changed=False)

    def state_destroy_dvs(self):
        task = self.dvs.Destroy_Task()
        changed, result = wait_for_task(task)
        self.module.exit_json(changed=changed, result=str(result))

    def state_update_dvs(self):
        self.module.exit_json(changed=False, msg="Currently not implemented.")

    def state_create_dvs(self):
        changed = True
        result = None

        if not self.module.check_mode:
            dc = find_datacenter_by_name(self.content, self.datacenter_name)
            changed, result = self.create_dvswitch(dc.networkFolder)

        self.module.exit_json(changed=changed, result=str(result))

    def check_dvs_configuration(self):
        self.dvs = find_dvs_by_name(self.content, self.switch_name)
        if self.dvs is None:
            return 'absent'
        else:
            return 'present'


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(datacenter_name=dict(required=True, type='str'),
                              switch_name=dict(required=True, type='str'),
                              mtu=dict(required=True, type='int'),
                              switch_version=dict(type='str'),
                              uplink_quantity=dict(required=True, type='int'),
                              discovery_proto=dict(required=True, choices=['cdp', 'lldp'], type='str'),
                              discovery_operation=dict(required=True, choices=['both', 'none', 'advertise', 'listen'], type='str'),
                              state=dict(default='present', choices=['present', 'absent'], type='str')))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    if not HAS_PYVMOMI:
        module.fail_json(msg='pyvmomi is required for this module')

    vmware_dvswitch = VMwareDVSwitch(module)
    vmware_dvswitch.process_state()


if __name__ == '__main__':
    main()
