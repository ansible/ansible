#!/usr/bin/python
#
# Copyright (c) 2017 Yawei Wang, <yaweiw@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: azure_rm_containerregistry
version_added: "2.5"
short_description: Manage an Azure Container Registry
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
    state:
        description:
            - Assert the state of the container registry. Use C(present) to create or update an container registry and C(absent) to delete it.
        default: present
        choices:
            - absent
            - present
    location:
        description:
            - Valid azure location. Defaults to location of the resource group.
    admin_user_enabled:
        description:
            - If enabled, you can use the registry name as username and admin user access key as password to docker login to your container registry.
        type: bool
        default: no
    sku:
        description:
            - Specifies the SKU to use. Currently can be either C(Basic), C(Standard) or C(Premium).
        default: Standard
        choices:
            - Basic
            - Standard
            - Premium

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - Yawei Wang (@yaweiw)

'''

EXAMPLES = '''
    - name: Create an azure container registry
      azure_rm_containerregistry:
        name: myRegistry
        location: eastus
        resource_group: myResourceGroup
        admin_user_enabled: true
        sku: Premium
        tags:
            Release: beta1
            Environment: Production

    - name: Remove an azure container registry
      azure_rm_containerregistry:
        name: myRegistry
        resource_group: myResourceGroup
        state: absent
'''
RETURN = '''
id:
    description:
        - Resource ID.
    returned: always
    type: str
    sample: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.ContainerRegistry/registries/myRegistry
name:
    description:
        - Registry name.
    returned: always
    type: str
    sample: myregistry
location:
    description:
        - Resource location.
    returned: always
    type: str
    sample: westus
admin_user_enabled:
    description:
        - Is admin user enabled.
    returned: always
    type: bool
    sample: true
sku:
    description:
        - The SKU name of the container registry.
    returned: always
    type: str
    sample: Standard
provisioning_state:
    description:
        - Provisioning state.
    returned: always
    type: str
    sample: Succeeded
login_server:
    description:
        - Registry login server.
    returned: always
    type: str
    sample: myregistry.azurecr.io
credentials:
    description:
        - Passwords defined for the registry.
    returned: always
    type: complex
    contains:
        password:
            description:
                - password value.
            returned: when registry exists and C(admin_user_enabled) is set
            type: str
            sample: pass1value
        password2:
            description:
                - password2 value.
            returned: when registry exists and C(admin_user_enabled) is set
            type: str
            sample: pass2value
tags:
    description:
        - Tags assigned to the resource. Dictionary of string:string pairs.
    returned: always
    type: dict
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

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
except ImportError as exc:
    # This is handled in azure_rm_common
    pass


def create_containerregistry_dict(registry, credentials):
    '''
    Helper method to deserialize a ContainerRegistry to a dict
    :param: registry: return container registry object from Azure rest API call
    :param: credentials: return credential objects from Azure rest API call
    :return: dict of return container registry and it's credentials
    '''
    results = dict(
        id=registry.id if registry is not None else "",
        name=registry.name if registry is not None else "",
        location=registry.location if registry is not None else "",
        admin_user_enabled=registry.admin_user_enabled if registry is not None else "",
        sku=registry.sku.name if registry is not None else "",
        provisioning_state=registry.provisioning_state if registry is not None else "",
        login_server=registry.login_server if registry is not None else "",
        credentials=dict(),
        tags=registry.tags if registry is not None else ""
    )
    if credentials:
        results['credentials'] = dict(
            password=credentials.passwords[0].value,
            password2=credentials.passwords[1].value
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
                default='present',
                choices=['present', 'absent']
            ),
            location=dict(
                type='str'
            ),
            admin_user_enabled=dict(
                type='bool',
                default=False
            ),
            sku=dict(
                type='str',
                default='Standard',
                choices=['Basic', 'Standard', 'Premium']
            )
        )

        self.resource_group = None
        self.name = None
        self.location = None
        self.state = None
        self.sku = None
        self.tags = None

        self.results = dict(changed=False, state=dict())

        super(AzureRMContainerRegistry, self).__init__(
            derived_arg_spec=self.module_arg_spec,
            supports_check_mode=True,
            supports_tags=True)

    def exec_module(self, **kwargs):
        """Main module execution method"""
        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        resource_group = None
        response = None
        to_do = Actions.NoAction

        resource_group = self.get_resource_group(self.resource_group)
        if not self.location:
            self.location = resource_group.location

        # Check if the container registry instance already present in the RG
        if self.state == 'present':
            response = self.get_containerregistry()

            if not response:
                to_do = Actions.Create
            else:
                self.log('Results : {0}'.format(response))
                self.results.update(response)
                if response['provisioning_state'] == "Succeeded":
                    to_do = Actions.NoAction
                    if (self.location is not None) and self.location != response['location']:
                        to_do = Actions.Update
                    elif (self.sku is not None) and self.location != response['sku']:
                        to_do = Actions.Update
                else:
                    to_do = Actions.NoAction

            self.log("Create / Update the container registry instance")
            if self.check_mode:
                return self.results

            self.results.update(self.create_update_containerregistry(to_do))
            if to_do != Actions.NoAction:
                self.results['changed'] = True
            else:
                self.results['changed'] = False

            self.log("Container registry instance created or updated")
        elif self.state == 'absent':
            if self.check_mode:
                return self.results
            self.delete_containerregistry()
            self.log("Container registry instance deleted")

        return self.results

    def create_update_containerregistry(self, to_do):
        '''
        Creates or updates a container registry.

        :return: deserialized container registry instance state dictionary
        '''
        self.log("Creating / Updating the container registry instance {0}".format(self.name))

        try:
            if to_do != Actions.NoAction:
                if to_do == Actions.Create:
                    name_status = self.containerregistry_client.registries.check_name_availability(self.name)
                    if name_status.name_available:
                        poller = self.containerregistry_client.registries.create(
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
                        raise Exception("Invalid registry name. reason: " + name_status.reason + " message: " + name_status.message)
                else:
                    registry = self.containerregistry_client.registries.get(self.resource_group, self.name)
                    if registry is not None:
                        poller = self.containerregistry_client.registries.update(
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
                    else:
                        raise Exception("Update registry failed as registry '" + self.name + "' doesn't exist.")
                response = self.get_poller_result(poller)
                if self.admin_user_enabled:
                    credentials = self.containerregistry_client.registries.list_credentials(self.resource_group, self.name)
                else:
                    self.log('Cannot perform credential operations as admin user is disabled')
                    credentials = None
            else:
                response = None
                credentials = None
        except (CloudError, Exception) as exc:
            self.log('Error attempting to create / update the container registry instance.')
            self.fail("Error creating / updating the container registry instance: {0}".format(str(exc)))
        return create_containerregistry_dict(response, credentials)

    def delete_containerregistry(self):
        '''
        Deletes the specified container registry in the specified subscription and resource group.

        :return: True
        '''
        self.log("Deleting the container registry instance {0}".format(self.name))
        try:
            self.containerregistry_client.registries.delete(self.resource_group, self.name).wait()
        except CloudError as e:
            self.log('Error attempting to delete the container registry instance.')
            self.fail("Error deleting the container registry instance: {0}".format(str(e)))

        return True

    def get_containerregistry(self):
        '''
        Gets the properties of the specified container registry.

        :return: deserialized container registry state dictionary
        '''
        self.log("Checking if the container registry instance {0} is present".format(self.name))
        found = False
        try:
            response = self.containerregistry_client.registries.get(self.resource_group, self.name)
            found = True
            self.log("Response : {0}".format(response))
            self.log("Container registry instance : {0} found".format(response.name))
        except CloudError as e:
            if e.error.error == 'ResourceNotFound':
                self.log('Did not find the container registry instance: {0}'.format(str(e)))
            else:
                self.fail('Error while trying to get container registry instance: {0}'.format(str(e)))
            response = None
        if found is True and self.admin_user_enabled is True:
            try:
                credentials = self.containerregistry_client.registries.list_credentials(self.resource_group, self.name)
            except CloudError as e:
                self.fail('List registry credentials failed: {0}'.format(str(e)))
                credentials = None
        elif found is True and self.admin_user_enabled is False:
            credentials = None
        else:
            return None
        return create_containerregistry_dict(response, credentials)


def main():
    """Main execution"""
    AzureRMContainerRegistry()


if __name__ == '__main__':
    main()
