#!/usr/bin/python
#
# Copyright (c) 2017 Julien Stroheker, <juliens@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_acr
version_added: "2.4"
short_description: Manage an Azure Container Registry (ACR).
description:
    - Create, update and delete an Azure Container Registry.

options:
    resource_group:
        description:
            - Name of a resource group where the Container Registry exists or will be created.
        required: true
    name:
        description:
            - Name of the Container Registry.
        required: true
        default: null
    state:
        description:
            - Assert the state of the ACR. Use 'present' to create or update an ACR and 'absent' to delete it.
        default: present
        choices:
            - absent
            - present
        required: false
    location:
        description:
            - Valid azure location. Defaults to location of the resource group.
        default: resource_group location
        required: false
    admin_user_enabled:
        description:
            - If enabled, you can use the registry name as username and admin user access key as password to docker login to your container registry.
        default: False
        required: false
    sku:
        description:
            - Specifies the SKU to use. Currently can be either Classic, Basic, Standard or Premium.
        default: Standard
        choices:
            - Classic
            - Basic
            - Standard
            - Premium
        required: false

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Yawei Wang (@yaweiw)"

'''

EXAMPLES = '''
    - name: Create an azure container registry
      azure_rm_acr:
        name: testacr1
        location: eastus
        resource_group: testrg
        state: present
        admin_user_enabled: True
        sku: Premium
        tags:
            Release: beta1
            Environment: Production

# Deletes the specified container registry in the specified subscription and resource group.
    - name: Remove an azure container registry
      azure_rm_acr:
        name: testacr2
        location: eastus
        resource_group: testrg
        state: absent
        sku: Standard
        tags:
            Ansible: azure_rm_acr
'''
RETURN = '''
state:
    description: Current state of the azure container registry
    returned: always
    type: dict
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase
from enum import Enum

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.containerregistry.models import (
        Registry,
        RegistryUpdateParameters,
        StorageAccountProperties,
        Sku,
        SkuName,
        SkuTier,
        ProvisioningState,
        PasswordName,
        WebhookCreateParameters,
        WebhookUpdateParameters,
        WebhookAction,
        WebhookStatus
    )
    from azure.mgmt.containerregistry import ContainerRegistryManagementClient
    import azure.mgmt.storage
except ImportError as exc:
    # This is handled in azure_rm_common
    print("import error {0}".format(str(exc)) + u'\n')

    pass


def create_acr_dict(registry):
    '''
    Helper method to deserialize a ContainerRegistry to a dict
    :param: acr: return object from Azure rest API call
    :return: dict with the state on Azure
    '''
    results = dict(
        id=registry.id,
        name=registry.name,
        location=registry.location,
        admin_user_enabled=registry.admin_user_enabled,
        sku=registry.sku.name,
        provisioning_state=registry.provisioning_state,
        tags=registry.tags
    )
    return results

class Actions:
    NoAction, Create, Update = range(3)

class AzureRMContainerRegistry(AzureRMModuleBase):
    """Configuration class for an Azure RM container registry resource"""

    def __init__(self):
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                required=True
            ),
            name=dict(
                type='str',
                required=True
            ),
            state=dict(
                type='str',
                required=False,
                default='present',
                choices=['present', 'absent']
            ),
            location=dict(
                type='str',
                required=False
            ),
            admin_user_enabled=dict(
                type='bool',
                required=False,
                default=False
            ),
            sku=dict(
                type='str',
                required=False,
                choices=['Classic', 'Basic', 'Standard', 'Premium']
            )
        )

        self.resource_group = None
        self.name = None
        self.location = None
        self.tags = None
        self.state = None
        self.sku = None
        self.tags = None
        self._containerregistry_mgmt_client = None

        self.results = dict(changed=False, state=dict())

        super(AzureRMContainerRegistry, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                      supports_check_mode=True,
                                                      supports_tags=True)

    def exec_module(self, **kwargs):
        """Main module execution method"""


        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])
            
        resource_group = None
        response = None
        to_do = Actions.NoAction

        try:
            resource_group = self.get_resource_group(self.resource_group)
        except CloudError:
            self.fail('resource group {} not found'.format(self.resource_group))
        if not self.location:
            self.location = resource_group.location

        # Check if the ACR instance already present in the RG
        if self.state == 'present':
            response = self.get_acr()
            self.results['state'] = response

            if not response:
                to_do = Actions.Create
            else:
                self.log('Results : {0}'.format(response))
                if response['provisioning_state'] == "Succeeded":
                    to_do = Actions.Update
                else:
                    to_do = Actions.NoAction

            self.log("Create / Update the ACR instance")
            if self.check_mode:
                return self.results

            self.results['state'] = self.create_update_acr(to_do)
            self.results['changed'] = True
            self.log("Action done")
        elif self.state == 'absent':
            self.delete_acr()
            self.log("ACR instance deleted")

        return self.results

    def create_update_acr(self, to_do):
        '''
        Creates or updates a container registry.

        :return: deserialized ACR instance state dictionary
        '''
        self.log("Creating / Updating the ACR instance {0}".format(self.name))

        try:
            if to_do != Actions.NoAction:
                if to_do == Actions.Create:
                    poller = self.containerregistry_mgmt_client.registries.create(
                        resource_group_name=self.resource_group,
                        registry_name=self.name,
                        registry=Registry(
                            location=self.location,
                            sku=Sku(
                                name=self.sku
                            ),
                            tags=self.tags,
                            admin_user_enabled=self.admin_user_enabled
                        )
                    )
                else:
                    poller = self.containerregistry_mgmt_client.registries.update(
                        resource_group_name=self.resource_group,
                        registry_name=self.name,
                        registry_update_parameters=RegistryUpdateParameters(
                            sku=Sku(
                                name=self.sku
                            ),
                            tags=self.tags,
                            admin_user_enabled=self.admin_user_enabled
                        )
                    )
                response = self.get_poller_result(poller)
            else:
                response = None
        except CloudError as exc:
            self.log('Error attempting to create the ACR instance.')
            self.fail("Error creating the ACR instance: {0}".format(str(exc)))
        return create_acr_dict(response)

    def delete_acr(self):
        '''
        Deletes the specified container registry in the specified subscription and resource group.

        :return: True
        '''
        self.log("Deleting the ACR instance {0}".format(self.name))
        try:
            self.containerregistry_mgmt_client.registries.delete(self.resource_group, self.name).wait()
        except CloudError as e:
            self.log('Error attempting to delete the ACR instance.')
            self.fail("Error deleting the ACR instance: {0}".format(str(e)))

        return True

    def get_acr(self):
        '''
        Gets the properties of the specified container registry.

        :return: deserialized ACR state dictionary
        '''
        self.log("Checking if the ACR instance {0} is present".format(self.name))
        found = False
        try:
            response = self.containerregistry_mgmt_client.registries.get(self.resource_group, self.name)
            found = True
            self.log("Response : {0}".format(response))
            self.log("ACR instance : {0} found".format(response.name))
        except CloudError as e:
            self.log('Did not find the ACR instance.')
        if found is True:
            return create_acr_dict(response)
        else:
            return False
    
    @property
    def containerregistry_mgmt_client(self):
        self.log('Getting container registry mgmt client')
        if not self._containerregistry_mgmt_client:
            self._containerregistry_mgmt_client = ContainerRegistryManagementClient(
                self.azure_credentials,
                self.subscription_id
            )
        return self._containerregistry_mgmt_client

def main():
    """Main execution"""
    AzureRMContainerRegistry()

if __name__ == '__main__':
    main()
