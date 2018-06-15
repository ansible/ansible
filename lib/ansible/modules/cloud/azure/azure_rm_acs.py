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
    state:
        description:
            - Assert the state of the ACS. Use 'present' to create or update an ACS and 'absent' to delete it.
        default: present
        choices:
            - absent
            - present
    location:
        description:
            - Valid azure location. Defaults to location of the resource group.
    orchestration_platform:
        description:
            - Specifies the Container Orchestration Platform to use. Currently can be either DCOS, Kubernetes or Swarm.
        choices:
            - 'DCOS'
            - 'Kubernetes'
            - 'Swarm'
        required: true
    master_profile:
        description:
            - Master profile suboptions.
        required: true
        suboptions:
            count:
                description:
                  - Number of masters (VMs) in the container service cluster. Allowed values are 1, 3, and 5.
                required: true
                choices:
                  - 1
                  - 3
                  - 5
            vm_size:
                description:
                    - The VM Size of each of the Agent Pool VM's (e.g. Standard_F1 / Standard_D2v2).
                required: true
                version_added: 2.5
            dns_prefix:
                description:
                  - The DNS Prefix to use for the Container Service master nodes.
                required: true
    linux_profile:
        description:
            - The linux profile suboptions.
        required: true
        suboptions:
            admin_username:
                description:
                  - The Admin Username for the Cluster.
                required: true
            ssh_key:
                description:
                    - The Public SSH Key used to access the cluster.
                required: true
    agent_pool_profiles:
        description:
            - The agent pool profile suboptions.
        required: true
        suboptions:
            name:
                description:
                  - Unique name of the agent pool profile in the context of the subscription and resource group.
                required: true
            count:
                description:
                    - Number of agents (VMs) to host docker containers. Allowed values must be in the range of 1 to 100 (inclusive).
                required: true
            dns_prefix:
                description:
                    - The DNS Prefix given to Agents in this Agent Pool.
                required: true
            vm_size:
                description:
                    - The VM Size of each of the Agent Pool VM's (e.g. Standard_F1 / Standard_D2v2).
                required: true
    service_principal:
        description:
            - The service principal suboptions.
        suboptions:
            client_id:
                description:
                    - The ID for the Service Principal.
                required: false
            client_secret:
                description:
                    - The secret password associated with the service principal.
                required: false
    diagnostics_profile:
        description:
            - Should VM Diagnostics be enabled for the Container Service VM's.
        required: true
        type: bool

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
              vm_size: Standard_D2_v2
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
              vm_size: Standard_D2_v2
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
              vm_size: Standard_D2_v2
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
              vm_size: Standard_A0
              dns_prefix: acstestingmasterdns5
        linux_profile:
            - admin_username: azureuser
              ssh_key: ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAA...
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
    Note: first_consecutive_static_ip is specifically set to None, for Azure server doesn't accept
    request body with this property. This should be an inconsistency bug before Azure client SDK
    and Azure server.
    :param: masterprofile: dict with the parameters to setup the ContainerServiceMasterProfile
    :return: ContainerServiceMasterProfile
    '''
    return ContainerServiceMasterProfile(
        count=masterprofile[0]['count'],
        dns_prefix=masterprofile[0]['dns_prefix'],
        vm_size=masterprofile[0]['vm_size'],
        first_consecutive_static_ip=None
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
    service_principal_profile_dict = None
    if acs.orchestrator_profile.orchestrator_type == 'Kubernetes':
        service_principal_profile_dict = create_service_principal_profile_dict(acs.service_principal_profile)

    return dict(
        id=acs.id,
        name=acs.name,
        location=acs.location,
        tags=acs.tags,
        orchestrator_profile=create_orchestrator_profile_dict(acs.orchestrator_profile),
        master_profile=create_master_profile_dict(acs.master_profile),
        linux_profile=create_linux_profile_dict(acs.linux_profile),
        service_principal_profile=service_principal_profile_dict,
        diagnostics_profile=create_diagnotstics_profile_dict(acs.diagnostics_profile),
        provisioning_state=acs.provisioning_state,
        agent_pool_profiles=create_agent_pool_profiles_dict(acs.agent_pool_profiles),
        type=acs.type
    )


def create_linux_profile_dict(linuxprofile):
    '''
    Helper method to deserialize a ContainerServiceLinuxProfile to a dict
    :param: linuxprofile: ContainerServiceLinuxProfile with the Azure callback object
    :return: dict with the state on Azure
    '''
    return dict(
        ssh_key=linuxprofile.ssh.public_keys[0].key_data,
        admin_username=linuxprofile.admin_username
    )


def create_master_profile_dict(masterprofile):
    '''
    Helper method to deserialize a ContainerServiceMasterProfile to a dict
    :param: masterprofile: ContainerServiceMasterProfile with the Azure callback object
    :return: dict with the state on Azure
    '''
    return dict(
        count=masterprofile.count,
        fqdn=masterprofile.fqdn,
        vm_size=masterprofile.vm_size,
        dns_prefix=masterprofile.dns_prefix
    )


def create_service_principal_profile_dict(serviceprincipalprofile):
    '''
    Helper method to deserialize a ContainerServiceServicePrincipalProfile to a dict
    Note: For security reason, the service principal secret is skipped on purpose.
    :param: serviceprincipalprofile: ContainerServiceServicePrincipalProfile with the Azure callback object
    :return: dict with the state on Azure
    '''
    return dict(
        client_id=serviceprincipalprofile.client_id
    )


def create_diagnotstics_profile_dict(diagnosticsprofile):
    '''
    Helper method to deserialize a ContainerServiceVMDiagnostics to a dict
    :param: diagnosticsprofile: ContainerServiceVMDiagnostics with the Azure callback object
    :return: dict with the state on Azure
    '''
    return dict(
        vm_diagnostics=diagnosticsprofile.vm_diagnostics.enabled
    )


def create_orchestrator_profile_dict(orchestratorprofile):
    '''
    Helper method to deserialize a ContainerServiceOrchestratorProfile to a dict
    :param: orchestratorprofile: ContainerServiceOrchestratorProfile with the Azure callback object
    :return: dict with the state on Azure
    '''
    return dict(
        orchestrator_type=str(orchestratorprofile.orchestrator_type)
    )


def create_agent_pool_profiles_dict(agentpoolprofiles):
    '''
    Helper method to deserialize a ContainerServiceAgentPoolProfile to a dict
    :param: agentpoolprofiles: ContainerServiceAgentPoolProfile with the Azure callback object
    :return: dict with the state on Azure
    '''
    return [dict(
        count=profile.count,
        vm_size=profile.vm_size,
        name=profile.name,
        dns_prefix=profile.dns_prefix,
        fqdn=profile.fqdn
    ) for profile in agentpoolprofiles]


class AzureRMContainerService(AzureRMModuleBase):
    """Configuration class for an Azure RM container service resource"""

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
            orchestration_platform=dict(
                type='str',
                required=True,
                choices=['DCOS', 'Kubernetes', 'Swarm']
            ),
            master_profile=dict(
                type='list',
                required=True
            ),
            linux_profile=dict(
                type='list',
                required=True
            ),
            agent_pool_profiles=dict(
                type='list',
                required=True
            ),
            service_principal=dict(
                type='list',
                required=False
            ),
            diagnostics_profile=dict(
                type='bool',
                required=True
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

        super(AzureRMContainerService, self).__init__(derived_arg_spec=self.module_arg_spec,
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

        resource_group = self.get_resource_group(self.resource_group)
        if not self.location:
            self.location = resource_group.location

        # Check if the ACS instance already present in the RG
        if self.state == 'present':

            if self.orchestration_platform == 'Kubernetes':
                if not self.service_principal:
                    self.fail('service_principal should be specified when using Kubernetes')
                if not self.service_principal[0].get('client_id'):
                    self.fail('service_principal.client_id should be specified when using Kubernetes')
                if not self.service_principal[0].get('client_secret'):
                    self.fail('service_principal.client_secret should be specified when using Kubernetes')

            mastercount = self.master_profile[0].get('count')
            if mastercount != 1 and mastercount != 3 and mastercount != 5:
                self.fail('Master Count number wrong : {} / should be 1 3 or 5'.format(mastercount))

            # For now Agent Pool cannot be more than 1, just remove this part in the future if it change
            agentpoolcount = len(self.agent_pool_profiles)
            if agentpoolcount > 1:
                self.fail('You cannot specify more than agent_pool_profiles')

            response = self.get_acs()
            self.results['state'] = response
            if not response:
                to_be_updated = True

            else:
                self.log('Results : {0}'.format(response))
                update_tags, response['tags'] = self.update_tags(response['tags'])

                if response['provisioning_state'] == "Succeeded":
                    if update_tags:
                        to_be_updated = True

                    def is_property_changed(profile, property, ignore_case=False):
                        base = response[profile].get(property)
                        new = getattr(self, profile)[0].get(property)
                        if ignore_case:
                            return base.lower() != new.lower()
                        else:
                            return base != new

                    # Cannot Update the master count for now // Uncomment this block in the future to support it
                    if is_property_changed('master_profile', 'count'):
                        # self.log(("Master Profile Count Diff, Was {0} / Now {1}"
                        #           .format(response['master_profile'].count,
                        #           self.master_profile[0].get('count'))))
                        # to_be_updated = True
                        self.module.warn("master_profile.count cannot be updated")

                    # Cannot Update the master vm_size for now. Could be a client SDK bug
                    # Uncomment this block in the future to support it
                    if is_property_changed('master_profile', 'vm_size', True):
                        # self.log(("Master Profile VM Size Diff, Was {0} / Now {1}"
                        #           .format(response['master_profile'].get('vm_size'),
                        #                   self.master_profile[0].get('vm_size'))))
                        # to_be_updated = True
                        self.module.warn("master_profile.vm_size cannot be updated")

                    # Cannot Update the SSH Key for now // Uncomment this block in the future to support it
                    if is_property_changed('linux_profile', 'ssh_key'):
                        # self.log(("Linux Profile Diff SSH, Was {0} / Now {1}"
                        #          .format(response['linux_profile'].ssh.public_keys[0].key_data,
                        #          self.linux_profile[0].get('ssh_key'))))
                        # to_be_updated = True
                        self.module.warn("linux_profile.ssh_key cannot be updated")

                    # self.log("linux_profile response : {0}".format(response['linux_profile'].get('admin_username')))
                    # self.log("linux_profile self : {0}".format(self.linux_profile[0].get('admin_username')))
                    # Cannot Update the Username for now // Uncomment this block in the future to support it
                    if is_property_changed('linux_profile', 'admin_username'):
                        # self.log(("Linux Profile Diff User, Was {0} / Now {1}"
                        #          .format(response['linux_profile'].admin_username,
                        #          self.linux_profile[0].get('admin_username'))))
                        # to_be_updated = True
                        self.module.warn("linux_profile.admin_username cannot be updated")

                    # Cannot have more that one agent pool profile for now // Uncomment this block in the future to support it
                    # if len(response['agent_pool_profiles']) != len(self.agent_pool_profiles):
                    #    self.log("Agent Pool count is diff, need to updated")
                    #    to_be_updated = True

                    for profile_result in response['agent_pool_profiles']:
                        matched = False
                        for profile_self in self.agent_pool_profiles:
                            if profile_result['name'] == profile_self['name']:
                                matched = True
                                if profile_result['count'] != profile_self['count'] or profile_result['vm_size'] != \
                                        profile_self['vm_size']:
                                    self.log(("Agent Profile Diff - Count was {0} / Now {1} - Vm_size was {2} / Now {3}"
                                              .format(profile_result['count'], profile_self['count'],
                                                      profile_result['vm_size'], profile_self['vm_size'])))
                                    to_be_updated = True
                        if not matched:
                            self.log("Agent Pool not found")
                            to_be_updated = True

            if to_be_updated:
                self.log("Need to Create / Update the ACS instance")

                if self.check_mode:
                    return self.results

                self.results['state'] = self.create_update_acs()
                self.results['changed'] = True

                self.log("Creation / Update done")
        elif self.state == 'absent':
            if self.check_mode:
                return self.results
            self.delete_acs()
            self.log("ACS instance deleted")

        return self.results

    def create_update_acs(self):
        '''
        Creates or updates a container service with the specified configuration of orchestrator, masters, and agents.

        :return: deserialized ACS instance state dictionary
        '''
        self.log("Creating / Updating the ACS instance {0}".format(self.name))

        service_principal_profile = None
        agentpools = []

        if self.agent_pool_profiles:
            for profile in self.agent_pool_profiles:
                self.log("Trying to push the following Profile {0}".format(profile))
                agentpools.append(create_agent_pool_profile_instance(profile))

        if self.orchestration_platform == 'Kubernetes':
            service_principal_profile = create_service_principal_profile_instance(self.service_principal)

        parameters = ContainerService(
            location=self.location,
            tags=self.tags,
            orchestrator_profile=create_orch_platform_instance(self.orchestration_platform),
            service_principal_profile=service_principal_profile,
            linux_profile=create_linux_profile_instance(self.linux_profile),
            master_profile=create_master_profile_instance(self.master_profile),
            agent_pool_profiles=agentpools,
            diagnostics_profile=create_diagnostics_profile_instance(self.diagnostics_profile)
        )

        # self.log("orchestrator_profile : {0}".format(parameters.orchestrator_profile))
        # self.log("service_principal_profile : {0}".format(parameters.service_principal_profile))
        # self.log("linux_profile : {0}".format(parameters.linux_profile))
        # self.log("ssh from yaml : {0}".format(results.get('linux_profile')[0]))
        # self.log("ssh : {0}".format(parameters.linux_profile.ssh))
        # self.log("master_profile : {0}".format(parameters.master_profile))
        # self.log("agent_pool_profiles : {0}".format(parameters.agent_pool_profiles))
        # self.log("vm_diagnostics : {0}".format(parameters.diagnostics_profile.vm_diagnostics))

        try:
            poller = self.containerservice_client.container_services.create_or_update(self.resource_group, self.name,
                                                                                      parameters)
            response = self.get_poller_result(poller)
        except CloudError as exc:
            self.log('Error attempting to create the ACS instance.')
            self.fail("Error creating the ACS instance: {0}".format(str(exc)))
        return create_acs_dict(response)

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
            poller = self.containerservice_client.container_services.delete(self.resource_group, self.name)
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
            response = self.containerservice_client.container_services.get(self.resource_group, self.name)
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
    AzureRMContainerService()


if __name__ == '__main__':
    main()
