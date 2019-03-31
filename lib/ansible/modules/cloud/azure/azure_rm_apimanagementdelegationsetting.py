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
module: azure_rm_apimanagementdelegationsetting
version_added: '2.9'
short_description: Manage Azure DelegationSetting instance.
description:
  - 'Create, update and delete instance of Azure DelegationSetting.'
options:
  resource_group_name:
    description:
      - The name of the resource group.
  service_name:
    description:
      - The name of the API Management service.
  properties:
    description:
      - Delegation settings contract properties.
    suboptions:
      url:
        description:
          - A delegation Url.
      validation_key:
        description:
          - >-
            A base64-encoded validation key to validate, that a request is
            coming from Azure API Management.
      subscriptions:
        description:
          - Subscriptions delegation settings.
        suboptions:
          enabled:
            description:
              - Enable or disable delegation for subscriptions.
      user_registration:
        description:
          - User registration delegation settings.
        suboptions:
          enabled:
            description:
              - Enable or disable delegation for user registration.
  state:
    description:
      - Assert the state of the DelegationSetting.
      - >-
        Use C(present) to create or update an DelegationSetting and C(absent) to
        delete it.
    default: present
    choices:
      - absent
      - present
extends_documentation_fragment:
  - azure
author:
  - Zim Kalinowski (@zikalino)

'''

EXAMPLES = '''
- name: ApiManagementPortalSettingsUpdateDelegation
  azure_rm_apimanagementdelegationsetting:
    serviceName: apimService1
    resourceGroupName: rg1
    api-version: '2018-01-01'
    subscriptionId: subid
    uid: 5931a75ae4bbd512288c680b
    If-Match: '*'
    parameters:
      properties:
        url: 'http://contoso.com/delegation'
        validationKey: >-
          nVF7aKIvr9mV/RM5lOD0sYoi8ThXTRHQP7o66hvUmjCDkPKR3qxPu/otJcNciz2aQdqPuzJH3ECG4TU2yZjQ7Q==
        subscriptions:
          enabled: true
        userRegistration:
          enabled: true

'''

RETURN = '''
{}

'''

import time
import json
from ansible.module_utils.azure_rm_common import AzureRMModuleBase
from ansible.module_utils.azure_rm_common_rest import GenericRestClient
from copy import deepcopy
from msrestazure.azure_exceptions import CloudError


class Actions:
    NoAction, Create, Update, Delete = range(4)


class AzureRMDelegationSettings(AzureRMModuleBase):
    """Configuration class for an Azure RM DelegationSetting resource"""

    def __init__(self):
        self.module_arg_spec = dict(
            resource_group_name=dict(
                type='str'
            ),
            service_name=dict(
                type='str'
            ),
            properties=dict(
                type='dict'
            ),
            state=dict(
                type='str',
                default='present',
                choices=['present', 'absent']
            )
        )

        self.resource_group_name = None
        self.service_name = None

        self.results = dict(changed=False)
        self.mgmt_client = None
        self.state = None
        self.url = None
        self.status_code = [ 200, 202 ]
        self.to_do = Actions.NoAction

        self.body = {}
        self.query_parameters = {}
        self.query_parameters['api-version'] = '2018-01-01'
        self.header_parameters = {}
        self.header_parameters['Content-Type'] = 'application/json; charset=utf-8'

        super(AzureRMDelegationSettings, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                       supports_check_mode=True,
                                                        supports_tags=False)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        for key in list(self.module_arg_spec.keys()):
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
            elif kwargs[key] is not None:
                if key == "properties":
                    self.body["properties"] = kwargs[key]

        self.adjust_parameters()

        old_response = None
        response = None

        self.mgmt_client = self.get_mgmt_svc_client(GenericRestClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        # prepare url
        self.url = '/subscriptions/{{ subscription_id }}/resourceGroups/{{ resource_group }}/providers/Microsoft.ApiManagement/service/{{ service_name }}/portalsettings/{{ portalsetting_name }}'
        self.url = self.url.replace('{{ subscription_id }}', self.subscription_id)
        self.url = self.url.replace('{{ resource_group }}', self.resource_group)
        self.url = self.url.replace('{{ service_name }}', self.service_name)
        self.url = self.url.replace('{{ portalsetting_name }}', self.portalsetting_name)

        old_response = self.get_delegationsetting()

        if not old_response:
            self.log("DelegationSetting instance doesn't exist")

            if self.state == 'absent':
                self.log("Old instance didn't exist")
            else:
                self.to_do = Actions.Create
        else:
            self.log('DelegationSetting instance already exists')

            if self.state == 'absent':
                self.to_do = Actions.Delete
            elif self.state == 'present':
                self.log('Need to check if DelegationSetting instance has to be deleted or may be updated')

        if (self.to_do == Actions.Create) or (self.to_do == Actions.Update):
            self.log('Need to Create / Update the DelegationSetting instance')

            if self.check_mode:
                self.results['changed'] = True
                return self.results

            response = self.create_update_delegationsetting()

            #if not old_response:
            self.results['changed'] = True
            self.results['response'] = response
            #else:
            #    self.results['changed'] = old_response.__ne__(response)
            self.log('Creation / Update done')
        elif self.to_do == Actions.Delete:
            self.log('DelegationSetting instance deleted')
            self.results['changed'] = True

            if self.check_mode:
                return self.results

            self.delete_delegationsetting()

            # make sure instance is actually deleted, for some Azure resources, instance is hanging around
            # for some time after deletion -- this should be really fixed in Azure
            while self.get_delegationsetting():
                time.sleep(20)
        else:
            self.log('DelegationSetting instance unchanged')
            self.results['changed'] = False
            response = old_response


        return self.results

    def adjust_parameters(self):
if self.parameters.get('properties', None) is not None:

    def rename_key(self, d, old_name, new_name):
        old_value = d.get(old_name, None)
        if old_value is not None:
            d.pop(old_name, None)
            d[new_name] = old_value

    def create_update_delegationsetting(self):
        '''
        Creates or updates DelegationSetting with the specified configuration.

        :return: deserialized DelegationSetting instance state dictionary
        '''
        #self.log('Creating / Updating the DelegationSetting instance {0}'.format(self.))

        try:
            if self.to_do == Actions.Create:
                response = self.mgmt_client.query(self.url,
                                                  'PUT',
                                                  self.query_parameters,
                                                  self.header_parameters,
                                                  self.body, # { 'location': 'eastus'},
                                                  self.status_code)
            else:
                response = self.mgmt_client.query(self.url,
                                                  'PUT',
                                                  self.query_parameters,
                                                  self.header_parameters,
                                                  self.body,
                                                  self.status_code)
            # implement poller in another way
            #if isinstance(response, AzureOperationPoller):
            #    response = self.get_poller_result(response)

        except CloudError as exc:
            self.log('Error attempting to create the DelegationSetting instance.')
            self.fail('Error creating the DelegationSetting instance: {0}'.format(str(exc)))

        try:
            response = json.loads(response.text)
        except:
           response = { 'text': response.text }
           pass

        return response

    def delete_delegationsetting(self):
        '''
        Deletes specified DelegationSetting instance in the specified subscription and resource group.

        :return: True
        '''
        #self.log('Deleting the DelegationSetting instance {0}'.format(self.))
        try:
            response = self.mgmt_client.query(self.url,
                                              'DELETE',
                                              self.query_parameters,
                                              self.header_parameters,
                                              None,
                                              self.status_code)
        except CloudError as e:
            self.log('Error attempting to delete the DelegationSetting instance.')
            self.fail('Error deleting the DelegationSetting instance: {0}'.format(str(e)))

        return True

    def get_delegationsetting(self):
        '''
        Gets the properties of the specified DelegationSetting.

        :return: deserialized DelegationSetting instance state dictionary
        '''
        #self.log('Checking if the DelegationSetting instance {0} is present'.format(self.))
        found = False
        try:
            response = self.mgmt_client.query(self.url,
                                              'GET',
                                              self.query_parameters,
                                              self.header_parameters,
                                              None,
                                              self.status_code)
            found = True
            self.log("Response : {0}".format(response))
            #self.log("DelegationSetting instance : {0} found".format(response.name))
        except CloudError as e:
            self.log('Did not find the DelegationSetting instance.')
        if found is True:
            return response

        return False


def main():
    """Main execution"""
    AzureRMDelegationSettings()

if __name__ == '__main__':
    main()