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
module: azure_rm_deployment_facts
version_added: "2.8"
short_description: Get Azure Deployment facts.
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
    - "Zim Kalinowski (@zikalino)"

'''

EXAMPLES = '''
  - name: Get instance of Deployment
    azure_rm_deployment_facts:
      resource_group: myResourceGroup
      name: myDeployment
'''

RETURN = '''
deployments:
    description: A list of dictionaries containing facts for Artifact.
    returned: always
    type: complex
    contains:
        id:
            description:
                - The identifier of the resource.
            returned: always
            type: str
            sample: id
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
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.devtestlabs import DevTestLabsClient
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMDeploymentFacts(AzureRMModuleBase):
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
        super(AzureRMDeploymentFacts, self).__init__(self.module_arg_spec, supports_tags=False)

    def exec_module(self, **kwargs):
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
        output_resources = []
        # for resource in d.get('properties', {}).get('output_resources'):
        #     output_resources.append(resource.get('id'))

        d = {
            'id': d.get('id'),
            'resource_group': self.resource_group, 
            'name': d.get('name'),
            'provisioning_state': d.get('properties', {}).get('provisioning_state'),
            'parameters': d.get('properties', {}).get('parameters'),
            'outputs': d.get('properties', {}).get('outputs'),
            'dependencies': d.get('properties', {}).get('dependencies'),
            'template_link': d.get('properties', {}).get('template_link')
        }
        return d


def main():
    AzureRMDeploymentFacts()


if __name__ == '__main__':
    main()
