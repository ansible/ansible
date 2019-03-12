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
        required: true
    name:
        description:
            - Name of the workspace.
        required: true
    state:
        description:
            - Assert the state of the image. Use C(present) to create or update a image and C(absent) to delete an image.
        default: present
        choices:
            - absent
            - present
    location:
        description:
            - Resource location.

extends_documentation_fragment:
    - azure
    - azure_tags

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
from ansible.module_utils.common.dict_transformations import _snake_to_camel

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
            name=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            location=dict(type='str'),
            sku=dict(type='str', default='per_gb_2018', choices=['free', 'standard', 'premium', 'unlimited', 'per_node', 'per_gb_2018', 'standalone']),
            retention_in_days=dict(type='int')
        )

        self.results = dict(
            changed=False,
            id=None
        )

        self.resource_group = None
        self.name = None
        self.state = None
        self.location = None
        self.sku = None
        self.retention_in_days = None

        super(AzureRMWorkspace, self).__init__(self.module_arg_spec, supports_check_mode=True)

    def exec_module(self, **kwargs):

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        self.results = dict()
        changed = False

        if not self.location:
            resource_group = self.get_resource_group(self.resource_group)
            self.location = resource_group.location

        if self.sku == 'per_gb_2018':
            self.sku = 'PerGB2018'
        else:
            self.sku = _snake_to_camel(self.sku)
        workspace = self.get_workspace()
        if not workspace and self.state == 'present':
            changed = True
            workspace = self.log_analytics_models.Workspace(sku=self.log_analytics_models.Sku(name=self.sku),
                                                            retention_in_days=self.retention_in_days)
            if not self.check_mode:
                workspace = self.create_workspace(workspace)
        elif workspace and self.state == 'absent':
            changed = True
            workspace = None
            if not self.check_mode:
                self.delete_workspace()
        if workspace:
            self.results = self.to_dict(workspace)
        self.results['changed'] = changed
        return self.results

    def create_workspace(self, workspace):
        try:
            poller = self.log_analytics_client.workspaces.create_or_update(self.resource_group, self.name, workspace)
            return self.get_poller_result(poller)
        except CloudError as exc:
            self.fail('Error when creating workspace {0} - {1}'.format(self.name, exc.message or str(exc)))

    def get_workspace(self):
        try:
            return self.log_analytics_client.workspaces.get(self.resource_group, self.name)
        except CloudError:
            pass

    def delete_workspace(self):
        try:
            self.log_analytics_client.workspaces.delete(self.resource_group, self.name)
        except CloudError as exc:
            self.fail('Error when deleting workspace {0} - {1}'.format(self.name, exc.message or str(exc)))

    def to_dict(self, workspace):
        return workspace.as_dict()


def main():
    AzureRMWorkspace()


if __name__ == '__main__':
    main()
