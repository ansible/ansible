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
module: azure_rm_sqldatabase_facts
version_added: "2.8"
short_description: Get Azure SQL Database facts.
description:
    - Get facts of Azure SQL Database.

options:
    resource_group:
        description:
            - The name of the resource group that contains the resource. You can obtain this value from the Azure Resource Manager API or the portal.
        required: True
    server_name:
        description:
            - The name of the server.
        required: True
    name:
        description:
            - The name of the database.
    elastic_pool_name:
        description:
            - The name of the elastic pool.
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.

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
      name: database_name

  - name: List instances of SQL Database
    azure_rm_sqldatabase_facts:
      resource_group: resource_group_name
      server_name: server_name
      elastic_pool_name: elastic_pool_name

  - name: List instances of SQL Database
    azure_rm_sqldatabase_facts:
      resource_group: resource_group_name
      server_name: server_name
'''

RETURN = '''
databases:
    description: A list of dictionaries containing facts for SQL Database.
    returned: always
    type: complex
    contains:
        id:
            description:
                - Resource ID.
            returned: always
            type: str
            sample: "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/Default-SQL-SouthEastAsia/providers/Microsoft.Sql/servers/testsvr/dat
                    abases/testdb"
        name:
            description:
                - Resource name.
            returned: always
            type: str
            sample: testdb
        location:
            description:
                - Resource location.
            returned: always
            type: str
            sample: southeastasia
        tags:
            description:
                - Resource tags.
            returned: always
            type: complex
            sample: tags
        sku:
            description:
                - The name and tier of the SKU.
            returned: always
            type: complex
            sample: sku
            contains:
                name:
                    description:
                        - The name of the SKU. Ex - P3. It is typically a letter+number code
                    returned: always
                    type: str
                    sample: BC_Gen4_2
                tier:
                    description:
                        - This field is required to be implemented by the Resource Provider if the service has more than one tier, but is not required on a PUT.
                    returned: always
                    type: str
                    sample: BusinessCritical
                capacity:
                    description:
                        - "If the SKU supports scale out/in then the capacity integer should be included. If scale out/in is not possible for the resource
                           this may be omitted."
                    returned: always
                    type: int
                    sample: 2
        kind:
            description:
                - Kind of database. This is metadata used for the Azure portal experience.
            returned: always
            type: str
            sample: v12.0,user
        status:
            description:
                - "The status of the database. Possible values include: 'Online', 'Restoring', 'RecoveryPending', 'Recovering', 'Suspect', 'Offline',
                   'Standby', 'Shutdown', 'EmergencyMode', 'AutoClosed', 'Copying', 'Creating', 'Inaccessible', 'OfflineSecondary', 'Pausing', 'Paused',
                   'Resuming', 'Scaling'"
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
            name=dict(
                type='str'
            ),
            elastic_pool_name=dict(
                type='str'
            ),
            tags=dict(
                type='list'
            )
        )
        # store the results of the module operation
        self.results = dict(
            changed=False
        )
        self.mgmt_client = None
        self.resource_group = None
        self.server_name = None
        self.name = None
        self.elastic_pool_name = None
        self.tags = None
        super(AzureRMDatabasesFacts, self).__init__(self.module_arg_spec, supports_tags=False)

    def exec_module(self, **kwargs):
        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])
        self.mgmt_client = self.get_mgmt_svc_client(SqlManagementClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        if self.name is not None:
            self.results['databases'] = self.get()
        elif self.elastic_pool_name is not None:
            self.results['databases'] = self.list_by_elastic_pool()
        else:
            self.results['databases'] = self.list_by_server()
        return self.results

    def get(self):
        response = None
        results = []
        try:
            response = self.mgmt_client.databases.get(resource_group_name=self.resource_group,
                                                      server_name=self.server_name,
                                                      database_name=self.name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for Databases.')

        if response and self.has_tags(response.tags, self.tags):
            results.append(self.format_item(response))

        return results

    def list_by_elastic_pool(self):
        response = None
        results = []
        try:
            response = self.mgmt_client.databases.list_by_elastic_pool(resource_group_name=self.resource_group,
                                                                       server_name=self.server_name,
                                                                       elastic_pool_name=self.elastic_pool_name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for Databases.')

        if response is not None:
            for item in response:
                if self.has_tags(item.tags, self.tags):
                    results.append(self.format_item(item))

        return results

    def list_by_server(self):
        response = None
        results = []
        try:
            response = self.mgmt_client.databases.list_by_server(resource_group_name=self.resource_group,
                                                                 server_name=self.server_name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for Databases.')

        if response is not None:
            for item in response:
                if self.has_tags(item.tags, self.tags):
                    results.append(self.format_item(item))

        return results

    def format_item(self, item):
        d = item.as_dict()
        d = {
            'resource_group': self.resource_group,
            'server_name': self.server_name,
            'id': d['id'],
            'name': d['name'],
            'location': d['location'],
            'tags': d['tags'],
            'sku': {'name': d['sku']['name'],
                    'tier': d['sku']['tier'],
                    'capacity': d['sku']['capacity']},
            'kind': d['kind'],
            'status': d['status']
        }
        return d


def main():
    AzureRMDatabasesFacts()


if __name__ == '__main__':
    main()
