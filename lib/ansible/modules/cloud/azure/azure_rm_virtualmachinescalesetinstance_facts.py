#!/usr/bin/python
#
# Copyright (c) 2019 Zim Kalinowski, <zikalino@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_virtualmachinescalesetinstance_facts
version_added: "2.8"
short_description: Get Azure Virtual Machine Scale Set Instance facts.
description:
    - Get facts of Azure Virtual Machine Scale Set VMs.

options:
    resource_group:
        description:
            - The name of the resource group.
        required: True
    vmss_name:
        description:
            - The name of the VM scale set.
        required: True
    instance_id:
        description:
            - The instance ID of the virtual machine.
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.

extends_documentation_fragment:
    - azure

author:
    - "Zim Kalinowski (@zikalino)"

'''

EXAMPLES = '''
  - name: List VM instances in Virtual Machine ScaleSet
    azure_rm_computevirtualmachinescalesetinstance_facts:
      resource_group: myResourceGroup
      vmss_name: myVMSS
'''

RETURN = '''
instances:
    description: A list of dictionaries containing facts for Virtual Machine Scale Set VM.
    returned: always
    type: complex
    contains:
        id:
            description:
                - Resource Id
            returned: always
            type: str
            sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Compute/virtualMachineScaleSets/my
                     VMSS/virtualMachines/2"
        tags:
            description:
                - Resource tags
            returned: always
            type: complex
            sample: { 'tag1': 'abc' }
        instance_id:
            description:
                - Virtual Machine instance Id
            returned: always
            type: str
            sample: 0
        name:
            description:
                - Virtual Machine name
            returned: always
            type: str
            sample: myVMSS_2
        latest_model:
            description:
                - Is latest model applied?
            returned: always
            type: bool
            sample: True
        provisioning_state:
            description:
                - Provisioning state of the Virtual Machine
            returned: always
            type: str
            sample: Succeeded
        power_state:
            description:
                - Provisioning state of the Virtual Machine
            returned: always
            type: str
            sample: running
        vm_id:
            description:
                - Virtual Machine Id
            returned: always
            type: str
            sample: 94a141a9-4530-46ac-b151-2c7ff09aa823
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.compute import ComputeManagementClient
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMVirtualMachineScaleSetVMFacts(AzureRMModuleBase):
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
            instance_id=dict(
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
        self.vmss_name = None
        self.instance_id = None
        self.tags = None
        super(AzureRMVirtualMachineScaleSetVMFacts, self).__init__(self.module_arg_spec, supports_tags=False)

    def exec_module(self, **kwargs):
        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])
        self.mgmt_client = self.get_mgmt_svc_client(ComputeManagementClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        if (self.instance_id is None):
            self.results['instances'] = self.list()
        else:
            self.results['instances'] = self.get()
        return self.results

    def get(self):
        response = None
        results = []
        try:
            response = self.mgmt_client.virtual_machine_scale_set_vms.get(resource_group_name=self.resource_group,
                                                                          vm_scale_set_name=self.vmss_name,
                                                                          instance_id=self.instance_id)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for Virtual Machine Scale Set VM.')

        if response and self.has_tags(response.tags, self.tags):
            results.append(self.format_response(response))

        return results

    def list(self):
        items = None
        try:
            items = self.mgmt_client.virtual_machine_scale_set_vms.list(resource_group_name=self.resource_group,
                                                                        virtual_machine_scale_set_name=self.vmss_name)
            self.log("Response : {0}".format(items))
        except CloudError as e:
            self.log('Could not get facts for Virtual Machine ScaleSet VM.')

        results = []
        for item in items:
            if self.has_tags(item.tags, self.tags):
                results.append(self.format_response(item))
        return results

    def format_response(self, item):
        d = item.as_dict()

        iv = self.mgmt_client.virtual_machine_scale_set_vms.get_instance_view(resource_group_name=self.resource_group,
                                                                              vm_scale_set_name=self.vmss_name,
                                                                              instance_id=d.get('instance_id', None)).as_dict()
        power_state = ""
        for index in range(len(iv['statuses'])):
            code = iv['statuses'][index]['code'].split('/')
            if code[0] == 'PowerState':
                power_state = code[1]
                break
        d = {
            'resource_group': self.resource_group,
            'id': d.get('id', None),
            'tags': d.get('tags', None),
            'instance_id': d.get('instance_id', None),
            'latest_model': d.get('latest_model_applied', None),
            'name': d.get('name', None),
            'provisioning_state': d.get('provisioning_state', None),
            'power_state': power_state,
            'vm_id': d.get('vm_id', None)
        }
        return d


def main():
    AzureRMVirtualMachineScaleSetVMFacts()


if __name__ == '__main__':
    main()
