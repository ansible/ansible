#!/usr/bin/python
#
# Copyright (c) 2017 Obezimnaka Boms, <t-ozboms@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: azure_rm_dnsrecordset_facts

version_added: "2.4"

short_description: Get DNS Record Set facts.

description:
    - Get facts for a specific DNS Record Set in a Zone, or a specific type in all Zones or in one Zone etc.

options:
    relative_name:
        description:
            - Only show results for a Record Set.
    resource_group:
        description:
            - Limit results by resource group. Required when filtering by name or type.
    zone_name:
        description:
            - Limit results by zones. Required when filtering by name or type.
    record_type:
        description:
            - Limit record sets by record type.
    top:
        description:
            - Limit the maximum number of record sets to return
        default: 100

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Ozi Boms @ozboms"

'''

EXAMPLES = '''
- name: Get facts for one Record Set
  azure_rm_dnsrecordset_facts:
    resource_group: Testing
    zone_name: example.com
    relative_name: server10
    record_type: A
- name: Get facts for all Type A Record Sets in a Zone
  azure_rm_dnsrecordset_facts:
    resource_group: Testing
    zone_name: example.com
    record_type: A
- name: Get all record sets in one zone
  azure_rm_dnsrecordset_facts:
    resource_group: Testing
    zone_name: example.com
'''

RETURN = '''
azure_dnsrecordset:
    description: List of record set dicts.
    returned: always
    type: list
    example: [
            {
                "etag": "60ac0480-44dd-4881-a2ed-680d20b3978e",
                "id": "/subscriptions/XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX/resourceGroups/testing/providers/Microsoft.Network/dnszones/newzone.com/A/servera",
                "name": "servera",
                "properties": {
                    "ARecords": [
                        {
                            "ipv4Address": "10.4.5.7"
                        },
                        {
                            "ipv4Address": "2.4.5.8"
                        }
                    ],
                    "TTL": 12900
                },
                "type": "Microsoft.Network/dnszones/A"
            }
        ]
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.common import AzureMissingResourceHttpError, AzureHttpError
except:
    # This is handled in azure_rm_common
    pass

AZURE_OBJECT_CLASS = 'RecordSet'


class AzureRMRecordSetFacts(AzureRMModuleBase):

    def __init__(self):

        # define user inputs into argument
        self.module_arg_spec = dict(
            relative_name=dict(type='str'),
            resource_group=dict(type='str'),
            zone_name=dict(type='str'),
            record_type=dict(type='str'),
            top=dict(type='str', default='100')
        )

        # store the results of the module operation
        self.results = dict(
            changed=False,
            ansible_facts=dict(azure_dnsrecordset=[])
        )

        self.relative_name = None
        self.resource_group = None
        self.zone_name = None
        self.record_type = None
        self.top = None

        super(AzureRMRecordSetFacts, self).__init__(self.module_arg_spec)

    def exec_module(self, **kwargs):

        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        # create conditionals to catch errors when calling record facts
        if self.relative_name and not self.resource_group:
            self.fail("Parameter error: resource group required when filtering by name or record type.")
        if self.relative_name and not self.zone_name:
            self.fail("Parameter error: DNS Zone required when filtering by name or record type.")

        # list the conditions for what to return based on input
        if self.relative_name is not None:
            # if there is a name listed, they want only facts about that specific Record Set itself
            self.results['ansible_facts']['azure_dnsrecordset'] = self.get_item()
        elif self.record_type:
            # else, they just want all the record sets of a specific type
            self.results['ansible_facts']['azure_dnsrecordset'] = self.list_type()
        elif self.zone_name:
            # if there is a zone name listed, then they want all the record sets in a zone
            self.results['ansible_facts']['azure_dnsrecordset'] = self.list_zone()
        return self.results

    def get_item(self):
        self.log('Get properties for {0}'.format(self.relative_name))
        item = None
        results = []

        # try to get information for specific Record Set
        try:
            item = self.dns_client.record_sets.get(self.resource_group, self.zone_name, self.relative_name, self.record_type)
        except CloudError:
            pass

        results = [self.serialize_obj(item, AZURE_OBJECT_CLASS)]
        return results

    def list_type(self):
        self.log('Lists the record sets of a specified type in a DNS zone')
        try:
            response = self.dns_client.record_sets.list_by_type(self.resource_group, self.zone_name, self.record_type, top=int(self.top))
        except AzureHttpError as exc:
            self.fail("Failed to list for record type {0} - {1}".format(self.record_type, str(exc)))

        results = []
        for item in response:
            results.append(self.serialize_obj(item, AZURE_OBJECT_CLASS))
        return results

    def list_zone(self):
        self.log('Lists all record sets in a DNS zone')
        try:
            response = self.dns_client.record_sets.list_by_dns_zone(self.resource_group, self.zone_name, top=int(self.top))
        except AzureHttpError as exc:
            self.fail("Failed to list for zone {0} - {1}".format(self.zone_name, str(exc)))

        results = []
        for item in response:
            results.append(self.serialize_obj(item, AZURE_OBJECT_CLASS))
        return results


def main():
    AzureRMRecordSetFacts()

if __name__ == '__main__':
    main()
