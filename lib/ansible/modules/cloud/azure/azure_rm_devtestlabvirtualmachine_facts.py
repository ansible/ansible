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
        required: True
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
virtual_machines:
    description: A list of dictionaries containing facts for Virtual Machine.
    returned: always
    type: complex
    contains:
        id:
            description:
                - The identifier of the resource.
            returned: always
            type: str
            sample: id
        tags:
            description:
                - The tags of the resource.
            returned: always
            type: complex
            sample: tags
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.devtestlabs import DevTestLabsClient
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMVirtualMachineFacts(AzureRMModuleBase):
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
                type='str',
                required=True
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
        super(AzureRMVirtualMachineFacts, self).__init__(self.module_arg_spec, supports_tags=False)

    def exec_module(self, **kwargs):
        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])
        self.mgmt_client = self.get_mgmt_svc_client(DevTestLabsClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        self.results['virtual_machines'] = self.get()
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
            self.log('Could not get facts for Virtual Machine.')

        if response and self.has_tags(response.tags, self.tags):
            results.append(self.format_response(response))

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
            'image': d.get('gallery_image'),
            'os_type': d.get('os_type').lower(),
            'vm_size': d.get('size'),
            'user_name': d.get('size'),
            'storage_type': d.get('storage_type').lower(),
            'compute_id': d.get('compute_id'),
            'fqdn': d.get('fqdn'),
            'provisioning_state': d.get('provisioning_state'),
            'tags': d.get('tags', None)
        }
        return d


def main():
    AzureRMVirtualMachineFacts()


if __name__ == '__main__':
    main()
