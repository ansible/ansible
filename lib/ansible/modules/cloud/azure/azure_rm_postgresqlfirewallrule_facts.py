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
module: azure_rm_postgresqlfirewallrule_facts
version_added: "2.8"
short_description: Get Azure PostgreSQL Firewall Rule facts.
description:
    - Get facts of Azure PostgreSQL Firewall Rule.

options:
    resource_group:
        description:
            - The name of the resource group.
        required: True
    server_name:
        description:
            - The name of the server.
        required: True
    name:
        description:
            - The name of the server firewall rule.

extends_documentation_fragment:
    - azure

author:
    - "Zim Kalinowski (@zikalino)"

'''

EXAMPLES = '''
  - name: Get instance of PostgreSQL Firewall Rule
    azure_rm_postgresqlfirewallrule_facts:
      resource_group: myResourceGroup
      server_name: server_name
      name: firewall_rule_name

  - name: List instances of PostgreSQL Firewall Rule
    azure_rm_postgresqlfirewallrule_facts:
      resource_group: myResourceGroup
      server_name: server_name
'''

RETURN = '''
rules:
    description: A list of dictionaries containing facts for PostgreSQL Firewall Rule.
    returned: always
    type: complex
    contains:
        id:
            description:
                - Resource ID
            returned: always
            type: str
            sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/TestGroup/providers/Microsoft.DBforPostgreSQL/servers/testserver/fire
                    wallRules/rule1"
        server_name:
            description:
                - The name of the server.
            returned: always
            type: str
            sample: testserver
        name:
            description:
                - Resource name.
            returned: always
            type: str
            sample: rule1
        start_ip_address:
            description:
                - The start IP address of the PostgreSQL firewall rule.
            returned: always
            type: str
            sample: 10.0.0.16
        end_ip_address:
            description:
                - The end IP address of the PostgreSQL firewall rule.
            returned: always
            type: str
            sample: 10.0.0.18
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.rdbms.postgresql import PostgreSQLManagementClient
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMPostgreSQLFirewallRulesFacts(AzureRMModuleBase):
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
        self.mgmt_client = None
        self.resource_group = None
        self.server_name = None
        self.name = None
        super(AzureRMPostgreSQLFirewallRulesFacts, self).__init__(self.module_arg_spec, supports_tags=False)

    def exec_module(self, **kwargs):
        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])
        self.mgmt_client = self.get_mgmt_svc_client(PostgreSQLManagementClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        if (self.name is not None):
            self.results['rules'] = self.get()
        else:
            self.results['rules'] = self.list_by_server()
        return self.results

    def get(self):
        response = None
        results = []
        try:
            response = self.mgmt_client.firewall_rules.get(resource_group_name=self.resource_group,
                                                           server_name=self.server_name,
                                                           firewall_rule_name=self.name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for FirewallRules.')

        if response is not None:
            results.append(self.format_item(response))

        return results

    def list_by_server(self):
        response = None
        results = []
        try:
            response = self.mgmt_client.firewall_rules.list_by_server(resource_group_name=self.resource_group,
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
            'resource_group': self.resource_group,
            'id': d['id'],
            'server_name': self.server_name,
            'name': d['name'],
            'start_ip_address': d['start_ip_address'],
            'end_ip_address': d['end_ip_address']
        }
        return d


def main():
    AzureRMPostgreSQLFirewallRulesFacts()


if __name__ == '__main__':
    main()
