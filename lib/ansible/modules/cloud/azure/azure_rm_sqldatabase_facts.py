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
module: azure_rm_sqldatabase_facts
version_added: "2.5"
short_description: Get SQL Database facts.
description:
    - Get facts of SQL Database.

options:
    resource_group:
        description:
            - The name of the resource group that contains the resource. You can obtain this value from the Azure Resource Manager API or the portal.
        required: True
    server_name:
        description:
            - The name of the server.
        required: True
    database_name:
        description:
            - The name of the database to be retrieved.
    expand:
        description:
            - "A comma separated list of child objects to expand in the response. Possible properties: serviceTierAdvisors, transparentDataEncryption."
    filter:
        description:
            - An OData filter expression that describes a subset of databases to return.
    elastic_pool_name:
        description:
            - The name of the elastic pool to be retrieved.
    recommended_elastic_pool_name:
        description:
            - The name of the recommended elastic pool to be retrieved.

extends_documentation_fragment:
    - azure

author:
    - "Zim Kalinowski (@zikalino)"

'''

EXAMPLES = '''
  - name: Get instance of SQL Database
    azure_rm_sqldatabase_facts:
      resource_group: resource_group_name
      server_name: server_name
      database_name: database_name
      expand: expand

  - name: List instances of SQL Database
    azure_rm_sqldatabase_facts:
      resource_group: resource_group_name
      server_name: server_name
      expand: expand
      filter: filter

  - name: List instances of SQL Database
    azure_rm_sqldatabase_facts:
      resource_group: resource_group_name
      server_name: server_name
      elastic_pool_name: elastic_pool_name

  - name: List instances of SQL Database
    azure_rm_sqldatabase_facts:
      resource_group: resource_group_name
      server_name: server_name
      recommended_elastic_pool_name: recommended_elastic_pool_name
'''

RETURN = '''
databases:
    description: A list of dict results where the key is the name of the SQL Database and the values are the facts for that SQL Database.
    returned: always
    type: complex
    contains:
        sqldatabase_name:
            description: The key is the name of the server that the values relate to.
            type: complex
            contains:
                id:
                    description:
                        - Resource ID.
                    returned: always
                    type: str
                    sample: "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/sqlcrudtest-6852/providers/Microsoft.Sql/servers/sqlcrudtest-
                            2080/databases/sqlcrudtest-9187"
                name:
                    description:
                        - Resource name.
                    returned: always
                    type: str
                    sample: sqlcrudtest-9187
                type:
                    description:
                        - Resource type.
                    returned: always
                    type: str
                    sample: Microsoft.Sql/servers/databases
                location:
                    description:
                        - Resource location.
                    returned: always
                    type: str
                    sample: Japan East
                kind:
                    description:
                        - Kind of database.  This is metadata used for the Azure portal experience.
                    returned: always
                    type: str
                    sample: v12.0,user
                collation:
                    description:
                        - The collation of the database. If createMode is not Default, this value is ignored.
                    returned: always
                    type: str
                    sample: SQL_Latin1_General_CP1_CI_AS
                edition:
                    description:
                        - "The edition of the database. The DatabaseEditions enumeration contains all the valid editions. If createMode is NonReadableSeconda
                          ry or OnlineSecondary, this value is ignored. To see possible values, query the capabilities API (/subscriptions/{subscriptionId}/
                          providers/Microsoft.Sql/locations/{locationID}/capabilities) referred to by operationId: 'Capabilities_ListByLocation.'. Possible
                          values include: 'Web', 'Business', 'Basic', 'Standard', 'Premium', 'Free', 'Stretch', 'DataWarehouse', 'System', 'System2'"
                    returned: always
                    type: str
                    sample: Basic
                status:
                    description:
                        - The status of the database.
                    returned: always
                    type: str
                    sample: Online
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from msrestazure.azure_operation import AzureOperationPoller
    from azure.mgmt.sql import SqlManagementClient
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMDatabasesFacts(AzureRMModuleBase):
    def __init__(self):
        # define user inputs into argument
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                required=True
            ),
            server_name=dict(
                type='str',
                required=True
            ),
            database_name=dict(
                type='str'
            ),
            expand=dict(
                type='str'
            ),
            filter=dict(
                type='str'
            ),
            elastic_pool_name=dict(
                type='str'
            ),
            recommended_elastic_pool_name=dict(
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
        self.server_name = None
        self.database_name = None
        self.expand = None
        self.filter = None
        self.elastic_pool_name = None
        self.recommended_elastic_pool_name = None
        super(AzureRMDatabasesFacts, self).__init__(self.module_arg_spec)

    def exec_module(self, **kwargs):
        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])
        self.mgmt_client = self.get_mgmt_svc_client(SqlManagementClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        if (self.resource_group is not None and
                self.server_name is not None and
                self.database_name is not None):
            self.results['databases'] = self.get()
        elif (self.resource_group is not None and
              self.server_name is not None):
            self.results['databases'] = self.list_by_server()
        elif (self.resource_group is not None and
              self.server_name is not None and
              self.elastic_pool_name is not None):
            self.results['databases'] = self.list_by_elastic_pool()
        elif (self.resource_group is not None and
              self.server_name is not None and
              self.recommended_elastic_pool_name is not None):
            self.results['databases'] = self.list_by_recommended_elastic_pool()
        return self.results

    def get(self):
        '''
        Gets facts of the specified SQL Database.

        :return: deserialized SQL Databaseinstance state dictionary
        '''
        response = None
        results = {}
        try:
            response = self.mgmt_client.databases.get(resource_group_name=self.resource_group,
                                                      server_name=self.server_name,
                                                      database_name=self.database_name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for Databases.')

        if response is not None:
            results[response.name] = response.as_dict()

        return results

    def list_by_server(self):
        '''
        Gets facts of the specified SQL Database.

        :return: deserialized SQL Databaseinstance state dictionary
        '''
        response = None
        results = {}
        try:
            response = self.mgmt_client.databases.list_by_server(resource_group_name=self.resource_group,
                                                                 server_name=self.server_name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for Databases.')

        if response is not None:
            for item in response:
                results[item.name] = item.as_dict()

        return results

    def list_by_elastic_pool(self):
        '''
        Gets facts of the specified SQL Database.

        :return: deserialized SQL Databaseinstance state dictionary
        '''
        response = None
        results = {}
        try:
            response = self.mgmt_client.databases.list_by_elastic_pool(resource_group_name=self.resource_group,
                                                                       server_name=self.server_name,
                                                                       elastic_pool_name=self.elastic_pool_name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for Databases.')

        if response is not None:
            for item in response:
                results[item.name] = item.as_dict()

        return results

    def list_by_recommended_elastic_pool(self):
        '''
        Gets facts of the specified SQL Database.

        :return: deserialized SQL Databaseinstance state dictionary
        '''
        response = None
        results = {}
        try:
            response = self.mgmt_client.databases.list_by_recommended_elastic_pool(resource_group_name=self.resource_group,
                                                                                   server_name=self.server_name,
                                                                                   recommended_elastic_pool_name=self.recommended_elastic_pool_name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for Databases.')

        if response is not None:
            for item in response:
                results[item.name] = item.as_dict()

        return results


def main():
    AzureRMDatabasesFacts()
if __name__ == '__main__':
    main()
