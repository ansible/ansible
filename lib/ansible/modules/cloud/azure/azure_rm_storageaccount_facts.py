#!/usr/bin/python
#
# Copyright (c) 2016 Matt Davis, <mdavis@ansible.com>
#                    Chris Houseknecht, <house@redhat.com>

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


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
    resource_group:
        description:
            - Limit results to a resource group. Required when filtering by name.
        aliases:
            - resource_group_name
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.
    show_connection_string:
        description:
            - Show the connection string for each of the storageaccount's endpoints.
            - Note that it will cost a lot of time when list all storageaccount rather than query a single one.
        type: bool
        version_added: "2.8"
    show_blob_cors:
        description:
            - Show the blob CORS settings for each of the storageaccount's blob.
            - Note that it will cost a lot time when list all storageaccount rather than querry a single one.
        type: bool
        version_added: "2.8"

extends_documentation_fragment:
    - azure

author:
    - "Chris Houseknecht (@chouseknecht)"
    - "Matt Davis (@nitzmahone)"

'''

EXAMPLES = '''
    - name: Get facts for one account
      azure_rm_storageaccount_facts:
        resource_group: myResourceGroup
        name: clh0002

    - name: Get facts for all accounts in a resource group
      azure_rm_storageaccount_facts:
        resource_group: myResourceGroup

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
        "id": "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/myResourceGroups/testing/providers/Microsoft.Storage/storageAccounts/testaccount001",
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
storageaccounts:
    description: List of storage account dicts in resource module's parameter format.
    returned: always
    type: complex
    contains:
        id:
            description:
                - Resource ID.
            sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Storage/storageAccounts/t
                     estaccount001"
        name:
            description:
                - Name of the storage account to update or create.
            sample: "testaccount001"
        location:
            description:
                - Valid azure location. Defaults to location of the resource group.
            sample: eastus
        account_type:
            description:
                - Type of storage account.
                - "NOTE: Standard_ZRS and Premium_LRS accounts cannot be changed to other account types."
                - Other account types cannot be changed to Standard_ZRS or Premium_LRS.
            sample: Standard_ZRS
        custom_domain:
            description:
                - User domain assigned to the storage account.
                - Must be a dictionary with 'name' and 'use_sub_domain' keys where 'name' is the CNAME source.
            type: complex
            contains:
                name:
                    description:
                        - CNAME source.
                    sample: testaccount
                use_sub_domain:
                    description:
                        - whether to use sub domain.
                    sample: true
        kind:
            description:
                - The 'kind' of storage.
            sample: Storage
        access_tier:
            description:
                - The access tier for this storage account.
            sample: Hot
        https_only:
            description:
                -  Allows https traffic only to storage service if sets to true.
            sample: false
        provisioning_state:
            description:
                - Gets the status of the storage account at the time the operation was called.
                - Possible values include 'Creating', 'ResolvingDNS', 'Succeeded'.
            sample: Succeeded
        secondary_location:
            description:
                - Gets the location of the geo-replicated secondary for the storage account.
                - Only available if the accountType is Standard_GRS or Standard_RAGRS.
            sample: westus
        status_of_primary:
            description:
                - Gets the status indicating whether the primary location of the storage account is available or unavailable.
            sample: available
        status_of_secondary:
            description:
                - Gets the status indicating whether the secondary location of the storage account is available or unavailable.
            sample: available
        primary_location:
            description:
                - Gets the location of the primary data center for the storage account.
            sample: eastus
        primary_endpoints:
            description:
                - Gets the URLs that are used to perform a retrieval of a public blob, queue, or table object.
                - Note that Standard_ZRS and Premium_LRS accounts only return the blob endpoint.
            type: complex
            contains:
                blob:
                    description:
                        - Gets the primary blob endpoint and connection string.
                    type: complex
                    contains:
                        endpoint:
                            description:
                                - Gets the primary blob endpoint.
                            sample: "https://testaccount001.blob.core.windows.net/"
                        connectionstring:
                            description:
                                - Connectionstring of the blob endpoint
                            sample: "DefaultEndpointsProtocol=https;EndpointSuffix=core.windows.net;AccountName=X;AccountKey=X;BlobEndpoint=X"
                queue:
                    description:
                        - Gets the primary queue endpoint and connection string.
                    type: complex
                    contains:
                        endpoint:
                            description:
                                - Gets the primary queue endpoint.
                            sample: "https://testaccount001.queue.core.windows.net/"
                        connectionstring:
                            description:
                                - Connectionstring of the queue endpoint
                            sample: "DefaultEndpointsProtocol=https;EndpointSuffix=core.windows.net;AccountName=X;AccountKey=X;QueueEndpoint=X"
                table:
                    description:
                        - Gets the primary table endpoint and connection string.
                    type: complex
                    contains:
                        endpoint:
                            description:
                                - Gets the primary table endpoint.
                            sample: "https://testaccount001.table.core.windows.net/"
                        connectionstring:
                            description:
                                - Connectionstring of the table endpoint
                            sample: "DefaultEndpointsProtocol=https;EndpointSuffix=core.windows.net;AccountName=X;AccountKey=X;TableEndpoint=X"
        secondary_endpoints:
            description:
                - Gets the URLs that are used to perform a retrieval of a public blob, queue, or table object from the secondary location.
                - Only available if the SKU name is Standard_RAGRS.
            type: complex
            contains:
                blob:
                    description:
                        - Gets the secondary blob endpoint and connection string.
                    type: complex
                    contains:
                        endpoint:
                            description:
                                - Gets the secondary blob endpoint.
                            sample: "https://testaccount001.blob.core.windows.net/"
                        connectionstring:
                            description:
                                - Connectionstring of the blob endpoint
                            sample: "DefaultEndpointsProtocol=https;EndpointSuffix=core.windows.net;AccountName=X;AccountKey=X;BlobEndpoint=X"
                queue:
                    description:
                        - Gets the secondary queue endpoint and connection string.
                    type: complex
                    contains:
                        endpoint:
                            description:
                                - Gets the secondary queue endpoint.
                            sample: "https://testaccount001.queue.core.windows.net/"
                        connectionstring:
                            description:
                                - Connectionstring of the queue endpoint
                            sample: "DefaultEndpointsProtocol=https;EndpointSuffix=core.windows.net;AccountName=X;AccountKey=X;QueueEndpoint=X"
                table:
                    description:
                        - Gets the secondary table endpoint and connection string.
                    type: complex
                    contains:
                        endpoint:
                            description:
                                - Gets the secondary table endpoint.
                            sample: "https://testaccount001.table.core.windows.net/"
                        connectionstring:
                            description:
                                - Connectionstring of the table endpoint
                            sample: "DefaultEndpointsProtocol=https;EndpointSuffix=core.windows.net;AccountName=X;AccountKey=X;TableEndpoint=X"
        tags:
            description:
                - Resource tags.
            type: dict
            sample: { "tag1": "abc" }
        blob_cors:
            description:
                - Blob CORS of blob.
            type: list
'''

try:
    from msrestazure.azure_exceptions import CloudError
except Exception:
    # This is handled in azure_rm_common
    pass

from ansible.module_utils.azure_rm_common import AzureRMModuleBase
from ansible.module_utils._text import to_native


AZURE_OBJECT_CLASS = 'StorageAccount'


class AzureRMStorageAccountFacts(AzureRMModuleBase):
    def __init__(self):

        self.module_arg_spec = dict(
            name=dict(type='str'),
            resource_group=dict(type='str', aliases=['resource_group_name']),
            tags=dict(type='list'),
            show_connection_string=dict(type='bool'),
            show_blob_cors=dict(type='bool')
        )

        self.results = dict(
            changed=False,
            ansible_facts=dict(azure_storageaccounts=[]),
            storageaccounts=[]
        )

        self.name = None
        self.resource_group = None
        self.tags = None
        self.show_connection_string = None
        self.show_blob_cors = None

        super(AzureRMStorageAccountFacts, self).__init__(self.module_arg_spec,
                                                         supports_tags=False,
                                                         facts_module=True)

    def exec_module(self, **kwargs):

        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        if self.name and not self.resource_group:
            self.fail("Parameter error: resource group required when filtering by name.")

        results = []
        if self.name:
            results = self.get_account()
        elif self.resource_group:
            results = self.list_resource_group()
        else:
            results = self.list_all()

        filtered = self.filter_tag(results)

        self.results['ansible_facts']['azure_storageaccounts'] = self.serialize(filtered)
        self.results['ansible_facts']['storageaccounts'] = self.format_to_dict(filtered)
        return self.results

    def get_account(self):
        self.log('Get properties for account {0}'.format(self.name))
        account = None
        try:
            account = self.storage_client.storage_accounts.get_properties(self.resource_group, self.name)
            return [account]
        except CloudError:
            pass
        return []

    def list_resource_group(self):
        self.log('List items')
        try:
            response = self.storage_client.storage_accounts.list_by_resource_group(self.resource_group)
        except Exception as exc:
            self.fail("Error listing for resource group {0} - {1}".format(self.resource_group, str(exc)))

        return response

    def list_all(self):
        self.log('List all items')
        try:
            response = self.storage_client.storage_accounts.list_by_resource_group(self.resource_group)
        except Exception as exc:
            self.fail("Error listing all items - {0}".format(str(exc)))

        return response

    def filter_tag(self, raw):
        return [item for item in raw if self.has_tags(item.tags, self.tags)]

    def serialize(self, raw):
        return [self.serialize_obj(item, AZURE_OBJECT_CLASS) for item in raw]

    def format_to_dict(self, raw):
        return [self.account_obj_to_dict(item) for item in raw]

    def account_obj_to_dict(self, account_obj, blob_service_props=None):
        account_dict = dict(
            id=account_obj.id,
            name=account_obj.name,
            location=account_obj.location,
            access_tier=(account_obj.access_tier.value
                         if account_obj.access_tier is not None else None),
            account_type=account_obj.sku.name.value,
            kind=account_obj.kind.value if account_obj.kind else None,
            provisioning_state=account_obj.provisioning_state.value,
            secondary_location=account_obj.secondary_location,
            status_of_primary=(account_obj.status_of_primary.value
                               if account_obj.status_of_primary is not None else None),
            status_of_secondary=(account_obj.status_of_secondary.value
                                 if account_obj.status_of_secondary is not None else None),
            primary_location=account_obj.primary_location,
            https_only=account_obj.enable_https_traffic_only
        )

        id_dict = self.parse_resource_to_dict(account_obj.id)
        account_dict['resource_group'] = id_dict.get('resource_group')
        account_key = self.get_connectionstring(account_dict['resource_group'], account_dict['name'])
        account_dict['custom_domain'] = None
        if account_obj.custom_domain:
            account_dict['custom_domain'] = dict(
                name=account_obj.custom_domain.name,
                use_sub_domain=account_obj.custom_domain.use_sub_domain
            )

        account_dict['primary_endpoints'] = None
        if account_obj.primary_endpoints:
            account_dict['primary_endpoints'] = dict(
                blob=self.format_endpoint_dict(account_dict['name'], account_key[0], account_obj.primary_endpoints.blob, 'blob'),
                queue=self.format_endpoint_dict(account_dict['name'], account_key[0], account_obj.primary_endpoints.queue, 'queue'),
                table=self.format_endpoint_dict(account_dict['name'], account_key[0], account_obj.primary_endpoints.table, 'table')
            )
        account_dict['secondary_endpoints'] = None
        if account_obj.secondary_endpoints:
            account_dict['secondary_endpoints'] = dict(
                blob=self.format_endpoint_dict(account_dict['name'], account_key[1], account_obj.primary_endpoints.blob, 'blob'),
                queue=self.format_endpoint_dict(account_dict['name'], account_key[1], account_obj.primary_endpoints.queue, 'queue'),
                table=self.format_endpoint_dict(account_dict['name'], account_key[1], account_obj.primary_endpoints.table, 'table'),
            )
        account_dict['tags'] = None
        if account_obj.tags:
            account_dict['tags'] = account_obj.tags
        blob_service_props = self.get_blob_service_props(account_dict['resource_group'], account_dict['name'])
        if blob_service_props and blob_service_props.cors and blob_service_props.cors.cors_rules:
            account_dict['blob_cors'] = [dict(
                allowed_origins=to_native(x.allowed_origins),
                allowed_methods=to_native(x.allowed_methods),
                max_age_in_seconds=x.max_age_in_seconds,
                exposed_headers=to_native(x.exposed_headers),
                allowed_headers=to_native(x.allowed_headers)
            ) for x in blob_service_props.cors.cors_rules]
        return account_dict

    def format_endpoint_dict(self, name, key, endpoint, storagetype, protocol='https'):
        result = dict(endpoint=endpoint)
        if key:
            result['connectionstring'] = 'DefaultEndpointsProtocol={0};EndpointSuffix={1};AccountName={2};AccountKey={3};{4}Endpoint={5}'.format(
                                         protocol,
                                         self._cloud_environment.suffixes.storage_endpoint,
                                         name,
                                         key,
                                         str.title(storagetype),
                                         endpoint)
        return result

    def get_blob_service_props(self, resource_group, name):
        if not self.show_blob_cors:
            return None
        try:
            blob_service_props = self.storage_client.blob_services.get_service_properties(resource_group, name)
            return blob_service_props
        except Exception:
            pass
        return None

    def get_connectionstring(self, resource_group, name):
        keys = ['', '']
        if not self.show_connection_string:
            return keys
        try:
            cred = self.storage_client.storage_accounts.list_keys(resource_group, name)
            # get the following try catch from CLI
            try:
                keys = [cred.keys[0].value, cred.keys[1].value]
            except AttributeError:
                keys = [cred.key1, cred.key2]
        except Exception:
            pass
        return keys


def main():
    AzureRMStorageAccountFacts()


if __name__ == '__main__':
    main()
