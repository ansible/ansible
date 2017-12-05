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
module: azure_rm_resourcegroup_facts

version_added: "2.1"

short_description: Get resource group facts.

description:
    - Get facts for a specific resource group or all resource groups.

options:
    name:
        description:
            - Limit results to a specific resource group.
        required: false
        default: null
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.
        required: false
        default: null

extends_documentation_fragment:
    - azure

author:
    - "Chris Houseknecht (@chouseknecht)"
    - "Matt Davis (@nitzmahone)"

'''

EXAMPLES = '''
    - name: Get facts for one resource group
      azure_rm_resourcegroup_facts:
        name: Testing

    - name: Get facts for all resource groups
      azure_rm_resourcegroup_facts:

    - name: Get facts by tags
      azure_rm_resourcegroup_facts:
        tags:
          - testing
          - foo:bar
'''
RETURN = '''
azure_resourcegroups:
    description: List of resource group dicts.
    returned: always
    type: list
    example: [{
        "id": "/subscriptions/XXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXX/resourceGroups/Testing",
        "location": "westus",
        "name": "Testing",
        "properties": {
            "provisioningState": "Succeeded"
        },
        "tags": {
            "delete": "never",
            "testing": "testing"
        }
    }]
'''

try:
    from msrestazure.azure_exceptions import CloudError
except:
    # This is handled in azure_rm_common
    pass

from ansible.module_utils.azure_rm_common import AzureRMModuleBase


AZURE_OBJECT_CLASS = 'ResourceGroup'


class AzureRMResourceGroupFacts(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            name=dict(type='str'),
            tags=dict(type='list')
        )

        self.results = dict(
            changed=False,
            ansible_facts=dict(azure_resourcegroups=[])
        )

        self.name = None
        self.tags = None

        super(AzureRMResourceGroupFacts, self).__init__(self.module_arg_spec,
                                                        supports_tags=False,
                                                        facts_module=True)

    def exec_module(self, **kwargs):

        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        if self.name:
            self.results['ansible_facts']['azure_resourcegroups'] = self.get_item()
        else:
            self.results['ansible_facts']['azure_resourcegroups'] = self.list_items()

        return self.results

    def get_item(self):
        self.log('Get properties for {0}'.format(self.name))
        item = None
        result = []

        try:
            item = self.rm_client.resource_groups.get(self.name)
        except CloudError:
            pass

        if item and self.has_tags(item.tags, self.tags):
            result = [self.serialize_obj(item, AZURE_OBJECT_CLASS)]

        return result

    def list_items(self):
        self.log('List all items')
        try:
            response = self.rm_client.resource_groups.list()
        except CloudError as exc:
            self.fail("Failed to list all items - {0}".format(str(exc)))

        results = []
        for item in response:
            if self.has_tags(item.tags, self.tags):
                results.append(self.serialize_obj(item, AZURE_OBJECT_CLASS))
        return results


def main():
    AzureRMResourceGroupFacts()

if __name__ == '__main__':
    main()
