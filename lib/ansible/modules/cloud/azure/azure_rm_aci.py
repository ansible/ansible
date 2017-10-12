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
module: azure_rm_acs
version_added: "2.4"
short_description: Manage an Azure Container Service Instance (ACS).
description:
    - Create, update and delete an Azure Container Service Instance.

options:
    resource_group:
        description:
            - Name of a resource group where the Container Services exists or will be created.
        required: true
    name:
        description:
            - Name of the Container Services instance.
        required: true
        default: null
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
    - "Julien Stroheker (@julienstroheker)"

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
    from azure.mgmt.containerinstance.models import ( ContainerGroup, Container, ResourceRequirements, ResourceRequests )
except ImportError:
    # This is handled in azure_rm_common
    pass


def create_agent_pool_profile_instance(agentpoolprofile):
    '''
    Helper method to serialize a dict to a ContainerServiceAgentPoolProfile
    :param: agentpoolprofile: dict with the parameters to setup the ContainerServiceAgentPoolProfile
    :return: ContainerServiceAgentPoolProfile
    '''
    return ContainerServiceAgentPoolProfile(
        name=agentpoolprofile['name'],
        count=agentpoolprofile['count'],
        dns_prefix=agentpoolprofile['dns_prefix'],
        vm_size=agentpoolprofile['vm_size']
    )


def create_orch_platform_instance(orchestrator):
    '''
    Helper method to serialize a dict to a ContainerServiceOrchestratorProfile
    :param: orchestrator: dict with the parameters to setup the ContainerServiceOrchestratorProfile
    :return: ContainerServiceOrchestratorProfile
    '''
    return ContainerServiceOrchestratorProfile(
        orchestrator_type=orchestrator,
    )


def create_service_principal_profile_instance(spnprofile):
    '''
    Helper method to serialize a dict to a ContainerServiceServicePrincipalProfile
    :param: spnprofile: dict with the parameters to setup the ContainerServiceServicePrincipalProfile
    :return: ContainerServiceServicePrincipalProfile
    '''
    return ContainerServiceServicePrincipalProfile(
        client_id=spnprofile[0]['client_id'],
        secret=spnprofile[0]['client_secret']
    )


def create_linux_profile_instance(linuxprofile):
    '''
    Helper method to serialize a dict to a ContainerServiceLinuxProfile
    :param: linuxprofile: dict with the parameters to setup the ContainerServiceLinuxProfile
    :return: ContainerServiceLinuxProfile
    '''
    return ContainerServiceLinuxProfile(
        admin_username=linuxprofile[0]['admin_username'],
        ssh=create_ssh_configuration_instance(linuxprofile[0]['ssh_key'])
    )


def create_ssh_configuration_instance(sshconf):
    '''
    Helper method to serialize a dict to a ContainerServiceSshConfiguration
    :param: sshconf: dict with the parameters to setup the ContainerServiceSshConfiguration
    :return: ContainerServiceSshConfiguration
    '''
    listssh = []
    key = ContainerServiceSshPublicKey(key_data=str(sshconf))
    listssh.append(key)
    return ContainerServiceSshConfiguration(
        public_keys=listssh
    )


def create_master_profile_instance(masterprofile):
    '''
    Helper method to serialize a dict to a ContainerServiceMasterProfile
    :param: masterprofile: dict with the parameters to setup the ContainerServiceMasterProfile
    :return: ContainerServiceMasterProfile
    '''
    return ContainerServiceMasterProfile(
        count=masterprofile[0]['count'],
        dns_prefix=masterprofile[0]['dns_prefix']
    )


def create_diagnostics_profile_instance(diagprofile):
    '''
    Helper method to serialize a dict to a ContainerServiceDiagnosticsProfile
    :param: diagprofile: dict with the parameters to setup the ContainerServiceDiagnosticsProfile
    :return: ContainerServiceDiagnosticsProfile
    '''
    return ContainerServiceDiagnosticsProfile(
        vm_diagnostics=create_vm_diagnostics_instance(diagprofile)
    )


def create_vm_diagnostics_instance(vmdiag):
    '''
    Helper method to serialize a dict to a ContainerServiceVMDiagnostics
    :param: vmdiag: dict with the parameters to setup the ContainerServiceVMDiagnostics
    :return: ContainerServiceVMDiagnostics
    '''
    return ContainerServiceVMDiagnostics(
        enabled=vmdiag
    )


def create_acs_dict(acs):
    '''
    Helper method to deserialize a ContainerService to a dict
    :param: acs: ContainerService or AzureOperationPoller with the Azure callback object
    :return: dict with the state on Azure
    '''
    results = dict(
        id=acs.id,
        name=acs.name,
        location=acs.location,
        tags=acs.tags,
        orchestrator_profile=create_orchestrator_profile_dict(acs.orchestrator_profile),
        master_profile=create_master_profile_dict(acs.master_profile),
        linux_profile=create_linux_profile_dict(acs.linux_profile),
        service_principal_profile=acs.service_principal_profile,
        diagnostics_profile=create_diagnotstics_profile_dict(acs.diagnostics_profile),
        provisioning_state=acs.provisioning_state,
        agent_pool_profiles=create_agent_pool_profiles_dict(acs.agent_pool_profiles),
        type=acs.type
    )
    return results


def create_linux_profile_dict(linuxprofile):
    '''
    Helper method to deserialize a ContainerServiceLinuxProfile to a dict
    :param: linuxprofile: ContainerServiceLinuxProfile with the Azure callback object
    :return: dict with the state on Azure
    '''
    results = dict(
        ssh_key=linuxprofile.ssh.public_keys[0].key_data,
        admin_username=linuxprofile.admin_username
    )
    return results


def create_master_profile_dict(masterprofile):
    '''
    Helper method to deserialize a ContainerServiceMasterProfile to a dict
    :param: masterprofile: ContainerServiceMasterProfile with the Azure callback object
    :return: dict with the state on Azure
    '''
    results = dict(
        count=masterprofile.count,
        fqdn=masterprofile.fqdn,
        dns_prefix=masterprofile.dns_prefix
    )
    return results


def create_diagnotstics_profile_dict(diagnosticsprofile):
    '''
    Helper method to deserialize a ContainerServiceVMDiagnostics to a dict
    :param: diagnosticsprofile: ContainerServiceVMDiagnostics with the Azure callback object
    :return: dict with the state on Azure
    '''
    results = dict(
        vm_diagnostics=diagnosticsprofile.vm_diagnostics.enabled
    )
    return results


def create_orchestrator_profile_dict(orchestratorprofile):
    '''
    Helper method to deserialize a ContainerServiceOrchestratorProfile to a dict
    :param: orchestratorprofile: ContainerServiceOrchestratorProfile with the Azure callback object
    :return: dict with the state on Azure
    '''
    results = dict(
        orchestrator_type=str(orchestratorprofile.orchestrator_type)
    )
    return results


def create_agent_pool_profiles_dict(agentpoolprofiles):
    '''
    Helper method to deserialize a ContainerServiceAgentPoolProfile to a dict
    :param: agentpoolprofiles: ContainerServiceAgentPoolProfile with the Azure callback object
    :return: dict with the state on Azure
    '''
    results = []
    for profile in agentpoolprofiles:
        result = dict(
            count=profile.count,
            vm_size=profile.vm_size,
            name=profile.name,
            dns_prefix=profile.dns_prefix,
            fqdn=profile.fqdn
        )
        results.append(result)
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
        self.orchestration_platform = None
        self.master_profile = None
        self.linux_profile = None
        self.agent_pool_profiles = None
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

            self.log("Need to Create / Update the ACS instance")

            if self.check_mode:
                return self.results

            self.results['state'] = self.create_update_acs()
            self.results['changed'] = True

            self.log("Creation / Update done")
        elif self.state == 'absent':
            self.delete_acs()
            self.log("ACS instance deleted")

        return self.results

    def create_update_acs(self):
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

        parameters = ContainerGroup(self.location, None, [Container("testvm10", "dockiot/ansible", ResourceRequirements(ResourceRequests(1.5, 1)))], None, None, None, "linux")

        try:
            response = self.containerinstance_client.container_groups.create_or_update(self.resource_group, self.name, parameters)
        except CloudError as exc:
            self.log('Error attempting to create the container instance.')
            self.fail("Error creating the ACS instance: {0}".format(str(exc)))
        return response

    def delete_acs(self):
        '''
        Deletes the specified container service in the specified subscription and resource group.
        The operation does not delete other resources created as part of creating a container service,
        including storage accounts, VMs, and availability sets.
        All the other resources created with the container service are part of the same resource group and can be deleted individually.

        :return: True
        '''
        self.log("Deleting the ACS instance {0}".format(self.name))
        try:
            poller = self.containerinstance_client.container_services.delete(self.resource_group, self.name)
            self.get_poller_result(poller)
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
            return create_acs_dict(response)
        else:
            return False


def main():
    """Main execution"""
    AzureRMContainerInstance()

if __name__ == '__main__':
    main()
