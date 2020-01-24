#!/usr/bin/python
#
# Copyright (c) 2019 Zim Kalinowski, (@zikalino)
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_devtestlab_info
version_added: "2.9"
short_description: Get Azure DevTest Lab facts
description:
    - Get facts of Azure DevTest Lab.

options:
    resource_group:
        description:
            - The name of the resource group.
        type: str
    name:
        description:
            - The name of the lab.
        type: str
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.
        type: list

extends_documentation_fragment:
    - azure

author:
    - Zim Kalinowski (@zikalino)
'''

EXAMPLES = '''
  - name: List instances of DevTest Lab by resource group
    azure_rm_devtestlab_info:
      resource_group: testrg

  - name: List instances of DevTest Lab in subscription
    azure_rm_devtestlab_info:

  - name: Get instance of DevTest Lab
    azure_rm_devtestlab_info:
      resource_group: testrg
      name: testlab
'''

RETURN = '''
labs:
    description:
        - A list of dictionaries containing facts for Lab.
    returned: always
    type: complex
    contains:
        id:
            description:
                - The identifier of the resource.
            returned: always
            type: str
            sample: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourcegroups/myResourceGroup/providers/microsoft.devtestlab/labs/myLab
        resource_group:
            description:
                - The name of the resource.
            returned: always
            type: str
            sample: testrg
        name:
            description:
                - The name of the resource.
            returned: always
            type: str
            sample: testlab
        location:
            description:
                - The location of the resource.
            returned: always
            type: str
            sample: eastus
        storage_type:
            description:
                - Lab storage type.
            returned: always
            type: str
            sample: standard
        premium_data_disks:
            description:
                - Are premium data disks allowed.
            returned: always
            type: bool
            sample: false
        provisioning_state:
            description:
                - Lab provisioning state.
            returned: always
            type: str
            sample: Succeeded
        artifacts_storage_account:
            description:
                - Artifacts storage account ID.
            returned: always
            type: str
            sample: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Storage/storageAccounts/myLab6346
        default_premium_storage_account:
            description:
                - Default premium storage account ID.
            returned: always
            type: str
            sample: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Storage/storageAccounts/myLab6346
        default_storage_account:
            description:
                - Default storage account ID.
            returned: always
            type: str
            sample: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Storage/storageAccounts/myLab6346
        premium_data_disk_storage_account:
            description:
                - Default storage account ID.
            returned: always
            type: str
            sample: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Storage/storageAccounts/myLab6346
        vault_name:
            description:
                - Key vault ID.
            returned: always
            type: str
            sample: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.KeyVault/vaults/myLab6788
        tags:
            description:
                - The tags of the resource.
            returned: always
            type: complex
            sample: "{ 'MyTag': 'MyValue' }"
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.devtestlabs import DevTestLabsClient
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMDevTestLabInfo(AzureRMModuleBase):
    def __init__(self):
        # define user inputs into argument
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str'
            ),
            name=dict(
                type='str'
            ),
            tags=dict(
                type='list'
            )
        )
        # store the results of the module operation
        self.results = dict(
            changed=False
        )
        self.mgmt_client = None
        self.resource_group = None
        self.name = None
        self.tags = None
        super(AzureRMDevTestLabInfo, self).__init__(self.module_arg_spec, supports_tags=False)

    def exec_module(self, **kwargs):
        is_old_facts = self.module._name == 'azure_rm_devtestlab_facts'
        if is_old_facts:
            self.module.deprecate("The 'azure_rm_devtestlab_facts' module has been renamed to 'azure_rm_devtestlab_info'", version='2.13')

        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])
        self.mgmt_client = self.get_mgmt_svc_client(DevTestLabsClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        if self.resource_group is not None:
            if self.name is not None:
                self.results['labs'] = self.get()
            else:
                self.results['labs'] = self.list_by_resource_group()
        else:
            self.results['labs'] = self.list_by_subscription()
        return self.results

    def list_by_resource_group(self):
        response = None
        results = []
        try:
            response = self.mgmt_client.labs.list_by_resource_group(resource_group_name=self.resource_group)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for Lab.')

        if response is not None:
            for item in response:
                if self.has_tags(item.tags, self.tags):
                    results.append(self.format_response(item))

        return results

    def list_by_subscription(self):
        response = None
        results = []
        try:
            response = self.mgmt_client.labs.list_by_subscription()
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for Lab.')

        if response is not None:
            for item in response:
                if self.has_tags(item.tags, self.tags):
                    results.append(self.format_response(item))

        return results

    def get(self):
        response = None
        results = []
        try:
            response = self.mgmt_client.labs.get(resource_group_name=self.resource_group,
                                                 name=self.name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for Lab.')

        if response and self.has_tags(response.tags, self.tags):
            results.append(self.format_response(response))

        return results

    def format_response(self, item):
        d = item.as_dict()
        d = {
            'id': d.get('id', None),
            'resource_group': self.resource_group,
            'name': d.get('name', None),
            'location': d.get('location', '').replace(' ', '').lower(),
            'storage_type': d.get('lab_storage_type', '').lower(),
            'premium_data_disks': d.get('premium_data_disks') == 'Enabled',
            'provisioning_state': d.get('provisioning_state'),
            'artifacts_storage_account': d.get('artifacts_storage_account'),
            'default_premium_storage_account': d.get('default_premium_storage_account'),
            'default_storage_account': d.get('default_storage_account'),
            'premium_data_disk_storage_account': d.get('premium_data_disk_storage_account'),
            'vault_name': d.get('vault_name'),
            'tags': d.get('tags', None)
        }
        return d


def main():
    AzureRMDevTestLabInfo()


if __name__ == '__main__':
    main()
