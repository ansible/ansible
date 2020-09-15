#!/usr/bin/python
#
# Copyright (c) 2016 Matt Davis, <mdavis@ansible.com>
#                    Chris Houseknecht, <house@redhat.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_resourcegroup_info

version_added: "2.1"

short_description: Get resource group facts

description:
    - Get facts for a specific resource group or all resource groups.

options:
    name:
        description:
            - Limit results to a specific resource group.
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.
    list_resources:
        description:
            - List all resources under the resource group.
            - Note this will cost network overhead for each resource group. Suggest use this when I(name) set.
        version_added: "2.8"

extends_documentation_fragment:
    - azure

author:
    - Chris Houseknecht (@chouseknecht)
    - Matt Davis (@nitzmahone)

'''

EXAMPLES = '''
    - name: Get facts for one resource group
      azure_rm_resourcegroup_info:
        name: myResourceGroup

    - name: Get facts for all resource groups
      azure_rm_resourcegroup_info:

    - name: Get facts by tags
      azure_rm_resourcegroup_info:
        tags:
          - testing
          - foo:bar

    - name: Get facts for one resource group including resources it contains
      azure_rm_resourcegroup_info:
        name: myResourceGroup
        list_resources: yes
'''
RETURN = '''
azure_resourcegroups:
    description:
        - List of resource group dicts.
    returned: always
    type: list
    contains:
        id:
            description:
                - Resource id.
            returned: always
            type: str
            sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroup/myResourceGroup"
        name:
            description:
                - Resource group name.
            returned: always
            type: str
            sample: foo
        tags:
            description:
                - Tags assigned to resource group.
            returned: always
            type: dict
            sample: { "tag": "value" }
        resources:
            description:
                - List of resources under the resource group.
            returned: when I(list_resources=yes).
            type: list
            contains:
                id:
                    description:
                        - Resource id.
                    returned: always
                    type: str
                    sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Compute/virtualMa
                             chines/myVirtualMachine"
                name:
                    description:
                        - Resource name.
                    returned: always
                    type: str
                    sample: myVirtualMachine
                location:
                    description:
                        - Resource region.
                    returned: always
                    type: str
                    sample: eastus
                type:
                    description:
                        - Resource type.
                    returned: always
                    type: str
                    sample: "Microsoft.Compute/virtualMachines"
                tags:
                    description:
                        - Tags to assign to the managed disk.
                    returned: always
                    type: dict
                    sample: { "tag": "value" }
'''

try:
    from msrestazure.azure_exceptions import CloudError
except Exception:
    # This is handled in azure_rm_common
    pass

from ansible.module_utils.azure_rm_common import AzureRMModuleBase


AZURE_OBJECT_CLASS = 'ResourceGroup'


class AzureRMResourceGroupInfo(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            name=dict(type='str'),
            tags=dict(type='list'),
            list_resources=dict(type='bool')
        )

        self.results = dict(
            changed=False,
            resourcegroups=[]
        )

        self.name = None
        self.tags = None
        self.list_resources = None

        super(AzureRMResourceGroupInfo, self).__init__(self.module_arg_spec,
                                                       supports_tags=False,
                                                       facts_module=True)

    def exec_module(self, **kwargs):
        is_old_facts = self.module._name == 'azure_rm_resourcegroup_facts'
        if is_old_facts:
            self.module.deprecate("The 'azure_rm_resourcegroup_facts' module has been renamed to 'azure_rm_resourcegroup_info'", version='2.13')

        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        if self.name:
            result = self.get_item()
        else:
            result = self.list_items()

        if self.list_resources:
            for item in result:
                item['resources'] = self.list_by_rg(item['name'])

        if is_old_facts:
            self.results['ansible_facts'] = dict(
                azure_resourcegroups=result
            )
        self.results['resourcegroups'] = result

        return self.results

    def get_item(self):
        self.log('Get properties for {0}'.format(self.name))
        item = None
        result = []

        try:
            item = self.rm_client.resource_groups.get(self.name)
        except CloudError:
            pass

        if item and self.has_tags(item.tags, self.tags):
            result = [self.serialize_obj(item, AZURE_OBJECT_CLASS)]

        return result

    def list_items(self):
        self.log('List all items')
        try:
            response = self.rm_client.resource_groups.list()
        except CloudError as exc:
            self.fail("Failed to list all items - {0}".format(str(exc)))

        results = []
        for item in response:
            if self.has_tags(item.tags, self.tags):
                results.append(self.serialize_obj(item, AZURE_OBJECT_CLASS))
        return results

    def list_by_rg(self, name):
        self.log('List resources under resource group')
        results = []
        try:
            response = self.rm_client.resources.list_by_resource_group(name)
            while True:
                results.append(response.next().as_dict())
        except StopIteration:
            pass
        except CloudError as exc:
            self.fail('Error when listing resources under resource group {0}: {1}'.format(name, exc.message or str(exc)))
        return results


def main():
    AzureRMResourceGroupInfo()


if __name__ == '__main__':
    main()
