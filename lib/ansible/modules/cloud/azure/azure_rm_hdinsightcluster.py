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
            - The version of the cluster. For example I(3.6)
    os_type:
        description:
            - The type of operating system.
        choices:
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
            kind:
                description:
                    - The type of cluster.
                choices:
                    - hadoop
                    - spark
                    - hbase
                    - storm
            gateway_rest_username:
                description:
                    - Gateway REST user name.
            gateway_rest_password:
                description:
                    - Gateway REST password.
    compute_profile_roles:
        description:
            - The list of roles in the cluster.
        type: list
        suboptions:
            name:
                description:
                    - The name of the role.
                choices:
                    - 'headnode'
                    - 'workernode'
                    - 'zookepernode'
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
                suboptions:
                    username:
                        description:
                            - User name
                    password:
                        description:
                            - Password
    storage_accounts:
        description:
            - The list of storage accounts in the cluster.
        type: list
        suboptions:
            name:
                description:
                    - Blob storage endpoint.
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
      gateway_rest_username: http-user
      gateway_rest_password: MuABCPassword!!@123
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
                choices=['linux']
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
        self.tags_changed = False
        self.new_instance_count = None

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

        dict_expand(self.parameters, ['cluster_version'], 'properties')
        dict_camelize(self.parameters, ['os_type'], True)
        dict_expand(self.parameters, ['os_type'], 'properties')
        dict_camelize(self.parameters, ['tier'], True)
        dict_expand(self.parameters, ['tier'], 'properties')

        dict_rename(self.parameters, ['cluster_definition', 'gateway_rest_username'], 'restAuthCredential.username')
        dict_rename(self.parameters, ['cluster_definition', 'gateway_rest_password'], 'restAuthCredential.password')
        dict_expand(self.parameters, ['cluster_definition', 'restAuthCredential.username'], 'gateway')
        dict_expand(self.parameters, ['cluster_definition', 'restAuthCredential.password'], 'gateway')
        dict_expand(self.parameters, ['cluster_definition', 'gateway'], 'configurations')

        dict_expand(self.parameters, ['cluster_definition'], 'properties')
        dict_expand(self.parameters, ['compute_profile_roles', 'vm_size'], 'hardware_profile')
        dict_rename(self.parameters, ['compute_profile_roles', 'linux_profile'], 'linux_operating_system_profile')
        dict_expand(self.parameters, ['compute_profile_roles', 'linux_operating_system_profile'], 'os_profile')
        dict_rename(self.parameters, ['compute_profile_roles'], 'roles')
        dict_expand(self.parameters, ['roles'], 'compute_profile')
        dict_expand(self.parameters, ['compute_profile'], 'properties')
        dict_rename(self.parameters, ['storage_accounts'], 'storageaccounts')
        dict_expand(self.parameters, ['storageaccounts'], 'storage_profile')
        dict_expand(self.parameters, ['storage_profile'], 'properties')

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
                compare_result = {}
                if (not default_compare(self.parameters, old_response, '', compare_result)):
                    if compare_result.pop('/properties/compute_profile/roles/*/target_instance_count', False):
                        # check if it's workernode
                        new_count = 0
                        old_count = 0
                        for role in self.parameters['properties']['compute_profile']['roles']:
                            if role['name'] == 'workernode':
                                new_count = role['target_instance_count']
                        for role in old_response['properties']['compute_profile']['roles']:
                            if role['name'] == 'workernode':
                                old_count = role['target_instance_count']
                        if old_count != new_count:
                            self.new_instance_count = new_count
                            self.to_do = Actions.Update
                    if compare_result.pop('/tags', False):
                        self.to_do = Actions.Update
                        self.tags_changed = True
                    if compare_result:
                        for k in compare_result.keys():
                            self.module.warn("property '" + k + "' cannot be updated (" + compare_result[k] + ")")
                        self.module.warn("only tags and target_instance_count can be updated")

        if (self.to_do == Actions.Create) or (self.to_do == Actions.Update):
            self.log("Need to Create / Update the Cluster instance")
            self.results['changed'] = True
            if self.check_mode:
                return self.results
            response = self.create_update_cluster()
            self.log("Creation / Update done")
        elif self.to_do == Actions.Delete:
            self.log("Cluster instance deleted")
            self.results['changed'] = True
            if self.check_mode:
                return self.results
            self.delete_cluster()
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
                if isinstance(response, LROPoller) or isinstance(response, AzureOperationPoller):
                    response = self.get_poller_result(response)
            else:
                if self.tags_changed:
                    response = self.mgmt_client.clusters.update(resource_group_name=self.resource_group,
                                                                cluster_name=self.name,
                                                                tags=self.parameters.get('tags'))
                    if isinstance(response, LROPoller) or isinstance(response, AzureOperationPoller):
                        response = self.get_poller_result(response)
                if self.new_instance_count:
                    response = self.mgmt_client.clusters.resize(resource_group_name=self.resource_group,
                                                                cluster_name=self.name,
                                                                target_instance_count=self.new_instance_count)
                    if isinstance(response, LROPoller) or isinstance(response, AzureOperationPoller):
                        response = self.get_poller_result(response)
        except CloudError as exc:
            self.fail("Error creating or updating Cluster instance: {0}".format(str(exc)))
        return response.as_dict() if response else {}

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
        match = True
    elif isinstance(new, dict):
        match = True
        if not isinstance(old, dict):
            result[path] = 'old dict is null'
            match = False
        else:
            for k in new.keys():
                if not default_compare(new.get(k), old.get(k, None), path + '/' + k, result):
                    match = False
    elif isinstance(new, list):
        if not isinstance(old, list) or len(new) != len(old):
            result[path] = 'length is different or null'
            match = False
        elif len(old) == 0:
            match = True
        else:
            match = True
            if isinstance(old[0], dict):
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
                    match = False
        return match
    else:
        if path.endswith('password'):
            match = True
        else:
            if path == '/location' or path.endswith('location_name'):
                new = new.replace(' ', '').lower()
                old = new.replace(' ', '').lower()
            if new == old:
                match = True
            else:
                result[path] = str(new) + ' != ' + str(old)
                match = False
    return match


def dict_camelize(d, path, camelize_first):
    if isinstance(d, list):
        for i in range(len(d)):
            dict_camelize(d[i], path, camelize_first)
    elif isinstance(d, dict):
        if len(path) == 1:
            old_value = d.get(path[0], None)
            if old_value is not None:
                d[path[0]] = _snake_to_camel(old_value, camelize_first)
        else:
            sd = d.get(path[0], None)
            if sd is not None:
                dict_camelize(sd, path[1:], camelize_first)


def dict_upper(d, path):
    if isinstance(d, list):
        for i in range(len(d)):
            dict_upper(d[i], path)
    elif isinstance(d, dict):
        if len(path) == 1:
            old_value = d.get(path[0], None)
            if old_value is not None:
                d[path[0]] = old_value.upper()
        else:
            sd = d.get(path[0], None)
            if sd is not None:
                dict_upper(sd, path[1:])


def dict_rename(d, path, new_name):
    if isinstance(d, list):
        for i in range(len(d)):
            dict_rename(d[i], path, new_name)
    elif isinstance(d, dict):
        if len(path) == 1:
            old_value = d.pop(path[0], None)
            if old_value is not None:
                d[new_name] = old_value
        else:
            sd = d.get(path[0], None)
            if sd is not None:
                dict_rename(sd, path[1:], new_name)


def dict_expand(d, path, outer_dict_name):
    if isinstance(d, list):
        for i in range(len(d)):
            dict_expand(d[i], path, outer_dict_name)
    elif isinstance(d, dict):
        if len(path) == 1:
            old_value = d.pop(path[0], None)
            if old_value is not None:
                d[outer_dict_name] = d.get(outer_dict_name, {})
                d[outer_dict_name][path[0]] = old_value
        else:
            sd = d.get(path[0], None)
            if sd is not None:
                dict_expand(sd, path[1:], outer_dict_name)


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
