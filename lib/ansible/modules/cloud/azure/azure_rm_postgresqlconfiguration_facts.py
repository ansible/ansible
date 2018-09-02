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
module: azure_rm_postgresqlconfiguration_facts
version_added: "2.5"
short_description: Get PostgreSQL Configuration facts.
description:
    - Get facts of PostgreSQL Configuration.

options:
    resource_group:
        description:
            - The name of the resource group that contains the resource. You can obtain this value from the Azure Resource Manager API or the portal.
        required: True
    server_name:
        description:
            - The name of the server.
        required: True
    configuration_name:
        description:
            - The name of the server configuration.

extends_documentation_fragment:
    - azure

author:
    - "Zim Kalinowski (@zikalino)"

'''

EXAMPLES = '''
  - name: Get instance of PostgreSQL Configuration
    azure_rm_postgresqlconfiguration_facts:
      resource_group: resource_group_name
      server_name: server_name
      configuration_name: configuration_name

  - name: List instances of PostgreSQL Configuration
    azure_rm_postgresqlconfiguration_facts:
      resource_group: resource_group_name
      server_name: server_name
'''

RETURN = '''
configurations:
    description: A list of dict results where the key is the name of the PostgreSQL Configuration and the values are the facts for that PostgreSQL Configuration.
    returned: always
    type: complex
    contains:
        postgresqlconfiguration_name:
            description: The key is the name of the server that the values relate to.
            type: complex
            contains:
                id:
                    description:
                        - Resource ID
                    returned: always
                    type: str
                    sample: "/subscriptions/ffffffff-ffff-ffff-ffff-ffffffffffff/resourceGroups/TestGroup/providers/Microsoft.DBforPostgreSQL/servers/testser
                            ver/configurations/array_nulls"
                name:
                    description:
                        - Resource name.
                    returned: always
                    type: str
                    sample: array_nulls
                type:
                    description:
                        - Resource type.
                    returned: always
                    type: str
                    sample: Microsoft.DBforPostgreSQL/servers/configurations
                value:
                    description:
                        - Value of the configuration.
                    returned: always
                    type: str
                    sample: on
                description:
                    description:
                        - Description of the configuration.
                    returned: always
                    type: str
                    sample: Enable input of NULL elements in arrays.
                source:
                    description:
                        - Source of the configuration.
                    returned: always
                    type: str
                    sample: system-default
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


class AzureRMConfigurationsFacts(AzureRMModuleBase):
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
            configuration_name=dict(
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
        self.configuration_name = None
        super(AzureRMConfigurationsFacts, self).__init__(self.module_arg_spec)

    def exec_module(self, **kwargs):
        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])
        self.mgmt_client = self.get_mgmt_svc_client(PostgreSQLManagementClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        if (self.resource_group is not None and
                self.server_name is not None and
                self.configuration_name is not None):
            self.results['configurations'] = self.get()
        elif (self.resource_group is not None and
              self.server_name is not None):
            self.results['configurations'] = self.list_by_server()
        return self.results

    def get(self):
        '''
        Gets facts of the specified PostgreSQL Configuration.

        :return: deserialized PostgreSQL Configurationinstance state dictionary
        '''
        response = None
        results = {}
        try:
            response = self.mgmt_client.configurations.get(resource_group_name=self.resource_group,
                                                           server_name=self.server_name,
                                                           configuration_name=self.configuration_name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for Configurations.')

        if response is not None:
            results[response.name] = response.as_dict()

        return results

    def list_by_server(self):
        '''
        Gets facts of the specified PostgreSQL Configuration.

        :return: deserialized PostgreSQL Configurationinstance state dictionary
        '''
        response = None
        results = {}
        try:
            response = self.mgmt_client.configurations.list_by_server(resource_group_name=self.resource_group,
                                                                      server_name=self.server_name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for Configurations.')

        if response is not None:
            for item in response:
                results[item.name] = item.as_dict()

        return results


def main():
    AzureRMConfigurationsFacts()
if __name__ == '__main__':
    main()
