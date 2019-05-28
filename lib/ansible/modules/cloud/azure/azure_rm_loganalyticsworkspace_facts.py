#!/usr/bin/python
#
# Copyright (c) 2019 Yuwei Zhou, <yuwzho@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_loganalyticsworkspace_facts
version_added: "2.8"
short_description: Get facts of Azure Log Analytics workspaces.
description:
    - Get, query Azure Log Analytics workspaces.
options:
    resource_group:
        description:
            - Name of resource group.
        required: True
    name:
        description:
            - Name of the workspace.
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.
    show_intelligence_packs:
        description:
            - Show the intelligence packs for a workspace.
            - Note this will cost one more network overhead for each workspace, expected slow response.
    show_management_groups:
        description:
            - Show the management groups for a workspace.
            - Note this will cost one more network overhead for each workspace, expected slow response.
    show_shared_keys:
        description:
            - Show the shared keys for a workspace.
            - Note this will cost one more network overhead for each workspace, expected slow response.
    show_usages:
        description:
            - Show the list of usages for a workspace.
            - Note this will cost one more network overhead for each workspace, expected slow response.
extends_documentation_fragment:
    - azure

author:
    - "Yuwei Zhou (@yuwzho)"

'''

EXAMPLES = '''
- name: Query a workspace
  azure_rm_loganalyticsworkspace_facts:
      resource_group: myResourceGroup
      name: myLogAnalyticsWorkspace
      show_intelligence_packs: true
      show_management_groups: true
      show_shared_keys: true
      show_usages: true
'''

RETURN = '''
id:
    description: Workspace resource path.
    type: str
    returned: success
    example: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.OperationalInsights/workspaces/m
              yLogAnalyticsWorkspace"
location:
    description:
        - Resource location.
    type: str
    returned: success
    example: "eastus"
sku:
    description:
        - The SKU of the workspace
    type: str
    returned: success
    example: "per_gb2018"
retention_in_days:
    description:
        - The workspace data retention in days.
        - -1 means Unlimited retention for the C(unlimited) C(sku).
        - 730 days is the maximum allowed for all other C(sku)s.
    type: int
    returned: success
    example: 40
intelligence_packs:
    description:
        - Lists all the intelligence packs possible and whether they are enabled or disabled for a given workspace.
    type: list
    returned: success
    example: ['name': 'CapacityPerformance', 'enabled': true]
management_groups:
    description:
        - List of management groups connected to the workspace.
    type: list
    returned: success
    example: "{'value': []}"
shared_keys:
    description:
        - Shared keys for the workspace.
    type: list
    returned: success
    example: "{
                'primarySharedKey': 'BozLY1JnZbxu0jWUQSY8iRPEM8ObmpP8rW+8bUl3+HpDJI+n689SxXgTgU7k1qdxo/WugRLxechxbolAfHM5uA==',
                'secondarySharedKey': '7tDt5W0JBrCQKtQA3igfFltLSzJeyr9LmuT+B/ibzd8cdC1neZ1ePOQLBx5NUzc0q2VUIK0cLhWNyFvo/hT8Ww=='
              }"
usages:
    description:
        - List of usage metrics for the workspace.
    type: list
    returned: success
    example: "{
                'value': [
                    {
                    'name': {
                        'value': 'DataAnalyzed',
                        'localizedValue': 'Data Analyzed'
                    },
                    'unit': 'Bytes',
                    'currentValue': 0,
                    'limit': 524288000,
                    'nextResetTime': '2017-10-03T00:00:00Z',
                    'quotaPeriod': 'P1D'
                    }
                ]
              }"
'''  # NOQA

from ansible.module_utils.azure_rm_common import AzureRMModuleBase, format_resource_id
from ansible.module_utils.common.dict_transformations import _snake_to_camel, _camel_to_snake

try:
    from msrestazure.tools import parse_resource_id
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMLogAnalyticsWorkspaceFact(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            resource_group=dict(type='str', required=True),
            name=dict(type='str'),
            tags=dict(type='list'),
            show_shared_keys=dict(type='bool'),
            show_intelligence_packs=dict(type='bool'),
            show_usages=dict(type='bool'),
            show_management_groups=dict(type='bool')
        )

        self.results = dict(
            changed=False,
            workspaces=[]
        )

        self.resource_group = None
        self.name = None
        self.tags = None
        self.show_intelligence_packs = None
        self.show_shared_keys = None
        self.show_usages = None
        self.show_management_groups = None

        super(AzureRMLogAnalyticsWorkspaceFact, self).__init__(self.module_arg_spec, supports_tags=False, facts_module=True)

    def exec_module(self, **kwargs):

        for key in list(self.module_arg_spec.keys()):
            setattr(self, key, kwargs[key])

        if self.name:
            item = self.get_workspace()
            response = [item] if item else []
        else:
            response = self.list_by_resource_group()

        self.results['workspaces'] = [self.to_dict(x) for x in response if self.has_tags(x.tags, self.tags)]
        return self.results

    def get_workspace(self):
        try:
            return self.log_analytics_client.workspaces.get(self.resource_group, self.name)
        except CloudError:
            pass
        return None

    def list_by_resource_group(self):
        try:
            return self.log_analytics_client.workspaces.list_by_resource_group(self.resource_group)
        except CloudError:
            pass
        return []

    def list_intelligence_packs(self):
        try:
            response = self.log_analytics_client.workspaces.list_intelligence_packs(self.resource_group, self.name)
            return [x.as_dict() for x in response]
        except CloudError as exc:
            self.fail('Error when listing intelligence packs {0}'.format(exc.message or str(exc)))

    def list_management_groups(self):
        result = []
        try:
            response = self.log_analytics_client.workspaces.list_management_groups(self.resource_group, self.name)
            while True:
                result.append(response.next().as_dict())
        except StopIteration:
            pass
        except CloudError as exc:
            self.fail('Error when listing management groups {0}'.format(exc.message or str(exc)))
        return result

    def list_usages(self):
        result = []
        try:
            response = self.log_analytics_client.workspaces.list_usages(self.resource_group, self.name)
            while True:
                result.append(response.next().as_dict())
        except StopIteration:
            pass
        except CloudError as exc:
            self.fail('Error when listing usages {0}'.format(exc.message or str(exc)))
        return result

    def get_shared_keys(self):
        try:
            return self.log_analytics_client.workspaces.get_shared_keys(self.resource_group, self.name).as_dict()
        except CloudError as exc:
            self.fail('Error when getting shared key {0}'.format(exc.message or str(exc)))

    def to_dict(self, workspace):
        result = workspace.as_dict()
        result['sku'] = _camel_to_snake(workspace.sku.name)
        if self.show_intelligence_packs:
            result['intelligence_packs'] = self.list_intelligence_packs()
        if self.show_management_groups:
            result['management_groups'] = self.list_management_groups()
        if self.show_shared_keys:
            result['shared_keys'] = self.get_shared_keys()
        if self.show_usages:
            result['usages'] = self.list_usages()
        return result


def main():
    AzureRMLogAnalyticsWorkspaceFact()


if __name__ == '__main__':
    main()
