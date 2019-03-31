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
module: azure_rm_apimanagementservice
version_added: '2.8'
short_description: Manage Azure ApiManagementService instance.
description:
  - 'Create, update and delete instance of Azure ApiManagementService.'
options:
  resource_group_name:
    description:
      - The name of the resource group.
  service_name:
    description:
      - The name of the API Management service.
  properties:
    description:
      - Properties of the API Management service.
    required: true
    suboptions:
      publisher_email:
        description:
          - Publisher email.
        required: true
      publisher_name:
        description:
          - Publisher name.
        required: true
  sku:
    description:
      - SKU properties of the API Management service.
    required: true
    suboptions:
      name:
        description:
          - Name of the Sku.
        required: true
      capacity:
        description:
          - >-
            Capacity of the SKU (number of deployed units of the SKU). The
            default value is 1.
  identity:
    description:
      - Managed service identity of the Api Management service.
    suboptions:
      type:
        description:
          - >-
            The identity type. Currently the only supported type is
            'SystemAssigned'.
        required: true
  location:
    description:
      - Resource location.
    required: true
  state:
    description:
      - Assert the state of the ApiManagementService.
      - >-
        Use C(present) to create or update an ApiManagementService and C(absent)
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
- name: ApiManagementCreateService
  azure_rm_apimanagementservice:
    serviceName: apimService1
    resourceGroupName: myResourceGroup
    location: West US
    sku:
      name: Premium
      capacity: '1'
    properties:
      publisherEmail: admin@live.com
      publisherName: contoso
- name: ApiManagementCreateMultiRegionServiceWithCustomHostname
  azure_rm_apimanagementservice:
    serviceName: apimService1
    resourceGroupName: myResourceGroup
    location: Central US
    sku:
      name: Premium
      capacity: '1'
    properties:
      publisherEmail: admin@live.com
      publisherName: contoso
      additionalLocations:
        - location: West US
          sku:
            name: Premium
            capacity: '1'
          virtualNetworkConfiguration:
            subnetResourceId: >-
              /subscriptions/{{ subscription_id }}/resourceGroups/{{
              resource_group }}/providers/Microsoft.Network/virtualNetworks/{{
              virtual_network_name }}/subnets/{{ subnet_name }}
      hostnameConfigurations:
        - type: Proxy
          hostName: proxyhostname1.contoso.com
          encodedCertificate: '************Base 64 Encoded Pfx Certificate************************'
          certificatePassword: >-
            **************Password of the
            Certificate************************************************
        - type: Proxy
          hostName: proxyhostname2.contoso.com
          encodedCertificate: '************Base 64 Encoded Pfx Certificate************************'
          certificatePassword: >-
            **************Password of the
            Certificate************************************************
          negotiateClientCertificate: true
        - type: Portal
          hostName: portalhostname1.contoso.com
          encodedCertificate: '************Base 64 Encoded Pfx Certificate************************'
          certificatePassword: >-
            **************Password of the
            Certificate************************************************
      virtualNetworkConfiguration:
        subnetResourceId: >-
          /subscriptions/{{ subscription_id }}/resourceGroups/{{ resource_group
          }}/providers/Microsoft.Network/virtualNetworks/{{ virtual_network_name
          }}/subnets/{{ subnet_name }}
      virtualNetworkType: External
- name: ApiManagementCreateServiceHavingMsi
  azure_rm_apimanagementservice:
    serviceName: apimService1
    resourceGroupName: myResourceGroup
    location: Japan East
    properties:
      publisherEmail: admin@contoso.com
      publisherName: Contoso
    sku:
      name: Developer
    identity:
      type: SystemAssigned
- name: ApiManagementCreateServiceWithSystemCertificates
  azure_rm_apimanagementservice:
    serviceName: apimService1
    resourceGroupName: myResourceGroup
    location: Central US
    tags:
      tag1: value1
      tag2: value2
      tag3: value3
    sku:
      name: Basic
      capacity: '1'
    properties:
      publisherEmail: apim@autorestsdk.com
      publisherName: autorestsdk
      certificates:
        - encodedCertificate: '************Base 64 Encoded Pfx Certificate************************'
          certificatePassword: >-
            **************Password of the
            Certificate************************************************
          storeName: CertificateAuthority

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


class AzureRMApiManagementService(AzureRMModuleBase):
    """Configuration class for an Azure RM ApiManagementService resource"""

    def __init__(self):
        self.module_arg_spec = dict(
            resource_group_name=dict(
                type='str'
            ),
            service_name=dict(
                type='str'
            ),
            properties=dict(
                type='dict',
                required=True
            ),
            sku=dict(
                type='dict',
                required=True
            ),
            identity=dict(
                type='dict'
            ),
            location=dict(
                type='str',
                required=True
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
        self.status_code = [200, 202]
        self.to_do = Actions.NoAction

        self.body = {}
        self.query_parameters = {}
        self.query_parameters['api-version'] = '2018-01-01'
        self.header_parameters = {}
        self.header_parameters['Content-Type'] = 'application/json; charset=utf-8'

        super(AzureRMApiManagementService, self).__init__(derived_arg_spec=self.module_arg_spec,
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
                elif key == "sku":
                    self.body["sku"] = kwargs[key]
                elif key == "identity":
                    self.body["identity"] = kwargs[key]
                elif key == "location":
                    self.body["location"] = kwargs[key]

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
                    '/{{ service_name }}')
        self.url = self.url.replace('{{ subscription_id }}', self.subscription_id)
        self.url = self.url.replace('{{ resource_group }}', self.resource_group)
        self.url = self.url.replace('{{ service_name }}', self.service_name)

        old_response = self.get_apimanagementservice()

        if not old_response:
            self.log("ApiManagementService instance doesn't exist")

            if self.state == 'absent':
                self.log("Old instance didn't exist")
            else:
                self.to_do = Actions.Create
        else:
            self.log('ApiManagementService instance already exists')

            if self.state == 'absent':
                self.to_do = Actions.Delete
            elif self.state == 'present':
                self.log('Need to check if ApiManagementService instance has to be deleted or may be updated')

        if (self.to_do == Actions.Create) or (self.to_do == Actions.Update):
            self.log('Need to Create / Update the ApiManagementService instance')

            if self.check_mode:
                self.results['changed'] = True
                return self.results

            response = self.create_update_apimanagementservice()

            # if not old_response:
            self.results['changed'] = True
            self.results['response'] = response
            # else:
            #     self.results['changed'] = old_response.__ne__(response)
            self.log('Creation / Update done')
        elif self.to_do == Actions.Delete:
            self.log('ApiManagementService instance deleted')
            self.results['changed'] = True

            if self.check_mode:
                return self.results

            self.delete_apimanagementservice()

            # make sure instance is actually deleted, for some Azure resources, instance is hanging around
            # for some time after deletion -- this should be really fixed in Azure
            while self.get_apimanagementservice():
                time.sleep(20)
        else:
            self.log('ApiManagementService instance unchanged')
            self.results['changed'] = False
            response = old_response

        return self.results

    def rename_key(self, d, old_name, new_name):
        old_value = d.get(old_name, None)
        if old_value is not None:
            d.pop(old_name, None)
            d[new_name] = old_value

    def create_update_apimanagementservice(self):
        '''
        Creates or updates ApiManagementService with the specified configuration.

        :return: deserialized ApiManagementService instance state dictionary
        '''
        # self.log('Creating / Updating the ApiManagementService instance {0}'.format(self.))

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
            self.log('Error attempting to create the ApiManagementService instance.')
            self.fail('Error creating the ApiManagementService instance: {0}'.format(str(exc)))

        try:
            response = json.loads(response.text)
        except Exception:
            response = {'text': response.text}
            pass

        return response

    def delete_apimanagementservice(self):
        '''
        Deletes specified ApiManagementService instance in the specified subscription and resource group.

        :return: True
        '''
        # self.log('Deleting the ApiManagementService instance {0}'.format(self.))
        try:
            response = self.mgmt_client.query(self.url,
                                              'DELETE',
                                              self.query_parameters,
                                              self.header_parameters,
                                              None,
                                              self.status_code)
        except CloudError as e:
            self.log('Error attempting to delete the ApiManagementService instance.')
            self.fail('Error deleting the ApiManagementService instance: {0}'.format(str(e)))

        return True

    def get_apimanagementservice(self):
        '''
        Gets the properties of the specified ApiManagementService.

        :return: deserialized ApiManagementService instance state dictionary
        '''
        # self.log('Checking if the ApiManagementService instance {0} is present'.format(self.))
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
            # self.log("ApiManagementService instance : {0} found".format(response.name))
        except CloudError as e:
            self.log('Did not find the ApiManagementService instance.')
        if found is True:
            return response

        return False


def main():
    """Main execution"""
    AzureRMApiManagementService()


if __name__ == '__main__':
    main()
