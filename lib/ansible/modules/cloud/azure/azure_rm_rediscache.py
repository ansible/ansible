#!/usr/bin/python
#
# Copyright (c) 2018 Yunge Zhu, <yungez@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_rediscache
version_added: "2.8"
short_description: Manage Azure Redis Cache instance.
description:
    - Create, update and delete instance of Azure Redis Cache.

options:
    resource_group:
        description:
            - Name of the resource group to which the resource belongs.
        required: True
    name:
        description:
            - Unique name of the redis cache to create or update. To create or update a deployment slot, use the {slot} parameter.
        required: True

    location:
        description:
            - Resource location. If not set, location from the resource group will be used as default.
    sku:
        description: Sku info of redis cache.
        suboptions:
            name:
                description: Type of redis cache to deploy
                choices:
                    - basic
                    - standard
                    - premium
                required: True
            size:
                description:
                    - Size of redis cache to deploy.
                    - When I(sku) is C(basic) or C(standard), allowed values are C0, C1, C2, C3, C4, C5, C6.
                    - When I(sku) is C(premium), allowed values are P1, P2, P3, P4.
                    - Please see U(https://docs.microsoft.com/en-us/rest/api/redis/redis/create#sku) for allowed values.
                choices:
                    - C0
                    - C1
                    - C2
                    - C3
                    - C4
                    - C5
                    - C6
                    - P1
                    - P2
                    - P3
                    - P4
                required: True
    enable_non_ssl_port:
        description:
            - When true, the non-ssl redis server port 6379 will be enabled.
        type: bool
        default: false
    maxfragmentationmemory_reserved:
        description:
            - Configures the amount of memory in MB that is reserved to accommodate for memory fragmentation.
            - Please see U(https://docs.microsoft.com/en-us/azure/redis-cache/cache-configure#advanced-settings) for more detail.
    maxmemory_reserved:
        description:
            - Configures the amount of memory in MB that is reserved for non-cache operations.
            - Please see U(https://docs.microsoft.com/en-us/azure/redis-cache/cache-configure#advanced-settings) for more detail.
    maxmemory_policy:
        description:
            - Configures the eviction policy of the cache.
            - Please see U(https://docs.microsoft.com/en-us/azure/redis-cache/cache-configure#advanced-settings) for more detail.
        choices:
            - volatile_lru
            - allkeys_lru
            - volatile_random
            - allkeys_random
            - volatile_ttl
            - noeviction
    notify_keyspace_events:
        description:
            - Allows clients to receive notifications when certain events occur.
            - Please see U(https://docs.microsoft.com/en-us/azure/redis-cache/cache-configure#advanced-settings) for more detail.
    shard_count:
        description:
            - The number of shards to be created when I(sku) is C(premium).
        type: int
    static_ip:
        description:
            - Static IP address. Required when deploying a redis cache inside an existing Azure virtual network.
    subnet:
        description:
            - Subnet in a virtual network to deploy the redis cache in.
            - "It can be resource id of subnet, eg.
              /subscriptions/{subid}/resourceGroups/{resourceGroupName}/Microsoft.{Network|ClassicNetwork}/VirtualNetworks/vnet1/subnets/subnet1"
            - It can be a dictionary where contains C(name), C(virtual_network_name) and C(resource_group).
            - C(name). Name of the subnet.
            - C(resource_group). Resource group name of the subnet.
            - C(virtual_network_name). Name of virtual network to which this subnet belongs.
    tenant_settings:
        description:
            - Dict of tenant settings.
    state:
      description:
        - Assert the state of the redis cache.
        - Use C(present) to create or update a redis cache and C(absent) to delete it.
      default: present
      choices:
        - absent
        - present

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Yunge Zhu(@yungezz)"

'''

EXAMPLES = '''
  - name: Create a redis cache
    azure_rm_rediscache:
        resource_group: myResourceGroup
        name: myRedisCache
        sku:
          name: basic
          size: C1


  - name: Scale up the redis cache
    azure_rm_rediscache:
        resource_group: myResourceGroup
        name: myRedisCache
        sku:
          name: standard
          size: C1
        tags:
          testing: foo

  - name: Create redis with subnet
    azure_rm_rediscache:
        resource_group: myResourceGroup
        name: myRedisCache2
        sku:
          name: premium
          size: P1
        subnet: /subscriptions/<subs_id>/resourceGroups/redistest1/providers/Microsoft.Network/virtualNetworks/testredisvnet1/subnets/subnet1

'''

RETURN = '''
id:
    description: Id of the redis cache.
    returned: always
    type: str
    sample: {
        "id": "/subscriptions/<subs_id>/resourceGroups/rg/providers/Microsoft.Cache/Redis/redis1"
    }
host_name:
    description: Host name of the redis cache.
    returned: state is present
    type: str
    sample: {
        "host_name": "redis1.redis.cache.windows.net"
    }
'''

import time
from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from msrestazure.azure_operation import AzureOperationPoller
    from msrest.serialization import Model
    from azure.mgmt.redis import RedisManagementClient
    from azure.mgmt.redis.models import (RedisCreateParameters, RedisUpdateParameters, Sku)
except ImportError:
    # This is handled in azure_rm_common
    pass


sku_spec = dict(
    name=dict(
        type='str',
        choices=['basic', 'standard', 'premium']),
    size=dict(
        type='str',
        choices=['C0', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'P1', 'P2', 'P3', 'P4']
    )
)


def rediscache_to_dict(redis):
    result = dict(
        id=redis.id,
        name=redis.name,
        location=redis.location,
        sku=dict(
            name=redis.sku.name.lower(),
            size=redis.sku.family + str(redis.sku.capacity)
        ),
        enable_non_ssl_port=redis.enable_non_ssl_port,
        host_name=redis.host_name,
        shard_count=redis.shard_count,
        subnet=redis.subnet_id,
        static_ip=redis.static_ip,
        provisioning_state=redis.provisioning_state,
        tenant_settings=redis.tenant_settings,
        tags=redis.tags if redis.tags else None
    )
    for key in redis.redis_configuration:
        result[hyphen_to_underline(key)] = hyphen_to_underline(redis.redis_configuration.get(key, None))
    return result


def hyphen_to_underline(input):
    if input and isinstance(input, str):
        return input.replace("-", "_")
    return input


def underline_to_hyphen(input):
    if input and isinstance(input, str):
        return input.replace("_", "-")
    return input


class Actions:
    NoAction, Create, Update, Delete = range(4)


class AzureRMRedisCaches(AzureRMModuleBase):
    """Configuration class for an Azure RM Redis Cache resource"""

    def __init__(self):
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                required=True
            ),
            name=dict(
                type='str',
                required=True
            ),
            location=dict(
                type='str'
            ),
            sku=dict(
                type='dict',
                options=sku_spec
            ),
            enable_non_ssl_port=dict(
                type='bool',
                default=False
            ),
            maxfragmentationmemory_reserved=dict(
                type='int'
            ),
            maxmemory_reserved=dict(
                type='int'
            ),
            maxmemory_policy=dict(
                type='str',
                choices=[
                    "volatile_lru",
                    "allkeys_lru",
                    "volatile_random",
                    "allkeys_random",
                    "volatile_ttl",
                    "noeviction"
                ]
            ),
            notify_keyspace_events=dict(
                type='int'
            ),
            shard_count=dict(
                type='int'
            ),
            static_ip=dict(
                type='str'
            ),
            subnet=dict(
                type='raw'
            ),
            tenant_settings=dict(
                type='dict'
            ),
            state=dict(
                type='str',
                default='present',
                choices=['present', 'absent']
            )
        )

        self._client = None

        self.resource_group = None
        self.name = None
        self.location = None

        self.sku = None
        self.size = None
        self.enable_non_ssl_port = False
        self.configuration_file_path = None
        self.shard_count = None
        self.static_ip = None
        self.subnet = None
        self.tenant_settings = None

        self.tags = None

        self.results = dict(
            changed=False,
            id=None,
            host_name=None
        )
        self.state = None
        self.to_do = Actions.NoAction

        self.frameworks = None

        super(AzureRMRedisCaches, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                 supports_check_mode=True,
                                                 supports_tags=True)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        old_response = None
        response = None
        to_be_updated = False

        # define redis_configuration properties
        self.redis_configuration_properties = ["maxfragmentationmemory_reserved",
                                               "maxmemory_reserved",
                                               "maxmemory_policy",
                                               "notify_keyspace_events"]

        # get management client
        self._client = self.get_mgmt_svc_client(RedisManagementClient,
                                                base_url=self._cloud_environment.endpoints.resource_manager,
                                                api_version='2018-03-01')

        # set location
        resource_group = self.get_resource_group(self.resource_group)
        if not self.location:
            self.location = resource_group.location

        # check subnet exists
        if self.subnet:
            self.subnet = self.parse_subnet()

        # get existing redis cache
        old_response = self.get_rediscache()

        if old_response:
            self.results['id'] = old_response['id']

        if self.state == 'present':
            # if redis not exists
            if not old_response:
                self.log("Redis cache instance doesn't exist")

                to_be_updated = True
                self.to_do = Actions.Create

                if not self.sku:
                    self.fail("Please specify sku to creating new redis cache.")

            else:
                # redis exists already, do update
                self.log("Redis cache instance already exists")

                update_tags, self.tags = self.update_tags(old_response.get('tags', None))

                if update_tags:
                    to_be_updated = True
                    self.to_do = Actions.Update

                # check if update
                if self.check_update(old_response):
                    to_be_updated = True
                    self.to_do = Actions.Update

        elif self.state == 'absent':
            if old_response:
                self.log("Delete Redis cache instance")
                self.results['id'] = old_response['id']
                to_be_updated = True
                self.to_do = Actions.Delete
            else:
                self.results['changed'] = False
                self.log("Redis cache {0} not exists.".format(self.name))

        if to_be_updated:
            self.log('Need to Create/Update redis cache')
            self.results['changed'] = True

            if self.check_mode:
                return self.results

            if self.to_do == Actions.Create:
                response = self.create_rediscache()
                self.results['id'] = response['id']
                self.results['host_name'] = response['host_name']

            if self.to_do == Actions.Update:
                response = self.update_rediscache()
                self.results['id'] = response['id']
                self.results['host_name'] = response['host_name']

            if self.to_do == Actions.Delete:
                self.delete_rediscache()
                self.log('Redis cache instance deleted')

        return self.results

    def check_update(self, existing):
        if self.enable_non_ssl_port is not None and existing['enable_non_ssl_port'] != self.enable_non_ssl_port:
            self.log("enable_non_ssl_port diff: origin {0} / update {1}".format(existing['enable_non_ssl_port'], self.enable_non_ssl_port))
            return True
        if self.sku is not None:
            if existing['sku']['name'] != self.sku['name']:
                self.log("sku diff: origin {0} / update {1}".format(existing['sku']['name'], self.sku['name']))
                return True
            if existing['sku']['size'] != self.sku['size']:
                self.log("size diff: origin {0} / update {1}".format(existing['sku']['size'], self.sku['size']))
                return True
        if self.tenant_settings is not None and existing['tenant_settings'] != self.tenant_settings:
            self.log("tenant_settings diff: origin {0} / update {1}".format(existing['tenant_settings'], self.tenant_settings))
            return True
        if self.shard_count is not None and existing['shard_count'] != self.shard_count:
            self.log("shard_count diff: origin {0} / update {1}".format(existing['shard_count'], self.shard_count))
            return True
        if self.subnet is not None and existing['subnet'] != self.subnet:
            self.log("subnet diff: origin {0} / update {1}".format(existing['subnet'], self.subnet))
            return True
        if self.static_ip is not None and existing['static_ip'] != self.static_ip:
            self.log("static_ip diff: origin {0} / update {1}".format(existing['static_ip'], self.static_ip))
            return True
        for config in self.redis_configuration_properties:
            if getattr(self, config) is not None and existing.get(config, None) != getattr(self, config, None):
                self.log("redis_configuration {0} diff: origin {1} / update {2}".format(config, existing.get(config, None), getattr(self, config, None)))
                return True
        return False

    def create_rediscache(self):
        '''
        Creates redis cache instance with the specified configuration.

        :return: deserialized redis cache instance state dictionary
        '''
        self.log(
            "Creating redis cache instance {0}".format(self.name))

        try:
            redis_config = dict()
            for key in self.redis_configuration_properties:
                if getattr(self, key, None):
                    redis_config[underline_to_hyphen(key)] = underline_to_hyphen(getattr(self, key))

            params = RedisCreateParameters(
                location=self.location,
                sku=Sku(self.sku['name'].title(), self.sku['size'][0], self.sku['size'][1:]),
                tags=self.tags,
                redis_configuration=redis_config,
                enable_non_ssl_port=self.enable_non_ssl_port,
                tenant_settings=self.tenant_settings,
                shard_count=self.shard_count,
                subnet_id=self.subnet,
                static_ip=self.static_ip
            )

            response = self._client.redis.create(resource_group_name=self.resource_group,
                                                 name=self.name,
                                                 parameters=params)
            if isinstance(response, AzureOperationPoller):
                response = self.get_poller_result(response)

        except CloudError as exc:
            self.log('Error attempting to create the redis cache instance.')
            self.fail(
                "Error creating the redis cache instance: {0}".format(str(exc)))
        return rediscache_to_dict(response)

    def update_rediscache(self):
        '''
        Updates redis cache instance with the specified configuration.

        :return: redis cache instance state dictionary
        '''
        self.log(
            "Updating redis cache instance {0}".format(self.name))

        try:
            redis_config = dict()
            for key in self.redis_configuration_properties:
                if getattr(self, key, None):
                    redis_config[underline_to_hyphen(key)] = underline_to_hyphen(getattr(self, key))

            params = RedisUpdateParameters(
                redis_configuration=redis_config,
                enable_non_ssl_port=self.enable_non_ssl_port,
                tenant_settings=self.tenant_settings,
                shard_count=self.shard_count,
                sku=Sku(self.sku['name'].title(), self.sku['size'][0], self.sku['size'][1:]),
                tags=self.tags
            )

            response = self._client.redis.update(resource_group_name=self.resource_group,
                                                 name=self.name,
                                                 parameters=params)
            if isinstance(response, AzureOperationPoller):
                response = self.get_poller_result(response)

        except CloudError as exc:
            self.log('Error attempting to update the redis cache instance.')
            self.fail(
                "Error updating the redis cache instance: {0}".format(str(exc)))
        return rediscache_to_dict(response)

    def delete_rediscache(self):
        '''
        Deletes specified redis cache instance in the specified subscription and resource group.

        :return: True
        '''
        self.log("Deleting the redis cache instance {0}".format(self.name))
        try:
            response = self._client.redis.delete(resource_group_name=self.resource_group,
                                                 name=self.name)
        except CloudError as e:
            self.log('Error attempting to delete the redis cache instance.')
            self.fail(
                "Error deleting the redis cache instance: {0}".format(str(e)))
        return True

    def get_rediscache(self):
        '''
        Gets the properties of the specified redis cache instance.

        :return: redis cache instance state dictionary
        '''
        self.log("Checking if the redis cache instance {0} is present".format(self.name))

        response = None

        try:
            response = self._client.redis.get(resource_group_name=self.resource_group,
                                              name=self.name)

            self.log("Response : {0}".format(response))
            self.log("Redis cache instance : {0} found".format(response.name))
            return rediscache_to_dict(response)

        except CloudError as ex:
            self.log("Didn't find redis cache {0} in resource group {1}".format(
                self.name, self.resource_group))

        return False

    def get_subnet(self):
        '''
        Gets the properties of the specified subnet.

        :return: subnet id
        '''
        self.log("Checking if the subnet {0} is present".format(self.name))

        response = None

        try:
            response = self.network_client.subnets.get(self.subnet['resource_group'],
                                                       self.subnet['virtual_network_name'],
                                                       self.subnet['name'])

            self.log("Subnet found : {0}".format(response))
            return response.id

        except CloudError as ex:
            self.log("Didn't find subnet {0} in resource group {1}".format(
                self.subnet['name'], self.subnet['resource_group']))

        return False

    def parse_subnet(self):
        if isinstance(self.subnet, dict):
            if 'virtual_network_name' not in self.subnet or \
               'name' not in self.subnet:
                self.fail("Subnet dict must contains virtual_network_name and name")
            if 'resource_group' not in self.subnet:
                self.subnet['resource_group'] = self.resource_group
            subnet_id = self.get_subnet()
        else:
            subnet_id = self.subnet
        return subnet_id


def main():
    """Main execution"""
    AzureRMRedisCaches()


if __name__ == '__main__':
    main()
