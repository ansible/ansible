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
module: azure_rm_hdinsightcluster_facts
version_added: "2.8"
short_description: Get Azure HDInsight Cluster facts.
description:
    - Get facts of Azure HDInsight Cluster.

options:
    resource_group:
        description:
            - Name of an Azure resource group.
    name:
        description:
            - HDInsight cluster name.
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.

extends_documentation_fragment:
    - azure

author:
    - "Zim Kalinowski (@zikalino)"

'''

EXAMPLES = '''
  - name: Get instance of HDInsight Cluster
    azure_rm_hdinsightcluster_facts:
      resource_group: myResourceGroup
      name: myCluster

  - name: List instances of HDInsight Cluster
    azure_rm_hdinsightcluster_facts:
      resource_group: myResourceGroup
'''

RETURN = '''
clusters:
    description: A list of dictionaries containing facts for HDInsight Cluster.
    returned: always
    type: complex
    contains:
        id:
            description:
                - The unique resource identifier of the HDInsight Cluster.
            returned: always
            type: str
            sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.HDInsight/clusters/myCluster"
        resource_group:
            description:
                - Name of an Azure resource group.
            returned: always
            type: str
            sample: myResourceGroup
        name:
            description:
                - The name of the HDInsight Cluster.
            returned: always
            type: str
            sample: testaccount
        location:
            description:
                - The location of the resource group to which the resource belongs.
            returned: always
            type: str
            sample: westus
        cluster_version:
            description:
                - The version of the cluster.
            returned: always
            type: str
            sample: 3.6.1000.67
        os_type:
            description:
                - The type of operating system.
            returned: always
            type: str
            sample: linux
        tier:
            description:
                - The cluster tier.
            returned: always
            type: str
            sample: standard
        cluster_definition:
            description:
                - The cluster definition.
            contains:
                kind:
                    description:
                        - The type of cluster.
                    returned: always
                    type: str
                    sample: spark
        compute_profile_roles:
            description:
                - The list of roles in the cluster.
            type: list
            suboptions:
                name:
                    description:
                        - The name of the role.
                    returned: always
                    type: str
                    sample: headnode
                target_instance_count:
                    description:
                        - The instance count of the cluster.
                    returned: always
                    type: int
                    sample: 2
                vm_size:
                    description:
                        - The size of the VM
                    returned: always
                    type: str
                    sample: Standard_D3
                linux_profile:
                    description:
                        - The Linux OS profile.
                    contains:
                        username:
                            description:
                                - User name
                            returned: always
                            type: str
                            sample: myuser
        connectivity_endpoints:
            description:
                - Cluster's connectivity endpoints.
            type: list
            contains:
                location:
                    description:
                        - Endpoint location.
                    returned: always
                    type: str
                    sample: myCluster-ssh.azurehdinsight.net
                name:
                    description:
                        - Endpoint name.
                    returned: always
                    type: str
                    sample: SSH
                port:
                    description:
                        - Endpoint port.
                    returned: always
                    type: int
                    sample: 22
                protocol:
                    description:
                        - Endpoint protocol.
                    returned: always
                    type: str
                    sample: TCP
        tags:
            description:
                - Tags
            returned: always
            type: complex
            sample: {}
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase
from ansible.module_utils.common.dict_transformations import _camel_to_snake

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.hdinsight import HDInsightManagementClient
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMHDInsightclusterFacts(AzureRMModuleBase):
    def __init__(self):
        # define user inputs into argument
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str'
            ),
            name=dict(
                type='str'
            ),
            tags=dict(
                type='list'
            )
        )
        # store the results of the module operation
        self.results = dict(
            changed=False
        )
        self.mgmt_client = None
        self.resource_group = None
        self.name = None
        self.tags = None

        super(AzureRMHDInsightclusterFacts, self).__init__(self.module_arg_spec, supports_tags=False)

    def exec_module(self, **kwargs):
        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])
        self.mgmt_client = self.get_mgmt_svc_client(HDInsightManagementClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        if self.name is not None:
            self.results['clusters'] = self.get()
        elif self.resource_group is not None:
            self.results['clusters'] = self.list_by_resource_group()
        else:
            self.results['clusters'] = self.list_all()
        return self.results

    def get(self):
        response = None
        results = []
        try:
            response = self.mgmt_client.clusters.get(resource_group_name=self.resource_group,
                                                     cluster_name=self.name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for HDInsight Cluster.')

        if response and self.has_tags(response.tags, self.tags):
            results.append(self.format_response(response))

        return results

    def list_by_resource_group(self):
        response = None
        results = []
        try:
            response = self.mgmt_client.clusters.list_by_resource_group(resource_group_name=self.resource_group)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for HDInsight Cluster.')

        if response is not None:
            for item in response:
                if self.has_tags(item.tags, self.tags):
                    results.append(self.format_response(item))

        return results

    def list_all(self):
        response = None
        results = []
        try:
            response = self.mgmt_client.clusters.list()
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for HDInsight Cluster.')

        if response is not None:
            for item in response:
                if self.has_tags(item.tags, self.tags):
                    results.append(self.format_response(item))

        return results

    def format_response(self, item):
        d = item.as_dict()
        d = {
            'id': d.get('id'),
            'resource_group': self.parse_resource_to_dict(d.get('id')).get('resource_group'),
            'name': d.get('name', None),
            'location': d.get('location', '').replace(' ', '').lower(),

            'cluster_version': d.get('properties', {}).get('cluster_version'),
            'os_type': d.get('properties', {}).get('os_type'),
            'tier': d.get('properties', {}).get('tier'),
            'cluster_definition': {
                'kind': d.get('properties', {}).get('cluster_definition', {}).get('kind')
            },
            'compute_profile_roles': [{
                'name': item.get('name'),
                'target_instance_count': item.get('target_instance_count'),
                'vm_size': item.get('hardware_profile', {}).get('vm_size'),
                'linux_profile': {
                    'username': item.get('os_profile', {}).get('linux_operating_system_profile', {}).get('username')
                }
            } for item in d.get('properties', []).get('compute_profile', {}).get('roles', [])],
            'connectivity_endpoints': d.get('properties', {}).get('connectivity_endpoints'),
            'tags': d.get('tags', None)
        }

        return d


def main():
    AzureRMHDInsightclusterFacts()


if __name__ == '__main__':
    main()
