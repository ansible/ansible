#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = '''
---
module: azure_rm_virtualnetworkgateway

version_added: "2.8"

short_description: Manage Azure virtual network gateways.

description:
    - Create, update or delete a virtual network gateway(VPN Gateway). When creating a VPN Gateway you must provide the name of an
      existing virtual network.

options:
    resource_group:
        description:
            - Name of a resource group where VPN Gateway exists or will be created.
        required: true
    name:
        description:
            - Name of VPN Gateway.
        required: true
    state:
        description:
            - Assert the state of the VPN Gateway. Use 'present' to create or update VPN gateway and
              'absent' to delete VPN gateway.
        default: present
        choices:
            - absent
            - present
        required: false
    location:
        description:
            - Valid azure location. Defaults to location of the resource group.
        required: false
    virtual_network:
        description:
            - An existing virtual network with which the VPN Gateway will be associated. Required
              when creating a VPN Gateway.
            - It can be the virtual network's name.
            - Make sure your virtual network is in the same resource group as VPN gateway when you give only the name.
            - It can be the virtual network's resource id.
            - It can be a dict which contains C(name) and C(resource_group) of the virtual network.
        aliases:
            - virtual_network_name
        required: true
    ip_configurations:
        description:
            - List of ip configurations
        suboptions:
            name:
                description:
                    - Name of the ip configuration.
                required: true
            private_ip_allocation_method:
                description:
                    - private ip allocation method.
                choices:
                    - dynamic
                    - static
                default: dynamic
            public_ip_address_name:
                description:
                    - Name of the public ip address. None for disable ip address.
            subnet:
                description:
                    - ID of the gateway subnet for VPN.
                default: GatewaySubnet
    gateway_type:
        description:
            - The type of this virtual network gateway
        default: vpn
        choices:
            - vpn
            - express_route
    vpn_type:
        description:
            - The type of this virtual network gateway
        default: route_based
        choices:
            - route_based
            - policy_based
    enable_bgp:
        description:
            - Whether BGP is enabled for this virtual network gateway or not
        default: false
    sku:
        description:
            - The reference of the VirtualNetworkGatewaySku resource which represents the SKU selected for Virtual network gateway.
        default: VpnGw1
        choices:
            - VpnGw1
            - VpnGw2
            - VpnGw3
    bgp_settings:
        description:
            - Virtual network gateway's BGP speaker settings.
        suboptions:
            asn:
                description:
                    - The BGP speaker's ASN.
                required: True

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Madhura Naniwadekar (@Madhura-CSI)"
'''

EXAMPLES = '''
    - name: Create virtual network gateway without bgp settings
      azure_rm_virtualnetworkgateway:
        resource_group: myResourceGroup
        name: myVirtualNetworkGateway
        ip_configurations:
          - name: testipconfig
            private_ip_allocation_method: Dynamic
            public_ip_address_name: testipaddr
        virtual_network: myVirtualNetwork
        tags:
          common: "xyz"

    - name: Create virtual network gateway with bgp
      azure_rm_virtualnetworkgateway:
        resource_group: myResourceGroup
        name: myVirtualNetworkGateway
        sku: vpn_gw1
        ip_configurations:
          - name: testipconfig
            private_ip_allocation_method: Dynamic
            public_ip_address_name: testipaddr
        enable_bgp: yes
        virtual_network: myVirtualNetwork
        bgp_settings:
          asn: 65515
          bgp_peering_address: "169.254.54.209"
        tags:
          common: "xyz"

    - name: Delete instance of virtual network gateway
      azure_rm_virtualnetworkgateway:
        resource_group: myResourceGroup
        name: myVirtualNetworkGateway
        state: absent
'''

RETURN = '''
id:
    description:
        - Virtual Network Gateway resource ID
    returned: always
    type: str
    sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Network/virtualNetworkGateways/myV
             irtualNetworkGateway"
'''

try:
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    # This is handled in azure_rm_common
    pass

from ansible.module_utils.azure_rm_common import AzureRMModuleBase, CIDR_PATTERN
from ansible.module_utils.common.dict_transformations import _snake_to_camel


AZURE_VPN_GATEWAY_OBJECT_CLASS = 'VirtualNetworkGateway'


ip_configuration_spec = dict(
    name=dict(type='str', required=True),
    private_ip_allocation_method=dict(type='str', choices=['Dynamic', 'Static'], default='Dynamic'),
    subnet=dict(type='str'),
    public_ip_address_name=dict(type='str'),
)


sku_spec = dict(
    name=dict(type='str', default='VpnGw1'),
    tier=dict(type='str', default='VpnGw1')
)


bgp_spec = dict(
    asn=dict(type='int', required=True),
)


def vgw_to_dict(vgw):
    results = dict(
        id=vgw.id,
        name=vgw.name,
        location=vgw.location,
        gateway_type=vgw.gateway_type,
        vpn_type=vgw.vpn_type,
        enable_bgp=vgw.enable_bgp,
        tags=vgw.tags,
        provisioning_state=vgw.provisioning_state,
        sku=dict(
            name=vgw.sku.name,
            tier=vgw.sku.tier
        ),
        bgp_settings=dict(
            asn=vgw.bgp_settings.asn,
            bgp_peering_address=vgw.bgp_settings.bgp_peering_address,
            peer_weight=vgw.bgp_settings.peer_weight
        ) if vgw.bgp_settings else None,
        etag=vgw.etag
    )
    return results


class AzureRMVirtualNetworkGateway(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            resource_group=dict(type='str', required=True),
            name=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            location=dict(type='str'),
            ip_configurations=dict(type='list', default=None, elements='dict', options=ip_configuration_spec),
            gateway_type=dict(type='str', default='vpn', choices=['vpn', 'express_route']),
            vpn_type=dict(type='str', default='route_based', choices=['route_based', 'policy_based']),
            enable_bgp=dict(type='bool', default=False),
            sku=dict(default='VpnGw1', choices=['VpnGw1', 'VpnGw2', 'VpnGw3']),
            bgp_settings=dict(type='dict', options=bgp_spec),
            virtual_network=dict(type='raw', aliases=['virtual_network_name'])
        )

        self.resource_group = None
        self.name = None
        self.state = None
        self.location = None
        self.ip_configurations = None
        self.gateway_type = None
        self.vpn_type = None
        self.enable_bgp = None
        self.sku = None
        self.bgp_settings = None

        self.results = dict(
            changed=False,
            state=dict()
        )

        super(AzureRMVirtualNetworkGateway, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                           supports_check_mode=True)

    def exec_module(self, **kwargs):

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        changed = False
        results = dict()
        vgw = None

        resource_group = self.get_resource_group(self.resource_group)
        if not self.location:
            self.location = resource_group.location

        self.virtual_network = self.parse_resource_to_dict(self.virtual_network)
        resource_group = self.get_resource_group(self.resource_group)

        try:
            vgw = self.network_client.virtual_network_gateways.get(self.resource_group, self.name)
            if self.state == 'absent':
                self.log("CHANGED: vnet exists but requested state is 'absent'")
                changed = True
        except CloudError:
            if self.state == 'present':
                self.log("CHANGED: VPN Gateway {0} does not exist but requested state is 'present'".format(self.name))
                changed = True

        if vgw:
            results = vgw_to_dict(vgw)
            if self.state == 'present':
                update_tags, results['tags'] = self.update_tags(results['tags'])
                if update_tags:
                    changed = True
                sku = dict(name=self.sku, tier=self.sku)
                if sku != results['sku']:
                    changed = True
                if self.enable_bgp != results['enable_bgp']:
                    changed = True
                if self.bgp_settings and self.bgp_settings['asn'] != results['bgp_settings']['asn']:
                    changed = True

        self.results['changed'] = changed
        self.results['id'] = results.get('id')

        if self.check_mode:
            return self.results
        if changed:
            if self.state == 'present':
                if not self.sku:
                    self.fail('Parameter error: sku is required when creating a vpn gateway')
                if not self.ip_configurations:
                    self.fail('Parameter error: ip_configurations required when creating a vpn gateway')
                subnet = self.network_models.SubResource(
                    id='/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Network/virtualNetworks/{2}/subnets/GatewaySubnet'.format(
                        self.virtual_network['subscription_id'],
                        self.virtual_network['resource_group'],
                        self.virtual_network['name']))

                public_ip_address = self.network_models.SubResource(
                    id='/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Network/publicIPAddresses/{2}'.format(
                        self.virtual_network['subscription_id'],
                        self.virtual_network['resource_group'],
                        self.ip_configurations[0]['public_ip_address_name']))

                vgw_ip_configurations = [
                    self.network_models.VirtualNetworkGatewayIPConfiguration(
                        private_ip_allocation_method=ip_config.get('private_ip_allocation_method'),
                        subnet=subnet,
                        public_ip_address=public_ip_address,
                        name='default'
                    ) for ip_config in self.ip_configurations
                ]

                vgw_sku = self.network_models.VirtualNetworkGatewaySku(
                    name=self.sku,
                    tier=self.sku
                )

                vgw_bgp_settings = self.network_models.BgpSettings(
                    asn=self.bgp_settings.get('asn'),
                ) if self.bgp_settings else None
                vgw = self.network_models.VirtualNetworkGateway(
                    location=self.location,
                    ip_configurations=vgw_ip_configurations,
                    gateway_type=_snake_to_camel(self.gateway_type, True),
                    vpn_type=_snake_to_camel(self.vpn_type, True),
                    enable_bgp=self.enable_bgp,
                    sku=vgw_sku,
                    bgp_settings=vgw_bgp_settings
                )
                if self.tags:
                    vgw.tags = self.tags
                results = self.create_or_update_vgw(vgw)

            else:
                results = self.delete_vgw()

        if self.state == 'present':
            self.results['id'] = results.get('id')
        return self.results

    def create_or_update_vgw(self, vgw):
        try:
            poller = self.network_client.virtual_network_gateways.create_or_update(self.resource_group, self.name, vgw)
            new_vgw = self.get_poller_result(poller)
            return vgw_to_dict(new_vgw)
        except Exception as exc:
            self.fail("Error creating or updating virtual network gateway {0} - {1}".format(self.name, str(exc)))

    def delete_vgw(self):
        try:
            poller = self.network_client.virtual_network_gateways.delete(self.resource_group, self.name)
            self.get_poller_result(poller)
        except Exception as exc:
            self.fail("Error deleting virtual network gateway {0} - {1}".format(self.name, str(exc)))
        return True


def main():
    AzureRMVirtualNetworkGateway()


if __name__ == '__main__':
    main()
