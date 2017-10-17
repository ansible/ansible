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
short_description: Manage an Azure Container Instance (ACS).
description:
    - Create, update and delete an Azure Container Instance.

options:
    resource_group:
        description:
            - Name of a resource group where the Container Services exists or will be created.
        required: true
    group_name:
        description:
            - Name of the container Group
        required: true
        default: null
    name:
        description:
            - Name of the container instance.
        required: true
        default: null
    image:
        description:
            - Image to be used to create container instance.
        required: true
        default: null
    os:
        description:
            - Operating System
        choices:
            - linux
            - windows
        default: linux
        required: false
    state:
        description:
            - Assert the state of the ACS. Use 'present' to create or update an ACS and 'absent' to delete it.
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
    - name: Create an azure container services instance running Kubernetes
      azure_rm_acs:
        name: acctestcontservice1
        location: eastus
        resource_group: Testing
        orchestration_platform: Kubernetes
        master_profile:
            - count: 3
              dns_prefix: acsk8smasterdns
        linux_profile:
            - admin_username: azureuser
              ssh_key: ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAA...
        service_principal:
            - client_id: "cf72ca99-f6b9-4004-b0e0-bee10c521948"
              client_secret: "mySPNp@ssw0rd!"
        agent_pool_profiles:
            - name: default
              count: 5
              dns_prefix: acsk8sagent
              vm_size: Standard_D2_v2
        diagnostics_profile: false
        tags:
            Environment: Production

    - name: Create an azure container services instance running DCOS
      azure_rm_acs:
        name: acctestcontservice2
        location: eastus
        resource_group: Testing
        orchestration_platform: DCOS
        master_profile:
            - count: 3
              dns_prefix: acsdcosmasterdns
        linux_profile:
            - admin_username: azureuser
              ssh_key: ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAA...
        agent_pool_profiles:
            - name: default
              count: 5
              dns_prefix: acscdcosagent
              vm_size: Standard_D2_v2
        diagnostics_profile: false
        tags:
            Environment: Production

    - name: Create an azure container services instance running Swarm
      azure_rm_acs:
        name: acctestcontservice3
        location: eastus
        resource_group: Testing
        orchestration_platform: Swarm
        master_profile:
            - count: 3
              dns_prefix: acsswarmmasterdns
        linux_profile:
            - admin_username: azureuser
              ssh_key: ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAA...
        agent_pool_profiles:
            - name: default
              count: 5
              dns_prefix: acsswarmagent
              vm_size: Standard_D2_v2
        diagnostics_profile: false
        tags:
            Environment: Production

# Deletes the specified container service in the specified subscription and resource group.
# The operation does not delete other resources created as part of creating a container service,
# including storage accounts, VMs, and availability sets. All the other resources created with the container
# service are part of the same resource group and can be deleted individually.
    - name: Remove an azure container services instance
      azure_rm_acs:
        name: acctestcontservice3
        location: eastus
        resource_group: Testing
        state: absent
        orchestration_platform: Swarm
        master_profile:
            - count: 1
              dns_prefix: acstestingmasterdns5
        linux_profile:
            - admin_username: azureuser
              ssh_key: ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAA...
        service_principal:
            - client_id: 7fb4173c-3ca3-4d5b-87f8-1daac941207a
              client_secret: MPNSuM1auUuITefiLGBrpZZnLMDKBLw2
        agent_pool_profiles:
            - name: default
              count: 4
              dns_prefix: acctestagent15
              vm_size: Standard_A0
        diagnostics_profile: false
        tags:
            Ansible: azure_rm_acs
'''
RETURN = '''
state:
    description: Current state of the azure container service
    returned: always
    type: dict
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.containerservice.models import (
        ContainerService, ContainerServiceOrchestratorProfile, ContainerServiceCustomProfile,
        ContainerServiceServicePrincipalProfile, ContainerServiceMasterProfile,
        ContainerServiceAgentPoolProfile, ContainerServiceWindowsProfile,
        ContainerServiceLinuxProfile, ContainerServiceSshConfiguration,
        ContainerServiceDiagnosticsProfile, ContainerServiceSshPublicKey,
        ContainerServiceVMDiagnostics
    )
    from azure.mgmt.containerinstance.models import (ContainerGroup, Container, ResourceRequirements, ResourceRequests)
    from azure.mgmt.containerinstance import ContainerInstanceManagementClient
except ImportError:
    # This is handled in azure_rm_common
    pass


def create_aci_dict(aci):
    '''
    Helper method to deserialize a ContainerService to a dict
    :param: acs: ContainerService or AzureOperationPoller with the Azure callback object
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
            os=dict(
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

        # Check if the ACS instance already present in the RG
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

        :return: deserialized ACS instance state dictionary
        '''
        self.log("Creating / Updating the ACS instance {0}".format(self.name))

        # self.log("orchestrator_profile : {0}".format(parameters.orchestrator_profile))
        # self.log("service_principal_profile : {0}".format(parameters.service_principal_profile))
        # self.log("linux_profile : {0}".format(parameters.linux_profile))
        # self.log("ssh from yaml : {0}".format(results.get('linux_profile')[0]))
        # self.log("ssh : {0}".format(parameters.linux_profile.ssh))
        # self.log("master_profile : {0}".format(parameters.master_profile))
        # self.log("agent_pool_profiles : {0}".format(parameters.agent_pool_profiles))
        # self.log("vm_diagnostics : {0}".format(parameters.diagnostics_profile.vm_diagnostics))

        parameters = ContainerGroup(self.location,
                                    None,
                                    [Container(self.name, self.image, ResourceRequirements(ResourceRequests(1.5, 1)))],
                                    None,
                                    None,
                                    None,
                                    self.os)

        try:
            client = ContainerInstanceManagementClient(self.azure_credentials, self.subscription_id)
            response = client.container_groups.create_or_update(self.resource_group, self.group_name, parameters)
        except CloudError as exc:
            self.log('Error attempting to create the container instance.')
            self.fail("Error creating the ACS instance: {0}".format(str(exc)))
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
            response = client.delete(self.resource_group, self.name)
        except CloudError as e:
            self.log('Error attempting to delete the ACS instance.')
            self.fail("Error deleting the ACS instance: {0}".format(str(e)))

        return True

    def get_acs(self):
        '''
        Gets the properties of the specified container service.

        :return: deserialized ACS instance state dictionary
        '''
        self.log("Checking if the ACS instance {0} is present".format(self.name))
        found = False
        try:
            response = self.containerinstance_client.container_services.get(self.resource_group, self.name)
            found = True
            self.log("Response : {0}".format(response))
            self.log("ACS instance : {0} found".format(response.name))
        except CloudError as e:
            self.log('Did not find the ACS instance.')
        if found is True:
            return create_aci_dict(response)

        return False


def main():
    """Main execution"""
    AzureRMContainerInstance()

if __name__ == '__main__':
    main()
