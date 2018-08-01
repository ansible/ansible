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
module: azure_rm_postgresqlserver_facts
version_added: "2.7"
short_description: Get PostgreSQL Server facts.
description:
    - Get facts of PostgreSQL Server.

options:
    resource_group:
        description:
            - The name of the resource group that contains the resource. You can obtain this value from the Azure Resource Manager API or the portal.
        required: True
    server_name:
        description:
            - The name of the server.

extends_documentation_fragment:
    - azure

author:
    - "Zim Kalinowski (@zikalino)"

'''

EXAMPLES = '''
  - name: Get instance of PostgreSQL Server
    azure_rm_postgresqlserver_facts:
      resource_group: resource_group_name
      server_name: server_name

  - name: List instances of PostgreSQL Server
    azure_rm_postgresqlserver_facts:
      resource_group: resource_group_name
'''

RETURN = '''
servers:
    description: A list of dict results where the key is the name of the PostgreSQL Server and the values are the facts for that PostgreSQL Server.
    returned: always
    type: complex
    contains:
        id:
            description:
                - Resource ID
            returned: always
            type: str
            sample: /subscriptions/ffffffff-ffff-ffff-ffff-ffffffffffff/resourceGroups/TestGroup/providers/Microsoft.DBforPostgreSQL/servers/testserver
        name:
            description:
                - Resource name.
            returned: always
            type: str
            sample: testserver
        type:
            description:
                - Resource type.
            returned: always
            type: str
            sample: Microsoft.DBforPostgreSQL/servers
        location:
            description:
                - The location the resource resides in.
            returned: always
            type: str
            sample: onebox
        sku:
            description:
                - The SKU (pricing tier) of the server.
            returned: always
            type: complex
            contains:
                name:
                    description:
                        - The name of the SKU
                    returned: always
                    type: str
                    sample: PGSQLB100
                tier:
                    description:
                        - The tier of the particular SKU
                    returned: always
                    type: str
                    sample: Basic
                capacity:
                    description:
                        - "The scale up/out capacity, representing server's compute units."
                    returned: always
                    type: int
                    sample: 100
        version:
            description:
                - Server version.
            returned: always
            type: str
            sample: version
        user_visible_state:
            description:
                - "A state of a server that is visible to user. Possible values include: 'Ready', 'Dropping', 'Disabled'"
            returned: always
            type: str
            sample: user_visible_state
        fully_qualified_domain_name:
            description:
                - The fully qualified domain name of a server.
            returned: always
            type: str
            sample: fully_qualified_domain_name
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from msrestazure.azure_operation import AzureOperationPoller
    from azure.mgmt.rdbms.postgresql import PostgreSQLManagementClient
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMServersFacts(AzureRMModuleBase):
    def __init__(self):
        # define user inputs into argument
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                required=True
            ),
            server_name=dict(
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
        super(AzureRMServersFacts, self).__init__(self.module_arg_spec, supports_tags=False)

    def exec_module(self, **kwargs):
        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])
        self.mgmt_client = self.get_mgmt_svc_client(PostgreSQLManagementClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        if (self.resource_group is not None and
                self.server_name is not None):
            self.results['servers'] = self.get()
        elif (self.resource_group is not None):
            self.results['servers'] = self.list_by_resource_group()
        return self.results

    def get(self):
        response = None
        results = []
        try:
            response = self.mgmt_client.servers.get(resource_group_name=self.resource_group,
                                                    server_name=self.server_name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for PostgreSQL Server.')

        if response is not None:
            results.append(self.format_item(response))

        return results

    def list_by_resource_group(self):
        response = None
        results = []
        try:
            response = self.mgmt_client.servers.list_by_resource_group(resource_group_name=self.resource_group)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for PostgreSQL Servers.')

        if response is not None:
            for item in response:
                results.append(self.format_item(item))

        return results

    def format_item(self, item):
        d = item.as_dict()
        d = {
            'id': d['id'],
            'resource_group': self.resource_group,
            'name': d['name'],
            'sku': d['sku'],
            'location': d['location'],
            'storage_mb': d['storage_profile']['storage_mb'],
            'version': d['version'],
            'enforce_ssl': (d['ssl_enforcement'] == 'Enabled'),
            'admin_username': d['administrator_login']
        }

        return d


def main():
    AzureRMServersFacts()


if __name__ == '__main__':
    main()
