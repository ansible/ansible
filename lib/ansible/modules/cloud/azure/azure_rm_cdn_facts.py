#!/usr/bin/python
#
# Copyright (c) 2018 Hai Cao, <t-haicao@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: azure_rm_cdn_facts

version_added: "2.7"

short_description: Get CDN facts

description:
    - Get facts for a specific CDN or all CDNs.

options:
    name:
        description:
            - Limit results to a specific CDN.
    resource_group:
        description:
            - The resource group to search for the desired CDN
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.

extends_documentation_fragment:
    - azure

author:
    - "Hai Cao <t-haicao@microsoft.com>"
'''

EXAMPLES = '''
    - name: Get facts for one CDN
      azure_rm_trafficmanager_facts:
        name: Testing
        resource_group: TestRG

    - name: Get facts for all CDNs
      azure_rm_trafficmanager_facts:

    - name: Get facts by tags
      azure_rm_trafficmanager_facts:
        tags:
          - Environment:Test
'''

RETURN = '''
cdns:
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.common import AzureHttpError
except:
    # handled in azure_rm_common
    pass

import re

AZURE_OBJECT_CLASS = 'trafficManagerProfiles'


def serialize_endpoint(endpoint):
    return dict(
        id=endpoint.id,
        name=endpoint.name,
        type=endpoint.type,
        target_resource_id=endpoint.target_resource_id,
        target=endpoint.target,
        endpoint_status=endpoint.endpoint_status,
        weight=endpoint.weight,
        priority=endpoint.priority,
        endpoint_location=endpoint.endpoint_location,
        min_child_endpoints=endpoint.min_child_endpoints,
        geo_mapping=endpoint.geo_mapping,
    )


class AzureRMCdnFacts(AzureRMModuleBase):
    """Utility class to get Azure CDN facts"""

    def __init__(self):

        self.module_args = dict(
            name=dict(type='str'),
            resource_group=dict(type='str'),
            tags=dict(type='list')
        )

        self.results = dict(
            changed=False,
            cdns=[]
        )

        self.name = None
        self.resource_group = None
        self.tags = None

        super(AzureRMCdnFacts, self).__init__(
            derived_arg_spec=self.module_args,
            supports_tags=False,
            facts_module=True
        )

    def exec_module(self, **kwargs):

        for key in self.module_args:
            setattr(self, key, kwargs[key])

        if self.name and not self.resource_group:
            self.fail("Parameter error: resource group required when filtering by name.")

        if self.name:
            self.results['cdns'] = self.get_item()
        elif self.resource_group:
            self.results['cdns'] = self.list_resource_group()
        else:
            self.results['cdns'] = self.list_all()

        return self.results

    def get_item(self):
        """Get a single Azure CDN"""

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
        """Get all Azure CDNs within a resource group"""

        self.log('List all Azure CDNs within a resource group')

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
        """Get all Azure CDNs within a subscription"""
        self.log('List all CDNs within a subscription')
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
        Convert a CDN object to dict.
        :param tm: CDN object
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
        new_result['traffic_routing_method'] = tm.traffic_routing_method
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
            interval_in_seconds=tm.monitor_config.interval_in_seconds,
            timeout_in_seconds=tm.monitor_config.timeout_in_seconds,
            tolerated_number_of_failures=tm.monitor_config.tolerated_number_of_failures
        )
        new_result['endpoints'] = [serialize_endpoint(endpoint) for endpoint in tm.endpoints]
        new_result['tags'] = tm.tags
        return new_result


def main():
    """Main module execution code path"""

    AzureRMCdnFacts()


if __name__ == '__main__':
    main()