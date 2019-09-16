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
module: azure_rm_sqlserver_info
version_added: "2.9"
short_description: Get SQL Server facts
description:
    - Get facts of SQL Server.

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
    - azure_tags

author:
    - Zim Kalinowski (@zikalino)

'''

EXAMPLES = '''
  - name: Get instance of SQL Server
    azure_rm_sqlserver_info:
      resource_group: myResourceGroup
      server_name: server_name

  - name: List instances of SQL Server
    azure_rm_sqlserver_info:
      resource_group: myResourceGroup
'''

RETURN = '''
servers:
    description:
        - A list of dict results where the key is the name of the SQL Server and the values are the facts for that SQL Server.
    returned: always
    type: complex
    contains:
        sqlserver_name:
            description:
                - The key is the name of the server that the values relate to.
            type: complex
            contains:
                id:
                    description:
                        - Resource ID.
                    returned: always
                    type: str
                    sample: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Sql/servers/sqlcrudtest-4645
                name:
                    description:
                        - Resource name.
                    returned: always
                    type: str
                    sample: sqlcrudtest-4645
                type:
                    description:
                        - Resource type.
                    returned: always
                    type: str
                    sample: Microsoft.Sql/servers
                location:
                    description:
                        - Resource location.
                    returned: always
                    type: str
                    sample: japaneast
                kind:
                    description:
                        - Kind of sql server. This is metadata used for the Azure portal experience.
                    returned: always
                    type: str
                    sample: v12.0
                version:
                    description:
                        - The version of the server.
                    returned: always
                    type: str
                    sample: 12.0
                state:
                    description:
                        - The state of the server.
                    returned: always
                    type: str
                    sample: Ready
                fully_qualified_domain_name:
                    description:
                        - The fully qualified domain name of the server.
                    returned: always
                    type: str
                    sample: fully_qualified_domain_name
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.sql import SqlManagementClient
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMSqlServerInfo(AzureRMModuleBase):
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
        )
        self.resource_group = None
        self.server_name = None
        super(AzureRMSqlServerInfo, self).__init__(self.module_arg_spec)

    def exec_module(self, **kwargs):
        is_old_facts = self.module._name == 'azure_rm_sqlserver_facts'
        if is_old_facts:
            self.module.deprecate("The 'azure_rm_sqlserver_facts' module has been renamed to 'azure_rm_sqlserver_info'", version='2.13')

        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        if (self.resource_group is not None and
                self.server_name is not None):
            self.results['servers'] = self.get()
        elif (self.resource_group is not None):
            self.results['servers'] = self.list_by_resource_group()
        return self.results

    def get(self):
        '''
        Gets facts of the specified SQL Server.

        :return: deserialized SQL Serverinstance state dictionary
        '''
        response = None
        results = {}
        try:
            response = self.sql_client.servers.get(resource_group_name=self.resource_group,
                                                   server_name=self.server_name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for Servers.')

        if response is not None:
            results[response.name] = response.as_dict()

        return results

    def list_by_resource_group(self):
        '''
        Gets facts of the specified SQL Server.

        :return: deserialized SQL Serverinstance state dictionary
        '''
        response = None
        results = {}
        try:
            response = self.sql_client.servers.list_by_resource_group(resource_group_name=self.resource_group)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for Servers.')

        if response is not None:
            for item in response:
                results[item.name] = item.as_dict()

        return results


def main():
    AzureRMSqlServerInfo()


if __name__ == '__main__':
    main()
