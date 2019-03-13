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
    sku:
        description:
            - The SKU of the workspace
        choices:
            - free
            - standard
            - premium
            - unlimited
            - per_node
            - per_gb2018
            - standalone
        default: per_gb2018
    retention_in_days:
        description:
            - The workspace data retention in days.
            - -1 means Unlimited retention for the C(unlimited) C(sku).
            - 730 days is the maximum allowed for all other C(sku)s.
    intelligence_packs:
        description:
            - Manage intelligence packs possible for this workspace.
            - "Enable one pack by setting it to C(true). E.g. {'Backup': true}".
            - "Disable one pack by setting it to C(false). E.g. {'Backup': false}".
            - Other intelligence packs not list in this property will not be changed.
        type: dict
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
            name=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            location=dict(type='str'),
            sku=dict(type='str', default='per_gb2018', choices=['free', 'standard', 'premium', 'unlimited', 'per_node', 'per_gb2018', 'standalone']),
            retention_in_days=dict(type='int'),
            intelligence_packs=dict(type='dict')
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
        self.intelligence_packs = None

        super(AzureRMWorkspace, self).__init__(self.module_arg_spec, supports_check_mode=True)

    def exec_module(self, **kwargs):

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        self.results = dict()
        changed = False

        if not self.location:
            resource_group = self.get_resource_group(self.resource_group)
            self.location = resource_group.location

        if self.sku == 'per_gb2018':
            self.sku = 'PerGB2018'
        else:
            self.sku = _snake_to_camel(self.sku)
        workspace = self.get_workspace()
        if not workspace and self.state == 'present':
            changed = True
            workspace = self.log_analytics_models.Workspace(sku=self.log_analytics_models.Sku(name=self.sku),
                                                            retention_in_days=self.retention_in_days,
                                                            location=self.location)
            if not self.check_mode:
                workspace = self.create_workspace(workspace)
        elif workspace and self.state == 'absent':
            changed = True
            workspace = None
            if not self.check_mode:
                self.delete_workspace()
        if workspace and workspace.id:
            self.results = self.to_dict(workspace)
            self.results['intelligence_packs'] = self.list_intelligence_packs()
            self.results['management_groups'] = self.list_management_groups()
            self.results['usages'] = self.list_usages()
            self.results['shared_keys'] = self.get_shared_keys()
        # handle the intelligence pack
        if workspace and workspace.id and self.intelligence_packs:
            intelligence_packs = self.results['intelligence_packs']
            for key in self.intelligence_packs.keys():
                enabled = self.intelligence_packs[key]
                for x in intelligence_packs:
                    if x['name'].lower() == key.lower():
                        if x['enabled'] != enabled:
                            changed = True
                            if not self.check_mode:
                                self.change_intelligence(x['name'], enabled)
                                x['enabled'] = enabled
                        break
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
        result = workspace.as_dict()
        result['sku'] = _camel_to_snake(workspace.sku.name)
        return result

    def list_intelligence_packs(self):
        try:
            response = self.log_analytics_client.workspaces.list_intelligence_packs(self.resource_group, self.name)
            return [x.as_dict() for x in response]
        except CloudError as exc:
            self.fail('Error when listing intelligence packs {0}'.format(exc.message or str(exc)))

    def change_intelligence(self, key, value):
        try:
            if value:
                self.log_analytics_client.workspaces.enable_intelligence_pack(self.resource_group, self.name, key)
            else:
                self.log_analytics_client.workspaces.disable_intelligence_pack(self.resource_group, self.name, key)
        except CloudError as exc:
            self.fail('Error when changing intelligence pack {0} - {1}'.format(key, exc.message or str(exc)))

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


def main():
    AzureRMWorkspace()


if __name__ == '__main__':
    main()
