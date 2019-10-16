#!/usr/bin/python
#
# Copyright (c) 2019 Zim Kalinowski, (@zikalino)
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_subnet_facts
version_added: "2.8"
short_description: Get Azure Subnet facts.
description:
    - Get facts of Azure Subnet.

options:
    resource_group:
        description:
            - The name of the resource group.
        required: True
    virtual_network_name:
        description:
            - The name of the virtual network.
        required: True
    name:
        description:
            - The name of the subnet.

extends_documentation_fragment:
    - azure

author:
    - "Zim Kalinowski (@zikalino)"

'''

EXAMPLES = '''
  - name: Get facts of specific subnet
    azure_rm_subnet_facts:
      resource_group: myResourceGroup
      virtual_network_name: myVirtualNetwork
      name: mySubnet

  - name: List facts for all subnets in virtual network
    azure_rm_subnet_facts:
      resource_group: myResourceGroup
      virtual_network_name: myVirtualNetwork
      name: mySubnet
'''

RETURN = '''
subnets:
    description: A list of dictionaries containing facts for subnet.
    returned: always
    type: complex
    contains:
        id:
            description:
                - Subnet resource ID.
            returned: always
            type: str
            sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Network/virtualNetworks/my
                     VirtualNetwork/subnets/mySubnet"
        resource_group:
            description:
                - Name of resource group.
            returned: always
            type: str
            sample: myResourceGroup
        virtual_network_name:
            description:
                - Name of the containing virtual network.
            returned: always
            type: str
            sample: myVirtualNetwork
        name:
            description:
                - Name of the subnet.
            returned: always
            type: str
            sample: mySubnet
        address_prefix_cidr:
            description:
                - CIDR defining the IPv4 address space of the subnet.
            returned: always
            type: str
            sample: "10.1.0.0/16"
        route_table:
            description:
                - Associated route table id.
            returned: always
            type: str
            sample: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Network/routeTables/myRouteTable
        security_group:
            description:
                - Associated security group id.
            returned: always
            type: str
            sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Network/networkSecurityGr
                     oups/myNsg"
        service_endpoints:
            description:
                - List of service endpoints.
            type: list
            returned: when available
            contains:
                service:
                    description:
                        - The type of the endpoint service.
                locations:
                    description:
                        - A list of location names.
                    type: list
                provisioning_state:
                    description:
                        - Provisioning state.
                    returned: always
                    type: str
                    sample: Succeeded
        provisioning_state:
            description:
                - Provisioning state.
            returned: always
            type: str
            sample: Succeeded
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.network import NetworkManagementClient
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMSubnetFacts(AzureRMModuleBase):
    def __init__(self):
        # define user inputs into argument
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                required=True
            ),
            virtual_network_name=dict(
                type='str',
                required=True
            ),
            name=dict(
                type='str'
            )
        )
        # store the results of the module operation
        self.results = dict(
            changed=False
        )
        self.resource_group = None
        self.virtual_network_name = None
        self.name = None
        super(AzureRMSubnetFacts, self).__init__(self.module_arg_spec, supports_tags=False)

    def exec_module(self, **kwargs):
        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        if self.name is not None:
            self.results['subnets'] = self.get()
        else:
            self.results['subnets'] = self.list()

        return self.results

    def get(self):
        response = None
        results = []
        try:
            response = self.network_client.subnets.get(resource_group_name=self.resource_group,
                                                       virtual_network_name=self.virtual_network_name,
                                                       subnet_name=self.name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.fail('Could not get facts for Subnet.')

        if response is not None:
            results.append(self.format_response(response))

        return results

    def list(self):
        response = None
        results = []
        try:
            response = self.network_client.subnets.get(resource_group_name=self.resource_group,
                                                       virtual_network_name=self.virtual_network_name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.fail('Could not get facts for Subnet.')

        if response is not None:
            for item in response:
                results.append(self.format_item(item))

        return results

    def format_response(self, item):
        d = item.as_dict()
        d = {
            'resource_group': self.resource_group,
            'virtual_network_name': self.parse_resource_to_dict(d.get('id')).get('name'),
            'name': d.get('name'),
            'id': d.get('id'),
            'address_prefix_cidr': d.get('address_prefix'),
            'route_table': d.get('route_table', {}).get('id'),
            'security_group': d.get('network_security_group', {}).get('id'),
            'provisioning_state': d.get('provisioning_state'),
            'service_endpoints': d.get('service_endpoints')
        }
        return d


def main():
    AzureRMSubnetFacts()


if __name__ == '__main__':
    main()
