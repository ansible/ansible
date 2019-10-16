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
module: azure_rm_devtestlabvirtualmachine_facts
version_added: "2.8"
short_description: Get Azure DevTest Lab Virtual Machine facts.
description:
    - Get facts of Azure DevTest Lab Virtual Machine.

options:
    resource_group:
        description:
            - The name of the resource group.
        required: True
    lab_name:
        description:
            - The name of the lab.
        required: True
    name:
        description:
            - The name of the virtual machine.
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.

extends_documentation_fragment:
    - azure

author:
    - "Zim Kalinowski (@zikalino)"

'''

EXAMPLES = '''
  - name: Get instance of DTL Virtual Machine
    azure_rm_devtestlabvirtualmachine_facts:
      resource_group: myResourceGroup
      lab_name: myLab
      name: myVm
'''

RETURN = '''
virtualmachines:
    description: A list of dictionaries containing facts for DevTest Lab Virtual Machine.
    returned: always
    type: complex
    contains:
        id:
            description:
                - The identifier of the virtual machine.
            returned: always
            type: str
            sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourcegroups/myResourceGroup/providers/microsoft.devtestlab/labs/myLab/virt
                     ualmachines/myVm"
        resource_group:
            description:
                - Name of the resource group.
            returned: always
            type: str
            sample: myResourceGroup
        lab_name:
            description:
                - Name of the lab.
            returned: always
            type: str
            sample: myLab
        name:
            description:
                - Name of the virtual machine.
            returned: always
            type: str
            sample: myVm
        notes:
            description:
                - Notes of the virtual machine.
            returned: always
            type: str
            sample: My VM notes
        disallow_public_ip_address:
            description:
                - Whether public IP should be not allowed.
            returned: always
            type: bool
            sample: false
        expiration_date:
            description:
                - Virtual machine expiration date.
            returned: always
            type: str
            sample: "2029-02-22T01:49:12.117974Z"
        image:
            description:
                - Gallery image reference.
            returned: always
            type: complex
            contains:
                offer:
                    description:
                        - Offer.
                    returned: when created from gallery image
                    type: str
                    sample: UbuntuServer
                os_type:
                    description:
                        - Operating system type.
                    returned: when created from gallery image
                    type: str
                    sample: Linux
                sku:
                    description:
                        - SKU.
                    returned: when created from gallery image
                    type: str
                    sample: 16.04-LTS
                publisher:
                    description:
                        - Publisher.
                    returned: when created from gallery image
                    type: str
                    sample: Canonical
                version:
                    description:
                        - Version.
                    returned: when created from gallery image
                    type: str
                    sample: latest
        os_type:
            description:
                - Operating system type.
            returned: always
            type: str
            sample: linux
        vm_size:
            description:
                - Virtual machine size.
            returned: always
            type: str
            sample: Standard_A2_v2
        user_name:
            description:
                - Admin user name.
            returned: always
            type: str
            sample: dtl_admin
        storage_type:
            description:
                - Storage type.
            returned: always
            type: str
            sample: standard
        compute_vm_id:
            description:
                - Resource id of compute virtual machine.
            returned: always
            type: str
            sample: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myLab-myVm-097933/providers/Microsoft.Compute/virtualMachines/myVm
        compute_vm_resource_group:
            description:
                - Resource group where compute virtual machine is created.
            returned: always
            type: str
            sample: myLab-myVm-097933
        compute_vm_name:
            description:
                - Name of compute virtual machine.
            returned: always
            type: str
            sample: myVm
        fqdn:
            description:
                - Fully qualified domain name.
            returned: always
            type: str
            sample: myvm.eastus.cloudapp.azure.com
        provisioning_state:
            description:
                - Provisioning state of the virtual network.
            returned: always
            type: str
            sample: Succeeded
        tags:
            description:
                - Tags
            returned: always
            type: complex
            sample: "{ 'foo': 'bar' }"
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.devtestlabs import DevTestLabsClient
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMDtlVirtualMachineFacts(AzureRMModuleBase):
    def __init__(self):
        # define user inputs into argument
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                required=True
            ),
            lab_name=dict(
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
        self.mgmt_client = None
        self.resource_group = None
        self.lab_name = None
        self.name = None
        self.tags = None
        super(AzureRMDtlVirtualMachineFacts, self).__init__(self.module_arg_spec, supports_tags=False)

    def exec_module(self, **kwargs):
        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])
        self.mgmt_client = self.get_mgmt_svc_client(DevTestLabsClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        if self.name:
            self.results['virtualmachines'] = self.get()
        else:
            self.results['virtualmachines'] = self.list()

        return self.results

    def get(self):
        response = None
        results = []
        try:
            response = self.mgmt_client.virtual_machines.get(resource_group_name=self.resource_group,
                                                             lab_name=self.lab_name,
                                                             name=self.name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.fail('Could not get facts for Virtual Machine.')

        if response and self.has_tags(response.tags, self.tags):
            results.append(self.format_response(response))

        return results

    def list(self):
        response = None
        results = []
        try:
            response = self.mgmt_client.virtual_machines.list(resource_group_name=self.resource_group,
                                                              lab_name=self.lab_name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.fail('Could not get facts for Virtual Machine.')

        if response is not None:
            for item in response:
                if self.has_tags(item.tags, self.tags):
                    results.append(self.format_response(item))
        return results

    def format_response(self, item):
        d = item.as_dict()
        d = {
            'id': d.get('id', None),
            'resource_group': self.parse_resource_to_dict(d.get('id')).get('resource_group'),
            'lab_name': self.parse_resource_to_dict(d.get('id')).get('name'),
            'name': d.get('name'),
            'notes': d.get('notes'),
            'disallow_public_ip_address': d.get('disallow_public_ip_address'),
            'expiration_date': d.get('expiration_date'),
            'image': d.get('gallery_image_reference'),
            'os_type': d.get('os_type').lower(),
            'vm_size': d.get('size'),
            'user_name': d.get('user_name'),
            'storage_type': d.get('storage_type').lower(),
            'compute_vm_id': d.get('compute_id'),
            'compute_vm_resource_group': self.parse_resource_to_dict(d.get('compute_id')).get('resource_group'),
            'compute_vm_name': self.parse_resource_to_dict(d.get('compute_id')).get('name'),
            'fqdn': d.get('fqdn'),
            'provisioning_state': d.get('provisioning_state'),
            'tags': d.get('tags', None)
        }
        return d


def main():
    AzureRMDtlVirtualMachineFacts()


if __name__ == '__main__':
    main()
