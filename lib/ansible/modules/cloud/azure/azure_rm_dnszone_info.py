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
module: azure_rm_dnszone_info

version_added: "2.9"

short_description: Get DNS zone facts

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
    - Obezimnaka Boms (@ozboms)

'''

EXAMPLES = '''
- name: Get facts for one zone
  azure_rm_dnszone_info:
    resource_group: myResourceGroup
    name: foobar22

- name: Get facts for all zones in a resource group
  azure_rm_dnszone_info:
    resource_group: myResourceGroup

- name: Get facts by tags
  azure_rm_dnszone_info:
    tags:
      - testing
'''

RETURN = '''
azure_dnszones:
    description:
        - List of zone dicts.
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
dnszones:
    description:
        - List of zone dicts, which share the same layout as azure_rm_dnszone module parameter.
    returned: always
    type: list
    contains:
        id:
            description:
                - id of the DNS Zone.
            sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Network/dnszones/azure.com"
        name:
            description:
                - name of the DNS zone.
            sample: azure.com
        type:
            description:
                - The type of this DNS zone (C(public) or C(private)).
            sample: private
        registration_virtual_networks:
            description:
                - A list of references to virtual networks that register hostnames in this DNS zone.
            type: list
            sample:  ["/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Network/virtualNetworks/bar"]
        resolution_virtual_networks:
            description:
                - A list of references to virtual networks that resolve records in this DNS zone.
            type: list
            sample:  ["/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Network/virtualNetworks/deadbeef"]
        number_of_record_sets:
            description:
                - The current number of record sets in this DNS zone.
            type: int
            sample: 2
        max_number_of_record_sets:
            description:
                - The maximum number of record sets that can be created in this DNS zone.
            type: int
            sample: 5000
        name_servers:
            description:
                - The name servers for this DNS zone.
            type: list
            sample:  [
                "ns1-03.azure-dns.com.",
                "ns2-03.azure-dns.net.",
                "ns3-03.azure-dns.org.",
                "ns4-03.azure-dns.info."
            ]
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase
from ansible.module_utils._text import to_native

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.common import AzureMissingResourceHttpError, AzureHttpError
except Exception:
    # This is handled in azure_rm_common
    pass

AZURE_OBJECT_CLASS = 'DnsZone'


class AzureRMDNSZoneInfo(AzureRMModuleBase):

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
            ansible_info=dict(azure_dnszones=[])
        )

        self.name = None
        self.resource_group = None
        self.tags = None

        super(AzureRMDNSZoneInfo, self).__init__(self.module_arg_spec)

    def exec_module(self, **kwargs):

        is_old_facts = self.module._name == 'azure_rm_dnszone_facts'
        if is_old_facts:
            self.module.deprecate("The 'azure_rm_dnszone_facts' module has been renamed to 'azure_rm_dnszone_info'", version='2.13')

        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        if self.name and not self.resource_group:
            self.fail("Parameter error: resource group required when filtering by name.")

        results = []
        # list the conditions and what to return based on user input
        if self.name is not None:
            # if there is a name, facts about that specific zone
            results = self.get_item()
        elif self.resource_group:
            # all the zones listed in that specific resource group
            results = self.list_resource_group()
        else:
            # all the zones in a subscription
            results = self.list_items()

        self.results['ansible_info']['azure_dnszones'] = self.serialize_items(results)
        self.results['dnszones'] = self.curated_items(results)

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
            results = [item]
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
                results.append(item)
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
                results.append(item)
        return results

    def serialize_items(self, raws):
        return [self.serialize_obj(item, AZURE_OBJECT_CLASS) for item in raws] if raws else []

    def curated_items(self, raws):
        return [self.zone_to_dict(item) for item in raws] if raws else []

    def zone_to_dict(self, zone):
        return dict(
            id=zone.id,
            name=zone.name,
            number_of_record_sets=zone.number_of_record_sets,
            max_number_of_record_sets=zone.max_number_of_record_sets,
            name_servers=zone.name_servers,
            tags=zone.tags,
            type=zone.zone_type.value.lower(),
            registration_virtual_networks=[to_native(x.id) for x in zone.registration_virtual_networks] if zone.registration_virtual_networks else None,
            resolution_virtual_networks=[to_native(x.id) for x in zone.resolution_virtual_networks] if zone.resolution_virtual_networks else None
        )


def main():
    AzureRMDNSZoneInfo()


if __name__ == '__main__':
    main()
