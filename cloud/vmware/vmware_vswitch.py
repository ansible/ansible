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
module: vmware_vswitch
short_description: Add a VMware Standard Switch to an ESXi host
description:
    - Add a VMware Standard Switch to an ESXi host
version_added: 2.0
author: "Joseph Callen (@jcpowermac), Russell Teague (@mtnbikenc)"
notes:
    - Tested on vSphere 5.5
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
    switch_name:
        description:
            - vSwitch name to add
        required: True
    nic_name:
        description:
            - vmnic name to attach to vswitch
        required: True
    number_of_ports:
        description:
            - Number of port to configure on vswitch
        default: 128
        required: False
    mtu:
        description:
            - MTU to configure on vswitch
        required: False
    state:
        description:
            - Add or remove the switch
        default: 'present'
        choices:
            - 'present'
            - 'absent'
        required: False
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
Example from Ansible playbook

    - name: Add a VMware vSwitch
      local_action:
        module: vmware_vswitch
        hostname: esxi_hostname
        username: esxi_username
        password: esxi_password
        switch_name: vswitch_name
        nic_name: vmnic_name
        mtu: 9000
'''

try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False


def find_vswitch_by_name(host, vswitch_name):
        for vss in host.config.network.vswitch:
            if vss.name == vswitch_name:
                return vss
        return None


class VMwareHostVirtualSwitch(object):
    
    def __init__(self, module):
        self.host_system = None
        self.content = None
        self.vss = None
        self.module = module
        self.switch_name = module.params['switch_name']
        self.number_of_ports = module.params['number_of_ports']
        self.nic_name = module.params['nic_name']
        self.mtu = module.params['mtu']
        self.state = module.params['state']
        self.content = connect_to_api(self.module)

    def process_state(self):
        try:
            vswitch_states = {
                'absent': {
                    'present': self.state_destroy_vswitch,
                    'absent': self.state_exit_unchanged,
                },
                'present': {
                    'update': self.state_update_vswitch,
                    'present': self.state_exit_unchanged,
                    'absent': self.state_create_vswitch,
                }
            }

            vswitch_states[self.state][self.check_vswitch_configuration()]()

        except vmodl.RuntimeFault as runtime_fault:
            self.module.fail_json(msg=runtime_fault.msg)
        except vmodl.MethodFault as method_fault:
            self.module.fail_json(msg=method_fault.msg)
        except Exception as e:
            self.module.fail_json(msg=str(e))


    # Source from
    # https://github.com/rreubenur/pyvmomi-community-samples/blob/patch-1/samples/create_vswitch.py
    
    def state_create_vswitch(self):
        vss_spec = vim.host.VirtualSwitch.Specification()
        vss_spec.numPorts = self.number_of_ports
        vss_spec.mtu = self.mtu
        vss_spec.bridge = vim.host.VirtualSwitch.BondBridge(nicDevice=[self.nic_name])
        self.host_system.configManager.networkSystem.AddVirtualSwitch(vswitchName=self.switch_name, spec=vss_spec)
        self.module.exit_json(changed=True)

    def state_exit_unchanged(self):
        self.module.exit_json(changed=False)

    def state_destroy_vswitch(self):
        config = vim.host.NetworkConfig()
    
        for portgroup in self.host_system.configManager.networkSystem.networkInfo.portgroup:
            if portgroup.spec.vswitchName == self.vss.name:
                portgroup_config = vim.host.PortGroup.Config()
                portgroup_config.changeOperation = "remove"
                portgroup_config.spec = vim.host.PortGroup.Specification()
                portgroup_config.spec.name = portgroup.spec.name
                portgroup_config.spec.name = portgroup.spec.name
                portgroup_config.spec.vlanId = portgroup.spec.vlanId
                portgroup_config.spec.vswitchName = portgroup.spec.vswitchName
                portgroup_config.spec.policy = vim.host.NetworkPolicy()
                config.portgroup.append(portgroup_config)
    
        self.host_system.configManager.networkSystem.UpdateNetworkConfig(config, "modify")
        self.host_system.configManager.networkSystem.RemoveVirtualSwitch(self.vss.name)
        self.module.exit_json(changed=True)

    def state_update_vswitch(self):
        self.module.exit_json(changed=False, msg="Currently not implemented.")

    def check_vswitch_configuration(self):
        host = get_all_objs(self.content, [vim.HostSystem])
        if not host:
            self.module.fail_json(msg="Unable to find host")
    
        self.host_system = host.keys()[0]
        self.vss = find_vswitch_by_name(self.host_system, self.switch_name)
    
        if self.vss is None:
            return 'absent'
        else:
            return 'present'
    

def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(switch_name=dict(required=True, type='str'),
                         nic_name=dict(required=True, type='str'),
                         number_of_ports=dict(required=False, type='int', default=128),
                         mtu=dict(required=False, type='int', default=1500),
                         state=dict(default='present', choices=['present', 'absent'], type='str')))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)

    if not HAS_PYVMOMI:
        module.fail_json(msg='pyvmomi is required for this module')

    host_virtual_switch = VMwareHostVirtualSwitch(module)
    host_virtual_switch.process_state()

from ansible.module_utils.vmware import *
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
