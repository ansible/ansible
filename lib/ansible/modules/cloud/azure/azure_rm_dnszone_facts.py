#!/usr/bin/python
#
# Copyright (c) 2017 Obezimnaka Boms, <t-ozboms@microsoft.com>
#
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: azure_rm_dnszone_facts

version_added: "2.4"

short_description: Get DNS zone facts.

description:
    - Get facts for a specific DNS zone or all DNS zones within a resource group.

options:
    resource_group:
        description:
            - Limit results by resource group. Required when filtering by name.
    name:
        description:
            - Only show results for a specific zone.
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Obezimnaka Boms @ozboms"

'''

EXAMPLES = '''
- name: Get facts for one zone
  azure_rm_dnszone_facts:
    resource_group: Testing
    name: foobar22

- name: Get facts for all zones in a resource group
  azure_rm_dnszone_facts:
    resource_group: Testing

- name: Get facts by tags
  azure_rm_dnszone_facts:
    tags:
      - testing
'''

RETURN = '''
azure_dnszones:
    description: List of zone dicts.
    returned: always
    type: list
    example:  [{
             "etag": "00000002-0000-0000-0dcb-df5776efd201",
                "location": "global",
                "properties": {
                    "maxNumberOfRecordSets": 5000,
                    "numberOfRecordSets": 15
                },
                "tags": {}
        }]
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.common import AzureMissingResourceHttpError, AzureHttpError
except:
    # This is handled in azure_rm_common
    pass

AZURE_OBJECT_CLASS = 'DnsZone'


class AzureRMDNSZoneFacts(AzureRMModuleBase):

    def __init__(self):

        # define user inputs into argument
        self.module_arg_spec = dict(
            name=dict(type='str'),
            resource_group=dict(type='str'),
            tags=dict(type='list')
        )

        # store the results of the module operation
        self.results = dict(
            changed=False,
            ansible_facts=dict(azure_dnszones=[])
        )

        self.name = None
        self.resource_group = None
        self.tags = None

        super(AzureRMDNSZoneFacts, self).__init__(self.module_arg_spec)

    def exec_module(self, **kwargs):

        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        if self.name and not self.resource_group:
            self.fail("Parameter error: resource group required when filtering by name.")

        # list the conditions and what to return based on user input

        if self.name is not None:
            # if there is a name, facts about that specific zone
            self.results['ansible_facts']['azure_dnszones'] = self.get_item()
        elif self.resource_group:
            # all the zones listed in that specific resource group
            self.results['ansible_facts']['azure_dnszones'] = self.list_resource_group()
        else:
            # all the zones in a subscription
            self.results['ansible_facts']['azure_dnszones'] = self.list_items()

        return self.results

    def get_item(self):
        self.log('Get properties for {0}'.format(self.name))
        item = None
        results = []
        # get specific zone
        try:
            item = self.dns_client.zones.get(self.resource_group, self.name)
        except CloudError:
            pass

        # serialize result
        if item and self.has_tags(item.tags, self.tags):
            results = [self.serialize_obj(item, AZURE_OBJECT_CLASS)]
        return results

    def list_resource_group(self):
        self.log('List items for resource group')
        try:
            response = self.dns_client.zones.list_by_resource_group(self.resource_group)
        except AzureHttpError as exc:
            self.fail("Failed to list for resource group {0} - {1}".format(self.resource_group, str(exc)))

        results = []
        for item in response:
            if self.has_tags(item.tags, self.tags):
                results.append(self.serialize_obj(item, AZURE_OBJECT_CLASS))
        return results

    def list_items(self):
        self.log('List all items')
        try:
            response = self.dns_client.zones.list()
        except AzureHttpError as exc:
            self.fail("Failed to list all items - {0}".format(str(exc)))

        results = []
        for item in response:
            if self.has_tags(item.tags, self.tags):
                results.append(self.serialize_obj(item, AZURE_OBJECT_CLASS))
        return results


def main():
    AzureRMDNSZoneFacts()

if __name__ == '__main__':
    main()
