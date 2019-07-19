#!/usr/bin/python
#
# Copyright (c) 2019 Yunge Zhu (@yungezz)
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: azure_rm_virtualnetworkpeering_facts
version_added: "2.8"
short_description: Get facts of Azure Virtual Network Peering.
description:
    - Get facts of Azure Virtual Network Peering.

options:
    resource_group:
        description:
            - Name of a resource group where the vnet exists.
        required: True
    virtual_network:
        description:
            - The name of Virtual network.
            - It can be name of virtual network.
            - It can be virtual network resource id.
        required: True
    name:
        description:
            - Name of the virtual network peering.

extends_documentation_fragment:
    - azure

author:
    - Yunge Zhu (@yungezz)
'''

EXAMPLES = '''
    - name: Get virtual network peering by name
      azure_rm_virtualnetworkpeering_facts:
        resource_group: myResourceGroup
        virtual_network: myVnet1
        name: myVnetPeer

    - name: List virtual network peering of virtual network
      azure_rm_virtualnetworkpeering:
        resource_group: myResourceGroup
        virtual_network: myVnet1
'''

RETURN = '''
vnetpeerings:
    description: A list of Virtual Network Peering facts.
    returned: always
    type: complex
    contains:
        id:
            description: Id of current Virtual Network peering.
            returned: always
            type: str
            sample:
                "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Network/virtualNetworks/myVnet/virtualNetworkPeerings/peer1"
        name:
            description: Name of Virtual Network peering.
            returned: always
            type: str
            sample: myPeering
        remote_virtual_network:
            description: Id of remote Virtual Network to be peered to.
            returned: always
            type: str
            sample: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Network/virtualNetworks/myVnet2
        remote_address_space:
            description: The reference of the remote Virtual Network address space.
            type: complex
            contains:
                address_prefixes:
                    description: A list of address blocks reserved for this Virtual Network in CIDR notation.
                    type: list
                    sample: 10.1.0.0/16
        peering_state:
            description: The status of the virtual network peering.
            returned: always
            type: str
            sample: Connected
        provisioning_state:
            description: The provisioning state of the resource.
            returned: always
            type: str
            sample: Succeeded
        allow_forwarded_traffic:
            description: Whether the forwarded traffic from the VMs in the remote Virtual Network will be allowed/disallowed.
            returned: always
            type: bool
            sample: False
        allow_gateway_transit:
            description: If gateway links can be used in remote Virtual Networking to link to this Virtual Network.
            returned: always
            type: bool
            sample: False
        allow_virtual_network_access:
            description: Whether the VMs in the linked Virtual Network space would be able to access all the VMs in local Virtual Network space.
            returned: always
            type: bool
            sample: False
        use_remote_gateways:
            description: If remote gateways can be used on this Virtual Network.
            returned: always
            type: bool
            sample: False
'''

try:
    from msrestazure.azure_exceptions import CloudError
    from msrest.polling import LROPoller
except ImportError:
    # This is handled in azure_rm_common
    pass

from ansible.module_utils.azure_rm_common import AzureRMModuleBase


def vnetpeering_to_dict(vnetpeering):
    '''
    Convert a virtual network peering object to a dict.
    '''
    results = dict(
        id=vnetpeering.id,
        name=vnetpeering.name,
        remote_virtual_network=vnetpeering.remote_virtual_network.id,
        remote_address_space=dict(
            address_prefixes=vnetpeering.remote_address_space.address_prefixes
        ),
        peering_state=vnetpeering.peering_state,
        provisioning_state=vnetpeering.provisioning_state,
        use_remote_gateways=vnetpeering.use_remote_gateways,
        allow_gateway_transit=vnetpeering.allow_gateway_transit,
        allow_forwarded_traffic=vnetpeering.allow_forwarded_traffic,
        allow_virtual_network_access=vnetpeering.allow_virtual_network_access
    )
    return results


class AzureRMVirtualNetworkPeeringFacts(AzureRMModuleBase):

    def __init__(self):
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                required=True
            ),
            name=dict(
                type='str'
            ),
            virtual_network=dict(
                type='raw',
                required=True
            )
        )

        self.resource_group = None
        self.name = None
        self.virtual_network = None

        self.results = dict(changed=False)

        super(AzureRMVirtualNetworkPeeringFacts, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                                supports_tags=False)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        for key in list(self.module_arg_spec.keys()):
            setattr(self, key, kwargs[key])

        # parse virtual_network
        self.virtual_network = self.parse_resource_to_dict(self.virtual_network)
        if self.virtual_network['resource_group'] != self.resource_group:
            self.fail('Resource group of virtual_network is not same as param resource_group')

        self.results['vnetpeerings'] = []
        # get vnet peering
        if self.name:
            self.results['vnetpeerings'] = self.get_by_name()
        else:
            self.results['vnetpeerings'] = self.list_by_vnet()

        return self.results

    def get_by_name(self):
        '''
        Gets the Virtual Network Peering.

        :return: List of Virtual Network Peering
        '''
        self.log(
            "Get Virtual Network Peering {0}".format(self.name))
        results = []
        try:
            response = self.network_client.virtual_network_peerings.get(resource_group_name=self.resource_group,
                                                                        virtual_network_name=self.virtual_network['name'],
                                                                        virtual_network_peering_name=self.name)
            self.log("Response : {0}".format(response))
            results.append(vnetpeering_to_dict(response))
        except CloudError:
            self.log('Did not find the Virtual Network Peering.')
        return results

    def list_by_vnet(self):
        '''
        Lists the Virtual Network Peering in specific Virtual Network.

        :return: List of Virtual Network Peering
        '''
        self.log(
            "List Virtual Network Peering in Virtual Network {0}".format(self.virtual_network['name']))
        results = []
        try:
            response = self.network_client.virtual_network_peerings.list(resource_group_name=self.resource_group,
                                                                         virtual_network_name=self.virtual_network['name'])
            self.log("Response : {0}".format(response))
            if response:
                for p in response:
                    results.append(vnetpeering_to_dict(p))
        except CloudError:
            self.log('Did not find the Virtual Network Peering.')
        return results


def main():
    """Main execution"""
    AzureRMVirtualNetworkPeeringFacts()


if __name__ == '__main__':
    main()
