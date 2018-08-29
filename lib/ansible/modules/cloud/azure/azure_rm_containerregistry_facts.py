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
module: azure_rm_containerregistry_facts
version_added: "2.7"
short_description: Get Registry facts.
description:
    - Get facts of Registry.

options:
    resource_group:
        description:
            - The name of the resource group to which the container registry belongs.
        required: True
    name:
        description:
            - The name of the container registry.

extends_documentation_fragment:
    - azure

author:
    - "Zim Kalinowski (@zikalino)"

'''

EXAMPLES = '''
  - name: Get instance of Registry
    azure_rm_containerregistry_facts:
      resource_group: sampleresourcegroup
      name: sampleregistry

  - name: List instances of Registry
    azure_rm_containerregistry_facts:
      resource_group: sampleresourcegroup
'''

RETURN = '''
registries:
    description: A list of dictionaries containing facts for registries.
    returned: always
    type: complex
    contains:
        id:
            description:
                - The resource ID.
            returned: always
            type: str
            sample: "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/myResourceGroup/providers/Microsoft.ContainerRegistry/registr
                    ies/myRegistry"
        name:
            description:
                - The name of the resource.
            returned: always
            type: str
            sample: myRegistry
        location:
            description:
                - The location of the resource. This cannot be changed after the resource is created.
            returned: always
            type: str
            sample: westus
        admin_user_enabled:
            description:
                - Is admin user enabled.
            returned: always
            type: bool
            sample: yes
        sku:
            description:
                - The SKU name of the container registry.
            returned: always
            type: str
            sample: Classic
        status_message:
            description:
                - The detailed status message of there registry, including alerts and error messages.
            returned: always
            type: str
            sample: The registry is ready.
        status_timestamp:
            description:
                - The timestamp when the status was changed to the current value.
            returned: always
            type: str
            sample: 2017-03-01T23:15:37.0707808Z
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from msrestazure.azure_operation import AzureOperationPoller
    from azure.mgmt.containerregistry import ContainerRegistryManagementClient
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMRegistriesFacts(AzureRMModuleBase):
    def __init__(self):
        # define user inputs into argument
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                required=True
            ),
            name=dict(
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
        self.name = None
        super(AzureRMRegistriesFacts, self).__init__(self.module_arg_spec, supports_tags=False)

    def exec_module(self, **kwargs):
        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])
        self.mgmt_client = self.get_mgmt_svc_client(ContainerRegistryManagementClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        if (self.resource_group is not None and
                self.name is not None):
            self.results['registries'] = self.get()
        elif (self.resource_group is not None):
            self.results['registries'] = self.list_by_resource_group()
        return self.results

    def get(self):
        response = None
        results = {}
        try:
            response = self.mgmt_client.registries.get(resource_group_name=self.resource_group,
                                                       registry_name=self.name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for Registries.')

        if response is not None:
            results[response.name] = self.format_item(response)

        return results

    def list_by_resource_group(self):
        response = None
        results = {}
        try:
            response = self.mgmt_client.registries.list_by_resource_group(resource_group_name=self.resource_group)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for Registries.')

        if response is not None:
            for item in response:
                results[item.name] = self.format_item(item)

        return results

    def format_item(self, item):
        d = item.as_dict()
        d = {
            'resource_group': self.resource_group,
            'name': self.name,
            'location': d['location'],
            'admin_user_enabled': d['admin_user_enabled'],
            'sku': d['sku']['tier'].lower(),
            'status_message': d['status']['message'],
            'status_timestamp': d['status']['timestamp'],
            'id': d['id']
        }
        return d


def main():
    AzureRMRegistriesFacts()


if __name__ == '__main__':
    main()
