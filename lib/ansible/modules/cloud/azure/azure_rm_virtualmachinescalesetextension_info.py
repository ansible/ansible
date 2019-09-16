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
module: azure_rm_virtualmachinescalesetextension_info
version_added: "2.9"
short_description: Get Azure Virtual Machine Scale Set Extension facts
description:
    - Get facts of Azure Virtual Machine Scale Set Extension.

options:
    resource_group:
        description:
            - The name of the resource group.
        required: True
    vmss_name:
        description:
            - The name of VMSS containing the extension.
        required: True
    name:
        description:
            - The name of the virtual machine extension.

extends_documentation_fragment:
    - azure

author:
    - Zim Kalinowski (@zikalino)

'''

EXAMPLES = '''
  - name: Get information on specific Virtual Machine Scale Set Extension
    azure_rm_virtualmachineextension_info:
      resource_group: myResourceGroup
      vmss_name: myvmss
      name: myextension

  - name: List installed Virtual Machine Scale Set Extensions
    azure_rm_virtualmachineextension_info:
      resource_group: myrg
      vmss_name: myvmss
'''

RETURN = '''
extensions:
    description:
        - A list of dictionaries containing facts for Virtual Machine Extension.
    returned: always
    type: complex
    contains:
        id:
            description:
                - Resource ID.
            returned: always
            type: str
            sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Compute/virtualMachineScaleSets/
                     myvmss/extensions/myextension"
        resource_group:
            description:
                - Resource group name.
            returned: always
            type: str
            sample: myrg
        vmss_name:
            description:
                - Virtual machine scale set name.
            returned: always
            type: str
            sample: myvmss
        name:
            description:
                - Virtual machine extension name.
            returned: always
            type: str
            sample: myextension
        publisher:
            description:
                - Extension publisher.
            returned: always
            type: str
            sample: Microsoft.Azure.Extensions
        type:
            description:
                - Extension type.
            returned: always
            type: str
            sample: CustomScript
        settings:
            description:
                - Extension specific settings dictionary.
            returned: always
            type: dict
            sample: { 'commandToExecute':'hostname' }
        auto_upgrade_minor_version:
            description:
                - Autoupgrade minor version flag.
            returned: always
            type: bool
            sample: true
        provisioning_state:
            description:
                - Provisioning state of the extension.
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


class AzureRMVirtualMachineScaleSetExtensionInfo(AzureRMModuleBase):
    def __init__(self):
        # define user inputs into argument
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                required=True
            ),
            vmss_name=dict(
                type='str',
                required=True
            ),
            name=dict(
                type='str'
            )
        )
        # store the results of the module operation
        self.results = dict(
            changed=False
        )
        self.resource_group = None
        self.vmss_name = None
        self.name = None
        super(AzureRMVirtualMachineScaleSetExtensionInfo, self).__init__(self.module_arg_spec, supports_tags=False)

    def exec_module(self, **kwargs):
        is_old_facts = self.module._name == 'azure_rm_virtualmachinescalesetextension_facts'
        if is_old_facts:
            self.module.deprecate("The 'azure_rm_virtualmachinescalesetextension_facts' module has been renamed to" +
                                  " 'azure_rm_virtualmachinescalesetextension_info'",
                                  version='2.13')

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
            response = self.compute_client.virtual_machine_scale_set_extensions.get(resource_group_name=self.resource_group,
                                                                                    vm_scale_set_name=self.vmss_name,
                                                                                    vmss_extension_name=self.name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for Virtual Machine Extension.')

        if response:
            results.append(self.format_response(response))

        return results

    def list_extensions(self):
        response = None
        results = []
        try:
            response = self.compute_client.virtual_machine_scale_set_extensions.list(resource_group_name=self.resource_group,
                                                                                     vm_scale_set_name=self.vmss_name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for Virtual Machine Extension.')

        if response is not None:
            for item in response:
                results.append(self.format_response(item))

        return results

    def format_response(self, item):
        id_template = "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Compute/virtualMachineScaleSets/{2}/extensions/{3}"
        d = item.as_dict()
        d = {
            'id': id_template.format(self.subscription_id, self.resource_group, self.vmss_name, d.get('name')),
            'resource_group': self.resource_group,
            'vmss_name': self.vmss_name,
            'name': d.get('name'),
            'publisher': d.get('publisher'),
            'type': d.get('type'),
            'settings': d.get('settings'),
            'auto_upgrade_minor_version': d.get('auto_upgrade_minor_version'),
            'provisioning_state': d.get('provisioning_state')
        }
        return d


def main():
    AzureRMVirtualMachineScaleSetExtensionInfo()


if __name__ == '__main__':
    main()
