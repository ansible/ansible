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
module: azure_rm_resource_facts
version_added: "2.6"
short_description: Generic facts of Azure resources.
description:
  - Obtain facts of any resource using Azure REST API.
  - This module gives access to resources that are not supported via Ansible modules.
  - Refer to https://docs.microsoft.com/en-us/rest/api/ regarding details related to specific resource REST API.

options:
  url:
    description:
      - Azure RM Resource URL.
  api_version:
    description:
      - Specific API version to be used.
  provider:
    description:
      - Provider type, should be specified in no URL is given
  resource_group:
    description:
      - Resource group to be used.
      - Required if URL is not specified.
  resource_type:
    description:
      - Resource type.
  resource_name:
    description:
      - Resource name.
  subresource:
    description:
      - List of subresources
    suboptions:
      namespace:
        description:
          - Subresource namespace
      type:
        description:
          - Subresource type
      name:
        description:
          - Subresource name

extends_documentation_fragment:
  - azure

author:
  - "Zim Kalinowski (@zikalino)"

'''

EXAMPLES = '''
  - name: Get scaleset info
    azure_rm_resource_facts:
      resource_group: myResourceGroup
      provider: compute
      resource_type: virtualmachinescalesets
      resource_name: myVmss
      api_version: "2017-12-01"

  - name: Query all the resources in the resource group
    azure_rm_resource_facts:
      resource_group: "{{ resource_group }}"
      resource_type: resources
'''

RETURN = '''
response:
    description: Response specific to resource type.
    returned: always
    type: dict
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase
from ansible.module_utils.azure_rm_common_rest import GenericRestClient

try:
    from msrestazure.azure_exceptions import CloudError
    from msrest.service_client import ServiceClient
    from msrestazure.tools import resource_id, is_valid_resource_id
    import json

except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMResourceFacts(AzureRMModuleBase):
    def __init__(self):
        # define user inputs into argument
        self.module_arg_spec = dict(
            url=dict(
                type='str'
            ),
            provider=dict(
                type='str'
            ),
            resource_group=dict(
                type='str'
            ),
            resource_type=dict(
                type='str'
            ),
            resource_name=dict(
                type='str'
            ),
            subresource=dict(
                type='list',
                default=[]
            ),
            api_version=dict(
                type='str'
            )
        )
        # store the results of the module operation
        self.results = dict(
            response=[]
        )
        self.mgmt_client = None
        self.url = None
        self.api_version = None
        self.provider = None
        self.resource_group = None
        self.resource_type = None
        self.resource_name = None
        self.subresource = []
        super(AzureRMResourceFacts, self).__init__(self.module_arg_spec, supports_tags=False)

    def exec_module(self, **kwargs):
        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])
        self.mgmt_client = self.get_mgmt_svc_client(GenericRestClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        if self.url is None:
            orphan = None
            rargs = dict()
            rargs['subscription'] = self.subscription_id
            rargs['resource_group'] = self.resource_group
            if not (self.provider is None or self.provider.lower().startswith('.microsoft')):
                rargs['namespace'] = "Microsoft." + self.provider
            else:
                rargs['namespace'] = self.provider

            if self.resource_type is not None and self.resource_name is not None:
                rargs['type'] = self.resource_type
                rargs['name'] = self.resource_name
                for i in range(len(self.subresource)):
                    resource_ns = self.subresource[i].get('namespace', None)
                    resource_type = self.subresource[i].get('type', None)
                    resource_name = self.subresource[i].get('name', None)
                    if resource_type is not None and resource_name is not None:
                        rargs['child_namespace_' + str(i + 1)] = resource_ns
                        rargs['child_type_' + str(i + 1)] = resource_type
                        rargs['child_name_' + str(i + 1)] = resource_name
                    else:
                        orphan = resource_type
            else:
                orphan = self.resource_type

            self.url = resource_id(**rargs)

            if orphan is not None:
                self.url += '/' + orphan

        # if api_version was not specified, get latest one
        if not self.api_version:
            try:
                # extract provider and resource type
                if "/providers/" in self.url:
                    provider = self.url.split("/providers/")[1].split("/")[0]
                    resourceType = self.url.split(provider + "/")[1].split("/")[0]
                    url = "/subscriptions/" + self.subscription_id + "/providers/" + provider
                    api_versions = json.loads(self.mgmt_client.query(url, "GET", {'api-version': '2015-01-01'}, None, None, [200], 0, 0).text)
                    for rt in api_versions['resourceTypes']:
                        if rt['resourceType'].lower() == resourceType.lower():
                            self.api_version = rt['apiVersions'][0]
                            break
                else:
                    # if there's no provider in API version, assume Microsoft.Resources
                    self.api_version = '2018-05-01'
                if not self.api_version:
                    self.fail("Couldn't find api version for {0}/{1}".format(provider, resourceType))
            except Exception as exc:
                self.fail("Failed to obtain API version: {0}".format(str(exc)))

        self.results['url'] = self.url

        query_parameters = {}
        query_parameters['api-version'] = self.api_version

        header_parameters = {}
        header_parameters['Content-Type'] = 'application/json; charset=utf-8'
        skiptoken = None

        while True:
            if skiptoken:
                query_parameters['skiptoken'] = skiptoken
            response = self.mgmt_client.query(self.url, "GET", query_parameters, header_parameters, None, [200, 404], 0, 0)
            try:
                response = json.loads(response.text)
                if isinstance(response, dict):
                    if response.get('value'):
                        self.results['response'] = self.results['response'] + response['value']
                        skiptoken = response.get('nextLink')
                    else:
                        self.results['response'] = self.results['response'] + [response]
            except Exception as e:
                self.fail('Failed to parse response: ' + str(e))
            if not skiptoken:
                break
        return self.results


def main():
    AzureRMResourceFacts()


if __name__ == '__main__':
    main()
