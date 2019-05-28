#!/usr/bin/python
#
# Copyright (c) 2018 Yunge Zhu <yungez@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: azure_rm_virtualnetworkpeering
version_added: "2.8"
short_description: Manage Azure Virtual Network Peering.
description:
    - Create, update and delete Azure Virtual Network Peering.

options:
    resource_group:
        description:
            - Name of a resource group where the vnet exists.
        required: true
    name:
        description:
            - Name of the virtual network peering.
        required: true
    virtual_network:
        description:
            - Virtual network to be peered.
            - It can be name of virtual network.
            - It can be virtual network resource id.
        required: true
    remote_virtual_network:
        description:
            - Remote virtual network to be peered.
            - It can be name of remote virtual network in same resource group.
            - It can be remote virtual network resource id.
            - It can be a dict which contains C(name) and C(resource_group) of remote virtual network.
            - Required when creating
    allow_virtual_network_access:
        description:
            - Allows VMs in the remote VNet to access all VMs in the local VNet.
        type: bool
        default: false
    allow_forwarded_traffic:
        description:
            - Allows forwarded traffic from the VMs in the remote VNet.
        type: bool
        default: false
    use_remote_gateways:
        description:
            - If remote gateways can be used on this virtual network.
        type: bool
        default: false
    allow_gateway_transit:
        description:
            - Allows VNet to use the remote VNet's gateway. Remote VNet gateway must have --allow-gateway-transit enabled for remote peering.
            - Only 1 peering can have this flag enabled. Cannot be set if the VNet already has a gateway.
        type: bool
        default: false
    state:
        description:
            - Assert the state of the virtual network peering. Use C(present) to create or update a peering and C(absent) to delete it.
        default: present
        choices:
            - absent
            - present

extends_documentation_fragment:
    - azure

author:
    - Yunge Zhu (@yungezz)
'''

EXAMPLES = '''
    - name: Create virtual network peering
      azure_rm_virtualnetworkpeering:
        resource_group: myResourceGroup
        virtual_network: myVirtualNetwork
        name: myPeering
        remote_virtual_network:
          resource_group: mySecondResourceGroup
          name: myRemoteVirtualNetwork
        allow_virtual_network_access: false
        allow_forwarded_traffic: true

    - name: Delete the virtual network peering
      azure_rm_virtualnetworkpeering:
        resource_group: myResourceGroup
        virtual_network: myVirtualNetwork
        name: myPeering
        state: absent
'''
RETURN = '''
id:
    description: Id of the Azure virtual network peering
    returned: always
    type: dict
    example:
        id: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Network/virtualNetworks/myVirtualN
             etwork/virtualNetworkPeerings/myPeering"
'''

try:
    from msrestazure.azure_exceptions import CloudError
    from msrestazure.tools import is_valid_resource_id
    from msrest.polling import LROPoller
except ImportError:
    # This is handled in azure_rm_common
    pass

from ansible.module_utils.azure_rm_common import AzureRMModuleBase, format_resource_id


def virtual_network_to_dict(vnet):
    '''
    Convert a virtual network object to a dict.
    '''
    results = dict(
        id=vnet.id,
        name=vnet.name,
        location=vnet.location,
        type=vnet.type,
        tags=vnet.tags,
        provisioning_state=vnet.provisioning_state,
        etag=vnet.etag
    )
    if vnet.dhcp_options and len(vnet.dhcp_options.dns_servers) > 0:
        results['dns_servers'] = []
        for server in vnet.dhcp_options.dns_servers:
            results['dns_servers'].append(server)
    if vnet.address_space and len(vnet.address_space.address_prefixes) > 0:
        results['address_prefixes'] = []
        for space in vnet.address_space.address_prefixes:
            results['address_prefixes'].append(space)
    return results


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
        allow_virtual_network_access=vnetpeering.allow_virtual_network_access,
        etag=vnetpeering.etag
    )
    return results


class AzureRMVirtualNetworkPeering(AzureRMModuleBase):

    def __init__(self):
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                required=True
            ),
            name=dict(
                type='str',
                required=True
            ),
            virtual_network=dict(
                type='raw'
            ),
            remote_virtual_network=dict(
                type='raw'
            ),
            allow_virtual_network_access=dict(
                type='bool',
                default=False
            ),
            allow_forwarded_traffic=dict(
                type='bool',
                default=False
            ),
            allow_gateway_transit=dict(
                type='bool',
                default=False
            ),
            use_remote_gateways=dict(
                type='bool',
                default=False
            ),
            state=dict(
                type='str',
                default='present',
                choices=['present', 'absent']
            )
        )

        self.resource_group = None
        self.name = None
        self.virtual_network = None
        self.remote_virtual_network = None
        self.allow_virtual_network_access = None
        self.allow_forwarded_traffic = None
        self.allow_gateway_transit = None
        self.use_remote_gateways = None

        self.results = dict(changed=False)

        super(AzureRMVirtualNetworkPeering, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                           supports_check_mode=True,
                                                           supports_tags=False)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        for key in list(self.module_arg_spec.keys()):
            setattr(self, key, kwargs[key])

        to_be_updated = False

        resource_group = self.get_resource_group(self.resource_group)

        # parse virtual_network
        self.virtual_network = self.parse_resource_to_dict(self.virtual_network)
        if self.virtual_network['resource_group'] != self.resource_group:
            self.fail('Resource group of virtual_network is not same as param resource_group')

        # parse remote virtual_network
        self.remote_virtual_network = self.format_vnet_id(self.remote_virtual_network)

        # get vnet peering
        response = self.get_vnet_peering()

        if self.state == 'present':
            if response:
                # check vnet id not changed
                existing_vnet = self.parse_resource_to_dict(response['id'])
                if existing_vnet['resource_group'] != self.virtual_network['resource_group'] or \
                   existing_vnet['name'] != self.virtual_network['name']:
                    self.fail("Cannot update virtual_network of Virtual Network Peering!")

                # check remote vnet id not changed
                if response['remote_virtual_network'].lower() != self.remote_virtual_network.lower():
                    self.fail("Cannot update remote_virtual_network of Virtual Network Peering!")

                # check if update
                to_be_updated = self.check_update(response)

            else:
                # not exists, create new vnet peering
                to_be_updated = True

                # check if vnet exists
                virtual_network = self.get_vnet(self.virtual_network['resource_group'], self.virtual_network['name'])
                if not virtual_network:
                    self.fail("Virtual network {0} in resource group {1} does not exist!".format(
                        self.virtual_network['name'], self.virtual_network['resource_group']))

        elif self.state == 'absent':
            if response:
                self.log('Delete Azure Virtual Network Peering')
                self.results['changed'] = True
                self.results['id'] = response['id']

                if self.check_mode:
                    return self.results

                response = self.delete_vnet_peering()

            else:
                self.fail("Azure Virtual Network Peering {0} does not exist in resource group {1}".format(self.name, self.resource_group))

        if to_be_updated:
            self.results['changed'] = True

            if self.check_mode:
                return self.results

            response = self.create_or_update_vnet_peering()
            self.results['id'] = response['id']

        return self.results

    def format_vnet_id(self, vnet):
        if not vnet:
            return vnet
        if isinstance(vnet, dict) and vnet.get('name') and vnet.get('resource_group'):
            remote_vnet_id = format_resource_id(vnet['name'],
                                                self.subscription_id,
                                                'Microsoft.Network',
                                                'virtualNetworks',
                                                vnet['resource_group'])
        elif isinstance(vnet, str):
            if is_valid_resource_id(vnet):
                remote_vnet_id = vnet
            else:
                remote_vnet_id = format_resource_id(vnet,
                                                    self.subscription_id,
                                                    'Microsoft.Network',
                                                    'virtualNetworks',
                                                    self.resource_group)
        else:
            self.fail("remote_virtual_network could be a valid resource id, dict of name and resource_group, name of virtual network in same resource group.")
        return remote_vnet_id

    def check_update(self, exisiting_vnet_peering):
        if self.allow_forwarded_traffic != exisiting_vnet_peering['allow_forwarded_traffic']:
            return True
        if self.allow_gateway_transit != exisiting_vnet_peering['allow_gateway_transit']:
            return True
        if self.allow_virtual_network_access != exisiting_vnet_peering['allow_virtual_network_access']:
            return True
        if self.use_remote_gateways != exisiting_vnet_peering['use_remote_gateways']:
            return True
        return False

    def get_vnet(self, resource_group, vnet_name):
        '''
        Get Azure Virtual Network
        :return: deserialized Azure Virtual Network
        '''
        self.log("Get the Azure Virtual Network {0}".format(vnet_name))
        vnet = self.network_client.virtual_networks.get(resource_group, vnet_name)

        if vnet:
            results = virtual_network_to_dict(vnet)
            return results
        return False

    def create_or_update_vnet_peering(self):
        '''
        Creates or Update Azure Virtual Network Peering.

        :return: deserialized Azure Virtual Network Peering instance state dictionary
        '''
        self.log("Creating or Updating the Azure Virtual Network Peering {0}".format(self.name))

        vnet_id = format_resource_id(self.virtual_network['name'],
                                     self.subscription_id,
                                     'Microsoft.Network',
                                     'virtualNetworks',
                                     self.virtual_network['resource_group'])
        peering = self.network_models.VirtualNetworkPeering(
            id=vnet_id,
            name=self.name,
            remote_virtual_network=self.network_models.SubResource(id=self.remote_virtual_network),
            allow_virtual_network_access=self.allow_virtual_network_access,
            allow_gateway_transit=self.allow_gateway_transit,
            allow_forwarded_traffic=self.allow_forwarded_traffic,
            use_remote_gateways=self.use_remote_gateways)

        try:
            response = self.network_client.virtual_network_peerings.create_or_update(self.resource_group,
                                                                                     self.virtual_network['name'],
                                                                                     self.name,
                                                                                     peering)
            if isinstance(response, LROPoller):
                response = self.get_poller_result(response)
            return vnetpeering_to_dict(response)
        except CloudError as exc:
            self.fail("Error creating Azure Virtual Network Peering: {0}.".format(exc.message))

    def delete_vnet_peering(self):
        '''
        Deletes the specified Azure Virtual Network Peering

        :return: True
        '''
        self.log("Deleting Azure Virtual Network Peering {0}".format(self.name))
        try:
            poller = self.network_client.virtual_network_peerings.delete(
                self.resource_group, self.virtual_network['name'], self.name)
            self.get_poller_result(poller)
            return True
        except CloudError as e:
            self.fail("Error deleting the Azure Virtual Network Peering: {0}".format(e.message))
            return False

    def get_vnet_peering(self):
        '''
        Gets the Virtual Network Peering.

        :return: deserialized Virtual Network Peering
        '''
        self.log(
            "Checking if Virtual Network Peering {0} is present".format(self.name))
        try:
            response = self.network_client.virtual_network_peerings.get(self.resource_group,
                                                                        self.virtual_network['name'],
                                                                        self.name)
            self.log("Response : {0}".format(response))
            return vnetpeering_to_dict(response)
        except CloudError:
            self.log('Did not find the Virtual Network Peering.')
            return False


def main():
    """Main execution"""
    AzureRMVirtualNetworkPeering()


if __name__ == '__main__':
    main()
