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
module: azure_rm_azurefirewall_info
version_added: '2.9'
short_description: Get AzureFirewall info.
description:
  - Get info of AzureFirewall.
options:
  resource_group:
    description:
      - The name of the resource group.
    type: str
  name:
    description:
      - Resource name.
    type: str
extends_documentation_fragment:
  - azure
author:
  - Zim Kalinowski (@zikalino)

'''

EXAMPLES = '''
- name: List all Azure Firewalls for a given subscription
  azure_rm_azurefirewall_info:
- name: List all Azure Firewalls for a given resource group
  azure_rm_azurefirewall_info:
    resource_group: myResourceGroup
- name: Get Azure Firewall
  azure_rm_azurefirewall_info:
    resource_group: myResourceGroup
    name: myAzureFirewall

'''

RETURN = '''
azure_firewalls:
  description: >-
    A list of dict results where the key is the name of the AzureFirewall and
    the values are the facts for that AzureFirewall.
  returned: always
  type: complex
  contains:
    azurefirewall_name:
      description: The key is the name of the server that the values relate to.
      type: complex
      contains:
        id:
          description:
            - Resource ID.
          returned: always
          type: str
          sample: null
        name:
          description:
            - Resource name.
          returned: always
          type: str
          sample: null
        type:
          description:
            - Resource type.
          returned: always
          type: str
          sample: null
        location:
          description:
            - Resource location.
          returned: always
          type: str
          sample: null
        tags:
          description:
            - Resource tags.
          returned: always
          sample: null
        properties:
          returned: always
          type: dict
          sample: null
        etag:
          description:
            - >-
              Gets a unique read-only string that changes whenever the resource
              is updated.
          returned: always
          type: str
          sample: null

'''

import time
import json
from ansible.module_utils.azure_rm_common import AzureRMModuleBase
from ansible.module_utils.azure_rm_common_rest import GenericRestClient
from copy import deepcopy
try:
    from msrestazure.azure_exceptions import CloudError
except Exception:
    # handled in azure_rm_common
    pass

class AzureRMAzureFirewallsInfo(AzureRMModuleBase):
    def __init__(self):
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str'
            ),
            name=dict(
                type='str'
            )
        )

        self.resource_group = None
        self.name = None

        self.results = dict(changed=False)
        self.mgmt_client = None
        self.state = None
        self.url = None
        self.status_code = [200]

        self.query_parameters = {}
        self.query_parameters['api-version'] = '2018-11-01'
        self.header_parameters = {}
        self.header_parameters['Content-Type'] = 'application/json; charset=utf-8'

        self.mgmt_client = None
        super(AzureRMAzureFirewallsInfo, self).__init__(self.module_arg_spec, supports_tags=True)

    def exec_module(self, **kwargs):

        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        self.mgmt_client = self.get_mgmt_svc_client(GenericRestClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        if (self.resource_group is not None and self.name is not None):
            # self.results['azure_firewalls'] = self.format_item(self.get())
            self.results['azure_firewalls'] = self.get()
        elif (self.resource_group is not None):
            # self.results['azure_firewalls'] = self.format_item(self.list())
            self.results['azure_firewalls'] = self.list()
        else:
            # self.results['azure_firewalls'] = [self.format_item(self.listall())]
            self.results['azure_firewalls'] = self.listall()
        return self.results

    def get(self):
        response = None
        results = {}
        # prepare url
        self.url = ('/subscriptions' +
                    '/{{ subscription_id }}' +
                    '/resourceGroups' +
                    '/{{ resource_group }}' +
                    '/providers' +
                    '/Microsoft.Network' +
                    '/azureFirewalls' +
                    '/{{ azure_firewall_name }}')
        self.url = self.url.replace('{{ subscription_id }}', self.subscription_id)
        self.url = self.url.replace('{{ resource_group }}', self.resource_group)
        self.url = self.url.replace('{{ azure_firewall_name }}', self.name)

        try:
            response = self.mgmt_client.query(self.url,
                                              'GET',
                                              self.query_parameters,
                                              self.header_parameters,
                                              None,
                                              self.status_code,
                                              600,
                                              30)
            results = json.loads(response.text)
            # self.log('Response : {0}'.format(response))
        except CloudError as e:
            self.log('Could not get info for @(Model.ModuleOperationNameUpper).')

        return results

    def list(self):
        response = None
        results = {}
        # prepare url
        self.url = ('/subscriptions' +
                    '/{{ subscription_id }}' +
                    '/resourceGroups' +
                    '/{{ resource_group }}' +
                    '/providers' +
                    '/Microsoft.Network' +
                    '/azureFirewalls')
        self.url = self.url.replace('{{ subscription_id }}', self.subscription_id)
        self.url = self.url.replace('{{ resource_group }}', self.resource_group)

        try:
            response = self.mgmt_client.query(self.url,
                                              'GET',
                                              self.query_parameters,
                                              self.header_parameters,
                                              None,
                                              self.status_code,
                                              600,
                                              30)
            results = json.loads(response.text)
            # self.log('Response : {0}'.format(response))
        except CloudError as e:
            self.log('Could not get info for @(Model.ModuleOperationNameUpper).')

        return results

    def listall(self):
        response = None
        results = {}
        # prepare url
        self.url = ('/subscriptions' +
                    '/{{ subscription_id }}' +
                    '/providers' +
                    '/Microsoft.Network' +
                    '/azureFirewalls')
        self.url = self.url.replace('{{ subscription_id }}', self.subscription_id)

        try:
            response = self.mgmt_client.query(self.url,
                                              'GET',
                                              self.query_parameters,
                                              self.header_parameters,
                                              None,
                                              self.status_code,
                                              600,
                                              30)
            results = json.loads(response.text)
            # self.log('Response : {0}'.format(response))
        except CloudError as e:
            self.log('Could not get info for @(Model.ModuleOperationNameUpper).')

        return results


def main():
    AzureRMAzureFirewallsInfo()


if __name__ == '__main__':
    main()
