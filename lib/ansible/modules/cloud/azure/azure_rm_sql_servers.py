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
module: azure_rm_sql_servers
version_added: "2.5"
short_description: Manage an Server.
description:
    - Create, update and delete an instance of Server.

options:
    resource_group:
        description:
            - The name of the resource group that contains the resource. You can obtain this value from the Azure Resource Manager API or the portal.
        required: True
    name:
        description:
            - The name of the server.
        required: True
    location:
        description:
            - Resource location.
        required: True
    tags:
        description:
            - Resource tags.
        required: False
    identity:
        description:
            - The Azure Active Directory identity of the server.
        required: False
        suboptions:
            type:
                description:
                    - The identity type. Set this to 'SystemAssigned' in order to automatically create and assign an Azure Active Directory principal for the resource. Possible values include: 'SystemAssigned'
                required: False
    administrator_login:
        description:
            - Administrator username for the server. Once created it cannot be changed.
        required: False
    administrator_login_password:
        description:
            - The administrator login password (required for server creation).
        required: False
    version:
        description:
            - The version of the server.
        required: False

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Zim Kalinowski (@zikalino)"

'''

EXAMPLES = '''
      - name: Create (or update) Servers
        azure_rm_sql_servers:
          resource_group: "{{ resource_group }}"
          name: zims-server
          location: westus
          tags: "{{ tags }}"
          identity:
            type: "{{ type }}"
          administrator_login: mylogin
          administrator_login_password: Testpasswordxyz12!
          version: "{{ version }}"
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


class AzureRMServers(AzureRMModuleBase):
    """Configuration class for an Azure RM Server resource"""

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
                type='str',
                required=True
            ),
            tags=dict(
                type='dict',
                required=False
            ),
            identity=dict(
                type='dict',
                required=False
            ),
            administrator_login=dict(
                type='str',
                required=False
            ),
            administrator_login_password=dict(
                type='str',
                required=False
            ),
            version=dict(
                type='str',
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

        super(AzureRMServers, self).__init__(derived_arg_spec=self.module_arg_spec,
                                             supports_check_mode=True,
                                             supports_tags=True)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
            elif key == "location":
                self.parameters["location"] = kwargs[key]
            elif key == "tags":
                self.parameters["tags"] = kwargs[key]
            elif key == "identity":
                self.parameters["identity"] = kwargs[key]
            elif key == "administrator_login":
                self.parameters["administrator_login"] = kwargs[key]
            elif key == "administrator_login_password":
                self.parameters["administrator_login_password"] = kwargs[key]
            elif key == "version":
                self.parameters["version"] = kwargs[key]

        response = None
        results = dict()
        to_be_updated = False

        self.mgmt_client = self.get_mgmt_svc_client(SqlManagementClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        try:
            resource_group = self.get_resource_group(self.resource_group)
        except CloudError:
            self.fail('resource group {0} not found'.format(self.resource_group))

        response = self.get_servers()

        if not response:
            self.log("Server instance doesn't exist")
            if self.state == 'absent':
                self.log("Nothing to delete")
            else:
                to_be_updated = True
        else:
            self.log("Server instance already exists")
            if self.state == 'absent':
                self.delete_servers()
                self.results['changed'] = True
                self.log("Server instance deleted")
            elif self.state == 'present':
                self.log("Need to check if Server instance has to be deleted or may be updated")
                to_be_updated = True

        if self.state == 'present':

            self.log("Need to Create / Update the Server instance")

            if self.check_mode:
                return self.results

            if to_be_updated:
                self.results['state'] = self.create_update_servers()
                self.results['changed'] = True
            else:
                self.results['state'] = response

            self.log("Creation / Update done")

        return self.results

    def create_update_servers(self):
        '''
        Creates or updates Server with the specified configuration.

        :return: deserialized Server instance state dictionary
        '''
        self.log("Creating / Updating the Server instance {0}".format(self.name))

        try:
            response = self.mgmt_client.servers.create_or_update(self.resource_group,
                                                                 self.name,
                                                                 self.parameters)
            if isinstance(response, AzureOperationPoller):
                response = self.get_poller_result(response)

        except CloudError as exc:
            self.log('Error attempting to create the Server instance.')
            self.fail("Error creating the Server instance: {0}".format(str(exc)))
        return response.as_dict()

    def delete_servers(self):
        '''
        Deletes specified Server instance in the specified subscription and resource group.

        :return: True
        '''
        self.log("Deleting the Server instance {0}".format(self.name))
        try:
            response = self.mgmt_client.servers.delete(self.resource_group,
                                                       self.name)
        except CloudError as e:
            self.log('Error attempting to delete the Server instance.')
            self.fail("Error deleting the Server instance: {0}".format(str(e)))

        return True

    def get_servers(self):
        '''
        Gets the properties of the specified Server.

        :return: deserialized Server instance state dictionary
        '''
        self.log("Checking if the Server instance {0} is present".format(self.name))
        found = False
        try:
            response = self.mgmt_client.servers.get(self.resource_group,
                                                    self.name)
            found = True
            self.log("Response : {0}".format(response))
            self.log("Server instance : {0} found".format(response.name))
        except CloudError as e:
            self.log('Did not find the Server instance.')
        if found is True:
            return response.as_dict()

        return False


def main():
    """Main execution"""
    AzureRMServers()

if __name__ == '__main__':
    main()
