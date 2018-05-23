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
module: azure_rm_storageaccount
version_added: "2.1"
short_description: Manage Azure storage accounts.
description:
    - Create, update or delete a storage account.
options:
    resource_group:
        description:
            - Name of the resource group to use.
        required: true
        aliases:
            - resource_group_name
    name:
        description:
            - Name of the storage account to update or create.
    state:
        description:
            - Assert the state of the storage account. Use 'present' to create or update a storage account and
              'absent' to delete an account.
        default: present
        choices:
            - absent
            - present
    location:
        description:
            - Valid azure location. Defaults to location of the resource group.
    account_type:
        description:
            - "Type of storage account. Required when creating a storage account. NOTE: Standard_ZRS and Premium_LRS
              accounts cannot be changed to other account types, and other account types cannot be changed to
              Standard_ZRS or Premium_LRS."
        choices:
            - Premium_LRS
            - Standard_GRS
            - Standard_LRS
            - Standard_RAGRS
            - Standard_ZRS
        aliases:
            - type
    custom_domain:
        description:
            - User domain assigned to the storage account. Must be a dictionary with 'name' and 'use_sub_domain'
              keys where 'name' is the CNAME source. Only one custom domain is supported per storage account at this
              time. To clear the existing custom domain, use an empty string for the custom domain name property.
            - Can be added to an existing storage account. Will be ignored during storage account creation.
    kind:
        description:
            - The 'kind' of storage.
        default: 'Storage'
        choices:
            - Storage
            - BlobStorage
        version_added: "2.2"
    access_tier:
        description:
            - The access tier for this storage account. Required for a storage account of kind 'BlobStorage'.
        choices:
            - Hot
            - Cool
        version_added: "2.4"
    force:
        description:
            - Attempt deletion if resource already exists and cannot be updated
        type: bool
        version_added: "2.6"

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Chris Houseknecht (@chouseknecht)"
    - "Matt Davis (@nitzmahone)"

'''

EXAMPLES = '''
    - name: remove account, if it exists
      azure_rm_storageaccount:
        resource_group: Testing
        name: clh0002
        state: absent

    - name: create an account
      azure_rm_storageaccount:
        resource_group: Testing
        name: clh0002
        type: Standard_RAGRS
        tags:
          - testing: testing
          - delete: on-exit
'''


RETURN = '''
state:
    description: Current state of the storage account.
    returned: always
    type: dict
    sample: {
        "account_type": "Standard_RAGRS",
        "custom_domain": null,
        "id": "/subscriptions/XXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXX/resourceGroups/testing/providers/Microsoft.Storage/storageAccounts/clh0003",
        "location": "eastus2",
        "name": "clh0003",
        "primary_endpoints": {
            "blob": "https://clh0003.blob.core.windows.net/",
            "queue": "https://clh0003.queue.core.windows.net/",
            "table": "https://clh0003.table.core.windows.net/"
        },
        "primary_location": "eastus2",
        "provisioning_state": "Succeeded",
        "resource_group": "Testing",
        "secondary_endpoints": {
            "blob": "https://clh0003-secondary.blob.core.windows.net/",
            "queue": "https://clh0003-secondary.queue.core.windows.net/",
            "table": "https://clh0003-secondary.table.core.windows.net/"
        },
        "secondary_location": "centralus",
        "status_of_primary": "Available",
        "status_of_secondary": "Available",
        "tags": null,
        "type": "Microsoft.Storage/storageAccounts"
    }
'''

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.storage.cloudstorageaccount import CloudStorageAccount
    from azure.common import AzureMissingResourceHttpError
except ImportError:
    # This is handled in azure_rm_common
    pass

from ansible.module_utils.azure_rm_common import AZURE_SUCCESS_STATE, AzureRMModuleBase, HAS_AZURE


class AzureRMStorageAccount(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            account_type=dict(type='str', choices=[], aliases=['type']),
            custom_domain=dict(type='dict'),
            location=dict(type='str'),
            name=dict(type='str', required=True),
            resource_group=dict(required=True, type='str', aliases=['resource_group_name']),
            state=dict(default='present', choices=['present', 'absent']),
            force=dict(type='bool', default=False),
            tags=dict(type='dict'),
            kind=dict(type='str', default='Storage', choices=['Storage', 'BlobStorage']),
            access_tier=dict(type='str', choices=['Hot', 'Cool'])
        )

        if HAS_AZURE:
            for key in self.storage_models.SkuName:
                self.module_arg_spec['account_type']['choices'].append(getattr(key, 'value'))

        self.results = dict(
            changed=False,
            state=dict()
        )

        self.account_dict = None
        self.resource_group = None
        self.name = None
        self.state = None
        self.location = None
        self.account_type = None
        self.custom_domain = None
        self.tags = None
        self.force = None
        self.kind = None
        self.access_tier = None

        super(AzureRMStorageAccount, self).__init__(self.module_arg_spec,
                                                    supports_check_mode=True)

    def exec_module(self, **kwargs):

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        resource_group = self.get_resource_group(self.resource_group)
        if not self.location:
            # Set default location
            self.location = resource_group.location

        if len(self.name) < 3 or len(self.name) > 24:
            self.fail("Parameter error: name length must be between 3 and 24 characters.")

        if self.custom_domain:
            if self.custom_domain.get('name', None) is None:
                self.fail("Parameter error: expecting custom_domain to have a name attribute of type string.")
            if self.custom_domain.get('use_sub_domain', None) is None:
                self.fail("Parameter error: expecting custom_domain to have a use_sub_domain "
                          "attribute of type boolean.")

        self.account_dict = self.get_account()

        if self.state == 'present' and self.account_dict and \
           self.account_dict['provisioning_state'] != AZURE_SUCCESS_STATE:
            self.fail("Error: storage account {0} has not completed provisioning. State is {1}. Expecting state "
                      "to be {2}.".format(self.name, self.account_dict['provisioning_state'], AZURE_SUCCESS_STATE))

        if self.account_dict is not None:
            self.results['state'] = self.account_dict
        else:
            self.results['state'] = dict()

        if self.state == 'present':
            if not self.account_dict:
                self.results['state'] = self.create_account()
            else:
                self.update_account()
        elif self.state == 'absent' and self.account_dict:
            self.delete_account()
            self.results['state'] = dict(Status='Deleted')

        return self.results

    def check_name_availability(self):
        self.log('Checking name availability for {0}'.format(self.name))
        try:
            response = self.storage_client.storage_accounts.check_name_availability(self.name)
        except CloudError as e:
            self.log('Error attempting to validate name.')
            self.fail("Error checking name availability: {0}".format(str(e)))
        if not response.name_available:
            self.log('Error name not available.')
            self.fail("{0} - {1}".format(response.message, response.reason))

    def get_account(self):
        self.log('Get properties for account {0}'.format(self.name))
        account_obj = None
        account_dict = None

        try:
            account_obj = self.storage_client.storage_accounts.get_properties(self.resource_group, self.name)
        except CloudError:
            pass

        if account_obj:
            account_dict = self.account_obj_to_dict(account_obj)

        return account_dict

    def account_obj_to_dict(self, account_obj):
        account_dict = dict(
            id=account_obj.id,
            name=account_obj.name,
            location=account_obj.location,
            resource_group=self.resource_group,
            type=account_obj.type,
            access_tier=(account_obj.access_tier.value
                         if account_obj.access_tier is not None else None),
            sku_tier=account_obj.sku.tier.value,
            sku_name=account_obj.sku.name.value,
            provisioning_state=account_obj.provisioning_state.value,
            secondary_location=account_obj.secondary_location,
            status_of_primary=(account_obj.status_of_primary.value
                               if account_obj.status_of_primary is not None else None),
            status_of_secondary=(account_obj.status_of_secondary.value
                                 if account_obj.status_of_secondary is not None else None),
            primary_location=account_obj.primary_location
        )
        account_dict['custom_domain'] = None
        if account_obj.custom_domain:
            account_dict['custom_domain'] = dict(
                name=account_obj.custom_domain.name,
                use_sub_domain=account_obj.custom_domain.use_sub_domain
            )

        account_dict['primary_endpoints'] = None
        if account_obj.primary_endpoints:
            account_dict['primary_endpoints'] = dict(
                blob=account_obj.primary_endpoints.blob,
                queue=account_obj.primary_endpoints.queue,
                table=account_obj.primary_endpoints.table
            )
        account_dict['secondary_endpoints'] = None
        if account_obj.secondary_endpoints:
            account_dict['secondary_endpoints'] = dict(
                blob=account_obj.secondary_endpoints.blob,
                queue=account_obj.secondary_endpoints.queue,
                table=account_obj.secondary_endpoints.table
            )
        account_dict['tags'] = None
        if account_obj.tags:
            account_dict['tags'] = account_obj.tags
        return account_dict

    def update_account(self):
        self.log('Update storage account {0}'.format(self.name))
        if self.account_type:
            if self.account_type != self.account_dict['sku_name']:
                # change the account type
                SkuName = self.storage_models.SkuName
                if self.account_dict['sku_name'] in [SkuName.premium_lrs, SkuName.standard_zrs]:
                    self.fail("Storage accounts of type {0} and {1} cannot be changed.".format(
                        SkuName.premium_lrs, SkuName.standard_zrs))
                if self.account_type in [SkuName.premium_lrs, SkuName.standard_zrs]:
                    self.fail("Storage account of type {0} cannot be changed to a type of {1} or {2}.".format(
                        self.account_dict['sku_name'], SkuName.premium_lrs, SkuName.standard_zrs))

                self.results['changed'] = True
                self.account_dict['sku_name'] = self.account_type

                if self.results['changed'] and not self.check_mode:
                    # Perform the update. The API only allows changing one attribute per call.
                    try:
                        self.log("sku_name: %s" % self.account_dict['sku_name'])
                        self.log("sku_tier: %s" % self.account_dict['sku_tier'])
                        sku = self.storage_models.Sku(SkuName(self.account_dict['sku_name']))
                        sku.tier = self.storage_models.SkuTier(self.account_dict['sku_tier'])
                        parameters = self.storage_models.StorageAccountUpdateParameters(sku=sku)
                        self.storage_client.storage_accounts.update(self.resource_group,
                                                                    self.name,
                                                                    parameters)
                    except Exception as exc:
                        self.fail("Failed to update account type: {0}".format(str(exc)))

        if self.custom_domain:
            if not self.account_dict['custom_domain'] or self.account_dict['custom_domain'] != self.custom_domain:
                self.results['changed'] = True
                self.account_dict['custom_domain'] = self.custom_domain

            if self.results['changed'] and not self.check_mode:
                new_domain = self.storage_models.CustomDomain(name=self.custom_domain['name'],
                                                              use_sub_domain=self.custom_domain['use_sub_domain'])
                parameters = self.storage_models.StorageAccountUpdateParameters(custom_domain=new_domain)
                try:
                    self.storage_client.storage_accounts.update(self.resource_group, self.name, parameters)
                except Exception as exc:
                    self.fail("Failed to update custom domain: {0}".format(str(exc)))

        if self.access_tier:
            if not self.account_dict['access_tier'] or self.account_dict['access_tier'] != self.access_tier:
                self.results['changed'] = True
                self.account_dict['access_tier'] = self.access_tier

            if self.results['changed'] and not self.check_mode:
                parameters = self.storage_models.StorageAccountUpdateParameters(access_tier=self.access_tier)
                try:
                    self.storage_client.storage_accounts.update(self.resource_group, self.name, parameters)
                except Exception as exc:
                    self.fail("Failed to update access tier: {0}".format(str(exc)))

        update_tags, self.account_dict['tags'] = self.update_tags(self.account_dict['tags'])
        if update_tags:
            self.results['changed'] = True
            if not self.check_mode:
                parameters = self.storage_models.StorageAccountUpdateParameters(tags=self.account_dict['tags'])
                try:
                    self.storage_client.storage_accounts.update(self.resource_group, self.name, parameters)
                except Exception as exc:
                    self.fail("Failed to update tags: {0}".format(str(exc)))

    def create_account(self):
        self.log("Creating account {0}".format(self.name))

        if not self.location:
            self.fail('Parameter error: location required when creating a storage account.')

        if not self.account_type:
            self.fail('Parameter error: account_type required when creating a storage account.')

        if not self.access_tier and self.kind == 'BlobStorage':
            self.fail('Parameter error: access_tier required when creating a storage account of type BlobStorage.')

        self.check_name_availability()
        self.results['changed'] = True

        if self.check_mode:
            account_dict = dict(
                location=self.location,
                account_type=self.account_type,
                name=self.name,
                resource_group=self.resource_group,
                tags=dict()
            )
            if self.tags:
                account_dict['tags'] = self.tags
            return account_dict
        sku = self.storage_models.Sku(self.storage_models.SkuName(self.account_type))
        sku.tier = self.storage_models.SkuTier.standard if 'Standard' in self.account_type else \
            self.storage_models.SkuTier.premium
        parameters = self.storage_models.StorageAccountCreateParameters(sku, self.kind, self.location,
                                                                        tags=self.tags, access_tier=self.access_tier)
        self.log(str(parameters))
        try:
            poller = self.storage_client.storage_accounts.create(self.resource_group, self.name, parameters)
            self.get_poller_result(poller)
        except CloudError as e:
            self.log('Error creating storage account.')
            self.fail("Failed to create account: {0}".format(str(e)))
        # the poller doesn't actually return anything
        return self.get_account()

    def delete_account(self):
        if self.account_dict['provisioning_state'] == self.storage_models.ProvisioningState.succeeded.value and \
           self.account_has_blob_containers() and self.force:
            self.fail("Account contains blob containers. Is it in use? Use the force option to attempt deletion.")

        self.log('Delete storage account {0}'.format(self.name))
        self.results['changed'] = True
        if not self.check_mode:
            try:
                status = self.storage_client.storage_accounts.delete(self.resource_group, self.name)
                self.log("delete status: ")
                self.log(str(status))
            except CloudError as e:
                self.fail("Failed to delete the account: {0}".format(str(e)))
        return True

    def account_has_blob_containers(self):
        '''
        If there are blob containers, then there are likely VMs depending on this account and it should
        not be deleted.
        '''
        self.log('Checking for existing blob containers')
        blob_service = self.get_blob_client(self.resource_group, self.name)
        try:
            response = blob_service.list_containers()
        except AzureMissingResourceHttpError:
            # No blob storage available?
            return False

        if len(response.items) > 0:
            return True
        return False


def main():
    AzureRMStorageAccount()

if __name__ == '__main__':
    main()
