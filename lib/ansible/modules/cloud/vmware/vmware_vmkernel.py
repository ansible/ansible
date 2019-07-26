#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Joseph Callen <jcallen () csc.com>
# Copyright: (c) 2017-18, Ansible Project
# Copyright: (c) 2017-18, Abhijeet Kasurde <akasurde@redhat.com>
# Copyright: (c) 2018, Christian Kotte <christian.kotte@gmx.de>
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
short_description: Manages a VMware VMkernel Adapter of an ESXi host.
description:
    - This module can be used to manage the VMKernel adapters / VMKernel network interfaces of an ESXi host.
    - The module assumes that the host is already configured with the Port Group in case of a vSphere Standard Switch (vSS).
    - The module assumes that the host is already configured with the Distributed Port Group in case of a vSphere Distributed Switch (vDS).
    - The module automatically migrates the VMKernel adapter from vSS to vDS or vice versa if present.
version_added: 2.0
author:
- Joseph Callen (@jcpowermac)
- Russell Teague (@mtnbikenc)
- Abhijeet Kasurde (@Akasurde)
- Christian Kotte (@ckotte)
notes:
    - The option C(device) need to be used with DHCP because otherwise it's not possible to check if a VMkernel device is already present
    - You can only change from DHCP to static, and vSS to vDS, or vice versa, in one step, without creating a new device, with C(device) specified.
    - You can only create the VMKernel adapter on a vDS if authenticated to vCenter and not if authenticated to ESXi.
    - Tested on vSphere 5.5 and 6.5
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
    vswitch_name:
      description:
      - The name of the vSwitch where to add the VMKernel interface.
      - Required parameter only if C(state) is set to C(present).
      - Optional parameter from version 2.5 and onwards.
      type: str
      aliases: ['vswitch']
    dvswitch_name:
      description:
      - The name of the vSphere Distributed Switch (vDS) where to add the VMKernel interface.
      - Required parameter only if C(state) is set to C(present).
      - Optional parameter from version 2.8 and onwards.
      type: str
      aliases: ['dvswitch']
      version_added: 2.8
    portgroup_name:
      description:
      - The name of the port group for the VMKernel interface.
      required: True
      aliases: ['portgroup']
      type: str
    network:
      description:
      - A dictionary of network details.
      - 'The following parameter is required:'
      - ' - C(type) (string): Type of IP assignment (either C(dhcp) or C(static)).'
      - 'The following parameters are required in case of C(type) is set to C(static):'
      - ' - C(ip_address) (string): Static IP address (implies C(type: static)).'
      - ' - C(subnet_mask) (string): Static netmask required for C(ip_address).'
      - 'The following parameter is optional in case of C(type) is set to C(static):'
      - ' - C(default_gateway) (string): Default gateway (Override default gateway for this adapter).'
      - 'The following parameter is optional:'
      - ' - C(tcpip_stack) (string): The TCP/IP stack for the VMKernel interface. Can be default, provisioning, vmotion, or vxlan. (default: default)'
      type: dict
      default: {
          type: 'static',
          tcpip_stack: 'default',
      }
      version_added: 2.5
    ip_address:
      description:
      - The IP Address for the VMKernel interface.
      - Use C(network) parameter with C(ip_address) instead.
      - Deprecated option, will be removed in version 2.9.
      type: str
    subnet_mask:
      description:
      - The Subnet Mask for the VMKernel interface.
      - Use C(network) parameter with C(subnet_mask) instead.
      - Deprecated option, will be removed in version 2.9.
      type: str
    mtu:
      description:
      - The MTU for the VMKernel interface.
      - The default value of 1500 is valid from version 2.5 and onwards.
      default: 1500
      type: int
    device:
      description:
      - Search VMkernel adapter by device name.
      - The parameter is required only in case of C(type) is set to C(dhcp).
      version_added: 2.8
      type: str
    enable_vsan:
      description:
      - Enable VSAN traffic on the VMKernel adapter.
      - This option is only allowed if the default TCP/IP stack is used.
      type: bool
    enable_vmotion:
      description:
      - Enable vMotion traffic on the VMKernel adapter.
      - This option is only allowed if the default TCP/IP stack is used.
      - You cannot enable vMotion on an additional adapter if you already have an adapter with the vMotion TCP/IP stack configured.
      type: bool
    enable_mgmt:
      description:
      - Enable Management traffic on the VMKernel adapter.
      - This option is only allowed if the default TCP/IP stack is used.
      type: bool
    enable_ft:
      description:
      - Enable Fault Tolerance traffic on the VMKernel adapter.
      - This option is only allowed if the default TCP/IP stack is used.
      type: bool
    enable_provisioning:
      description:
      - Enable Provisioning traffic on the VMKernel adapter.
      - This option is only allowed if the default TCP/IP stack is used.
      type: bool
      version_added: 2.8
    enable_replication:
      description:
      - Enable vSphere Replication traffic on the VMKernel adapter.
      - This option is only allowed if the default TCP/IP stack is used.
      type: bool
      version_added: 2.8
    enable_replication_nfc:
      description:
      - Enable vSphere Replication NFC traffic on the VMKernel adapter.
      - This option is only allowed if the default TCP/IP stack is used.
      type: bool
      version_added: 2.8
    state:
      description:
      - If set to C(present), the VMKernel adapter will be created with the given specifications.
      - If set to C(absent), the VMKernel adapter will be removed.
      - If set to C(present) and VMKernel adapter exists, the configurations will be updated.
      choices: [ present, absent ]
      default: present
      version_added: 2.5
      type: str
    esxi_hostname:
      description:
      - Name of ESXi host to which VMKernel is to be managed.
      - "From version 2.5 onwards, this parameter is required."
      required: True
      version_added: 2.5
      type: str
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
-  name: Add Management vmkernel port using static network type
   vmware_vmkernel:
      hostname: '{{ esxi_hostname }}'
      username: '{{ esxi_username }}'
      password: '{{ esxi_password }}'
      esxi_hostname: '{{ esxi_hostname }}'
      vswitch_name: vSwitch0
      portgroup_name: PG_0001
      network:
        type: 'static'
        ip_address: 192.168.127.10
        subnet_mask: 255.255.255.0
      state: present
      enable_mgmt: True
   delegate_to: localhost

-  name: Add Management vmkernel port using DHCP network type
   vmware_vmkernel:
      hostname: '{{ esxi_hostname }}'
      username: '{{ esxi_username }}'
      password: '{{ esxi_password }}'
      esxi_hostname: '{{ esxi_hostname }}'
      vswitch_name: vSwitch0
      portgroup_name: PG_0002
      state: present
      network:
        type: 'dhcp'
      enable_mgmt: True
   delegate_to: localhost

-  name: Change IP allocation from static to dhcp
   vmware_vmkernel:
      hostname: '{{ esxi_hostname }}'
      username: '{{ esxi_username }}'
      password: '{{ esxi_password }}'
      esxi_hostname: '{{ esxi_hostname }}'
      vswitch_name: vSwitch0
      portgroup_name: PG_0002
      state: present
      device: vmk1
      network:
        type: 'dhcp'
      enable_mgmt: True
   delegate_to: localhost

-  name: Delete VMkernel port
   vmware_vmkernel:
      hostname: '{{ esxi_hostname }}'
      username: '{{ esxi_username }}'
      password: '{{ esxi_password }}'
      esxi_hostname: '{{ esxi_hostname }}'
      vswitch_name: vSwitch0
      portgroup_name: PG_0002
      state: absent
   delegate_to: localhost

-  name: Add Management vmkernel port to Distributed Switch
   vmware_vmkernel:
      hostname: '{{ vcenter_hostname }}'
      username: '{{ vcenter_username }}'
      password: '{{ vcenter_password }}'
      esxi_hostname: '{{ esxi_hostname }}'
      dvswitch_name: dvSwitch1
      portgroup_name: dvPG_0001
      network:
        type: 'static'
        ip_address: 192.168.127.10
        subnet_mask: 255.255.255.0
      state: present
      enable_mgmt: True
   delegate_to: localhost

-  name: Add vMotion vmkernel port with vMotion TCP/IP stack
   vmware_vmkernel:
      hostname: '{{ vcenter_hostname }}'
      username: '{{ vcenter_username }}'
      password: '{{ vcenter_password }}'
      esxi_hostname: '{{ esxi_hostname }}'
      dvswitch_name: dvSwitch1
      portgroup_name: dvPG_0001
      network:
        type: 'static'
        ip_address: 192.168.127.10
        subnet_mask: 255.255.255.0
        tcpip_stack: vmotion
      state: present
   delegate_to: localhost
'''

RETURN = r'''
result:
    description: metadata about VMKernel name
    returned: always
    type: dict
    sample: {
        "changed": false,
        "msg": "VMkernel Adapter already configured properly",
        "device": "vmk1",
        "ipv4": "static",
        "ipv4_gw": "No override",
        "ipv4_ip": "192.168.1.15",
        "ipv4_sm": "255.255.255.0",
        "mtu": 9000,
        "services": "vMotion",
        "switch": "vDS"
    }
'''

try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import (
    PyVmomi, TaskError, vmware_argument_spec, wait_for_task,
    find_dvspg_by_name, find_dvs_by_name, get_all_objs
)
from ansible.module_utils._text import to_native


class PyVmomiHelper(PyVmomi):
    """Class to manage VMkernel configuration of an ESXi host system"""

    def __init__(self, module):
        super(PyVmomiHelper, self).__init__(module)
        if self.params['network']:
            self.network_type = self.params['network'].get('type')
            self.ip_address = self.params['network'].get('ip_address', None)
            self.subnet_mask = self.params['network'].get('subnet_mask', None)
            self.default_gateway = self.params['network'].get('default_gateway', None)
            self.tcpip_stack = self.params['network'].get('tcpip_stack')
        self.device = self.params['device']
        if self.network_type == 'dhcp' and not self.device:
            module.fail_json(msg="device is a required parameter when network type is set to 'dhcp'")
        self.mtu = self.params['mtu']
        self.enable_vsan = self.params['enable_vsan']
        self.enable_vmotion = self.params['enable_vmotion']
        self.enable_mgmt = self.params['enable_mgmt']
        self.enable_ft = self.params['enable_ft']
        self.enable_provisioning = self.params['enable_provisioning']
        self.enable_replication = self.params['enable_replication']
        self.enable_replication_nfc = self.params['enable_replication_nfc']

        self.vswitch_name = self.params['vswitch_name']
        self.vds_name = self.params['dvswitch_name']
        self.port_group_name = self.params['portgroup_name']

        self.esxi_host_name = self.params['esxi_hostname']
        hosts = self.get_all_host_objs(esxi_host_name=self.esxi_host_name)
        if hosts:
            self.esxi_host_obj = hosts[0]
        else:
            self.module.fail_json(
                msg="Failed to get details of ESXi server. Please specify esxi_hostname."
            )

        if self.network_type == 'static':
            if self.module.params['state'] == 'absent':
                pass
            elif not self.ip_address:
                module.fail_json(msg="ip_address is a required parameter when network type is set to 'static'")
            elif not self.subnet_mask:
                module.fail_json(msg="subnet_mask is a required parameter when network type is set to 'static'")

        # find Port Group
        if self.vswitch_name:
            self.port_group_obj = self.get_port_group_by_name(
                host_system=self.esxi_host_obj,
                portgroup_name=self.port_group_name,
                vswitch_name=self.vswitch_name
            )
            if not self.port_group_obj:
                module.fail_json(msg="Portgroup '%s' not found on vSS '%s'" % (self.port_group_name, self.vswitch_name))
        elif self.vds_name:
            self.dv_switch_obj = find_dvs_by_name(self.content, self.vds_name)
            if not self.dv_switch_obj:
                module.fail_json(msg="vDS '%s' not found" % self.vds_name)
            self.port_group_obj = find_dvspg_by_name(self.dv_switch_obj, self.port_group_name)
            if not self.port_group_obj:
                module.fail_json(msg="Portgroup '%s' not found on vDS '%s'" % (self.port_group_name, self.vds_name))

        # find VMkernel Adapter
        if self.device:
            self.vnic = self.get_vmkernel_by_device(device_name=self.device)
        else:
            # config change (e.g. DHCP to static, or vice versa); doesn't work with virtual port change
            self.vnic = self.get_vmkernel_by_portgroup_new(port_group_name=self.port_group_name)
            if not self.vnic and self.network_type == 'static':
                # vDS to vSS or vSS to vSS (static IP)
                self.vnic = self.get_vmkernel_by_ip(ip_address=self.ip_address)

    def get_port_group_by_name(self, host_system, portgroup_name, vswitch_name):
        """
        Get specific port group by given name
        Args:
            host_system: Name of Host System
            portgroup_name: Name of Port Group
            vswitch_name: Name of the vSwitch

        Returns: List of port groups by given specifications

        """
        portgroups = self.get_all_port_groups_by_host(host_system=host_system)

        for portgroup in portgroups:
            if portgroup.spec.vswitchName == vswitch_name and portgroup.spec.name == portgroup_name:
                return portgroup
        return None

    def ensure(self):
        """
        Manage internal VMKernel management
        Returns: NA

        """
        host_vmk_states = {
            'absent': {
                'present': self.host_vmk_delete,
                'absent': self.host_vmk_unchange,
            },
            'present': {
                'present': self.host_vmk_update,
                'absent': self.host_vmk_create,
            }
        }

        try:
            host_vmk_states[self.module.params['state']][self.check_state()]()
        except vmodl.RuntimeFault as runtime_fault:
            self.module.fail_json(msg=to_native(runtime_fault.msg))
        except vmodl.MethodFault as method_fault:
            self.module.fail_json(msg=to_native(method_fault.msg))

    def get_vmkernel_by_portgroup_new(self, port_group_name=None):
        """
        Check if vmkernel available or not
        Args:
            port_group_name: name of port group

        Returns: vmkernel managed object if vmkernel found, false if not

        """
        for vnic in self.esxi_host_obj.config.network.vnic:
            # check if it's a vSS Port Group
            if vnic.spec.portgroup == port_group_name:
                return vnic
            # check if it's a vDS Port Group
            try:
                if vnic.spec.distributedVirtualPort.portgroupKey == self.port_group_obj.key:
                    return vnic
            except AttributeError:
                pass
        return False

    def get_vmkernel_by_ip(self, ip_address):
        """
        Check if vmkernel available or not
        Args:
            ip_address: IP address of vmkernel device

        Returns: vmkernel managed object if vmkernel found, false if not

        """
        for vnic in self.esxi_host_obj.config.network.vnic:
            if vnic.spec.ip.ipAddress == ip_address:
                return vnic
        return None

    def get_vmkernel_by_device(self, device_name):
        """
        Check if vmkernel available or not
        Args:
            device_name: name of vmkernel device

        Returns: vmkernel managed object if vmkernel found, false if not

        """
        for vnic in self.esxi_host_obj.config.network.vnic:
            if vnic.device == device_name:
                return vnic
        return None

    def check_state(self):
        """
        Check internal state management
        Returns: Present if found and absent if not found

        """
        return 'present' if self.vnic else 'absent'

    def host_vmk_delete(self):
        """
        Delete VMKernel
        Returns: NA

        """
        results = dict(changed=False, msg='')
        vmk_device = self.vnic.device
        try:
            if self.module.check_mode:
                results['msg'] = "VMkernel Adapter would be deleted"
            else:
                self.esxi_host_obj.configManager.networkSystem.RemoveVirtualNic(vmk_device)
                results['msg'] = "VMkernel Adapter deleted"
            results['changed'] = True
            results['device'] = vmk_device
        except vim.fault.NotFound as not_found:
            self.module.fail_json(
                msg="Failed to find vmk to delete due to %s" %
                to_native(not_found.msg)
            )
        except vim.fault.HostConfigFault as host_config_fault:
            self.module.fail_json(
                msg="Failed to delete vmk due host config issues : %s" %
                to_native(host_config_fault.msg)
            )

        self.module.exit_json(**results)

    def host_vmk_unchange(self):
        """
        Denote no change in VMKernel
        Returns: NA

        """
        self.module.exit_json(changed=False)

    def host_vmk_update(self):
        """
        Update VMKernel with given parameters
        Returns: NA

        """
        changed = changed_settings = changed_vds = changed_services = \
            changed_service_vmotion = changed_service_mgmt = changed_service_ft = \
            changed_service_vsan = changed_service_prov = changed_service_rep = changed_service_rep_nfc = False
        changed_list = []
        results = dict(changed=False, msg='')

        results['tcpip_stack'] = self.tcpip_stack
        net_stack_instance_key = self.get_api_net_stack_instance(self.tcpip_stack)
        if self.vnic.spec.netStackInstanceKey != net_stack_instance_key:
            self.module.fail_json(msg="The TCP/IP stack cannot be changed on an existing VMkernel adapter!")

        # Check MTU
        results['mtu'] = self.mtu
        if self.vnic.spec.mtu != self.mtu:
            changed_settings = True
            changed_list.append("MTU")
            results['mtu_previous'] = self.vnic.spec.mtu

        # Check IPv4 settings
        results['ipv4'] = self.network_type
        results['ipv4_ip'] = self.ip_address
        results['ipv4_sm'] = self.subnet_mask
        if self.default_gateway:
            results['ipv4_gw'] = self.default_gateway
        else:
            results['ipv4_gw'] = "No override"
        if self.vnic.spec.ip.dhcp:
            if self.network_type == 'static':
                changed_settings = True
                changed_list.append("IPv4 settings")
                results['ipv4_previous'] = "DHCP"
        if not self.vnic.spec.ip.dhcp:
            if self.network_type == 'dhcp':
                changed_settings = True
                changed_list.append("IPv4 settings")
                results['ipv4_previous'] = "static"
            elif self.network_type == 'static':
                if self.ip_address != self.vnic.spec.ip.ipAddress:
                    changed_settings = True
                    changed_list.append("IP")
                    results['ipv4_ip_previous'] = self.vnic.spec.ip.ipAddress
                if self.subnet_mask != self.vnic.spec.ip.subnetMask:
                    changed_settings = True
                    changed_list.append("SM")
                    results['ipv4_sm_previous'] = self.vnic.spec.ip.subnetMask
                if self.default_gateway:
                    try:
                        if self.default_gateway != self.vnic.spec.ipRouteSpec.ipRouteConfig.defaultGateway:
                            changed_settings = True
                            changed_list.append("GW override")
                            results['ipv4_gw_previous'] = self.vnic.spec.ipRouteSpec.ipRouteConfig.defaultGateway
                    except AttributeError:
                        changed_settings = True
                        changed_list.append("GW override")
                        results['ipv4_gw_previous'] = "No override"
                else:
                    try:
                        if self.vnic.spec.ipRouteSpec.ipRouteConfig.defaultGateway:
                            changed_settings = True
                            changed_list.append("GW override")
                            results['ipv4_gw_previous'] = self.vnic.spec.ipRouteSpec.ipRouteConfig.defaultGateway
                    except AttributeError:
                        pass

        # Check virtual port (vSS or vDS)
        results['portgroup'] = self.port_group_name
        dvs_uuid = None
        if self.vswitch_name:
            results['switch'] = self.vswitch_name
            try:
                if self.vnic.spec.distributedVirtualPort.switchUuid:
                    changed_vds = True
                    changed_list.append("Virtual Port")
                    dvs_uuid = self.vnic.spec.distributedVirtualPort.switchUuid
            except AttributeError:
                pass
            if changed_vds:
                results['switch_previous'] = self.find_dvs_by_uuid(dvs_uuid)
                self.dv_switch_obj = find_dvs_by_name(self.content, results['switch_previous'])
                results['portgroup_previous'] = self.find_dvspg_by_key(
                    self.dv_switch_obj, self.vnic.spec.distributedVirtualPort.portgroupKey
                )
        elif self.vds_name:
            results['switch'] = self.vds_name
            try:
                if self.vnic.spec.distributedVirtualPort.switchUuid != self.dv_switch_obj.uuid:
                    changed_vds = True
                    changed_list.append("Virtual Port")
                    dvs_uuid = self.vnic.spec.distributedVirtualPort.switchUuid
            except AttributeError:
                changed_vds = True
                changed_list.append("Virtual Port")
            if changed_vds:
                results['switch_previous'] = self.find_dvs_by_uuid(dvs_uuid)
                results['portgroup_previous'] = self.vnic.spec.portgroup
                portgroups = self.get_all_port_groups_by_host(host_system=self.esxi_host_obj)
                for portgroup in portgroups:
                    if portgroup.spec.name == self.vnic.spec.portgroup:
                        results['switch_previous'] = portgroup.spec.vswitchName

        results['services'] = self.create_enabled_services_string()
        # Check configuration of service types (only if default TCP/IP stack is used)
        if self.vnic.spec.netStackInstanceKey == 'defaultTcpipStack':
            service_type_vmks = self.get_all_vmks_by_service_type()
            if (self.enable_vmotion and self.vnic.device not in service_type_vmks['vmotion']) or \
                    (not self.enable_vmotion and self.vnic.device in service_type_vmks['vmotion']):
                changed_services = changed_service_vmotion = True

            if (self.enable_mgmt and self.vnic.device not in service_type_vmks['management']) or \
                    (not self.enable_mgmt and self.vnic.device in service_type_vmks['management']):
                changed_services = changed_service_mgmt = True

            if (self.enable_ft and self.vnic.device not in service_type_vmks['faultToleranceLogging']) or \
                    (not self.enable_ft and self.vnic.device in service_type_vmks['faultToleranceLogging']):
                changed_services = changed_service_ft = True

            if (self.enable_vsan and self.vnic.device not in service_type_vmks['vsan']) or \
                    (not self.enable_vsan and self.vnic.device in service_type_vmks['vsan']):
                changed_services = changed_service_vsan = True

            if (self.enable_provisioning and self.vnic.device not in service_type_vmks['vSphereProvisioning']) or \
                    (not self.enable_provisioning and self.vnic.device in service_type_vmks['vSphereProvisioning']):
                changed_services = changed_service_prov = True

            if (self.enable_replication and self.vnic.device not in service_type_vmks['vSphereReplication']) or \
                    (not self.enable_provisioning and self.vnic.device in service_type_vmks['vSphereReplication']):
                changed_services = changed_service_rep = True

            if (self.enable_replication_nfc and self.vnic.device not in service_type_vmks['vSphereReplicationNFC']) or \
                    (not self.enable_provisioning and self.vnic.device in service_type_vmks['vSphereReplicationNFC']):
                changed_services = changed_service_rep_nfc = True
            if changed_services:
                changed_list.append("services")

        if changed_settings or changed_vds or changed_services:
            changed = True
            if self.module.check_mode:
                changed_suffix = ' would be updated'
            else:
                changed_suffix = ' updated'
            if len(changed_list) > 2:
                message = ', '.join(changed_list[:-1]) + ', and ' + str(changed_list[-1])
            elif len(changed_list) == 2:
                message = ' and '.join(changed_list)
            elif len(changed_list) == 1:
                message = changed_list[0]
            message = "VMkernel Adapter " + message + changed_suffix
            if changed_settings or changed_vds:
                vnic_config = vim.host.VirtualNic.Specification()
                ip_spec = vim.host.IpConfig()
                if self.network_type == 'dhcp':
                    ip_spec.dhcp = True
                else:
                    ip_spec.dhcp = False
                    ip_spec.ipAddress = self.ip_address
                    ip_spec.subnetMask = self.subnet_mask
                    if self.default_gateway:
                        vnic_config.ipRouteSpec = vim.host.VirtualNic.IpRouteSpec()
                        vnic_config.ipRouteSpec.ipRouteConfig = vim.host.IpRouteConfig()
                        vnic_config.ipRouteSpec.ipRouteConfig.defaultGateway = self.default_gateway
                    else:
                        vnic_config.ipRouteSpec = vim.host.VirtualNic.IpRouteSpec()
                        vnic_config.ipRouteSpec.ipRouteConfig = vim.host.IpRouteConfig()

                vnic_config.ip = ip_spec
                vnic_config.mtu = self.mtu

                if changed_vds:
                    if self.vswitch_name:
                        vnic_config.portgroup = self.port_group_name
                    elif self.vds_name:
                        vnic_config.distributedVirtualPort = vim.dvs.PortConnection()
                        vnic_config.distributedVirtualPort.switchUuid = self.dv_switch_obj.uuid
                        vnic_config.distributedVirtualPort.portgroupKey = self.port_group_obj.key

                try:
                    if not self.module.check_mode:
                        self.esxi_host_obj.configManager.networkSystem.UpdateVirtualNic(self.vnic.device, vnic_config)
                except vim.fault.NotFound as not_found:
                    self.module.fail_json(
                        msg="Failed to update vmk as virtual network adapter cannot be found %s" %
                        to_native(not_found.msg)
                    )
                except vim.fault.HostConfigFault as host_config_fault:
                    self.module.fail_json(
                        msg="Failed to update vmk due to host config issues : %s" %
                        to_native(host_config_fault.msg)
                    )
                except vim.fault.InvalidState as invalid_state:
                    self.module.fail_json(
                        msg="Failed to update vmk as ipv6 address is specified in an ipv4 only system : %s" %
                        to_native(invalid_state.msg)
                    )
                except vmodl.fault.InvalidArgument as invalid_arg:
                    self.module.fail_json(
                        msg="Failed to update vmk as IP address or Subnet Mask in the IP configuration"
                        "are invalid or PortGroup does not exist : %s" % to_native(invalid_arg.msg)
                    )

            if changed_services:
                changed_list.append("Services")
                services_previous = []
                vnic_manager = self.esxi_host_obj.configManager.virtualNicManager

                if changed_service_mgmt:
                    if self.vnic.device in service_type_vmks['management']:
                        services_previous.append('Mgmt')
                    operation = 'select' if self.enable_mgmt else 'deselect'
                    self.set_service_type(
                        vnic_manager=vnic_manager, vmk=self.vnic, service_type='management', operation=operation
                    )

                if changed_service_vmotion:
                    if self.vnic.device in service_type_vmks['vmotion']:
                        services_previous.append('vMotion')
                    operation = 'select' if self.enable_vmotion else 'deselect'
                    self.set_service_type(
                        vnic_manager=vnic_manager, vmk=self.vnic, service_type='vmotion', operation=operation
                    )

                if changed_service_ft:
                    if self.vnic.device in service_type_vmks['faultToleranceLogging']:
                        services_previous.append('FT')
                    operation = 'select' if self.enable_ft else 'deselect'
                    self.set_service_type(
                        vnic_manager=vnic_manager, vmk=self.vnic, service_type='faultToleranceLogging', operation=operation
                    )

                if changed_service_prov:
                    if self.vnic.device in service_type_vmks['vSphereProvisioning']:
                        services_previous.append('Prov')
                    operation = 'select' if self.enable_provisioning else 'deselect'
                    self.set_service_type(
                        vnic_manager=vnic_manager, vmk=self.vnic, service_type='vSphereProvisioning', operation=operation
                    )

                if changed_service_rep:
                    if self.vnic.device in service_type_vmks['vSphereReplication']:
                        services_previous.append('Repl')
                    operation = 'select' if self.enable_replication else 'deselect'
                    self.set_service_type(
                        vnic_manager=vnic_manager, vmk=self.vnic, service_type='vSphereReplication', operation=operation
                    )

                if changed_service_rep_nfc:
                    if self.vnic.device in service_type_vmks['vSphereReplicationNFC']:
                        services_previous.append('Repl_NFC')
                    operation = 'select' if self.enable_replication_nfc else 'deselect'
                    self.set_service_type(
                        vnic_manager=vnic_manager, vmk=self.vnic, service_type='vSphereReplicationNFC', operation=operation
                    )

                if changed_service_vsan:
                    if self.vnic.device in service_type_vmks['vsan']:
                        services_previous.append('VSAN')
                    if self.enable_vsan:
                        results['vsan'] = self.set_vsan_service_type()
                    else:
                        self.set_service_type(
                            vnic_manager=vnic_manager, vmk=self.vnic, service_type='vsan', operation=operation
                        )

                results['services_previous'] = ', '.join(services_previous)
        else:
            message = "VMkernel Adapter already configured properly"

        results['changed'] = changed
        results['msg'] = message
        results['device'] = self.vnic.device
        self.module.exit_json(**results)

    def find_dvs_by_uuid(self, uuid):
        """
        Find DVS by UUID
        Returns: DVS name
        """
        dvs_list = get_all_objs(self.content, [vim.DistributedVirtualSwitch])
        for dvs in dvs_list:
            if dvs.uuid == uuid:
                return dvs.summary.name
        return None

    def find_dvspg_by_key(self, dv_switch, portgroup_key):
        """
        Find dvPortgroup by key
        Returns: dvPortgroup name
        """

        portgroups = dv_switch.portgroup

        for portgroup in portgroups:
            if portgroup.key == portgroup_key:
                return portgroup.name

        return None

    def set_vsan_service_type(self):
        """
        Set VSAN service type
        Returns: result of UpdateVsan_Task

        """
        result = None
        vsan_system = self.esxi_host_obj.configManager.vsanSystem

        vsan_port_config = vim.vsan.host.ConfigInfo.NetworkInfo.PortConfig()
        vsan_port_config.device = self.vnic.device

        vsan_config = vim.vsan.host.ConfigInfo()
        vsan_config.networkInfo = vim.vsan.host.ConfigInfo.NetworkInfo()
        vsan_config.networkInfo.port = [vsan_port_config]
        if not self.module.check_mode:
            try:
                vsan_task = vsan_system.UpdateVsan_Task(vsan_config)
                wait_for_task(vsan_task)
            except TaskError as task_err:
                self.module.fail_json(
                    msg="Failed to set service type to vsan for %s : %s" % (self.vnic.device, to_native(task_err))
                )
        return result

    def host_vmk_create(self):
        """
        Create VMKernel
        Returns: NA

        """
        results = dict(changed=False, message='')
        if self.vswitch_name:
            results['switch'] = self.vswitch_name
        elif self.vds_name:
            results['switch'] = self.vds_name
        results['portgroup'] = self.port_group_name

        vnic_config = vim.host.VirtualNic.Specification()

        ip_spec = vim.host.IpConfig()
        results['ipv4'] = self.network_type
        if self.network_type == 'dhcp':
            ip_spec.dhcp = True
        else:
            ip_spec.dhcp = False
            results['ipv4_ip'] = self.ip_address
            results['ipv4_sm'] = self.subnet_mask
            ip_spec.ipAddress = self.ip_address
            ip_spec.subnetMask = self.subnet_mask
            if self.default_gateway:
                vnic_config.ipRouteSpec = vim.host.VirtualNic.IpRouteSpec()
                vnic_config.ipRouteSpec.ipRouteConfig = vim.host.IpRouteConfig()
                vnic_config.ipRouteSpec.ipRouteConfig.defaultGateway = self.default_gateway
        vnic_config.ip = ip_spec

        results['mtu'] = self.mtu
        vnic_config.mtu = self.mtu

        results['tcpip_stack'] = self.tcpip_stack
        vnic_config.netStackInstanceKey = self.get_api_net_stack_instance(self.tcpip_stack)

        vmk_device = None
        try:
            if self.module.check_mode:
                results['msg'] = "VMkernel Adapter would be created"
            else:
                if self.vswitch_name:
                    vmk_device = self.esxi_host_obj.configManager.networkSystem.AddVirtualNic(
                        self.port_group_name,
                        vnic_config
                    )
                elif self.vds_name:
                    vnic_config.distributedVirtualPort = vim.dvs.PortConnection()
                    vnic_config.distributedVirtualPort.switchUuid = self.dv_switch_obj.uuid
                    vnic_config.distributedVirtualPort.portgroupKey = self.port_group_obj.key
                    vmk_device = self.esxi_host_obj.configManager.networkSystem.AddVirtualNic(portgroup="", nic=vnic_config)
                results['msg'] = "VMkernel Adapter created"
            results['changed'] = True
            results['device'] = vmk_device
            if self.network_type != 'dhcp':
                if self.default_gateway:
                    results['ipv4_gw'] = self.default_gateway
                else:
                    results['ipv4_gw'] = "No override"
            results['services'] = self.create_enabled_services_string()
        except vim.fault.AlreadyExists as already_exists:
            self.module.fail_json(
                msg="Failed to add vmk as portgroup already has a virtual network adapter %s" %
                to_native(already_exists.msg)
            )
        except vim.fault.HostConfigFault as host_config_fault:
            self.module.fail_json(
                msg="Failed to add vmk due to host config issues : %s" %
                to_native(host_config_fault.msg)
            )
        except vim.fault.InvalidState as invalid_state:
            self.module.fail_json(
                msg="Failed to add vmk as ipv6 address is specified in an ipv4 only system : %s" %
                to_native(invalid_state.msg)
            )
        except vmodl.fault.InvalidArgument as invalid_arg:
            self.module.fail_json(
                msg="Failed to add vmk as IP address or Subnet Mask in the IP configuration "
                "are invalid or PortGroup does not exist : %s" % to_native(invalid_arg.msg)
            )

        # do service type configuration
        if self.tcpip_stack == 'default' and not all(
                option is False for option in [self.enable_vsan, self.enable_vmotion,
                                               self.enable_mgmt, self.enable_ft,
                                               self.enable_provisioning, self.enable_replication,
                                               self.enable_replication_nfc]):
            self.vnic = self.get_vmkernel_by_device(device_name=vmk_device)

            # VSAN
            if self.enable_vsan:
                results['vsan'] = self.set_vsan_service_type()

            # Other service type
            host_vnic_manager = self.esxi_host_obj.configManager.virtualNicManager
            if self.enable_vmotion:
                self.set_service_type(host_vnic_manager, self.vnic, 'vmotion')

            if self.enable_mgmt:
                self.set_service_type(host_vnic_manager, self.vnic, 'management')

            if self.enable_ft:
                self.set_service_type(host_vnic_manager, self.vnic, 'faultToleranceLogging')

            if self.enable_provisioning:
                self.set_service_type(host_vnic_manager, self.vnic, 'vSphereProvisioning')

            if self.enable_replication:
                self.set_service_type(host_vnic_manager, self.vnic, 'vSphereReplication')

            if self.enable_replication_nfc:
                self.set_service_type(host_vnic_manager, self.vnic, 'vSphereReplicationNFC')

        self.module.exit_json(**results)

    def set_service_type(self, vnic_manager, vmk, service_type, operation='select'):
        """
        Set service type to given VMKernel
        Args:
            vnic_manager: Virtual NIC manager object
            vmk: VMkernel managed object
            service_type: Name of service type
            operation: Select to select service type, deselect to deselect service type

        """
        try:
            if operation == 'select':
                if not self.module.check_mode:
                    vnic_manager.SelectVnicForNicType(service_type, vmk.device)
            elif operation == 'deselect':
                if not self.module.check_mode:
                    vnic_manager.DeselectVnicForNicType(service_type, vmk.device)
        except vmodl.fault.InvalidArgument as invalid_arg:
            self.module.fail_json(
                msg="Failed to %s VMK service type '%s' on '%s' due to : %s" %
                (operation, service_type, vmk.device, to_native(invalid_arg.msg))
            )

    def get_all_vmks_by_service_type(self):
        """
        Return information about service types and VMKernel
        Returns: Dictionary of service type as key and VMKernel list as value

        """
        service_type_vmk = dict(
            vmotion=[],
            vsan=[],
            management=[],
            faultToleranceLogging=[],
            vSphereProvisioning=[],
            vSphereReplication=[],
            vSphereReplicationNFC=[],
        )

        for service_type in list(service_type_vmk):
            vmks_list = self.query_service_type_for_vmks(service_type)
            service_type_vmk[service_type] = vmks_list
        return service_type_vmk

    def query_service_type_for_vmks(self, service_type):
        """
        Return list of VMKernels
        Args:
            service_type: Name of service type

        Returns: List of VMKernel which belongs to that service type

        """
        vmks_list = []
        query = None
        try:
            query = self.esxi_host_obj.configManager.virtualNicManager.QueryNetConfig(service_type)
        except vim.fault.HostConfigFault as config_fault:
            self.module.fail_json(
                msg="Failed to get all VMKs for service type %s due to host config fault : %s" %
                (service_type, to_native(config_fault.msg))
            )
        except vmodl.fault.InvalidArgument as invalid_argument:
            self.module.fail_json(
                msg="Failed to get all VMKs for service type %s due to invalid arguments : %s" %
                (service_type, to_native(invalid_argument.msg))
            )

        if not query.selectedVnic:
            return vmks_list
        selected_vnics = [vnic for vnic in query.selectedVnic]
        vnics_with_service_type = [vnic.device for vnic in query.candidateVnic if vnic.key in selected_vnics]
        return vnics_with_service_type

    def create_enabled_services_string(self):
        """Create services list"""
        services = []
        if self.enable_mgmt:
            services.append('Mgmt')
        if self.enable_vmotion:
            services.append('vMotion')
        if self.enable_ft:
            services.append('FT')
        if self.enable_vsan:
            services.append('VSAN')
        if self.enable_provisioning:
            services.append('Prov')
        if self.enable_replication:
            services.append('Repl')
        if self.enable_replication_nfc:
            services.append('Repl_NFC')
        return ', '.join(services)

    @staticmethod
    def get_api_net_stack_instance(tcpip_stack):
        """Get TCP/IP stack instance name or key"""
        net_stack_instance = None
        if tcpip_stack == 'default':
            net_stack_instance = 'defaultTcpipStack'
        elif tcpip_stack == 'provisioning':
            net_stack_instance = 'vSphereProvisioning'
        # vmotion and vxlan stay the same
        elif tcpip_stack == 'vmotion':
            net_stack_instance = 'vmotion'
        elif tcpip_stack == 'vxlan':
            net_stack_instance = 'vxlan'
        elif tcpip_stack == 'defaultTcpipStack':
            net_stack_instance = 'default'
        elif tcpip_stack == 'vSphereProvisioning':
            net_stack_instance = 'provisioning'
        # vmotion and vxlan stay the same
        elif tcpip_stack == 'vmotion':
            net_stack_instance = 'vmotion'
        elif tcpip_stack == 'vxlan':
            net_stack_instance = 'vxlan'
        return net_stack_instance


def main():
    """Main"""
    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(
        esxi_hostname=dict(required=True, type='str'),
        portgroup_name=dict(required=True, type='str', aliases=['portgroup']),
        ip_address=dict(removed_in_version=2.9, type='str'),
        subnet_mask=dict(removed_in_version=2.9, type='str'),
        mtu=dict(required=False, type='int', default=1500),
        device=dict(type='str'),
        enable_vsan=dict(required=False, type='bool', default=False),
        enable_vmotion=dict(required=False, type='bool', default=False),
        enable_mgmt=dict(required=False, type='bool', default=False),
        enable_ft=dict(required=False, type='bool', default=False),
        enable_provisioning=dict(type='bool', default=False),
        enable_replication=dict(type='bool', default=False),
        enable_replication_nfc=dict(type='bool', default=False),
        vswitch_name=dict(required=False, type='str', aliases=['vswitch']),
        dvswitch_name=dict(required=False, type='str', aliases=['dvswitch']),
        network=dict(
            type='dict',
            options=dict(
                type=dict(type='str', default='static', choices=['static', 'dhcp']),
                ip_address=dict(type='str'),
                subnet_mask=dict(type='str'),
                default_gateway=dict(type='str'),
                tcpip_stack=dict(type='str', default='default', choices=['default', 'provisioning', 'vmotion', 'vxlan']),
            ),
            default=dict(
                type='static',
                tcpip_stack='default',
            ),
        ),
        state=dict(
            type='str',
            default='present',
            choices=['absent', 'present']
        ),
    ))

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=[
                               ['vswitch_name', 'dvswitch_name'],
                               ['tcpip_stack', 'enable_vsan'],
                               ['tcpip_stack', 'enable_vmotion'],
                               ['tcpip_stack', 'enable_mgmt'],
                               ['tcpip_stack', 'enable_ft'],
                               ['tcpip_stack', 'enable_provisioning'],
                               ['tcpip_stack', 'enable_replication'],
                               ['tcpip_stack', 'enable_replication_nfc'],
                           ],
                           required_one_of=[
                               ['vswitch_name', 'dvswitch_name'],
                               ['portgroup_name', 'device'],
                           ],
                           required_if=[
                               ['state', 'present', ['portgroup_name']],
                               ['state', 'absent', ['device']]
                           ],
                           supports_check_mode=True)

    pyv = PyVmomiHelper(module)
    pyv.ensure()


if __name__ == '__main__':
    main()
