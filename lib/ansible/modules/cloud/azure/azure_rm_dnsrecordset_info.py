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
module: azure_rm_dnsrecordset_info

version_added: "2.9"

short_description: Get DNS Record Set facts

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
            - Limit the maximum number of record sets to return.
        type: int

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - Ozi Boms (@ozboms)

'''

EXAMPLES = '''
- name: Get facts for one Record Set
  azure_rm_dnsrecordset_info:
    resource_group: myResourceGroup
    zone_name: example.com
    relative_name: server10
    record_type: A
- name: Get facts for all Type A Record Sets in a Zone
  azure_rm_dnsrecordset_info:
    resource_group: myResourceGroup
    zone_name: example.com
    record_type: A
- name: Get all record sets in one zone
  azure_rm_dnsrecordset_info:
    resource_group: myResourceGroup
    zone_name: example.com
'''

RETURN = '''
azure_dnsrecordset:
    description:
        - List of record set dicts.
    returned: always
    type: list
    example: [
    {
        "etag": "60ac0480-44dd-4881-a2ed-680d20b3978e",
        "id": "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Network/dnszones/newzone.com/A/servera",
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
    }]
dnsrecordsets:
    description:
        - List of record set dicts, which shares the same hierarchy as M(azure_rm_dnsrecordset) module's parameter.
    returned: always
    type: list
    contains:
        id:
            description:
                - ID of the dns recordset.
            sample: "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Network/dnszones/newzone.
                     com/A/servera"
        relative_name:
            description:
                - Name of the dns recordset.
            sample: servera
        record_type:
            description:
                - The type of the record set.
                - Can be C(A), C(AAAA), C(CNAME), C(MX), C(NS), C(SRV), C(TXT), C(PTR).
            sample: A
        time_to_live:
            description:
                - Time to live of the record set in seconds.
            sample: 12900
        records:
            description:
                - List of records depending on the type of recordset.
            sample: [
                        {
                            "ipv4Address": "10.4.5.7"
                        },
                        {
                            "ipv4Address": "2.4.5.8"
                        }
                    ]
        provisioning_state:
            description:
                - Provision state of the resource.
            sample: Successed
        fqdn:
            description:
                - Fully qualified domain name of the record set.
            sample: www.newzone.com
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.common import AzureMissingResourceHttpError, AzureHttpError
except Exception:
    # This is handled in azure_rm_common
    pass

AZURE_OBJECT_CLASS = 'RecordSet'


RECORDSET_VALUE_MAP = dict(
    A='arecords',
    AAAA='aaaa_records',
    CNAME='cname_record',
    MX='mx_records',
    NS='ns_records',
    PTR='ptr_records',
    SRV='srv_records',
    TXT='txt_records',
    SOA='soa_record',
    CAA='caa_records'
    # FUTURE: add missing record types from https://github.com/Azure/azure-sdk-for-python/blob/master/azure-mgmt-dns/azure/mgmt/dns/models/record_set.py
)


class AzureRMRecordSetInfo(AzureRMModuleBase):

    def __init__(self):

        # define user inputs into argument
        self.module_arg_spec = dict(
            relative_name=dict(type='str'),
            resource_group=dict(type='str'),
            zone_name=dict(type='str'),
            record_type=dict(type='str'),
            top=dict(type='int')
        )

        # store the results of the module operation
        self.results = dict(
            changed=False,
        )

        self.relative_name = None
        self.resource_group = None
        self.zone_name = None
        self.record_type = None
        self.top = None

        super(AzureRMRecordSetInfo, self).__init__(self.module_arg_spec)

    def exec_module(self, **kwargs):

        is_old_facts = self.module._name == 'azure_rm_dnsrecordset_facts'
        if is_old_facts:
            self.module.deprecate("The 'azure_rm_dnsrecordset_facts' module has been renamed to 'azure_rm_dnsrecordset_info'", version='2.13')

        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        if not self.top or self.top <= 0:
            self.top = None

        # create conditionals to catch errors when calling record facts
        if self.relative_name and not self.resource_group:
            self.fail("Parameter error: resource group required when filtering by name or record type.")
        if self.relative_name and not self.zone_name:
            self.fail("Parameter error: DNS Zone required when filtering by name or record type.")

        results = []
        # list the conditions for what to return based on input
        if self.relative_name is not None:
            # if there is a name listed, they want only facts about that specific Record Set itself
            results = self.get_item()
        elif self.record_type:
            # else, they just want all the record sets of a specific type
            results = self.list_type()
        elif self.zone_name:
            # if there is a zone name listed, then they want all the record sets in a zone
            results = self.list_zone()

        if is_old_facts:
            self.results['ansible_facts'] = {
                'azure_dnsrecordset': self.serialize_list(results)
            }
        self.results['dnsrecordsets'] = self.curated_list(results)
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

        results = [item]
        return results

    def list_type(self):
        self.log('Lists the record sets of a specified type in a DNS zone')
        try:
            response = self.dns_client.record_sets.list_by_type(self.resource_group, self.zone_name, self.record_type, top=self.top)
        except AzureHttpError as exc:
            self.fail("Failed to list for record type {0} - {1}".format(self.record_type, str(exc)))

        results = []
        for item in response:
            results.append(item)
        return results

    def list_zone(self):
        self.log('Lists all record sets in a DNS zone')
        try:
            response = self.dns_client.record_sets.list_by_dns_zone(self.resource_group, self.zone_name, top=self.top)
        except AzureHttpError as exc:
            self.fail("Failed to list for zone {0} - {1}".format(self.zone_name, str(exc)))

        results = []
        for item in response:
            results.append(item)
        return results

    def serialize_list(self, raws):
        return [self.serialize_obj(item, AZURE_OBJECT_CLASS) for item in raws] if raws else []

    def curated_list(self, raws):
        return [self.record_to_dict(item) for item in raws] if raws else []

    def record_to_dict(self, record):
        record_type = record.type[len('Microsoft.Network/dnszones/'):]
        records = getattr(record, RECORDSET_VALUE_MAP.get(record_type))
        if not isinstance(records, list):
            records = [records]
        return dict(
            id=record.id,
            relative_name=record.name,
            record_type=record_type,
            records=[x.as_dict() for x in records],
            time_to_live=record.ttl,
            fqdn=record.fqdn,
            provisioning_state=record.provisioning_state
        )


def main():
    AzureRMRecordSetInfo()


if __name__ == '__main__':
    main()
