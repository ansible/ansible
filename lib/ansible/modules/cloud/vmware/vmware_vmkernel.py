#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2015, Joseph Callen <jcallen () csc.com>
# Copyright: (c) 2017, Ansible Project
# Copyright: (c) 2017, Abhijeet Kasurde <akasurde@redhat.com>
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
module: vmware_vmkernel
short_description: Create a VMware VMkernel Interface.
description:
    - Create a VMware VMkernel Interface.
version_added: 2.0
author:
- Joseph Callen (@jcpowermac)
- Russell Teague (@mtnbikenc)
- Abhijeet Kasurde (@akasurde) <akasurde@redhat.com>
notes:
    - Tested on vSphere 5.5, 6.5
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
    vswitch_name:
        description:
            - The name of the vswitch where to add the VMK interface.
        required: True
    portgroup_name:
        description:
            - The name of the portgroup for the VMK interface.
        required: True
    network:
        description:
            - A dictionary of network details.
            - 'Following parameter is required:'
            - ' - C(type) (string): Type of IP assignment (either C(dhcp) or C(static)).'
            - 'Following parameters are required in case of C(type) is set to C(static)'
            - ' - C(ip_address) (string): Static IP address (implies C(type: static)).'
            - ' - C(netmask) (string): Static netmask required for C(ip).'
        version_added: 2.5
    ip_address:
        description:
            - The IP Address for the VMK interface.
            - Use C(network) parameter with C(ip_address) instead.
            - Deprecated option, will be removed in version 2.9.
    subnet_mask:
        description:
            - The Subnet Mask for the VMK interface.
            - Use C(network) parameter with C(subnet_mask) instead.
            - Deprecated option, will be removed in version 2.9.
    vland_id:
        description:
            - The VLAN ID for the VMK interface.
        required: True
    mtu:
        description:
            - The MTU for the VMK interface.
        required: False
    enable_vsan:
        description:
            - Enable the VMK interface for VSAN traffic.
        required: False
    enable_vmotion:
        description:
            - Enable the VMK interface for vMotion traffic.
        required: False
    enable_mgmt:
        description:
            - Enable the VMK interface for Management traffic.
        required: False
    enable_ft:
        description:
            - Enable the VMK interface for Fault Tolerance traffic.
        required: False
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
-  name: Add Management vmkernel port using static network type
   vmware_vmkernel:
      hostname: 192.168.127.9
      username: admin
      password: supersecret123
      vswitch_name: vSwitch0
      portgroup_name: PG_0001
      vlan_id: vlan_id
      network:
        type: 'static'
        ip_address: 192.168.127.10
        subnet_mask: 255.255.255.0
      enable_mgmt: True

-  name: Add Management vmkernel port using DHCP network type
   vmware_vmkernel:
      hostname: 192.168.127.9
      username: admin
      password: supersecret123
      vswitch_name: vSwitch0
      portgroup_name: PG_0002
      vlan_id: vlan_id
      network:
        type: 'dhcp'
      enable_mgmt: True
'''

try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import get_all_objs, PyVmomi, vmware_argument_spec


class PyVmomiHelper(PyVmomi):
    def __init__(self, module):
        super(PyVmomiHelper, self).__init__(module)
        self.port_group_name = self.params['portgroup_name']
        self.ip_address = self.params['network'].get('ip_address', None)
        self.subnet_mask = self.params['network'].get('subnet_mask', None)
        self.network_type = self.params['network']['type']
        self.mtu = self.params['mtu']
        self.enable_vsan = self.params['enable_vsan']
        self.enable_vmotion = self.params['enable_vmotion']
        self.enable_mgmt = self.params['enable_mgmt']
        self.enable_ft = self.params['enable_ft']
        self.vswitch_name = self.params['vswitch_name']
        self.vlan_id = self.params['vlan_id']

        # TODO: Add logic to select different hostsystem
        host = get_all_objs(self.content, [vim.HostSystem])
        if not host:
            self.module.fail_json(msg="Unable to locate Physical Host.")
        self.host_system = host.keys()[0]

    def create_vmkernel_adapter(self):
        host_config_manager = self.host_system.configManager
        host_network_system = host_config_manager.networkSystem
        host_virtual_vic_manager = host_config_manager.virtualNicManager
        config = vim.host.NetworkConfig()

        config.portgroup = [vim.host.PortGroup.Config()]
        config.portgroup[0].changeOperation = "add"
        config.portgroup[0].spec = vim.host.PortGroup.Specification()
        config.portgroup[0].spec.name = self.port_group_name
        config.portgroup[0].spec.vlanId = self.vlan_id
        config.portgroup[0].spec.vswitchName = self.vswitch_name
        config.portgroup[0].spec.policy = vim.host.NetworkPolicy()

        config.vnic = [vim.host.VirtualNic.Config()]
        config.vnic[0].changeOperation = "add"
        config.vnic[0].portgroup = self.port_group_name
        config.vnic[0].spec = vim.host.VirtualNic.Specification()
        config.vnic[0].spec.ip = vim.host.IpConfig()

        if self.network_type == 'dhcp':
            config.vnic[0].spec.ip.dhcp = True
        else:
            config.vnic[0].spec.ip.dhcp = False

            if self.ip_address is None:
                self.module.fail_json(msg="network.ip_address is required parameter in "
                                          "case of 'static' network_type.")
            if self.subnet_mask is None:
                self.module.fail_json(msg="network.subnet_mask is required parameter in "
                                          "case of 'static' network_type.")

            config.vnic[0].spec.ip.ipAddress = self.ip_address
            config.vnic[0].spec.ip.subnetMask = self.subnet_mask

        if self.mtu:
            config.vnic[0].spec.mtu = self.mtu

        host_network_config_result = host_network_system.UpdateNetworkConfig(config, "modify")

        for vnic_device in host_network_config_result.vnicDevice:
            if self.enable_vsan:
                vsan_system = host_config_manager.vsanSystem
                vsan_config = vim.vsan.host.ConfigInfo()
                vsan_config.networkInfo = vim.vsan.host.ConfigInfo.NetworkInfo()

                vsan_config.networkInfo.port = [vim.vsan.host.ConfigInfo.NetworkInfo.PortConfig()]

                vsan_config.networkInfo.port[0].device = vnic_device
                vsan_system.UpdateVsan_Task(vsan_config)

            if self.enable_vmotion:
                host_virtual_vic_manager.SelectVnicForNicType("vmotion", vnic_device)

            if self.enable_mgmt:
                host_virtual_vic_manager.SelectVnicForNicType("management", vnic_device)

            if self.enable_ft:
                host_virtual_vic_manager.SelectVnicForNicType("faultToleranceLogging", vnic_device)
        return True


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(portgroup_name=dict(required=True, type='str'),
                              ip_address=dict(removed_in_version=2.9, type='str'),
                              subnet_mask=dict(removed_in_version=2.9, type='str'),
                              mtu=dict(required=False, type='int'),
                              enable_vsan=dict(required=False, type='bool'),
                              enable_vmotion=dict(required=False, type='bool'),
                              enable_mgmt=dict(required=False, type='bool'),
                              enable_ft=dict(required=False, type='bool'),
                              vswitch_name=dict(required=True, type='str'),
                              vlan_id=dict(required=True, type='int'),
                              network=dict(required=True,
                                           type='dict',
                                           options=dict(
                                               type=dict(type='str', choices=['static', 'dhcp']),
                                               ip_address=dict(type='str'),
                                               subnet_mask=dict(type='str'),
                                           ),
                                           ),
                              )
                         )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)
    pyv = PyVmomiHelper(module)
    try:
        changed = pyv.create_vmkernel_adapter()
        module.exit_json(changed=changed)
    except vmodl.RuntimeFault as runtime_fault:
        module.fail_json(msg=runtime_fault.msg)
    except vmodl.MethodFault as method_fault:
        module.fail_json(msg=method_fault.msg)
    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
