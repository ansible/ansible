#!/usr/bin/python
#
# Copyright (c) 2016 Matt Davis, <mdavis@ansible.com>
#                    Chris Houseknecht, <house@redhat.com>

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'curated'}


DOCUMENTATION = '''
---
module: azure_rm_storageaccount_facts

version_added: "2.1"

short_description: Get storage account facts.

description:
    - Get facts for one storage account or all storage accounts within a resource group.

options:
    name:
        description:
            - Only show results for a specific account.
        required: false
        default: null
    resource_group:
        description:
            - Limit results to a resource group. Required when filtering by name.
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
    - name: Get facts for one account
      azure_rm_storageaccount_facts:
        resource_group: Testing
        name: clh0002

    - name: Get facts for all accounts in a resource group
      azure_rm_storageaccount_facts:
        resource_group: Testing

    - name: Get facts for all accounts by tags
      azure_rm_storageaccount_facts:
        tags:
          - testing
          - foo:bar
'''

RETURN = '''
azure_storageaccounts:
    description: List of storage account dicts.
    returned: always
    type: list
    example: [{
        "id": "/subscriptions/XXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXX/resourceGroups/testing/providers/Microsoft.Storage/storageAccounts/testaccount001",
        "location": "eastus2",
        "name": "testaccount001",
        "properties": {
            "accountType": "Standard_LRS",
            "creationTime": "2016-03-28T02:46:58.290113Z",
            "primaryEndpoints": {
                "blob": "https://testaccount001.blob.core.windows.net/",
                "file": "https://testaccount001.file.core.windows.net/",
                "queue": "https://testaccount001.queue.core.windows.net/",
                "table": "https://testaccount001.table.core.windows.net/"
            },
            "primaryLocation": "eastus2",
            "provisioningState": "Succeeded",
            "statusOfPrimary": "Available"
        },
        "tags": {},
        "type": "Microsoft.Storage/storageAccounts"
    }]
'''

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.common import AzureMissingResourceHttpError, AzureHttpError
except:
    # This is handled in azure_rm_common
    pass

from ansible.module_utils.azure_rm_common import AzureRMModuleBase


AZURE_OBJECT_CLASS = 'StorageAccount'


class AzureRMStorageAccountFacts(AzureRMModuleBase):
    def __init__(self):

        self.module_arg_spec = dict(
            name=dict(type='str'),
            resource_group=dict(type='str'),
            tags=dict(type='list'),
        )

        self.results = dict(
            changed=False,
            ansible_facts=dict(azure_storageaccounts=[])
        )

        self.name = None
        self.resource_group = None
        self.tags = None

        super(AzureRMStorageAccountFacts, self).__init__(self.module_arg_spec,
                                                         supports_tags=False,
                                                         facts_module=True)

    def exec_module(self, **kwargs):

        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        if self.name and not self.resource_group:
            self.fail("Parameter error: resource group required when filtering by name.")

        if self.name:
            self.results['ansible_facts']['azure_storageaccounts'] = self.get_account()
        elif self.resource_group:
            self.results['ansible_facts']['azure_storageaccounts'] = self.list_resource_group()
        else:
            self.results['ansible_facts']['azure_storageaccounts'] = self.list_all()

        return self.results

    def get_account(self):
        self.log('Get properties for account {0}'.format(self.name))
        account = None
        result = []

        try:
            account = self.storage_client.storage_accounts.get_properties(self.resource_group, self.name)
        except CloudError:
            pass

        if account and self.has_tags(account.tags, self.tags):
            result = [self.serialize_obj(account, AZURE_OBJECT_CLASS)]

        return result

    def list_resource_group(self):
        self.log('List items')
        try:
            response = self.storage_client.storage_accounts.list_by_resource_group(self.resource_group)
        except Exception as exc:
            self.fail("Error listing for resource group {0} - {1}".format(self.resource_group, str(exc)))

        results = []
        for item in response:
            if self.has_tags(item.tags, self.tags):
                results.append(self.serialize_obj(item, AZURE_OBJECT_CLASS))
        return results

    def list_all(self):
        self.log('List all items')
        try:
            response = self.storage_client.storage_accounts.list_by_resource_group(self.resource_group)
        except Exception as exc:
            self.fail("Error listing all items - {0}".format(str(exc)))

        results = []
        for item in response:
            if self.has_tags(item.tags, self.tags):
                results.append(self.serialize_obj(item, AZURE_OBJECT_CLASS))
        return results


def main():
    AzureRMStorageAccountFacts()


if __name__ == '__main__':
    main()
