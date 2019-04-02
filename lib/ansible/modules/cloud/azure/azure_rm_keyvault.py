#!/usr/bin/python
#
# Copyright (c) 2017 Zim Kalinowski, <zikalino@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_keyvault
version_added: "2.5"
short_description: Manage Key Vault instance.
description:
    - Create, update and delete instance of Key Vault.

options:
    resource_group:
        description:
            - The name of the Resource Group to which the server belongs.
        required: True
    vault_name:
        description:
            - Name of the vault
        required: True
    location:
        description:
            - Resource location. If not set, location from the resource group will be used as default.
    vault_tenant:
        description:
            - The Azure Active Directory tenant ID that should be used for authenticating requests to the key vault.
    sku:
        description:
            - SKU details
        suboptions:
            family:
                description:
                    - SKU family name
            name:
                description:
                    - SKU name to specify whether the key vault is a standard vault or a premium vault.
                required: True
                choices:
                    - 'standard'
                    - 'premium'
    access_policies:
        description:
            - "An array of 0 to 16 identities that have access to the key vault. All identities in the array must use the same tenant ID as the key vault's
               tenant ID."
        suboptions:
            tenant_id:
                description:
                    - The Azure Active Directory tenant ID that should be used for authenticating requests to the key vault.
                    - Current keyvault C(tenant_id) value will be used if not specified.
            object_id:
                description:
                    - "The object ID of a user, service principal or security group in the Azure Active Directory tenant for the vault. The object ID must be
                       unique for the list of access policies."
                    - Please note this is not application id. Object id can be obtained by running "az ad sp show --id <application id>".
                required: True
            application_id:
                description:
                    -  Application ID of the client making request on behalf of a principal
            keys:
                description:
                    - List of permissions to keys
                choices:
                    - 'encrypt'
                    - 'decrypt'
                    - 'wrapkey'
                    - 'unwrapkey'
                    - 'sign'
                    - 'verify'
                    - 'get'
                    - 'list'
                    - 'create'
                    - 'update'
                    - 'import'
                    - 'delete'
                    - 'backup'
                    - 'restore'
                    - 'recover'
                    - 'purge'
            secrets:
                description:
                    - List of permissions to secrets
                choices:
                    - 'get'
                    - 'list'
                    - 'set'
                    - 'delete'
                    - 'backup'
                    - 'restore'
                    - 'recover'
                    - 'purge'
            certificates:
                description:
                    - List of permissions to certificates
                choices:
                    - 'get'
                    - 'list'
                    - 'delete'
                    - 'create'
                    - 'import'
                    - 'update'
                    - 'managecontacts'
                    - 'getissuers'
                    - 'listissuers'
                    - 'setissuers'
                    - 'deleteissuers'
                    - 'manageissuers'
                    - 'recover'
                    - 'purge'
            storage:
                description:
                    - List of permissions to storage accounts
    enabled_for_deployment:
        description:
            - Property to specify whether Azure Virtual Machines are permitted to retrieve certificates stored as secrets from the key vault.
        type: bool
    enabled_for_disk_encryption:
        description:
            - Property to specify whether Azure Disk Encryption is permitted to retrieve secrets from the vault and unwrap keys.
        type: bool
    enabled_for_template_deployment:
        description:
            - Property to specify whether Azure Resource Manager is permitted to retrieve secrets from the key vault.
        type: bool
    enable_soft_delete:
        description:
            - Property to specify whether the soft delete functionality is enabled for this key vault.
        type: bool
    recover_mode:
        description:
            - Create vault in recovery mode.
        type: bool
    state:
        description:
            - Assert the state of the KeyVault. Use C(present) to create or update an KeyVault and C(absent) to delete it.
        default: present
        choices:
            - absent
            - present

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Zim Kalinowski (@zikalino)"

'''

EXAMPLES = '''
  - name: Create instance of Key Vault
    azure_rm_keyvault:
      resource_group: myResourceGroup
      vault_name: samplekeyvault
      enabled_for_deployment: yes
      vault_tenant: 72f98888-8666-4144-9199-2d7cd0111111
      sku:
        name: standard
      access_policies:
        - tenant_id: 72f98888-8666-4144-9199-2d7cd0111111
          object_id: 99998888-8666-4144-9199-2d7cd0111111
          keys:
            - get
            - list
'''

RETURN = '''
id:
    description:
        - The Azure Resource Manager resource ID for the key vault.
    returned: always
    type: str
    sample: id
'''

import collections
import time
from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.keyvault import KeyVaultManagementClient
    from msrest.polling import LROPoller
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass


class Actions:
    NoAction, Create, Update, Delete = range(4)


class AzureRMVaults(AzureRMModuleBase):
    """Configuration class for an Azure RM Key Vault resource"""

    def __init__(self):
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                required=True
            ),
            vault_name=dict(
                type='str',
                required=True
            ),
            location=dict(
                type='str'
            ),
            vault_tenant=dict(
                type='str'
            ),
            sku=dict(
                type='dict'
            ),
            access_policies=dict(
                type='list',
                elements='dict',
                options=dict(
                    tenant_id=dict(type='str'),
                    object_id=dict(type='str', required=True),
                    application_id=dict(type='str'),
                    # FUTURE: add `choices` support once choices supports lists of values
                    keys=dict(type='list'),
                    secrets=dict(type='list'),
                    certificates=dict(type='list'),
                    storage=dict(type='list')
                )
            ),
            enabled_for_deployment=dict(
                type='bool'
            ),
            enabled_for_disk_encryption=dict(
                type='bool'
            ),
            enabled_for_template_deployment=dict(
                type='bool'
            ),
            enable_soft_delete=dict(
                type='bool'
            ),
            recover_mode=dict(
                type='bool'
            ),
            state=dict(
                type='str',
                default='present',
                choices=['present', 'absent']
            )
        )

        self.module_required_if = [['state', 'present', ['vault_tenant']]]

        self.resource_group = None
        self.vault_name = None
        self.parameters = dict()
        self.tags = None

        self.results = dict(changed=False)
        self.mgmt_client = None
        self.state = None
        self.to_do = Actions.NoAction

        super(AzureRMVaults, self).__init__(derived_arg_spec=self.module_arg_spec,
                                            supports_check_mode=True,
                                            supports_tags=True,
                                            required_if=self.module_required_if)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        # translate Ansible input to SDK-formatted dict in self.parameters
        for key in list(self.module_arg_spec.keys()) + ['tags']:
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
            elif kwargs[key] is not None:
                if key == "location":
                    self.parameters["location"] = kwargs[key]
                elif key == "vault_tenant":
                    self.parameters.setdefault("properties", {})["tenant_id"] = kwargs[key]
                elif key == "sku":
                    self.parameters.setdefault("properties", {})["sku"] = kwargs[key]
                elif key == "access_policies":
                    access_policies = kwargs[key]
                    for policy in access_policies:
                        if 'keys' in policy:
                            policy.setdefault("permissions", {})["keys"] = policy["keys"]
                            policy.pop("keys", None)
                        if 'secrets' in policy:
                            policy.setdefault("permissions", {})["secrets"] = policy["secrets"]
                            policy.pop("secrets", None)
                        if 'certificates' in policy:
                            policy.setdefault("permissions", {})["certificates"] = policy["certificates"]
                            policy.pop("certificates", None)
                        if 'storage' in policy:
                            policy.setdefault("permissions", {})["storage"] = policy["storage"]
                            policy.pop("storage", None)
                        if policy.get('tenant_id') is None:
                            # default to key vault's tenant, since that's all that's currently supported anyway
                            policy['tenant_id'] = kwargs['vault_tenant']
                    self.parameters.setdefault("properties", {})["access_policies"] = access_policies
                elif key == "enabled_for_deployment":
                    self.parameters.setdefault("properties", {})["enabled_for_deployment"] = kwargs[key]
                elif key == "enabled_for_disk_encryption":
                    self.parameters.setdefault("properties", {})["enabled_for_disk_encryption"] = kwargs[key]
                elif key == "enabled_for_template_deployment":
                    self.parameters.setdefault("properties", {})["enabled_for_template_deployment"] = kwargs[key]
                elif key == "enable_soft_delete":
                    self.parameters.setdefault("properties", {})["enable_soft_delete"] = kwargs[key]
                elif key == "recover_mode":
                    self.parameters.setdefault("properties", {})["create_mode"] = 'recover' if kwargs[key] else 'default'

        old_response = None
        response = None

        self.mgmt_client = self.get_mgmt_svc_client(KeyVaultManagementClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager,
                                                    api_version="2018-02-14")

        resource_group = self.get_resource_group(self.resource_group)

        if "location" not in self.parameters:
            self.parameters["location"] = resource_group.location

        old_response = self.get_keyvault()

        if not old_response:
            self.log("Key Vault instance doesn't exist")
            if self.state == 'absent':
                self.log("Old instance didn't exist")
            else:
                self.to_do = Actions.Create
        else:
            self.log("Key Vault instance already exists")
            if self.state == 'absent':
                self.to_do = Actions.Delete
            elif self.state == 'present':
                self.log("Need to check if Key Vault instance has to be deleted or may be updated")
                if ('location' in self.parameters) and (self.parameters['location'] != old_response['location']):
                    self.to_do = Actions.Update
                elif ('tenant_id' in self.parameters) and (self.parameters['tenant_id'] != old_response['tenant_id']):
                    self.to_do = Actions.Update
                elif ('enabled_for_deployment' in self.parameters) and (self.parameters['enabled_for_deployment'] != old_response['enabled_for_deployment']):
                    self.to_do = Actions.Update
                elif (('enabled_for_disk_encryption' in self.parameters) and
                        (self.parameters['enabled_for_deployment'] != old_response['enabled_for_deployment'])):
                    self.to_do = Actions.Update
                elif (('enabled_for_template_deployment' in self.parameters) and
                        (self.parameters['enabled_for_template_deployment'] != old_response['enabled_for_template_deployment'])):
                    self.to_do = Actions.Update
                elif ('enable_soft_delete' in self.parameters) and (self.parameters['enabled_soft_delete'] != old_response['enable_soft_delete']):
                    self.to_do = Actions.Update
                elif ('create_mode' in self.parameters) and (self.parameters['create_mode'] != old_response['create_mode']):
                    self.to_do = Actions.Update
                elif 'access_policies' in self.parameters['properties']:
                    if len(self.parameters['properties']['access_policies']) != len(old_response['properties']['access_policies']):
                        self.to_do = Actions.Update
                    else:
                        # FUTURE: this list isn't really order-dependent- we should be set-ifying the rules list for order-independent comparison
                        for i in range(len(old_response['properties']['access_policies'])):
                            n = self.parameters['properties']['access_policies'][i]
                            o = old_response['properties']['access_policies'][i]
                            if n.get('tenant_id', False) != o.get('tenant_id', False):
                                self.to_do = Actions.Update
                                break
                            if n.get('object_id', None) != o.get('object_id', None):
                                self.to_do = Actions.Update
                                break
                            if n.get('application_id', None) != o.get('application_id', None):
                                self.to_do = Actions.Update
                                break
                            if sorted(n.get('keys', [])) != sorted(o.get('keys', [])):
                                self.to_do = Actions.Update
                                break
                            if sorted(n.get('secrets', [])) != sorted(o.get('secrets', [])):
                                self.to_do = Actions.Update
                                break
                            if sorted(n.get('certificates', [])) != sorted(o.get('certificates', [])):
                                self.to_do = Actions.Update
                                break
                            if sorted(n.get('storage', [])) != sorted(o.get('storage', [])):
                                self.to_do = Actions.Update
                                break

                update_tags, newtags = self.update_tags(old_response.get('tags', dict()))

                if update_tags:
                    self.to_do = Actions.Update
                    self.tags = newtags

        if (self.to_do == Actions.Create) or (self.to_do == Actions.Update):
            self.log("Need to Create / Update the Key Vault instance")

            if self.check_mode:
                self.results['changed'] = True
                return self.results

            self.parameters["tags"] = self.tags

            response = self.create_update_keyvault()

            if not old_response:
                self.results['changed'] = True
            else:
                self.results['changed'] = old_response.__ne__(response)
            self.log("Creation / Update done")
        elif self.to_do == Actions.Delete:
            self.log("Key Vault instance deleted")
            self.results['changed'] = True

            if self.check_mode:
                return self.results

            self.delete_keyvault()
            # make sure instance is actually deleted, for some Azure resources, instance is hanging around
            # for some time after deletion -- this should be really fixed in Azure
            while self.get_keyvault():
                time.sleep(20)
        else:
            self.log("Key Vault instance unchanged")
            self.results['changed'] = False
            response = old_response

        if response:
            self.results["id"] = response["id"]

        return self.results

    def create_update_keyvault(self):
        '''
        Creates or updates Key Vault with the specified configuration.

        :return: deserialized Key Vault instance state dictionary
        '''
        self.log("Creating / Updating the Key Vault instance {0}".format(self.vault_name))

        try:
            response = self.mgmt_client.vaults.create_or_update(resource_group_name=self.resource_group,
                                                                vault_name=self.vault_name,
                                                                parameters=self.parameters)
            if isinstance(response, LROPoller):
                response = self.get_poller_result(response)

        except CloudError as exc:
            self.log('Error attempting to create the Key Vault instance.')
            self.fail("Error creating the Key Vault instance: {0}".format(str(exc)))
        return response.as_dict()

    def delete_keyvault(self):
        '''
        Deletes specified Key Vault instance in the specified subscription and resource group.

        :return: True
        '''
        self.log("Deleting the Key Vault instance {0}".format(self.vault_name))
        try:
            response = self.mgmt_client.vaults.delete(resource_group_name=self.resource_group,
                                                      vault_name=self.vault_name)
        except CloudError as e:
            self.log('Error attempting to delete the Key Vault instance.')
            self.fail("Error deleting the Key Vault instance: {0}".format(str(e)))

        return True

    def get_keyvault(self):
        '''
        Gets the properties of the specified Key Vault.

        :return: deserialized Key Vault instance state dictionary
        '''
        self.log("Checking if the Key Vault instance {0} is present".format(self.vault_name))
        found = False
        try:
            response = self.mgmt_client.vaults.get(resource_group_name=self.resource_group,
                                                   vault_name=self.vault_name)
            found = True
            self.log("Response : {0}".format(response))
            self.log("Key Vault instance : {0} found".format(response.name))
        except CloudError as e:
            self.log('Did not find the Key Vault instance.')
        if found is True:
            return response.as_dict()

        return False


def main():
    """Main execution"""
    AzureRMVaults()


if __name__ == '__main__':
    main()
