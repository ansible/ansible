#!/usr/bin/python
#
# Copyright (c) 2018 Yunge Zhu <yungez@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: azure_rm_rediscache_facts

version_added: "2.8"

short_description: Get Azure Redis Cache instance facts

description:
    - Get facts for Azure Redis Cache instance.

options:
    resource_group:
        description:
            - The resource group to search for the desired Azure redis cache
        required: True
    name:
        description:
            - Limit results to a specific Azure redis cache.
    return_access_keys:
        description:
            - Indicate wheather to return access keys of the redis cache.
        default: False
        type: bool
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.

extends_documentation_fragment:
    - azure

author:
    - "Yunge Zhu <yungez@microsoft.com>"
'''

EXAMPLES = '''
    rediscaches:
    - configuration:
        maxclients: '1000'
        maxfragmentationmemory-reserved: '50'
        maxmemory-delta: '50'
        maxmemory-reserved: '50'
      enable_non_ssl_port: false
      host_name: testredis1.redis.cache.windows.net
      id: /subscriptions/<subs_id>/resourceGroups/rerdistest1/providers/Microsoft.Cache/Redis/testredis1
      location: East US
      name: testredis1
      provisioning_state: Creating
      resource_group: testrg1
      shard_count: null
      sku:
        name: Basic
        size: C1
      static_ip: 1.2.3.4
      subnet: null
      tags: {}
      tenant_settings: null
'''

RETURN = '''
rediscaches:
    description: List of Azure redis cache instances.
    returned: always
    type: complex
    contains:
        resource_group:
            description:
                - Name of a resource group where the Azure redis cache belongs to.
            returned: always
            type: str
            sample: testGroup
        name:
            description:
                - Name of the Azure redis cache.
            returned: always
            type: str
            sample: testRedis
        id:
            description:
                - Id of the Azure redis cache.
            returned: always
            type: str
            sample: /subscriptions/<subs_id>/resourceGroups/<resourcegroup>/providers/Microsoft.Cache/Redis/testredis1
        provisioning_state:
            description:
                - Provisioning state of the redis cahe
            returned: always
            type: str
            sample: Creating
        location:
            description:
                - Location of the Azure redis cache.
            type: str
            sample: WestUS
        enable_non_ssl_port:
            description:
                - Specifies whether the non-ssl Redis server port (6379) is enabled.
            type: bool
            sample: false
        sku:
            description:
                - Dict of sku information.
            type: dict
            contains:
                name:
                    description: Name of the sku.
                    returned: always
                    type: str
                    sample: standard
                size:
                    description: Size of the redis cache.
                    returned: always
                    type: str
                    sample: C1
        static_ip:
            description:
                - Static IP address.
            type: str
            sample: 10.75.0.11
        subnet:
            description:
                - The full resource ID of a subnet in a virtual network to deploy the Redis cache in.
            type: str
            sample:
                - /subscriptions/<subid>/resourceGroups/<resourceGroupName>/Microsoft.Network|ClassicNetwork/VirtualNetworks/vnet1/subnets/subnet1
        configuration:
            description:
                - Dict of redis configuration.
            type: dict
            sample: maxmeory_reserved
        host_name:
            description:
                - Redis host name.
            type: str
            sample: testRedis.redis.cache.windows.net
        shard_count:
            description:
                - The number of shards on a Premium Cluster Cache.
            type: int
            sample: 1
        tenant_settings:
            description:
                - Dict of tenant settings.
            type: dict
        tags:
            description:
                - List of tags.
            type: list
            sample:
                - foo
        access_keys:
            description:
                - Redis cache access keys.
            type: dict
            returned: when C(return_access_keys) is true.
            contains:
                primary:
                    description: The current primary key that clients can use to authenticate the redis cahce.
                    type: str
                    sample: X2xXXxx7xxxxxx5xxxx0xxxxx75xxxxxxxxXXXxxxxx=
                secondary:
                    description: The current secondary key that clients can use to authenticate the redis cahce.
                    type: str
                    sample: X2xXXxx7xxxxxx5xxxx0xxxxx75xxxxxxxxXXXxxxxx=
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from azure.common import AzureHttpError
    from azure.mgmt.redis import RedisManagementClient
    from msrestazure.azure_exceptions import CloudError
except:
    # handled in azure_rm_common
    pass

import re


class AzureRMRedisCacheFacts(AzureRMModuleBase):
    """Utility class to get Azure Azure Redis cache facts"""

    def __init__(self):

        self.module_args = dict(
            name=dict(type='str'),
            resource_group=dict(
                type='str',
                required=True
            ),
            return_access_keys=dict(
                type='bool',
                default=False
            ),
            tags=dict(type='list')
        )

        self.results = dict(
            changed=False,
            rediscaches=[]
        )

        self.name = None
        self.resource_group = None
        self.profile_name = None
        self.tags = None

        self._client = None

        super(AzureRMRedisCacheFacts, self).__init__(
            derived_arg_spec=self.module_args,
            supports_tags=False,
            facts_module=True
        )

    def exec_module(self, **kwargs):

        for key in self.module_args:
            setattr(self, key, kwargs[key])

        # get management client
        self._client = self.get_mgmt_svc_client(RedisManagementClient,
                                                base_url=self._cloud_environment.endpoints.resource_manager,
                                                api_version='2018-03-01')

        if self.name:
            self.results['rediscaches'] = self.get_item()
        else:
            self.results['rediscaches'] = self.list_by_resourcegroup()

        return self.results

    def get_item(self):
        """Get a single Azure redis cache"""

        self.log('Get properties for {0}'.format(self.name))

        item = None
        result = []

        try:
            item = self._client.redis.get(resource_group_name=self.resource_group, name=self.name)
        except CloudError:
            pass

        if item and self.has_tags(item.tags, self.tags):
            result = [self.serialize_rediscache(item)]

        return result

    def list_by_resourcegroup(self):
        """Get all Azure Azure redis cache within a resource group"""

        self.log('List all Azure redis cache within a resource group')

        try:
            response = self._client.redis.list_by_resource_group(self.resource_group)
        except CloudError as exc:
            self.fail('Failed to list all items - {0}'.format(str(exc)))

        results = []
        for item in response:
            if self.has_tags(item.tags, self.tags):
                results.append(self.serialize_rediscache(item))

        return results

    def serialize_rediscache(self, rediscache):
        '''
        Convert a Azure redis cache object to dict.
        :param cdn: Azure redis cache object
        :return: dict
        '''
        new_result = dict(
            id=rediscache.id,
            resource_group=re.sub('\\/.*', '', re.sub('.*resourceGroups\\/', '', rediscache.id)),
            name=rediscache.name,
            location=rediscache.location,
            provisioning_state=rediscache.provisioning_state,
            configuration=rediscache.redis_configuration,
            tenant_settings=rediscache.tenant_settings,
            shard_count=rediscache.shard_count,
            enable_non_ssl_port=rediscache.enable_non_ssl_port,
            static_ip=rediscache.static_ip,
            subnet=rediscache.subnet_id,
            host_name=rediscache.host_name,
            tags=rediscache.tags
        )

        if rediscache.sku:
            new_result['sku'] = dict(
                name=rediscache.sku.name,
                size=rediscache.sku.family.lower() + str(rediscache.sku.capacity)
            )
        if self.return_access_keys:
            new_result['access_keys'] = dict(
                primary=rediscache.access_keys.primary_key,
                secondary=rediscache.access_keys.secondary_key
            )
        return new_result


def main():
    """Main module execution code path"""

    AzureRMRedisCacheFacts()


if __name__ == '__main__':
    main()
