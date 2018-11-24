#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Christian Kotte <christian.kotte@gmx.de>
#
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
module: vmware_host_tcpip_stacks
short_description: Manage TCP/IP stack configuration of an ESXI host system
description:
- This module can be used to configure system TCP/IP stacks on an ESXi host system.
- The DNS configuration of the default TCP/IP stack needs to be done with the M(vmware_host_dns) module.
version_added: 2.8
author:
- Christian Kotte (@ckotte)
notes:
- Tested on vSphere 6.5
- You cannot remove the default gateway from the (vMotion) TCP/IP stack if you have a VMkernel adapter configured for this TCP/IP stack
- Custom TCP/IP stack creation isn't possible yet
requirements:
- python >= 2.6
- PyVmomi
options:
  default:
    description:
    - Default TCP/IP stack configuration.
    - 'The following parameters can be used:'
    - ' - C(vmkernel_gateway) (string): The default gateway address used by this instance. The current address will be used if not specified.'
    - ' - C(congestion_algorithm) (string): The TCP congestion control algorithm used by this instance. (default: newreno).'
    - '   - choices: [newreno, cubic]'
    - ' - C(num_connections) (int): The maximum number of socket connections that are requested on this instance. (default: 11000).'
    type: dict
  provisioning:
    description:
    - Provisioning TCP/IP stack configuration.
    - 'The following parameters can be used:'
    - ' - C(vmkernel_gateway) (string): The default gateway address used by this instance.'
    - ' - C(congestion_algorithm) (string): The TCP congestion control algorithm used by this instance. (default: newreno).'
    - '   - choices: [newreno, cubic]'
    - ' - C(num_connections) (int): The maximum number of socket connections that are requested on this instance. (default: 11000).'
    type: dict
  vmotion:
    description:
    - vMotion TCP/IP stack configuration.
    - 'The following parameters can be used:'
    - ' - C(vmkernel_gateway) (string): The default gateway address used by this instance.'
    - ' - C(congestion_algorithm) (string): The TCP congestion control algorithm used by this instance. (default: newreno).'
    - '   - choices: [newreno, cubic]'
    - ' - C(num_connections) (int): The maximum number of socket connections that are requested on this instance. (default: 11000).'
    type: dict
  vxlan:
    description:
    - VXLAN TCP/IP stack configuration.
    - 'The following parameters can be used:'
    - ' - C(vmkernel_gateway) (string): The default gateway address used by this instance.'
    - ' - C(congestion_algorithm) (string): The TCP congestion control algorithm used by this instance. (default: newreno).'
    - '   - choices: [newreno, cubic]'
    - ' - C(num_connections) (int): The maximum number of socket connections that are requested on this instance. (default: 11000).'
    type: dict
  esxi_hostname:
    description:
    - Name of the host system to work with.
    - This parameter is required if C(cluster_name) is not specified.
    type: str
  cluster_name:
    description:
    - Name of the cluster from which all host systems will be used.
    - This parameter is required if C(esxi_hostname) is not specified.
    type: str
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Configure vMotion TCP/IP stack gateway
  vmware_host_tcpip_stacks:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname: '{{ esxi_hostname }}'
    vmotion:
      vmkernel_gateway: 192.168.2.1
  delegate_to: localhost

- name: Configure vMotion TCP/IP stack
  vmware_host_tcpip_stacks:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname: '{{ esxi_hostname }}'
    vmotion:
      vmkernel_gateway: 192.168.2.1
      congestion_algorithm: newreno
      num_connections: 11000
  delegate_to: localhost

- name: Configure all TCP/IP stacks
  vmware_host_tcpip_stacks:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname: '{{ esxi_hostname }}'
    default:
      vmkernel_gateway: 192.168.1.1
      congestion_algorithm: newreno
      num_connections: 11000
    provisioning:
      congestion_algorithm: newreno
      num_connections: 11000
    vmotion:
      vmkernel_gateway: 192.168.2.1
      congestion_algorithm: newreno
      num_connections: 11000
    vxlan:
      congestion_algorithm: newreno
      num_connections: 11000
  delegate_to: localhost
'''

RETURN = r'''
result:
  description: metadata about host TCP/IP stack configuration
  returned: always
  type: dict
  sample: {
    "esx01.example.local": {
      "changed": false,
      "default_congestion_algorithm": "newreno",
      "default_num_connections": 11000,
      "default_vmkernel_gateway": "192.168.1.1",
      "msg": "All settings are already configured",
      "prov_congestion_algorithm": "newreno",
      "prov_vmkernel_gateway": null,
      "prov_vmkernel_num_connections": 11000,
      "vxlan_congestion_algorithm": "newreno",
      "vxlan_vmkernel_gateway": null,
      "vxlan_vmkernel_num_connections": 11000,
    },
  }
'''

try:
    from pyVmomi import vim, vmodl
    import ipaddress
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec
from ansible.module_utils._text import to_native
from ansible.module_utils.six import text_type


class VmwareHostTcpIpStacks(PyVmomi):
    """Class to manage TCP/IP stack configuration of an ESXi host system"""

    def __init__(self, module):
        super(VmwareHostTcpIpStacks, self).__init__(module)
        cluster_name = self.params.get('cluster_name')
        esxi_host_name = self.params.get('esxi_hostname')
        self.hosts = self.get_all_host_objs(cluster_name=cluster_name, esxi_host_name=esxi_host_name)
        if not self.hosts:
            self.module.fail_json(msg="Failed to find host system.")

    def ensure(self):
        """Function to manage TCP/IP stack configuration of an ESXi host system"""
        results = dict(changed=False, result=dict())
        if self.params['default']:
            default_vmkernel_gateway = self.params['default'].get('vmkernel_gateway')
            default_congestion_algorithm = self.params['default'].get('congestion_algorithm')
            default_num_connections = self.params['default'].get('num_connections')
        if self.params['provisioning']:
            prov_vmkernel_gateway = self.params['provisioning'].get('vmkernel_gateway')
            prov_congestion_algorithm = self.params['provisioning'].get('congestion_algorithm')
            prov_vmkernel_num_connections = self.params['provisioning'].get('num_connections')
        if self.params['vmotion']:
            vmotion_vmkernel_gateway = self.params['vmotion'].get('vmkernel_gateway')
            vmotion_congestion_algorithm = self.params['vmotion'].get('congestion_algorithm')
            vmotion_num_connections = self.params['vmotion'].get('num_connections')
        if self.params['vxlan']:
            vxlan_vmkernel_gateway = self.params['vxlan'].get('vmkernel_gateway')
            vxlan_congestion_algorithm = self.params['vxlan'].get('congestion_algorithm')
            vxlan_num_connections = self.params['vxlan'].get('num_connections')
        host_change_list = []
        for host in self.hosts:
            changed = False
            changed_list = []
            results['result'][host.name] = dict(changed='', msg='')

            host_netstack_config = host.config.network.netStackInstance

            changed_instances_list = []
            for instance in host_netstack_config:
                netstack_spec = vim.host.NetworkConfig.NetStackSpec()
                netstack_spec.netStackInstance = vim.host.NetStackInstance()
                changed_instance = False
                # Check default TCP/IP stack
                if instance.key == 'defaultTcpipStack':
                    results['result'][host.name]['default_vmkernel_gateway'] = default_vmkernel_gateway
                    results['result'][host.name]['default_num_connections'] = default_num_connections
                    results['result'][host.name]['default_congestion_algorithm'] = default_congestion_algorithm
                    (netstack_spec,
                     changed_instance,
                     vmkernel_gateway_previous,
                     num_connections_previous,
                     congestion_algorithm_previous) = self.create_netstack_spec(
                         instance,
                         'defaultTcpipStack',
                         default_vmkernel_gateway,
                         default_num_connections,
                         default_congestion_algorithm)
                    if changed_instance:
                        changed = True
                        changed_list.append("default TCP/IP stack")
                        # vmkernel_gateway_previous can be Null
                        if default_vmkernel_gateway:
                            results['result'][host.name]['default_vmkernel_gateway_previous'] = vmkernel_gateway_previous
                        if num_connections_previous:
                            results['result'][host.name]['default_num_connections_previous'] = num_connections_previous
                        if congestion_algorithm_previous:
                            results['result'][host.name]['default_congestion_algorithm_previous'] = \
                                congestion_algorithm_previous
                        changed_instances_list.append(netstack_spec)
                # Check Provisioning TCP/IP stack
                if instance.key == 'vSphereProvisioning':
                    results['result'][host.name]['prov_vmkernel_gateway'] = prov_vmkernel_gateway
                    results['result'][host.name]['prov_vmkernel_num_connections'] = prov_vmkernel_num_connections
                    results['result'][host.name]['prov_congestion_algorithm'] = prov_congestion_algorithm
                    (netstack_spec,
                     changed_instance,
                     vmkernel_gateway_previous,
                     num_connections_previous,
                     congestion_algorithm_previous) = self.create_netstack_spec(
                         instance,
                         'vSphereProvisioning',
                         prov_vmkernel_gateway,
                         prov_vmkernel_num_connections,
                         prov_congestion_algorithm)
                    if changed_instance:
                        changed = True
                        changed_list.append("provisioning TCP/IP stack")
                        # vmkernel_gateway_previous can be Null
                        if prov_vmkernel_gateway:
                            results['result'][host.name]['prov_vmkernel_gateway_previous'] = vmkernel_gateway_previous
                        if num_connections_previous:
                            results['result'][host.name]['prov_vmkernel_num_connections_previous'] = num_connections_previous
                        if congestion_algorithm_previous:
                            results['result'][host.name]['prov_congestion_algorithm_previous'] = \
                                congestion_algorithm_previous
                        changed_instances_list.append(netstack_spec)
                # Check vMotion TCP/IP stack
                if instance.key == 'vmotion':
                    results['result'][host.name]['vmotion_vmkernel_gateway'] = vmotion_vmkernel_gateway
                    results['result'][host.name]['vmotion_vmkernel_num_connections'] = vmotion_num_connections
                    results['result'][host.name]['vmotion_congestion_algorithm'] = vmotion_congestion_algorithm
                    (netstack_spec,
                     changed_instance,
                     vmkernel_gateway_previous,
                     num_connections_previous,
                     congestion_algorithm_previous) = self.create_netstack_spec(
                         instance,
                         'vmotion',
                         vmotion_vmkernel_gateway,
                         vmotion_num_connections,
                         vmotion_congestion_algorithm)
                    if changed_instance:
                        changed = True
                        changed_list.append("vMotion TCP/IP stack")
                        # vmkernel_gateway_previous can be Null
                        if vmkernel_gateway_previous:
                            results['result'][host.name]['vmotion_vmkernel_gateway_previous'] = vmkernel_gateway_previous
                        if num_connections_previous:
                            results['result'][host.name]['vmotion_num_connections_previous'] = num_connections_previous
                        if congestion_algorithm_previous:
                            results['result'][host.name]['vmotion_congestion_algorithm_previous'] = \
                                congestion_algorithm_previous
                        changed_instances_list.append(netstack_spec)
                # Check VXLAN TCP/IP stack
                if instance.key == 'vxlan':
                    results['result'][host.name]['vxlan_vmkernel_gateway'] = vxlan_vmkernel_gateway
                    results['result'][host.name]['vxlan_vmkernel_num_connections'] = vxlan_num_connections
                    results['result'][host.name]['vxlan_congestion_algorithm'] = vxlan_congestion_algorithm
                    (netstack_spec,
                     changed_instance,
                     vmkernel_gateway_previous,
                     num_connections_previous,
                     congestion_algorithm_previous) = self.create_netstack_spec(
                         instance,
                         'vxlan',
                         vxlan_vmkernel_gateway,
                         vxlan_num_connections,
                         vxlan_congestion_algorithm)
                    if changed_instance:
                        changed = True
                        changed_list.append("VXLAN TCP/IP stack")
                        # vmkernel_gateway_previous can be Null
                        if vxlan_vmkernel_gateway:
                            results['result'][host.name]['vxlan_vmkernel_gateway_previous'] = vmkernel_gateway_previous
                        if num_connections_previous:
                            results['result'][host.name]['vxlan_num_connections_previous'] = num_connections_previous
                        if congestion_algorithm_previous:
                            results['result'][host.name]['vxlan_congestion_algorithm_previous'] = \
                                congestion_algorithm_previous
                        changed_instances_list.append(netstack_spec)

            if changed:
                config = vim.host.NetworkConfig()
                config.netStackSpec = changed_instances_list
                if self.module.check_mode:
                    changed_suffix = ' would be changed'
                else:
                    changed_suffix = ' changed'
                if len(changed_list) > 2:
                    message = ', '.join(changed_list[:-1]) + ', and ' + str(changed_list[-1])
                elif len(changed_list) == 2:
                    message = ' and '.join(changed_list)
                elif len(changed_list) == 1:
                    message = changed_list[0]
                message += changed_suffix
                results['result'][host.name]['changed'] = True
                host_network_system = host.configManager.networkSystem
                if not self.module.check_mode:
                    try:
                        host_network_system.UpdateNetworkConfig(config, 'modify')
                    except vim.fault.AlreadyExists:
                        self.module.fail_json(
                            msg="Network entity specified in the configuration already exist on host '%s'" % host.name
                        )
                    except vim.fault.NotFound:
                        self.module.fail_json(
                            msg="Network entity specified in the configuration doesn't exist on host '%s'" % host.name
                        )
                    except vim.fault.ResourceInUse:
                        self.module.fail_json(msg="Resource is in use on host '%s'" % host.name)
                    except vmodl.fault.InvalidArgument:
                        self.module.fail_json(
                            msg="An invalid parameter is passed in for one of the networking objects for host '%s'" %
                            host.name
                        )
                    except vmodl.fault.NotSupported as not_supported:
                        self.module.fail_json(
                            msg="Operation isn't supported for the instance on '%s' : %s" %
                            (host.name, to_native(not_supported.msg))
                        )
                    except vim.fault.HostConfigFault as config_fault:
                        self.module.fail_json(
                            msg="Failed to configure TCP/IP stacks for host '%s' due to : %s" %
                            (host.name, to_native(config_fault.msg))
                        )
            else:
                results['result'][host.name]['changed'] = False
                message = 'All settings are already configured'
            results['result'][host.name]['msg'] = message

            host_change_list.append(changed)

        if any(host_change_list):
            results['changed'] = True
        self.module.exit_json(**results)

    def create_netstack_spec(self, instance, key, vmkernel_gateway, num_connections, congestion_algorithm):
        """Create TCP/IP stack spec"""
        changed = False
        vmkernel_gateway_previous = num_connections_previous = congestion_algorithm_previous = None
        netstack_spec = vim.host.NetworkConfig.NetStackSpec()
        netstack_spec.operation = 'edit'
        netstack_spec.netStackInstance = vim.host.NetStackInstance()
        netstack_spec.netStackInstance.key = key
        # The display name is only customizable with custom stacks
        netstack_spec.netStackInstance.name = key
        # DNS configuration is only supported for the default TCP/IP stack or custom stacks
        # netstack_spec.netStackInstance.dnsConfig = vim.host.DnsConfig()
        ip_address = None
        if vmkernel_gateway:
            try:
                # string need to be unicode; otherwise, the command will fail
                ip_address = ipaddress.ip_address(text_type(vmkernel_gateway))
            except ipaddress.AddressValueError:
                self.module.fail_json(msg="%s is not a valid IP address!" % vmkernel_gateway)
        # Don't change VMkernel gateway if not specified for default TCP/IP stack since it can make the ESXi host unreachable
        if not (key == 'defaultTcpipStack' and vmkernel_gateway is None) and (
                instance.ipRouteConfig.defaultGateway != vmkernel_gateway):
            changed = True
            vmkernel_gateway_previous = instance.ipRouteConfig.defaultGateway
            netstack_spec.netStackInstance.ipRouteConfig = vim.host.IpRouteConfig()
            if ip_address and ip_address.version == 6:
                netstack_spec.netStackInstance.ipRouteConfig.ipV6GatewayDevice = vmkernel_gateway
                # netstack_spec.netStackInstance.key.ipRouteConfig.ipV6GatewayDevice
            else:
                netstack_spec.netStackInstance.ipRouteConfig.defaultGateway = vmkernel_gateway
                # netstack_spec.netStackInstance.key.ipRouteConfig.gatewayDevice
        if instance.requestedMaxNumberOfConnections != num_connections:
            changed = True
            num_connections_previous = instance.requestedMaxNumberOfConnections
            netstack_spec.netStackInstance.requestedMaxNumberOfConnections = num_connections
        if instance.congestionControlAlgorithm != congestion_algorithm:
            changed = True
            congestion_algorithm_previous = instance.congestionControlAlgorithm
            netstack_spec.netStackInstance.congestionControlAlgorithm = congestion_algorithm
        # Routes can only be defined for custom stacks
        # netstack_spec.netStackInstance.routeTableConfig = vim.host.IpRouteTableConfig()
        return netstack_spec, changed, \
            vmkernel_gateway_previous, num_connections_previous, congestion_algorithm_previous


def main():
    """Main"""
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        esxi_hostname=dict(required=False, type='str'),
        cluster_name=dict(required=False, type='str'),
        default=dict(
            type='dict',
            options=dict(
                vmkernel_gateway=dict(type='str'),
                congestion_algorithm=dict(type='str', default='newreno', choices=['newreno', 'cubic']),
                num_connections=dict(type='int', default=11000),
            ),
        ),
        provisioning=dict(
            type='dict',
            options=dict(
                vmkernel_gateway=dict(type='str'),
                congestion_algorithm=dict(type='str', default='newreno', choices=['newreno', 'cubic']),
                num_connections=dict(type='int', default=11000),
            ),
        ),
        vmotion=dict(
            type='dict',
            options=dict(
                vmkernel_gateway=dict(type='str'),
                congestion_algorithm=dict(type='str', default='newreno', choices=['newreno', 'cubic']),
                num_connections=dict(type='int', default=11000),
            ),
        ),
        vxlan=dict(
            type='dict',
            options=dict(
                vmkernel_gateway=dict(type='str'),
                congestion_algorithm=dict(type='str', default='newreno', choices=['newreno', 'cubic']),
                num_connections=dict(type='int', default=11000),
            ),
        ),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[
            ['cluster_name', 'esxi_hostname'],
        ],
        mutually_exclusive=[
            ['cluster_name', 'host_name'],
        ],
        supports_check_mode=True
    )

    dns = VmwareHostTcpIpStacks(module)
    dns.ensure()


if __name__ == '__main__':
    main()
