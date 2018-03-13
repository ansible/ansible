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
module: azure_rm_sql_elasticpool
version_added: "2.5"
short_description: Manage an ElasticPools.
description:
    - Create, update and delete an instance of ElasticPools.

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
    tags:
        description:
            - Resource tags.
        required: False
    location:
        description:
            - Resource location.
        required: True
    edition:
        description:
            - "The edition of the elastic pool. Possible values include: 'Basic', 'Standard', 'Premium'"
        required: False
    dtu:
        description:
            - The total shared DTU for the database elastic pool.
        required: False
    database_dtu_max:
        description:
            - The maximum DTU any one database can consume.
        required: False
    database_dtu_min:
        description:
            - The minimum DTU all databases are guaranteed.
        required: False
    storage_mb:
        description:
            - Gets storage limit for the database elastic pool in MB.
        required: False
    zone_redundant:
        description:
            - "Whether or not this database elastic pool is zone redundant, which means the replicas of this database will be spread across multiple availabi
               lity zones."
        required: False

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Zim Kalinowski (@zikalino)"

'''

EXAMPLES = '''
      - name: Create (or update) Sql
        azure_rm_sql_elasticpool:
          resource_group: "{{ resource_group_name }}"
          server_name: zims-server
          name: test-elastic-pool
          tags: "{{ tags }}"
          location: westus
          edition: "{{ edition }}"
          dtu: "{{ dtu }}"
          database_dtu_max: "{{ database_dtu_max }}"
          database_dtu_min: "{{ database_dtu_min }}"
          storage_mb: "{{ storage_mb }}"
          zone_redundant: "{{ zone_redundant }}"
'''

RETURN = '''
state:
    description: Current state of ElasticPools
    returned: always
    type: dict
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


class AzureRMElasticPools(AzureRMModuleBase):
    """Configuration class for an Azure RM ElasticPools resource"""

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
            tags=dict(
                type='dict',
                required=False
            ),
            location=dict(
                type='str',
                required=True
            ),
            edition=dict(
                type='str',
                required=False
            ),
            dtu=dict(
                type='int',
                required=False
            ),
            database_dtu_max=dict(
                type='int',
                required=False
            ),
            database_dtu_min=dict(
                type='int',
                required=False
            ),
            storage_mb=dict(
                type='int',
                required=False
            ),
            zone_redundant=dict(
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
        self.server_name = None
        self.name = None
        self.parameters = dict()

        self.results = dict(changed=False, state=dict())
        self.mgmt_client = None
        self.state = None

        super(AzureRMElasticPools, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                  supports_check_mode=True,
                                                  supports_tags=True)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
            elif key == "tags":
                self.parameters["tags"] = kwargs[key]
            elif key == "location":
                self.parameters["location"] = kwargs[key]
            elif key == "edition":
                self.parameters["edition"] = kwargs[key]
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

        response = None
        results = dict()
        to_be_updated = False

        self.mgmt_client = self.get_mgmt_svc_client(SqlManagementClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        try:
            resource_group = self.get_resource_group(self.resource_group)
        except CloudError:
            self.fail('resource group {0} not found'.format(self.resource_group))

        response = self.get_sql()

        if not response:
            self.log("ElasticPools instance doesn't exist")
            if self.state == 'absent':
                self.log("Nothing to delete")
            else:
                to_be_updated = True
        else:
            self.log("ElasticPools instance already exists")
            if self.state == 'absent':
                self.delete_sql()
                self.results['changed'] = True
                self.log("ElasticPools instance deleted")
            elif self.state == 'present':
                self.log("Need to check if ElasticPools instance has to be deleted or may be updated")
                to_be_updated = True

        if self.state == 'present':

            self.log("Need to Create / Update the ElasticPools instance")

            if self.check_mode:
                return self.results

            if to_be_updated:
                self.results['state'] = self.create_update_sql()
                self.results['changed'] = True
            else:
                self.results['state'] = response

            self.log("Creation / Update done")

        return self.results

    def create_update_sql(self):
        '''
        Creates or updates ElasticPools with the specified configuration.

        :return: deserialized ElasticPools instance state dictionary
        '''
        self.log("Creating / Updating the ElasticPools instance {0}".format(self.name))

        try:
            response = self.mgmt_client.elastic_pools.create_or_update(self.resource_group,
                                                                       self.server_name,
                                                                       self.name,
                                                                       self.parameters)
            if isinstance(response, AzureOperationPoller):
                response = self.get_poller_result(response)

        except CloudError as exc:
            self.log('Error attempting to create the ElasticPools instance.')
            self.fail("Error creating the ElasticPools instance: {0}".format(str(exc)))
        return response.as_dict()

    def delete_sql(self):
        '''
        Deletes specified ElasticPools instance in the specified subscription and resource group.

        :return: True
        '''
        self.log("Deleting the ElasticPools instance {0}".format(self.name))
        try:
            response = self.mgmt_client.elastic_pools.delete(self.resource_group,
                                                             self.server_name,
                                                             self.name)
        except CloudError as e:
            self.log('Error attempting to delete the ElasticPools instance.')
            self.fail("Error deleting the ElasticPools instance: {0}".format(str(e)))

        return True

    def get_sql(self):
        '''
        Gets the properties of the specified ElasticPools.

        :return: deserialized ElasticPools instance state dictionary
        '''
        self.log("Checking if the ElasticPools instance {0} is present".format(self.name))
        found = False
        try:
            response = self.mgmt_client.elastic_pools.get(self.resource_group,
                                                          self.server_name,
                                                          self.name)
            found = True
            self.log("Response : {0}".format(response))
            self.log("ElasticPools instance : {0} found".format(response.name))
        except CloudError as e:
            self.log('Did not find the ElasticPools instance.')
        if found is True:
            return response.as_dict()

        return False


def main():
    """Main execution"""
    AzureRMElasticPools()

if __name__ == '__main__':
    main()
