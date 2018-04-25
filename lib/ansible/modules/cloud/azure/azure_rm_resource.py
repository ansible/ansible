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
module: azure_rm_resource
version_added: "2.6"
short_description: Create any Azure resource.
description:
  - Create, update or delete any Azure resource using Azure REST API.
  - This module gives access to resources that are not supported via Ansible modules.
  - Refer to https://docs.microsoft.com/en-us/rest/api/ regarding details related to specific resource REST API.

options:
  url:
    description:
      - Azure RM Resource URL.
  provider:
    description:
      - Provider type.
      - Required if URL is not specified.
  resource_group:
    description:
      - Resource group to be used.
      - Required if URL is not specified.
  resource_type:
    description:
      - Resource type.
      - Required if URL is not specified.
  resource_name:
    description:
      - Resource name.
      - Required if URL Is not specified.
  subresource:
    description:
      - List of subresources
    type: list
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
  body:
    description:
      - The body of the http request/response to the web service.
  method:
    description:
      - The HTTP method of the request or response. It MUST be uppercase.
        choices: [ "GET", "PUT", "POST", "HEAD", "PATCH", "DELETE", "MERGE" ]
        default: "PUT"
  status_code:
    description:
      - A valid, numeric, HTTP status code that signifies success of the
        request. Can also be comma separated list of status codes.
    default: [ 200, 201, 202 ]
  state:
    description:
      - Assert the state of the resource. Use C(present) to create or update resource or C(absent) to delete resource.
    default: present
    choices:
        - absent
        - present

extends_documentation_fragment:
  - azure

author:
  - "Zim Kalinowski (@zikalino)"

'''

EXAMPLES = '''
  - name: Update scaleset info using azure_rm_resource
    azure_rm_resource:
      resource_group: "{{ resource_group }}"
      provider: compute
      resource_type: virtualmachinescalesets
      resource_name: "{{ scaleset_name }}"
      api_version: "2017-12-01"
      body: "{{ body }}"
'''

RETURN = '''
response:
    description: Response specific to resource type.
    returned: always
    type: dict
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase
from ansible.module_utils.azure_rm_common_rest import GenericRestClient
from msrestazure.tools import resource_id, is_valid_resource_id

try:
    from msrestazure.azure_exceptions import CloudError
    from msrestazure import AzureConfiguration
    from msrest.service_client import ServiceClient
    import json

except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMResource(AzureRMModuleBase):
    def __init__(self):
        # define user inputs into argument
        self.module_arg_spec = dict(
            url=dict(
                type='str',
                required=False
            ),
            provider=dict(
                type='str',
            ),
            resource_group=dict(
                type='str',
            ),
            resource_type=dict(
                type='str',
            ),
            resource_name=dict(
                type='str',
            ),
            subresource=dict(
                type='list',
                default=[]
            ),
            api_version=dict(
                type='str',
                required=True
            ),
            method=dict(
                type='str',
                default='PUT',
                choices=[ "GET", "PUT", "POST", "HEAD", "PATCH", "DELETE", "MERGE" ]
            ),
            body=dict(
                type='raw'
            ),
            status_code=dict(
                type='list',
                default=[200, 201, 202]
            ),
            state=dict(
                type='str',
                default='present',
                choices=['present', 'absent']
            )
        )
        # store the results of the module operation
        self.results = dict(
            changed=False,
            response=None
        )
        self.mgmt_client = None
        self.url = None
        self.api_version = None
        self.provider = None
        self.resource_group = None
        self.resource_type = None
        self.resource_name = None
        self.subresource_type = None
        self.subresource_name = None
        self.method = None
        self.status_code = []
        self.state = None
        super(AzureRMResource, self).__init__(self.module_arg_spec)

    def exec_module(self, **kwargs):
        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])
        self.mgmt_client = self.get_mgmt_svc_client(GenericRestClient,
                                                    base_url=self._cloud_environment.endpoints.resource_manager)

        if self.state == 'absent':
            self.method = 'DELETE'
            self.status_code.append(204)

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
            
        query_parameters = {}
        query_parameters['api-version'] = self.api_version

        header_parameters = {}
        header_parameters['Content-Type'] = 'application/json; charset=utf-8'

        response = self.mgmt_client.query(self.url, self.method, query_parameters, header_parameters, self.body, self.status_code)

        try:
            self.results['response'] = json.loads(response.text)
        except:
            self.results['response'] = response.text

        self.results['changed'] = True

        if self.state == 'absent' and response.status_code == 204:
            self.results['changed'] = False

        return self.results


def main():
    AzureRMResource()
if __name__ == '__main__':
    main()
