#!/usr/bin/python
#
# Copyright (c) 2018 Sertac Ozercan, <seozerca@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: azure_rm_aks
version_added: "2.6"
short_description: Manage a managed Azure Container Service (AKS) Instance.
description:
    - Create, update and delete a managed Azure Container Service (AKS) Instance.

options:
    resource_group:
        description:
            - Name of a resource group where the managed Azure Container Services (AKS) exists or will be created.
        required: true
    name:
        description:
            - Name of the managed Azure Container Services (AKS) instance.
        required: true
    state:
        description:
            - Assert the state of the AKS. Use C(present) to create or update an AKS and C(absent) to delete it.
        default: present
        choices:
            - absent
            - present
    location:
        description:
            - Valid azure location. Defaults to location of the resource group.
    dns_prefix:
        description:
            - DNS prefix specified when creating the managed cluster.
    kubernetes_version:
        description:
            - Version of Kubernetes specified when creating the managed cluster.
    linux_profile:
        description:
            - The linux profile suboptions.
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
        suboptions:
            name:
                description:
                  - Unique name of the agent pool profile in the context of the subscription and resource group.
                required: true
            count:
                description:
                    - Number of agents (VMs) to host docker containers.
                    - Allowed values must be in the range of 1 to 100 (inclusive).
                required: true
            vm_size:
                description:
                    - The VM Size of each of the Agent Pool VM's (e.g. Standard_F1 / Standard_D2v2).
                required: true
            os_disk_size_gb:
                description:
                    - Size of the OS disk.
    service_principal:
        description:
            - The service principal suboptions.
        suboptions:
            client_id:
                description:
                    - The ID for the Service Principal.
                required: true
            client_secret:
                description:
                    - The secret password associated with the service principal.
                required: true
    enable_rbac:
        description:
            - Enable RBAC.
            - Existing non-RBAC enabled AKS clusters cannot currently be updated for RBAC use.
        type: bool
        default: no
        version_added: 2.8
    network_profile:
        description:
            - Profile of network configuration.
        suboptions:
            network_plugin:
                description:
                    - Network plugin used for building Kubernetes network.
                    - This property cannot been changed.
                    - With C(kubenet), nodes get an IP address from the Azure virtual network subnet.
                    - AKS features such as Virtual Nodes or network policies aren't supported with C(kubenet).
                    - C(azure) enables Azure Container Networking Interface(CNI), every pod gets an IP address from the subnet and can be accessed directly.
                choices:
                    - azure
                    - kubenet
            network_policy:
                description: Network policy used for building Kubernetes network.
            pod_cidr:
                description:
                    - A CIDR notation IP range from which to assign pod IPs when kubenet is used.
                    - It should be a large address space that isn't in use elsewhere in your network environment.
                    - This address range must be large enough to accommodate the number of nodes that you expect to scale up to.
            service_cidr:
                description:
                    - A CIDR notation IP range from which to assign service cluster IPs.
                    - It must not overlap with any Subnet IP ranges.
                    - It should be the *.10 address of your service IP address range.
            dns_service_ip:
                description:
                    - An IP address assigned to the Kubernetes DNS service.
                    - It must be within the Kubernetes service address range specified in serviceCidr.
            docker_bridge_cidr:
                description:
                    - A CIDR notation IP range assigned to the Docker bridge network.
                    - It must not overlap with any Subnet IP ranges or the Kubernetes service address range.
        version_added: 2.8
    aad_profile:
        description:
            - Profile of Azure Active Directory configuration.
        suboptions:
            client_app_id:
                description: The client AAD application ID.
            server_app_id:
                description: The server AAD application ID.
            server_app_secret:
                description: The server AAD application secret.
            tenant_id:
                description:
                    - The AAD tenant ID to use for authentication.
                    - If not specified, will use the tenant of the deployment subscription.
        version_added: 2.8
    addon:
        description:
            - Profile of managed cluster add-on.
            - Key can be C(http_application_routing), C(monitoring), C(virtual_node).
            - Value must be a dict contains a bool variable C(enabled).
        type: dict
        suboptions:
            http_application_routing:
                description:
                    - The HTTP application routing solution makes it easy to access applications that are deployed to your cluster.
                type: dict
                suboptions:
                    enabled:
                        description:
                            - Whether the solution enabled.
                        type: bool
            monitoring:
                description:
                    - It gives you performance visibility by collecting memory and processor metrics from controllers, nodes,
                      and containers that are available in Kubernetes through the Metrics API.
                type: dict
                suboptions:
                    enabled:
                        description:
                            - Whether the solution enabled.
                        type: bool
                    log_analytics_workspace_resource_id:
                        description:
                            - Where to store the container metrics.
            virtual_node:
                description:
                    - With virtual nodes, you have quick provisioning of pods, and only pay per second for their execution time.
                    - You don't need to wait for Kubernetes cluster autoscaler to deploy VM compute nodes to run the additional pods.
                type: dict
                suboptions:
                    enabled:
                        description:
                            - Whether the solution enabled.
                        type: bool
                    subnet_resource_id:
                        description:
                            - Subnet associdated to the cluster.
        version_added: 2.8

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Sertac Ozercan (@sozercan)"
    - "Yuwei Zhou (@yuwzho)"

'''

EXAMPLES = '''
    - name: Create a managed Azure Container Services (AKS) instance
      azure_rm_aks:
        name: acctestaks1
        location: eastus
        resource_group: myResourceGroup
        dns_prefix: akstest
        linux_profile:
          admin_username: azureuser
          ssh_key: ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAA...
        service_principal:
          client_id: "cf72ca99-f6b9-4004-b0e0-bee10c521948"
          client_secret: "mySPNp@ssw0rd!"
        agent_pool_profiles:
          - name: default
            count: 5
            vm_size: Standard_D2_v2
        tags:
          Environment: Production

    - name: Remove a managed Azure Container Services (AKS) instance
      azure_rm_aks:
        name: acctestaks3
        resource_group: myResourceGroup
        state: absent
'''
RETURN = '''
state:
    description: Current state of the Azure Container Service (AKS)
    returned: always
    type: dict
    example:
        agent_pool_profiles:
         - count: 1
           dns_prefix: Null
           name: default
           os_disk_size_gb: Null
           os_type: Linux
           ports: Null
           storage_profile: ManagedDisks
           vm_size: Standard_DS1_v2
           vnet_subnet_id: Null
        changed: false
        dns_prefix: aks9860bdcd89
        id: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourcegroups/yuwzhoaks/providers/Microsoft.ContainerService/managedClusters/aks9860bdc"
        kube_config: "......"
        kubernetes_version: 1.11.4
        linux_profile:
           admin_username: azureuser
           ssh_key: ssh-rsa AAAAB3NzaC1yc2EAAAADA.....
        location: eastus
        name: aks9860bdc
        provisioning_state: Succeeded
        service_principal_profile:
           client_id: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
        tags: {}
        type: Microsoft.ContainerService/ManagedClusters
'''
from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    # This is handled in azure_rm_common
    pass


def create_aks_dict(aks):
    '''
    Helper method to deserialize a ContainerService to a dict
    :param: aks: ContainerService or AzureOperationPoller with the Azure callback object
    :return: dict with the state on Azure
    '''

    return dict(
        id=aks.id,
        name=aks.name,
        location=aks.location,
        dns_prefix=aks.dns_prefix,
        kubernetes_version=aks.kubernetes_version,
        tags=aks.tags,
        linux_profile=create_linux_profile_dict(aks.linux_profile),
        service_principal_profile=create_service_principal_profile_dict(
            aks.service_principal_profile),
        provisioning_state=aks.provisioning_state,
        agent_pool_profiles=create_agent_pool_profiles_dict(
            aks.agent_pool_profiles),
        type=aks.type,
        kube_config=aks.kube_config,
        enable_rbac=aks.enable_rbac,
        network_profile=create_network_profiles_dict(aks.network_profile),
        aad_profile=create_aad_profiles_dict(aks.aad_profile),
        addon=create_addon_dict(aks.addon_profiles),
        fqdn=aks.fqdn,
        node_resource_group=aks.node_resource_group
    )


def create_network_profiles_dict(network):
    return dict(
        network_plugin=network.network_plugin,
        network_policy=network.network_policy,
        pod_cidr=network.pod_cidr,
        service_cidr=network.service_cidr,
        dns_service_ip=network.dns_service_ip,
        docker_bridge_cidr=network.docker_bridge_cidr
    ) if network else dict()


def create_aad_profiles_dict(aad):
    return aad.as_dict() if aad else dict()


def create_addon_dict(addon):
    result = dict()
    addon = addon or dict()
    for key in addon.keys():
        result[key] = addon[key].config
        result[key]['enabled'] = addon[key].enabled
    return result


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
        os_disk_size_gb=profile.os_disk_size_gb,
        storage_profile=profile.storage_profile,
        vnet_subnet_id=profile.vnet_subnet_id,
        os_type=profile.os_type
    ) for profile in agentpoolprofiles] if agentpoolprofiles else None


def create_addon_profiles_spec():
    '''
    Helper method to parse the ADDONS dictionary and generate the addon spec
    '''
    spec = dict()
    for key in ADDONS.keys():
        values = ADDONS[key]
        addon_spec = dict(
            enabled=dict(type='bool', default=True)
        )
        configs = values.get('config') or {}
        for item in configs.keys():
            addon_spec[item] = dict(type='str', aliases=[configs[item]], required=True)
        spec[key] = dict(type='dict', options=addon_spec, aliases=[values['name']])
    return spec


ADDONS = {
    'http_application_routing': dict(name='httpApplicationRouting'),
    'monitoring': dict(name='omsagent', config={'log_analytics_workspace_resource_id': 'logAnalyticsWorkspaceResourceID'}),
    'virtual_node': dict(name='aciConnector', config={'subnet_resource_id': 'SubnetName'})
}


linux_profile_spec = dict(
    admin_username=dict(type='str', required=True),
    ssh_key=dict(type='str', required=True)
)


service_principal_spec = dict(
    client_id=dict(type='str', required=True),
    client_secret=dict(type='str', no_log=True)
)


agent_pool_profile_spec = dict(
    name=dict(type='str', required=True),
    count=dict(type='int', required=True),
    vm_size=dict(type='str', required=True),
    os_disk_size_gb=dict(type='int'),
    dns_prefix=dict(type='str'),
    ports=dict(type='list', elements='int'),
    storage_profiles=dict(type='str', choices=[
                          'StorageAccount', 'ManagedDisks']),
    vnet_subnet_id=dict(type='str'),
    os_type=dict(type='str', choices=['Linux', 'Windows'])
)


network_profile_spec = dict(
    network_plugin=dict(type='str', choices=['azure', 'kubenet']),
    network_policy=dict(type='str'),
    pod_cidr=dict(type='str'),
    service_cidr=dict(type='str'),
    dns_service_ip=dict(type='str'),
    docker_bridge_cidr=dict(type='str')
)


aad_profile_spec = dict(
    client_app_id=dict(type='str'),
    server_app_id=dict(type='str'),
    server_app_secret=dict(type='str', no_log=True),
    tenant_id=dict(type='str')
)


class AzureRMManagedCluster(AzureRMModuleBase):
    """Configuration class for an Azure RM container service (AKS) resource"""

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
            dns_prefix=dict(
                type='str'
            ),
            kubernetes_version=dict(
                type='str'
            ),
            linux_profile=dict(
                type='dict',
                options=linux_profile_spec
            ),
            agent_pool_profiles=dict(
                type='list',
                elements='dict',
                options=agent_pool_profile_spec
            ),
            service_principal=dict(
                type='dict',
                options=service_principal_spec
            ),
            enable_rbac=dict(
                type='bool',
                default=False
            ),
            network_profile=dict(
                type='dict',
                options=network_profile_spec
            ),
            aad_profile=dict(
                type='dict',
                options=aad_profile_spec
            ),
            addon=dict(
                type='dict',
                options=create_addon_profiles_spec()
            )
        )

        self.resource_group = None
        self.name = None
        self.location = None
        self.dns_prefix = None
        self.kubernetes_version = None
        self.tags = None
        self.state = None
        self.linux_profile = None
        self.agent_pool_profiles = None
        self.service_principal = None
        self.enable_rbac = False
        self.network_profile = None
        self.aad_profile = None
        self.addon = None

        required_if = [
            ('state', 'present', [
             'dns_prefix', 'linux_profile', 'agent_pool_profiles', 'service_principal'])
        ]

        self.results = dict(changed=False)

        super(AzureRMManagedCluster, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                    supports_check_mode=True,
                                                    supports_tags=True,
                                                    required_if=required_if)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        resource_group = None
        to_be_updated = False
        update_tags = False

        resource_group = self.get_resource_group(self.resource_group)
        if not self.location:
            self.location = resource_group.location

        response = self.get_aks()

        # Check if the AKS instance already present in the RG
        if self.state == 'present':
            # For now Agent Pool cannot be more than 1, just remove this part in the future if it change
            agentpoolcount = len(self.agent_pool_profiles)
            if agentpoolcount > 1:
                self.fail('You cannot specify more than one agent_pool_profiles currently')

            available_versions = self.get_all_versions()
            if not response:
                to_be_updated = True
                if self.kubernetes_version not in available_versions.keys():
                    self.fail("Unsupported kubernetes version. Expected one of {0} but got {1}".format(available_versions.keys(), self.kubernetes_version))
            else:
                self.results = response
                self.results['changed'] = False
                self.log('Results : {0}'.format(response))
                update_tags, response['tags'] = self.update_tags(response['tags'])

                if response['provisioning_state'] == "Succeeded":

                    def is_property_changed(profile, property, ignore_case=False):
                        base = response[profile].get(property)
                        new = getattr(self, profile).get(property)
                        if ignore_case:
                            return base.lower() != new.lower()
                        else:
                            return base != new

                    # Cannot Update the SSH Key for now // Let service to handle it
                    if is_property_changed('linux_profile', 'ssh_key'):
                        self.log(("Linux Profile Diff SSH, Was {0} / Now {1}"
                                  .format(response['linux_profile']['ssh_key'], self.linux_profile.get('ssh_key'))))
                        to_be_updated = True
                        # self.module.warn("linux_profile.ssh_key cannot be updated")

                    # self.log("linux_profile response : {0}".format(response['linux_profile'].get('admin_username')))
                    # self.log("linux_profile self : {0}".format(self.linux_profile[0].get('admin_username')))
                    # Cannot Update the Username for now // Let service to handle it
                    if is_property_changed('linux_profile', 'admin_username'):
                        self.log(("Linux Profile Diff User, Was {0} / Now {1}"
                                  .format(response['linux_profile']['admin_username'], self.linux_profile.get('admin_username'))))
                        to_be_updated = True
                        # self.module.warn("linux_profile.admin_username cannot be updated")

                    # Cannot have more that one agent pool profile for now
                    if len(response['agent_pool_profiles']) != len(self.agent_pool_profiles):
                        self.log("Agent Pool count is diff, need to updated")
                        to_be_updated = True

                    if response['kubernetes_version'] != self.kubernetes_version:
                        upgrade_versions = available_versions.get(response['kubernetes_version']) or available_versions.keys()
                        if upgrade_versions and self.kubernetes_version not in upgrade_versions:
                            self.fail('Cannot upgrade kubernetes version to {0}, supported value are {1}'.format(self.kubernetes_version, upgrade_versions))
                        to_be_updated = True

                    if response['enable_rbac'] != self.enable_rbac:
                        to_be_updated = True

                    if self.network_profile:
                        for key in self.network_profile.keys():
                            original = response['network_profile'].get(key) or ''
                            if self.network_profile[key] and self.network_profile[key].lower() != original.lower():
                                to_be_updated = True

                    def compare_addon(origin, patch, config):
                        if not patch:
                            return True
                        if not origin:
                            return False
                        if origin['enabled'] != patch['enabled']:
                            return False
                        config = config or dict()
                        for key in config.keys():
                            if origin.get(config[key]) != patch.get(key):
                                return False
                        return True

                    if self.addon:
                        for key in ADDONS.keys():
                            addon_name = ADDONS[key]['name']
                            if not compare_addon(response['addon'].get(addon_name), self.addon.get(key), ADDONS[key].get('config')):
                                to_be_updated = True

                    for profile_result in response['agent_pool_profiles']:
                        matched = False
                        for profile_self in self.agent_pool_profiles:
                            if profile_result['name'] == profile_self['name']:
                                matched = True
                                os_disk_size_gb = profile_self.get('os_disk_size_gb') or profile_result['os_disk_size_gb']
                                if profile_result['count'] != profile_self['count'] \
                                        or profile_result['vm_size'] != profile_self['vm_size'] \
                                        or profile_result['os_disk_size_gb'] != os_disk_size_gb \
                                        or profile_result['vnet_subnet_id'] != profile_self.get('vnet_subnet_id', profile_result['vnet_subnet_id']):
                                    self.log(("Agent Profile Diff - Origin {0} / Update {1}".format(str(profile_result), str(profile_self))))
                                    to_be_updated = True
                        if not matched:
                            self.log("Agent Pool not found")
                            to_be_updated = True

            if to_be_updated:
                self.log("Need to Create / Update the AKS instance")

                if not self.check_mode:
                    self.results = self.create_update_aks()
                    self.log("Creation / Update done")

                self.results['changed'] = True
            elif update_tags:
                self.log("Need to Update the AKS tags")

                if not self.check_mode:
                    self.results['tags'] = self.update_aks_tags()
                self.results['changed'] = True
            return self.results

        elif self.state == 'absent' and response:
            self.log("Need to Delete the AKS instance")
            self.results['changed'] = True

            if self.check_mode:
                return self.results

            self.delete_aks()

            self.log("AKS instance deleted")

        return self.results

    def create_update_aks(self):
        '''
        Creates or updates a managed Azure container service (AKS) with the specified configuration of agents.

        :return: deserialized AKS instance state dictionary
        '''
        self.log("Creating / Updating the AKS instance {0}".format(self.name))

        agentpools = []

        if self.agent_pool_profiles:
            agentpools = [self.create_agent_pool_profile_instance(profile) for profile in self.agent_pool_profiles]

        service_principal_profile = self.create_service_principal_profile_instance(self.service_principal)

        parameters = self.managedcluster_models.ManagedCluster(
            location=self.location,
            dns_prefix=self.dns_prefix,
            kubernetes_version=self.kubernetes_version,
            tags=self.tags,
            service_principal_profile=service_principal_profile,
            agent_pool_profiles=agentpools,
            linux_profile=self.create_linux_profile_instance(self.linux_profile),
            enable_rbac=self.enable_rbac,
            network_profile=self.create_network_profile_instance(self.network_profile),
            aad_profile=self.create_aad_profile_instance(self.aad_profile),
            addon_profiles=self.create_addon_profile_instance(self.addon)
        )

        # self.log("service_principal_profile : {0}".format(parameters.service_principal_profile))
        # self.log("linux_profile : {0}".format(parameters.linux_profile))
        # self.log("ssh from yaml : {0}".format(results.get('linux_profile')[0]))
        # self.log("ssh : {0}".format(parameters.linux_profile.ssh))
        # self.log("agent_pool_profiles : {0}".format(parameters.agent_pool_profiles))

        try:
            poller = self.managedcluster_client.managed_clusters.create_or_update(self.resource_group, self.name, parameters)
            response = self.get_poller_result(poller)
            response.kube_config = self.get_aks_kubeconfig()
            return create_aks_dict(response)
        except CloudError as exc:
            self.log('Error attempting to create the AKS instance.')
            self.fail("Error creating the AKS instance: {0}".format(exc.message))

    def update_aks_tags(self):
        try:
            poller = self.managedcluster_client.managed_clusters.update_tags(self.resource_group, self.name, self.tags)
            response = self.get_poller_result(poller)
            return response.tags
        except CloudError as exc:
            self.fail("Error attempting to update AKS tags: {0}".format(exc.message))

    def delete_aks(self):
        '''
        Deletes the specified managed container service (AKS) in the specified subscription and resource group.

        :return: True
        '''
        self.log("Deleting the AKS instance {0}".format(self.name))
        try:
            poller = self.managedcluster_client.managed_clusters.delete(self.resource_group, self.name)
            self.get_poller_result(poller)
            return True
        except CloudError as e:
            self.log('Error attempting to delete the AKS instance.')
            self.fail("Error deleting the AKS instance: {0}".format(e.message))
            return False

    def get_aks(self):
        '''
        Gets the properties of the specified container service.

        :return: deserialized AKS instance state dictionary
        '''
        self.log("Checking if the AKS instance {0} is present".format(self.name))
        try:
            response = self.managedcluster_client.managed_clusters.get(self.resource_group, self.name)
            self.log("Response : {0}".format(response))
            self.log("AKS instance : {0} found".format(response.name))
            response.kube_config = self.get_aks_kubeconfig()
            return create_aks_dict(response)
        except CloudError:
            self.log('Did not find the AKS instance.')
            return False

    def get_all_versions(self):
        try:
            result = dict()
            response = self.containerservice_client.container_services.list_orchestrators(self.location, resource_type='managedClusters')
            orchestrators = response.orchestrators
            for item in orchestrators:
                result[item.orchestrator_version] = [x.orchestrator_version for x in item.upgrades] if item.upgrades else []
            return result
        except Exception as exc:
            self.fail('Error when getting AKS supported kubernetes version list for location {0} - {1}'.format(self.location, exc.message or str(exc)))

    def get_aks_kubeconfig(self):
        '''
        Gets kubeconfig for the specified AKS instance.

        :return: AKS instance kubeconfig
        '''
        access_profile = self.managedcluster_client.managed_clusters.get_access_profile(resource_group_name=self.resource_group,
                                                                                        resource_name=self.name,
                                                                                        role_name="clusterUser")
        return access_profile.kube_config.decode('utf-8')

    def create_agent_pool_profile_instance(self, agentpoolprofile):
        '''
        Helper method to serialize a dict to a ManagedClusterAgentPoolProfile
        :param: agentpoolprofile: dict with the parameters to setup the ManagedClusterAgentPoolProfile
        :return: ManagedClusterAgentPoolProfile
        '''
        return self.managedcluster_models.ManagedClusterAgentPoolProfile(**agentpoolprofile)

    def create_service_principal_profile_instance(self, spnprofile):
        '''
        Helper method to serialize a dict to a ManagedClusterServicePrincipalProfile
        :param: spnprofile: dict with the parameters to setup the ManagedClusterServicePrincipalProfile
        :return: ManagedClusterServicePrincipalProfile
        '''
        return self.managedcluster_models.ManagedClusterServicePrincipalProfile(
            client_id=spnprofile['client_id'],
            secret=spnprofile['client_secret']
        )

    def create_linux_profile_instance(self, linuxprofile):
        '''
        Helper method to serialize a dict to a ContainerServiceLinuxProfile
        :param: linuxprofile: dict with the parameters to setup the ContainerServiceLinuxProfile
        :return: ContainerServiceLinuxProfile
        '''
        return self.managedcluster_models.ContainerServiceLinuxProfile(
            admin_username=linuxprofile['admin_username'],
            ssh=self.managedcluster_models.ContainerServiceSshConfiguration(public_keys=[
                self.managedcluster_models.ContainerServiceSshPublicKey(key_data=str(linuxprofile['ssh_key']))])
        )

    def create_network_profile_instance(self, network):
        return self.managedcluster_models.ContainerServiceNetworkProfile(**network) if network else None

    def create_aad_profile_instance(self, aad):
        return self.managedcluster_models.ManagedClusterAADProfile(**aad) if aad else None

    def create_addon_profile_instance(self, addon):
        result = dict()
        addon = addon or {}
        for key in addon.keys():
            if not ADDONS.get(key):
                self.fail('Unsupported addon {0}'.format(key))
            if addon.get(key):
                name = ADDONS[key]['name']
                config_spec = ADDONS[key].get('config') or dict()
                config = addon[key]
                for v in config_spec.keys():
                    config[config_spec[v]] = config[v]
                result[name] = self.managedcluster_models.ManagedClusterAddonProfile(config=config, enabled=config['enabled'])
        return result


def main():
    """Main execution"""
    AzureRMManagedCluster()


if __name__ == '__main__':
    main()
