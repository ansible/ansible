#!/usr/bin/python
#
# Copyright (c) 2016 Matt Davis, <mdavis@ansible.com>
#                    Chris Houseknecht, <house@redhat.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_virtualnetwork_facts

version_added: "2.1"

short_description: Get virtual network facts.

description:
    - Get facts for a specific virtual network or all virtual networks within a resource group.

options:
    name:
        description:
            - Only show results for a specific security group.
    resource_group:
        description:
            - Limit results by resource group. Required when filtering by name.
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.

extends_documentation_fragment:
    - azure

author:
    - "Chris Houseknecht (@chouseknecht) <house@redhat.com>"
    - "Matt Davis (@nitzmahone) <mdavis@redhat.com>"

'''

EXAMPLES = '''
    - name: Get facts for one virtual network
      azure_rm_virtualnetwork_facts:
        resource_group: myResourceGroup
        name: secgroup001

    - name: Get facts for all virtual networks
      azure_rm_virtualnetwork_facts:
        resource_group: myResourceGroup

    - name: Get facts by tags
      azure_rm_virtualnetwork_facts:
        tags:
          - testing
'''
RETURN = '''
azure_virtualnetworks:
    description: List of virtual network dicts.
    returned: always
    type: list
    example: [{
        "etag": 'W/"532ba1be-ae71-40f2-9232-3b1d9cf5e37e"',
        "id": "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroup/myResourceGroup/providers/Microsoft.Network/virtualNetworks/vnet2001",
        "location": "eastus2",
        "name": "vnet2001",
        "properties": {
            "addressSpace": {
                "addressPrefixes": [
                    "10.10.0.0/16"
                ]
            },
            "provisioningState": "Succeeded",
            "resourceGuid": "a7ba285f-f7e7-4e17-992a-de4d39f28612",
            "subnets": []
        },
        "type": "Microsoft.Network/virtualNetworks"
    }]
virtualnetworks:
    description: List of virtual network dicts with same format as azure_rm_virtualnetwork module parameters.
    returned: always
    type: list
    contains:
            id:
                description:
                    - Resource ID.
                sample: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Network/virtualNetworks/vnet2001
                type: str
            address_prefixes:
                description:
                    - List of IPv4 address ranges where each is formatted using CIDR notation.
                sample: ["10.10.0.0/16"]
                type: list
            dns_servers:
                description:
                    - Custom list of DNS servers.
                type: list
                sample: ["www.azure.com"]
            location:
                description:
                    - Valid azure location.
                type: str
                sample: eastus
            tags:
                description:
                    - Tags assigned to the resource. Dictionary of string:string pairs.
                type: dict
                sample: { "tag1": "abc" }
            provisioning_state:
                description:
                    - Provisioning state of the resource.
                sample: Successed
                type: str
            name:
                description:
                    - name of the virtual network.
                type: str
                sample: foo
            subnets:
                description:
                    - Subnets associate to this virtual network.
                type: list
                contains:
                    id:
                        description:
                            - Resource ID.
                        type: str
                    name:
                        description:
                            - Resource Name.
                        type: str
                    provisioning_state:
                        description:
                            - provision state of the Resource.
                        type: str
                        sample: Successed
                    address_prefix:
                        description:
                            - The address prefix for the subnet.
                    network_security_group:
                        description:
                            - Existing security group id with which to associate the subnet.
                        type: str
                    route_table:
                        description:
                            - The reference of the RouteTable resource.
                        type: str
                    service_endpoints:
                        description:
                            - An array of service endpoints.
                        type: list
'''

try:
    from msrestazure.azure_exceptions import CloudError
except Exception:
    # This is handled in azure_rm_common
    pass

from ansible.module_utils.azure_rm_common import AzureRMModuleBase


AZURE_OBJECT_CLASS = 'VirtualNetwork'


class AzureRMNetworkInterfaceFacts(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            name=dict(type='str'),
            resource_group=dict(type='str'),
            tags=dict(type='list'),
        )

        self.results = dict(
            changed=False,
            ansible_facts=dict(azure_virtualnetworks=[]),
            virtualnetworks=[]
        )

        self.name = None
        self.resource_group = None
        self.tags = None

        super(AzureRMNetworkInterfaceFacts, self).__init__(self.module_arg_spec,
                                                           supports_tags=False,
                                                           facts_module=True)

    def exec_module(self, **kwargs):

        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        if self.name is not None:
            results = self.get_item()
        elif self.resource_group is not None:
            results = self.list_resource_group()
        else:
            results = self.list_items()

        self.results['ansible_facts']['azure_virtualnetworks'] = self.serialize(results)
        self.results['virtualnetworks'] = self.curated(results)

        return self.results

    def get_item(self):
        self.log('Get properties for {0}'.format(self.name))
        item = None
        results = []

        try:
            item = self.network_client.virtual_networks.get(self.resource_group, self.name)
        except CloudError:
            pass

        if item and self.has_tags(item.tags, self.tags):
            results = [item]
        return results

    def list_resource_group(self):
        self.log('List items for resource group')
        try:
            response = self.network_client.virtual_networks.list(self.resource_group)
        except CloudError as exc:
            self.fail("Failed to list for resource group {0} - {1}".format(self.resource_group, str(exc)))

        results = []
        for item in response:
            if self.has_tags(item.tags, self.tags):
                results.append(item)
        return results

    def list_items(self):
        self.log('List all for items')
        try:
            response = self.network_client.virtual_networks.list_all()
        except CloudError as exc:
            self.fail("Failed to list all items - {0}".format(str(exc)))

        results = []
        for item in response:
            if self.has_tags(item.tags, self.tags):
                results.append(item)
        return results

    def serialize(self, raws):
        self.log("Serialize all items")
        return [self.serialize_obj(item, AZURE_OBJECT_CLASS) for item in raws] if raws else []

    def curated(self, raws):
        self.log("Format all items")
        return [self.virtualnetwork_to_dict(x) for x in raws] if raws else []

    def virtualnetwork_to_dict(self, vnet):
        results = dict(
            id=vnet.id,
            name=vnet.name,
            location=vnet.location,
            tags=vnet.tags,
            provisioning_state=vnet.provisioning_state
        )
        if vnet.dhcp_options and len(vnet.dhcp_options.dns_servers) > 0:
            results['dns_servers'] = []
            for server in vnet.dhcp_options.dns_servers:
                results['dns_servers'].append(server)
        if vnet.address_space and len(vnet.address_space.address_prefixes) > 0:
            results['address_prefixes'] = []
            for space in vnet.address_space.address_prefixes:
                results['address_prefixes'].append(space)
        if vnet.subnets and len(vnet.subnets) > 0:
            results['subnets'] = [self.subnet_to_dict(x) for x in vnet.subnets]
        return results

    def subnet_to_dict(self, subnet):
        result = dict(
            id=subnet.id,
            name=subnet.name,
            provisioning_state=subnet.provisioning_state,
            address_prefix=subnet.address_prefix,
            network_security_group=subnet.network_security_group.id if subnet.network_security_group else None,
            route_table=subnet.route_table.id if subnet.route_table else None
        )
        if subnet.service_endpoints:
            result['service_endpoints'] = [{'service': item.service, 'locations': item.locations} for item in subnet.service_endpoints]
        return result


def main():
    AzureRMNetworkInterfaceFacts()


if __name__ == '__main__':
    main()
