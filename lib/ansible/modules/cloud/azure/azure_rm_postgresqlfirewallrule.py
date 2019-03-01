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
module: azure_rm_postgresqlfirewallrule
version_added: "2.8"
short_description: Manage PostgreSQL firewall rule instance.
description:
    - Create, update and delete instance of PostgreSQL firewall rule.

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
            - The name of the PostgreSQL firewall rule.
        required: True
    start_ip_address:
        description:
            - The start IP address of the PostgreSQL firewall rule. Must be IPv4 format.
    end_ip_address:
        description:
            - The end IP address of the PostgreSQL firewall rule. Must be IPv4 format.
    state:
        description:
            - Assert the state of the PostgreSQL firewall rule. Use C(present) to create or update a PostgreSQL firewall rule and C(absent) to delete it.
        default: present
        choices:
            - absent
            - present

extends_documentation_fragment:
    - azure

author:
    - "Zim Kalinowski (@zikalino)"

'''

EXAMPLES = '''
  - name: Create (or update) PostgreSQL firewall rule
    azure_rm_postgresqlfirewallrule:
      resource_group: myResourceGroup
      server_name: testserver
      name: rule1
      start_ip_address: 10.0.0.16
      end_ip_address: 10.0.0.18
'''

RETURN = '''
id:
    description:
        - Resource ID
    returned: always
    type: str
    sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.DBforPostgreSQL/servers/testserver
             /firewallRules/rule1"
'''

import time
from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from msrest.polling import LROPoller
    from azure.mgmt.rdbms.postgresql import PostgreSQLManagementClient
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass


class Actions:
    NoAction, Create, Update, Delete = range(4)


class AzureRMPostgreSqlFirewallRules(AzureRMModuleBase):
    """Configuration class for an Azure RM PostgreSQL firewall rule resource"""

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
            start_ip_address=dict(
                type='str'
            ),
            end_ip_address=dict(
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
        self.start_ip_address = None
        self.end_ip_address = None

        self.results = dict(changed=False)
        self.state = None
        self.to_do = Actions.NoAction

        super(AzureRMPostgreSqlFirewallRules, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                             supports_check_mode=True,
                                                             supports_tags=False)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        for key in list(self.module_arg_spec.keys()):
            if hasattr(self, key):
                setattr(self, key, kwargs[key])

        old_response = None
        response = None

        resource_group = self.get_resource_group(self.resource_group)

        old_response = self.get_firewallrule()

        if not old_response:
            self.log("PostgreSQL firewall rule instance doesn't exist")
            if self.state == 'absent':
                self.log("Old instance didn't exist")
            else:
                self.to_do = Actions.Create
        else:
            self.log("PostgreSQL firewall rule instance already exists")
            if self.state == 'absent':
                self.to_do = Actions.Delete
            elif self.state == 'present':
                self.log("Need to check if PostgreSQL firewall rule instance has to be deleted or may be updated")
                if (self.start_ip_address is not None) and (self.start_ip_address != old_response['start_ip_address']):
                    self.to_do = Actions.Update
                if (self.end_ip_address is not None) and (self.end_ip_address != old_response['end_ip_address']):
                    self.to_do = Actions.Update

        if (self.to_do == Actions.Create) or (self.to_do == Actions.Update):
            self.log("Need to Create / Update the PostgreSQL firewall rule instance")

            if self.check_mode:
                self.results['changed'] = True
                return self.results

            response = self.create_update_firewallrule()

            if not old_response:
                self.results['changed'] = True
            else:
                self.results['changed'] = old_response.__ne__(response)
            self.log("Creation / Update done")
        elif self.to_do == Actions.Delete:
            self.log("PostgreSQL firewall rule instance deleted")
            self.results['changed'] = True

            if self.check_mode:
                return self.results

            self.delete_firewallrule()
            # make sure instance is actually deleted, for some Azure resources, instance is hanging around
            # for some time after deletion -- this should be really fixed in Azure
            while self.get_firewallrule():
                time.sleep(20)
        else:
            self.log("PostgreSQL firewall rule instance unchanged")
            self.results['changed'] = False
            response = old_response

        if response:
            self.results["id"] = response["id"]

        return self.results

    def create_update_firewallrule(self):
        '''
        Creates or updates PostgreSQL firewall rule with the specified configuration.

        :return: deserialized PostgreSQL firewall rule instance state dictionary
        '''
        self.log("Creating / Updating the PostgreSQL firewall rule instance {0}".format(self.name))

        try:
            response = self.postgresql_client.firewall_rules.create_or_update(resource_group_name=self.resource_group,
                                                                              server_name=self.server_name,
                                                                              firewall_rule_name=self.name,
                                                                              start_ip_address=self.start_ip_address,
                                                                              end_ip_address=self.end_ip_address)
            if isinstance(response, LROPoller):
                response = self.get_poller_result(response)

        except CloudError as exc:
            self.log('Error attempting to create the PostgreSQL firewall rule instance.')
            self.fail("Error creating the PostgreSQL firewall rule instance: {0}".format(str(exc)))
        return response.as_dict()

    def delete_firewallrule(self):
        '''
        Deletes specified PostgreSQL firewall rule instance in the specified subscription and resource group.

        :return: True
        '''
        self.log("Deleting the PostgreSQL firewall rule instance {0}".format(self.name))
        try:
            response = self.postgresql_client.firewall_rules.delete(resource_group_name=self.resource_group,
                                                                    server_name=self.server_name,
                                                                    firewall_rule_name=self.name)
        except CloudError as e:
            self.log('Error attempting to delete the PostgreSQL firewall rule instance.')
            self.fail("Error deleting the PostgreSQL firewall rule instance: {0}".format(str(e)))

        return True

    def get_firewallrule(self):
        '''
        Gets the properties of the specified PostgreSQL firewall rule.

        :return: deserialized PostgreSQL firewall rule instance state dictionary
        '''
        self.log("Checking if the PostgreSQL firewall rule instance {0} is present".format(self.name))
        found = False
        try:
            response = self.postgresql_client.firewall_rules.get(resource_group_name=self.resource_group,
                                                                 server_name=self.server_name,
                                                                 firewall_rule_name=self.name)
            found = True
            self.log("Response : {0}".format(response))
            self.log("PostgreSQL firewall rule instance : {0} found".format(response.name))
        except CloudError as e:
            self.log('Did not find the PostgreSQL firewall rule instance.')
        if found is True:
            return response.as_dict()

        return False


def main():
    """Main execution"""
    AzureRMPostgreSqlFirewallRules()


if __name__ == '__main__':
    main()
