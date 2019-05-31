#!/usr/bin/python
#
# Copyright (c) 2019 Zim Kalinowski, (@zikalino)
# Copyright (c) 2019 Matti Ranta, (@techknowlogick)
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_mariadbconfiguration
version_added: "2.8"
short_description: Manage Configuration instance
description:
    - Create, update and delete instance of Configuration.

options:
    resource_group:
        description:
            - The name of the resource group that contains the resource.
        required: True
    server_name:
        description:
            - The name of the server.
        required: True
    name:
        description:
            - The name of the server configuration.
        required: True
    value:
        description:
            - Value of the configuration.
    state:
        description:
            - Assert the state of the MariaDB configuration. Use C(present) to update setting, or C(absent) to reset to default value.
        default: present
        choices:
            - absent
            - present

extends_documentation_fragment:
    - azure

author:
    - Zim Kalinowski (@zikalino)
    - Matti Ranta (@techknowlogick)
'''

EXAMPLES = '''
  - name: Update SQL Server setting
    azure_rm_mariadbconfiguration:
      resource_group: myResourceGroup
      server_name: myServer
      name: event_scheduler
      value: "ON"
'''

RETURN = '''
id:
    description:
        - Resource ID.
    returned: always
    type: str
    sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.DBforMariaDB/servers/myServer/confi
             gurations/event_scheduler"
'''

import time
from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from msrest.polling import LROPoller
    from azure.mgmt.rdbms.mysql import MariaDBManagementClient
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass


class Actions:
    NoAction, Create, Update, Delete = range(4)


class AzureRMMariaDbConfiguration(AzureRMModuleBase):

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
            value=dict(
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
        self.value = None

        self.results = dict(changed=False)
        self.state = None
        self.to_do = Actions.NoAction

        super(AzureRMMariaDbConfiguration, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                          supports_check_mode=True,
                                                          supports_tags=False)

    def exec_module(self, **kwargs):

        for key in list(self.module_arg_spec.keys()):
            if hasattr(self, key):
                setattr(self, key, kwargs[key])

        old_response = None
        response = None

        old_response = self.get_configuration()

        if not old_response:
            self.log("Configuration instance doesn't exist")
            if self.state == 'absent':
                self.log("Old instance didn't exist")
            else:
                self.to_do = Actions.Create
        else:
            self.log("Configuration instance already exists")
            if self.state == 'absent' and old_response['source'] == 'user-override':
                self.to_do = Actions.Delete
            elif self.state == 'present':
                self.log("Need to check if Configuration instance has to be deleted or may be updated")
                if self.value != old_response.get('value'):
                    self.to_do = Actions.Update

        if (self.to_do == Actions.Create) or (self.to_do == Actions.Update):
            self.log("Need to Create / Update the Configuration instance")

            if self.check_mode:
                self.results['changed'] = True
                return self.results

            response = self.create_update_configuration()

            self.results['changed'] = True
            self.log("Creation / Update done")
        elif self.to_do == Actions.Delete:
            self.log("Configuration instance deleted")
            self.results['changed'] = True

            if self.check_mode:
                return self.results

            self.delete_configuration()
        else:
            self.log("Configuration instance unchanged")
            self.results['changed'] = False
            response = old_response

        if response:
            self.results["id"] = response["id"]

        return self.results

    def create_update_configuration(self):
        self.log("Creating / Updating the Configuration instance {0}".format(self.name))

        try:
            response = self.mariadb_client.configurations.create_or_update(resource_group_name=self.resource_group,
                                                                           server_name=self.server_name,
                                                                           configuration_name=self.name,
                                                                           value=self.value,
                                                                           source='user-override')
            if isinstance(response, LROPoller):
                response = self.get_poller_result(response)

        except CloudError as exc:
            self.log('Error attempting to create the Configuration instance.')
            self.fail("Error creating the Configuration instance: {0}".format(str(exc)))
        return response.as_dict()

    def delete_configuration(self):
        self.log("Deleting the Configuration instance {0}".format(self.name))
        try:
            response = self.mariadb_client.configurations.create_or_update(resource_group_name=self.resource_group,
                                                                           server_name=self.server_name,
                                                                           configuration_name=self.name,
                                                                           source='system-default')
        except CloudError as e:
            self.log('Error attempting to delete the Configuration instance.')
            self.fail("Error deleting the Configuration instance: {0}".format(str(e)))

        return True

    def get_configuration(self):
        self.log("Checking if the Configuration instance {0} is present".format(self.name))
        found = False
        try:
            response = self.mariadb_client.configurations.get(resource_group_name=self.resource_group,
                                                              server_name=self.server_name,
                                                              configuration_name=self.name)
            found = True
            self.log("Response : {0}".format(response))
            self.log("Configuration instance : {0} found".format(response.name))
        except CloudError as e:
            self.log('Did not find the Configuration instance.')
        if found is True:
            return response.as_dict()

        return False


def main():
    """Main execution"""
    AzureRMMariaDbConfiguration()


if __name__ == '__main__':
    main()
