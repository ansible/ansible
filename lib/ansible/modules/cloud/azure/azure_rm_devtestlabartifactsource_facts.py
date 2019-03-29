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
module: azure_rm_devtestlabartifactsource_facts
version_added: "2.8"
short_description: Get Azure DevTest Lab Artifact Source facts.
description:
    - Get facts of Azure DevTest Lab Artifact Source.

options:
    resource_group:
        description:
            - The name of the resource group.
        required: True
    lab_name:
        description:
            - The name of DevTest Lab.
        required: True
    name:
        description:
            - The name of DevTest Lab Artifact Source.
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.

extends_documentation_fragment:
    - azure

author:
    - "Zim Kalinowski (@zikalino)"

'''

EXAMPLES = '''
  - name: Get instance of DevTest Lab Artifact Source
    azure_rm_devtestlabartifactsource_facts:
      resource_group: myResourceGroup
      lab_name: myLab
      name: myArtifactSource
'''

RETURN = '''
artifactsources:
    description: A list of dictionaries containing facts for DevTest Lab Artifact Source.
    returned: always
    type: complex
    contains:
        id:
            description:
                - The identifier of the artifact source.
            returned: always
            type: str
            sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.DevTestLab/labs/myLab/ar
                     tifactSources/myArtifactSource"
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
                - The name of the artifact source.
            returned: always
            type: str
            sample: myArtifactSource
        display_name:
            description:
                - "The artifact source's display name."
            returned: always
            type: str
            sample: Public Artifact Repo
        source_type:
            description:
                - "The artifact source's type."
            returned: always
            type: str
            sample: github
        is_enabled:
            description:
                - Is the artifact source enabled.
            returned: always
            type: str
            sample: True
        uri:
            description:
                - URI of the artifact source.
            returned: always
            type: str
            sample: https://github.com/Azure/azure-devtestlab.git
        folder_path:
            description:
                - The folder containing artifacts.
            returned: always
            type: str
            sample: /Artifacts
        arm_template_folder_path:
            description:
                - The folder containing Azure Resource Manager templates.
            returned: always
            type: str
            sample: /Environments
        provisioning_state:
            description:
                - Provisioning state of artifact source.
            returned: always
            type: str
            sample: Succeeded
        tags:
            description:
                - The tags of the resource.
            returned: always
            type: complex
            sample: "{ 'MyTag': 'MyValue' }"
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.devtestlabs import DevTestLabsClient
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMDtlArtifactSourceFacts(AzureRMModuleBase):
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
        super(AzureRMDtlArtifactSourceFacts, self).__init__(self.module_arg_spec, supports_tags=False)

    def exec_module(self, **kwargs):
        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])
        self.mgmt_client = self.get_mgmt_svc_client(DevTestLabsClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        if self.name:
            self.results['artifactsources'] = self.get()
        else:
            self.results['artifactsources'] = self.list()

        return self.results

    def get(self):
        response = None
        results = []
        try:
            response = self.mgmt_client.artifact_sources.get(resource_group_name=self.resource_group,
                                                             lab_name=self.lab_name,
                                                             name=self.name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.fail('Could not get facts for Artifact Source.')

        if response and self.has_tags(response.tags, self.tags):
            results.append(self.format_response(response))

        return results

    def list(self):
        response = None
        results = []
        try:
            response = self.mgmt_client.artifact_sources.list(resource_group_name=self.resource_group,
                                                              lab_name=self.lab_name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.fail('Could not get facts for Artifact Source.')

        if response is not None:
            for item in response:
                if self.has_tags(item.tags, self.tags):
                    results.append(self.format_response(item))

        return results

    def format_response(self, item):
        d = item.as_dict()
        d = {
            'id': d.get('id'),
            'resource_group': self.parse_resource_to_dict(d.get('id')).get('resource_group'),
            'lab_name': self.parse_resource_to_dict(d.get('id')).get('name'),
            'name': d.get('name'),
            'display_name': d.get('display_name'),
            'tags': d.get('tags'),
            'source_type': d.get('source_type').lower(),
            'is_enabled': d.get('status') == 'Enabled',
            'uri': d.get('uri'),
            'arm_template_folder_path': d.get('arm_template_folder_path'),
            'folder_path': d.get('folder_path'),
            'provisioning_state': d.get('provisioning_state')
        }
        return d


def main():
    AzureRMDtlArtifactSourceFacts()


if __name__ == '__main__':
    main()
