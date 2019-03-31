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
module: azure_rm_apimanagementapi
version_added: '2.9'
short_description: Manage Azure Api instance.
description:
  - 'Create, update and delete instance of Azure Api.'
options:
  resource_group_name:
    description:
      - The name of the resource group.
  service_name:
    description:
      - The name of the API Management service.
  api_id:
    description:
      - >-
        API revision identifier. Must be unique in the current API Management
        service instance. Non-current revision has ;rev=n as a suffix where n is
        the revision number.
  properties:
    description:
      - Api entity create of update properties.
    suboptions:
      content_value:
        description:
          - Content value when Importing an API.
      content_format:
        description:
          - Format of the Content in which the API is getting imported.
      wsdl_selector:
        description:
          - Criteria to limit import of WSDL to a subset of the document.
        suboptions:
          wsdl_service_name:
            description:
              - Name of service to import from WSDL
          wsdl_endpoint_name:
            description:
              - Name of endpoint(port) to import from WSDL
      api_type:
        description:
          - 'Type of Api to create. '
          - ' * `http` creates a SOAP to REST API '
          - ' * `soap` creates a SOAP pass-through API .'
  _if-_match:
    description:
      - >-
        ETag of the Entity. Not required when creating an entity, but required
        when updating an entity.
  state:
    description:
      - Assert the state of the Api.
      - Use C(present) to create or update an Api and C(absent) to delete it.
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
- name: ApiManagementCreateApiUsingSwaggerImport
  azure_rm_apimanagementapi:
    serviceName: apimService1
    resourceGroupName: myResourceGroup
    apiId: petstore
    properties:
      contentFormat: swagger-link-json
      contentValue: 'http://petstore.swagger.io/v2/swagger.json'
      path: petstore
- name: ApiManagementCreateApiUsingWadlImport
  azure_rm_apimanagementapi:
    serviceName: apimService1
    resourceGroupName: myResourceGroup
    apiId: petstore
    properties:
      contentFormat: wadl-link-json
      contentValue: >-
        https://developer.cisco.com/media/wae-release-6-2-api-reference/wae-collector-rest-api/application.wadl
      path: collector
- name: ApiManagementCreateSoapToRestApiUsingWsdlImport
  azure_rm_apimanagementapi:
    serviceName: apimService1
    resourceGroupName: myResourceGroup
    apiId: soapApi
    properties:
      contentFormat: wsdl-link
      contentValue: 'http://www.webservicex.net/CurrencyConvertor.asmx?WSDL'
      path: currency
      wsdlSelector:
        wsdlServiceName: CurrencyConvertor
        wsdlEndpointName: CurrencyConvertorSoap
- name: ApiManagementCreateSoapPassThroughApiUsingWsdlImport
  azure_rm_apimanagementapi:
    serviceName: apimService1
    resourceGroupName: myResourceGroup
    apiId: soapApi
    properties:
      contentFormat: wsdl-link
      contentValue: 'http://www.webservicex.net/CurrencyConvertor.asmx?WSDL'
      path: currency
      apiType: soap
      wsdlSelector:
        wsdlServiceName: CurrencyConvertor
        wsdlEndpointName: CurrencyConvertorSoap
- name: ApiManagementCreateApi
  azure_rm_apimanagementapi:
    serviceName: apimService1
    resourceGroupName: myResourceGroup
    apiId: tempgroup
    properties:
      description: apidescription5200
      authenticationSettings:
        oAuth2:
          authorizationServerId: authorizationServerId2283
          scope: oauth2scope2580
      subscriptionKeyParameterNames:
        header: header4520
        query: query3037
      displayName: apiname1463
      serviceUrl: 'http://newechoapi.cloudapp.net/api'
      path: newapiPath
      protocols:
        - https
        - http
- name: ApiManagementCreateApiRevision
  azure_rm_apimanagementapi:
    serviceName: apimService1
    resourceGroupName: myResourceGroup
    apiId: echo-api;rev=4
    properties:
      displayName: Echo API
      description: >-
        This is a sample server Petstore server.  You can find out more about
        Swagger at [http://swagger.io](http://swagger.io) or on
        [irc.freenode.net, #swagger](http://swagger.io/irc/).  For this sample,
        you can use the api key `special-key` to test the authorization filters.
      serviceUrl: 'http://petstore.swagger.io/v5'
      path: petstore2
      protocols:
        - https
      subscriptionKeyParameterNames:
        header: Ocp-Apim-Subscription-Key
        query: subscription-key
      isCurrent: false
      apiRevisionDescription: moved to swagger petstore backend
- name: ApiManagementCreateApiWithOpenIdConnect
  azure_rm_apimanagementapi:
    serviceName: apimService1
    resourceGroupName: myResourceGroup
    apiId: tempgroup
    properties:
      displayName: Swagger Petstore
      description: >-
        This is a sample server Petstore server.  You can find out more about
        Swagger at [http://swagger.io](http://swagger.io) or on
        [irc.freenode.net, #swagger](http://swagger.io/irc/).  For this sample,
        you can use the api key `special-key` to test the authorization filters.
      serviceUrl: 'http://petstore.swagger.io/v2'
      path: petstore
      protocols:
        - https
      authenticationSettings:
        openid:
          openidProviderId: testopenid
          bearerTokenSendingMethods:
            - authorizationHeader
      subscriptionKeyParameterNames:
        header: Ocp-Apim-Subscription-Key
        query: subscription-key

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


class AzureRMApi(AzureRMModuleBase):
    """Configuration class for an Azure RM Api resource"""

    def __init__(self):
        self.module_arg_spec = dict(
            resource_group_name=dict(
                type='str'
            ),
            service_name=dict(
                type='str'
            ),
            api_id=dict(
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
        self.api_id = None
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

        super(AzureRMApi, self).__init__(derived_arg_spec=self.module_arg_spec,
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
                    '/apis' +
                    '/{{ apis_name }}')
        self.url = self.url.replace('{{ subscription_id }}', self.subscription_id)
        self.url = self.url.replace('{{ resource_group }}', self.resource_group)
        self.url = self.url.replace('{{ service_name }}', self.service_name)
        self.url = self.url.replace('{{ apis_name }}', self.apis_name)

        old_response = self.get_api()

        if not old_response:
            self.log("Api instance doesn't exist")

            if self.state == 'absent':
                self.log("Old instance didn't exist")
            else:
                self.to_do = Actions.Create
        else:
            self.log('Api instance already exists')

            if self.state == 'absent':
                self.to_do = Actions.Delete
            elif self.state == 'present':
                self.log('Need to check if Api instance has to be deleted or may be updated')

        if (self.to_do == Actions.Create) or (self.to_do == Actions.Update):
            self.log('Need to Create / Update the Api instance')

            if self.check_mode:
                self.results['changed'] = True
                return self.results

            response = self.create_update_api()

            # if not old_response:
            self.results['changed'] = True
            self.results['response'] = response
            # else:
            #     self.results['changed'] = old_response.__ne__(response)
            self.log('Creation / Update done')
        elif self.to_do == Actions.Delete:
            self.log('Api instance deleted')
            self.results['changed'] = True

            if self.check_mode:
                return self.results

            self.delete_api()

            # make sure instance is actually deleted, for some Azure resources, instance is hanging around
            # for some time after deletion -- this should be really fixed in Azure
            while self.get_api():
                time.sleep(20)
        else:
            self.log('Api instance unchanged')
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

    def create_update_api(self):
        '''
        Creates or updates Api with the specified configuration.

        :return: deserialized Api instance state dictionary
        '''
        # self.log('Creating / Updating the Api instance {0}'.format(self.))

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
            self.log('Error attempting to create the Api instance.')
            self.fail('Error creating the Api instance: {0}'.format(str(exc)))

        try:
            response = json.loads(response.text)
        except Exception:
            response = {'text': response.text}
            pass

        return response

    def delete_api(self):
        '''
        Deletes specified Api instance in the specified subscription and resource group.

        :return: True
        '''
        # self.log('Deleting the Api instance {0}'.format(self.))
        try:
            response = self.mgmt_client.query(self.url,
                                              'DELETE',
                                              self.query_parameters,
                                              self.header_parameters,
                                              None,
                                              self.status_code)
        except CloudError as e:
            self.log('Error attempting to delete the Api instance.')
            self.fail('Error deleting the Api instance: {0}'.format(str(e)))

        return True

    def get_api(self):
        '''
        Gets the properties of the specified Api.

        :return: deserialized Api instance state dictionary
        '''
        # self.log('Checking if the Api instance {0} is present'.format(self.))
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
            # self.log("Api instance : {0} found".format(response.name))
        except CloudError as e:
            self.log('Did not find the Api instance.')
        if found is True:
            return response

        return False


def main():
    """Main execution"""
    AzureRMApi()


if __name__ == '__main__':
    main()
