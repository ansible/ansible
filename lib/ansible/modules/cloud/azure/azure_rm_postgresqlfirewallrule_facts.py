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
module: azure_rm_postgresqlfirewallrule_facts
version_added: "2.5"
short_description: Get PostgreSQL Firewall Rule facts.
description:
    - Get facts of PostgreSQL Firewall Rule.

options:
    resource_group:
        description:
            - The name of the resource group that contains the resource. You can obtain this value from the Azure Resource Manager API or the portal.
        required: True
    server_name:
        description:
            - The name of the server.
        required: True
    firewall_rule_name:
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
      resource_group: resource_group_name
      server_name: server_name
      firewall_rule_name: firewall_rule_name

  - name: List instances of PostgreSQL Firewall Rule
    azure_rm_postgresqlfirewallrule_facts:
      resource_group: resource_group_name
      server_name: server_name
'''

RETURN = '''
firewall_rules:
    description: A list of dict results where the key is the name of the PostgreSQL Firewall Rule and the values are the facts for that PostgreSQL Firewall Rule.
    returned: always
    type: complex
    contains:
        postgresqlfirewallrule_name:
            description: The key is the name of the server that the values relate to.
            type: complex
            contains:
                id:
                    description:
                        - Resource ID
                    returned: always
                    type: str
                    sample: "/subscriptions/ffffffff-ffff-ffff-ffff-ffffffffffff/resourceGroups/TestGroup/providers/Microsoft.DBforPostgreSQL/servers/testser
                            ver/firewallRules/rule1"
                name:
                    description:
                        - Resource name.
                    returned: always
                    type: str
                    sample: rule1
                type:
                    description:
                        - Resource type.
                    returned: always
                    type: str
                    sample: Microsoft.DBforPostgreSQL/servers/firewallRules
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from msrestazure.azure_operation import AzureOperationPoller
    from azure.mgmt.rdbms.postgresql import PostgreSQLManagementClient
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMFirewallRulesFacts(AzureRMModuleBase):
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
            firewall_rule_name=dict(
                type='str'
            )
        )
        # store the results of the module operation
        self.results = dict(
            changed=False,
            ansible_facts=dict()
        )
        self.mgmt_client = None
        self.resource_group = None
        self.server_name = None
        self.firewall_rule_name = None
        super(AzureRMFirewallRulesFacts, self).__init__(self.module_arg_spec)

    def exec_module(self, **kwargs):
        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])
        self.mgmt_client = self.get_mgmt_svc_client(PostgreSQLManagementClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        if (self.resource_group is not None and
                self.server_name is not None and
                self.firewall_rule_name is not None):
            self.results['firewall_rules'] = self.get()
        elif (self.resource_group is not None and
              self.server_name is not None):
            self.results['firewall_rules'] = self.list_by_server()
        return self.results

    def get(self):
        '''
        Gets facts of the specified PostgreSQL Firewall Rule.

        :return: deserialized PostgreSQL Firewall Ruleinstance state dictionary
        '''
        response = None
        results = {}
        try:
            response = self.mgmt_client.firewall_rules.get(resource_group_name=self.resource_group,
                                                           server_name=self.server_name,
                                                           firewall_rule_name=self.firewall_rule_name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for FirewallRules.')

        if response is not None:
            results[response.name] = response.as_dict()

        return results

    def list_by_server(self):
        '''
        Gets facts of the specified PostgreSQL Firewall Rule.

        :return: deserialized PostgreSQL Firewall Ruleinstance state dictionary
        '''
        response = None
        results = {}
        try:
            response = self.mgmt_client.firewall_rules.list_by_server(resource_group_name=self.resource_group,
                                                                      server_name=self.server_name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for FirewallRules.')

        if response is not None:
            for item in response:
                results[item.name] = item.as_dict()

        return results


def main():
    AzureRMFirewallRulesFacts()
if __name__ == '__main__':
    main()
