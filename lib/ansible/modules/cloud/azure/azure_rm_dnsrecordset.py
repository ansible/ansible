#!/usr/bin/python
#
# Copyright (c) 2017 Obezimnaka Boms, <t-ozboms@microsoft.com>
# Copyright (c) 2017 Ansible Project
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: azure_rm_dnsrecordset

version_added: "2.4"

short_description: Create, delete and update DNS record sets and records.

description:
    - Creates, deletes, and updates DNS records sets and records within an existing Azure DNS Zone.

options:
    resource_group:
        description:
            - name of resource group
        required: true
    zone_name:
        description:
            - name of the existing DNS zone in which to manage the record set
        required: true
    relative_name:
        description:
            - relative name of the record set
        required: true
    record_type:
        description:
            - the type of record set to create or delete
        choices:
            - A
            - AAAA
            - CNAME
            - MX
            - NS
            - SRV
            - TXT
            - PTR
        required: true
    record_mode:
        description:
            - whether existing record values not sent to the module should be purged
        default: purge
        choices:
            - append
            - purge
    state:
        description:
            - Assert the state of the record set. Use C(present) to create or update and
              C(absent) to delete.
        default: present
        choices:
            - absent
            - present
    time_to_live:
        description:
            - time to live of the record set in seconds
        default: 3600
    records:
        description:
            - list of records to be created depending on the type of record (set)
        suboptions:
            preference:
                description:
                    - used for creating an MX record set/records
            priority:
                description:
                   - used for creating an SRV record set/records
            weight:
                description:
                    - used for creating an SRV record set/records
            port:
                description:
                    - used for creating an SRV record set/records
            entry:
                description:
                    - primary data value for all record types.

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Obezimnaka Boms (@ozboms)"
    - "Matt Davis (@nitzmahone)"
'''

EXAMPLES = '''

- name: ensure an "A" record set with multiple records
  azure_rm_dnsrecordset:
    resource_group: Testing
    relative_name: www
    zone_name: testing.com
    record_type: A
    state: present
    records:
      - entry: 192.168.100.101
      - entry: 192.168.100.102
      - entry: 192.168.100.103

- name: delete a record set
  azure_rm_dnsrecordset:
    resource_group: Testing
    record_type: A
    relative_name: www
    zone_name: testing.com
    state: absent

- name: create multiple "A" record sets with multiple records
  azure_rm_dnsrecordset:
    resource_group: Testing
    zone_name: testing.com
    state: present
    relative_name: "{{ item.name }}"
    record_type: "{{ item.type }}"
    records: "{{ item.records }}"
  with_items:
    - { name: 'servera', type: 'A', records: [ { entry: '10.10.10.20' }, { entry: '10.10.10.21' }] }
    - { name: 'serverb', type: 'A', records: [ { entry: '10.10.10.30' }, { entry: '10.10.10.41' }] }
    - { name: 'serverc', type: 'A', records: [ { entry: '10.10.10.40' }, { entry: '10.10.10.41' }] }

- name: create SRV records in a new record set
  azure_rm_dnsrecordset:
    resource_group: Testing
    relative_name: _sip._tcp.testing.com
    zone_name: testing.com
    time_to_live: 7200
    record_type: SRV
    state: present
    records:
    - entry: sip.testing.com
      preference: 10
      priority: 20
      weight: 10
      port: 5060

- name: create PTR record in a new record set
  azure_rm_dnsrecordset:
    resource_group: Testing
    relative_name: 192.168.100.101.in-addr.arpa
    zone_name: testing.com
    record_type: PTR
    records:
    - entry: servera.testing.com

- name: create TXT record in a new record set
  azure_rm_dnsrecordset:
    resource_group: Testing
    relative_name: mail.testing.com
    zone_name: testing.com
    record_type: TXT
    records:
    - entry: 'v=spf1 a -all'

'''

RETURN = '''
'''

import inspect
import sys

from ansible.module_utils.basic import _load_params
from ansible.module_utils.six import iteritems
from ansible.module_utils.azure_rm_common import AzureRMModuleBase, HAS_AZURE

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.dns.models import Zone, RecordSet, ARecord, AaaaRecord, MxRecord, NsRecord, PtrRecord, SrvRecord, TxtRecord, CnameRecord, SoaRecord
except ImportError:
    # This is handled in azure_rm_common
    pass


RECORD_ARGSPECS = dict(
    A=dict(
        ipv4_address=dict(type='str', required=True, aliases=['entry'])
    ),
    AAAA=dict(
        ipv6_address=dict(type='str', required=True, aliases=['entry'])
    ),
    CNAME=dict(
        cname=dict(type='str', required=True, aliases=['entry'])
    ),
    MX=dict(
        preference=dict(type='int', required=True),
        exchange=dict(type='str', required=True, aliases=['entry'])
    ),
    NS=dict(
        nsdname=dict(type='str', required=True, aliases=['entry'])
    ),
    PTR=dict(
        ptrdname=dict(type='str', required=True, aliases=['entry'])
    ),
    SRV=dict(
        priority=dict(type='int', required=True),
        port=dict(type='int', required=True),
        weight=dict(type='int', required=True),
        target=dict(type='str', required=True, aliases=['entry'])
    ),
    TXT=dict(
        value=dict(type='list', required=True, aliases=['entry'])
    ),
    # FUTURE: ensure all record types are supported (see https://github.com/Azure/azure-sdk-for-python/tree/master/azure-mgmt-dns/azure/mgmt/dns/models)
)

RECORDSET_VALUE_MAP = dict(
    A=dict(attrname='arecords', classobj=ARecord, is_list=True),
    AAAA=dict(attrname='aaaa_records', classobj=AaaaRecord, is_list=True),
    CNAME=dict(attrname='cname_record', classobj=CnameRecord, is_list=False),
    MX=dict(attrname='mx_records', classobj=MxRecord, is_list=True),
    NS=dict(attrname='ns_records', classobj=NsRecord, is_list=True),
    PTR=dict(attrname='ptr_records', classobj=PtrRecord, is_list=True),
    SRV=dict(attrname='srv_records', classobj=SrvRecord, is_list=True),
    TXT=dict(attrname='txt_records', classobj=TxtRecord, is_list=True),
    # FUTURE: add missing record types from https://github.com/Azure/azure-sdk-for-python/blob/master/azure-mgmt-dns/azure/mgmt/dns/models/record_set.py
) if HAS_AZURE else {}


class AzureRMRecordSet(AzureRMModuleBase):

    def __init__(self):

        # we're doing two-pass arg validation, sample and store the args internally to allow this
        _load_params()

        self.module_arg_spec = dict(
            resource_group=dict(type='str', required=True),
            relative_name=dict(type='str', required=True),
            zone_name=dict(type='str', required=True),
            record_type=dict(choices=RECORD_ARGSPECS.keys(), required=True, type='str'),
            record_mode=dict(choices=['append', 'purge'], default='purge'),
            state=dict(choices=['present', 'absent'], default='present', type='str'),
            time_to_live=dict(type='int', default=3600),
            records=dict(type='list', elements='dict')
        )

        required_if = [
            ('state', 'present', ['records'])
        ]

        self.results = dict(
            changed=False
        )

        # first-pass arg validation so we can get the record type- skip exec_module
        super(AzureRMRecordSet, self).__init__(self.module_arg_spec, required_if=required_if, supports_check_mode=True, skip_exec=True)

        # look up the right subspec and metadata
        record_subspec = RECORD_ARGSPECS.get(self.module.params['record_type'])
        self.record_type_metadata = RECORDSET_VALUE_MAP.get(self.module.params['record_type'])

        # patch the right record shape onto the argspec
        self.module_arg_spec['records']['options'] = record_subspec

        # monkeypatch __hash__ on SDK model objects so we can safely use them in sets
        for rvm in RECORDSET_VALUE_MAP.values():
            rvm['classobj'].__hash__ = gethash

        # rerun validation and actually run the module this time
        super(AzureRMRecordSet, self).__init__(self.module_arg_spec, required_if=required_if, supports_check_mode=True)

    def exec_module(self, **kwargs):
        for key in self.module_arg_spec.keys():
            setattr(self, key, kwargs[key])

        # retrieve resource group to make sure it exists
        self.get_resource_group(self.resource_group)
        zone = self.dns_client.zones.get(self.resource_group, self.zone_name)
        if not zone:
            self.fail('The zone {0} does not exist in the resource group {1}'.format(self.zone_name, self.resource_group))

        try:
            self.log('Fetching Record Set {0}'.format(self.relative_name))
            record_set = self.dns_client.record_sets.get(self.resource_group, self.zone_name, self.relative_name, self.record_type)
        except CloudError as ce:
            record_set = None
            # FUTURE: fail on anything other than ResourceNotFound

        # FUTURE: implement diff mode

        if self.state == 'present':
            # convert the input records to SDK objects
            self.input_sdk_records = self.create_sdk_records(self.records)

            if not record_set:
                changed = True
            else:
                # and use it to get the type-specific records
                server_records = getattr(record_set, self.record_type_metadata['attrname'])

                # compare the input records to the server records
                changed = self.records_changed(self.input_sdk_records, server_records)

                # also check top-level recordset properties
                changed |= record_set.ttl != self.time_to_live

                # FUTURE: add metadata/tag check on recordset

            self.results['changed'] |= changed

        elif self.state == 'absent':
            if record_set:
                self.results['changed'] = True

        if self.check_mode:
            return self.results

        if self.results['changed']:
            if self.state == 'present':
                record_set_args = dict(
                    ttl=self.time_to_live
                )

                if not self.record_type_metadata['is_list']:
                    records_to_create_or_update = self.input_sdk_records[0]
                elif self.record_mode == 'append' and record_set:  # append mode, merge with existing values before update
                    records_to_create_or_update = set(self.input_sdk_records).union(set(server_records))
                else:
                    records_to_create_or_update = self.input_sdk_records

                record_set_args[self.record_type_metadata['attrname']] = records_to_create_or_update

                record_set = RecordSet(**record_set_args)

                rsout = self.dns_client.record_sets.create_or_update(self.resource_group, self.zone_name, self.relative_name, self.record_type, record_set)

            elif self.state == 'absent':
                # delete record set
                self.delete_record_set()

        return self.results

    def delete_record_set(self):
        try:
            # delete the record set
            self.dns_client.record_sets.delete(self.resource_group, self.zone_name, self.relative_name, self.record_type)
        except Exception as exc:
            self.fail("Error deleting record set {0} - {1}".format(self.relative_name, str(exc)))
        return None

    def create_sdk_records(self, input_records):
        record_sdk_class = self.record_type_metadata['classobj']
        record_argspec = inspect.getargspec(record_sdk_class.__init__)
        return [record_sdk_class(**dict([(k, v) for k, v in iteritems(x) if k in record_argspec.args])) for x in input_records]

    def records_changed(self, input_records, server_records):
        # ensure we're always comparing a list, even for the single-valued types
        if not isinstance(server_records, list):
            server_records = [server_records]

        input_set = set(input_records)
        server_set = set(server_records)

        if self.record_mode == 'append':  # only a difference if the server set is missing something from the input set
            return len(input_set.difference(server_set)) > 0

        # non-append mode; any difference in the sets is a change
        return input_set != server_set


# Quick 'n dirty hash impl suitable for monkeypatching onto SDK model objects (so we can use set comparisons)
def gethash(self):
    if not getattr(self, '_cachedhash', None):
        spec = inspect.getargspec(self.__init__)
        valuetuple = tuple(
            map(lambda v: v if not isinstance(v, list) else str(v), [
                getattr(self, x, None) for x in spec.args if x != 'self'
            ])
        )
        self._cachedhash = hash(valuetuple)
    return self._cachedhash


def main():
    AzureRMRecordSet()

if __name__ == '__main__':
    main()
