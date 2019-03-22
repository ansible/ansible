#!/usr/bin/python
#
# Copyright (c) 2018 Zim Kalinowski, <zikalino@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_cosmosdbaccount
version_added: "2.8"
short_description: Manage Azure Database Account instance.
description:
    - Create, update and delete instance of Azure Database Account.

options:
    resource_group:
        description:
            - Name of an Azure resource group.
        required: True
    name:
        description:
            - Cosmos DB database account name.
        required: True
    location:
        description:
            - The location of the resource group to which the resource belongs.
            - Required when C(state) is I(present).
    kind:
        description:
            - Indicates the type of database account. This can only be set at database account creation.
        choices:
            - 'global_document_db'
            - 'mongo_db'
            - 'parse'
    consistency_policy:
        description:
            - The consistency policy for the Cosmos DB account.
        suboptions:
            default_consistency_level:
                description:
                    - The default consistency level and configuration settings of the Cosmos DB account.
                    - Required when C(state) is I(present).
                choices:
                    - 'eventual'
                    - 'session'
                    - 'bounded_staleness'
                    - 'strong'
                    - 'consistent_prefix'
            max_staleness_prefix:
                description:
                    - "When used with the Bounded Staleness consistency level, this value represents the number of stale requests tolerated. Accepted range
                       for this value is 1 - 2,147,483,647. Required when I(default_consistency_policy) is set to C(bounded_staleness)."
                type: int
            max_interval_in_seconds:
                description:
                    - "When used with the Bounded Staleness consistency level, this value represents the time amount of staleness (in seconds) tolerated.
                       Accepted range for this value is 5 - 86400. Required when I(default_consistency_policy) is set to C(bounded_staleness)."
                type: int
    geo_rep_locations:
        description:
            - An array that contains the georeplication locations enabled for the Cosmos DB account.
            - Required when C(state) is I(present).
        type: list
        suboptions:
            name:
                description:
                    - The name of the region.
            failover_priority:
                description:
                    - "The failover priority of the region. A failover priority of 0 indicates a write region. The maximum value for a failover priority =
                       (total number of regions - 1). Failover priority values must be unique for each of the regions in which the database account exists."
                type: int
    database_account_offer_type:
        description:
            - Database account offer type, for example I(Standard)
            - Required when C(state) is I(present).
    ip_range_filter:
        description:
            - "Cosmos DB Firewall Support: This value specifies the set of IP addresses or IP address ranges in CIDR form to be included as the allowed list
               of client IPs for a given database account. IP addresses/ranges must be comma separated and must not contain any spaces."
    is_virtual_network_filter_enabled:
        description:
            - Flag to indicate whether to enable/disable Virtual Network ACL rules.
        type: bool
    enable_automatic_failover:
        description:
            - "Enables automatic failover of the write region in the rare event that the region is unavailable due to an outage. Automatic failover will
               result in a new write region for the account and is chosen based on the failover priorities configured for the account."
        type: bool
    enable_cassandra:
        description:
            - Enable Cassandra.
        type: bool
    enable_table:
        description:
            - Enable Table.
        type: bool
    enable_gremlin:
        description:
            - Enable Gremlin.
        type: bool
    virtual_network_rules:
        description:
            - List of Virtual Network ACL rules configured for the Cosmos DB account.
        type: list
        suboptions:
            subnet:
                description:
                    - It can be a string containing resource id of a subnet.
                    - It can be a dictionary containing 'resource_group', 'virtual_network_name' and 'subnet_name'
            ignore_missing_vnet_service_endpoint:
                description:
                    - Create Cosmos DB account without existing virtual network service endpoint.
                type: bool

    enable_multiple_write_locations:
        description:
            - Enables the account to write in multiple locations
        type: bool
    state:
      description:
        - Assert the state of the Database Account.
        - Use C(present) to create or update an Database Account and C(absent) to delete it.
      default: present
      choices:
        - absent
        - present

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Zim Kalinowski (@zikalino)"

'''

EXAMPLES = '''
  - name: Create Cosmos DB Account - min
    azure_rm_cosmosdbaccount:
      resource_group: myResourceGroup
      name: myDatabaseAccount
      location: westus
      geo_rep_locations:
        - name: southcentralus
          failover_priority: 0
      database_account_offer_type: Standard

  - name: Create Cosmos DB Account - max
    azure_rm_cosmosdbaccount:
      resource_group: myResourceGroup
      name: myDatabaseAccount
      location: westus
      kind: mongo_db
      geo_rep_locations:
        - name: southcentralus
          failover_priority: 0
      database_account_offer_type: Standard
      ip_range_filter: 10.10.10.10
      enable_multiple_write_locations: yes
      virtual_network_rules:
        - subnet: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Network/virtualNetworks/myVi
                   rtualNetwork/subnets/mySubnet"
      consistency_policy:
        default_consistency_level: bounded_staleness
        max_staleness_prefix: 10
        max_interval_in_seconds: 1000
'''

RETURN = '''
id:
    description:
        - The unique resource identifier of the database account.
    returned: always
    type: str
    sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.DocumentDB/databaseAccounts/myData
             baseAccount"
'''

import time
from ansible.module_utils.azure_rm_common import AzureRMModuleBase
from ansible.module_utils.common.dict_transformations import _snake_to_camel

try:
    from msrestazure.azure_exceptions import CloudError
    from msrest.polling import LROPoller
    from msrestazure.azure_operation import AzureOperationPoller
    from azure.mgmt.cosmosdb import CosmosDB
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass


class Actions:
    NoAction, Create, Update, Delete = range(4)


class AzureRMCosmosDBAccount(AzureRMModuleBase):
    """Configuration class for an Azure RM Database Account resource"""

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
            kind=dict(
                type='str',
                choices=['global_document_db',
                         'mongo_db',
                         'parse']
            ),
            consistency_policy=dict(
                type='dict',
                options=dict(
                    default_consistency_level=dict(
                        type='str',
                        choices=['eventual',
                                 'session',
                                 'bounded_staleness',
                                 'strong',
                                 'consistent_prefix']
                    ),
                    max_staleness_prefix=dict(
                        type='int'
                    ),
                    max_interval_in_seconds=dict(
                        type='int'
                    )
                )
            ),
            geo_rep_locations=dict(
                type='list',
                options=dict(
                    name=dict(
                        type='str',
                        required=True
                    ),
                    failover_priority=dict(
                        type='int',
                        required=True
                    )
                )
            ),
            database_account_offer_type=dict(
                type='str'
            ),
            ip_range_filter=dict(
                type='str'
            ),
            is_virtual_network_filter_enabled=dict(
                type='bool'
            ),
            enable_automatic_failover=dict(
                type='bool'
            ),
            enable_cassandra=dict(
                type='bool'
            ),
            enable_table=dict(
                type='bool'
            ),
            enable_gremlin=dict(
                type='bool'
            ),
            virtual_network_rules=dict(
                type='list',
                options=dict(
                    id=dict(
                        type='str',
                        required=True
                    ),
                    ignore_missing_vnet_service_endpoint=dict(
                        type='bool'
                    )
                )
            ),
            enable_multiple_write_locations=dict(
                type='bool'
            ),
            state=dict(
                type='str',
                default='present',
                choices=['present', 'absent']
            )
        )

        self.resource_group = None
        self.name = None
        self.parameters = dict()

        self.results = dict(changed=False)
        self.mgmt_client = None
        self.state = None
        self.to_do = Actions.NoAction

        super(AzureRMCosmosDBAccount, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                     supports_check_mode=True,
                                                     supports_tags=True)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
            elif kwargs[key] is not None:
                self.parameters[key] = kwargs[key]

        kind = self.parameters.get('kind')
        if kind == 'global_document_db':
            self.parameters['kind'] = 'GlobalDocumentDB'
        elif kind == 'mongo_db':
            self.parameters['kind'] = 'MongoDB'
        elif kind == 'parse':
            self.parameters['kind'] = 'Parse'

        dict_camelize(self.parameters, ['consistency_policy', 'default_consistency_level'], True)
        dict_rename(self.parameters, ['geo_rep_locations', 'name'], 'location_name')
        dict_rename(self.parameters, ['geo_rep_locations'], 'locations')
        self.parameters['capabilities'] = []
        if self.parameters.pop('enable_cassandra', False):
            self.parameters['capabilities'].append({'name': 'EnableCassandra'})
        if self.parameters.pop('enable_table', False):
            self.parameters['capabilities'].append({'name': 'EnableTable'})
        if self.parameters.pop('enable_gremlin', False):
            self.parameters['capabilities'].append({'name': 'EnableGremlin'})

        for rule in self.parameters.get('virtual_network_rules', []):
            subnet = rule.pop('subnet')
            if isinstance(subnet, dict):
                virtual_network_name = subnet.get('virtual_network_name')
                subnet_name = subnet.get('subnet_name')
                resource_group_name = subnet.get('resource_group', self.resource_group)
                template = "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Network/virtualNetworks/{2}/subnets/{3}"
                subnet = template.format(self.subscription_id, resource_group_name, virtual_network_name, subnet_name)
            rule['id'] = subnet

        response = None

        self.mgmt_client = self.get_mgmt_svc_client(CosmosDB,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        resource_group = self.get_resource_group(self.resource_group)

        if "location" not in self.parameters:
            self.parameters["location"] = resource_group.location

        old_response = self.get_databaseaccount()

        if not old_response:
            self.log("Database Account instance doesn't exist")
            if self.state == 'absent':
                self.log("Old instance didn't exist")
            else:
                self.to_do = Actions.Create
        else:
            self.log("Database Account instance already exists")
            if self.state == 'absent':
                self.to_do = Actions.Delete
            elif self.state == 'present':
                old_response['locations'] = old_response['failover_policies']
                if not default_compare(self.parameters, old_response, '', self.results):
                    self.to_do = Actions.Update

        if (self.to_do == Actions.Create) or (self.to_do == Actions.Update):
            self.log("Need to Create / Update the Database Account instance")

            if self.check_mode:
                self.results['changed'] = True
                return self.results

            response = self.create_update_databaseaccount()

            self.results['changed'] = True
            self.log("Creation / Update done")
        elif self.to_do == Actions.Delete:
            self.log("Database Account instance deleted")
            self.results['changed'] = True

            if self.check_mode:
                return self.results

            self.delete_databaseaccount()
        else:
            self.log("Database Account instance unchanged")
            self.results['changed'] = False
            response = old_response

        if self.state == 'present':
            self.results.update({'id': response.get('id', None)})
        return self.results

    def create_update_databaseaccount(self):
        '''
        Creates or updates Database Account with the specified configuration.

        :return: deserialized Database Account instance state dictionary
        '''
        self.log("Creating / Updating the Database Account instance {0}".format(self.name))

        try:
            response = self.mgmt_client.database_accounts.create_or_update(resource_group_name=self.resource_group,
                                                                           account_name=self.name,
                                                                           create_update_parameters=self.parameters)
            if isinstance(response, LROPoller) or isinstance(response, AzureOperationPoller):
                response = self.get_poller_result(response)

        except CloudError as exc:
            self.log('Error attempting to create the Database Account instance.')
            self.fail("Error creating the Database Account instance: {0}".format(str(exc)))
        return response.as_dict()

    def delete_databaseaccount(self):
        '''
        Deletes specified Database Account instance in the specified subscription and resource group.

        :return: True
        '''
        self.log("Deleting the Database Account instance {0}".format(self.name))
        try:
            response = self.mgmt_client.database_accounts.delete(resource_group_name=self.resource_group,
                                                                 account_name=self.name)

            # This currently doesnt' work as there is a bug in SDK / Service
            # if isinstance(response, LROPoller) or isinstance(response, AzureOperationPoller):
            #     response = self.get_poller_result(response)
        except CloudError as e:
            self.log('Error attempting to delete the Database Account instance.')
            self.fail("Error deleting the Database Account instance: {0}".format(str(e)))

        return True

    def get_databaseaccount(self):
        '''
        Gets the properties of the specified Database Account.

        :return: deserialized Database Account instance state dictionary
        '''
        self.log("Checking if the Database Account instance {0} is present".format(self.name))
        found = False
        try:
            response = self.mgmt_client.database_accounts.get(resource_group_name=self.resource_group,
                                                              account_name=self.name)
            found = True
            self.log("Response : {0}".format(response))
            self.log("Database Account instance : {0} found".format(response.name))
        except CloudError as e:
            self.log('Did not find the Database Account instance.')
        if found is True:
            return response.as_dict()

        return False


def default_compare(new, old, path, result):
    if new is None:
        return True
    elif isinstance(new, dict):
        if not isinstance(old, dict):
            result['compare'] = 'changed [' + path + '] old dict is null'
            return False
        for k in new.keys():
            if not default_compare(new.get(k), old.get(k, None), path + '/' + k, result):
                return False
        return True
    elif isinstance(new, list):
        if not isinstance(old, list) or len(new) != len(old):
            result['compare'] = 'changed [' + path + '] length is different or null'
            return False
        elif len(old) == 0:
            return True
        elif isinstance(old[0], dict):
            key = None
            if 'id' in old[0] and 'id' in new[0]:
                key = 'id'
            elif 'name' in old[0] and 'name' in new[0]:
                key = 'name'
            else:
                key = list(old[0])[0]
            new = sorted(new, key=lambda x: x.get(key, ''))
            old = sorted(old, key=lambda x: x.get(key, ''))
        else:
            new = sorted(new)
            old = sorted(old)
        for i in range(len(new)):
            if not default_compare(new[i], old[i], path + '/*', result):
                return False
        return True
    else:
        if path == '/location' or path.endswith('location_name'):
            new = new.replace(' ', '').lower()
            old = new.replace(' ', '').lower()
        if new == old:
            return True
        else:
            result['compare'] = 'changed [' + path + '] ' + str(new) + ' != ' + str(old)
            return False


def dict_camelize(d, path, camelize_first):
    if isinstance(d, list):
        for i in range(len(d)):
            dict_camelize(d[i], path, camelize_first)
    elif isinstance(d, dict):
        if len(path) == 1:
            old_value = d.get(path[0], None)
            if old_value is not None:
                d[path[0]] = _snake_to_camel(old_value, camelize_first)
        else:
            sd = d.get(path[0], None)
            if sd is not None:
                dict_camelize(sd, path[1:], camelize_first)


def dict_upper(d, path):
    if isinstance(d, list):
        for i in range(len(d)):
            dict_upper(d[i], path)
    elif isinstance(d, dict):
        if len(path) == 1:
            old_value = d.get(path[0], None)
            if old_value is not None:
                d[path[0]] = old_value.upper()
        else:
            sd = d.get(path[0], None)
            if sd is not None:
                dict_upper(sd, path[1:])


def dict_rename(d, path, new_name):
    if isinstance(d, list):
        for i in range(len(d)):
            dict_rename(d[i], path, new_name)
    elif isinstance(d, dict):
        if len(path) == 1:
            old_value = d.pop(path[0], None)
            if old_value is not None:
                d[new_name] = old_value
        else:
            sd = d.get(path[0], None)
            if sd is not None:
                dict_rename(sd, path[1:], new_name)


def dict_expand(d, path, outer_dict_name):
    if isinstance(d, list):
        for i in range(len(d)):
            dict_expand(d[i], path, outer_dict_name)
    elif isinstance(d, dict):
        if len(path) == 1:
            old_value = d.pop(path[0], None)
            if old_value is not None:
                d[outer_dict_name] = d.get(outer_dict_name, {})
                d[outer_dict_name] = old_value
        else:
            sd = d.get(path[0], None)
            if sd is not None:
                dict_expand(sd, path[1:], outer_dict_name)


def main():
    """Main execution"""
    AzureRMCosmosDBAccount()


if __name__ == '__main__':
    main()
