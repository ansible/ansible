#!/usr/bin/python
#
# Copyright (c) 2017 Zim Kalinowski, <zikalino@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_appgwroutetable_facts
version_added: "2.5"
short_description: Get Route Table facts.
description:
    - Get facts of Route Table.

options:
    resource_group:
        description:
            - The name of the resource group.
        required: True
    route_table_name:
        description:
            - The name of the route table.
        required: True
    expand:
        description:
            - Expands referenced resources.

extends_documentation_fragment:
    - azure

author:
    - "Zim Kalinowski (@zikalino)"

'''

EXAMPLES = '''
  - name: Get instance of Route Table
    azure_rm_appgwroutetable_facts:
      resource_group: resource_group_name
      route_table_name: route_table_name
      expand: expand
'''

RETURN = '''
route_tables:
    description: A list of dict results where the key is the name of the Route Table and the values are the facts for that Route Table.
    returned: always
    type: complex
    contains:
        routetable_name:
            description: The key is the name of the server that the values relate to.
            type: complex
            contains:
                id:
                    description:
                        - Resource ID.
                    returned: always
                    type: str
                    sample: /subscriptions/subid/resourceGroups/rg1/providers/Microsoft.Network/routeTables/testrt
                name:
                    description:
                        - Resource name.
                    returned: always
                    type: str
                    sample: testrt
                type:
                    description:
                        - Resource type.
                    returned: always
                    type: str
                    sample: Microsoft.Network/routeTables
                location:
                    description:
                        - Resource location.
                    returned: always
                    type: str
                    sample: westus
                routes:
                    description:
                        - Collection of routes contained within a route table.
                    returned: always
                    type: complex
                    sample: routes
                    contains:
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from msrestazure.azure_operation import AzureOperationPoller
    from azure.mgmt.network import NetworkManagementClient
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMRouteTablesFacts(AzureRMModuleBase):
    def __init__(self):
        # define user inputs into argument
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                required=True
            ),
            route_table_name=dict(
                type='str',
                required=True
            ),
            expand=dict(
                type='str'
            )
        )
        # store the results of the module operation
        self.results = dict(
            changed=False,
            ansible_facts=dict()
        )
        self.mgmt_client = None
        self.resource_group = None
        self.route_table_name = None
        self.expand = None
        super(AzureRMRouteTablesFacts, self).__init__(self.module_arg_spec)

    def exec_module(self, **kwargs):
        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])
        self.mgmt_client = self.get_mgmt_svc_client(NetworkManagementClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        if (self.resource_group is not None and
                self.route_table_name is not None):
            self.results['route_tables'] = self.get()
        return self.results

    def get(self):
        '''
        Gets facts of the specified Route Table.

        :return: deserialized Route Tableinstance state dictionary
        '''
        response = None
        results = {}
        try:
            response = self.mgmt_client.route_tables.get(resource_group_name=self.resource_group,
                                                         route_table_name=self.route_table_name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for RouteTables.')

        if response is not None:
            results[response.name] = response.as_dict()

        return results


def main():
    AzureRMRouteTablesFacts()
if __name__ == '__main__':
    main()
