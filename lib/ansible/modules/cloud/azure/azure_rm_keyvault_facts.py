#!/usr/bin/python
#
# Copyright (c) 2017 Obezimnaka Boms, <t-ozboms@microsoft.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: azure_rm_keyvault_facts

version_added: "2.5"

short_description: Get key vault facts.

description:
    - Get facts for a specific key vault or all key vaults within a resource group.

options:
    resource_group:
        description:
            - Limit results by resource group. Required when filtering by name.
    name:
        description:
            - Only show results for a specific key vault.
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.
    top:
        description:
            - Maximum number of results to return.

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Obezimnaka Boms @ozboms"

'''

EXAMPLES = '''
    - name: Get facts for one key vault
      azure_rm_keyvault_facts:
        resource_group: Testing
        name: foobar22

    - name: Get facts for all zones in a resource group
      azure_rm_keyvault_facts:
        resource_group: Testing
        top: 50

    - name: Get facts by tags
      azure_rm_keyvault_facts:
        tags:
          - testing
'''

RETURN = '''
azure_keyvault:
    description: List of key vault dicts.
    returned: always
    type: list
    example:  []
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.common import AzureMissingResourceHttpError, AzureHttpError
    from azure.mgmt.keyvault.models import ResourcePaged
except:
    # This is handled in azure_rm_common
    pass

AZURE_OBJECT_CLASS = 'KeyVault'


class AzureRMKeyVaultFacts(AzureRMModuleBase):

    def __init__(self):

        # define user inputs into argument
        self.module_arg_spec = dict(
            name=dict(type='str'),
            resource_group=dict(type='str'),
            tags=dict(type='list'),
            top=dict(type='int')
        )

        # store the results of the module operation
        self.results = dict(
            changed=False,
            ansible_facts=dict(azure_keyvault=[])
        )

        self.name = None
        self.resource_group = None
        self.tags = None
        self.top = None

        super(AzureRMKeyVaultFacts, self).__init__(self.module_arg_spec)

    def exec_module(self, **kwargs):

        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        if self.name and not self.resource_group:
            self.fail("Parameter error: resource group required when filtering by name.")

        # list the conditions and what to return based on user input

        if self.name is not None:
            # specific key vault
            self.results['ansible_facts']['azure_keyvault'] = self.get_item()
        elif self.resource_group:
            # all the key vaults listed in that specific resource group
            self.results['ansible_facts']['azure_keyvault'] = self.list_resource_group()
        else:
            # all the key vaults in a subscription
            self.results['ansible_facts']['azure_keyvault'] = self.list_items()

        return self.results

    def get_item(self):
        self.log('Get properties for {0}'.format(self.name))
        item = None
        results = []
        # get specific key vault
        try:
            item = self.keyvault_client.vaults.get(self.resource_group, self.name)
        except CloudError:
            pass

        # serialize result
        if item and self.has_tags(item.tags, self.tags):
            results = [item.as_dict()]
        return results

    def list_resource_group(self):
        self.log('List items for resource group')
        try:
            response = self.keyvault_client.vaults.list_by_resource_group(self.resource_group, top=self.top)
        except AzureHttpError as exc:
            self.fail("Failed to list for resource group {0} - {1}".format(self.resource_group, str(exc)))

        results = [r.as_dict() for r in response if self.has_tags(r.tags, self.tags)]
        # for item in response:
        #     if self.has_tags(item.tags, self.tags):
        #         results.append(item.as_dict())
        return results

    def list_items(self):
        self.log('List all items')
        try:
            response = self.keyvault_client.vaults.list(top=self.top)
        except AzureHttpError as exc:
            self.fail("Failed to list all items - {0}".format(str(exc)))

        results = [r.as_dict() for r in response if self.has_tags(r.tags, self.tags)]
        # for item in response:
        #     if self.has_tags(item.tags, self.tags):
        #         results.append(self.serialize_obj(item, AZURE_OBJECT_CLASS))
        return results


def main():
    AzureRMKeyVaultFacts()

if __name__ == '__main__':
    main()
