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
module: azure_rm_mysqldatabase
version_added: "2.5"
short_description: Manage MySQL Database instance.
description:
    - Create, update and delete instance of MySQL Database.

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
        required: True
    charset:
        description:
            - The charset of the database. Check MySQL documentation for possible values.
            - This is only set on creation, use I(force_update) to recreate a database if the
              values don't match.
    collation:
        description:
            - The collation of the database. Check MySQL documentation for possible values.
            - This is only set on creation, use I(force_update) to recreate a database if the
              values don't match.
    force_update:
      description:
          - When set to C(true), will delete and recreate the existing MySQL database if any
            of the properties don't match what is set.
          - When set to C(false), no change will occur to the database even if any
            of the properties do not match.
      type: bool
      default: 'no'
    state:
        description:
            - Assert the state of the MySQL Database. Use 'present' to create or update a database and 'absent' to delete it.
        default: present
        choices:
            - absent
            - present
        version_added: 2.6

extends_documentation_fragment:
    - azure

author:
    - "Zim Kalinowski (@zikalino)"

'''

EXAMPLES = '''
  - name: Create (or update) MySQL Database
    azure_rm_mysqldatabase:
      resource_group: TestGroup
      server_name: testserver
      name: db1
'''

RETURN = '''
id:
    description:
        - Resource ID
    returned: always
    type: str
    sample: /subscriptions/ffffffff-ffff-ffff-ffff-ffffffffffff/resourceGroups/TestGroup/providers/Microsoft.DBforMySQL/servers/testserver/databases/db1
name:
    description:
        - Resource name.
    returned: always
    type: str
    sample: db1
'''

import time
from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from azure.mgmt.rdbms.mysql import MySQLManagementClient
    from msrestazure.azure_exceptions import CloudError
    from msrest.polling import LROPoller
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass


class Actions:
    NoAction, Create, Update, Delete = range(4)


class AzureRMDatabases(AzureRMModuleBase):
    """Configuration class for an Azure RM MySQL Database resource"""

    def __init__(self):
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
                type='str',
                required=True
            ),
            charset=dict(
                type='str'
            ),
            collation=dict(
                type='str'
            ),
            force_update=dict(
                type='bool',
                default=False
            ),
            state=dict(
                type='str',
                default='present',
                choices=['present', 'absent']
            )
        )

        self.resource_group = None
        self.server_name = None
        self.name = None
        self.parameters = dict()

        self.results = dict(changed=False)
        self.mgmt_client = None
        self.state = None
        self.to_do = Actions.NoAction

        super(AzureRMDatabases, self).__init__(derived_arg_spec=self.module_arg_spec,
                                               supports_check_mode=True,
                                               supports_tags=False)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        for key in list(self.module_arg_spec.keys()):
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
            elif kwargs[key] is not None:
                if key == "charset":
                    self.parameters["charset"] = kwargs[key]
                elif key == "collation":
                    self.parameters["collation"] = kwargs[key]

        old_response = None
        response = None

        self.mgmt_client = self.get_mgmt_svc_client(MySQLManagementClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        resource_group = self.get_resource_group(self.resource_group)

        old_response = self.get_mysqldatabase()

        if not old_response:
            self.log("MySQL Database instance doesn't exist")
            if self.state == 'absent':
                self.log("Old instance didn't exist")
            else:
                self.to_do = Actions.Create
        else:
            self.log("MySQL Database instance already exists")
            if self.state == 'absent':
                self.to_do = Actions.Delete
            elif self.state == 'present':
                self.log("Need to check if MySQL Database instance has to be deleted or may be updated")
                if ('collation' in self.parameters) and (self.parameters['collation'] != old_response['collation']):
                    self.to_do = Actions.Update
                if ('charset' in self.parameters) and (self.parameters['charset'] != old_response['charset']):
                    self.to_do = Actions.Update
        if self.to_do == Actions.Update:
            if self.force_update:
                if not self.check_mode:
                    self.delete_mysqldatabase()
            else:
                self.to_do = Actions.NoAction

        if (self.to_do == Actions.Create) or (self.to_do == Actions.Update):
            self.log("Need to Create / Update the MySQL Database instance")

            if self.check_mode:
                self.results['changed'] = True
                return self.results

            response = self.create_update_mysqldatabase()
            self.results['changed'] = True
            self.log("Creation / Update done")
        elif self.to_do == Actions.Delete:
            self.log("MySQL Database instance deleted")
            self.results['changed'] = True

            if self.check_mode:
                return self.results

            self.delete_mysqldatabase()
            # make sure instance is actually deleted, for some Azure resources, instance is hanging around
            # for some time after deletion -- this should be really fixed in Azure
            while self.get_mysqldatabase():
                time.sleep(20)
        else:
            self.log("MySQL Database instance unchanged")
            self.results['changed'] = False
            response = old_response

        if response:
            self.results["id"] = response["id"]
            self.results["name"] = response["name"]

        return self.results

    def create_update_mysqldatabase(self):
        '''
        Creates or updates MySQL Database with the specified configuration.

        :return: deserialized MySQL Database instance state dictionary
        '''
        self.log("Creating / Updating the MySQL Database instance {0}".format(self.name))

        try:
            response = self.mgmt_client.databases.create_or_update(resource_group_name=self.resource_group,
                                                                   server_name=self.server_name,
                                                                   database_name=self.name,
                                                                   parameters=self.parameters)
            if isinstance(response, LROPoller):
                response = self.get_poller_result(response)

        except CloudError as exc:
            self.log('Error attempting to create the MySQL Database instance.')
            self.fail("Error creating the MySQL Database instance: {0}".format(str(exc)))
        return response.as_dict()

    def delete_mysqldatabase(self):
        '''
        Deletes specified MySQL Database instance in the specified subscription and resource group.

        :return: True
        '''
        self.log("Deleting the MySQL Database instance {0}".format(self.name))
        try:
            response = self.mgmt_client.databases.delete(resource_group_name=self.resource_group,
                                                         server_name=self.server_name,
                                                         database_name=self.name)
        except CloudError as e:
            self.log('Error attempting to delete the MySQL Database instance.')
            self.fail("Error deleting the MySQL Database instance: {0}".format(str(e)))

        return True

    def get_mysqldatabase(self):
        '''
        Gets the properties of the specified MySQL Database.

        :return: deserialized MySQL Database instance state dictionary
        '''
        self.log("Checking if the MySQL Database instance {0} is present".format(self.name))
        found = False
        try:
            response = self.mgmt_client.databases.get(resource_group_name=self.resource_group,
                                                      server_name=self.server_name,
                                                      database_name=self.name)
            found = True
            self.log("Response : {0}".format(response))
            self.log("MySQL Database instance : {0} found".format(response.name))
        except CloudError as e:
            self.log('Did not find the MySQL Database instance.')
        if found is True:
            return response.as_dict()

        return False


def main():
    """Main execution"""
    AzureRMDatabases()

if __name__ == '__main__':
    main()
