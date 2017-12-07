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
                    'supported_by': 'certified'}


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
        default: null
        required: false
    resource_group:
        description:
            - Limit results by resource group. Required when filtering by name.
        default: null
        required: false
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.
        default: null
        required: false

extends_documentation_fragment:
    - azure

author:
    - "Chris Houseknecht house@redhat.com"
    - "Matt Davis mdavis@redhat.com"

'''

EXAMPLES = '''
    - name: Get facts for one virtual network
      azure_rm_virtualnetwork_facts:
        resource_group: Testing
        name: secgroup001

    - name: Get facts for all virtual networks
      azure_rm_virtualnetwork_facts:
        resource_group: Testing

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
        "id": "/subscriptions/XXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXX/resourceGroups/Testing/providers/Microsoft.Network/virtualNetworks/vnet2001",
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
'''

try:
    from msrestazure.azure_exceptions import CloudError
except:
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
            ansible_facts=dict(azure_virtualnetworks=[])
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
            self.results['ansible_facts']['azure_virtualnetworks'] = self.get_item()
        else:
            self.results['ansible_facts']['azure_virtualnetworks'] = self.list_items()

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
            results = [self.serialize_obj(item, AZURE_OBJECT_CLASS)]

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
                results.append(self.serialize_obj(item, AZURE_OBJECT_CLASS))
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
                results.append(self.serialize_obj(item, AZURE_OBJECT_CLASS))
        return results


def main():
    AzureRMNetworkInterfaceFacts()

if __name__ == '__main__':
    main()
