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
        required: false
    location:
        description:
            - Valid azure location. Defaults to location of the resource group.
        default: resource_group location
        required: false
    orchestration_platform:
        description:
            - Specifies the Container Orchestration Platform to use. Currently can be either DCOS, Kubernetes or Swarm.
        required: true
    master_profile
        description:
            - Master profile suboptions.
        required: true
        default: null
        suboptions:
            count:
                description:
                  - Number of masters (VMs) in the container service cluster. 
                    Allowed values are 1, 3, and 5. The default value is 1.
                required: true
                choices:
                  - 1
                  - 3
                  - 5
            dns_prefix:
                description:
                  - The DNS Prefix to use for the Container Service master nodes.
                required: true
    linux_profile
        description:
            - The linux profile suboptions.
        required: true
        default: null
        suboptions:
            admin_username:
                description:
                  - The Admin Username for the Cluster.
                required: true
                default: azureuser
            ssh_key:
                description:
                    - The Public SSH Key used to access the cluster.
                required: true
    agent_pool_profiles
        description:
            - The agent pool profile suboptions.
        required: true
        default: null
        suboptions:
            name:
                description:
                  - Unique name of the agent pool profile in the context of the subscription and resource group.
                required: true
            count:
                description:
                    - Number of agents (VMs) to host docker containers. 
                      Allowed values must be in the range of 1 to 100 (inclusive). 
                      The default value is 1.
                required: true
                default: 1
            dns_prefix:
                description:
                    - The DNS Prefix given to Agents in this Agent Pool.
                required: true
            vm_size:
                description:
                    - The VM Size of each of the Agent Pool VM's (e.g. Standard_F1 / Standard_D2v2).
                required: true
                default: Standard_D2v2
    service_principal:
        description:
            - The service principal suboptions.
        required: true
        default: null
        suboptions:
            client_id:
                description:
                    - The ID for the Service Principal.
                required: true
            client_secret:
                description:
                    - The secret password associated with the service principal.
                required: true
    diagnostics_profile:
        description:
            - Should VM Diagnostics be enabled for the Container Service VM's.
        required: true
        default: false
    tags:
        testing: testing
        delete: on-exit
    
extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Julien Stroheker (@ju_stroh)"
'''

EXAMPLES = '''
    - name: Create an azure container services instance
      azure_rm_acs:
        name: acctestcontservice1
        location: eastus
        resource_group: Testing
        orchestration_platform: DCOS
        master_profile:
            - count: 1
              dns_prefix: acstestingmasterdns
        linux_profile:
            - admin_username: azureuser
              ssh_key: "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCqaZoyiz1qbdOQ8xEf6uEu1cCwYowo5FHtsBhqLoDnnp7KUTEBN+io238wdhjkasndq238e2/983289dasjnasey823/YkUCuzxDpsH7DUDhZcwySLKVVe0Qm3+928dfsjsejk298r/+vAnflKebuypNlmocIvakFWoZda18FOmsOoIVXQ8HWFNCuw9ZCunMSN62QGamCe3dL5cXlkgHYv7ekJE15IA9aOJcM7e90oeTqo+dsajda82e78sdja/llas8tsXY85LFqRnr3gJ02bAscjc477+X+j/gkpFoN1QEmt juliens@msft.com"
        service_principal:
            - client_id: "cf72ca99-f6b9-4004-b0e0-bee10c521948"
              client_secret: "mySPNp@ssw0rd!"
        agent_pool_profiles:
            - name: default
              count: 1
              dns_prefix: acctestagent1
              vm_size: Standard_A0
        diagnostics_profile: false
        tags:
            Environment: Production

'''

RETURN = '''
state:
    description: Current state of the azure container services
    returned: always
    type: dict
changed:
    description: Whether or not the resource has changed
    returned: always
    type: bool
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

def create_agent_pool_profile_instance(agp):
    return ContainerServiceAgentPoolProfile(
        name=agp['name'],
        count=agp['count'],
        dns_prefix=agp['dns_prefix'],
        vm_size=agp['vm_size']
    )

def create_orch_platform_instance(orchestrator):
    return ContainerServiceOrchestratorProfile(
        orchestrator_type=orchestrator,
    )

def create_service_principal_profile_instance(spnprofile):
    return ContainerServiceServicePrincipalProfile(
        client_id=spnprofile[0]['client_id'],
        secret=spnprofile[0]['client_secret']
    )

def create_linux_profile_instance(linuxprofile):
    return ContainerServiceLinuxProfile(
        admin_username=linuxprofile[0]['admin_username'],
        ssh=create_ssh_configuration_instance(linuxprofile[0]['ssh_key'])
    )

def create_ssh_configuration_instance(sshconf):
    listssh = []
    key = ContainerServiceSshPublicKey(key_data=str(sshconf))
    listssh.append(key)
    return ContainerServiceSshConfiguration(
        public_keys=listssh
    )

def create_master_profile_instance(masterprofile):
    return ContainerServiceMasterProfile(
        count=masterprofile[0]['count'],
        dns_prefix=masterprofile[0]['dns_prefix']
    )

def create_diagnostics_profile_instance(diagprofile):
    return ContainerServiceDiagnosticsProfile(
        vm_diagnostics=create_vm_diagnostics_instance(diagprofile)
    )

def create_vm_diagnostics_instance(vmdiag):
    return ContainerServiceVMDiagnostics(
        enabled=vmdiag
    )

def create_acs_dict(acs):
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
    results = dict(
        ssh_key=linuxprofile.ssh.public_keys[0].key_data,
        admin_username=linuxprofile.admin_username
    )
    return results

def create_master_profile_dict(masterprofile):
    results = dict(
        count=masterprofile.count,
        fqdn=masterprofile.fqdn,
        dns_prefix=masterprofile.dns_prefix
    )
    return results

def create_diagnotstics_profile_dict(diagnosticsprofile):
    results = dict(
        vm_diagnostics=diagnosticsprofile.vm_diagnostics.enabled
    )
    return results

def create_orchestrator_profile_dict(orchestratorprofile):
    results = dict(
        orchestrator_type=str(orchestratorprofile.orchestrator_type)
    )
    return results

def create_agent_pool_profiles_dict(agentpoolprofiles):
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
                required=True
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

        try:
            resource_group = self.get_resource_group(self.resource_group)
        except CloudError:
            self.fail('resource group {} not found'.format(self.resource_group))
        if not self.location:
            self.location = resource_group.location
        mastercount = self.master_profile[0].get('count')
        if mastercount != 1 and mastercount != 3 and mastercount != 5:
            self.fail('Master Count number wrong : {} / should be 1 3 or 5'.format(mastercount))


        # Check if the ACS instance already present in the RG
        if self.state == 'present':
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

                    # Cannot Update the master count for now
                    # if response['master_profile'].count != self.master_profile[0].get('count'):
                    #     self.log("Master Profile Count Diff, Was {0} / Now {1}".format(response['master_profile'].count, self.master_profile[0].get('count')))
                    #     to_be_updated = True

                    # Cannot Update the SSH Key for now
                    # if response['linux_profile'].ssh.public_keys[0].key_data != self.linux_profile[0].get('ssh_key'):
                    #     self.log("Linux Profile Diff SSH, Was {0} / Now {1}".format(response['linux_profile'].ssh.public_keys[0].key_data, self.linux_profile[0].get('ssh_key')))
                    #     to_be_updated = True
                    
                    # Cannot Update the Username for now
                    # if response['linux_profile'].admin_username != self.linux_profile[0].get('admin_username'):
                    #     self.log("Linux Profile Diff User, Was {0} / Now {1}".format(response['linux_profile'].admin_username, self.linux_profile[0].get('admin_username')))
                    #     to_be_updated = True
                   
                    if len(response['agent_pool_profiles']) != len(self.agent_pool_profiles):
                        self.log("Agent Pool length is diff, TBU")
                        to_be_updated = True

                    for profile_result in response['agent_pool_profiles']:
                        matched = False
                        for profile_self in self.agent_pool_profiles:
                            if profile_result['name'] == profile_self['name']:
                                matched = True
                                if profile_result['count'] != profile_self['count'] or profile_result['vm_size'] != profile_self['vm_size']:
                                    self.log("Agent Profile Diff - Count was {0} / Now {1} - Vm_size was {2} / Now {3}".format(profile_result['count'], profile_self['count'], profile_result['vm_size'], profile_self['vm_size']))
                                    to_be_updated = True
                        if not matched:
                            self.log("Agent Pool not found, TBU")
                            to_be_updated = True

            if to_be_updated:
                self.log("Need to Create / Update the ACS instance")

                results['name'] = self.name
                results['location'] = self.location
                results['tags'] = self.tags
                results['orchestrator_profile'] = self.orchestration_platform
                results['service_principal_profile'] = self.service_principal
                results['linux_profile'] = self.linux_profile
                results['master_profile'] = self.master_profile
                results['agent_pool_profiles'] = self.agent_pool_profiles
                results['diagnostics_profile'] = self.diagnostics_profile

                self.results['state'] = self.create_acs(results)
                self.results['changed'] = True

                self.log("Creation / Update done")
        elif self.state == 'absent':
            self.delete_acs()
            self.log("ACS instance deleted")

        return self.results

    def create_acs(self, results):
        self.log("Creating / Updating the ACS instance {0}".format(self.name))

        service_principal_profile = None
        agentpools = []

        if results.get('agent_pool_profiles'):
            for profile in results.get('agent_pool_profiles'):
                self.log("Trying to push the following Profile {0}".format(profile))
                agentpools.append(create_agent_pool_profile_instance(profile))

        if results.get('orchestrator_profile') == 'Kubernetes':
            service_principal_profile = create_service_principal_profile_instance(results.get('service_principal_profile'))
        
        parameters = ContainerService(
            location = results.get('location'),
            tags = results.get('tags'),
            orchestrator_profile = create_orch_platform_instance(results.get('orchestrator_profile')),
            service_principal_profile = service_principal_profile,
            linux_profile = create_linux_profile_instance(results.get('linux_profile')),
            master_profile = create_master_profile_instance(results.get('master_profile')),
            agent_pool_profiles = agentpools,
            diagnostics_profile = create_diagnostics_profile_instance(results.get('diagnostics_profile'))
        )

        self.log("orchestrator_profile : {0}".format(parameters.orchestrator_profile))
        self.log("service_principal_profile : {0}".format(parameters.service_principal_profile))
        self.log("linux_profile : {0}".format(parameters.linux_profile))
        self.log("ssh from yaml : {0}".format(results.get('linux_profile')[0]))
        self.log("ssh : {0}".format(parameters.linux_profile.ssh))
        self.log("master_profile : {0}".format(parameters.master_profile))
        self.log("agent_pool_profiles : {0}".format(parameters.agent_pool_profiles))
        self.log("vm_diagnostics : {0}".format(parameters.diagnostics_profile.vm_diagnostics))
        
        try:
            poller = self.containerservice_client.container_services.create_or_update(self.resource_group, self.name, parameters)
            response = self.get_poller_result(poller)
        except CloudError as exc:
            self.log('Error attempting to create the ACS instance.')
            self.fail("Error creating the ACS instance: {0}".format(str(exc)))
        return create_acs_dict(response)

    def delete_acs(self):
        self.log("Deleting the ACS instance {0}".format(self.name))
        try:
            poller = self.containerservice_client.container_services.delete(self.resource_group, self.name)
            self.get_poller_result(poller)
        except CloudError as e:
            self.log('Error attempting to delete the ACS instance.')
            self.fail("Error deleting the ACS instance: {0}".format(str(e)))

        return True

    def get_acs(self):
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