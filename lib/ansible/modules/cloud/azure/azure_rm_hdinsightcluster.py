#!/usr/bin/python
#
# Copyright (c) 2018 Zim Kalinowski, <zikalino@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_hdinsightcluster
version_added: "2.8"
short_description: Manage Cluster instance.
description:
    - Create, update and delete instance of Cluster.

options:
    resource_group:
        description:
            - The name of the resource group.
        required: True
    name:
        description:
            - The name of the cluster.
        required: True
    location:
        description:
            - Resource location. If not set, location from the resource group will be used as default.
    cluster_version:
        description:
            - The version of the cluster.
    os_type:
        description:
            - The type of operating system.
        choices:
            - 'windows'
            - 'linux'
    tier:
        description:
            - The cluster tier.
        choices:
            - 'standard'
            - 'premium'
    cluster_definition:
        description:
            - The cluster definition.
        suboptions:
            blueprint:
                description:
                    - The link to the blueprint.
            kind:
                description:
                    - The type of cluster.
            component_version:
                description:
                    - The versions of different services in the cluster.
            configurations:
                description:
                    - The cluster configurations.
    security_profile:
        description:
            - The security profile.
        suboptions:
            directory_type:
                description:
                    - The directory type.
                choices:
                    - 'active_directory'
            domain:
                description:
                    - "The organization's active directory domain."
            organizational_unit_dn:
                description:
                    - The organizational unit within the Active Directory to place the cluster and service accounts.
            ldaps_urls:
                description:
                    - The LDAPS protocol URLs to communicate with the Active Directory.
                type: list
            domain_username:
                description:
                    - The I(domain) user account that will have admin privileges on the cluster.
            domain_user_password:
                description:
                    - The I(domain) admin password.
            cluster_users_group_dns:
                description:
                    - Optional. The Distinguished Names for cluster user groups
                type: list
    compute_profile:
        description:
            - The compute profile.
        suboptions:
            roles:
                description:
                    - The list of roles in the cluster.
                type: list
                suboptions:
                    name:
                        description:
                            - The name of the role.
                    min_instance_count:
                        description:
                            - The minimum instance count of the cluster.
                    target_instance_count:
                        description:
                            - The instance count of the cluster.
                    hardware_profile:
                        description:
                            - The hardware profile.
                        suboptions:
                            vm_size:
                                description:
                                    - The size of the VM
                    os_profile:
                        description:
                            - The operating system profile.
                        suboptions:
                            linux_operating_system_profile:
                                description:
                                    - The Linux OS profile.
                    virtual_network_profile:
                        description:
                            - The virtual network profile.
                        suboptions:
                            id:
                                description:
                                    - The ID of the virtual network.
                            subnet:
                                description:
                                    - The name of the subnet.
                    data_disks_groups:
                        description:
                            - The data disks groups for the role.
                        type: list
                        suboptions:
                            disks_per_node:
                                description:
                                    - The number of disks per node.
                    script_actions:
                        description:
                            - The list of script actions on the role.
                        type: list
                        suboptions:
                            name:
                                description:
                                    - The name of the script action.
                                required: True
                            uri:
                                description:
                                    - The URI to the script.
                                required: True
                            parameters:
                                description:
                                    - The parameters for the script provided.
                                required: True
    storage_profile:
        description:
            - The storage profile.
        suboptions:
            storageaccounts:
                description:
                    - The list of storage accounts in the cluster.
                type: list
                suboptions:
                    name:
                        description:
                            - The name of the storage account.
                    is_default:
                        description:
                            - Whether or not the storage account is the default storage account.
                    container:
                        description:
                            - The container in the storage account.
                    key:
                        description:
                            - The storage account access key.
    state:
      description:
        - Assert the state of the Cluster.
        - Use 'present' to create or update an Cluster and 'absent' to delete it.
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
  - name: Create (or update) Cluster
    azure_rm_hdinsightcluster:
      resource_group: rg1
      name: cluster1
      location: eastus
      cluster_version: 3.5
      os_type: Linux
      tier: Standard
      cluster_definition:
        kind: Hadoop
        configurations: {
  "gateway": {
    "restAuthCredential.isEnabled": "true",
    "restAuthCredential.username": "admin",
    "restAuthCredential.password": "**********"
  }
}
'''

RETURN = '''
id:
    description:
        - Fully qualified resource Id for the resource.
    returned: always
    type: str
    sample: /subscriptions/subid/resourceGroups/rg1/providers/Microsoft.HDInsight/clusters/cluster1
'''

import time
from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from msrest.polling import LROPoller
    from azure.mgmt.hdinsight import HDInsightManagementClient
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass


class Actions:
    NoAction, Create, Update, Delete = range(4)


class AzureRMClusters(AzureRMModuleBase):
    """Configuration class for an Azure RM Cluster resource"""

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
            location=dict(
                type='str'
            ),
            cluster_version=dict(
                type='str'
            ),
            os_type=dict(
                type='str',
                choices=['windows',
                         'linux']
            ),
            tier=dict(
                type='str',
                choices=['standard',
                         'premium']
            ),
            cluster_definition=dict(
                type='dict'
            ),
            security_profile=dict(
                type='dict'
            ),
            compute_profile=dict(
                type='dict'
            ),
            storage_profile=dict(
                type='dict'
            ),
            state=dict(
                type='str',
                default='present',
                choices=['present', 'absent']
            )
        )

        self.resource_group = None
        self.name = None
        self.parameters = dict()

        self.results = dict(changed=False)
        self.mgmt_client = None
        self.state = None
        self.to_do = Actions.NoAction

        super(AzureRMClusters, self).__init__(derived_arg_spec=self.module_arg_spec,
                                              supports_check_mode=True,
                                              supports_tags=True)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
            elif kwargs[key] is not None:
                if key == "location":
                    self.parameters["location"] = kwargs[key]
                elif key == "cluster_version":
                    self.parameters.setdefault("properties", {})["cluster_version"] = kwargs[key]
                elif key == "os_type":
                    self.parameters.setdefault("properties", {})["os_type"] = _snake_to_camel(kwargs[key], True)
                elif key == "tier":
                    self.parameters.setdefault("properties", {})["tier"] = _snake_to_camel(kwargs[key], True)
                elif key == "cluster_definition":
                    self.parameters.setdefault("properties", {})["cluster_definition"] = kwargs[key]
                elif key == "security_profile":
                    ev = kwargs[key]
                    if 'directory_type' in ev:
                        if ev['directory_type'] == 'active_directory':
                            ev['directory_type'] = 'ActiveDirectory'
                    self.parameters.setdefault("properties", {})["security_profile"] = ev
                elif key == "compute_profile":
                    self.parameters.setdefault("properties", {})["compute_profile"] = kwargs[key]
                elif key == "storage_profile":
                    self.parameters.setdefault("properties", {})["storage_profile"] = kwargs[key]

        old_response = None
        response = None

        self.mgmt_client = self.get_mgmt_svc_client(HDInsightManagementClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        resource_group = self.get_resource_group(self.resource_group)

        if "location" not in self.parameters:
            self.parameters["location"] = resource_group.location

        old_response = self.get_cluster()

        if not old_response:
            self.log("Cluster instance doesn't exist")
            if self.state == 'absent':
                self.log("Old instance didn't exist")
            else:
                self.to_do = Actions.Create
        else:
            self.log("Cluster instance already exists")
            if self.state == 'absent':
                self.to_do = Actions.Delete
            elif self.state == 'present':
                self.log("Need to check if Cluster instance has to be deleted or may be updated")
                self.to_do = Actions.Update

        if (self.to_do == Actions.Create) or (self.to_do == Actions.Update):
            self.log("Need to Create / Update the Cluster instance")

            if self.check_mode:
                self.results['changed'] = True
                return self.results

            response = self.create_update_cluster()

            if not old_response:
                self.results['changed'] = True
            else:
                self.results['changed'] = old_response.__ne__(response)
            self.log("Creation / Update done")
        elif self.to_do == Actions.Delete:
            self.log("Cluster instance deleted")
            self.results['changed'] = True

            if self.check_mode:
                return self.results

            self.delete_cluster()
            # make sure instance is actually deleted, for some Azure resources, instance is hanging around
            # for some time after deletion -- this should be really fixed in Azure.
            while self.get_cluster():
                time.sleep(20)
        else:
            self.log("Cluster instance unchanged")
            self.results['changed'] = False
            response = old_response

        self.results.update(self.format_item(response))
        return self.results

    def create_update_cluster(self):
        '''
        Creates or updates Cluster with the specified configuration.

        :return: deserialized Cluster instance state dictionary
        '''
        self.log("Creating / Updating the Cluster instance {0}".format(self.name))

        try:
            if self.to_do == Actions.Create:
                response = self.mgmt_client.clusters.create(resource_group_name=self.resource_group,
                                                            cluster_name=self.name,
                                                            parameters=self.parameters)
            else:
                response = self.mgmt_client.clusters.update(resource_group_name=self.resource_group,
                                                            cluster_name=self.name,
                                                            parameters=self.parameters)
            if isinstance(response, LROPoller):
                response = self.get_poller_result(response)

        except CloudError as exc:
            self.log('Error attempting to create the Cluster instance.')
            self.fail("Error creating the Cluster instance: {0}".format(str(exc)))
        return response.as_dict()

    def delete_cluster(self):
        '''
        Deletes specified Cluster instance in the specified subscription and resource group.

        :return: True
        '''
        self.log("Deleting the Cluster instance {0}".format(self.name))
        try:
            response = self.mgmt_client.clusters.delete(resource_group_name=self.resource_group,
                                                        cluster_name=self.name)
        except CloudError as e:
            self.log('Error attempting to delete the Cluster instance.')
            self.fail("Error deleting the Cluster instance: {0}".format(str(e)))

        return True

    def get_cluster(self):
        '''
        Gets the properties of the specified Cluster.

        :return: deserialized Cluster instance state dictionary
        '''
        self.log("Checking if the Cluster instance {0} is present".format(self.name))
        found = False
        try:
            response = self.mgmt_client.clusters.get(resource_group_name=self.resource_group,
                                                     cluster_name=self.name)
            found = True
            self.log("Response : {0}".format(response))
            self.log("Cluster instance : {0} found".format(response.name))
        except Exception as e:
            self.log('Did not find the Cluster instance.')
        if found is True:
            return response.as_dict()

        return False

    def format_item(self, item):
        d = item.as_dict()
        d = {
            'id': d['id']
        }
        return d


def _snake_to_camel(snake, capitalize_first=False):
    if capitalize_first:
        return ''.join(x.capitalize() or '_' for x in snake.split('_'))
    else:
        return snake.split('_')[0] + ''.join(x.capitalize() or '_' for x in snake.split('_')[1:])


def main():
    """Main execution"""
    AzureRMClusters()


if __name__ == '__main__':
    main()
