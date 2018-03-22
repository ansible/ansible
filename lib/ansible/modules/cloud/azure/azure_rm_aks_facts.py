#!/usr/bin/python
#
# Copyright (c) 2018 Yuwei Zhou, <yuwzho@microsoft.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: azure_rm_aks_facts

version_added: "2.6"

short_description: Get Azure Kubernetes Service facts.

description:
    - Get facts for a specific Azure Kubernetes Service or all Azure Kubernetes Services.

options:
    name:
        description:
            - Limit results to a specific resource group.
    resource_group:
        description:
            - The resource group to search for the desired Azure Kubernetes Service
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.

extends_documentation_fragment:
    - azure

author:
    - "Yuwei Zhou (@yuwzho)"
'''

EXAMPLES = '''
    - name: Get facts for one Azure Kubernetes Service
      azure_rm_aks_facts:
        name: Testing
        resource_group: TestRG

    - name: Get facts for all Azure Kubernetes Services
      azure_rm_aks_facts:

    - name: Get facts by tags
      azure_rm_aks_facts:
        tags:
          - testing
'''

RETURN = '''
azure_aks:
    description: List of Azure Kubernetes Service dicts.
    returned: always
    type: list
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.common import AzureHttpError
except:
    # handled in azure_rm_common
    pass

AZURE_OBJECT_CLASS = 'managedClusters'


class AzureRMManagedClusterFacts(AzureRMModuleBase):
    """Utility class to get Azure Kubernetes Service facts"""

    def __init__(self):

        self.module_args = dict(
            name=dict(type='str'),
            resource_group=dict(type='str'),
            tags=dict(type='list')
        )

        self.results = dict(
            changed=False,
            ansible_facts=dict(
                aks=[]
            )
        )

        self.name = None
        self.resource_group = None
        self.tags = None

        super(AzureRMManagedClusterFacts, self).__init__(
            derived_arg_spec=self.module_args,
            supports_tags=False,
            facts_module=True
        )

    def exec_module(self, **kwargs):

        for key in self.module_args:
            setattr(self, key, kwargs[key])

        self.results['ansible_facts']['aks'] = (
            self.get_item() if self.name
            else self.list_items()
        )

        return self.results

    def get_item(self):
        """Get a single Azure Kubernetes Service"""

        self.log('Get properties for {0}'.format(self.name))

        item = None
        result = []

        try:
            item = self.containerservice_client.managed_clusters.get(self.resource_group, self.name)
        except CloudError:
            pass

        if item and self.has_tags(item.tags, self.tags):
            result = [self.serialize_obj(item, AZURE_OBJECT_CLASS)]

        return result

    def list_items(self):
        """Get all Azure Kubernetes Services"""

        self.log('List all Azure Kubernetes Services')

        try:
            response = self.containerservice_client.managed_clusters.list()
        except AzureHttpError as exc:
            self.fail('Failed to list all items - {0}'.format(str(exc)))

        results = []
        for item in response:
            if self.has_tags(item.tags, self.tags):
                results.append(self.serialize_obj(item, AZURE_OBJECT_CLASS))

        return results


def main():
    """Main module execution code path"""

    AzureRMManagedClusterFacts()

if __name__ == '__main__':
    main()
