#!/usr/bin/python
#
# Copyright (c) 2019 Hai Cao, <t-haicao@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: azure_rm_cdnendpoint_info

version_added: "2.9"

short_description: Get Azure CDN endpoint facts

description:
    - Get facts for a specific Azure CDN endpoint or all Azure CDN endpoints.

options:
    resource_group:
        description:
            - Name of resource group where this CDN profile belongs to.
        required: true
    profile_name:
        description:
            - Name of CDN profile.
        required: true
    name:
        description:
            - Limit results to a specific Azure CDN endpoint.
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.

extends_documentation_fragment:
    - azure

author:
    - Hai Cao (@caohai)
    - Yunge zhu (@yungezz)
'''

EXAMPLES = '''
  - name: Get facts for all endpoints in CDN profile
    azure_rm_cdnendpoint_info:
      resource_group: myResourceGroup
      profile_name: myCDNProfile

  - name: Get facts of specific CDN endpoint
    azure_rm_cdnendpoint_info:
      resource_group: myResourceGroup
      profile_name: myCDNProfile
      name: myEndpoint1
'''

RETURN = '''
cdnendpoints:
    description: List of Azure CDN endpoints.
    returned: always
    type: complex
    contains:
        resource_group:
            description:
                - Name of a resource group where the Azure CDN endpoint exists.
            returned: always
            type: str
            sample: myResourceGroup
        name:
            description:
                - Name of the Azure CDN endpoint.
            returned: always
            type: str
            sample: myEndpoint
        profile_name:
            description:
                - Name of the Azure CDN profile that this endpoint is attached to.
            returned: always
            type: str
            sample: myProfile
        location:
            description:
                - Location of the Azure CDN endpoint.
            type: str
            sample: WestUS
        id:
            description:
                - ID of the Azure CDN endpoint.
            type: str
            sample:
                "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourcegroups/myCDN/providers/Microsoft.Cdn/profiles/myProfile/endpoints/myEndpoint1"
        provisioning_state:
            description:
                - Provisioning status of the Azure CDN endpoint.
            type: str
            sample: Succeeded
        resource_state:
            description:
                - Resource status of the profile.
            type: str
            sample: Running
        is_compression_enabled:
            description:
                - Indicates whether content compression is enabled on CDN.
            type: bool
            sample: true
        is_http_allowed:
            description:
                - Indicates whether HTTP traffic is allowed on the endpoint.
            type: bool
            sample: true
        is_https_allowed:
            description:
                - Indicates whether HTTPS traffic is allowed on the endpoint.
            type: bool
            sample: true
        query_string_caching_behavior:
            description:
                - Defines how CDN caches requests that include query strings.
            type: str
            sample: IgnoreQueryString
        content_types_to_compress:
            description:
                - List of content types on which compression applies.
            type: list
            sample: [
                "text/plain",
                "text/html",
                "text/css",
                "text/javascript",
                "application/x-javascript",
                "application/javascript",
                "application/json",
                "application/xml"
            ]
        origins:
            description:
                - The source of the content being delivered via CDN.
            sample: {
                "host_name": "xxxxxxxx.blob.core.windows.net",
                "http_port": null,
                "https_port": null,
                "name": "xxxxxxxx-blob-core-windows-net"
            }
        origin_host_header:
            description:
                - The host header value sent to the origin with each request.
            type: str
            sample: xxxxxxxx.blob.core.windows.net
        origin_path:
            description:
                - A directory path on the origin that CDN can use to retrieve content from.
            type: str
            sample: /pic/
        tags:
            description:
                - The tags of the Azure CDN endpoint.
            type: list
            sample: foo
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from azure.mgmt.cdn import CdnManagementClient
    from azure.mgmt.cdn.models import ErrorResponseException
    from azure.common import AzureHttpError
except ImportError:
    # handled in azure_rm_common
    pass

import re

AZURE_OBJECT_CLASS = 'endpoints'


class AzureRMCdnEndpointInfo(AzureRMModuleBase):
    """Utility class to get Azure Azure CDN endpoint facts"""

    def __init__(self):

        self.module_args = dict(
            name=dict(type='str'),
            resource_group=dict(
                type='str',
                required=True
            ),
            profile_name=dict(
                type='str',
                required=True
            ),
            tags=dict(type='list')
        )

        self.results = dict(
            changed=False,
            cdnendpoints=[]
        )

        self.name = None
        self.resource_group = None
        self.profile_name = None
        self.tags = None

        super(AzureRMCdnEndpointInfo, self).__init__(
            derived_arg_spec=self.module_args,
            supports_tags=False,
            facts_module=True
        )

    def exec_module(self, **kwargs):

        is_old_facts = self.module._name == 'azure_rm_cdnendpoint_facts'
        if is_old_facts:
            self.module.deprecate("The 'azure_rm_cdnendpoint_facts' module has been renamed to 'azure_rm_cdnendpoint_info'", version='2.13')

        for key in self.module_args:
            setattr(self, key, kwargs[key])

        self.cdn_client = self.get_mgmt_svc_client(CdnManagementClient,
                                                   base_url=self._cloud_environment.endpoints.resource_manager,
                                                   api_version='2017-04-02')

        if self.name:
            self.results['cdnendpoints'] = self.get_item()
        else:
            self.results['cdnendpoints'] = self.list_by_profile()

        return self.results

    def get_item(self):
        """Get a single Azure Azure CDN endpoint"""

        self.log('Get properties for {0}'.format(self.name))

        item = None
        result = []

        try:
            item = self.cdn_client.endpoints.get(
                self.resource_group, self.profile_name, self.name)
        except ErrorResponseException:
            pass

        if item and self.has_tags(item.tags, self.tags):
            result = [self.serialize_cdnendpoint(item)]

        return result

    def list_by_profile(self):
        """Get all Azure Azure CDN endpoints within an Azure CDN profile"""

        self.log('List all Azure CDN endpoints within an Azure CDN profile')

        try:
            response = self.cdn_client.endpoints.list_by_profile(
                self.resource_group, self.profile_name)
        except ErrorResponseException as exc:
            self.fail('Failed to list all items - {0}'.format(str(exc)))

        results = []
        for item in response:
            if self.has_tags(item.tags, self.tags):
                results.append(self.serialize_cdnendpoint(item))

        return results

    def serialize_cdnendpoint(self, cdnendpoint):
        '''
        Convert a Azure CDN endpoint object to dict.
        :param cdn: Azure CDN endpoint object
        :return: dict
        '''
        result = self.serialize_obj(cdnendpoint, AZURE_OBJECT_CLASS)

        new_result = {}
        new_result['id'] = cdnendpoint.id
        new_result['resource_group'] = re.sub('\\/.*', '', re.sub('.*resourcegroups\\/', '', result['id']))
        new_result['profile_name'] = re.sub('\\/.*', '', re.sub('.*profiles\\/', '', result['id']))
        new_result['name'] = cdnendpoint.name
        new_result['type'] = cdnendpoint.type
        new_result['location'] = cdnendpoint.location
        new_result['resource_state'] = cdnendpoint.resource_state
        new_result['provisioning_state'] = cdnendpoint.provisioning_state
        new_result['query_string_caching_behavior'] = cdnendpoint.query_string_caching_behavior
        new_result['is_compression_enabled'] = cdnendpoint.is_compression_enabled
        new_result['is_http_allowed'] = cdnendpoint.is_http_allowed
        new_result['is_https_allowed'] = cdnendpoint.is_https_allowed
        new_result['content_types_to_compress'] = cdnendpoint.content_types_to_compress
        new_result['origin_host_header'] = cdnendpoint.origin_host_header
        new_result['origin_path'] = cdnendpoint.origin_path
        new_result['origin'] = dict(
            name=cdnendpoint.origins[0].name,
            host_name=cdnendpoint.origins[0].host_name,
            http_port=cdnendpoint.origins[0].http_port,
            https_port=cdnendpoint.origins[0].https_port
        )
        new_result['tags'] = cdnendpoint.tags
        return new_result


def main():
    """Main module execution code path"""

    AzureRMCdnEndpointInfo()


if __name__ == '__main__':
    main()
