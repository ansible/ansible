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

short_description: Get Azure Cache for Redis instance facts

description:
    - Get facts for Azure Cache for Redis instance.

options:
    resource_group:
        description:
            - The resource group to search for the desired Azure Cache for Redis
        required: True
    name:
        description:
            - Limit results to a specific Azure Cache for Redis.
    return_access_keys:
        description:
            - Indicate weather to return access keys of the Azure Cache for Redis.
        default: False
        type: bool
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.

extends_documentation_fragment:
    - azure

author:
    - "Yunge Zhu (@yungezz)"
'''

EXAMPLES = '''
    - name: Get Azure Cache for Redis by name
      azure_rm_rediscache_facts:
        resource_group: myResourceGroup
        name: myRedis

    - name: Get Azure Cache for Redis with access keys by name
      azure_rm_rediscache_facts:
        resource_group: myResourceGroup
        name: myRedis
        return_access_keys: true

    - name: Get Azure Cache for Redis in specific resource group
      azure_rm_rediscache_facts:
        resource_group: myResourceGroup
'''

RETURN = '''
rediscaches:
    description: List of Azure Cache for Redis instances.
    returned: always
    type: complex
    contains:
        resource_group:
            description:
                - Name of a resource group where the Azure Cache for Redis belongs to.
            returned: always
            type: str
            sample: myResourceGroup
        name:
            description:
                - Name of the Azure Cache for Redis.
            returned: always
            type: str
            sample: myRedis
        id:
            description:
                - Id of the Azure Cache for Redis.
            returned: always
            type: str
            sample: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Cache/Redis/myRedis
        provisioning_state:
            description:
                - Provisioning state of the redis cahe
            returned: always
            type: str
            sample: Creating
        location:
            description:
                - Location of the Azure Cache for Redis.
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
                    description: Size of the Azure Cache for Redis.
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
                - The full resource ID of a subnet in a virtual network to deploy the Azure Cache for Redis in.
            type: str
            sample:
                - "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/Microsoft.Network/VirtualNetworks/myVirtualNetwo
                   rk/subnets/mySubnet"
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
                - Azure Cache for Redis access keys.
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
except ImportError:
    # handled in azure_rm_common
    pass

import re


class AzureRMRedisCacheFacts(AzureRMModuleBase):
    """Utility class to get Azure Cache for Redis facts"""

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
        """Get a single Azure Cache for Redis"""

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
        """Get all Azure Cache for Redis within a resource group"""

        self.log('List all Azure Cache for Redis within a resource group')

        try:
            response = self._client.redis.list_by_resource_group(self.resource_group)
        except CloudError as exc:
            self.fail('Failed to list all items - {0}'.format(str(exc)))

        results = []
        for item in response:
            if self.has_tags(item.tags, self.tags):
                results.append(self.serialize_rediscache(item))

        return results

    def list_keys(self):
        """List Azure Cache for Redis keys"""

        self.log('List keys for {0}'.format(self.name))

        item = None

        try:
            item = self._client.redis.list_keys(resource_group_name=self.resource_group, name=self.name)
        except CloudError as exc:
            self.fail("Failed to list redis keys of {0} - {1}".format(self.name, str(exc)))

        return item

    def serialize_rediscache(self, rediscache):
        '''
        Convert an Azure Cache for Redis object to dict.
        :param rediscache: Azure Cache for Redis object
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
                name=rediscache.sku.name.lower(),
                size=rediscache.sku.family + str(rediscache.sku.capacity)
            )
        if self.return_access_keys:
            access_keys = self.list_keys()
            if access_keys:
                new_result['access_keys'] = dict(
                    primary=access_keys.primary_key,
                    secondary=access_keys.secondary_key
                )
        return new_result


def main():
    """Main module execution code path"""

    AzureRMRedisCacheFacts()


if __name__ == '__main__':
    main()
