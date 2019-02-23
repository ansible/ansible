#!/usr/bin/python
#
# Copyright (c) 2018 Zim Kalinowski, (@zikalino)
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_virtualmachineextension_facts
version_added: "2.8"
short_description: Get Azure Virtual Machine Extension facts.
description:
    - Get facts of Azure Virtual Machine Extension.

options:
    resource_group:
        description:
            - The name of the resource group.
        required: True
    virtual_machine_name:
        description:
            - The name of the virtual machine containing the extension.
        required: True
    name:
        description:
            - The name of the virtual machine extension.
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.

extends_documentation_fragment:
    - azure

author:
    - "Zim Kalinowski (@zikalino)"

'''

EXAMPLES = '''
  - name: Get information on specific Virtual Machine Extension
    azure_rm_virtualmachineextension_facts:
      resource_group: myResourceGroup
      virtual_machine_name: myvm
      name: myextension

  - name: List installed Virtual Machine Extensions
    azure_rm_virtualmachineextension_facts:
      resource_group: myResourceGroup
      virtual_machine_name: myvm
'''

RETURN = '''
extensions:
    description: A list of dictionaries containing facts for Virtual Machine Extension.
    returned: always
    type: complex
    contains:
        id:
            description:
                - Resource Id
            returned: always
            type: str
            sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Compute/myvm/testVM/extens
                     ions/myextension"
        resource_group:
            description:
                - Resource group name
            returned: always
            type: str
            sample: myResourceGroup
        virtual_machine_name:
            description:
                - Virtual machine name
            returned: always
            type: str
            sample: myvm
        name:
            description:
                - Virtual machine name
            returned: always
            type: str
            sample: myextension
        location:
            description:
                - Location
            returned: always
            type: str
            sample: eastus
        publisher:
            description:
                - Extension publisher
            returned: always
            type: str
            sample: Microsoft.Azure.Extensions
        type:
            description:
                - Extension type
            returned: always
            type: str
            sample: CustomScript
        settings:
            description:
                - Extension specific settings dictionary
            returned: always
            type: complex
            sample: "{'commandToExecute': 'hostname'}"
        auto_upgrade_minor_version:
            description:
                - Autoupgrade minor version flag
            returned: always
            type: bool
            sample: true
        tags:
            description:
                - Resource tags
            returned: always
            type: complex
            sample: "{ mytag: abc }"
        provisioning_state:
            description:
                - Provisioning state of the extension
            returned: always
            type: str
            sample: Succeeded
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMVirtualMachineExtensionFacts(AzureRMModuleBase):
    def __init__(self):
        # define user inputs into argument
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                required=True
            ),
            virtual_machine_name=dict(
                type='str',
                required=True
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
        self.resource_group = None
        self.virtual_machine_name = None
        self.name = None
        self.tags = None
        super(AzureRMVirtualMachineExtensionFacts, self).__init__(self.module_arg_spec, supports_tags=False)

    def exec_module(self, **kwargs):
        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        if self.name is not None:
            self.results['extensions'] = self.get_extensions()
        else:
            self.results['extensions'] = self.list_extensions()

        return self.results

    def get_extensions(self):
        response = None
        results = []
        try:
            response = self.compute_client.virtual_machine_extensions.get(resource_group_name=self.resource_group,
                                                                          vm_name=self.virtual_machine_name,
                                                                          vm_extension_name=self.name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for Virtual Machine Extension.')

        if response and self.has_tags(response.tags, self.tags):
            results.append(self.format_response(response))

        return results

    def list_extensions(self):
        response = None
        results = []
        try:
            response = self.compute_client.virtual_machine_extensions.list(resource_group_name=self.resource_group,
                                                                           vm_name=self.virtual_machine_name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for Virtual Machine Extension.')

        if response is not None and response.value is not None:
            for item in response.value:
                if self.has_tags(item.tags, self.tags):
                    results.append(self.format_response(item))

        return results

    def format_response(self, item):
        d = item.as_dict()
        d = {
            'id': d.get('id', None),
            'resource_group': self.resource_group,
            'virtual_machine_name': self.virtual_machine_name,
            'location': d.get('location'),
            'name': d.get('name'),
            'publisher': d.get('publisher'),
            'type': d.get('virtual_machine_extension_type'),
            'settings': d.get('settings'),
            'auto_upgrade_minor_version': d.get('auto_upgrade_minor_version'),
            'tags': d.get('tags', None),
            'provisioning_state': d.get('provisioning_state')
        }
        return d


def main():
    AzureRMVirtualMachineExtensionFacts()


if __name__ == '__main__':
    main()
