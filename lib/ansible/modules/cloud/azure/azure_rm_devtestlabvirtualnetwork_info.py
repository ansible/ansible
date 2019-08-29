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
module: azure_rm_devtestlabvirtualnetwork_info
version_added: "2.9"
short_description: Get Azure DevTest Lab Virtual Network facts
description:
    - Get facts of Azure DevTest Lab Virtual Network.

options:
    resource_group:
        description:
            - The name of the resource group.
        required: True
        type: str
    lab_name:
        description:
            - The name of DevTest Lab.
        required: True
        type: str
    name:
        description:
            - The name of DevTest Lab Virtual Network.
        type: str

extends_documentation_fragment:
    - azure

author:
    - Zim Kalinowski (@zikalino)

'''

EXAMPLES = '''
  - name: Get instance of DevTest Lab Virtual Network
    azure_rm_devtestlabvirtualnetwork_info:
      resource_group: myResourceGroup
      lab_name: myLab
      name: myVirtualNetwork

  - name: List all Virtual Networks in DevTest Lab
    azure_rm_devtestlabvirtualnetwork_info:
      resource_group: myResourceGroup
      lab_name: myLab
      name: myVirtualNetwork
'''

RETURN = '''
virtualnetworks:
    description:
        - A list of dictionaries containing facts for DevTest Lab Virtual Network.
    returned: always
    type: complex
    contains:
        id:
            description:
                - The identifier of the virtual network.
            returned: always
            type: str
            sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourcegroups/myResourceGroup/providers/microsoft.devtestlab/labs/myLab/virt
                     ualnetworks/myVirtualNetwork"
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
                - Name of the virtual network.
            returned: always
            type: str
            sample: myVirtualNetwork
        description:
            description:
                - Description of the virtual network.
            returned: always
            type: str
            sample: My Virtual Network
        external_provider_resource_id:
            description:
                - Resource id of an external virtual network.
            returned: always
            type: str
            sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Network/virtualNetworks/my
                     VirtualNetwork"
        provisioning_state:
            description:
                - Provisioning state of the virtual network.
            returned: always
            type: str
            sample: Succeeded
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.devtestlabs import DevTestLabsClient
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMDevTestLabVirtualNetworkInfo(AzureRMModuleBase):
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
        super(AzureRMDevTestLabVirtualNetworkInfo, self).__init__(self.module_arg_spec, supports_tags=False)

    def exec_module(self, **kwargs):
        is_old_facts = self.module._name == 'azure_rm_devtestlabvirtualnetwork_facts'
        if is_old_facts:
            self.module.deprecate("The 'azure_rm_devtestlabvirtualnetwork_facts' module has been renamed to 'azure_rm_devtestlabvirtualnetwork_info'",
                                  version='2.13')

        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])
        self.mgmt_client = self.get_mgmt_svc_client(DevTestLabsClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        if self.name:
            self.results['virtualnetworks'] = self.get()
        else:
            self.results['virtualnetworks'] = self.list()

        return self.results

    def list(self):
        response = None
        results = []
        try:
            response = self.mgmt_client.virtual_networks.list(resource_group_name=self.resource_group,
                                                              lab_name=self.lab_name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.fail('Could not list Virtual Networks for DevTest Lab.')

        if response is not None:
            for item in response:
                results.append(self.format_response(item))

        return results

    def get(self):
        response = None
        results = []
        try:
            response = self.mgmt_client.virtual_networks.get(resource_group_name=self.resource_group,
                                                             lab_name=self.lab_name,
                                                             name=self.name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.fail('Could not get facts for Virtual Network.')

        if response:
            results.append(self.format_response(response))

        return results

    def format_response(self, item):
        d = item.as_dict()
        d = {
            'resource_group': self.resource_group,
            'lab_name': self.lab_name,
            'name': d.get('name', None),
            'id': d.get('id', None),
            'external_provider_resource_id': d.get('external_provider_resource_id', None),
            'provisioning_state': d.get('provisioning_state', None),
            'description': d.get('description', None)
        }
        return d


def main():
    AzureRMDevTestLabVirtualNetworkInfo()


if __name__ == '__main__':
    main()
