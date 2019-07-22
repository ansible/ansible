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
module: azure_rm_sqlfirewallrule_facts
version_added: "2.8"
short_description: Get Azure SQL Firewall Rule facts.
description:
    - Get facts of SQL Firewall Rule.

options:
    resource_group:
        description:
            - The name of the resource group that contains the server.
        required: True
    server_name:
        description:
            - The name of the server.
        required: True
    name:
        description:
            - The name of the firewall rule.

extends_documentation_fragment:
    - azure

author:
    - "Zim Kalinowski (@zikalino)"

'''

EXAMPLES = '''
  - name: Get instance of SQL Firewall Rule
    azure_rm_sqlfirewallrule_facts:
      resource_group: myResourceGroup
      server_name: testserver
      name: testrule

  - name: List instances of SQL Firewall Rule
    azure_rm_sqlfirewallrule_facts:
      resource_group: myResourceGroup
      server_name: testserver
'''

RETURN = '''
rules:
    description: A list of dict results containing the facts for matching SQL firewall rules.
    returned: always
    type: complex
    contains:
        id:
            description:
                - Resource ID
            returned: always
            type: str
            sample: "/subscriptions/xxxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Sql/servers/testser
                    ver/firewallRules/testrule"
        resource_group:
            description:
                - Resource group name.
            returned: always
            type: str
            sample: testgroup
        server_name:
            description:
                - SQL server name.
            returned: always
            type: str
            sample: testserver
        name:
            description:
                - Firewall rule name.
            returned: always
            type: str
            sample: testrule
        start_ip_address:
            description:
                - The start IP address of the firewall rule.
            returned: always
            type: str
            sample: 10.0.0.1
        end_ip_address:
            description:
                - The start IP address of the firewall rule.
            returned: always
            type: str
            sample: 10.0.0.5
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from msrest.polling import LROPoller
    from azure.mgmt.sql import SqlManagementClient
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMSqlFirewallRuleFacts(AzureRMModuleBase):
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
            name=dict(
                type='str'
            )
        )
        # store the results of the module operation
        self.results = dict(
            changed=False
        )
        self.resource_group = None
        self.server_name = None
        self.name = None
        super(AzureRMSqlFirewallRuleFacts, self).__init__(self.module_arg_spec, supports_tags=False)

    def exec_module(self, **kwargs):
        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        if (self.name is not None):
            self.results['rules'] = self.get()
        else:
            self.results['rules'] = self.list_by_server()
        return self.results

    def get(self):
        '''
        Gets facts of the specified SQL Firewall Rule.

        :return: deserialized SQL Firewall Ruleinstance state dictionary
        '''
        response = None
        results = []
        try:
            response = self.sql_client.firewall_rules.get(resource_group_name=self.resource_group,
                                                          server_name=self.server_name,
                                                          firewall_rule_name=self.name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for FirewallRules.')

        if response is not None:
            results.append(self.format_item(response))

        return results

    def list_by_server(self):
        '''
        Gets facts of the specified SQL Firewall Rule.

        :return: deserialized SQL Firewall Ruleinstance state dictionary
        '''
        response = None
        results = []
        try:
            response = self.sql_client.firewall_rules.list_by_server(resource_group_name=self.resource_group,
                                                                     server_name=self.server_name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for FirewallRules.')

        if response is not None:
            for item in response:
                results.append(self.format_item(item))

        return results

    def format_item(self, item):
        d = item.as_dict()
        d = {
            'id': d['id'],
            'resource_group': self.resource_group,
            'server_name': self.server_name,
            'name': d['name'],
            'start_ip_address': d['start_ip_address'],
            'end_ip_address': d['end_ip_address']
        }
        return d


def main():
    AzureRMSqlFirewallRuleFacts()


if __name__ == '__main__':
    main()
