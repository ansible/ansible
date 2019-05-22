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
module: azure_rm_devtestlabartifactsource
version_added: "2.8"
short_description: Manage Azure DevTest Labs Artifacts Source instance
description:
    - Create, update and delete instance of Azure DevTest Labs Artifacts Source.

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
            - The name of the artifact source.
        required: True
    display_name:
        description:
            - The artifact source's display name.
    uri:
        description:
            - The artifact source's URI.
    source_type:
        description:
            - The artifact source's type.
        choices:
            - 'vso'
            - 'github'
    folder_path:
        description:
            - The folder containing artifacts.
    arm_template_folder_path:
        description:
            - The folder containing Azure Resource Manager templates.
    branch_ref:
        description:
            - The artifact source's branch reference.
    security_token:
        description:
            - The security token to authenticate to the artifact source.
    is_enabled:
        description:
            - Indicates whether the artifact source is enabled.
        type: bool
    state:
      description:
          - Assert the state of the DevTest Labs Artifacts Source.
          - Use C(present) to create or update an DevTest Labs Artifacts Source and C(absent) to delete it.
      default: present
      choices:
          - absent
          - present

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - Zim Kalinowski (@zikalino)

'''

EXAMPLES = '''
  - name: Create (or update) DevTest Labs Artifacts Source
    azure_rm_devtestlabartifactsource:
      resource_group: myrg
      lab_name: mylab
      name: myartifacts
      uri: https://github.com/myself/myrepo.git
      source_type: github
      folder_path: /
      security_token: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
'''

RETURN = '''
id:
    description:
        - The identifier of the resource.
    returned: always
    type: str
    sample: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourcegroups/myrg/providers/microsoft.devtestlab/labs/mylab/artifactsources/myartifacts
is_enabled:
    description:
        - Indicates whether the artifact source is enabled.
    returned: always
    type: bool
    sample: true
'''

import time
from ansible.module_utils.azure_rm_common import AzureRMModuleBase
from ansible.module_utils.common.dict_transformations import _snake_to_camel

try:
    from msrestazure.azure_exceptions import CloudError
    from msrest.polling import LROPoller
    from msrestazure.azure_operation import AzureOperationPoller
    from azure.mgmt.devtestlabs import DevTestLabsClient
    from msrest.serialization import Model
except ImportError:
    # This is handled in azure_rm_common
    pass


class Actions:
    NoAction, Create, Update, Delete = range(4)


class AzureRMDevTestLabArtifactsSource(AzureRMModuleBase):
    """Configuration class for an Azure RM DevTest Labs Artifacts Source resource"""

    def __init__(self):
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
            display_name=dict(
                type='str'
            ),
            uri=dict(
                type='str'
            ),
            source_type=dict(
                type='str',
                choices=['vso',
                         'github']
            ),
            folder_path=dict(
                type='str'
            ),
            arm_template_folder_path=dict(
                type='str'
            ),
            branch_ref=dict(
                type='str'
            ),
            security_token=dict(
                type='str'
            ),
            is_enabled=dict(
                type='bool'
            ),
            state=dict(
                type='str',
                default='present',
                choices=['present', 'absent']
            )
        )

        self.resource_group = None
        self.lab_name = None
        self.name = None
        self.artifact_source = dict()

        self.results = dict(changed=False)
        self.mgmt_client = None
        self.state = None
        self.to_do = Actions.NoAction

        required_if = [
            ('state', 'present', [
             'source_type', 'uri', 'security_token'])
        ]

        super(AzureRMDevTestLabArtifactsSource, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                               supports_check_mode=True,
                                                               supports_tags=True,
                                                               required_if=required_if)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
            elif kwargs[key] is not None:
                self.artifact_source[key] = kwargs[key]

        if self.artifact_source.get('source_type') == 'github':
            self.artifact_source['source_type'] = 'GitHub'
        elif self.artifact_source.get('source_type') == 'vso':
            self.artifact_source['source_type'] = 'VsoGit'

        if self.artifact_source.get('status') is not None:
            self.artifact_source['status'] = 'Enabled' if self.artifact_source.get('status') else 'Disabled'

        response = None

        self.mgmt_client = self.get_mgmt_svc_client(DevTestLabsClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager,
                                                    api_version='2018-10-15')

        old_response = self.get_devtestlabartifactssource()

        if not old_response:
            self.log("DevTest Labs Artifacts Source instance doesn't exist")
            if self.state == 'absent':
                self.log("Old instance didn't exist")
            else:
                self.to_do = Actions.Create
        else:
            self.log("DevTest Labs Artifacts Source instance already exists")
            if self.state == 'absent':
                self.to_do = Actions.Delete
            elif self.state == 'present':
                self.results['old_response'] = old_response

                if self.artifact_source.get('display_name') is not None:
                    if self.artifact_source.get('display_name') != old_response.get('display_name'):
                        self.to_do = Actions.Update
                else:
                    self.artifact_source['display_name'] = old_response.get('display_name')

                if self.artifact_source.get('source_type').lower() != old_response.get('source_type').lower():
                    self.to_do = Actions.Update

                if self.artifact_source.get('uri') != old_response.get('uri'):
                    self.to_do = Actions.Update

                if self.artifact_source.get('branch_ref') is not None:
                    if self.artifact_source.get('branch_ref') != old_response.get('branch_ref'):
                        self.to_do = Actions.Update
                else:
                    self.artifact_source['branch_ref'] = old_response.get('branch_ref')

                if self.artifact_source.get('status') is not None:
                    if self.artifact_source.get('status') != old_response.get('status'):
                        self.to_do = Actions.Update
                else:
                    self.artifact_source['status'] = old_response.get('status')

                if self.artifact_source.get('folder_path') is not None:
                    if self.artifact_source.get('folder_path') != old_response.get('folder_path'):
                        self.to_do = Actions.Update
                else:
                    self.artifact_source['folder_path'] = old_response.get('folder_path')

                if self.artifact_source.get('arm_template_folder_path') is not None:
                    if self.artifact_source.get('arm_template_folder_path') != old_response.get('arm_template_folder_path'):
                        self.to_do = Actions.Update
                else:
                    self.artifact_source['arm_template_folder_path'] = old_response.get('arm_template_folder_path')

        if (self.to_do == Actions.Create) or (self.to_do == Actions.Update):
            self.log("Need to Create / Update the DevTest Labs Artifacts Source instance")
            self.results['changed'] = True
            if self.check_mode:
                return self.results
            response = self.create_update_devtestlabartifactssource()
            self.log("Creation / Update done")
        elif self.to_do == Actions.Delete:
            self.log("DevTest Labs Artifacts Source instance deleted")
            self.results['changed'] = True
            if self.check_mode:
                return self.results
            self.delete_devtestlabartifactssource()
        else:
            self.log("DevTest Labs Artifacts Source instance unchanged")
            self.results['changed'] = False
            response = old_response

        if self.state == 'present':
            self.results.update({
                'id': response.get('id', None),
                'is_enabled': (response.get('status', None).lower() == 'enabled')
            })
        return self.results

    def create_update_devtestlabartifactssource(self):
        '''
        Creates or updates DevTest Labs Artifacts Source with the specified configuration.

        :return: deserialized DevTest Labs Artifacts Source instance state dictionary
        '''
        self.log("Creating / Updating the DevTest Labs Artifacts Source instance {0}".format(self.name))

        try:
            response = self.mgmt_client.artifact_sources.create_or_update(resource_group_name=self.resource_group,
                                                                          lab_name=self.lab_name,
                                                                          name=self.name,
                                                                          artifact_source=self.artifact_source)
            if isinstance(response, LROPoller) or isinstance(response, AzureOperationPoller):
                response = self.get_poller_result(response)

        except CloudError as exc:
            self.log('Error attempting to create the DevTest Labs Artifacts Source instance.')
            self.fail("Error creating the DevTest Labs Artifacts Source instance: {0}".format(str(exc)))
        return response.as_dict()

    def delete_devtestlabartifactssource(self):
        '''
        Deletes specified DevTest Labs Artifacts Source instance in the specified subscription and resource group.

        :return: True
        '''
        self.log("Deleting the DevTest Labs Artifacts Source instance {0}".format(self.name))
        try:
            response = self.mgmt_client.artifact_sources.delete(resource_group_name=self.resource_group,
                                                                lab_name=self.lab_name,
                                                                name=self.name)
        except CloudError as e:
            self.log('Error attempting to delete the DevTest Labs Artifacts Source instance.')
            self.fail("Error deleting the DevTest Labs Artifacts Source instance: {0}".format(str(e)))

        return True

    def get_devtestlabartifactssource(self):
        '''
        Gets the properties of the specified DevTest Labs Artifacts Source.

        :return: deserialized DevTest Labs Artifacts Source instance state dictionary
        '''
        self.log("Checking if the DevTest Labs Artifacts Source instance {0} is present".format(self.name))
        found = False
        try:
            response = self.mgmt_client.artifact_sources.get(resource_group_name=self.resource_group,
                                                             lab_name=self.lab_name,
                                                             name=self.name)
            found = True
            self.log("Response : {0}".format(response))
            self.log("DevTest Labs Artifacts Source instance : {0} found".format(response.name))
        except CloudError as e:
            self.log('Did not find the DevTest Labs Artifacts Source instance.')
        if found is True:
            return response.as_dict()

        return False


def main():
    """Main execution"""
    AzureRMDevTestLabArtifactsSource()


if __name__ == '__main__':
    main()
