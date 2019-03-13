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
module: azure_rm_workspace
version_added: "2.8"
short_description: Manage Azure Log Analytics workspaces.
description:
    - Create, delete Azure Log Analytics workspaces.
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
extends_documentation_fragment:
    - azure

author:
    - "Yuwei Zhou (@yuwzho)"

'''

EXAMPLES = '''
'''

RETURN = '''
id:
    description: Workspace resource path.
    type: str
    returned: success
    example: "/subscriptions/XXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXX/resourceGroups/foo/providers/Microsoft.OperationalInsights/workspaces/bar"
'''  # NOQA

from ansible.module_utils.azure_rm_common import AzureRMModuleBase, format_resource_id
from ansible.module_utils.common.dict_transformations import _snake_to_camel, _camel_to_snake

try:
    from msrestazure.tools import parse_resource_id
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMWorkspace(AzureRMModuleBase):

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

        super(AzureRMWorkspace, self).__init__(self.module_arg_spec, supports_check_mode=True)

    def exec_module(self, **kwargs):

        for key in list(self.module_arg_spec.keys()):
            setattr(self, key, kwargs[key])

        if self.name:
            response = [self.get_workspace()]
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
    AzureRMWorkspace()


if __name__ == '__main__':
    main()
