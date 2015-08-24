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
    hostname:
        description:
            - The hostname or IP address of the ESXi server
        required: True
    username:
        description:
            - The username of the ESXi server
        required: True
        aliases: ['user', 'admin']
    password:
        description:
            - The password of the ESXi server
        required: True
        aliases: ['pass', 'pwd']
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


# Source from
# https://github.com/rreubenur/pyvmomi-community-samples/blob/patch-1/samples/create_vswitch.py

def state_create_vswitch(module):

    switch_name = module.params['switch_name']
    number_of_ports = module.params['number_of_ports']
    nic_name = module.params['nic_name']
    mtu = module.params['mtu']
    host = module.params['host']

    vss_spec = vim.host.VirtualSwitch.Specification()
    vss_spec.numPorts = number_of_ports
    vss_spec.mtu = mtu
    vss_spec.bridge = vim.host.VirtualSwitch.BondBridge(nicDevice=[nic_name])
    host.configManager.networkSystem.AddVirtualSwitch(vswitchName=switch_name, spec=vss_spec)
    module.exit_json(changed=True)


def state_exit_unchanged(module):
    module.exit_json(changed=False)


def state_destroy_vswitch(module):
    vss = module.params['vss']
    host = module.params['host']
    config = vim.host.NetworkConfig()

    for portgroup in host.configManager.networkSystem.networkInfo.portgroup:
        if portgroup.spec.vswitchName == vss.name:
            portgroup_config = vim.host.PortGroup.Config()
            portgroup_config.changeOperation = "remove"
            portgroup_config.spec = vim.host.PortGroup.Specification()
            portgroup_config.spec.name = portgroup.spec.name
            portgroup_config.spec.vlanId = portgroup.spec.vlanId
            portgroup_config.spec.vswitchName = portgroup.spec.vswitchName
            portgroup_config.spec.policy = vim.host.NetworkPolicy()
            config.portgroup.append(portgroup_config)

    host.configManager.networkSystem.UpdateNetworkConfig(config, "modify")
    host.configManager.networkSystem.RemoveVirtualSwitch(vss.name)
    module.exit_json(changed=True)


def state_update_vswitch(module):
    module.exit_json(changed=False, msg="Currently not implemented.")


def check_vswitch_configuration(module):
    switch_name = module.params['switch_name']
    content = connect_to_api(module)
    module.params['content'] = content

    host = get_all_objs(content, [vim.HostSystem])
    if not host:
        module.fail_json(msg="Unble to find host")

    host_system = host.keys()[0]
    module.params['host'] = host_system
    vss = find_vswitch_by_name(host_system, switch_name)

    if vss is None:
        return 'absent'
    else:
        module.params['vss'] = vss
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

    try:
        vswitch_states = {
            'absent': {
                'present': state_destroy_vswitch,
                'absent': state_exit_unchanged,
            },
            'present': {
                'update': state_update_vswitch,
                'present': state_exit_unchanged,
                'absent': state_create_vswitch,
            }
        }

        vswitch_states[module.params['state']][check_vswitch_configuration(module)](module)

    except vmodl.RuntimeFault as runtime_fault:
        module.fail_json(msg=runtime_fault.msg)
    except vmodl.MethodFault as method_fault:
        module.fail_json(msg=method_fault.msg)
    except Exception as e:
        module.fail_json(msg=str(e))

from ansible.module_utils.vmware import *
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
