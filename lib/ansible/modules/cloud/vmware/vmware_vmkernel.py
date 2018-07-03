#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Joseph Callen <jcallen () csc.com>
# Copyright: (c) 2017-18, Ansible Project
# Copyright: (c) 2017-18, Abhijeet Kasurde <akasurde@redhat.com>
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
short_description: Manage a VMware VMkernel Interface aka. Virtual NICs of host system.
description:
    - 'This module can be used to manage the VMWare VMKernel interface (also known as Virtual NICs) of host system.'
    - This module assumes that the host is already configured with Portgroup and vSwitch.
version_added: 2.0
author:
- Joseph Callen (@jcpowermac)
- Russell Teague (@mtnbikenc)
- Abhijeet Kasurde (@Akasurde) <akasurde@redhat.com>
notes:
    - Tested on vSphere 5.5, 6.5
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
    vswitch_name:
        description:
            - The name of the vSwitch where to add the VMKernel interface.
            - Required parameter only if C(state) is set to C(present).
            - Optional parameter from version 2.5 and onwards.
        required: False
    portgroup_name:
        description:
            - The name of the port group for the VMKernel interface.
        required: True
    network:
        description:
            - A dictionary of network details.
            - 'Following parameter is required:'
            - ' - C(type) (string): Type of IP assignment (either C(dhcp) or C(static)).'
            - 'Following parameters are required in case of C(type) is set to C(static)'
            - ' - C(ip_address) (string): Static IP address (implies C(type: static)).'
            - ' - C(subnet_mask) (string): Static netmask required for C(ip).'
        version_added: 2.5
    ip_address:
        description:
            - The IP Address for the VMKernel interface.
            - Use C(network) parameter with C(ip_address) instead.
            - Deprecated option, will be removed in version 2.9.
    subnet_mask:
        description:
            - The Subnet Mask for the VMKernel interface.
            - Use C(network) parameter with C(subnet_mask) instead.
            - Deprecated option, will be removed in version 2.9.
    vlan_id:
        description:
            - The VLAN ID for the VMKernel interface.
            - Required parameter only if C(state) is set to C(present).
            - Optional parameter from version 2.5 and onwards.
        required: False
        version_added: 2.0
    mtu:
        description:
            - The MTU for the VMKernel interface.
            - The default value of 1500 is valid from version 2.5 and onwards.
        required: False
        default: 1500
    enable_vsan:
        description:
            - Enable the VMKernel interface for VSAN traffic.
        required: False
        type: bool
    enable_vmotion:
        description:
            - Enable the VMKernel interface for vMotion traffic.
        required: False
        type: bool
    enable_mgmt:
        description:
            - Enable the VMKernel interface for Management traffic.
        required: False
        type: bool
    enable_ft:
        description:
            - Enable the VMKernel interface for Fault Tolerance traffic.
        required: False
        type: bool
    state:
        description:
            - If set to C(present), VMKernel is created with the given specifications.
            - If set to C(absent), VMKernel is removed from the given configurations.
            - If set to C(present) and VMKernel exists then VMKernel configurations are updated.
        required: False
        choices: [ present, absent ]
        default: present
        version_added: 2.5
    esxi_hostname:
        description:
            - Name of ESXi host to which VMKernel is to be managed.
            - "From version 2.5 onwards, this parameter is required."
        required: True
        version_added: 2.5
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
      state: present
      enable_mgmt: True

-  name: Add Management vmkernel port using DHCP network type
   vmware_vmkernel:
      hostname: 192.168.127.9
      username: admin
      password: supersecret123
      vswitch_name: vSwitch0
      portgroup_name: PG_0002
      vlan_id: vlan_id
      state: present
      network:
        type: 'dhcp'
      enable_mgmt: True

-  name: Delete VMkernel port using DHCP network type
   vmware_vmkernel:
      hostname: 192.168.127.9
      username: admin
      password: supersecret123
      vswitch_name: vSwitch0
      portgroup_name: PG_0002
      vlan_id: vlan_id
      state: absent

'''

RETURN = r'''
result:
    description: metadata about VMKernel name
    returned: always
    type: dict
    sample: { results : "vmk1" }
'''

try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec, wait_for_task
from ansible.module_utils._text import to_native


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

        self.esxi_host_name = self.params['esxi_hostname']

        hosts = self.get_all_host_objs(esxi_host_name=self.esxi_host_name)
        if hosts:
            self.esxi_host_obj = hosts[0]
        else:
            self.module.fail_json("Failed to get details of ESXi server."
                                  " Please specify esxi_hostname.")

        self.port_group_obj = self.get_port_group_by_name(host_system=self.esxi_host_obj, portgroup_name=self.port_group_name)
        if not self.port_group_obj:
            module.fail_json(msg="Portgroup name %s not found" % self.port_group_name)

        if self.network_type == 'static':
            if not self.ip_address:
                module.fail_json(msg="network.ip_address is required parameter when network is set to 'static'.")
            if not self.subnet_mask:
                module.fail_json(msg="network.subnet_mask is required parameter when network is set to 'static'.")

    def get_port_group_by_name(self, host_system, portgroup_name):
        """
        Function to get specific port group by given name
        Args:
            host_system: Name of Host System
            portgroup_name: Name of Port Group

        Returns: List of port groups by given specifications

        """
        pgs_list = self.get_all_port_groups_by_host(host_system=host_system)
        desired_pg = None
        for pg in pgs_list:
            if pg.spec.name == portgroup_name:
                return pg
        return desired_pg

    def ensure(self):
        """
        Function to manage internal VMKernel management
        Returns: NA

        """
        host_vmk_states = {
            'absent': {
                'update': self.host_vmk_delete,
                'present': self.host_vmk_delete,
                'absent': self.host_vmk_unchange,
            },
            'present': {
                'update': self.host_vmk_update,
                'present': self.host_vmk_unchange,
                'absent': self.host_vmk_create,
            }
        }

        try:
            host_vmk_states[self.module.params['state']][self.check_state()]()
        except vmodl.RuntimeFault as runtime_fault:
            self.module.fail_json(msg=to_native(runtime_fault.msg))
        except vmodl.MethodFault as method_fault:
            self.module.fail_json(msg=to_native(method_fault.msg))
        except Exception as e:
            self.module.fail_json(msg=to_native(e))

    def get_vmkernel(self, port_group_name=None):
        """
        Function to check if vmkernel
        Args:
            port_group_name: name of port group

        Returns: vmkernel managed object if vmkernel found, false if not

        """
        ret = False
        vnics = [vnic for vnic in self.esxi_host_obj.config.network.vnic if vnic.spec.portgroup == port_group_name]
        if vnics:
            ret = vnics[0]
        return ret

    def check_state(self):
        """
        Function to check internal state management
        Returns: Present if found, absent if not, update if change in fields

        """
        state = 'absent'
        self.vnic = self.get_vmkernel(port_group_name=self.port_group_name)
        if self.vnic:
            state = 'present'
            if self.vnic.spec.mtu != self.mtu:
                state = 'update'
            if self.vnic.spec.ip.dhcp:
                if self.network_type == 'static':
                    state = 'update'

            if not self.vnic.spec.ip.dhcp:
                if self.network_type == 'dhcp':
                    state = 'update'
                elif self.network_type == 'static':
                    if (self.ip_address != self.vnic.spec.ip.ipAddress) or \
                            (self.subnet_mask != self.vnic.spec.ip.subnetMask):
                        state = 'update'
            # Add for vsan, vmotion and management
            service_type_vmks = self.get_all_vmks_by_service_type()
            if (self.enable_vmotion and self.vnic.device not in service_type_vmks['vmotion']) or \
                    (not self.enable_vmotion and self.vnic.device in service_type_vmks['vmotion']):
                state = 'update'

            if (self.enable_mgmt and self.vnic.device not in service_type_vmks['management']) or \
                    (not self.enable_mgmt and self.vnic.device in service_type_vmks['management']):
                state = 'update'

            if (self.enable_ft and self.vnic.device not in service_type_vmks['faultToleranceLogging']) or \
                    (not self.enable_ft and self.vnic.device in service_type_vmks['faultToleranceLogging']):
                state = 'update'

            if (self.enable_vsan and self.vnic.device not in service_type_vmks['vsan']) or \
                    (not self.enable_vsan and self.vnic.device in service_type_vmks['vsan']):
                state = 'update'
        return state

    def host_vmk_delete(self):
        """
        Function to delete VMKernel
        Returns: NA

        """
        results = dict(changed=False, result='')
        vmk_device = self.vnic.device
        try:
            self.esxi_host_obj.configManager.networkSystem.RemoveVirtualNic(vmk_device)
            results['result'] = vmk_device
            results['changed'] = True
        except vim.fault.NotFound as not_found:
            self.module.fail_json(msg="Failed to find vmk to delete "
                                      "due to %s" % to_native(not_found.msg))
        except vim.fault.HostConfigFault as host_config_fault:
            self.module.fail_json(msg="Failed to delete vmk due host "
                                      "config issues : %s" % to_native(host_config_fault.msg))
        except Exception as e:
            self.module.fail_json(msg="Failed to delete vmk due to general "
                                      "exception : %s" % to_native(e))

        self.module.exit_json(**results)

    def host_vmk_unchange(self):
        """
        Function to denote no change in VMKernel
        Returns: NA

        """
        self.module.exit_json(changed=False)

    def host_vmk_update(self):
        """
        Function to update VMKernel with given parameters
        Returns: NA

        """
        results = dict(changed=False, result='')
        vnic_config = vim.host.VirtualNic.Specification()
        ip_spec = vim.host.IpConfig()
        if self.network_type == 'dhcp':
            ip_spec.dhcp = True
        else:
            ip_spec.dhcp = False
            ip_spec.ipAddress = self.ip_address
            ip_spec.subnetMask = self.subnet_mask

        vnic_config.ip = ip_spec
        vnic_config.mtu = self.mtu

        try:
            self.esxi_host_obj.configManager.networkSystem.UpdateVirtualNic(self.vnic.device, vnic_config)
            results['changed'] = True
            results['result'] = self.vnic.device
        except vim.fault.NotFound as not_found:
            self.module.fail_json(msg="Failed to update vmk as virtual network adapter"
                                      " cannot be found %s" % to_native(not_found.msg))
        except vim.fault.HostConfigFault as host_config_fault:
            self.module.fail_json(msg="Failed to update vmk due to host config "
                                      "issues : %s" % to_native(host_config_fault.msg))
        except vim.fault.InvalidState as invalid_state:
            self.module.fail_json(msg="Failed to update vmk as ipv6 address is specified in an "
                                      "ipv4 only system : %s" % to_native(invalid_state.msg))
        except vmodl.fault.InvalidArgument as invalid_arg:
            self.module.fail_json(msg="Failed to update vmk as IP address or Subnet Mask in the IP "
                                      "configuration are invalid or PortGroup "
                                      "does not exist : %s" % to_native(invalid_arg.msg))
        except Exception as e:
            self.module.fail_json(msg="Failed to add vmk due to general "
                                      "exception : %s" % to_native(e))

        # Query All service type for VMKernel
        service_type_vmk = self.get_all_vmks_by_service_type()

        vnic_manager = self.esxi_host_obj.configManager.virtualNicManager

        if self.enable_vmotion and self.vnic.device not in service_type_vmk['vmotion']:
            results['changed'] = self.set_service_type(vnic_manager=vnic_manager, vmk=self.vnic, service_type='vmotion')
        elif not self.enable_vmotion and self.vnic.device in service_type_vmk['vmotion']:
            results['changed'] = self.set_service_type(vnic_manager=vnic_manager, vmk=self.vnic, service_type='vmotion', operation='deselect')

        if self.enable_mgmt and self.vnic.device not in service_type_vmk['management']:
            results['changed'] = self.set_service_type(vnic_manager=vnic_manager, vmk=self.vnic, service_type='management')
        elif not self.enable_mgmt and self.vnic.device in service_type_vmk['management']:
            results['changed'] = self.set_service_type(vnic_manager=vnic_manager, vmk=self.vnic, service_type='management', operation='deselect')

        if self.enable_ft and self.vnic.device not in service_type_vmk['faultToleranceLogging']:
            results['changed'] = self.set_service_type(vnic_manager=vnic_manager, vmk=self.vnic, service_type='faultToleranceLogging')
        elif not self.enable_ft and self.vnic.device in service_type_vmk['faultToleranceLogging']:
            results['changed'] = self.set_service_type(vnic_manager=vnic_manager, vmk=self.vnic, service_type='faultToleranceLogging', operation='deselect')

        if self.enable_vsan and self.vnic.device not in service_type_vmk['vsan']:
            results['changed'], results['result'] = self.set_vsan_service_type()
        elif not self.enable_vsan and self.vnic.device in service_type_vmk['vsan']:
            results['changed'] = self.set_service_type(vnic_manager=vnic_manager, vmk=self.vnic, service_type='vsan', operation='deselect')

        results['result'] = self.vnic.device
        self.module.exit_json(**results)

    def set_vsan_service_type(self):
        """
        Function to set VSAN service type
        Returns: True and result for success, False and result for failure

        """
        changed, result = (False, '')
        vsan_system = self.esxi_host_obj.configManager.vsanSystem

        vsan_port_config = vim.vsan.host.ConfigInfo.NetworkInfo.PortConfig()
        vsan_port_config.device = self.vnic.device

        vsan_config = vim.vsan.host.ConfigInfo()
        vsan_config.networkInfo = vim.vsan.host.ConfigInfo.NetworkInfo()
        vsan_config.networkInfo.port = [vsan_port_config]
        try:
            vsan_task = vsan_system.UpdateVsan_Task(vsan_config)
            changed, result = wait_for_task(vsan_task)
        except Exception as e:
            self.module.fail_json(msg="Failed to set service type to vsan for"
                                      " %s : %s" % (self.vnic.device, to_native(e)))
        return changed, result

    def host_vmk_create(self):
        """
        Function to create VMKernel
        Returns: NA

        """
        results = dict(changed=False, result='')
        vnic_config = vim.host.VirtualNic.Specification()
        ip_spec = vim.host.IpConfig()
        if self.network_type == 'dhcp':
            ip_spec.dhcp = True
        else:
            ip_spec.dhcp = False
            ip_spec.ipAddress = self.ip_address
            ip_spec.subnetMask = self.subnet_mask

        vnic_config.ip = ip_spec
        vnic_config.mtu = self.mtu
        vmk_device = None
        try:
            vmk_device = self.esxi_host_obj.configManager.networkSystem.AddVirtualNic(self.port_group_name, vnic_config)
            results['changed'] = True
            results['result'] = vmk_device
            self.vnic = self.get_vmkernel(port_group_name=self.port_group_name)
        except vim.fault.AlreadyExists as already_exists:
            self.module.fail_json(msg="Failed to add vmk as portgroup already has a "
                                      "virtual network adapter %s" % to_native(already_exists.msg))
        except vim.fault.HostConfigFault as host_config_fault:
            self.module.fail_json(msg="Failed to add vmk due to host config "
                                      "issues : %s" % to_native(host_config_fault.msg))
        except vim.fault.InvalidState as invalid_state:
            self.module.fail_json(msg="Failed to add vmk as ipv6 address is specified in an "
                                      "ipv4 only system : %s" % to_native(invalid_state.msg))
        except vmodl.fault.InvalidArgument as invalid_arg:
            self.module.fail_json(msg="Failed to add vmk as IP address or Subnet Mask in the IP "
                                      "configuration are invalid or PortGroup "
                                      "does not exist : %s" % to_native(invalid_arg.msg))
        except Exception as e:
            self.module.fail_json(msg="Failed to add vmk due to general "
                                      "exception : %s" % to_native(e))

        # VSAN
        if self.enable_vsan:
            results['changed'], results['result'] = self.set_vsan_service_type()

        # Other service type
        host_vnic_manager = self.esxi_host_obj.configManager.virtualNicManager
        if self.enable_vmotion:
            results['changed'] = self.set_service_type(host_vnic_manager, self.vnic, 'vmotion')

        if self.enable_mgmt:
            results['changed'] = self.set_service_type(host_vnic_manager, self.vnic, 'management')

        if self.enable_ft:
            results['changed'] = self.set_service_type(host_vnic_manager, self.vnic, 'faultToleranceLogging')

        self.module.exit_json(**results)

    def set_service_type(self, vnic_manager, vmk, service_type, operation='select'):
        """
        Function to set service type to given VMKernel
        Args:
            vnic_manager: Virtual NIC manager object
            vmk: VMkernel managed object
            service_type: Name of service type
            operation: Select to select service type, deselect to deselect service type

        Returns: True if set, false if not

        """
        ret = False
        try:
            if operation == 'select':
                vnic_manager.SelectVnicForNicType(service_type, vmk.device)
            elif operation == 'deselect':
                vnic_manager.DeselectVnicForNicType(service_type, vmk.device)
            ret = True
        except vmodl.fault.InvalidArgument as invalid_arg:
            self.module.fail_json(msg="Failed to %s VMK service type %s to %s due"
                                      " to %s" % (operation, service_type, vmk.device, to_native(invalid_arg.msg)))
        except Exception as e:
            self.module.fail_json(msg="Failed to %s VMK service type %s to %s due"
                                      " generic exception : %s" % (operation, service_type, vmk.device, to_native(e)))

        return ret

    def get_all_vmks_by_service_type(self):
        """
        Function to return information about service types and VMKernel
        Returns: Dictionary of service type as key and VMKernel list as value

        """
        service_type_vmk = dict(vmotion=[], vsan=[], management=[], faultToleranceLogging=[])
        for service_type in service_type_vmk.keys():
            vmks_list = self.query_service_type_for_vmks(service_type)
            service_type_vmk[service_type] = vmks_list
        return service_type_vmk

    def query_service_type_for_vmks(self, service_type):
        """
        Function to return list of VMKernels
        Args:
            service_type: Name of service type

        Returns: List of VMKernel which belongs to that service type

        """
        vmks_list = []
        query = None
        try:
            query = self.esxi_host_obj.configManager.virtualNicManager.QueryNetConfig(service_type)
        except vim.fault.HostConfigFault as config_fault:
            self.module.fail_json(msg="Failed to get all VMKs for service type %s due to"
                                      " host config fault : %s" % (service_type, to_native(config_fault.msg)))
        except vmodl.fault.InvalidArgument as invalid_argument:
            self.module.fail_json(msg="Failed to get all VMKs for service type %s due to"
                                      " invalid arguments : %s" % (service_type, to_native(invalid_argument.msg)))
        except Exception as e:
            self.module.fail_json(msg="Failed to get all VMKs for service type %s due to"
                                      "%s" % (service_type, to_native(e)))

        if not query.selectedVnic:
            return vmks_list
        selected_vnics = [vnic for vnic in query.selectedVnic]
        vnics_with_service_type = [vnic.device for vnic in query.candidateVnic if vnic.key in selected_vnics]
        return vnics_with_service_type


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(
        esxi_hostname=dict(required=True, type='str'),
        portgroup_name=dict(required=True, type='str'),
        ip_address=dict(removed_in_version=2.9, type='str'),
        subnet_mask=dict(removed_in_version=2.9, type='str'),
        mtu=dict(required=False, type='int', default=1500),
        enable_vsan=dict(required=False, type='bool'),
        enable_vmotion=dict(required=False, type='bool'),
        enable_mgmt=dict(required=False, type='bool'),
        enable_ft=dict(required=False, type='bool'),
        vswitch_name=dict(required=False, type='str'),
        vlan_id=dict(required=False, type='int'),
        state=dict(type='str',
                   choices=['present', 'absent'],
                   default='present'),
        network=dict(
            required=True,
            type='dict',
            options=dict(
                type=dict(type='str', choices=['static', 'dhcp']),
                ip_address=dict(type='str'),
                subnet_mask=dict(type='str'),
            ),
        ),
    )
    )

    required_if = [
        ['state', 'present', ['vswitch_name', 'vlan_id']],
    ]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_if=required_if,
                           supports_check_mode=False)

    pyv = PyVmomiHelper(module)
    pyv.ensure()


if __name__ == '__main__':
    main()
