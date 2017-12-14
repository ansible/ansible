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
module: azure_rm_mysqlserver
version_added: "2.5"
short_description: Manage MySQL Server instance
description:
    - Create, update and delete instance of MySQL Server

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
    location:
        description:
            - The location the resource resides in.
    storage_mb:
        description:
            - The maximum storage allowed for a server.
    version:
        description:
            - "Server version. Possible values include: '5.6', '5.7'"
    ssl_enforcement:
        description:
            - "Enable ssl enforcement or not when connect to server. Possible values include: 'Enabled', 'Disabled'"
    create_mode:
        description:
            - "Currently only 'Default' value supported"
    admin_username:
        description:
            - "The administrator's login name of a server. Can only be specified when the server is being created (and is required for creation)."
    admin_password:
        description:
            - The password of the administrator login.

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Zim Kalinowski (@zikalino)"

'''

EXAMPLES = '''
  - name: Create (or update) MySQL Server
    azure_rm_mysqlserver:
      resource_group: resource_group_name
      name: server_name
      sku:
        name: name
        tier: tier
        capacity: capacity
        size: size
        family: family
      location: location
      storage_mb: storage_mb
      version: version
      ssl_enforcement: ssl_enforcement
      create_mode: create_mode
      admin_username: administrator_login
      admin_password: administrator_login_password
'''

RETURN = '''
id:
    description:
        - Resource ID
    returned: always
    type: str
    sample: id
version:
    description:
        - "Server version. Possible values include: '5.6', '5.7'"
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

import time
from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from msrestazure.azure_operation import AzureOperationPoller
    from azure.mgmt.rdbms.mysql import MySQLManagementClient
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass


class Actions:
    NoAction, Create, Update, Delete = range(4)


class AzureRMServers(AzureRMModuleBase):
    """Configuration class for an Azure RM MySQL Server resource"""

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
            location=dict(
                type='str',
                required=False
            ),
            storage_mb=dict(
                type='long',
                required=False
            ),
            version=dict(
                type='str',
                required=False
            ),
            ssl_enforcement=dict(
                type='str',
                required=False
            ),
            create_mode=dict(
                type='str',
                default='Default'
            ),
            admin_username=dict(
                type='str',
                required=False
            ),
            admin_password=dict(
                type='str',
                no_log=True,
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

        self.results = dict(changed=False)
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
            elif kwargs[key] is not None:
                if key == "sku":
                    self.parameters["sku"] = kwargs[key]
                elif key == "location":
                    self.parameters["location"] = kwargs[key]
                elif key == "storage_mb":
                    self.parameters.setdefault("properties", {})["storage_mb"] = kwargs[key]
                elif key == "version":
                    self.parameters.setdefault("properties", {})["version"] = kwargs[key]
                elif key == "ssl_enforcement":
                    self.parameters.setdefault("properties", {})["ssl_enforcement"] = kwargs[key]
                elif key == "create_mode":
                    self.parameters.setdefault("properties", {})["create_mode"] = kwargs[key]
                elif key == "admin_username":
                    self.parameters.setdefault("properties", {})["administrator_login"] = kwargs[key]
                elif key == "admin_password":
                    self.parameters.setdefault("properties", {})["administrator_login_password"] = kwargs[key]

        old_response = None
        response = None
        results = dict()

        self.mgmt_client = self.get_mgmt_svc_client(MySQLManagementClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        resource_group = self.get_resource_group(self.resource_group)

        if "location" not in self.parameters:
            self.parameters["location"] = resource_group.location

        old_response = self.get_mysqlserver()

        if not old_response:
            self.log("MySQL Server instance doesn't exist")
            if self.state == 'absent':
                self.log("Old instance didn't exist")
            else:
                self.to_do = Actions.Create
        else:
            self.log("MySQL Server instance already exists")
            if self.state == 'absent':
                self.to_do = Actions.Delete
            elif self.state == 'present':
                self.log("Need to check if MySQL Server instance has to be deleted or may be updated")
                self.to_do = Actions.Update

        if (self.to_do == Actions.Create) or (self.to_do == Actions.Update):
            self.log("Need to Create / Update the MySQL Server instance")

            if self.check_mode:
                self.results['changed'] = True
                return self.results

            response = self.create_update_mysqlserver()

            if not old_response:
                self.results['changed'] = True
            else:
                self.results['changed'] = old_response.__ne__(response)
            self.log("Creation / Update done")
        elif self.to_do == Actions.Delete:
            self.log("MySQL Server instance deleted")
            self.results['changed'] = True

            if self.check_mode:
                return self.results

            self.delete_mysqlserver()
            # make sure instance is actually deleted, for some Azure resources, instance is hanging around
            # for some time after deletion -- this should be really fixed in Azure
            while self.get_mysqlserver():
                time.sleep(20)
        else:
            self.log("MySQL Server instance unchanged")
            self.results['changed'] = False
            response = old_response

        if response:
            self.results["id"] = response["id"]
            self.results["version"] = response["version"]
            self.results["user_visible_state"] = response["user_visible_state"]
            self.results["fully_qualified_domain_name"] = response["fully_qualified_domain_name"]

        return self.results

    def create_update_mysqlserver(self):
        '''
        Creates or updates MySQL Server with the specified configuration.

        :return: deserialized MySQL Server instance state dictionary
        '''
        self.log("Creating / Updating the MySQL Server instance {0}".format(self.name))

        try:
            response = self.mgmt_client.servers.create_or_update(self.resource_group,
                                                                 self.name,
                                                                 self.parameters)
            if isinstance(response, AzureOperationPoller):
                response = self.get_poller_result(response)

        except CloudError as exc:
            self.log('Error attempting to create the MySQL Server instance.')
            self.fail("Error creating the MySQL Server instance: {0}".format(str(exc)))
        return response.as_dict()

    def delete_mysqlserver(self):
        '''
        Deletes specified MySQL Server instance in the specified subscription and resource group.

        :return: True
        '''
        self.log("Deleting the MySQL Server instance {0}".format(self.name))
        try:
            response = self.mgmt_client.servers.delete(self.resource_group,
                                                       self.name)
        except CloudError as e:
            self.log('Error attempting to delete the MySQL Server instance.')
            self.fail("Error deleting the MySQL Server instance: {0}".format(str(e)))

        return True

    def get_mysqlserver(self):
        '''
        Gets the properties of the specified MySQL Server.

        :return: deserialized MySQL Server instance state dictionary
        '''
        self.log("Checking if the MySQL Server instance {0} is present".format(self.name))
        found = False
        try:
            response = self.mgmt_client.servers.get(self.resource_group,
                                                    self.name)
            found = True
            self.log("Response : {0}".format(response))
            self.log("MySQL Server instance : {0} found".format(response.name))
        except CloudError as e:
            self.log('Did not find the MySQL Server instance.')
        if found is True:
            return response.as_dict()

        return False


def main():
    """Main execution"""
    AzureRMServers()

if __name__ == '__main__':
    main()
