#!/usr/bin/python
#
# Copyright (c) 2019 Zim Kalinowski, (@zikalino)
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
short_description: Manage Azure HDInsight Cluster instance.
description:
    - Create, update and delete instance of Azure HDInsight Cluster.

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
    compute_profile_roles:
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
            vm_size:
                description:
                    - The size of the VM
            linux_profile:
                description:
                    - The Linux OS profile.
    storage_accounts:
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
                    - The container in the storage account, only to be specified for WASB storage accounts.
            file_system:
                description:
                    - The filesystem, only to be specified for Azure Data Lake Storage Gen 2.
            key:
                description:
                    - The storage account access key.
    state:
      description:
        - Assert the state of the cluster.
        - Use C(present) to create or update a cluster and C(absent) to delete it.
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
- name: Create instance of HDInsight Cluster
  azure_rm_hdinsightcluster:
    resource_group: myResourceGroup
    name: myCluster
    location: eastus2
    cluster_version: 3.6
    os_type: linux
    tier: standard
    cluster_definition:
      kind: spark
      configurations:
        gateway:
          restAuthCredential.username: http-user
          restAuthCredential.password: MuABCPassword!!@123
    storage_accounts:
      - name: myStorageAccount.blob.core.windows.net
        is_default: yes
        container: myContainer
        key: GExmaxH4lDNdHA9nwAsCt8t4AOQas2y9vXQP1kKALTram7Q3/5xLVIab3+nYG1x63Xyak9/VXxQyNBHA9pDWw==
    compute_profile_roles:
      - name: headnode
        target_instance_count: 2
        hardware_profile:
          vm_size: Standard_D3
        linux_profile:
          username: sshuser
          password: MuABCPassword!!@123
      - name: workernode
        target_instance_count: 2
        vm_size: Standard_D3
        linux_profile:
          username: sshuser
          password: MuABCPassword!!@123
'''

RETURN = '''
id:
    description:
        - Fully qualified resource id of the cluster.
    returned: always
    type: str
    sample: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.HDInsight/clusters/myCluster
'''

import time
from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from msrest.polling import LROPoller
    from msrestazure.azure_operation import AzureOperationPoller
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
            compute_profile_roles=dict(
                type='list'
            ),
            storage_accounts=dict(
                type='list'
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
                self.parameters[key] = kwargs[key]

        expand(self.parameters, ['cluster_version'], expand='properties')
        expand(self.parameters, ['os_type'], expand='properties', camelize=True)
        expand(self.parameters, ['tier'], expand='properties', camelize=True)
        expand(self.parameters, ['cluster_definition'], expand='properties')
        expand(self.parameters, ['compute_profile_roles', 'vm_size'], expand='hardware_profile')
        expand(self.parameters, ['compute_profile_roles', 'linux_profile'], rename='linux_operating_system_profile', expand='os_profile')
        expand(self.parameters, ['compute_profile_roles'], rename='roles', expand='compute_profile')
        expand(self.parameters, ['compute_profile'], expand='properties')
        expand(self.parameters, ['storage_accounts'], rename='storageaccounts', expand='storage_profile')
        expand(self.parameters, ['storage_profile'], expand='properties')

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
                # get doesn't return storage profile, so can't be compared
                old_response['properties']['storage_profile'] = self.parameters['properties']['storage_profile']

                # cluster version returned by get may be longer, for instance "3.6.1000.67"
                if old_response['properties']['cluster_version'].startswith(self.parameters['properties']['cluster_version']):
                     self.parameters['properties']['cluster_version'] = old_response['properties']['cluster_version']

                if (not default_compare(self.parameters, old_response, '', self.results)):
                    self.results['old_response'] = old_response
                    self.to_do = Actions.Update

        if (self.to_do == Actions.Create) or (self.to_do == Actions.Update):
            self.log("Need to Create / Update the Cluster instance")

            if self.check_mode:
                self.results['changed'] = True
                return self.results

            response = self.create_update_cluster()

            self.results['changed'] = True
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

        if self.state == 'present':
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
                                                            cluster_name=self.name)
            if isinstance(response, LROPoller) or isinstance(response, AzureOperationPoller):
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

    def format_item(self, d):
        d = {
            'id': d.get('id', None)
        }
        return d


def default_compare(new, old, path, result):
    if new is None:
        return True
    elif isinstance(new, dict):
        if not isinstance(old, dict):
            result['compare'] = 'changed [' + path + '] old dict is null'
            return False
        for k in new.keys():
            if not default_compare(new.get(k), old.get(k, None), path + '/' + k, result):
                return False
        return True
    elif isinstance(new, list):
        if not isinstance(old, list) or len(new) != len(old):
            result['compare'] = 'changed [' + path + '] length is different or null'
            return False
        elif len(old) == 0:
            return True
        elif isinstance(old[0], dict):
            key = None
            if 'id' in old[0] and 'id' in new[0]:
                key = 'id'
            elif 'name' in old[0] and 'name' in new[0]:
                key = 'name'
            else:
                key = list(old[0])[0]
            new = sorted(new, key=lambda x: x.get(key, ''))
            old = sorted(old, key=lambda x: x.get(key, ''))
        else:
            new = sorted(new)
            old = sorted(old)
        for i in range(len(new)):
            if not default_compare(new[i], old[i], path + '/*', result):
                return False
        return True
    else:
        if path == '/location' or path.endswith('location_name'):
            new = new.replace(' ', '').lower()
            old = new.replace(' ', '').lower()
        if new == old:
            return True
        else:
            result['compare'] = 'changed [' + path + '] ' + str(new) + ' != ' + str(old)
            return False


def expand(d, path, **kwargs):
    expandx = kwargs.get('expand', None)
    rename = kwargs.get('rename', None)
    camelize = kwargs.get('camelize', False)
    camelize_lower = kwargs.get('camelize_lower', False)
    upper = kwargs.get('upper', False)
    map = kwargs.get('map', None)
    if isinstance(d, list):
        for i in range(len(d)):
            expand(d[i], path, **kwargs)
    elif isinstance(d, dict):
        if len(path) == 1:
            old_name = path[0]
            new_name = old_name if rename is None else rename
            old_value = d.get(old_name, None)
            new_value = None
            if old_value is not None:
                if map is not None:
                    new_value = map.get(old_value, None)
                if new_value is None:
                    if camelize:
                        new_value = _snake_to_camel(old_value, True)
                    elif camelize_lower:
                        new_value = _snake_to_camel(old_value, False)
                    elif upper:
                        new_value = old_value.upper()
                    else:
                        new_value = old_value
            if expandx is None:
                # just rename
                if new_name != old_name:
                    d.pop(old_name, None)
            else:
                # expand and rename
                d[expandx] = d.get(expandx, {})
                d.pop(old_name, None)
                d = d[expandx]
            d[new_name] = new_value
        else:
            sd = d.get(path[0], None)
            if sd is not None:
                expand(sd, path[1:], **kwargs)


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
