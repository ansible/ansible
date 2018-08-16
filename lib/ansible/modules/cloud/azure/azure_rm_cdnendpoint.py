#!/usr/bin/python
#
# Copyright (c) 2018 Hai Cao, <t-haicao@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: azure_rm_cdnendpoint
version_added: "2.7"
short_description: Manage a CDN endpoint.
description:
    - Create, update and delete a CDN endpoint.

options:
    resource_group:
        description:
            - Name of a resource group where the CDN endpoint exists or will be created.
        required: true
    name:
        description:
            - Name of the CDN endpoint.
        required: true
    state:
        description:
            - Assert the state of the CDN endpoint. Use C(present) to create or update a CDN endpoint and C(absent) to delete it.
        default: present
        choices:
            - absent
            - present
    location:
        description:
            - Valid azure location. Defaults to location of the resource group.
extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Hai Cao <t-haicao@microsoft.com>"
'''

EXAMPLES = '''
'''
RETURN = '''
state:
    description: Current state of the CDN endpoint
    returned: always
    type: dict
    example:
'''
from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from azure.mgmt.cdn.models import Endpoint, DeepCreatedOrigin, EndpointUpdateParameters, QueryStringCachingBehavior, ErrorResponseException
except ImportError:
    # This is handled in azure_rm_common
    pass


def cdnendpoint_to_dict(cdnendpoint):
    return dict(
        id=cdnendpoint.id,
        name=cdnendpoint.name,
        type=cdnendpoint.type,
        location=cdnendpoint.location,
        tags=cdnendpoint.tags,
        origin_host_header=cdnendpoint.origin_host_header,
        origin_path=cdnendpoint.origin_path,
        content_types_to_compress=cdnendpoint.content_types_to_compress,
        is_compression_enabled=cdnendpoint.is_compression_enabled,
        is_http_allowed=cdnendpoint.is_http_allowed,
        is_https_allowed=cdnendpoint.is_https_allowed,
        query_string_caching_behavior=cdnendpoint.query_string_caching_behavior,
        optimization_type=cdnendpoint.optimization_type,
        probe_path=cdnendpoint.probe_path,
        geo_filters=[geo_filter_to_dict(geo_filter) for geo_filter in cdnendpoint.geo_filters] if cdnendpoint.geo_filters else None,
        host_name=cdnendpoint.host_name,
        origins=[deep_created_origin_to_dict(origin) for origin in cdnendpoint.origins] if cdnendpoint.origins else None,
        resource_state=cdnendpoint.resource_state,
        provisioning_state=cdnendpoint.provisioning_state
    )

def deep_created_origin_to_dict(origin):
    return dict(
        name=origin.name,
        host_name=origin.host_name,
        http_port=origin.http_port,
        https_port=origin.https_port,
    )

def geo_filter_to_dict(geo_filter):
    return dict(
        relative_path=geo_filter.relative_path,
        action=geo_filter.action,
        country_codes=geo_filter.country_codes,
    )

def default_content_types():
    return ["text/plain",
            "text/html",
            "text/css",
            "text/javascript",
            "application/x-javascript",
            "application/javascript",
            "application/json",
            "application/xml"]

origin_spec=dict(
    name=dict(
        type='str',
        required=True
    ),
    host_name=dict(
        type='str',
        required=True
    ),
    http_port=dict(
        type='int'
    ),
    https_port=dict(
        type='int'
    )
)


class AzureRMCdnendpoint(AzureRMModuleBase):

    def __init__(self):
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                required=True
            ),
            name=dict(
                type='str',
                required=True
            ),
            location=dict(
                type='str'
            ),
            state=dict(
                type='str',
                default='present',
                choices=['present', 'absent']
            ),
            started=dict(
                type='bool'
            ),
            profile_name=dict(
                type='str',
                required=True
            ),
            origin=dict(
                type='dict',
                options=origin_spec
            ),
            origin_host_header=dict(
                type='str',
            ),
            origin_path=dict(
                type='str',
            ),
            content_types_to_compress=dict(
                type='list',
                elements='str',
            ),
            is_compression_enabled=dict(
                type='bool',
            ),
            is_http_allowed=dict(
                type='bool',
            ),
            is_https_allowed=dict(
                type='bool',
            ),
            query_string_caching_behavior=dict(
                type='str',
                choices=[
                    'IgnoreQueryString',
                    'BypassCaching',
                    'UseQueryString',
                    'NotSet'
                ]
            ),
        )

        self.resource_group=None
        self.name=None
        self.state=None
        self.started=None
        self.location=None
        self.profile_name=None
        self.origin=None
        self.tags=None
        self.origin_host_header=None
        self.origin_path=None
        self.content_types_to_compress=None
        self.is_compression_enabled=None
        self.is_http_allowed=None
        self.is_https_allowed=None
        self.query_string_caching_behavior=None

        self.results = dict(changed=False)

        super(AzureRMCdnendpoint, self).__init__(derived_arg_spec=self.module_arg_spec,
                                                supports_check_mode=True,
                                                supports_tags=True)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        to_be_updated = False

        resource_group = self.get_resource_group(self.resource_group)
        if not self.location:
            self.location = resource_group.location

        response = self.get_cdnendpoint()

        if self.state == 'present':

            if not response and self.started is None:
                if self.origin == None:
                    self.fail("Origin is not provided when trying to create endpoint")
                self.log("Need to create the CDN endpoint")

                if not self.check_mode:
                    self.results = self.create_cdnendpoint()
                    self.log("Creation done")

                self.results['changed'] = True
                return self.results

            elif not response and self.started is not None:
                self.log("Can't stop/stop a non-existed endpoint")
                self.fail("This endpoint is not found, stop/start is forbidden")

            else:
                self.log('Results : {0}'.format(response))
                update_tags, response['tags'] = self.update_tags(response['tags'])

                if response['provisioning_state'] == "Succeeded":

                    if self.started == False and response['resource_state'] == 'Running':
                        self.log("Need to stop the CDN endpoint")

                        if not self.check_mode:
                            self.results = self.stop_cdnendpoint()
                            self.log("Endpoint stopped")

                        self.results['changed'] = True
                        return self.results

                    elif self.started and response['resource_state'] == 'Stopped':
                        self.log("Need to start the CDN endpoint")

                        if not self.check_mode:
                            self.results = self.start_cdnendpoint()
                            self.log("Endpoint stopped")

                        self.results['changed'] = True
                        return self.results

                    elif self.started is not None:
                        self.log("Start/Stop not performed due to current resource state")
                        self.results=response
                        self.results['changed'] = False
                        return self.results

                    if update_tags:
                        to_be_updated = True

                    to_be_updated = to_be_updated or self.check_update(response)

                    if to_be_updated:
                        self.log("Need to update the CDN endpoint")

                        if not self.check_mode:
                            self.results = self.update_cdnendpoint()
                            self.log("Update done")

                        self.results['changed'] = True
                        return self.results

        elif self.state == 'absent' and response:
            self.log("Need to delete the CDN endpoint")
            self.results['changed'] = True

            if not self.check_mode:
                self.delete_cdnendpoint()
                self.log("CDN endpoint deleted")

            return self.results

        return self.results

    def create_cdnendpoint(self):
        '''
        Creates a Azure CDN endpoint.

        :return: deserialized Azure CDN endpoint instance state dictionary
        '''
        self.log("Creating the Azure CDN endpoint instance {0}".format(self.name))

        parameters = Endpoint(
            origins=[
                DeepCreatedOrigin(
                    name=self.origin['name'],
                    host_name=self.origin['host_name'],
                    http_port=self.origin['http_port'],
                    https_port=self.origin['https_port'],
                )
            ],
            location=self.location,
            tags=self.tags,
            origin_host_header=self.origin_host_header,
            origin_path=self.origin_path,
            content_types_to_compress=default_content_types() if self.is_compression_enabled and not self.content_types_to_compress else self.content_types_to_compress,
            is_compression_enabled=self.is_compression_enabled if self.is_compression_enabled is not None else False,
            is_http_allowed=self.is_http_allowed if self.is_http_allowed is not None else True,
            is_https_allowed=self.is_https_allowed if self.is_https_allowed is not None else True,
            query_string_caching_behavior=QueryStringCachingBehavior[self.query_string_caching_behavior] if self.query_string_caching_behavior else QueryStringCachingBehavior.ignore_query_string
        )

        try:
            poller = self.cdn_management_client.endpoints.create(self.resource_group, self.profile_name, self.name, parameters)
            response = self.get_poller_result(poller)
            return cdnendpoint_to_dict(response)
        except ErrorResponseException as exc:
            self.log('Error attempting to create Azure CDN endpoint instance.')
            self.fail("Error creating Azure CDN endpoint instance: {0}".format(exc.message))

    def update_cdnendpoint(self):
        '''
        Updates a Azure CDN endpoint.

        :return: deserialized Azure CDN endpoint instance state dictionary
        '''
        self.log("Updating the Azure CDN endpoint instance {0}".format(self.name))

        endpoint_update_properties = EndpointUpdateParameters(
            tags=self.tags,
            origin_host_header=self.origin_host_header,
            origin_path=self.origin_path,
            content_types_to_compress=default_content_types() if self.is_compression_enabled and not self.content_types_to_compress else self.content_types_to_compress,
            is_compression_enabled=self.is_compression_enabled,
            is_http_allowed=self.is_http_allowed,
            is_https_allowed=self.is_https_allowed,
            query_string_caching_behavior=self.query_string_caching_behavior,
        )

        try:
            poller = self.cdn_management_client.endpoints.update(self.resource_group, self.profile_name, self.name, endpoint_update_properties)
            response = self.get_poller_result(poller)
            return cdnendpoint_to_dict(response)
        except ErrorResponseException as exc:
            self.log('Error attempting to update Azure CDN endpoint instance.')
            self.fail("Error updating Azure CDN endpoint instance: {0}".format(exc.message))

    def delete_cdnendpoint(self):
        '''
        Deletes the specified Azure CDN endpoint in the specified subscription and resource group.

        :return: True
        '''
        self.log("Deleting the CDN endpoint {0}".format(self.name))
        try:
            poller = self.cdn_management_client.endpoints.delete(
                self.resource_group, self.profile_name, self.name)
            self.get_poller_result(poller)
            return True
        except ErrorResponseException as e:
            self.log('Error attempting to delete the CDN endpoint.')
            self.fail("Error deleting the CDN endpoint: {0}".format(e.message))
            return False

    def get_cdnendpoint(self):
        '''
        Gets the properties of the specified CDN endpoint.

        :return: deserialized CDN endpoint state dictionary
        '''
        self.log(
            "Checking if the CDN endpoint {0} is present".format(self.name))
        try:
            response = self.cdn_management_client.endpoints.get(self.resource_group, self.profile_name, self.name)
            self.log("Response : {0}".format(response))
            self.log("CDN endpoint : {0} found".format(response.name))
            return cdnendpoint_to_dict(response)
        except ErrorResponseException:
            self.log('Did not find the CDN endpoint.')
            return False

    def start_cdnendpoint(self):
        '''
        Starts an existing CDN endpoint that is on a stopped state.

        :return: deserialized CDN endpoint state dictionary
        '''
        self.log(
            "Starting the CDN endpoint {0}".format(self.name))
        try:
            poller = self.cdn_management_client.endpoints.start(self.resource_group, self.profile_name, self.name)
            response = self.get_poller_result(poller)
            self.log("Response : {0}".format(response))
            self.log("CDN endpoint : {0} started".format(response.name))
            return self.get_cdnendpoint()
        except ErrorResponseException:
            self.log('Fail to start the CDN endpoint.')
            return False

    def stop_cdnendpoint(self):
        '''
        Stops an existing CDN endpoint that is on a running state.

        :return: deserialized CDN endpoint state dictionary
        '''
        self.log(
            "Stopping the CDN endpoint {0}".format(self.name))
        try:
            poller = self.cdn_management_client.endpoints.stop(self.resource_group, self.profile_name, self.name)
            response = self.get_poller_result(poller)
            self.log("Response : {0}".format(response))
            self.log("CDN endpoint : {0} stopped".format(response.name))
            return self.get_cdnendpoint()
        except ErrorResponseException:
            self.log('Fail to stop the CDN endpoint.')
            return False

    def check_update(self, response):
            
        if response['tags'] != self.tags:
            self.log("Tags Diff - Origin {0} / Update {1}".format(response['tags'], self.tags))
            return True
            
        if self.origin_host_header and response['origin_host_header'] != self.origin_host_header:
            self.log("Origin host header Diff - Origin {0} / Update {1}".format(response['origin_host_header'], self.origin_host_header))
            return True
            
        if self.origin_path and response['origin_path'] != self.origin_path:
            self.log("Origin path Diff - Origin {0} / Update {1}".format(response['origin_path'], self.origin_path))
            return True
            
        if self.content_types_to_compress and response['content_types_to_compress'] != self.content_types_to_compress:
            self.log("Content types to compress Diff - Origin {0} / Update {1}".format(response['content_types_to_compress'], self.content_types_to_compress))
            return True

        if self.is_compression_enabled is not None and response['is_compression_enabled'] != self.is_compression_enabled:
            self.log("is_compression_enabled Diff - Origin {0} / Update {1}".format(response['is_compression_enabled'], self.is_compression_enabled))
            return True
            
        if self.is_http_allowed is not None and response['is_http_allowed'] != self.is_http_allowed:
            self.log("is_http_allowed Diff - Origin {0} / Update {1}".format(response['is_http_allowed'], self.is_http_allowed))
            return True

        if self.is_https_allowed is not None and response['is_https_allowed'] != self.is_https_allowed:
            self.log("is_https_allowed Diff - Origin {0} / Update {1}".format(response['is_https_allowed'], self.is_https_allowed))
            return True
            
        if self.query_string_caching_behavior and response['query_string_caching_behavior'] != self.query_string_caching_behavior:
            self.log("query_string_caching_behavior Diff - Origin {0} / Update {1}".format(response['query_string_caching_behavior'], self.query_string_caching_behavior))
            return True

        return False



def main():
    """Main execution"""
    AzureRMCdnendpoint()


if __name__ == '__main__':
    main()
