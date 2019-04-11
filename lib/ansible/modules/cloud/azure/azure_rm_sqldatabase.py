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
module: azure_rm_sqldatabase
version_added: "2.5"
short_description: Manage SQL Database instance.
description:
    - Create, update and delete instance of SQL Database.

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
            - The name of the database to be operated on (updated or created).
        required: True
    location:
        description:
            - Resource location. If not set, location from the resource group will be used as C(default).
    collation:
        description:
            - The collation of the database. If I(create_mode) is not C(default), this value is ignored.
    create_mode:
        description:
            - Specifies the mode of database creation.
            - "C(default): regular database creation."
            - "C(copy): creates a database as a copy of an existing database."
            - "C(online_secondary)/C(non_readable_secondary): creates a database as a (readable or nonreadable) secondary replica of an existing database."
            - "C(point_in_time_restore): Creates a database by restoring a point in time backup of an existing database."
            - "C(recovery): Creates a database by restoring a geo-replicated backup."
            - "C(restore): Creates a database by restoring a backup of a deleted database."
            - "C(restore_long_term_retention_backup): Creates a database by restoring from a long term retention vault."
            - "C(copy), C(non_readable_secondary), C(online_secondary) and C(restore_long_term_retention_backup) are not supported for C(data_warehouse)
               edition."
        choices:
            - 'copy'
            - 'default'
            - 'non_readable_secondary'
            - 'online_secondary'
            - 'point_in_time_restore'
            - 'recovery'
            - 'restore'
            - 'restore_long_term_retention_backup'
    source_database_id:
        description:
            - Required unless I(create_mode) is C(default) or C(restore_long_term_retention_backup).
            - Specifies the resource ID of the source database
    source_database_deletion_date:
        description:
            - "Required if I(create_mode) is C(restore) and I(source_database_id) is the deleted database's original resource id when it existed (as
               opposed to its current restorable dropped database id), then this value is required. Specifies the time that the database was deleted."
    restore_point_in_time:
        description:
            - "Required if I(create_mode) is C(point_in_time_restore), this value is required. If I(create_mode) is C(restore), this value is optional.
               Specifies the point in time (ISO8601 format) of the source database that will be restored to create the new database. Must be greater than
               or equal to the source database's earliestRestoreDate value."
    recovery_services_recovery_point_resource_id:
        description:
            - "Required if I(create_mode) is C(restore_long_term_retention_backup), then this value is required. Specifies the resource ID of the
               recovery point to restore from."
    edition:
        description:
            - "The edition of the database. The DatabaseEditions enumeration contains all the valid editions. If I(create_mode) is C(non_readable_secondary)
              or C(online_secondary), this value is ignored. To see possible values, query the capabilities API
               (/subscriptions/{subscriptionId}/providers/Microsoft.Sql/locations/{locationID}/capabilities) referred to by operationId:
               'Capabilities_ListByLocation.'."
        choices:
            - 'web'
            - 'business'
            - 'basic'
            - 'standard'
            - 'premium'
            - 'free'
            - 'stretch'
            - 'data_warehouse'
            - 'system'
            - 'system2'
    max_size_bytes:
        description:
            - "The max size of the database expressed in bytes. If I(create_mode) is not C(default), this value is ignored. To see possible values, query the
               capabilities API (/subscriptions/{subscriptionId}/providers/Microsoft.Sql/locations/{locationID}/capabilities) referred to by operationId:
               'Capabilities_ListByLocation.'"
    elastic_pool_name:
        description:
            - "The name of the elastic pool the database is in. Not supported for C(data_warehouse) edition."
    read_scale:
        description:
            - "If the database is a geo-secondary, indicates whether read-only connections are allowed to this database or not. Not supported for
               C(data_warehouse) edition."
        type: bool
        default: False
    sample_name:
        description:
            - "Indicates the name of the sample schema to apply when creating this database. If I(create_mode) is not C(default), this value is ignored. Not
               supported for C(data_warehouse) edition."
        choices:
            - 'adventure_works_lt'
    zone_redundant:
        description:
            - Is this database is zone redundant? It means the replicas of this database will be spread across multiple availability zones.
        type: bool
        default: False
    force_update:
      description:
          - SQL Database will be updated if given parameters differ from existing resource state.
          - To force SQL Database update in any circumstances set this parameter to True.
      type: bool
    state:
      description:
        - Assert the state of the SQL Database. Use C(present) to create or update an SQL Database and C(absent) to delete it.
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
  - name: Create (or update) SQL Database
    azure_rm_sqldatabase:
      resource_group: myResourceGroup
      server_name: sqlcrudtest-5961
      name: testdb
      location: eastus

  - name: Restore SQL Database
    azure_rm_sqldatabase:
      resource_group: myResourceGroup
      server_name: sqlcrudtest-5961
      name: restoreddb
      location: eastus
      create_mode: restore
      restorable_dropped_database_id: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Sql/s
                                       ervers/testsvr/restorableDroppedDatabases/testdb2,131444841315030000"

  - name: Create SQL Database in Copy Mode
    azure_rm_sqldatabase:
      resource_group: myResourceGroup
      server_name: sqlcrudtest-5961
      name: copydb
      location: eastus
      create_mode: copy
      source_database_id: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Sql/servers/tests
                           vr/databases/testdb"

'''

RETURN = '''
id:
    description:
        - Resource ID.
    returned: always
    type: str
    sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Sql/servers/sqlcrudtest-5961/databases/t
            estdb"
database_id:
    description:
        - The ID of the database.
    returned: always
    type: str
    sample: database_id
status:
    description:
        - The status of the database.
    returned: always
    type: str
    sample: Online
'''

import time
from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from msrest.polling import LROPoller
    from azure.mgmt.sql import SqlManagementClient
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass


class Actions:
    NoAction, Create, Update, Delete = range(4)


class AzureRMSqlDatabase(AzureRMModuleBase):
    """Configuration class for an Azure RM SQL Database resource"""

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
            location=dict(
                type='str'
            ),
            collation=dict(
                type='str'
            ),
            create_mode=dict(
                type='str',
                choices=['copy',
                         'default',
                         'non_readable_secondary',
                         'online_secondary',
                         'point_in_time_restore',
                         'recovery',
                         'restore',
                         'restore_long_term_retention_backup']
            ),
            source_database_id=dict(
                type='str'
            ),
            source_database_deletion_date=dict(
                type='datetime'
            ),
            restore_point_in_time=dict(
                type='datetime'
            ),
            recovery_services_recovery_point_resource_id=dict(
                type='str'
            ),
            edition=dict(
                type='str',
                choices=['web',
                         'business',
                         'basic',
                         'standard',
                         'premium',
                         'free',
                         'stretch',
                         'data_warehouse',
                         'system',
                         'system2']
            ),
            max_size_bytes=dict(
                type='str'
            ),
            elastic_pool_name=dict(
                type='str'
            ),
            read_scale=dict(
                type='bool',
                default=False
            ),
            sample_name=dict(
                type='str',
                choices=['adventure_works_lt']
            ),
            zone_redundant=dict(
                type='bool',
                default=False
            ),
            force_update=dict(
                type='bool'
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
        self.tags = None

        self.results = dict(changed=False)
        self.state = None
        self.to_do = Actions.NoAction

        super(AzureRMSqlDatabase, self).__init__(derived_arg_spec=self.module_arg_spec,
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
                elif key == "collation":
                    self.parameters["collation"] = kwargs[key]
                elif key == "create_mode":
                    self.parameters["create_mode"] = _snake_to_camel(kwargs[key], True)
                elif key == "source_database_id":
                    self.parameters["source_database_id"] = kwargs[key]
                elif key == "source_database_deletion_date":
                    self.parameters["source_database_deletion_date"] = kwargs[key]
                elif key == "restore_point_in_time":
                    self.parameters["restore_point_in_time"] = kwargs[key]
                elif key == "recovery_services_recovery_point_resource_id":
                    self.parameters["recovery_services_recovery_point_resource_id"] = kwargs[key]
                elif key == "edition":
                    self.parameters["edition"] = _snake_to_camel(kwargs[key], True)
                elif key == "max_size_bytes":
                    self.parameters["max_size_bytes"] = kwargs[key]
                elif key == "elastic_pool_name":
                    self.parameters["elastic_pool_name"] = kwargs[key]
                elif key == "read_scale":
                    self.parameters["read_scale"] = 'Enabled' if kwargs[key] else 'Disabled'
                elif key == "sample_name":
                    ev = kwargs[key]
                    if ev == 'adventure_works_lt':
                        ev = 'AdventureWorksLT'
                    self.parameters["sample_name"] = ev
                elif key == "zone_redundant":
                    self.parameters["zone_redundant"] = True if kwargs[key] else False

        old_response = None
        response = None

        resource_group = self.get_resource_group(self.resource_group)

        if "location" not in self.parameters:
            self.parameters["location"] = resource_group.location

        old_response = self.get_sqldatabase()

        if not old_response:
            self.log("SQL Database instance doesn't exist")
            if self.state == 'absent':
                self.log("Old instance didn't exist")
            else:
                self.to_do = Actions.Create
        else:
            self.log("SQL Database instance already exists")
            if self.state == 'absent':
                self.to_do = Actions.Delete
            elif self.state == 'present':
                self.log("Need to check if SQL Database instance has to be deleted or may be updated")
                if ('location' in self.parameters) and (self.parameters['location'] != old_response['location']):
                    self.to_do = Actions.Update
                if (('read_scale' in self.parameters) and
                        (self.parameters['read_scale'] != old_response['read_scale'])):
                    self.to_do = Actions.Update
                if (('max_size_bytes' in self.parameters) and
                        (self.parameters['max_size_bytes'] != old_response['max_size_bytes'])):
                    self.to_do = Actions.Update
                if (('edition' in self.parameters) and
                        (self.parameters['edition'] != old_response['edition'])):
                    self.to_do = Actions.Update
                update_tags, newtags = self.update_tags(old_response.get('tags', dict()))
                if update_tags:
                    self.tags = newtags

        if (self.to_do == Actions.Create) or (self.to_do == Actions.Update):
            self.log("Need to Create / Update the SQL Database instance")

            if self.check_mode:
                self.results['changed'] = True
                return self.results

            self.parameters['tags'] = self.tags
            response = self.create_update_sqldatabase()

            if not old_response:
                self.results['changed'] = True
            else:
                self.results['changed'] = old_response.__ne__(response)
            self.log("Creation / Update done")
        elif self.to_do == Actions.Delete:
            self.log("SQL Database instance deleted")
            self.results['changed'] = True

            if self.check_mode:
                return self.results

            self.delete_sqldatabase()
            # make sure instance is actually deleted, for some Azure resources, instance is hanging around
            # for some time after deletion -- this should be really fixed in Azure
            while self.get_sqldatabase():
                time.sleep(20)
        else:
            self.log("SQL Database instance unchanged")
            self.results['changed'] = False
            response = old_response

        if response:
            self.results["id"] = response["id"]
            self.results["database_id"] = response["database_id"]
            self.results["status"] = response["status"]

        return self.results

    def create_update_sqldatabase(self):
        '''
        Creates or updates SQL Database with the specified configuration.

        :return: deserialized SQL Database instance state dictionary
        '''
        self.log("Creating / Updating the SQL Database instance {0}".format(self.name))

        try:
            response = self.sql_client.databases.create_or_update(resource_group_name=self.resource_group,
                                                                  server_name=self.server_name,
                                                                  database_name=self.name,
                                                                  parameters=self.parameters)
            if isinstance(response, LROPoller):
                response = self.get_poller_result(response)

        except CloudError as exc:
            self.log('Error attempting to create the SQL Database instance.')
            self.fail("Error creating the SQL Database instance: {0}".format(str(exc)))
        return response.as_dict()

    def delete_sqldatabase(self):
        '''
        Deletes specified SQL Database instance in the specified subscription and resource group.

        :return: True
        '''
        self.log("Deleting the SQL Database instance {0}".format(self.name))
        try:
            response = self.sql_client.databases.delete(resource_group_name=self.resource_group,
                                                        server_name=self.server_name,
                                                        database_name=self.name)
        except CloudError as e:
            self.log('Error attempting to delete the SQL Database instance.')
            self.fail("Error deleting the SQL Database instance: {0}".format(str(e)))

        return True

    def get_sqldatabase(self):
        '''
        Gets the properties of the specified SQL Database.

        :return: deserialized SQL Database instance state dictionary
        '''
        self.log("Checking if the SQL Database instance {0} is present".format(self.name))
        found = False
        try:
            response = self.sql_client.databases.get(resource_group_name=self.resource_group,
                                                     server_name=self.server_name,
                                                     database_name=self.name)
            found = True
            self.log("Response : {0}".format(response))
            self.log("SQL Database instance : {0} found".format(response.name))
        except CloudError as e:
            self.log('Did not find the SQL Database instance.')
        if found is True:
            return response.as_dict()

        return False


def _snake_to_camel(snake, capitalize_first=False):
    if capitalize_first:
        return ''.join(x.capitalize() or '_' for x in snake.split('_'))
    else:
        return snake.split('_')[0] + ''.join(x.capitalize() or '_' for x in snake.split('_')[1:])


def main():
    """Main execution"""
    AzureRMSqlDatabase()


if __name__ == '__main__':
    main()
