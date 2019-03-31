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
module: azure_rm_apimanagementauthorizationserver
version_added: '2.9'
short_description: Manage Azure AuthorizationServer instance.
description:
  - 'Create, update and delete instance of Azure AuthorizationServer.'
options:
  resource_group_name:
    description:
      - The name of the resource group.
  service_name:
    description:
      - The name of the API Management service.
  authsid:
    description:
      - Identifier of the authorization server.
  properties:
    description:
      - Properties of the External OAuth authorization server Contract.
    suboptions:
      display_name:
        description:
          - User-friendly authorization server name.
        required: true
      client_registration_endpoint:
        description:
          - >-
            Optional reference to a page where client or app registration for
            this authorization server is performed. Contains absolute URL to
            entity being referenced.
        required: true
      authorization_endpoint:
        description:
          - >-
            OAuth authorization endpoint. See
            http://tools.ietf.org/html/rfc6749#section-3.2.
        required: true
      grant_types:
        description:
          - >-
            Form of an authorization grant, which the client uses to request the
            access token.
        required: true
      client_id:
        description:
          - Client or app id registered with this authorization server.
        required: true
  _if-_match:
    description:
      - >-
        ETag of the Entity. Not required when creating an entity, but required
        when updating an entity.
  state:
    description:
      - Assert the state of the AuthorizationServer.
      - >-
        Use C(present) to create or update an AuthorizationServer and C(absent)
        to delete it.
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
- name: ApiManagementCreateAuthorizationServer
  azure_rm_apimanagementauthorizationserver:
    serviceName: apimService1
    resourceGroupName: myResourceGroup
    authsid: newauthServer
    properties:
      displayName: test2
      description: test server
      clientRegistrationEndpoint: 'https://www.contoso.com/apps'
      authorizationEndpoint: 'https://www.contoso.com/oauth2/auth'
      authorizationMethods:
        - GET
      tokenEndpoint: 'https://www.contoso.com/oauth2/token'
      supportState: true
      defaultScope: read write
      grantTypes:
        - authorizationCode
        - implicit
      bearerTokenSendingMethods:
        - authorizationHeader
      clientId: '1'
      clientSecret: '2'
      resourceOwnerUsername: un
      resourceOwnerPassword: pwd

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


class AzureRMAuthorizationServer(AzureRMModuleBase):
    """Configuration class for an Azure RM AuthorizationServer resource"""

    def __init__(self):
        self.module_arg_spec = dict(
            resource_group_name=dict(
                type='str'
            ),
            service_name=dict(
                type='str'
            ),
            authsid=dict(
                type='str'
            ),
            properties=dict(
                type='dict'
            ),
            _if-_match=dict(
                type='str'
            ),
            state=dict(
                type='str',
                default='present',
                choices=['present', 'absent']
            )
        )

        self.resource_group_name = None
        self.service_name = None
        self.authsid = None
        self._if-_match = None

        self.results = dict(changed=False)
        self.mgmt_client = None
        self.state = None
        self.url = None
        self.status_code = [200, 202]
        self.to_do = Actions.NoAction

        self.body = {}
        self.query_parameters = {}
        self.query_parameters['api-version'] = '2018-01-01'
        self.header_parameters = {}
        self.header_parameters['Content-Type'] = 'application/json; charset=utf-8'

        super(AzureRMAuthorizationServer, self).__init__(derived_arg_spec=self.module_arg_spec,
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

        self.url = ('/subscriptions' +
                    '/{{ subscription_id }}' +
                    '/resourceGroups' +
                    '/{{ resource_group }}' +
                    '/providers' +
                    '/Microsoft.ApiManagement' +
                    '/service' +
                    '/{{ service_name }}' +
                    '/authorizationServers' +
                    '/{{ authorization_server_name }}')
        self.url = self.url.replace('{{ subscription_id }}', self.subscription_id)
        self.url = self.url.replace('{{ resource_group }}', self.resource_group)
        self.url = self.url.replace('{{ service_name }}', self.service_name)
        self.url = self.url.replace('{{ authorization_server_name }}', self.authorization_server_name)

        old_response = self.get_authorizationserver()

        if not old_response:
            self.log("AuthorizationServer instance doesn't exist")

            if self.state == 'absent':
                self.log("Old instance didn't exist")
            else:
                self.to_do = Actions.Create
        else:
            self.log('AuthorizationServer instance already exists')

            if self.state == 'absent':
                self.to_do = Actions.Delete
            elif self.state == 'present':
                self.log('Need to check if AuthorizationServer instance has to be deleted or may be updated')

        if (self.to_do == Actions.Create) or (self.to_do == Actions.Update):
            self.log('Need to Create / Update the AuthorizationServer instance')

            if self.check_mode:
                self.results['changed'] = True
                return self.results

            response = self.create_update_authorizationserver()

            # if not old_response:
            self.results['changed'] = True
            self.results['response'] = response
            # else:
            #     self.results['changed'] = old_response.__ne__(response)
            self.log('Creation / Update done')
        elif self.to_do == Actions.Delete:
            self.log('AuthorizationServer instance deleted')
            self.results['changed'] = True

            if self.check_mode:
                return self.results

            self.delete_authorizationserver()

            # make sure instance is actually deleted, for some Azure resources, instance is hanging around
            # for some time after deletion -- this should be really fixed in Azure
            while self.get_authorizationserver():
                time.sleep(20)
        else:
            self.log('AuthorizationServer instance unchanged')
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

    def create_update_authorizationserver(self):
        '''
        Creates or updates AuthorizationServer with the specified configuration.

        :return: deserialized AuthorizationServer instance state dictionary
        '''
        # self.log('Creating / Updating the AuthorizationServer instance {0}'.format(self.))

        try:
            if self.to_do == Actions.Create:
                response = self.mgmt_client.query(self.url,
                                                  'PUT',
                                                  self.query_parameters,
                                                  self.header_parameters,
                                                  self.body,
                                                  self.status_code)
            else:
                response = self.mgmt_client.query(self.url,
                                                  'PUT',
                                                  self.query_parameters,
                                                  self.header_parameters,
                                                  self.body,
                                                  self.status_code)
            # implement poller in another way
            # if isinstance(response, AzureOperationPoller):
            #    response = self.get_poller_result(response)

        except CloudError as exc:
            self.log('Error attempting to create the AuthorizationServer instance.')
            self.fail('Error creating the AuthorizationServer instance: {0}'.format(str(exc)))

        try:
            response = json.loads(response.text)
        except Exception:
            response = {'text': response.text}
            pass

        return response

    def delete_authorizationserver(self):
        '''
        Deletes specified AuthorizationServer instance in the specified subscription and resource group.

        :return: True
        '''
        # self.log('Deleting the AuthorizationServer instance {0}'.format(self.))
        try:
            response = self.mgmt_client.query(self.url,
                                              'DELETE',
                                              self.query_parameters,
                                              self.header_parameters,
                                              None,
                                              self.status_code)
        except CloudError as e:
            self.log('Error attempting to delete the AuthorizationServer instance.')
            self.fail('Error deleting the AuthorizationServer instance: {0}'.format(str(e)))

        return True

    def get_authorizationserver(self):
        '''
        Gets the properties of the specified AuthorizationServer.

        :return: deserialized AuthorizationServer instance state dictionary
        '''
        # self.log('Checking if the AuthorizationServer instance {0} is present'.format(self.))
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
            # self.log("AuthorizationServer instance : {0} found".format(response.name))
        except CloudError as e:
            self.log('Did not find the AuthorizationServer instance.')
        if found is True:
            return response

        return False


def main():
    """Main execution"""
    AzureRMAuthorizationServer()


if __name__ == '__main__':
    main()
