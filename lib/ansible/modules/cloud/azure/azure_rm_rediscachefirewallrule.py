#!/usr/bin/python
#
# Copyright (c) 2019 Yunge Zhu, <yungez@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_rediscachefirewallrule
version_added: "2.8"
short_description: Manage Azure Cache for Redis Firewall rules
description:
    - Create, update and delete Azure Cache for Redis Firewall rules.

options:
    resource_group:
        description:
            - Name of the resource group to which the resource belongs.
        required: True
    cache_name:
        description:
            - Name of the Azure Cache for Redis.
        required: True
    name:
        description:
            - Name of the Firewall rule.
        required: True
    start_ip_address:
        description:
            - The start IP address of the Azure Cache for Redis Firewall rule. Must be IPv4 format.
            - Required when creating Firewall rule.
    end_ip_address:
        description:
            - The end IP address of the Azure Cache for Redis Firewall rule. Must be IPv4 format.
            - Required when creating Firewall rule.
    state:
      description:
          - Assert the state of the Firewall rule of Azure Cache for Redis.
          - Use C(present) to create or update Firewall rule of Azure Cache for Redis and C(absent) to delete it.
      default: present
      choices:
          - absent
          - present

extends_documentation_fragment:
    - azure

author:
    - Yunge Zhu(@yungezz)

'''

EXAMPLES = '''
  - name: Create a Firewall rule for Azure Cache for Redis
    azure_rm_rediscachefirewallrule:
        resource_group: myResourceGroup
        cache_name: myRedisCache
        name: myRule
        start_ip_address: 192.168.1.1
        end_ip_address: 192.168.1.4

  - name: Update a Firewall rule for Azure Cache for Redis
    azure_rm_rediscachefirewallrule:
        resource_group: myResourceGroup
        cache_name: myRedisCache
        name: myRule
        end_ip_address: 192.168.1.5
'''

RETURN = '''
id:
    description:
        - Id of the Azure Cache for Redis.
    returned: always
    type: str
    sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Cache/redis/myRedis/firewallRules/myRule"
'''

import time
from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from msrest.polling import LROPoller
    from msrestazure.azure_operation import AzureOperationPoller
    from msrest.serialization import Model
    from azure.mgmt.redis import RedisManagementClient
except ImportError:
    # This is handled in azure_rm_common
    pass


def firewall_rule_to_dict(rule):
    return dict(
        id=rule.id,
        name=rule.name,
        start_ip_address=rule.start_ip,
        end_ip_address=rule.end_ip,
        type=rule.type
    )


class Actions:
    NoAction, CreateUpdate, Delete = range(3)


class AzureRMRedisCacheFirewallRule(AzureRMModuleBase):
    """Configuration class for an Azure RM Cache for Redis Firewall Rule resource"""

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
            cache_name=dict(
                type='str',
                required=True
            ),
            start_ip_address=dict(
                type='str'
            ),
            end_ip_address=dict(
                type='str'
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
        self.cache_name = None

        self.start_ip_address = None
        self.end_ip_address = None

        self.results = dict(
            changed=False,
            id=None
        )
        self.state = None

        self.to_do = Actions.NoAction

        super(AzureRMRedisCacheFirewallRule, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                            supports_check_mode=True,
                                                            supports_tags=False)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        for key in list(self.module_arg_spec.keys()):
            setattr(self, key, kwargs[key])

        old_response = None
        response = None

        # get management client
        self._client = self.get_mgmt_svc_client(RedisManagementClient,
                                                base_url=self._cloud_environment.endpoints.resource_manager,
                                                api_version='2018-03-01')

        # check if the firewall rule exists
        old_response = self.get()

        if old_response:
            self.results['id'] = old_response['id']

        if self.state == 'present':
            # if firewall rule not exists
            if not old_response:
                self.log("Firewall Rule of Azure Cache for Redis doesn't exist")

                self.to_do = Actions.CreateUpdate

            else:
                # redis exists already, do update
                self.log("Firewall Rule of Azure Cache for Redis already exists")

                if self.start_ip_address is None:
                    self.start_ip_address = old_response['start_ip_address']
                if self.end_ip_address is None:
                    self.end_ip_address = old_response['end_ip_address']

                # check if update
                if self.check_update(old_response):
                    self.to_do = Actions.CreateUpdate

        elif self.state == 'absent':
            if old_response:
                self.log("Delete Firewall Rule of Azure Cache for Redis")
                self.results['id'] = old_response['id']
                self.to_do = Actions.Delete
            else:
                self.results['changed'] = False
                self.log("Azure Cache for Redis {0} doesn't exist.".format(self.name))

        if self.to_do == Actions.CreateUpdate:
            self.log('Need to Create/Update Firewall rule of Azure Cache for Redis')
            self.results['changed'] = True

            if self.check_mode:
                return self.results

            response = self.create_or_update()
            self.results['id'] = response['id']

        if self.to_do == Actions.Delete:
            self.log('Delete Firewall rule of Azure Cache for Redis')
            self.results['changed'] = True

            if self.check_mode:
                return self.results

            self.delete()
            self.log('Firewall rule of Azure Cache for Redis deleted')

        return self.results

    def check_update(self, existing):
        if self.start_ip_address and self.start_ip_address != existing['start_ip_address']:
            self.log("start_ip_address diff: origin {0} / update {1}".format(existing['start_ip_address'], self.start_ip_address))
            return True
        if self.end_ip_address and self.end_ip_address != existing['end_ip_address']:
            self.log("end_ip_address diff: origin {0} / update {1}".format(existing['end_ip_address'], self.end_ip_address))
            return True
        return False

    def create_or_update(self):
        '''
        Creates Firewall rule of Azure Cache for Redis with the specified configuration.

        :return: deserialized Firewall rule of Azure Cache for Redis state dictionary
        '''
        self.log(
            "Creating Firewall rule of Azure Cache for Redis {0}".format(self.name))

        try:
            response = self._client.firewall_rules.create_or_update(resource_group_name=self.resource_group,
                                                                    cache_name=self.cache_name,
                                                                    rule_name=self.name,
                                                                    start_ip=self.start_ip_address,
                                                                    end_ip=self.end_ip_address)
            if isinstance(response, LROPoller) or isinstance(response, AzureOperationPoller):
                response = self.get_poller_result(response)

        except CloudError as exc:
            self.log('Error attempting to create/update Firewall rule of Azure Cache for Redis.')
            self.fail(
                "Error creating/updating Firewall rule of Azure Cache for Redis: {0}".format(str(exc)))
        return firewall_rule_to_dict(response)

    def delete(self):
        '''
        Deletes specified Firewall rule of Azure Cache for Redis in the specified subscription and resource group.

        :return: True
        '''
        self.log("Deleting the Firewall rule of Azure Cache for Redis {0}".format(self.name))
        try:
            response = self._client.firewall_rules.delete(resource_group_name=self.resource_group,
                                                          rule_name=self.name,
                                                          cache_name=self.cache_name)
        except CloudError as e:
            self.log('Error attempting to delete the Firewall rule of Azure Cache for Redis.')
            self.fail(
                "Error deleting the Firewall rule of Azure Cache for Redis: {0}".format(str(e)))
        return True

    def get(self):
        '''
        Gets the properties of the specified Firewall rule of Azure Cache for Redis.

        :return: Azure Cache for Redis Firewall Rule instance state dictionary
        '''
        self.log("Checking if the Firewall Rule {0} is present".format(self.name))

        response = None

        try:
            response = self._client.firewall_rules.get(resource_group_name=self.resource_group,
                                                       rule_name=self.name,
                                                       cache_name=self.cache_name)

            self.log("Response : {0}".format(response))
            self.log("Redis Firewall Rule : {0} found".format(response.name))
            return firewall_rule_to_dict(response)

        except CloudError as ex:
            self.log("Didn't find Azure Redis Firewall rule {0} in resource group {1}".format(
                self.name, self.resource_group))

        return False


def main():
    """Main execution"""
    AzureRMRedisCacheFirewallRule()


if __name__ == '__main__':
    main()
