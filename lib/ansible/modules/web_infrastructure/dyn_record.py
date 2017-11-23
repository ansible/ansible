#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Olivier Boukili boukili.olivier <> gmail.com>, olivier <> malt.com
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: dyn_record
author: Olivier Boukili (@oboukili)"
version_added: "2.5"
short_description: Manage DNS records on Dyn's managed DNS (a DNS service).
description:
  - Manage DNS records on Dyn's managed DNS (a DNS service) using Dyn API
    on a single DNS zone. The Dyn user must be granted the following permissions
    on all impacted zones ZoneChangeSet, ZonePublish, ZoneAddNode, ZoneRemoveNode,
    ZoneGet, RecordAdd, RecordUpdate, RecordDelete, RecordGet, RecordBulkAdd,
    RecordBulkUpdate, RecordDiscard.
    This module supports ansible check_mode.
options:
  dyn_customer_name:
    default: None
    description:
      - Dyn customer name required for API authentication. Can also be passed on
        as the DYN_CUSTOMER_NAME environment variable.
    required: false
  dyn_user_name:
    default: None
    description:
      - Dyn username required for API authentication. Can also be passed on
        as the DYN_USER_NAME environment variable.
    required: false
  dyn_password:
    default: None
    description:
      - Dyn password required for API authentication. Can also be passed on
        as the DYN_PASSWORD environment variable.
    required: false
  zone:
    default: None
    description:
      - Dyn DNS zone to act upon.
    required: true
  records:
    default: None
    description:
      - JSON/YAML list of the node(s) name(s) to act upon (examples below).
        Note that duplicates node records are not supported (for example TXT records
        with different rdata, but sharing the same fqdn)!
        Note that the "record_type" attribute is mandatory.
        Note that every "record_type" Record attribute is supported.
        except the ALIAS Record type that for some reason use a different API path.
        Note that the "rdata" container format must conform to the specification of its record_type.
        Note that the "ttl" key can be omitted as it has a default of 0 (the zone default TTL).
    required: True
  state:
    default: present
    description:
      - Whether the record(s) must be present or absent.
        When 'present', if the record(s) already exist(s), it(they) will be updated.
        Note that this parameter is ignored when the 'node' parameter is not specified
        (in case of a simple zone publish).
    required: false
    choices: ["present", "absent"]
  notes:
    default: "Published by Ansible"
    description:
      - Zone publish notes when the 'publish' attribute is set to True.
    required: false
  validate_certs:
    default: true
    description:
      - Whether to valide TLS certificates during the module execution.
    required: false
'''

EXAMPLES = '''
# Create and publish a single A record.
- dyn_record:
    dyn_customer_name: customer
    dyn_user_name: user
    dyn_password: password
    zone: myzone.com
    records:
      - record_type: A
        node: www
        rdata:
          address: 1.2.3.4

# Create and publish multiple records of different types, passing on credentials from the environment:
- dyn_record:
    zone: myzone.com
    records:
      - record_type: A
        node: www
        rdata:
          address: 1.2.3.4
        ttl: 30
      - record_type: TXT
        node: _acme-challenge
        rdata:
          txtdata: someauthtoken
      - record_type: CNAME
        node: sub
        rdata:
          cname: www.anotherzone.com
    notes: Added a new node and cname redirects on {{ ansible_date_time.iso8601_micro }}
  environment:
    DYN_CUSTOMER_NAME: customer
    DYN_USER_NAME: user
    DYN_PASSWORD: password

# Delete a single CNAME record (first found).
- dyn_record:
    dyn_customer_name: customer
    dyn_user_name: user
    dyn_password: password
    zone: myzone.com
    records:
      - record_type: CNAME
        node: old
    state: absent

# Delete a single CNAME record (matching rdata).
- dyn_record:
    dyn_customer_name: customer
    dyn_user_name: user
    dyn_password: password
    zone: myzone.com
    records:
      - record_type: CNAME
        node: old
        rdata:
          cname: www.somedomain.org
    state: absent
'''

RETURN = '''
deleted:
    description: Nested boolean indicating whether the record(s) has/have been deleted (only when state is "absent").
    type: boolean
    returned: success
    sample: >
      {
        "myrecord": {
            "deleted": true
        },
        "anotherrecord": {
            "deleted":false
        }
      }
record_before/after:
    description: Nested dictionary of the record(s) before updating/creating it/them (only when state is "present").
    type: dict
    returned: success
    sample: >
      {
        "myrecord": {
           "changed": true,
            "record_before": {
                "fqdn": "myrecord.myzone.com",
                "zone": "myzone.com",
                "ttl": "30",
                "record_type": "A",
                "rdata": {
                    "address":"1.2.3.4"
                }
            },
            "record_after": {
                "fqdn": "myrecord.myzone.com",
                "zone": "myzone.com",
                "ttl": "15",
                "record_type": "A",
                "rdata": {
                    "address": "4.3.2.1"
                }
            }
        },
        "myunchangedtxtrecord":
            "changed": false,
            "record_before": {
                "fqdn": "myunchangedtxtrecord.myzone.com",
                "zone": "myzone.com",
                "ttl": "30",
                "record_type": "TXT",
                "rdata": {
                    "txtdata": "sometxtdata"
                }
            },
            "record_after": {
                "fqdn": "myunchangedtxtrecord.myzone.com",
                "zone": "myzone.com",
                "ttl": "30",
                "record_type": "TXT",
                "rdata": {
                    "txtdata": "sometxtdata"
                }
            }
        }
published:
    description: Boolean that indicates whether the zone has been published.
    type: bool
    returned: success
'''

import os
import json
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url


class DynectAPI(object):
    '''DynDNS API endpoint. Reads the following environment variables
    if they are not present within the module parameters:
        - DYN_CUSTOMER_NAME
        - DYN_USER_NAME
        - DYN_PASSWORD
    attributes:
        module -> ansible module instance (AnsibleModule object).
    '''

    def __init__(self, module):
        if module.params['dyn_customer_name'] is None:
            if 'DYN_CUSTOMER_NAME' not in os.environ:
                module.fail_json(msg="DYN_CUSTOMER_NAME should be present in environment!")
            else:
                self.dyn_customer_name = str(os.environ['DYN_CUSTOMER_NAME'])
        else:
            self.dyn_customer_name = module.params['dyn_customer_name']
        if module.params['dyn_user_name'] is None:
            if 'DYN_USER_NAME' not in os.environ:
                module.fail_json(msg="DYN_USER_NAME should be present in environment!")
            else:
                self.dyn_user_name = str(os.environ['DYN_USER_NAME'])
        else:
            self.dyn_user_name = module.params['dyn_user_name']
        if module.params['dyn_password'] is None:
            if 'DYN_PASSWORD' not in os.environ:
                module.fail_json(msg="DYN_PASSWORD should be present in environment!")
            else:
                self.dyn_password = str(os.environ['DYN_PASSWORD'])
        else:
            self.dyn_password = module.params['dyn_password']
        self.module = module
        self.api_uri = 'https://api.dynect.net'
        self.auth_token = self.getauthenticationtoken()

    def getauthenticationtoken(self):
        '''authenticate to Dynect API'''
        auth_payload = {
            'customer_name': self.dyn_customer_name,
            'user_name': self.dyn_user_name,
            'password': self.dyn_password
        }
        try:
            response, info = fetch_url(self.module, self.api_uri + "/REST/Session/",
                                       method="post",
                                       data=self.module.jsonify(auth_payload),
                                       headers={'Content-Type': 'application/json'})
        except Exception as exception:
            self.module.fail_json(msg=str(exception))
        else:
            status_code = info['status']
            if status_code >= 400:
                self.module.fail_json(msg=str(info['body']))
            else:
                body = response.read()
                return json.loads(body)['data']['token']

    def logout(self):
        '''logout from Dynect API'''
        try:
            operation = fetch_url(self.module, self.api_uri + "/REST/Session/", method="delete")
        except Exception as exception:
            self.module.fail_json(msg=str(exception))
        else:
            return operation[0]


class DynDnsZone(object):
    '''DynDNS zone control.
    attributes:
        module -> ansible module instance (AnsibleModule object).
    '''

    def __init__(self, module):
        self.module = module
        self.zone = module.params['zone']
        self.session = DynectAPI(module)

    def recordget(self, node, record_type, **kwargs):
        '''Gets a record, or a list of records matching the node, from the zone'''
        if 'record_id' not in kwargs:
            try:
                response, info = fetch_url(self.module, self.session.api_uri + "/REST/" +
                                           str(record_type).upper() + "Record/" +
                                           str(self.zone) + "/" + str(node) + "." + str(self.zone) + "/",
                                           method="get",
                                           headers={'Content-Type': 'application/json', 'Auth-Token': self.session.auth_token})
            except Exception as exception:
                self.module.fail_json(msg=str(exception))
            else:
                status_code = info['status']
                if status_code >= 400 and status_code != 404:
                    self.module.fail_json(msg=str(info['body']))
                elif not status_code == 404:
                    body = response.read()
                    records = json.loads(body)['data']
                else:
                    records = []

                for record_path in records:
                    singlerecord = self.recordgetfromid(record_path)
                    if 'rdata' in kwargs and singlerecord['rdata'] == kwargs['rdata']:
                        return singlerecord
                    elif 'rdata' not in kwargs:
                        return singlerecord

            return None
        else:
            self.recordgetfromid(record_path)

    def recordgetfromid(self, record_id):
        '''Get a record details from its record id path'''
        try:
            response, info = fetch_url(self.module, self.session.api_uri +
                                       str(record_id),
                                       method="get",
                                       headers={'Content-Type': 'application/json', 'Auth-Token': self.session.auth_token})
        except Exception as exception:
            self.module.fail_json(msg=str(exception))
        else:
            if response is not None:
                status_code = info['status']
                if status_code >= 400:
                    self.module.fail_json(msg=str(info['body']))
                body = response.read()
                return json.loads(body)['data']
            return None

    def recordadd(self, record_type, node, rdata, ttl="0"):
        '''Adds/Updates a record within the zone'''
        if rdata is None:
            self.module.fail_json(msg="rdata should not be empty!")

        # Check whether the record exists to either update or create it.
        foundrecord = self.recordget(node, record_type)
        payload = {'rdata': rdata, 'ttl': str(ttl)}
        # Filtered keys for Ansible module idempotence
        filteredkeys = ['record_id']

        if foundrecord is None:
            try:
                response, info = fetch_url(self.module, self.session.api_uri + "/REST/" +
                                           str(record_type).upper() + "Record/" +
                                           str(self.zone) + "/" + str(node) + "." +
                                           str(self.zone) + "/",
                                           method="post",
                                           data=self.module.jsonify(payload),
                                           headers={'Content-Type': 'application/json', 'Auth-Token': self.session.auth_token})
            except Exception as exception:
                self.module.fail_json(msg=str(exception))
            else:
                if info["status"] >= 400:
                    self.module.fail_json(msg=str(info))
                else:
                    body = response.read()
                    record_after = json.loads(body)['data']
                    for unwantedkey in filteredkeys:
                        del record_after[unwantedkey]
                    return {'record_before': {}, 'record_after': record_after}

        else:
            if foundrecord['rdata'] != rdata or (foundrecord['ttl'] != ttl and ttl != 0):
                try:
                    response, info = fetch_url(self.module, self.session.api_uri + "/REST/" +
                                               str(record_type).upper() + "Record/" +
                                               str(self.zone) + "/" + str(node) + "." +
                                               str(self.zone) + "/" +
                                               str(foundrecord['record_id']),
                                               method="put",
                                               data=self.module.jsonify(payload),
                                               headers={'Content-Type': 'application/json', 'Auth-Token': self.session.auth_token})
                except Exception as exception:
                    self.module.fail_json(msg=str(exception))
                else:
                    if info["status"] >= 400:
                        self.module.fail_json(msg=str(info))
                    else:
                        body = response.read()
                        record_after = json.loads(body)['data']
                        record_before = foundrecord
                        for unwantedkey in filteredkeys:
                            del record_after[unwantedkey]
                            del record_before[unwantedkey]
                    return {'record_before': record_before, 'record_after': record_after}
            else:
                return {'record_before': foundrecord, 'record_after': foundrecord}

    def recorddelete(self, node, record_type, rdata=None):
        '''Deletes a record within the zone'''
        # Check whether the record exists to delete it afterwards.
        foundrecord = self.recordget(node, record_type, rdata=rdata)

        if foundrecord is None:
            return {'deleted': False}
        else:
            try:
                response, info = fetch_url(self.module, self.session.api_uri + "/REST/" +
                                           str(record_type).upper() + "Record/" +
                                           str(self.zone) + "/" + str(node) + "." +
                                           str(self.zone) + "/" +
                                           str(foundrecord['record_id']),
                                           method="delete",
                                           headers={'Content-Type': 'application/json', 'Auth-Token': self.session.auth_token})
            except Exception as exception:
                self.module.fail_json(msg=str(exception))
            else:
                if info["status"] >= 400:
                    self.module.fail_json(msg=str(info))
                else:
                    # body = response.read()
                    return {'deleted': True}

    def getpendingchanges(self):
        '''Get a list of the zone pending changes.'''
        try:
            response, info = fetch_url(self.module, self.session.api_uri + "/REST/ZoneChanges/" +
                                       str(self.zone) + "/",
                                       method="get",
                                       headers={'Content-Type': 'application/json', 'Auth-Token': self.session.auth_token})
        except Exception as exception:
            self.module.fail_json(msg=str(exception))
        else:
            if info["status"] >= 400:
                self.module.fail_json(msg=str(info))
            else:
                body = response.read()
                zonechanges = json.loads(body)['data']
                return zonechanges

    def publish(self):
        '''Publish pending zone changes'''
        payload = {'publish': True, 'notes': str(self.module.params['notes'])}

        try:
            response, info = fetch_url(self.module, self.session.api_uri + "/REST/Zone/" +
                                       str(self.zone) + "/",
                                       method="put",
                                       data=self.module.jsonify(payload),
                                       headers={'Content-Type': 'application/json', 'Auth-Token': self.session.auth_token})
        except Exception as exception:
            self.module.fail_json(msg=str(exception))
        else:
            if info["status"] >= 400:
                self.module.fail_json(msg=str(info))
            else:
                body = response.read()
                return json.loads(body)


def main():
    """Initiates module."""
    module = AnsibleModule(
        argument_spec=dict(
            dyn_customer_name=dict(required=False, default=None, type='str'),
            dyn_user_name=dict(required=False, default=None, type='str'),
            dyn_password=dict(required=False, default=None, type='str', no_log=True),
            zone=dict(required=True, default=None, type='str'),
            records=dict(required=True, default=None, type='list'),
            state=dict(required=False, default="present", type='str',
                       choices=["absent", "present"]),
            notes=dict(required=False, default="Published by Ansible", type='str'),
            validate_certs=dict(required=False, default=True, type='bool')
        ),
        supports_check_mode=True
    )
    if not module.params['records'] is None and module.params['state'] == "present":
        if len([record for record in module.params['records'] if record['rdata'] is None]) > 0:
            module.fail_json(msg="rdata should be specified for every node!")
    # Instanciate an API session.
    zone = DynDnsZone(module)
    changed = False
    json_output = {}

    # A loop is used not to trigger API rate limiting.
    for record in module.params['records']:
        json_output[record['node']] = {}
        if module.params['state'] == "present":
            if not module.check_mode:
                response = zone.recordadd(record_type=record['record_type'],
                                          node=record['node'],
                                          rdata=record['rdata'],
                                          ttl=str("0" if 'ttl' not in record.keys() else record['ttl']))
                if response['record_before'] != response['record_after']:
                    if len(response['record_before']) > 0 and response['record_before']['rdata'] != response['record_after']['rdata']:
                        json_output[record['node']]['changed'] = changed = True
                    elif response['record_after']['ttl'] == 0:
                        json_output[record['node']]['changed'] = changed = False
                    else:
                        json_output[record['node']]['changed'] = changed = True
                else:
                    json_output[record['node']]['changed'] = False
                json_output[record['node']]['record_before'] = response['record_before']
                json_output[record['node']]['record_after'] = response['record_after']
            else:
                modified_record = {'zone': str(module.params['zone']),
                                   'ttl': str("0" if 'ttl' not in record.keys() else record['ttl']),
                                   'record_type': str(record['record_type']),
                                   'fqdn': str(record['node'] + "." + module.params['zone']),
                                   'rdata': record['rdata']}
                response = zone.recordget(record_type=record['record_type'], node=record['node'])

                if response != modified_record:
                    if response['rdata'] != modified_record['rdata']:
                        json_output[record['node']]['changed'] = changed = True
                    elif modified_record['ttl'] == 0:
                        json_output[record['node']]['changed'] = changed = False
                    else:
                        json_output[record['node']]['changed'] = changed = True
                else:
                    json_output[record['node']]['changed'] = False
                json_output[record['node']]['record_before'] = response
                json_output[record['node']]['record_after'] = modified_record
        else:
            if not module.check_mode:
                response = zone.recorddelete(record_type=record['record_type'],
                                             node=record['node'],
                                             rdata=None if 'rdata' not in
                                             record.keys() else record['rdata'])
                json_output[record['node']]['deleted'] = changed = response['deleted']
            else:
                response = zone.recordget(record_type=record['record_type'], node=record['node'])
                if response is not None:
                    changed = True
                json_output[record['node']]['deleted'] = True if response is not None else False

    if (module.params['state'] == "present" and
            len([record for record in json_output.keys() if json_output[record]['changed']]) > 0) \
            or module.params['state'] == "absent" and \
            len([record for record in json_output.keys() if json_output[record]['deleted']]) > 0:

        if not module.check_mode:
            zone.publish()
        json_output['published'] = True
    else:
        json_output['published'] = False

    zone.session.logout()
    module.exit_json(changed=changed, data=json_output)


if __name__ == '__main__':
    main()
