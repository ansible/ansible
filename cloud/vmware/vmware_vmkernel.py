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
module: vmware_vmkernel
short_description: Create a VMware VMkernel Interface
description:
    - Create a VMware VMkernel Interface
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
            - The hostname or IP address of the ESXi Server
        required: True
    username:
        description:
            - The username of the ESXi Server
        required: True
        aliases: ['user', 'admin']
    password:
        description:
            - The password of ESXi Server
        required: True
        aliases: ['pass', 'pwd']
    vswitch_name:
        description:
            - The name of the vswitch where to add the VMK interface
        required: True
    portgroup_name:
        description:
            - The name of the portgroup for the VMK interface
        required: True
    ip_address:
        description:
            - The IP Address for the VMK interface
        required: True
    subnet_mask:
        description:
            - The Subnet Mask for the VMK interface
        required: True
    vland_id:
        description:
            - The VLAN ID for the VMK interface
        required: True
    mtu:
        description:
            - The MTU for the VMK interface
        required: False
    enable_vsan:
        description:
            - Enable the VMK interface for VSAN traffic
        required: False
    enable_vmotion:
        description:
            - Enable the VMK interface for vMotion traffic
        required: False
    enable_mgmt:
        description:
            - Enable the VMK interface for Management traffic
        required: False
    enable_ft:
        description:
            - Enable the VMK interface for Fault Tolerance traffic
        required: False
'''

EXAMPLES = '''
# Example command from Ansible Playbook

-  name: Add Management vmkernel port (vmk1)
   local_action:
      module: vmware_vmkernel
      hostname: esxi_hostname
      username: esxi_username
      password: esxi_password
      vswitch_name: vswitch_name
      portgroup_name: portgroup_name
      vlan_id: vlan_id
      ip_address: ip_address
      subnet_mask: subnet_mask
      enable_mgmt: True
'''

try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False


def create_vmkernel_adapter(host_system, port_group_name,
                            vlan_id, vswitch_name,
                            ip_address, subnet_mask,
                            mtu, enable_vsan, enable_vmotion, enable_mgmt, enable_ft):

    host_config_manager = host_system.configManager
    host_network_system = host_config_manager.networkSystem
    host_virtual_vic_manager = host_config_manager.virtualNicManager
    config = vim.host.NetworkConfig()

    config.portgroup = [vim.host.PortGroup.Config()]
    config.portgroup[0].changeOperation = "add"
    config.portgroup[0].spec = vim.host.PortGroup.Specification()
    config.portgroup[0].spec.name = port_group_name
    config.portgroup[0].spec.vlanId = vlan_id
    config.portgroup[0].spec.vswitchName = vswitch_name
    config.portgroup[0].spec.policy = vim.host.NetworkPolicy()

    config.vnic = [vim.host.VirtualNic.Config()]
    config.vnic[0].changeOperation = "add"
    config.vnic[0].portgroup = port_group_name
    config.vnic[0].spec = vim.host.VirtualNic.Specification()
    config.vnic[0].spec.ip = vim.host.IpConfig()
    config.vnic[0].spec.ip.dhcp = False
    config.vnic[0].spec.ip.ipAddress = ip_address
    config.vnic[0].spec.ip.subnetMask = subnet_mask
    if mtu:
        config.vnic[0].spec.mtu = mtu

    host_network_config_result = host_network_system.UpdateNetworkConfig(config, "modify")

    for vnic_device in host_network_config_result.vnicDevice:
        if enable_vsan:
            vsan_system = host_config_manager.vsanSystem
            vsan_config = vim.vsan.host.ConfigInfo()
            vsan_config.networkInfo = vim.vsan.host.ConfigInfo.NetworkInfo()

            vsan_config.networkInfo.port = [vim.vsan.host.ConfigInfo.NetworkInfo.PortConfig()]

            vsan_config.networkInfo.port[0].device = vnic_device
            host_vsan_config_result = vsan_system.UpdateVsan_Task(vsan_config)

        if enable_vmotion:
            host_virtual_vic_manager.SelectVnicForNicType("vmotion", vnic_device)

        if enable_mgmt:
            host_virtual_vic_manager.SelectVnicForNicType("management", vnic_device)

        if enable_ft:
            host_virtual_vic_manager.SelectVnicForNicType("faultToleranceLogging", vnic_device)
    return True


def main():

    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(portgroup_name=dict(required=True, type='str'),
                         ip_address=dict(required=True, type='str'),
                         subnet_mask=dict(required=True, type='str'),
                         mtu=dict(required=False, type='int'),
                         enable_vsan=dict(required=False, type='bool'),
                         enable_vmotion=dict(required=False, type='bool'),
                         enable_mgmt=dict(required=False, type='bool'),
                         enable_ft=dict(required=False, type='bool'),
                         vswitch_name=dict(required=True, type='str'),
                         vlan_id=dict(required=True, type='int')))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)

    if not HAS_PYVMOMI:
        module.fail_json(msg='pyvmomi is required for this module')

    port_group_name = module.params['portgroup_name']
    ip_address = module.params['ip_address']
    subnet_mask = module.params['subnet_mask']
    mtu = module.params['mtu']
    enable_vsan = module.params['enable_vsan']
    enable_vmotion = module.params['enable_vmotion']
    enable_mgmt = module.params['enable_mgmt']
    enable_ft = module.params['enable_ft']
    vswitch_name = module.params['vswitch_name']
    vlan_id = module.params['vlan_id']

    try:
        content = connect_to_api(module)
        host = get_all_objs(content, [vim.HostSystem])
        if not host:
            module.fail_json(msg="Unable to locate Physical Host.")
        host_system = host.keys()[0]
        changed = create_vmkernel_adapter(host_system, port_group_name,
                                          vlan_id, vswitch_name,
                                          ip_address, subnet_mask,
                                          mtu, enable_vsan, enable_vmotion, enable_mgmt, enable_ft)
        module.exit_json(changed=changed)
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
