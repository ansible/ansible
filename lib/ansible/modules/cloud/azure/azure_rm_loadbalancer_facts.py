#!/usr/bin/python
#
# Copyright (c) 2016 Thomas Stringer, <tomstr@microsoft.com>
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
module: azure_rm_loadbalancer_facts

version_added: "2.4"

short_description: Get load balancer facts.

description:
    - Get facts for a specific load balancer or all load balancers.

options:
    name:
        description:
            - Limit results to a specific resource group.
        required: false
        default: null
    resource_group:
        description:
            - The resource group to search for the desired load balancer
        required: false
        default: null
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.
        required: false
        default: null

extends_documentation_fragment:
    - azure

author:
    - "Thomas Stringer (@tstringer)"
'''

EXAMPLES = '''
    - name: Get facts for one load balancer
      azure_rm_loadbalancer_facts:
        name: Testing
        resource_group: TestRG

    - name: Get facts for all load balancers
      azure_rm_loadbalancer_facts:

    - name: Get facts by tags
      azure_rm_loadbalancer_facts:
        tags:
          - testing
'''

RETURN = '''
azure_loadbalancers:
    description: List of load balancer dicts.
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

AZURE_OBJECT_CLASS = 'LoadBalancer'


class AzureRMLoadBalancerFacts(AzureRMModuleBase):
    """Utility class to get load balancer facts"""

    def __init__(self):

        self.module_args = dict(
            name=dict(type='str'),
            resource_group=dict(type='str'),
            tags=dict(type='list')
        )

        self.results = dict(
            changed=False,
            ansible_facts=dict(
                azure_loadbalancers=[]
            )
        )

        self.name = None
        self.resource_group = None
        self.tags = None

        super(AzureRMLoadBalancerFacts, self).__init__(
            derived_arg_spec=self.module_args,
            supports_tags=False,
            facts_module=True
        )

    def exec_module(self, **kwargs):

        for key in self.module_args:
            setattr(self, key, kwargs[key])

        if self.resource_group is not None and self.name is not None:
            self.results['loadbalancers'] = self.get()
        elif self.resource_group is not None:
            self.results['loadbalancers'] = self.list_by_resource_group()
        else:
            self.results['loadbalancers'] = self.list_all()

        # old way of listing load balancers
        self.results['ansible_facts']['azure_loadbalancers'] = [k for k in self.results['loadbalancers']]

        return self.results

    def get(self):
        '''
        Gets facts of the specified Load Balancer.

        :return: deserialized Load Balancerinstance state dictionary
        '''
        response = None
        results = {}
        try:
            response = self.network_client.load_balancers.get(resource_group_name=self.resource_group,
                                                              load_balancer_name=self.name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for LoadBalancers.')

        if response is not None:
            results[response.name] = response.as_dict()

        return results

    def list_by_resource_group(self):
        '''
        Get all Load Balancers in a specified resource group.

        :return: deserialized Load Balancer instance state dictionary
        '''
        response = None
        results = {}
        try:
            response = self.network_client.load_balancers.list(resource_group_name=self.resource_group)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for Load Balancers.')

        if response is not None:
            for item in response:
                results[item.name] = item.as_dict()

        return results

    def list_all(self):
        '''
        Get all Load Balancers in a specified resource group.

        :return: deserialized Load Balancer instance state dictionary
        '''
        response = None
        results = {}
        try:
            response = self.network_client.load_balancers.list_all()
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for Load Balancers.')

        if response is not None:
            for item in response:
                results[item.name] = item.as_dict()

        return results


def main():
    """Main module execution code path"""

    AzureRMLoadBalancerFacts()

if __name__ == '__main__':
    main()
