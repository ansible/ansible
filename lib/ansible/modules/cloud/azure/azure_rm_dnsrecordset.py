#!/usr/bin/python
#
# Copyright (c) 2017 Obezimnaka Boms, <t-ozboms@microsoft.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: azure_rm_dnsrecordset

version_added: "2.4"

short_description: Create, delete and update record sets and records.

description:
    - Creates, deletes, and updates records sets and their records.

options:
    resource_group:
        description:
            - name of resource group.
        required: true
    relative_name:
        description:
            - relative name of the record set.
        required: true
    zone_name:
        description:
            - name of the zone in which to create or delete the record set
        required: true
    record_type:
        description:
            - the type of record set or record to create or delete
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
    record_set_state:
        description:
            - Assert the state of the record set. Use 'present' to create or update and
              'absent' to delete.
        default: present
        choices:
            - absent
            - present
    record_state:
        description:
            - Assert the state of the records. Use 'present' to create or update. Update will append the new records.
              Use 'absent' to delete a specific record or set of records.
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
            - specific records to be created or deleted depending on the type of record (set)
        aliases:
            - ipv4_address
            - ipv6_address
            - cname
            - exchange
            - nsdname
            - ptrdname
            - value
            - target
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

extends_documentation_fragment:
    - azure

author: "Obezimnaka Boms (@ozboms)"
'''

EXAMPLES = '''

- name: create new "A" record set with multiple records
  azure_rm_dnsrecordset:
    resource_group: Testing
    relative_name: www
    zone_name: testing.com
    record_type: A
    record_set_state: present
    record_state: present
    records:
      - 192.168.100.101
      - 192.168.100.102
      - 192.168.100.103

- name: delete a record set
  azure_rm_dnsrecordset:
    resource_group: Testing
    record_type: A
    relative_name: www
    zone_name: testing.com
    record_set_state: absent

- name: create multiple "A" record sets with multiple records
  azure_rm_dnsrecordset:
    resource_group: Testing
    zone_name: testing.com
    record_set_state: present
    record_state: present
    relative_name: "{{ item.name }}"
    record_type: "{{ item.type }}"
    records: "{{ item.records }}"
  with_items:
    - { name: 'servera', type: 'A', records: ['10.10.10.20', '10.10.10.21'] }
    - { name: 'serverb', type: 'A', records: ['10.10.10.30', '10.10.10.31'] }
    - { name: 'serverc', type: 'A', records: ['10.10.10.40', '10.10.10.41'] }

- name: create SRV records in a new record set
  azure_rm_dnsrecordset:
    resource_group: 'Testing'
    relative_name: '_sip._tcp.testing.com'
    zone_name: 'testing.com'
    record_type: 'SRV'
    record_set_state: 'present'
    records: 'sip.testing.com'
    preference: 10
    record_state: 'present'
    time_to_live: 7200
    priority: 20
    weight: 10
    port: 5060

- name: create PTR record in a new record set
  azure_rm_dnsrecordset:
    resource_group: 'Testing'
    relative_name: '192.168.100.101.in-addr.arpa'
    zone_name: 'testing.com'
    record_type: 'PTR'
    record_set_state: 'present'
    records: 'servera.testing.com'
    record_state: 'present'

- name: create TXT record in a new record set
  azure_rm_dnsrecordset:
    resource_group: 'Testing'
    relative_name: 'mail.testing.com'
    zone_name: 'testing.com'
    record_type: 'TXT'
    record_set_state: 'present'
    records: 'v=spf1 a -all'
    record_state: 'present'

'''

RETURN = '''
state:
    description: Current state of the record set.
    returned: always
    type: dict
    sample: {
        "aaaa_records": [],
        "arecords": [
            {
                "ipv4_address": "1.2.3.4"
            },
            {
                "ipv4_address": "2.4.5.6"
            },
            {
                "ipv4_address": "7.8.3.9"
            },
            {
                "ipv4_address": "10.3.2.8"
            }
        ],
        "cname_record": null,
        "full_list": [
            "1.2.3.4",
            "2.4.5.6",
            "7.8.3.9",
            "10.3.2.8"
        ],
        "id": "/subscriptions/XXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXX/resourceGroups/Testing/providers/Microsoft.Network/dnszones/recordzone.com/A/server_a",
        "mx_records": [],
        "name": "server_a",
        "ns_records": [],
        "port_list": [],
        "pref_list": [],
        "prior_list": [],
        "ptr_records": [],
        "srv_records": [],
        "ttl": 12900,
        "txt_records": [],
        "type": "Microsoft.Network/dnszones/A",
        "weight_list": []
    }
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.dns.models import Zone, RecordSet, ARecord, AaaaRecord, MxRecord, NsRecord, PtrRecord, SrvRecord, TxtRecord, CnameRecord, SoaRecord
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMRecordSet(AzureRMModuleBase):

    def __init__(self):

        # define user inputs into argument
        self.module_arg_spec = dict(
            resource_group=dict(type='str', required=True),
            relative_name=dict(type='str', required=True),
            zone_name=dict(type='str', required=True),
            record_type=dict(choices=['A', 'AAAA', 'CNAME', 'MX', 'NS', 'SRV', 'TXT', 'PTR'], required=True, type='str'),
            record_set_state=dict(choices=['present', 'absent'], default='present', type='str'),
            record_state=dict(choices=['present', 'absent'], default='absent', type='str'),
            time_to_live=dict(type='str', default='3600'),
            records=dict(type='list', aliases=['ipv4_address', 'ipv6_address', 'cname', 'exchange', 'nsdname', 'ptrdname', 'value', 'target']),
            preference=dict(type='list'),
            priority=dict(type='list'),
            weight=dict(type='list'),
            port=dict(type='list')
        )

        # store the results of the module operation
        self.results = dict(
            changed=False,
            record_set_state=dict()
        )

        self.resource_group = None
        self.relative_name = None
        self.zone_name = None
        self.record_type = None
        self.record_set_state = None
        self.record_state = None
        self.time_to_live = None
        self.records = None
        self.preference = None
        self.priority = None
        self.weight = None
        self.port = None
        # self.tags = None

        super(AzureRMRecordSet, self).__init__(self.module_arg_spec,
                                               supports_check_mode=True)

    def exec_module(self, **kwargs):

        # create a new variable in case the 'try' doesn't find a record set
        curr_record = None
        record_set = None
        for key in self.module_arg_spec.keys():
            setattr(self, key, kwargs[key])

        self.results['check_mode'] = self.check_mode

        # get resource group and zone
        resource_group = self.get_resource_group(self.resource_group)
        zone = self.dns_client.zones.get(self.resource_group, self.zone_name)
        if not zone:
            self.fail('The zone {0} does not exist in the resource group {1}'.format(self.zone_name, self.resource_group))

        changed = False
        results = dict()
        try:
            self.log('Fetching Record Set {0}'.format(self.relative_name))
            record_set = self.dns_client.record_sets.get(self.resource_group, self.zone_name, self.relative_name, self.record_type)

            # set object into a dictionary
            results = record_set_to_dict(record_set)
            # to create a new record set, self.state == present
            if self.record_set_state == 'present':
                if self.record_state == 'present':
                    for each in self.records:
                        # loop through the current records you want to add
                        # if at least one is not in the record set you got, then we want changed = True
                        if each not in results['full_list']:
                            changed = True
                            break

                elif self.record_state == 'absent':
                    # if the state == absent, then we want to delete the records which are given to us if they are in there
                    for each_rec in self.records:
                        # loop through current records
                        # if at least one is in there, we make changed = True
                        if each_rec in results['full_list']:
                            changed = True
                            break

                # update_tags, results['tags'] = self.update_tags(results['tags'])
                # if update_tags:
                #    changed = True

            elif self.record_set_state == 'absent':
                changed = True

        except CloudError:
            # the record set does not exist
            if self.record_set_state == 'present':
                changed = True
                if self.record_set_state == 'absent':
                    self.fail("You cannot delete records {0} to the record set {1} you are creating ".format(self.records, self.relative_name))
            else:
                # you can't delete what is not there
                changed = False

        self.results['changed'] = changed
        self.results['record_set_state'] = results

        # return the results if your only gathering information and not changing anything
        if self.check_mode:
            return self.results
        if changed:
            # either create a new record set, or update the one we have
            if self.record_set_state == 'present':
                if not record_set:
                    self.log('Creating record set {0} of type {1}'.format(self.relative_name, self.record_type))

                    # function creates a record_set based on the record type
                    curr_record = create_current_record(self)
                    record_set = turn_to_input(self, curr_record)
                else:
                    # update record set
                    if self.record_state == 'present':
                        # create new lists from the results of the given record set we got from azure
                        mergedlist = results['full_list']
                        preference_lst = results['pref_list']
                        priority_lst = results['prior_list']
                        weight_lst = results['weight_list']
                        port_lst = results['port_list']
                        # loop through records to add if they are not already in the list we pulled down, then add them in and their components
                        for i in range(len(self.records)):
                            if self.records[i] not in mergedlist:
                                mergedlist.append(self.records[i])
                                if self.record_type == 'MX':
                                    preference_lst.append(self.preference[i])
                                elif self.record_type == 'SRV':
                                    priority_lst.append(self.priority[i])
                                    weight_lst.append(self.weight[i])
                                    port_lst.append(self.port[i])
                        # set self dicitionaries to updated lists and use those to create a new record set list to be passed into the turn_to_input function
                        self.preference = preference_lst
                        self.records = mergedlist
                        self.priority = priority_lst
                        self.weight = weight_lst
                        self.port = port_lst
                        # self.tags = results['tags']
                        curr_record = create_current_record(self)
                        record_set = turn_to_input(self, curr_record)
                    elif self.record_state == 'absent':
                        # we loop through the contents of the results and if one of them matches a record in curr_record, remove it from results
                        mergedlist = []
                        preference_lst = []
                        priority_lst = []
                        weight_lst = []
                        port_lst = []
                        # loop through records and if they are not in the input by the user, then we can add them to the final list to be used
                        for i in range(len(results['full_list'])):
                            if results['full_list'][i] not in self.records:
                                mergedlist.append(results['full_list'][i])
                                if self.record_type == 'MX':
                                    preference_lst.append(results['pref_list'][i])
                                elif self.record_type == 'SRV':
                                    priority_lst.append(results['prior_list'][i])
                                    weight_lst.append(results['weight_list'][i])
                                    port_lst.append(results['port_list'][i])
                        self.preference = preference_lst
                        self.records = mergedlist
                        self.priority = priority_lst
                        self.weight = weight_lst
                        self.port = port_lst
                        curr_record = create_current_record(self)
                        record_set = turn_to_input(self, curr_record)

                self.results['record_set_state'] = self.create_or_update_record_set(record_set)
            elif self.record_set_state == 'absent':
                # delete record set
                self.delete_record_set()
                # the delete does not actually return anything. if no exception, then we'll assume
                # it worked.
                self.results['record_set_state']['status'] = 'Deleted'
        return self.results

    def create_or_update_record_set(self, record_set):
        try:
            # create or update the new record set object we created
            new_record_set = self.dns_client.record_sets.create_or_update(self.resource_group, self.zone_name, self.relative_name, self.record_type, record_set)
        except Exception as exc:
            self.fail("Error creating or updating record set {0} - {1}".format(self.relative_name, str(exc)))
        return record_set_to_dict(new_record_set)

    def delete_record_set(self):
        try:
            # delete the record set
            self.dns_client.record_sets.delete(self.resource_group, self.zone_name, self.relative_name, self.record_type)
        except Exception as exc:
            self.fail("Error deleting record set {0} - {1}".format(self.relative_name, str(exc)))
        return None


def record_set_to_dict(RecordSet):
    # turn RecordSet object into a dictionary to be used later
    # create a new list variable to use any record type as a parameter (full_list)
    result = dict(
        id=RecordSet.id,
        name=RecordSet.name,
        type=RecordSet.type,
        ttl=RecordSet.ttl,
        metadata=RecordSet.metadata,
        full_list=[],
        pref_list=[],
        prior_list=[],
        weight_list=[],
        port_list=[],
        arecords=[],
        aaaa_records=[],
        ptr_records=[],
        mx_records=[],
        ns_records=[],
        txt_records=[],
        srv_records=[],
        cname_record=None
    )
    if RecordSet.arecords:
        for _ in RecordSet.arecords:
            result['arecords'].append(dict(
                ipv4_address=_.ipv4_address))
            result['full_list'].append(_.ipv4_address)

    elif RecordSet.aaaa_records:
        for _ in RecordSet.aaaa_records:
            result['aaaa_records'].append(dict(
                ipv6_address=_.ipv6_address))
            result['full_list'].append(_.ipv6_address)

    elif RecordSet.ptr_records:
        for _ in RecordSet.ptr_records:
            result['ptr_records'].append(dict(
                ptrdname=_.ptrdname))
            result['full_list'].append(_.ptrdname)

    elif RecordSet.mx_records:
        for _ in RecordSet.mx_records:
            result['mx_records'].append(dict(
                preference=_.preference,
                exchange=_.exchange
            ))
            result['pref_list'].append(_.preference)
            result['full_list'].append(_.exchange)

    elif RecordSet.ns_records:
        for _ in RecordSet.ns_records:
            result['ns_records'].append(dict(
                nsdname=_.nsdname))
            result['full_list'].append(_.nsdname)

    elif RecordSet.txt_records:
        for _ in RecordSet.txt_records:
            result['txt_records'].append(dict(
                value=_.value))
            result['full_list'].append(_.value)

    elif RecordSet.srv_records:
        for _ in RecordSet.srv_records:
            result['srv_records'].append(dict(
                priority=_.priority,
                weight=_.weight,
                port=_.port,
                target=_.target
            ))
            result['full_list'].append(_.target)
            result['prior_list'].append(_.priority)
            result['weight_list'].append(_.weight)
            result['port_list'].append(_.port)

    elif RecordSet.cname_record:
        result['cname_record'] = dict(
            cname=RecordSet.cname_record.cname)
        result['full_list'].append(RecordSet.cname_record.cname)

    return result


def create_current_record(self):
    # takes in a list of str records, the record type and returns a list of the specific record type
    retrn_lst = []

    if self.record_type == 'A':
        if len(self.records) == 0:
            return retrn_lst
        for each_record in self.records:
            # we want to append to the final list the object type ARecord where the parameter is a str called each_record representing the user input
            retrn_lst.append(ARecord(ipv4_address=each_record))
        return retrn_lst

    elif self.record_type == 'AAAA':
        if len(self.records) == 0:
            return retrn_lst
        for each_record_1 in self.records:
            retrn_lst.append(AaaaRecord(ipv6_address=each_record_1))
        return retrn_lst

    elif self.record_type == 'MX':
        if len(self.records) == 0:
            return retrn_lst
        if len(self.records) != len(self.preference):
            self.fail('You must have an exchange for each preference or vice versa')
        # if type matches to 'MX', loop through records/exchange and preference, using the same indices to create the object
        for i in range(len(self.records)):
            retrn_lst.append(MxRecord(preference=int(self.preference[i]), exchange=self.records[i]))
        return retrn_lst

    elif self.record_type == 'NS':
        if len(self.records) == 0:
            return retrn_lst
        for each_record_2 in self.records:
            retrn_lst.append(NsRecord(nsdname=each_record_2))
        return retrn_lst

    elif self.record_type == 'TXT':
        if len(self.records) == 0:
            return retrn_lst
        for each_record_3 in self.records:
            retrn_lst.append(TxtRecord(value=each_record_3))
        return retrn_lst

    elif self.record_type == 'PTR':
        if len(self.records) == 0:
            return retrn_lst
        for each_record_4 in self.records:
            retrn_lst.append(PtrRecord(ptrdname=each_record_4))
        return retrn_lst

    elif self.record_type == 'SRV':
        if len(self.records) == 0:
            return retrn_lst
        count = len(self.records)
        if count != len(self.priority) or count != len(self.port) or count != len(self.weight):
            self.fail('You must have a weight, a port and a priority for each target')
        for i in range(len(self.records)):
            retrn_lst.append(SrvRecord(priority=int(self.priority[i]), weight=int(self.weight[i]), port=int(self.port[i]), target=self.records[i]))
        return retrn_lst

    elif self.record_type == 'CNAME':
        if len(self.records) > 1:
            self.fail('You cannot have more than one record in a single CNAME record set')
        elif len(self.records) == 0:
            return retrn_lst
        curr = CnameRecord(cname=self.records[0])
        return curr
    return retrn_lst


def turn_to_input(self, curr_record):
    val = turn_to_long(self.time_to_live)

    if self.record_type == 'A':
        x = RecordSet(arecords=curr_record, type=self.record_type, ttl=val)
    elif self.record_type == 'AAAA':
        x = RecordSet(aaaa_records=curr_record, type=self.record_type, ttl=val)
    elif self.record_type == 'CNAME':
        x = RecordSet(cname_record=curr_record, type=self.record_type, ttl=val)
    elif self.record_type == 'MX':
        x = RecordSet(mx_records=curr_record, type=self.record_type, ttl=val)
    elif self.record_type == 'NS':
        x = RecordSet(ns_records=curr_record, type=self.record_type, ttl=val)
    elif self.record_type == 'SRV':
        x = RecordSet(srv_records=curr_record, type=self.record_type, ttl=val)
    elif self.record_type == 'TXT':
        x = RecordSet(txt_records=curr_record, type=self.record_type, ttl=val)
    elif self.record_type == 'PTR':
        x = RecordSet(ptr_records=curr_record, type=self.record_type, ttl=val)
    return x


def turn_to_long(value):
    try:
        output = long(value)
    except NameError:
        output = int(value)
    return output


def main():
    AzureRMRecordSet()

if __name__ == '__main__':
    main()
