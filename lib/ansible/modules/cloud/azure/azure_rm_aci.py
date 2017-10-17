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
module: azure_rm_aci
version_added: "2.4"
short_description: Manage an Azure Container Instance (ACI).
description:
    - Create, update and delete an Azure Container Instance.

options:
    resource_group:
        description:
            - Name of resource group.
        required: true
    group_name:
        description:
            - The name of the container group.
        required: true
        default: null
    name:
        description:
            - The name of the container instance.
        required: true
        default: null
    image:
        description:
            - The container image name.
        required: true
        default: null
    os_type:
        description:
            - The OS type of containers.
        choices:
            - linux
            - windows
        default: linux
        required: false
    memory:
        description:
            - The required memory of the containers in GB.
        default: 1.5
        required: false
    cpu:
        description:
            - The required number of CPU cores of the containers.
        default: 1
        required: false
    state:
        description:
            - Assert the state of the ACI. Use 'present' to create or update an ACI and 'absent' to delete it.
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
    registry_login_server:
        description:
            - The container image registry login server.
        required: false
    registry_username:
        description:
            - The username to log in container image registry server.
        required: false
    registry_password:
        description:
            - The password to log in container image registry server.
        required: false
    service_principal:
        description:
            - The service principal suboptions.
        required: false
        default: null
        suboptions:
            client_id:
                description:
                    - The ID for the Service Principal.
                required: false
            client_secret:
                description:
                    - The secret password associated with the service principal.
                required: false

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Zim Kalinowski (@zikalino)"

'''

EXAMPLES = '''
    - name: Create an azure container instance
      azure_rm_aci:
        group_name: testinstancegroup
        name: testinstance
        location: eastus
        resource_group: Testing
        image: contoso/testimage
        tags:
            Environment: Production

    - name: Delete existing azure container instance
      azure_rm_aci:
        group_name: testinstancegroup
        name: testinstance
        location: eastus
        resource_group: Testing
        state: absent
        tags:
            Environment: Production
'''
RETURN = '''
state:
    description: Current state of the azure instance
    returned: always
    type: dict
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.containerinstance.models import (ContainerGroup, Container, ResourceRequirements, ResourceRequests, ImageRegistryCredential)
    from azure.mgmt.containerinstance import ContainerInstanceManagementClient
except ImportError:
    # This is handled in azure_rm_common
    pass


def create_aci_dict(aci):
    '''
    Helper method to deserialize a ContainerService to a dict
    :param: aci: Container
    :return: dict with the state on Azure
    '''
    results = dict(
        id=aci.id,
        name=aci.name,
        tags=aci.tags,
        location=aci.location,
        type=aci.type,
        ip_address=aci.ip_address,
        restart_policy=aci.restart_policy,
        state=aci.state,
        provisioning_state=aci.provisioning_state,
        image_registry_credentials=aci.image_registry_credentials,
        volumes=aci.volumes,
        os_type=aci.os_type
    )
    return results


class AzureRMContainerInstance(AzureRMModuleBase):
    """Configuration class for an Azure RM container instance resource"""

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
            group_name=dict(
                type='str',
                required=True
            ),
            image=dict(
                type='str',
                required=True
            ),
            memory=dict(
                type='float',
                required=False,
                default=1.5
            ),
            cpu=dict(
                type='int',
                required=False,
                default=1
            ),
            os_type=dict(
                type='str',
                required=False,
                default='linux',
                choices=['linux', 'windows']
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
            registry_login_server=dict(
                type='str',
                required=False,
                default=None
            ),
            registry_username=dict(
                type='str',
                required=False,
                default=None
            ),
            registry_password=dict(
                type='str',
                required=False,
                default=None
            ),
            service_principal=dict(
                type='list',
                required=False
            )
        )

        self.resource_group = None
        self.name = None
        self.location = None
        self.tags = None
        self.state = None
        self.service_principal = None
        self.diagnostics_profile = None

        self.results = dict(changed=False, state=dict())

        super(AzureRMContainerInstance, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                       supports_check_mode=True,
                                                       supports_tags=True)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        resource_group = None
        response = None
        results = dict()
        to_be_updated = False

        try:
            resource_group = self.get_resource_group(self.resource_group)
        except CloudError:
            self.fail('resource group {} not found'.format(self.resource_group))
        if not self.location:
            self.location = resource_group.location

        # Check if the ACI instance already present in the RG
        if self.state == 'present':

            self.log("Need to Create / Update the ACI instance")

            if self.check_mode:
                return self.results

            self.results['state'] = self.create_update_aci()
            self.results['changed'] = True

            self.log("Creation / Update done")
        elif self.state == 'absent':
            self.delete_aci()
            self.log("ACI instance deleted")

        return self.results

    def create_update_aci(self):
        '''
        Creates or updates a container service with the specified configuration of orchestrator, masters, and agents.

        :return: deserialized ACI instance state dictionary
        '''
        self.log("Creating / Updating the ACI instance {0}".format(self.name))

        # self.log("orchestrator_profile : {0}".format(parameters.orchestrator_profile))
        # self.log("service_principal_profile : {0}".format(parameters.service_principal_profile))
        # self.log("linux_profile : {0}".format(parameters.linux_profile))
        # self.log("ssh from yaml : {0}".format(results.get('linux_profile')[0]))
        # self.log("ssh : {0}".format(parameters.linux_profile.ssh))
        # self.log("master_profile : {0}".format(parameters.master_profile))
        # self.log("agent_pool_profiles : {0}".format(parameters.agent_pool_profiles))
        # self.log("vm_diagnostics : {0}".format(parameters.diagnostics_profile.vm_diagnostics))

        credentials = None

        if self.registry_login_server is not None:
            credentials = ImageRegistryCredential(self.registry_login_server,
                                                  self.registry_username,
                                                  self.registry_password)

        parameters = ContainerGroup(self.location,
                                    None,
                                    [Container(self.name, self.image, ResourceRequirements(ResourceRequests(self.memory, self.cpu)))],
                                    credentials,
                                    None,
                                    None,
                                    self.os_type)

        try:
            client = ContainerInstanceManagementClient(self.azure_credentials, self.subscription_id)
            response = client.container_groups.create_or_update(self.resource_group, self.group_name, parameters)
        except CloudError as exc:
            self.log('Error attempting to create the container instance.')
            self.fail("Error creating the ACI instance: {0}".format(str(exc)))
        return create_aci_dict(response)

    def delete_aci(self):
        '''
        Deletes the specified container instance in the specified subscription and resource group.
        The operation does not delete other resources created as part of creating a container service,
        including storage accounts, VMs, and availability sets.
        All the other resources created with the container service are part of the same resource group and can be deleted individually.

        :return: True
        '''
        self.log("Deleting the ACI instance {0}".format(self.name))
        try:
            client = ContainerInstanceManagementClient(self.azure_credentials, self.subscription_id)
            response = client.container_groups.delete(self.resource_group, self.group_name)
        except CloudError as e:
            self.log('Error attempting to delete the ACI instance.')
            self.fail("Error deleting the ACI instance: {0}".format(str(e)))

        return True

    def get_aci(self):
        '''
        Gets the properties of the specified container service.

        :return: deserialized ACI instance state dictionary
        '''
        self.log("Checking if the ACI instance {0} is present".format(self.name))
        found = False
        try:
            response = self.containerinstance_client.container_services.get(self.resource_group, self.name)
            found = True
            self.log("Response : {0}".format(response))
            self.log("ACI instance : {0} found".format(response.name))
        except CloudError as e:
            self.log('Did not find the ACI instance.')
        if found is True:
            return create_aci_dict(response)

        return False


def main():
    """Main execution"""
    AzureRMContainerInstance()

if __name__ == '__main__':
    main()
