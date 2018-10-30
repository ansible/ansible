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
short_description: Manage Database Account instance.
description:
    - Create, update and delete instance of Database Account.

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
                required: True
                choices:
                    - 'eventual'
                    - 'session'
                    - 'bounded_staleness'
                    - 'strong'
                    - 'consistent_prefix'
            max_staleness_prefix:
                description:
                    - "When used with the Bounded Staleness consistency level, this value represents the number of stale requests tolerated. Accepted range
                       for this value is 1 - 2,147,483,647. Required when defaultConsistencyPolicy is set to 'C(bounded_staleness)'."
            max_interval_in_seconds:
                description:
                    - "When used with the Bounded Staleness consistency level, this value represents the time amount of staleness (in seconds) tolerated.
                       Accepted range for this value is 5 - 86400. Required when defaultConsistencyPolicy is set to 'C(bounded_staleness)'."
    locations:
        description:
            - An array that contains the georeplication locations enabled for the Cosmos DB account.
        type: list
        suboptions:
            location_name:
                description:
                    - The name of the region.
            failover_priority:
                description:
                    - "The failover priority of the region. A failover priority of 0 indicates a write region. The maximum value for a failover priority =
                       (total number of regions - 1). Failover priority values must be unique for each of the regions in which the database account exists."
    database_account_offer_type:
        description:
            - TBD
    ip_range_filter:
        description:
            - "Cosmos DB Firewall Support: This value specifies the set of IP addresses or IP address ranges in CIDR form to be included as the allowed list
               of client IPs for a given database account. IP addresses/ranges must be comma separated and must not contain any spaces."
    is_virtual_network_filter_enabled:
        description:
            - Flag to indicate whether to enable/disable Virtual Network ACL rules.
    enable_automatic_failover:
        description:
            - "Enables automatic failover of the write region in the rare event that the region is unavailable due to an outage. Automatic failover will
               result in a new write region for the account and is chosen based on the failover priorities configured for the account."
    capabilities:
        description:
            - List of Cosmos DB capabilities for the account
        type: list
        suboptions:
            name:
                description:
                    - "Name of the Cosmos DB capability. For example, 'name': 'EnableCassandra'. Current values also include 'EnableTable' and
                       'EnableGremlin'."
    virtual_network_rules:
        description:
            - List of Virtual Network ACL rules configured for the Cosmos DB account.
        type: list
        suboptions:
            id:
                description:
                    - "Resource ID of a subnet, for example:
                       /subscriptions/{subscriptionId}/resourceGroups/{groupName}/providers/Microsoft.Network/virtualNetworks/{virtualNetworkName}/subnets/{
                      subnetName}."
    enable_multiple_write_locations:
        description:
            - Enables the account to write in multiple I(locations)
    state:
      description:
        - Assert the state of the Database Account.
        - Use 'present' to create or update an Database Account and 'absent' to delete it.
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
  - name: Create (or update) Database Account
    azure_rm_cosmosdbaccount:
      resource_group: rg1
      name: ddb1
      location: westus
      locations:
        - location_name: eastus
          failover_priority: 0
      database_account_offer_type: Standard
'''

RETURN = '''
id:
    description:
        - The unique resource identifier of the database account.
    returned: always
    type: str
    sample: /subscriptions/subid/resourceGroups/rg1/providers/Microsoft.DocumentDB/databaseAccounts/ddb1
'''

import time
from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from msrest.polling import LROPoller
    from msrestazure.azure_operation import AzureOperationPoller
    from azure.mgmt.cosmosdb import CosmosDB
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass

comparison_failure = {}

class Actions:
    NoAction, Create, Update, Delete = range(4)


class AzureRMDatabaseAccounts(AzureRMModuleBase):
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
                type='dict'
            ),
            locations=dict(
                type='list'
            ),
            database_account_offer_type=dict(
                type='str'
            ),
            ip_range_filter=dict(
                type='str'
            ),
            is_virtual_network_filter_enabled=dict(
                type='str'
            ),
            enable_automatic_failover=dict(
                type='str'
            ),
            capabilities=dict(
                type='list'
            ),
            virtual_network_rules=dict(
                type='list'
            ),
            enable_multiple_write_locations=dict(
                type='str'
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

        super(AzureRMDatabaseAccounts, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                      supports_check_mode=True,
                                                      supports_tags=True)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
            elif kwargs[key] is not None:
                if key == "location":
                    self.parameters["location"] = kwargs[key]
                elif key == "kind":
                    ev = kwargs[key]
                    if ev == 'global_document_db':
                        ev = 'GlobalDocumentDB'
                    elif ev == 'mongo_db':
                        ev = 'MongoDB'
                    self.parameters["kind"] = _snake_to_camel(ev, True)
                elif key == "consistency_policy":
                    ev = kwargs[key]
                    if 'default_consistency_level' in ev:
                        if ev['default_consistency_level'] == 'eventual':
                            ev['default_consistency_level'] = 'Eventual'
                        elif ev['default_consistency_level'] == 'session':
                            ev['default_consistency_level'] = 'Session'
                        elif ev['default_consistency_level'] == 'bounded_staleness':
                            ev['default_consistency_level'] = 'BoundedStaleness'
                        elif ev['default_consistency_level'] == 'strong':
                            ev['default_consistency_level'] = 'Strong'
                        elif ev['default_consistency_level'] == 'consistent_prefix':
                            ev['default_consistency_level'] = 'ConsistentPrefix'
                    self.parameters["consistency_policy"] = ev
                elif key == "locations":
                    self.parameters["locations"] = kwargs[key]
                elif key == "database_account_offer_type":
                    self.parameters["database_account_offer_type"] = kwargs[key]
                elif key == "ip_range_filter":
                    self.parameters["ip_range_filter"] = kwargs[key]
                elif key == "is_virtual_network_filter_enabled":
                    self.parameters["is_virtual_network_filter_enabled"] = kwargs[key]
                elif key == "enable_automatic_failover":
                    self.parameters["enable_automatic_failover"] = kwargs[key]
                elif key == "capabilities":
                    self.parameters["capabilities"] = kwargs[key]
                elif key == "virtual_network_rules":
                    self.parameters["virtual_network_rules"] = kwargs[key]
                elif key == "enable_multiple_write_locations":
                    self.parameters["enable_multiple_write_locations"] = kwargs[key]

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
                if (not compare(self.parameters, old_response,
                                {'location': 'location',
                                 'kind': None,
                                 'consistency_policy': {
                                     'default_consistency_level': None,
                                     'max_staleness_prefix': None,
                                     'max_interval_in_seconds': None
                                 },
                                 'ip_range_filter': None,
                                 'enable_automatic_failover': None,
                                 'enable_multiple_write_locations': None,
                                 'locations': {
                                     'location_name': 'location',
                                     '__sort__': 'failover_priority'
                                 }
                                })):
                    self.to_do = Actions.Update
                self.results['comparison_failure'] = comparison_failure

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
            # make sure instance is actually deleted, for some Azure resources, instance is hanging around
            # for some time after deletion -- this should be really fixed in Azure.
            while self.get_databaseaccount():
                time.sleep(20)
        else:
            self.log("Database Account instance unchanged")
            self.results['changed'] = False
            response = old_response

        if self.state == 'present':
            self.results.update(self.format_item(response))
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

    def format_item(self, d):
        d = {
            'id': d.get('id', None)
        }
        return d


def compare(a, b, t):
    if isinstance(t, dict):
        if isinstance(a, list) and isinstance(b, list):
            s = t.get('__sort__', None)
            if s is not None:
                a = sorted(a, key=lambda x: x[s])
                b = sorted(b, key=lambda x: x[s])
            if len(a) != len(b):
                comparison_failure['error'] = "DDD " + str(a) + "--" + str(b) 
                return False
            for i in range(len(a)):
                if not compare(a[i], b[i], t):
                    return False
            return True
        elif isinstance(a, dict) and isinstance(b, dict):
            for k in t.keys():
                if not k == '__sort__':
                    if not compare(a.get(k, None), b.get(k, None), t[k]):
                        return False
            return True
        else:
            comparison_failure['error'] = "AAA " + str(a) + "--" + str(b) 
            return a is None
    else:
        if a is None:
            return True
        if t == "location":
            # location needs to be normalized, remove spaces, lowercase
            a = a.replace(' ', '').lower()
            b = b.replace(' ', '').lower()
            if a != b:
                comparison_failure['error'] = "BBB " + str(a) + "--" + str(b) 
            return a == b
        else:
            # default comparison
            if a != b:
                comparison_failure['error'] = "CCC " + str(a) + "--" + str(b) 
            return a == b


def _snake_to_camel(snake, capitalize_first=False):
    if capitalize_first:
        return ''.join(x.capitalize() or '_' for x in snake.split('_'))
    else:
        return snake.split('_')[0] + ''.join(x.capitalize() or '_' for x in snake.split('_')[1:])


def main():
    """Main execution"""
    AzureRMDatabaseAccounts()


if __name__ == '__main__':
    main()
