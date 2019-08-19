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
module: azure_rm_storageaccount
version_added: "2.1"
short_description: Manage Azure storage accounts
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
            - State of the storage account. Use C(present) to create or update a storage account and use C(absent) to delete an account.
        default: present
        choices:
            - absent
            - present
    location:
        description:
            - Valid Azure location. Defaults to location of the resource group.
    account_type:
        description:
            - Type of storage account. Required when creating a storage account.
            - C(Standard_ZRS) and C(Premium_LRS) accounts cannot be changed to other account types.
            - Other account types cannot be changed to C(Standard_ZRS) or C(Premium_LRS).
        choices:
            - Premium_LRS
            - Standard_GRS
            - Standard_LRS
            - StandardSSD_LRS
            - Standard_RAGRS
            - Standard_ZRS
            - Premium_ZRS
        aliases:
            - type
    custom_domain:
        description:
            - User domain assigned to the storage account.
            - Must be a dictionary with I(name) and I(use_sub_domain) keys where I(name) is the CNAME source.
            - Only one custom domain is supported per storage account at this time.
            - To clear the existing custom domain, use an empty string for the custom domain name property.
            - Can be added to an existing storage account. Will be ignored during storage account creation.
        aliases:
            - custom_dns_domain_suffix
    kind:
        description:
            - The kind of storage.
        default: 'Storage'
        choices:
            - Storage
            - StorageV2
            - BlobStorage
        version_added: "2.2"
    access_tier:
        description:
            - The access tier for this storage account. Required when I(kind=BlobStorage).
        choices:
            - Hot
            - Cool
        version_added: "2.4"
    force_delete_nonempty:
        description:
            - Attempt deletion if resource already exists and cannot be updated.
        type: bool
        aliases:
            - force
    https_only:
        description:
            -  Allows https traffic only to storage service when set to C(true).
        type: bool
        version_added: "2.8"
    blob_cors:
        description:
            - Specifies CORS rules for the Blob service.
            - You can include up to five CorsRule elements in the request.
            - If no blob_cors elements are included in the argument list, nothing about CORS will be changed.
            - If you want to delete all CORS rules and disable CORS for the Blob service, explicitly set I(blob_cors=[]).
        type: list
        version_added: "2.8"
        suboptions:
            allowed_origins:
                description:
                    - A list of origin domains that will be allowed via CORS, or "*" to allow all domains.
                type: list
                required: true
            allowed_methods:
                description:
                    - A list of HTTP methods that are allowed to be executed by the origin.
                type: list
                required: true
            max_age_in_seconds:
                description:
                    - The number of seconds that the client/browser should cache a preflight response.
                type: int
                required: true
            exposed_headers:
                description:
                    - A list of response headers to expose to CORS clients.
                type: list
                required: true
            allowed_headers:
                description:
                    - A list of headers allowed to be part of the cross-origin request.
                type: list
                required: true

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - Chris Houseknecht (@chouseknecht)
    - Matt Davis (@nitzmahone)
'''

EXAMPLES = '''
    - name: remove account, if it exists
      azure_rm_storageaccount:
        resource_group: myResourceGroup
        name: clh0002
        state: absent

    - name: create an account
      azure_rm_storageaccount:
        resource_group: myResourceGroup
        name: clh0002
        type: Standard_RAGRS
        tags:
          testing: testing
          delete: on-exit

    - name: create an account with blob CORS
      azure_rm_storageaccount:
        resource_group: myResourceGroup
        name: clh002
        type: Standard_RAGRS
        blob_cors:
            - allowed_origins:
                - http://www.example.com/
              allowed_methods:
                - GET
                - POST
              allowed_headers:
                - x-ms-meta-data*
                - x-ms-meta-target*
                - x-ms-meta-abc
              exposed_headers:
                - x-ms-meta-*
              max_age_in_seconds: 200
'''


RETURN = '''
state:
    description:
        - Current state of the storage account.
    returned: always
    type: complex
    contains:
        account_type:
            description:
                - Type of storage account.
            returned: always
            type: str
            sample: Standard_RAGRS
        custom_domain:
            description:
                - User domain assigned to the storage account.
            returned: always
            type: complex
            contains:
                name:
                    description:
                        - CNAME source.
                    returned: always
                    type: str
                    sample: testaccount
                use_sub_domain:
                    description:
                        - Whether to use sub domain.
                    returned: always
                    type: bool
                    sample: true
        id:
            description:
                - Resource ID.
            returned: always
            type: str
            sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Storage/storageAccounts/clh0003"
        location:
            description:
                - Valid Azure location. Defaults to location of the resource group.
            returned: always
            type: str
            sample: eastus2
        name:
            description:
                - Name of the storage account to update or create.
            returned: always
            type: str
            sample: clh0003
        primary_endpoints:
            description:
                - The URLs to retrieve the public I(blob), I(queue), or I(table) object from the primary location.
            returned: always
            type: dict
            sample: {
                    "blob": "https://clh0003.blob.core.windows.net/",
                    "queue": "https://clh0003.queue.core.windows.net/",
                    "table": "https://clh0003.table.core.windows.net/"
                    }
        primary_location:
            description:
                - The location of the primary data center for the storage account.
            returned: always
            type: str
            sample: eastus2
        provisioning_state:
            description:
                - The status of the storage account.
                - Possible values include C(Creating), C(ResolvingDNS), C(Succeeded).
            returned: always
            type: str
            sample: Succeeded
        resource_group:
            description:
                - The resource group's name.
            returned: always
            type: str
            sample: Testing
        secondary_endpoints:
            description:
                - The URLs to retrieve the public I(blob), I(queue), or I(table) object from the secondary location.
            returned: always
            type: dict
            sample: {
                    "blob": "https://clh0003-secondary.blob.core.windows.net/",
                    "queue": "https://clh0003-secondary.queue.core.windows.net/",
                    "table": "https://clh0003-secondary.table.core.windows.net/"
                    }
        secondary_location:
            description:
                - The location of the geo-replicated secondary for the storage account.
            returned: always
            type: str
            sample: centralus
        status_of_primary:
            description:
                - The status of the primary location of the storage account; either C(available) or C(unavailable).
            returned: always
            type: str
            sample: available
        status_of_secondary:
            description:
                - The status of the secondary location of the storage account; either C(available) or C(unavailable).
            returned: always
            type: str
            sample: available
        tags:
            description:
                - Resource tags.
            returned: always
            type: dict
            sample: { 'tags1': 'value1' }
        type:
            description:
                - The storage account type.
            returned: always
            type: str
            sample: "Microsoft.Storage/storageAccounts"
'''

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.storage.cloudstorageaccount import CloudStorageAccount
    from azure.common import AzureMissingResourceHttpError
except ImportError:
    # This is handled in azure_rm_common
    pass

import copy
from ansible.module_utils.azure_rm_common import AZURE_SUCCESS_STATE, AzureRMModuleBase
from ansible.module_utils._text import to_native

cors_rule_spec = dict(
    allowed_origins=dict(type='list', elements='str', required=True),
    allowed_methods=dict(type='list', elements='str', required=True),
    max_age_in_seconds=dict(type='int', required=True),
    exposed_headers=dict(type='list', elements='str', required=True),
    allowed_headers=dict(type='list', elements='str', required=True),
)


def compare_cors(cors1, cors2):
    if len(cors1) != len(cors2):
        return False
    copy2 = copy.copy(cors2)
    for rule1 in cors1:
        matched = False
        for rule2 in copy2:
            if (rule1['max_age_in_seconds'] == rule2['max_age_in_seconds']
                    and set(rule1['allowed_methods']) == set(rule2['allowed_methods'])
                    and set(rule1['allowed_origins']) == set(rule2['allowed_origins'])
                    and set(rule1['allowed_headers']) == set(rule2['allowed_headers'])
                    and set(rule1['exposed_headers']) == set(rule2['exposed_headers'])):
                matched = True
                copy2.remove(rule2)
        if not matched:
            return False
    return True


class AzureRMStorageAccount(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            account_type=dict(type='str',
                              choices=['Premium_LRS', 'Standard_GRS', 'Standard_LRS', 'StandardSSD_LRS', 'Standard_RAGRS', 'Standard_ZRS', 'Premium_ZRS'],
                              aliases=['type']),
            custom_domain=dict(type='dict', aliases=['custom_dns_domain_suffix']),
            location=dict(type='str'),
            name=dict(type='str', required=True),
            resource_group=dict(required=True, type='str', aliases=['resource_group_name']),
            state=dict(default='present', choices=['present', 'absent']),
            force_delete_nonempty=dict(type='bool', default=False, aliases=['force']),
            tags=dict(type='dict'),
            kind=dict(type='str', default='Storage', choices=['Storage', 'StorageV2', 'BlobStorage']),
            access_tier=dict(type='str', choices=['Hot', 'Cool']),
            https_only=dict(type='bool', default=False),
            blob_cors=dict(type='list', options=cors_rule_spec, elements='dict')
        )

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
        self.force_delete_nonempty = None
        self.kind = None
        self.access_tier = None
        self.https_only = None
        self.blob_cors = None

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
        blob_service_props = None
        account_dict = None

        try:
            account_obj = self.storage_client.storage_accounts.get_properties(self.resource_group, self.name)
            blob_service_props = self.storage_client.blob_services.get_service_properties(self.resource_group, self.name)
        except CloudError:
            pass

        if account_obj:
            account_dict = self.account_obj_to_dict(account_obj, blob_service_props)

        return account_dict

    def account_obj_to_dict(self, account_obj, blob_service_props=None):
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
            primary_location=account_obj.primary_location,
            https_only=account_obj.enable_https_traffic_only
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
        if blob_service_props and blob_service_props.cors and blob_service_props.cors.cors_rules:
            account_dict['blob_cors'] = [dict(
                allowed_origins=[to_native(y) for y in x.allowed_origins],
                allowed_methods=[to_native(y) for y in x.allowed_methods],
                max_age_in_seconds=x.max_age_in_seconds,
                exposed_headers=[to_native(y) for y in x.exposed_headers],
                allowed_headers=[to_native(y) for y in x.allowed_headers]
            ) for x in blob_service_props.cors.cors_rules]
        return account_dict

    def update_account(self):
        self.log('Update storage account {0}'.format(self.name))
        if bool(self.https_only) != bool(self.account_dict.get('https_only')):
            self.results['changed'] = True
            self.account_dict['https_only'] = self.https_only
            if not self.check_mode:
                try:
                    parameters = self.storage_models.StorageAccountUpdateParameters(enable_https_traffic_only=self.https_only)
                    self.storage_client.storage_accounts.update(self.resource_group,
                                                                self.name,
                                                                parameters)
                except Exception as exc:
                    self.fail("Failed to update account type: {0}".format(str(exc)))

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
                        sku = self.storage_models.Sku(name=SkuName(self.account_dict['sku_name']))
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

        if self.blob_cors and not compare_cors(self.account_dict.get('blob_cors', []), self.blob_cors):
            self.results['changed'] = True
            if not self.check_mode:
                self.set_blob_cors()

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
                enable_https_traffic_only=self.https_only,
                tags=dict()
            )
            if self.tags:
                account_dict['tags'] = self.tags
            if self.blob_cors:
                account_dict['blob_cors'] = self.blob_cors
            return account_dict
        sku = self.storage_models.Sku(name=self.storage_models.SkuName(self.account_type))
        sku.tier = self.storage_models.SkuTier.standard if 'Standard' in self.account_type else \
            self.storage_models.SkuTier.premium
        parameters = self.storage_models.StorageAccountCreateParameters(sku=sku,
                                                                        kind=self.kind,
                                                                        location=self.location,
                                                                        tags=self.tags,
                                                                        access_tier=self.access_tier)
        self.log(str(parameters))
        try:
            poller = self.storage_client.storage_accounts.create(self.resource_group, self.name, parameters)
            self.get_poller_result(poller)
        except CloudError as e:
            self.log('Error creating storage account.')
            self.fail("Failed to create account: {0}".format(str(e)))
        if self.blob_cors:
            self.set_blob_cors()
        # the poller doesn't actually return anything
        return self.get_account()

    def delete_account(self):
        if self.account_dict['provisioning_state'] == self.storage_models.ProvisioningState.succeeded.value and \
           not self.force_delete_nonempty and self.account_has_blob_containers():
            self.fail("Account contains blob containers. Is it in use? Use the force_delete_nonempty option to attempt deletion.")

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

    def set_blob_cors(self):
        try:
            cors_rules = self.storage_models.CorsRules(cors_rules=[self.storage_models.CorsRule(**x) for x in self.blob_cors])
            self.storage_client.blob_services.set_service_properties(self.resource_group,
                                                                     self.name,
                                                                     self.storage_models.BlobServiceProperties(cors=cors_rules))
        except Exception as exc:
            self.fail("Failed to set CORS rules: {0}".format(str(exc)))


def main():
    AzureRMStorageAccount()


if __name__ == '__main__':
    main()
