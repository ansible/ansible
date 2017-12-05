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
module: azure_rm_postgresqlserver
version_added: "2.5"
short_description: Manage PostgreSQL Server instance
description:
    - Create, update and delete instance of PostgreSQL Server

options:
    resource_group:
        description:
            - The name of the resource group that contains the resource. You can obtain this value from the Azure Resource Manager API or the portal.
        required: True
    name:
        description:
            - The name of the server.
        required: True
    sku:
        description:
            - The SKU (pricing tier) of the server.
        suboptions:
            name:
                description:
                    - The name of the sku, typically, a letter + Number code, e.g. P3.
            tier:
                description:
                    - "The tier of the particular SKU, e.g. Basic. Possible values include: 'Basic', 'Standard'"
            capacity:
                description:
                    - "The scale up/out capacity, representing server's compute units."
            size:
                description:
                    - The size code, to be interpreted by resource as appropriate.
            family:
                description:
                    - The family of hardware.
    properties:
        description:
            - Properties of the server.
        suboptions:
            storage_mb:
                description:
                    - The maximum storage allowed for a server.
            version:
                description:
                    - "Server version. Possible values include: '9.5', '9.6'"
            ssl_enforcement:
                description:
                    - "Enable ssl enforcement or not when connect to server. Possible values include: 'Enabled', 'Disabled'"
            create_mode:
                description:
                    - Constant filled by server.
                required: True
            admin_username:
                description:
                    - "The administrator's login name of a server. Can only be specified when the server is being created (and is required for creation)."
                required: True
            admin_password:
                description:
                    - The password of the administrator login.
                required: True
    location:
        description:
            - The location the resource resides in.
    tags:
        description:
            - Application-specific metadata in the form of key-value pairs.

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Zim Kalinowski (@zikalino)"

'''

EXAMPLES = '''
  - name: Create (or update) PostgreSQL Server
    azure_rm_postgresqlserver:
      resource_group: resource_group_name
      name: server_name
      sku:
        name: name
        tier: tier
        capacity: capacity
        size: size
        family: family
      properties:
        storage_mb: storage_mb
        version: version
        ssl_enforcement: ssl_enforcement
        create_mode: create_mode
        admin_username: administrator_login
        admin_password: administrator_login_password
      location: location
      tags: tags
'''

RETURN = '''
state:
    description: Current state of PostgreSQL Server
    returned: always
    type: complex
    contains:
        id:
            description:
                - Resource ID
            returned: always
            type: str
            sample: id
        version:
            description:
                - "Server version. Possible values include: '9.5', '9.6'"
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


class Actions:
    NoAction, Create, Update, Delete = range(4)


class AzureRMServers(AzureRMModuleBase):
    """Configuration class for an Azure RM PostgreSQL Server resource"""

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
            sku=dict(
                type='dict',
                required=False
            ),
            properties=dict(
                type='dict',
                required=False
            ),
            location=dict(
                type='str',
                required=False
            ),
            tags=dict(
                type='dict',
                required=False
            ),
            state=dict(
                type='str',
                required=False,
                default='present',
                choices=['present', 'absent']
            )
        )

        self.resource_group = None
        self.name = None
        self.parameters = dict()

        self.results = dict(changed=False, state=dict())
        self.mgmt_client = None
        self.state = None
        self.to_do = Actions.NoAction

        super(AzureRMServers, self).__init__(derived_arg_spec=self.module_arg_spec,
                                             supports_check_mode=True,
                                             supports_tags=True)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
            elif key == "sku":
                self.parameters["sku"] = kwargs[key]
            elif key == "properties":
                self.parameters["properties"] = kwargs[key]
            elif key == "location":
                self.parameters["location"] = kwargs[key]
            elif key == "tags":
                self.parameters["tags"] = kwargs[key]

        self.adjust_parameters()

        old_response = None
        results = dict()

        self.mgmt_client = self.get_mgmt_svc_client(PostgreSQLManagementClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        try:
            resource_group = self.get_resource_group(self.resource_group)
        except CloudError:
            self.fail('resource group {0} not found'.format(self.resource_group))

        if not ("location" in self.parameters):
            self.parameters["location"] = resource_group.location

        old_response = self.get_postgresqlserver()

        if not old_response:
            self.log("PostgreSQL Server instance doesn't exist")
            if self.state == 'absent':
                self.log("Old instance didn't exist")
            else:
                self.to_do = Actions.Create
        else:
            self.log("PostgreSQL Server instance already exists")
            if self.state == 'absent':
                self.to_do = Actions.Delete
            elif self.state == 'present':
                self.log("Need to check if PostgreSQL Server instance has to be deleted or may be updated")
                self.to_do = Actions.Update

        if (self.to_do == Actions.Create) or (self.to_do == Actions.Update):
            self.log("Need to Create / Update the PostgreSQL Server instance")

            if self.check_mode:
                return self.results

            self.results['state'] = self.create_update_postgresqlserver()
            if not old_response:
                self.results['changed'] = True
            else:
                self.results['changed'] = old_response.__ne__(self.results['state'])

            # remove unnecessary fields from return state
            self.results['state'].pop('name', None)
            self.results['state'].pop('type', None)
            self.results['state'].pop('location', None)
            self.results['state'].pop('tags', None)
            self.results['state'].pop('sku', None)
            self.results['state'].pop('administrator_login', None)
            self.results['state'].pop('storage_mb', None)
            self.results['state'].pop('ssl_enforcement', None)
            self.log("Creation / Update done")
        elif self.to_do == Actions.Delete:
            self.log("PostgreSQL Server instance deleted")
            self.delete_postgresqlserver()
            self.results['changed'] = True
        else:
            self.log("PostgreSQL Server instance unchanged")
            self.results['state'] = old_response
            self.results['changed'] = False

        return self.results

    def adjust_parameters(self):
        if self.parameters.get('properties', None) is not None:
            self.rename_key(self.parameters['properties'], 'admin_username', 'administrator_login')
            self.rename_key(self.parameters['properties'], 'admin_password', 'administrator_login_password')

    def rename_key(self, d, old_name, new_name):
        old_value = d.get(old_name, None)
        if old_value is not None:
            d.pop(old_name, None)
            d[new_name] = old_value;

    def create_update_postgresqlserver(self):
        '''
        Creates or updates PostgreSQL Server with the specified configuration.

        :return: deserialized PostgreSQL Server instance state dictionary
        '''
        self.log("Creating / Updating the PostgreSQL Server instance {0}".format(self.name))

        try:
            if self.to_do == Actions.Create:
                response = self.mgmt_client.servers.create(self.resource_group,
                                                           self.name,
                                                           self.parameters)
            else:
                response = self.mgmt_client.servers.update(self.resource_group,
                                                           self.name,
                                                           self.parameters)
            if isinstance(response, AzureOperationPoller):
                response = self.get_poller_result(response)

        except CloudError as exc:
            self.log('Error attempting to create the PostgreSQL Server instance.')
            self.fail("Error creating the PostgreSQL Server instance: {0}".format(str(exc)))
        return response.as_dict()

    def delete_postgresqlserver(self):
        '''
        Deletes specified PostgreSQL Server instance in the specified subscription and resource group.

        :return: True
        '''
        self.log("Deleting the PostgreSQL Server instance {0}".format(self.name))
        try:
            response = self.mgmt_client.servers.delete(self.resource_group,
                                                       self.name)
        except CloudError as e:
            self.log('Error attempting to delete the PostgreSQL Server instance.')
            self.fail("Error deleting the PostgreSQL Server instance: {0}".format(str(e)))

        return True

    def get_postgresqlserver(self):
        '''
        Gets the properties of the specified PostgreSQL Server.

        :return: deserialized PostgreSQL Server instance state dictionary
        '''
        self.log("Checking if the PostgreSQL Server instance {0} is present".format(self.name))
        found = False
        try:
            response = self.mgmt_client.servers.get(self.resource_group,
                                                    self.name)
            found = True
            self.log("Response : {0}".format(response))
            self.log("PostgreSQL Server instance : {0} found".format(response.name))
        except CloudError as e:
            self.log('Did not find the PostgreSQL Server instance.')
        if found is True:
            return response.as_dict()

        return False


def main():
    """Main execution"""
    AzureRMServers()

if __name__ == '__main__':
    main()
