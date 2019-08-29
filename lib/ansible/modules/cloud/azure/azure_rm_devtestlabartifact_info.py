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
module: azure_rm_devtestlabartifact_info
version_added: "2.9"
short_description: Get Azure DevTest Lab Artifact facts
description:
    - Get facts of Azure DevTest Lab Artifact.

options:
    resource_group:
        description:
            - The name of the resource group.
        required: True
        type: str
    lab_name:
        description:
            - The name of the lab.
        required: True
        type: str
    artifact_source_name:
        description:
            - The name of the artifact source.
        required: True
        type: str
    name:
        description:
            - The name of the artifact.
        type: str

extends_documentation_fragment:
    - azure

author:
    - Zim Kalinowski (@zikalino)

'''

EXAMPLES = '''
  - name: Get instance of DevTest Lab Artifact
    azure_rm_devtestlabartifact_info:
      resource_group: myResourceGroup
      lab_name: myLab
      artifact_source_name: myArtifactSource
      name: myArtifact
'''

RETURN = '''
artifacts:
    description:
        - A list of dictionaries containing facts for DevTest Lab Artifact.
    returned: always
    type: complex
    contains:
        id:
            description:
                - The identifier of the artifact.
            returned: always
            type: str
            sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.DevTestLab/labs/myLab/ar
                     tifactSources/myArtifactSource/artifacts/myArtifact"
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
        artifact_source_name:
            description:
                - The name of the artifact source.
            returned: always
            type: str
            sample: myArtifactSource
        name:
            description:
                - The name of the artifact.
            returned: always
            type: str
            sample: myArtifact
        description:
            description:
                - Description of the artifact.
            returned: always
            type: str
            sample: Installs My Software
        file_path:
            description:
                - Artifact's path in the repo.
            returned: always
            type: str
            sample: Artifacts/myArtifact
        publisher:
            description:
                - Publisher name.
            returned: always
            type: str
            sample: MyPublisher
        target_os_type:
            description:
                - Target OS type.
            returned: always
            type: str
            sample: Linux
        title:
            description:
                - Title of the artifact.
            returned: always
            type: str
            sample: My Software
        parameters:
            description:
                - A dictionary containing parameters definition of the artifact.
            returned: always
            type: complex
            sample: {}
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.devtestlabs import DevTestLabsClient
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMArtifactInfo(AzureRMModuleBase):
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
            artifact_source_name=dict(
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
        self.artifact_source_name = None
        self.name = None
        super(AzureRMArtifactInfo, self).__init__(self.module_arg_spec, supports_tags=False)

    def exec_module(self, **kwargs):
        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])
        self.mgmt_client = self.get_mgmt_svc_client(DevTestLabsClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        if self.name:
            self.results['artifacts'] = self.get()
        else:
            self.results['artifacts'] = self.list()

        return self.results

    def get(self):
        response = None
        results = []
        try:
            response = self.mgmt_client.artifacts.get(resource_group_name=self.resource_group,
                                                      lab_name=self.lab_name,
                                                      artifact_source_name=self.artifact_source_name,
                                                      name=self.name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for Artifact.')

        if response:
            results.append(self.format_response(response))

        return results

    def list(self):
        response = None
        results = []
        try:
            response = self.mgmt_client.artifacts.list(resource_group_name=self.resource_group,
                                                       lab_name=self.lab_name,
                                                       artifact_source_name=self.artifact_source_name)
            self.log("Response : {0}".format(response))
        except CloudError as e:
            self.log('Could not get facts for Artifact.')

        if response is not None:
            for item in response:
                results.append(self.format_response(item))

        return results

    def format_response(self, item):
        d = item.as_dict()
        d = {
            'resource_group': self.parse_resource_to_dict(d.get('id')).get('resource_group'),
            'lab_name': self.parse_resource_to_dict(d.get('id')).get('name'),
            'artifact_source_name': self.parse_resource_to_dict(d.get('id')).get('child_name_1'),
            'id': d.get('id'),
            'description': d.get('description'),
            'file_path': d.get('file_path'),
            'name': d.get('name'),
            'parameters': d.get('parameters'),
            'publisher': d.get('publisher'),
            'target_os_type': d.get('target_os_type'),
            'title': d.get('title')
        }
        return d


def main():
    AzureRMArtifactInfo()


if __name__ == '__main__':
    main()
