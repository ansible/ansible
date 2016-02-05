#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Joseph Callen <jcallen () csc.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: vmware_dvswitch
short_description: Create or remove a distributed vSwitch
description:
    - Create or remove a distributed vSwitch
version_added: 2.0
author: "Joseph Callen (@jcpowermac)"
notes:
    - Tested on vSphere 5.5
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

class VMwareDVSwitch(object):
    def __init__(self, module):
        self.module = module
        self.dvs = None
        self.switch_name = self.module.params['switch_name']
        self.datacenter_name = self.module.params['datacenter_name']
        self.mtu = self.module.params['mtu']
        self.uplink_quantity = self.module.params['uplink_quantity']
        self.discovery_proto = self.module.params['discovery_proto']
        self.discovery_operation = self.module.params['discovery_operation']
        self.switch_name = self.module.params['switch_name']
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

        for count in range(1, self.uplink_quantity+1):
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
                              uplink_quantity=dict(required=True, type='int'),
                              discovery_proto=dict(required=True, choices=['cdp', 'lldp'], type='str'),
                              discovery_operation=dict(required=True, choices=['both', 'none', 'advertise', 'listen'], type='str'),
                              state=dict(default='present', choices=['present', 'absent'], type='str')))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    if not HAS_PYVMOMI:
        module.fail_json(msg='pyvmomi is required for this module')

    vmware_dvswitch = VMwareDVSwitch(module)
    vmware_dvswitch.process_state()

from ansible.module_utils.vmware import *
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
