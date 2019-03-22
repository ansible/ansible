#!/usr/bin/python
#
# Copyright (c) 2018 Hai Cao, <t-haicao@microsoft.com>, Yunge Zhu <yungez@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: azure_rm_cdnprofile_facts

version_added: "2.8"

short_description: Get Azure CDN profile facts

description:
    - Get facts for a specific Azure CDN profile or all CDN profiles.

options:
    name:
        description:
            - Limit results to a specific CDN profile.
    resource_group:
        description:
            - The resource group to search for the desired CDN profile
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.

extends_documentation_fragment:
    - azure

author:
    - "Hai Cao (@caohai) <t-haicao@microsoft.com>"
    - "Yunge Zhu (@yungezz) <yungez@microsoft.com>"
'''

EXAMPLES = '''
    - name: Get facts for one CDN profile
      azure_rm_cdnprofile_facts:
        name: Testing
        resource_group: myResourceGroup

    - name: Get facts for all CDN profiles
      azure_rm_cdnprofile_facts:

    - name: Get facts by tags
      azure_rm_cdnprofile_facts:
        tags:
          - Environment:Test
'''

RETURN = '''
cdnprofiles:
    description: List of CDN profiles.
    returned: always
    type: complex
    contains:
        resource_group:
            description:
                - Name of a resource group where the CDN profile exists.
            returned: always
            type: str
            sample: myResourceGroup
        name:
            description:
                - Name of the CDN profile.
            returned: always
            type: str
            sample: Testing
        location:
            description:
                - Location of the CDN profile.
            type: str
            sample: WestUS
        id:
            description:
                - ID of the CDN profile.
            type: str
            sample: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourcegroups/myResourceGroup/providers/Microsoft.Cdn/profiles/cdntest
        provisioning_state:
            description:
                - Provisioning status of the profile.
            type: str
            sample: Succeeded
        resource_state:
            description:
                - Resource status of the profile.
            type: str
            sample: Active
        sku:
            description:
                - The pricing tier, defines a CDN provider, feature list and rate of the CDN profile.
            type: str
            sample: standard_verizon
        type:
            description:
                - The type of the CDN profile.
            type: str
            sample: Microsoft.Cdn/profiles
        tags:
            description:
                - The tags of the CDN profile.
            type: list
            sample: [
                {"foo": "bar"}
            ]
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from azure.mgmt.cdn.models import ErrorResponseException
    from azure.common import AzureHttpError
    from azure.mgmt.cdn import CdnManagementClient
except Exception:
    # handled in azure_rm_common
    pass

import re

AZURE_OBJECT_CLASS = 'profiles'


class AzureRMCdnprofileFacts(AzureRMModuleBase):
    """Utility class to get Azure CDN profile facts"""

    def __init__(self):

        self.module_args = dict(
            name=dict(type='str'),
            resource_group=dict(type='str'),
            tags=dict(type='list')
        )

        self.results = dict(
            changed=False,
            cdnprofiles=[]
        )

        self.name = None
        self.resource_group = None
        self.tags = None
        self.cdn_client = None

        super(AzureRMCdnprofileFacts, self).__init__(
            derived_arg_spec=self.module_args,
            supports_tags=False,
            facts_module=True
        )

    def exec_module(self, **kwargs):

        for key in self.module_args:
            setattr(self, key, kwargs[key])

        self.cdn_client = self.get_cdn_client()

        if self.name and not self.resource_group:
            self.fail("Parameter error: resource group required when filtering by name.")

        if self.name:
            self.results['cdnprofiles'] = self.get_item()
        elif self.resource_group:
            self.results['cdnprofiles'] = self.list_resource_group()
        else:
            self.results['cdnprofiles'] = self.list_all()

        return self.results

    def get_item(self):
        """Get a single Azure CDN profile"""

        self.log('Get properties for {0}'.format(self.name))

        item = None
        result = []

        try:
            item = self.cdn_client.profiles.get(
                self.resource_group, self.name)
        except ErrorResponseException:
            pass

        if item and self.has_tags(item.tags, self.tags):
            result = [self.serialize_cdnprofile(item)]

        return result

    def list_resource_group(self):
        """Get all Azure CDN profiles within a resource group"""

        self.log('List all Azure CDNs within a resource group')

        try:
            response = self.cdn_client.profiles.list_by_resource_group(
                self.resource_group)
        except AzureHttpError as exc:
            self.fail('Failed to list all items - {0}'.format(str(exc)))

        results = []
        for item in response:
            if self.has_tags(item.tags, self.tags):
                results.append(self.serialize_cdnprofile(item))

        return results

    def list_all(self):
        """Get all Azure CDN profiles within a subscription"""
        self.log('List all CDN profiles within a subscription')
        try:
            response = self.cdn_client.profiles.list()
        except Exception as exc:
            self.fail("Error listing all items - {0}".format(str(exc)))

        results = []
        for item in response:
            if self.has_tags(item.tags, self.tags):
                results.append(self.serialize_cdnprofile(item))
        return results

    def serialize_cdnprofile(self, cdnprofile):
        '''
        Convert a CDN profile object to dict.
        :param cdn: CDN profile object
        :return: dict
        '''
        result = self.serialize_obj(cdnprofile, AZURE_OBJECT_CLASS)

        new_result = {}
        new_result['id'] = cdnprofile.id
        new_result['resource_group'] = re.sub('\\/.*', '', re.sub('.*resourcegroups\\/', '', result['id']))
        new_result['name'] = cdnprofile.name
        new_result['type'] = cdnprofile.type
        new_result['location'] = cdnprofile.location
        new_result['resource_state'] = cdnprofile.resource_state
        new_result['sku'] = cdnprofile.sku.name
        new_result['provisioning_state'] = cdnprofile.provisioning_state
        new_result['tags'] = cdnprofile.tags
        return new_result

    def get_cdn_client(self):
        if not self.cdn_client:
            self.cdn_client = self.get_mgmt_svc_client(CdnManagementClient,
                                                       base_url=self._cloud_environment.endpoints.resource_manager,
                                                       api_version='2017-04-02')
        return self.cdn_client


def main():
    """Main module execution code path"""

    AzureRMCdnprofileFacts()


if __name__ == '__main__':
    main()
