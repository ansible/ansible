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
module: azure_rm_computevirtualmachinescalesetextension_facts
version_added: "2.8"
short_description: Get Azure Virtual Machine Scale Set Extension facts.
description:
    - Get facts of Azure Virtual Machine Scale Set Extension.

options:
    resource_group:
        description:
            - The name of the resource group.
        required: True
    vm_scale_set_name:
        description:
            - The name of the VM scale set containing the extension.
        required: True
    name:
        description:
            - The name of the VM scale set extension.
        required: True
    expand:
        description:
            - The expand expression to apply on the operation.

extends_documentation_fragment:
    - azure

author:
    - "Zim Kalinowski (@zikalino)"

'''

EXAMPLES = '''
  - name: Get instance of Virtual Machine Scale Set Extension
    azure_rm_computevirtualmachinescalesetextension_facts:
      resource_group: resource_group_name
      vm_scale_set_name: vm_scale_set_name
      name: vmss_extension_name
      expand: expand
'''

RETURN = '''
virtual_machine_scale_set_extensions:
    description: A list of dictionaries containing facts for Virtual Machine Scale Set Extension.
    returned: always
    type: complex
    contains:
        id:
            description:
                - Resource Id
            returned: always
            type: str
            sample: id
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.compute import ComputeManagementClient
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMVirtualMachineScaleSetExtensionFacts(AzureRMModuleBase):
    def __init__(self):
        # define user inputs into argument
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                required=True
            ),
            vm_scale_set_name=dict(
                type='str',
                required=True
            ),
            name=dict(
                type='str',
                required=True
            ),
            expand=dict(
                type='str'
            )
        )
        # store the results of the module operation
        self.results = dict(
            changed=False
        )
        self.mgmt_client = None
        self.resource_group = None
        self.vm_scale_set_name = None
        self.name = None
        self.expand = None
        super(AzureRMVirtualMachineScaleSetExtensionFacts, self).__init__(self.module_arg_spec, supports_tags=False)

    def exec_module(self, **kwargs):
        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])
        self.mgmt_client = self.get_mgmt_svc_client(ComputeManagementClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        self.results['virtual_machine_scale_set_extensions'] = self.get()
        return self.results

    def get(self):
        response = None
        results = []
        try:
            response = self.mgmt_client.virtual_machine_scale_set_extensions.get(resource_group_name=self.resource_group,
                                                                                 vm_scale_set_name=self.vm_scale_set_name,
                                                                                 vmss_extension_name=self.name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for Virtual Machine Scale Set Extension.')

        if response is not None:
            results.append(self.format_response(response))

        return results

    def format_response(self, item):
        d = item.as_dict()
        d = {
            'resource_group': self.resource_group,
            'id': d.get('id', None)
        }
        return d


def main():
    AzureRMVirtualMachineScaleSetExtensionFacts()


if __name__ == '__main__':
    main()
