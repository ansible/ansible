#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2016, Thomas Stringer <tomstr@microsoft.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: azure_rm_loadbalancer_info

version_added: "2.9"

short_description: Get load balancer facts

description:
    - Get facts for a specific load balancer or all load balancers.

options:
    name:
        description:
            - Limit results to a specific resource group.
    resource_group:
        description:
            - The resource group to search for the desired load balancer.
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.

extends_documentation_fragment:
    - azure

author:
    - Thomas Stringer (@trstringer)
'''

EXAMPLES = '''
    - name: Get facts for one load balancer
      azure_rm_loadbalancer_info:
        name: Testing
        resource_group: myResourceGroup

    - name: Get facts for all load balancers
      azure_rm_loadbalancer_info:

    - name: Get facts for all load balancers in a specific resource group
      azure_rm_loadbalancer_info:
        resource_group: myResourceGroup

    - name: Get facts by tags
      azure_rm_loadbalancer_info:
        tags:
          - testing
'''

RETURN = '''
azure_loadbalancers:
    description:
        - List of load balancer dicts.
    returned: always
    type: list
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.common import AzureHttpError
except Exception:
    # handled in azure_rm_common
    pass

AZURE_OBJECT_CLASS = 'LoadBalancer'


class AzureRMLoadBalancerInfo(AzureRMModuleBase):
    """Utility class to get load balancer facts"""

    def __init__(self):

        self.module_args = dict(
            name=dict(type='str'),
            resource_group=dict(type='str'),
            tags=dict(type='list')
        )

        self.results = dict(
            changed=False,
            ansible_info=dict(
                azure_loadbalancers=[]
            )
        )

        self.name = None
        self.resource_group = None
        self.tags = None

        super(AzureRMLoadBalancerInfo, self).__init__(
            derived_arg_spec=self.module_args,
            supports_tags=False,
            facts_module=True
        )

    def exec_module(self, **kwargs):

        is_old_facts = self.module._name == 'azure_rm_loadbalancer_facts'
        if is_old_facts:
            self.module.deprecate("The 'azure_rm_loadbalancer_facts' module has been renamed to 'azure_rm_loadbalancer_info'", version='2.13')

        for key in self.module_args:
            setattr(self, key, kwargs[key])

        self.results['ansible_info']['azure_loadbalancers'] = (
            self.get_item() if self.name
            else self.list_items()
        )

        return self.results

    def get_item(self):
        """Get a single load balancer"""

        self.log('Get properties for {0}'.format(self.name))

        item = None
        result = []

        try:
            item = self.network_client.load_balancers.get(self.resource_group, self.name)
        except CloudError:
            pass

        if item and self.has_tags(item.tags, self.tags):
            result = [self.serialize_obj(item, AZURE_OBJECT_CLASS)]

        return result

    def list_items(self):
        """Get all load balancers"""

        self.log('List all load balancers')

        if self.resource_group:
            try:
                response = self.network_client.load_balancers.list(self.resource_group)
            except AzureHttpError as exc:
                self.fail('Failed to list items in resource group {0} - {1}'.format(self.resource_group, str(exc)))
        else:
            try:
                response = self.network_client.load_balancers.list_all()
            except AzureHttpError as exc:
                self.fail('Failed to list all items - {0}'.format(str(exc)))

        results = []
        for item in response:
            if self.has_tags(item.tags, self.tags):
                results.append(self.serialize_obj(item, AZURE_OBJECT_CLASS))

        return results


def main():
    """Main module execution code path"""

    AzureRMLoadBalancerInfo()


if __name__ == '__main__':
    main()
