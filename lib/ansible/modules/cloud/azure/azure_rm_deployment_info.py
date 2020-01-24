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
module: azure_rm_deployment_info
version_added: "2.9"
short_description: Get Azure Deployment facts
description:
    - Get facts of Azure Deployment.

options:
    resource_group:
        description:
            - The name of the resource group.
        required: True
    name:
        description:
            - The name of the deployment.

extends_documentation_fragment:
    - azure

author:
    - Zim Kalinowski (@zikalino)

'''

EXAMPLES = '''
  - name: Get instance of Deployment
    azure_rm_deployment_info:
      resource_group: myResourceGroup
      name: myDeployment
'''

RETURN = '''
deployments:
    description:
        - A list of dictionaries containing facts for deployments.
    returned: always
    type: complex
    contains:
        id:
            description:
                - The identifier of the resource.
            returned: always
            type: str
            sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Resources/deployments/myDeployment"
        resource_group:
            description:
                - Resource group name.
            returned: always
            sample: myResourceGroup
        name:
            description:
                - Deployment name.
            returned: always
            sample: myDeployment
        provisioning_state:
            description:
                - Provisioning state of the deployment.
            returned: always
            sample: Succeeded
        template_link:
            description:
                - Link to the template.
            returned: always
            sample: "https://raw.githubusercontent.com/Azure/azure-quickstart-templates/d01a5c06f4f1bc03a049ca17bbbd6e06d62657b3/101-vm-simple-linux/
                     azuredeploy.json"
        parameters:
            description:
                - Dictionary containing deployment parameters.
            returned: always
            type: complex
        outputs:
            description:
                - Dictionary containing deployment outputs.
            returned: always
        output_resources:
            description:
                - List of resources.
            returned: always
            type: complex
            contains:
                id:
                    description:
                        - Resource id.
                    returned: always
                    type: str
                    sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Network/networkI
                             nterfaces/myNetworkInterface"
                name:
                    description:
                        - Resource name.
                    returned: always
                    type: str
                    sample: myNetworkInterface
                type:
                    description:
                        - Resource type.
                    returned: always
                    type: str
                    sample: Microsoft.Network/networkInterfaces
                depends_on:
                    description:
                        - List of resource ids.
                    type: list
                    returned: always
                    sample:
                        - "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGropup/providers/Microsoft.Network/virtualNet
                           works/myVirtualNetwork"
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.devtestlabs import DevTestLabsClient
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMDeploymentInfo(AzureRMModuleBase):
    def __init__(self):
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                required=True
            ),
            name=dict(
                type='str'
            )
        )
        self.results = dict(
            changed=False
        )
        self.resource_group = None
        self.name = None

        super(AzureRMDeploymentInfo, self).__init__(self.module_arg_spec, supports_tags=False)

    def exec_module(self, **kwargs):

        is_old_facts = self.module._name == 'azure_rm_deployment_facts'
        if is_old_facts:
            self.module.deprecate("The 'azure_rm_deployment_facts' module has been renamed to 'azure_rm_deployment_info'", version='2.13')

        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        if self.name:
            self.results['deployments'] = self.get()
        else:
            self.results['deployments'] = self.list()

        return self.results

    def get(self):
        response = None
        results = []
        try:
            response = self.rm_client.deployments.get(self.resource_group, deployment_name=self.name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for Deployment.')

        if response:
            results.append(self.format_response(response))

        return results

    def list(self):
        response = None
        results = []
        try:
            response = self.rm_client.deployments.list(self.resource_group)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for Deployment.')

        if response is not None:
            for item in response:
                results.append(self.format_response(item))

        return results

    def format_response(self, item):
        d = item.as_dict()
        output_resources = {}
        for dependency in d.get('properties', {}).get('dependencies'):
            # go through dependent resources
            depends_on = []
            for depends_on_resource in dependency['depends_on']:
                depends_on.append(depends_on_resource['id'])
                # append if not in list
                if not output_resources.get(depends_on_resource['id']):
                    sub_resource = {
                        'id': depends_on_resource['id'],
                        'name': depends_on_resource['resource_name'],
                        'type': depends_on_resource['resource_type'],
                        'depends_on': []
                    }
                    output_resources[depends_on_resource['id']] = sub_resource
            resource = {
                'id': dependency['id'],
                'name': dependency['resource_name'],
                'type': dependency['resource_type'],
                'depends_on': depends_on
            }
            output_resources[dependency['id']] = resource

        # convert dictionary to list
        output_resources_list = []
        for r in output_resources:
            output_resources_list.append(output_resources[r])

        d = {
            'id': d.get('id'),
            'resource_group': self.resource_group,
            'name': d.get('name'),
            'provisioning_state': d.get('properties', {}).get('provisioning_state'),
            'parameters': d.get('properties', {}).get('parameters'),
            'outputs': d.get('properties', {}).get('outputs'),
            'output_resources': output_resources_list,
            'template_link': d.get('properties', {}).get('template_link').get('uri')
        }
        return d


def main():
    AzureRMDeploymentInfo()


if __name__ == '__main__':
    main()
