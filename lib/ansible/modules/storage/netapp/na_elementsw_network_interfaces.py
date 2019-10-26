#!/usr/bin/python
# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

'''
Element Software Node Network Interfaces - Bond 1G and 10G configuration
'''
from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''

module: na_elementsw_network_interfaces

short_description: NetApp Element Software Configure Node Network Interfaces
extends_documentation_fragment:
    - netapp.solidfire
version_added: '2.7'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
- Configure Element SW Node Network Interfaces for Bond 1G and 10G IP address.

options:
    method:
        description:
        - Type of Method used to configure the interface.
        - method depends on other settings such as the use of a static IP address, which will change the method to static.
        - loopback - Used to define the IPv4 loopback interface.
        - manual - Used to define interfaces for which no configuration is done by default.
        - dhcp - May be used to obtain an IP address via DHCP.
        - static - Used to define Ethernet interfaces with statically allocated IPv4 addresses.
        choices: ['loopback', 'manual', 'dhcp', 'static']
        required: true

    ip_address_1g:
        description:
        - IP address for the 1G network.
        required: true

    ip_address_10g:
        description:
        - IP address for the 10G network.
        required: true

    subnet_1g:
        description:
        - 1GbE Subnet Mask.
        required: true

    subnet_10g:
        description:
        - 10GbE Subnet Mask.
        required: true

    gateway_address_1g:
        description:
        - Router network address to send packets out of the local network.
        required: true

    gateway_address_10g:
        description:
        - Router network address to send packets out of the local network.
        required: true

    mtu_1g:
        description:
        - Maximum Transmission Unit for 1GbE, Largest packet size that a network protocol can transmit.
        - Must be greater than or equal to 1500 bytes.
        default: '1500'

    mtu_10g:
        description:
        - Maximum Transmission Unit for 10GbE, Largest packet size that a network protocol can transmit.
        - Must be greater than or equal to 1500 bytes.
        default: '1500'

    dns_nameservers:
        description:
        - List of addresses for domain name servers.

    dns_search_domains:
        description:
        - List of DNS search domains.

    bond_mode_1g:
        description:
        - Bond mode for 1GbE configuration.
        choices: ['ActivePassive', 'ALB', 'LACP']
        default: 'ActivePassive'

    bond_mode_10g:
        description:
        - Bond mode for 10GbE configuration.
        choices: ['ActivePassive', 'ALB', 'LACP']
        default: 'ActivePassive'

    lacp_1g:
        description:
        - Link Aggregation Control Protocol useful only if LACP is selected as the Bond Mode.
        - Slow - Packets are transmitted at 30 second intervals.
        - Fast - Packets are transmitted in 1 second intervals.
        choices: ['Fast', 'Slow']
        default: 'Slow'

    lacp_10g:
        description:
        - Link Aggregation Control Protocol useful only if LACP is selected as the Bond Mode.
        - Slow - Packets are transmitted at 30 second intervals.
        - Fast - Packets are transmitted in 1 second intervals.
        choices: ['Fast', 'Slow']
        default: 'Slow'

    virtual_network_tag:
        description:
        - This is the primary network tag. All nodes in a cluster have the same VLAN tag.

'''

EXAMPLES = """

  - name: Set Node network interfaces configuration for Bond 1G and 10G properties
    tags:
    - elementsw_network_interfaces
    na_elementsw_network_interfaces:
      hostname: "{{ elementsw_hostname }}"
      username: "{{ elementsw_username }}"
      password: "{{ elementsw_password }}"
      method: static
      ip_address_1g: 10.226.109.68
      ip_address_10g: 10.226.201.72
      subnet_1g: 255.255.255.0
      subnet_10g: 255.255.255.0
      gateway_address_1g: 10.193.139.1
      gateway_address_10g: 10.193.140.1
      mtu_1g: 1500
      mtu_10g: 9000
      bond_mode_1g: ActivePassive
      bond_mode_10g: LACP
      lacp_10g: Fast
"""

RETURN = """

msg:
    description: Success message
    returned: success
    type: str

"""
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils

HAS_SF_SDK = netapp_utils.has_sf_sdk()

try:
    from solidfire.models import Network, NetworkConfig
    HAS_SF_SDK = True
except Exception:
    HAS_SF_SDK = False


class ElementSWNetworkInterfaces(object):
    """
    Element Software Network Interfaces - Bond 1G and 10G Network configuration
    """

    def __init__(self):
        self.argument_spec = netapp_utils.ontap_sf_host_argument_spec()
        self.argument_spec.update(
            method=dict(type='str', required=True, choices=['loopback', 'manual', 'dhcp', 'static']),
            ip_address_1g=dict(type='str', required=True),
            ip_address_10g=dict(type='str', required=True),
            subnet_1g=dict(type='str', required=True),
            subnet_10g=dict(type='str', required=True),
            gateway_address_1g=dict(type='str', required=True),
            gateway_address_10g=dict(type='str', required=True),
            mtu_1g=dict(type='str', default='1500'),
            mtu_10g=dict(type='str', default='1500'),
            dns_nameservers=dict(type='list'),
            dns_search_domains=dict(type='list'),
            bond_mode_1g=dict(type='str', default='ActivePassive', choices=['ActivePassive', 'ALB', 'LACP']),
            bond_mode_10g=dict(type='str', default='ActivePassive', choices=['ActivePassive', 'ALB', 'LACP']),
            lacp_1g=dict(type='str', default='Slow', choices=['Fast', 'Slow']),
            lacp_10g=dict(type='str', default='Slow', choices=['Fast', 'Slow']),
            virtual_network_tag=dict(type='str'),
        )

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True,
        )

        input_params = self.module.params

        self.method = input_params['method']
        self.ip_address_1g = input_params['ip_address_1g']
        self.ip_address_10g = input_params['ip_address_10g']
        self.subnet_1g = input_params['subnet_1g']
        self.subnet_10g = input_params['subnet_10g']
        self.gateway_address_1g = input_params['gateway_address_1g']
        self.gateway_address_10g = input_params['gateway_address_10g']
        self.mtu_1g = input_params['mtu_1g']
        self.mtu_10g = input_params['mtu_10g']
        self.dns_nameservers = input_params['dns_nameservers']
        self.dns_search_domains = input_params['dns_search_domains']
        self.bond_mode_1g = input_params['bond_mode_1g']
        self.bond_mode_10g = input_params['bond_mode_10g']
        self.lacp_1g = input_params['lacp_1g']
        self.lacp_10g = input_params['lacp_10g']
        self.virtual_network_tag = input_params['virtual_network_tag']

        if HAS_SF_SDK is False:
            self.module.fail_json(msg="Unable to import the SolidFire Python SDK")
        else:
            self.sfe = netapp_utils.create_sf_connection(module=self.module, port=442)

    def set_network_config(self):
        """
        set network configuration
        """
        try:
            self.sfe.set_network_config(network=self.network_object)
        except Exception as exception_object:
            self.module.fail_json(msg='Error network setting for node %s' % (to_native(exception_object)),
                                  exception=traceback.format_exc())

    def get_network_params_object(self):
        """
        Get Element SW Network object
        :description: get Network object

        :return: NetworkConfig object
        :rtype: object(NetworkConfig object)
        """
        try:
            bond_1g_network = NetworkConfig(method=self.method,
                                            address=self.ip_address_1g,
                                            netmask=self.subnet_1g,
                                            gateway=self.gateway_address_1g,
                                            mtu=self.mtu_1g,
                                            dns_nameservers=self.dns_nameservers,
                                            dns_search=self.dns_search_domains,
                                            bond_mode=self.bond_mode_1g,
                                            bond_lacp_rate=self.lacp_1g,
                                            virtual_network_tag=self.virtual_network_tag)
            bond_10g_network = NetworkConfig(method=self.method,
                                             address=self.ip_address_10g,
                                             netmask=self.subnet_10g,
                                             gateway=self.gateway_address_10g,
                                             mtu=self.mtu_10g,
                                             dns_nameservers=self.dns_nameservers,
                                             dns_search=self.dns_search_domains,
                                             bond_mode=self.bond_mode_10g,
                                             bond_lacp_rate=self.lacp_10g,
                                             virtual_network_tag=self.virtual_network_tag)
            network_object = Network(bond1_g=bond_1g_network,
                                     bond10_g=bond_10g_network)
            return network_object
        except Exception as e:
            self.module.fail_json(msg='Error with setting up network object for node 1G and 10G configuration : %s' % to_native(e),
                                  exception=to_native(e))

    def apply(self):
        """
        Check connection and initialize node with cluster ownership
        """
        changed = False
        result_message = None
        self.network_object = self.get_network_params_object()
        if self.network_object is not None:
            self.set_network_config()
            changed = True
        else:
            result_message = "Skipping changes, No change requested"
        self.module.exit_json(changed=changed, msg=result_message)


def main():
    """
    Main function
    """
    elementsw_network_interfaces = ElementSWNetworkInterfaces()
    elementsw_network_interfaces.apply()


if __name__ == '__main__':
    main()
