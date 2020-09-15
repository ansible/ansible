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
module: azure_rm_trafficmanagerprofile_info

version_added: "2.9"

short_description: Get Azure Traffic Manager profile facts

description:
    - Get facts for a Azure specific Traffic Manager profile or all Traffic Manager profiles.

options:
    name:
        description:
            - Limit results to a specific Traffic Manager profile.
    resource_group:
        description:
            - The resource group to search for the desired Traffic Manager profile.
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.

extends_documentation_fragment:
    - azure

author:
    - Hai Cao (@caohai)
    - Yunge Zhu (@yungezz)
'''

EXAMPLES = '''
    - name: Get facts for one Traffic Manager profile
      azure_rm_trafficmanager_info:
        name: Testing
        resource_group: myResourceGroup

    - name: Get facts for all Traffic Manager profiles
      azure_rm_trafficmanager_info:

    - name: Get facts by tags
      azure_rm_trafficmanager_info:
        tags:
          - Environment:Test
'''

RETURN = '''
tms:
    description:
        - List of Traffic Manager profiles.
    returned: always
    type: complex
    contains:
        resource_group:
            description:
                - Name of a resource group where the Traffic Manager profile exists.
            returned: always
            type: str
            sample: testGroup
        name:
            description:
                - Name of the Traffic Manager profile.
            returned: always
            type: str
            sample: testTm
        state:
            description:
                - The state of the Traffic Manager profile.
            returned: always
            type: str
            sample: present
        location:
            description:
                - Location of the Traffic Manager profile.
            returned: always
            type: str
            sample: global
        profile_status:
            description:
                - The status of the Traffic Manager profile.
            returned: always
            type: str
            sample: Enabled
        routing_method:
            description:
                - The traffic routing method of the Traffic Manager profile.
            returned: always
            type: str
            sample: performance
        dns_config:
            description:
                - The DNS settings of the Traffic Manager profile.
            returned: always
            type: complex
            contains:
                relative_name:
                    description:
                        - The relative DNS name provided by the Traffic Manager profile.
                    returned: always
                    type: str
                    sample: testTm
                fqdn:
                    description:
                        - The fully-qualified domain name(FQDN) of the Traffic Manager profile.
                    returned: always
                    type: str
                    sample: testTm.trafficmanager.net
                ttl:
                    description:
                        - The DNS Time-To-Live(TTL), in seconds.
                    returned: always
                    type: int
                    sample: 60
        monitor_config:
            description:
                - The endpoint monitoring settings of the Traffic Manager profile.
            returned: always
            type: complex
            contains:
                protocol:
                    description:
                        - The protocol C(HTTP), C(HTTPS) or C(TCP) used to probe for endpoint health.
                    returned: always
                    type: str
                    sample: HTTP
                port:
                    description:
                        - The TCP port used to probe for endpoint health.
                    returned: always
                    type: int
                    sample: 80
                path:
                    description:
                        - The path relative to the endpoint domain name used to probe for endpoint health.
                    returned: always
                    type: str
                    sample: /
                interval:
                    description:
                        - The monitor interval for endpoints in this profile in seconds.
                    returned: always
                    type: int
                    sample: 10
                timeout:
                    description:
                        - The monitor timeout for endpoints in this profile in seconds.
                    returned: always
                    type: int
                    sample: 30
                tolerated_failures:
                    description:
                        - The number of consecutive failed health check before declaring an endpoint Degraded after the next failed health check.
                    returned: always
                    type: int
                    sample: 3
        endpoints:
            description:
                - The list of endpoints in the Traffic Manager profile.
            returned: always
            type: complex
            contains:
                id:
                    description:
                        - Fully qualified resource ID for the resource.
                    returned: always
                    type: str
                    sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Network/trafficMan
                             agerProfiles/tmtest/externalEndpoints/e1"
                name:
                    description:
                        - The name of the endpoint.
                    returned: always
                    type: str
                    sample: e1
                type:
                    description:
                        - The type of the endpoint.
                    returned: always
                    type: str
                    sample: external_endpoints
                target_resource_id:
                    description:
                        - The Azure Resource URI of the of the endpoint.
                    returned: always
                    type: str
                    sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.ClassicCompute/dom
                             ainNames/vscjavaci"
                target:
                    description:
                        - The fully-qualified DNS name of the endpoint.
                    returned: always
                    type: str
                    sample: 8.8.8.8
                status:
                    description:
                        - The status of the endpoint.
                    returned: always
                    type: str
                    sample: Enabled
                weight:
                    description:
                        - The weight of this endpoint when the profile has I(routing_method=weighted).
                    returned: always
                    type: int
                    sample: 10
                priority:
                    description:
                        - The priority of this endpoint when the profile has I(routing_method=priority).
                    returned: always
                    type: str
                    sample: 3
                location:
                    description:
                        - The location of endpoints when I(type=external_endpoints) or I(type=nested_endpoints), and profile I(routing_method=performance).
                    returned: always
                    type: str
                    sample: East US
                min_child_endpoints:
                    description:
                        - The minimum number of endpoints that must be available in the child profile to make the parent profile available.
                    returned: always
                    type: int
                    sample: 3
                geo_mapping:
                    description:
                        - The list of countries/regions mapped to this endpoint when the profile has routing_method C(geographic).
                    returned: always
                    type: list
                    sample: [
                        "GEO-NA",
                        "GEO-AS"
                    ]
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase
from ansible.module_utils.common.dict_transformations import _camel_to_snake

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.common import AzureHttpError
except Exception:
    # handled in azure_rm_common
    pass

import re

AZURE_OBJECT_CLASS = 'trafficManagerProfiles'


def serialize_endpoint(endpoint):
    result = dict(
        id=endpoint.id,
        name=endpoint.name,
        target_resource_id=endpoint.target_resource_id,
        target=endpoint.target,
        status=endpoint.endpoint_status,
        weight=endpoint.weight,
        priority=endpoint.priority,
        location=endpoint.endpoint_location,
        min_child_endpoints=endpoint.min_child_endpoints,
        geo_mapping=endpoint.geo_mapping,
    )

    if endpoint.type:
        result['type'] = _camel_to_snake(endpoint.type.split("/")[-1])

    return result


class AzureRMTrafficManagerProfileInfo(AzureRMModuleBase):
    """Utility class to get Azure Traffic Manager profile facts"""

    def __init__(self):

        self.module_args = dict(
            name=dict(type='str'),
            resource_group=dict(type='str'),
            tags=dict(type='list')
        )

        self.results = dict(
            changed=False,
            tms=[]
        )

        self.name = None
        self.resource_group = None
        self.tags = None

        super(AzureRMTrafficManagerProfileInfo, self).__init__(
            derived_arg_spec=self.module_args,
            supports_tags=False,
            facts_module=True
        )

    def exec_module(self, **kwargs):
        is_old_facts = self.module._name == 'azure_rm_trafficmanagerprofile_facts'
        if is_old_facts:
            self.module.deprecate("The 'azure_rm_trafficmanagerprofile_facts' module has been renamed to 'azure_rm_trafficmanagerprofile_info'", version='2.13')

        for key in self.module_args:
            setattr(self, key, kwargs[key])

        if self.name and not self.resource_group:
            self.fail("Parameter error: resource group required when filtering by name.")

        if self.name:
            self.results['tms'] = self.get_item()
        elif self.resource_group:
            self.results['tms'] = self.list_resource_group()
        else:
            self.results['tms'] = self.list_all()

        return self.results

    def get_item(self):
        """Get a single Azure Traffic Manager profile"""

        self.log('Get properties for {0}'.format(self.name))

        item = None
        result = []

        try:
            item = self.traffic_manager_management_client.profiles.get(
                self.resource_group, self.name)
        except CloudError:
            pass

        if item and self.has_tags(item.tags, self.tags):
            result = [self.serialize_tm(item)]

        return result

    def list_resource_group(self):
        """Get all Azure Traffic Managers profiles within a resource group"""

        self.log('List all Azure Traffic Managers within a resource group')

        try:
            response = self.traffic_manager_management_client.profiles.list_by_resource_group(
                self.resource_group)
        except AzureHttpError as exc:
            self.fail('Failed to list all items - {0}'.format(str(exc)))

        results = []
        for item in response:
            if self.has_tags(item.tags, self.tags):
                results.append(self.serialize_tm(item))

        return results

    def list_all(self):
        """Get all Azure Traffic Manager profiles within a subscription"""
        self.log('List all Traffic Manager profiles within a subscription')
        try:
            response = self.traffic_manager_management_client.profiles.list_by_subscription()
        except Exception as exc:
            self.fail("Error listing all items - {0}".format(str(exc)))

        results = []
        for item in response:
            if self.has_tags(item.tags, self.tags):
                results.append(self.serialize_tm(item))
        return results

    def serialize_tm(self, tm):
        '''
        Convert a Traffic Manager profile object to dict.
        :param tm: Traffic Manager profile object
        :return: dict
        '''
        result = self.serialize_obj(tm, AZURE_OBJECT_CLASS)

        new_result = {}
        new_result['id'] = tm.id
        new_result['resource_group'] = re.sub('\\/.*', '', re.sub('.*resourceGroups\\/', '', result['id']))
        new_result['name'] = tm.name
        new_result['state'] = 'present'
        new_result['location'] = tm.location
        new_result['profile_status'] = tm.profile_status
        new_result['routing_method'] = tm.traffic_routing_method.lower()
        new_result['dns_config'] = dict(
            relative_name=tm.dns_config.relative_name,
            fqdn=tm.dns_config.fqdn,
            ttl=tm.dns_config.ttl
        )
        new_result['monitor_config'] = dict(
            profile_monitor_status=tm.monitor_config.profile_monitor_status,
            protocol=tm.monitor_config.protocol,
            port=tm.monitor_config.port,
            path=tm.monitor_config.path,
            interval=tm.monitor_config.interval_in_seconds,
            timeout=tm.monitor_config.timeout_in_seconds,
            tolerated_failures=tm.monitor_config.tolerated_number_of_failures
        )
        new_result['endpoints'] = [serialize_endpoint(endpoint) for endpoint in tm.endpoints]
        new_result['tags'] = tm.tags
        return new_result


def main():
    """Main module execution code path"""

    AzureRMTrafficManagerProfileInfo()


if __name__ == '__main__':
    main()
