#!/usr/bin/python
#
# Copyright (c) 2018 Hai Cao, <t-haicao@microsoft.com>, Yunge Zhu <yungez@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: azure_rm_trafficmanagerendpoint_facts

version_added: "2.7"

short_description: Get Azure Traffic Manager endpoint facts

description:
    - Get facts for a specific Traffic Manager endpoints or all endpoints  in a Traffic Manager profile

options:
    name:
        description:
            - Limit results to a specific Traffic Manager endpoint.
    resource_group:
        description:
            - The resource group to search for the desired Traffic Manager profile
        required: True
    profile_name:
        description:
            - Name of Traffic Manager Profile
        required: True
    type:
        description:
            - Type of endpoint.
        choices:
            - azure_endpoints
            - external_endpoints
            - nested_endpoints

extends_documentation_fragment:
    - azure

author:
    - "Hai Cao (@caohai) <t-haicao@microsoft.com>"
    - "Yunge Zhu (@yungezz) <yungez@microsoft.com>"
'''

EXAMPLES = '''
    - name: Get endpoints facts of a Traffic Manager profile
      azure_rm_trafficmanagerendpoint_facts:
        resource_group: myResourceGroup
        profile_name: Testing

    - name: Get specific endpoint of a Traffic Manager profile
      azure_rm_trafficmanager_facts:
        resource_group: myResourceGroup
        profile_name: Testing
        name: test_external_endpoint

'''

RETURN = '''
endpoints:
    description: List of Traffic Manager endpoints.
    returned: always
    type: complex
    contains:
        resource_group:
            description:
                - Name of a resource group.
            returned: always
            type: str
            sample: myResourceGroup
        name:
            description:
                - Name of the Traffic Manager endpoint.
            returned: always
            type: str
            sample: testendpoint
        type:
            description:
                - The type of the endpoint.
            type: str
            sample: external_endpoints
        target_resource_id:
            description:
                - The Azure Resource URI of the of the endpoint.
            type: str
            sample: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.ClassicCompute/domainNames/vscjavaci
        target:
            description:
                - The fully-qualified DNS name of the endpoint.
            type: str
            sample: 8.8.8.8
        enabled:
            description:
                - The status of the endpoint.
            type: str
            sample: Enabled
        weight:
            description:
                - The weight of this endpoint when using the 'Weighted' traffic routing method.
            type: int
            sample: 10
        priority:
            description:
                - The priority of this endpoint when using the 'Priority' traffic routing method.
            type: str
            sample: 3
        location:
            description:
                - The location of the external or nested endpoints when using the 'Performance' traffic routing method.
            type: str
            sample: East US
        min_child_endpoints:
            description:
                - The minimum number of endpoints that must be available in the child profile to make the parent profile available.
            type: int
            sample: 3
        geo_mapping:
            description:
                - The list of countries/regions mapped to this endpoint when using the 'Geographic' traffic routing method.
            type: list
            sample: [
                "GEO-NA",
                "GEO-AS"
                ]
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase
from ansible.module_utils.common.dict_transformations import (
    _snake_to_camel, _camel_to_snake
)

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.common import AzureHttpError
except Exception:
    # handled in azure_rm_common
    pass

import re

AZURE_OBJECT_CLASS = 'TrafficManagerEndpoints'


def serialize_endpoint(endpoint, resource_group):
    result = dict(
        id=endpoint.id,
        name=endpoint.name,
        target_resource_id=endpoint.target_resource_id,
        target=endpoint.target,
        enabled=True,
        weight=endpoint.weight,
        priority=endpoint.priority,
        location=endpoint.endpoint_location,
        min_child_endpoints=endpoint.min_child_endpoints,
        geo_mapping=endpoint.geo_mapping,
        monitor_status=endpoint.endpoint_monitor_status,
        resource_group=resource_group
    )

    if endpoint.endpoint_status and endpoint.endpoint_status == 'Disabled':
        result['enabled'] = False

    if endpoint.type:
        result['type'] = _camel_to_snake(endpoint.type.split("/")[-1])

    return result


class AzureRMTrafficManagerEndpointFacts(AzureRMModuleBase):
    """Utility class to get Azure Traffic Manager Endpoint facts"""

    def __init__(self):

        self.module_args = dict(
            profile_name=dict(
                type='str',
                required=True),
            resource_group=dict(
                type='str',
                required=True),
            name=dict(type='str'),
            type=dict(
                type='str',
                choices=[
                    'azure_endpoints',
                    'external_endpoints',
                    'nested_endpoints'
                ])
        )

        self.results = dict(
            changed=False,
            endpoints=[]
        )

        self.profile_name = None
        self.name = None
        self.resource_group = None
        self.type = None

        super(AzureRMTrafficManagerEndpointFacts, self).__init__(
            derived_arg_spec=self.module_args,
            supports_tags=False,
            facts_module=True
        )

    def exec_module(self, **kwargs):

        for key in self.module_args:
            setattr(self, key, kwargs[key])

        if self.type:
            self.type = _snake_to_camel(self.type)

        if self.name and not self.resource_group:
            self.fail("Parameter error: resource group required when filtering by name.")

        if self.name:
            self.results['endpoints'] = self.get_item()
        elif self.type:
            self.results['endpoints'] = self.list_by_type()
        else:
            self.results['endpoints'] = self.list_by_profile()

        return self.results

    def get_item(self):
        """Get a single Azure Traffic Manager endpoint"""

        self.log('Get properties for {0}'.format(self.name))

        item = None
        result = []

        try:
            item = self.traffic_manager_management_client.endpoints.get(
                self.resource_group, self.profile_name, self.type, self.name)
        except CloudError:
            pass

        if item:
            if (self.type and self.type == item.type) or self.type is None:
                result = [self.serialize_tm(item)]

        return result

    def list_by_profile(self):
        """Get all Azure Traffic Manager endpoints of a profile"""

        self.log('List all endpoints belongs to a Traffic Manager profile')

        try:
            response = self.traffic_manager_management_client.profiles.get(self.resource_group, self.profile_name)
        except AzureHttpError as exc:
            self.fail('Failed to list all items - {0}'.format(str(exc)))

        results = []
        if response and response.endpoints:
            for endpoint in response.endpoints:
                results.append(serialize_endpoint(endpoint, self.resource_group))

        return results

    def list_by_type(self):
        """Get all Azure Traffic Managers endpoints of a profile by type"""
        self.log('List all Traffic Manager endpoints of a profile by type')
        try:
            response = self.traffic_manager_management_client.profiles.get(self.resource_group, self.profile_name)
        except AzureHttpError as exc:
            self.fail('Failed to list all items - {0}'.format(str(exc)))

        results = []
        for item in response:
            if item.endpoints:
                for endpoint in item.endpoints:
                    if endpoint.type == self.type:
                        results.append(serialize_endpoint(endpoint, self.resource_group))
        return results


def main():
    """Main module execution code path"""

    AzureRMTrafficManagerEndpointFacts()


if __name__ == '__main__':
    main()
