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
module: azure_rm_containerregistry_facts
version_added: "2.7"
short_description: Get Azure Container Registry facts.
description:
    - Get facts for Container Registry.

options:
    resource_group:
        description:
            - The name of the resource group to which the container registry belongs.
        required: True
    name:
        description:
            - The name of the container registry.
    retrieve_credentials:
        description:
            - Retrieve credentials for container registry.
        type: bool
        default: no
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.

extends_documentation_fragment:
    - azure

author:
    - "Zim Kalinowski (@zikalino)"

'''

EXAMPLES = '''
  - name: Get instance of Registry
    azure_rm_containerregistry_facts:
      resource_group: myResourceGroup
      name: sampleregistry

  - name: List instances of Registry
    azure_rm_containerregistry_facts:
      resource_group: myResourceGroup
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
            sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.ContainerRegistry/registr
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
            sample: classic
        provisioning_state:
            description:
                - Provisioning state of the container registry
            returned: always
            type: str
            sample: Succeeded
        login_server:
            description:
                - Login server for the registry.
            returned: always
            type: str
            sample: acrd08521b.azurecr.io
        credentials:
            description:
                - Credentials, fields will be empty if admin user is not enabled for ACR
            return: when C(retrieve_credentials) is set and C(admin_user_enabled) is set on ACR
            type: complex
            contains:
                username:
                    description:
                        - The user name for container registry.
                    returned: when registry exists and C(admin_user_enabled) is set
                    type: str
                    sample: zim
                password:
                    description:
                        - password value
                    returned: when registry exists and C(admin_user_enabled) is set
                    type: str
                    sample: pass1value
                password2:
                    description:
                        - password2 value
                    returned: when registry exists and C(admin_user_enabled) is set
                    type: str
                    sample: pass2value
        tags:
            description: Tags assigned to the resource. Dictionary of string:string pairs.
            type: dict
            sample: { "tag1": "abc" }
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


class AzureRMContainerRegistryFacts(AzureRMModuleBase):
    def __init__(self):
        # define user inputs into argument
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                required=True
            ),
            name=dict(
                type='str'
            ),
            tags=dict(
                type='list'
            ),
            retrieve_credentials=dict(
                type='bool',
                default=False
            )
        )
        # store the results of the module operation
        self.results = dict(
            changed=False
        )
        self.resource_group = None
        self.name = None
        self.retrieve_credentials = False
        super(AzureRMContainerRegistryFacts, self).__init__(self.module_arg_spec, supports_tags=False)

    def exec_module(self, **kwargs):
        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        if self.name:
            self.results['registries'] = self.get()
        elif self.resource_group:
            self.results['registries'] = self.list_by_resource_group()
        else:
            self.results['registries'] = self.list_all()

        return self.results

    def get(self):
        response = None
        results = []
        try:
            response = self.containerregistry_client.registries.get(resource_group_name=self.resource_group,
                                                                    registry_name=self.name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for Registries.')

        if response is not None:
            if self.has_tags(response.tags, self.tags):
                results.append(self.format_item(response))

        return results

    def list_all(self):
        response = None
        results = []
        try:
            response = self.containerregistry_client.registries.list()
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.fail('Could not get facts for Registries.')

        if response is not None:
            for item in response:
                if self.has_tags(item.tags, self.tags):
                    results.append(self.format_item(item))
        return results

    def list_by_resource_group(self):
        response = None
        results = []
        try:
            response = self.containerregistry_client.registries.list_by_resource_group(resource_group_name=self.resource_group)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.fail('Could not get facts for Registries.')

        if response is not None:
            for item in response:
                if self.has_tags(item.tags, self.tags):
                    results.append(self.format_item(item))
        return results

    def format_item(self, item):
        d = item.as_dict()
        resource_group = d['id'].split('resourceGroups/')[1].split('/')[0]
        name = d['name']
        credentials = {}
        admin_user_enabled = d['admin_user_enabled']

        if self.retrieve_credentials and admin_user_enabled:
            credentials = self.containerregistry_client.registries.list_credentials(resource_group, name).as_dict()
            for index in range(len(credentials['passwords'])):
                password = credentials['passwords'][index]
                if password['name'] == 'password':
                    credentials['password'] = password['value']
                elif password['name'] == 'password2':
                    credentials['password2'] = password['value']
            credentials.pop('passwords')

        d = {
            'resource_group': resource_group,
            'name': d['name'],
            'location': d['location'],
            'admin_user_enabled': admin_user_enabled,
            'sku': d['sku']['tier'].lower(),
            'provisioning_state': d['provisioning_state'],
            'login_server': d['login_server'],
            'id': d['id'],
            'tags': d.get('tags', None),
            'credentials': credentials
        }
        return d


def main():
    AzureRMContainerRegistryFacts()


if __name__ == '__main__':
    main()
