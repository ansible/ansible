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
module: azure_rm_sqlelasticpool
version_added: "2.8"
short_description: Manage SQL Elastic Pool instance.
description:
    - Create, update and delete instance of SQL Elastic Pool.

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
            - The name of the elastic pool to be operated on (updated or created).
        required: True
    location:
        description:
            - Resource location. If not set, location from the resource group will be used as default.
    edition:
        description:
            - The edition of the elastic pool.
        choices:
            - 'basic'
            - 'standard'
            - 'premium'
    dtu:
        description:
            - The total shared DTU for the database elastic pool.
    database_dtu_max:
        description:
            - The maximum I(dtu) any one database can consume.
    database_dtu_min:
        description:
            - The minimum I(dtu) all databases are guaranteed.
    storage_mb:
        description:
            - Gets storage limit for the database elastic pool in MB.
    zone_redundant:
        description:
            - "Whether or not this database elastic pool is zone redundant, which means the replicas of this database will be spread across multiple
               availability zones."
    state:
      description:
        - Assert the state of the SQL Elastic Pool.
        - Use 'present' to create or update an SQL Elastic Pool and 'absent' to delete it.
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
  - name: Create (or update) SQL Elastic Pool
    azure_rm_sqlelasticpool:
      resource_group: sqlcrudtest-2369
      server_name: sqlcrudtest-8069
      name: sqlcrudtest-8102
      location: eastus
'''

RETURN = '''
id:
    description:
        - Resource ID.
    returned: always
    type: str
    sample: "/subscriptions/00000000-1111-2222-3333-444444444444/resourceGroups/sqlcrudtest-2369/providers/Microsoft.Sql/servers/sqlcrudtest-8069/elasticPool
            s/sqlcrudtest-8102"
state:
    description:
        - "The state of the elastic pool. Possible values include: 'Creating', 'Ready', 'Disabled'"
    returned: always
    type: str
    sample: Ready
'''

import time
from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from msrestazure.azure_operation import AzureOperationPoller
    from azure.mgmt.sql import SqlManagementClient
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass


class Actions:
    NoAction, Create, Update, Delete = range(4)


class AzureRMElasticPools(AzureRMModuleBase):
    """Configuration class for an Azure RM SQL Elastic Pool resource"""

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
            edition=dict(
                type='str',
                choices=['basic',
                         'standard',
                         'premium']
            ),
            dtu=dict(
                type='int'
            ),
            database_dtu_max=dict(
                type='int'
            ),
            database_dtu_min=dict(
                type='int'
            ),
            storage_mb=dict(
                type='int'
            ),
            zone_redundant=dict(
                type='str'
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

        super(AzureRMElasticPools, self).__init__(derived_arg_spec=self.module_arg_spec,
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
                elif key == "edition":
                    self.parameters["edition"] = _snake_to_camel(kwargs[key], True)
                elif key == "dtu":
                    self.parameters["dtu"] = kwargs[key]
                elif key == "database_dtu_max":
                    self.parameters["database_dtu_max"] = kwargs[key]
                elif key == "database_dtu_min":
                    self.parameters["database_dtu_min"] = kwargs[key]
                elif key == "storage_mb":
                    self.parameters["storage_mb"] = kwargs[key]
                elif key == "zone_redundant":
                    self.parameters["zone_redundant"] = kwargs[key]

        old_response = None
        response = None

        self.mgmt_client = self.get_mgmt_svc_client(SqlManagementClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        resource_group = self.get_resource_group(self.resource_group)

        if "location" not in self.parameters:
            self.parameters["location"] = resource_group.location

        old_response = self.get_sqlelasticpool()

        if not old_response:
            self.log("SQL Elastic Pool instance doesn't exist")
            if self.state == 'absent':
                self.log("Old instance didn't exist")
            else:
                self.to_do = Actions.Create
        else:
            self.log("SQL Elastic Pool instance already exists")
            if self.state == 'absent':
                self.to_do = Actions.Delete
            elif self.state == 'present':
                self.log("Need to check if SQL Elastic Pool instance has to be deleted or may be updated")
                if ('edition' in self.parameters) and (self.parameters['edition'] != old_response['edition']):
                    self.to_do = Actions.Update
                if ('dtu' in self.parameters) and (self.parameters['dtu'] != old_response['dtu']):
                    self.to_do = Actions.Update
                if ('database_dtu_max' in self.parameters) and (self.parameters['database_dtu_max'] != old_response['database_dtu_max']):
                    self.to_do = Actions.Update
                if ('database_dtu_min' in self.parameters) and (self.parameters['database_dtu_min'] != old_response['database_dtu_min']):
                    self.to_do = Actions.Update
                if ('storage_mb' in self.parameters) and (self.parameters['storage_mb'] != old_response['storage_mb']):
                    self.to_do = Actions.Update
                if ('zone_redundant' in self.parameters) and (self.parameters['zone_redundant'] != old_response['zone_redundant']):
                    self.to_do = Actions.Update

        if (self.to_do == Actions.Create) or (self.to_do == Actions.Update):
            self.log("Need to Create / Update the SQL Elastic Pool instance")

            if self.check_mode:
                self.results['changed'] = True
                return self.results

            response = self.create_update_sqlelasticpool()

            if not old_response:
                self.results['changed'] = True
            else:
                self.results['changed'] = old_response.__ne__(response)
            self.log("Creation / Update done")
        elif self.to_do == Actions.Delete:
            self.log("SQL Elastic Pool instance deleted")
            self.results['changed'] = True

            if self.check_mode:
                return self.results

            self.delete_sqlelasticpool()
            # make sure instance is actually deleted, for some Azure resources, instance is hanging around
            # for some time after deletion -- this should be really fixed in Azure.
            while self.get_sqlelasticpool():
                time.sleep(20)
        else:
            self.log("SQL Elastic Pool instance unchanged")
            self.results['changed'] = False
            response = old_response

        if self.state == 'present':
            self.results.update(self.format_item(response))
        return self.results

    def create_update_sqlelasticpool(self):
        '''
        Creates or updates SQL Elastic Pool with the specified configuration.

        :return: deserialized SQL Elastic Pool instance state dictionary
        '''
        self.log("Creating / Updating the SQL Elastic Pool instance {0}".format(self.name))

        try:
            response = self.mgmt_client.elastic_pools.create_or_update(resource_group_name=self.resource_group,
                                                                       server_name=self.server_name,
                                                                       elastic_pool_name=self.name,
                                                                       parameters=self.parameters)
            if isinstance(response, AzureOperationPoller):
                response = self.get_poller_result(response)

        except CloudError as exc:
            self.log('Error attempting to create the SQL Elastic Pool instance.')
            self.fail("Error creating the SQL Elastic Pool instance: {0}".format(str(exc)))
        return response.as_dict()

    def delete_sqlelasticpool(self):
        '''
        Deletes specified SQL Elastic Pool instance in the specified subscription and resource group.

        :return: True
        '''
        self.log("Deleting the SQL Elastic Pool instance {0}".format(self.name))
        try:
            response = self.mgmt_client.elastic_pools.delete(resource_group_name=self.resource_group,
                                                             server_name=self.server_name,
                                                             elastic_pool_name=self.name)
        except CloudError as e:
            self.log('Error attempting to delete the SQL Elastic Pool instance.')
            self.fail("Error deleting the SQL Elastic Pool instance: {0}".format(str(e)))

        return True

    def get_sqlelasticpool(self):
        '''
        Gets the properties of the specified SQL Elastic Pool.

        :return: deserialized SQL Elastic Pool instance state dictionary
        '''
        self.log("Checking if the SQL Elastic Pool instance {0} is present".format(self.name))
        found = False
        try:
            response = self.mgmt_client.elastic_pools.get(resource_group_name=self.resource_group,
                                                          server_name=self.server_name,
                                                          elastic_pool_name=self.name)
            found = True
            self.log("Response : {0}".format(response))
            self.log("SQL Elastic Pool instance : {0} found".format(response.name))
        except CloudError as e:
            self.log('Did not find the SQL Elastic Pool instance.')
        if found is True:
            return response.as_dict()

        return False

    def format_item(self, d):
        d = {
            'id': d['id'],
            'state': d['state']
        }
        return d


def _snake_to_camel(snake, capitalize_first=False):
    if capitalize_first:
        return ''.join(x.capitalize() or '_' for x in snake.split('_'))
    else:
        return snake.split('_')[0] + ''.join(x.capitalize() or '_' for x in snake.split('_')[1:])


def main():
    """Main execution"""
    AzureRMElasticPools()


if __name__ == '__main__':
    main()
