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
    required: yes
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
      resource_group: "{{ resource_group }}"
      provider: compute
      resource_type: virtualmachinescalesets
      resource_name: "{{ scaleset_name }}"
      api_version: "2017-12-01"
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
                type='str',
                required=False
            ),
            provider=dict(
                type='str',
                required=False
            ),
            resource_group=dict(
                type='str',
                required=False
            ),
            resource_type=dict(
                type='str',
                required=False
            ),
            resource_name=dict(
                type='str',
                required=False
            ),
            subresource=dict(
                type='list',
                required=False,
                default=[]
            ),
            api_version=dict(
                type='str',
                required=True
            )
        )
        # store the results of the module operation
        self.results = dict(
            response=None
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
            rargs = dict()
            rargs['subscription'] = self.subscription_id
            rargs['resource_group'] = self.resource_group
            if not (self.provider is None or self.provider.lower().startswith('.microsoft')):
                rargs['namespace'] = "Microsoft." + self.provider
            else:
                rargs['namespace'] = self.provider
            rargs['type'] = self.resource_type
            rargs['name'] = self.resource_name

            for i in range(len(self.subresource)):
                rargs['child_namespace_' + str(i + 1)] = self.subresource[i].get('namespace', None)
                rargs['child_type_' + str(i + 1)] = self.subresource[i].get('type', None)
                rargs['child_name_' + str(i + 1)] = self.subresource[i].get('name', None)

            self.url = resource_id(**rargs)

            # this is to fix a problem with resource_id implementation, when resource_name is not specified
            if self.resource_type is not None and self.resource_name is None:
                self.url += '/' + self.resource_type

        self.results['url'] = self.url

        query_parameters = {}
        query_parameters['api-version'] = self.api_version

        header_parameters = {}
        header_parameters['Content-Type'] = 'application/json; charset=utf-8'

        response = self.mgmt_client.query(self.url, "GET", query_parameters, header_parameters, None, [200, 404])

        try:
            response = json.loads(response.text)
            if response is list:
                self.results['response'] = response
            else:
                self.results['response'] = [response]
        except:
            self.results['response'] = []

        return self.results


def main():
    AzureRMResourceFacts()


if __name__ == '__main__':
    main()
