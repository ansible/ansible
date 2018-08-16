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
module: azure_rm_publicipaddress_facts

version_added: "2.1"

short_description: Get public IP facts.

description:
    - Get facts for a specific public IP or all public IPs within a resource group.

options:
    name:
        description:
            - Only show results for a specific Public IP.
    resource_group:
        description:
            - Limit results by resource group. Required when using name parameter.
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.

extends_documentation_fragment:
    - azure

author:
    - "Chris Houseknecht (@chouseknecht)"
    - "Matt Davis (@nitzmahone)"
'''

EXAMPLES = '''
    - name: Get facts for one Public IP
      azure_rm_publicipaddress_facts:
        resource_group: Testing
        name: publicip001

    - name: Get facts for all Public IPs within a resource groups
      azure_rm_publicipaddress_facts:
        resource_group: Testing
'''

RETURN = '''
azure_publicipaddresses:
    description: List of public IP address dicts.
    returned: always
    type: list
    example: [{
        "etag": 'W/"a31a6d7d-cb18-40a5-b16d-9f4a36c1b18a"',
        "id": "/subscriptions/XXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXX/resourceGroups/Testing/providers/Microsoft.Network/publicIPAddresses/pip2001",
        "location": "eastus2",
        "name": "pip2001",
        "properties": {
            "idleTimeoutInMinutes": 4,
            "provisioningState": "Succeeded",
            "publicIPAllocationMethod": "Dynamic",
            "resourceGuid": "29de82f4-a7da-440e-bd3d-9cabb79af95a"
        },
        "type": "Microsoft.Network/publicIPAddresses"
    }]
'''
try:
    from msrestazure.azure_exceptions import CloudError
    from azure.common import AzureMissingResourceHttpError, AzureHttpError
except:
    # This is handled in azure_rm_common
    pass

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

AZURE_OBJECT_CLASS = 'PublicIp'


class AzureRMPublicIPFacts(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            name=dict(type='str'),
            resource_group=dict(type='str'),
            tags=dict(type='list')
        )

        self.results = dict(
            changed=False,
            ansible_facts=dict(azure_publicipaddresses=[])
        )

        self.name = None
        self.resource_group = None
        self.tags = None

        super(AzureRMPublicIPFacts, self).__init__(self.module_arg_spec,
                                                   supports_tags=False,
                                                   facts_module=True)

    def exec_module(self, **kwargs):

        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        if self.name and not self.resource_group:
            self.fail("Parameter error: resource group required when filtering by name.")

        if self.name:
            self.results['ansible_facts']['azure_publicipaddresses'] = self.get_item()
        elif self.resource_group:
            self.results['ansible_facts']['azure_publicipaddresses'] = self.list_resource_group()
        else:
            self.results['ansible_facts']['azure_publicipaddresses'] = self.list_all()

        return self.results

    def get_item(self):
        self.log('Get properties for {0}'.format(self.name))
        item = None
        result = []

        try:
            item = self.network_client.public_ip_addresses.get(self.resource_group, self.name)
        except CloudError:
            pass

        if item and self.has_tags(item.tags, self.tags):
            pip = self.serialize_obj(item, AZURE_OBJECT_CLASS)
            pip['name'] = item.name
            pip['type'] = item.type
            result = [pip]

        return result

    def list_resource_group(self):
        self.log('List items in resource groups')
        try:
            response = self.network_client.public_ip_addresses.list(self.resource_group)
        except AzureHttpError as exc:
            self.fail("Error listing items in resource groups {0} - {1}".format(self.resource_group, str(exc)))

        results = []
        for item in response:
            if self.has_tags(item.tags, self.tags):
                pip = self.serialize_obj(item, AZURE_OBJECT_CLASS)
                pip['name'] = item.name
                pip['type'] = item.type
                results.append(pip)
        return results

    def list_all(self):
        self.log('List all items')
        try:
            response = self.network_client.public_ip_addresses.list_all()
        except AzureHttpError as exc:
            self.fail("Error listing all items - {0}".format(str(exc)))

        results = []
        for item in response:
            if self.has_tags(item.tags, self.tags):
                pip = self.serialize_obj(item, AZURE_OBJECT_CLASS)
                pip['name'] = item.name
                pip['type'] = item.type
                results.append(pip)
        return results


def main():
    AzureRMPublicIPFacts()


if __name__ == '__main__':
    main()
