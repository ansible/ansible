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
version_added: "2.6"
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
    description:
      - Dyn customer name required for API authentication. Can also be passed on
        as the DYN_CUSTOMER_NAME environment variable.
    required: false
  dyn_user_name:
    description:
      - Dyn username required for API authentication. Can also be passed on
        as the DYN_USER_NAME environment variable.
    required: false
  dyn_password:
    description:
      - Dyn password required for API authentication. Can also be passed on
        as the DYN_PASSWORD environment variable.
    required: false
  api_retries:
    default: 5
    description:
      - Maximum number of API retries when hitting Dyn's API rate limit. Can also
        be passed on as the DYN_API_RETRIES environment variable.
    required: False
  api_timeout:
    default: 60
    description:
      - Maximum timeout in seconds of each API call. Can also
        be passed on as the DYN_API_TIMEOUT environment variable.
    required: False
  zone:
    description:
      - Dyn DNS zone to act upon.
    required: true
  force_duplicate:
    type: bool
    default: False
    description:
      - Force the creation of a "duplicate" record sharing the same node of an existing record for
        supported record types, instead of updating an existing record (for example,
        a new TXT record with another rdata.txtdata value). Use with caution.
    required: False
  node:
    description:
      - Local part of the FQDN (e.g. 'www' in 'www.example.org').
    required: True
  record_type:
    default: A
    description:
      - Type of the record, case-insensitive. Every record exposed by the Dyn REST API
        should be supported, except for the ALIAS record type (https://help.dyn.com/rest-resources/).
    required: false
  rdata:
    description:
      - Record data value dictionary that should match the specified record type.
    required: true
  ttl:
    default: 0
    description:
      - Record Time-To-Live value, if not specified, will default to the zone default TTL.
    required: false
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
    type: bool
    default: true
    description:
      - Whether to valide TLS certificates during the module execution.
    required: false
'''

EXAMPLES = '''
# Create and publish a single A record, using the zone default TTL.
- dyn_record:
    dyn_customer_name: customer
    dyn_user_name: user
    dyn_password: password
    zone: myzone.com
    record_type: A
    node: www
    rdata:
      address: 1.2.3.4

# Create and publish a new A record, passing on credentials from the environment:
- dyn_record:
    zone: myzone.com
    node: www
    rdata:
      address: 1.2.3.4
    ttl: 30
    notes: Added a new node on {{ ansible_date_time.iso8601_micro }}
  environment:
    DYN_CUSTOMER_NAME: customer
    DYN_USER_NAME: user
    DYN_PASSWORD: password

# Delete a single CNAME record (matching rdata).
- dyn_record:
    dyn_customer_name: customer
    dyn_user_name: user
    dyn_password: password
    zone: myzone.com
    record_type: CNAME
    node: old
    rdata:
      cname: www.somedomain.org
    state: absent

# Add a single new TXT record, even if other TXT records sharing the same node (fqdn) already exist.
- dyn_record:
    dyn_customer_name: customer
    dyn_user_name: user
    dyn_password: password
    zone: myzone.com
    record_type: TXT
    node: _acme-challenge.www
    rdata:
      txtdata: somechallenge
    force_duplicate: true

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
old/new_record:
    description: Nested dictionary of the record(s) before updating/creating it/them (only when state is "present").
    type: dict
    returned: success
    sample: >
      {
        "myrecord": {
           "changed": true,
            "old_record": {
                "fqdn": "myrecord.myzone.com",
                "record_id": 0,
                "record_type": "A",
                "rdata": {
                    "address":"1.2.3.4"
                },
                "ttl": "30",
                "zone": "myzone.com"
            },
            "new_record": {
                "fqdn": "myrecord.myzone.com",
                "record_id": 284178946,
                "record_type": "A",
                "rdata": {
                    "address": "4.3.2.1"
                },
                "ttl": "15",
                "zone": "myzone.com"
            }
        },
        "myunchangedtxtrecord":
            "changed": false,
            "old_record": {
                "fqdn": "myunchangedtxtrecord.myzone.com",
                "zone": "myzone.com",
                "ttl": "30",
                "record_id": 214478213,
                "record_type": "TXT",
                "rdata": {
                    "txtdata": "sometxtdata"
                }
            },
            "new_record": {
                "fqdn": "myunchangedtxtrecord.myzone.com",
                "zone": "myzone.com",
                "ttl": "30",
                "record_id": 214478213,
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
from ansible.module_utils.dynect import DynDnsZone
from ansible.module_utils.basic import AnsibleModule


def main():
    """Initiates module."""
    module = AnsibleModule(
        argument_spec=dict(
            dyn_customer_name=dict(required=False, default=os.environ.get('DYN_CUSTOMER_NAME'), type='str'),
            dyn_user_name=dict(required=False, default=os.environ.get('DYN_USER_NAME'), type='str'),
            dyn_password=dict(required=False, default=os.environ.get('DYN_PASSWORD'), type='str', no_log=True),
            api_retries=dict(required=False, default=os.environ.get('DYN_API_RETRIES') or 5, type='int'),
            api_timeout=dict(required=False, default=os.environ.get('DYN_API_TIMEOUT') or 60, type='int'),
            zone=dict(required=True, default=None, type='str'),
            node=dict(required=True, default=None, type='str'),
            record_type=dict(required=False, default='A', type='str'),
            rdata=dict(required=True, default=None, type='dict'),
            ttl=dict(required=False, default=0, type='int'),
            force_duplicate=dict(required=False, default=False, type='bool'),
            state=dict(required=False, default="present", type='str',
                       choices=["absent", "present"]),
            notes=dict(required=False, default="Published by Ansible", type='str'),
            validate_certs=dict(required=False, default=True, type='bool')
        ),
        supports_check_mode=True
    )

    if module.params['api_retries'] <= 0:
        module.fail_json(msg="The number of API retries cannot be null or negative!")
    if module.params['api_timeout'] <= 0:
        module.fail_json(msg="The API timeout cannot be null or negative!")

    # Instanciate an API session.
    zone = DynDnsZone(module)
    changed = False
    json_output = {}

    json_output[module.params['node']] = {}
    if module.params['state'] == "present":
        if not module.check_mode:
            response = zone.recordaddorupdate(record_type=module.params['record_type'],
                                              node=module.params['node'],
                                              rdata=module.params['rdata'],
                                              ttl=module.params['ttl'])
        else:
            response = {}
            response['old_record'] = zone.recordget(record_type=module.params['record_type'],
                                                    node=module.params['node'],
                                                    rdata=module.params['rdata'])
            if not module.params['force_duplicate'] and response['old_record'] == {}:
                response['old_record'] = zone.recordget(record_type=module.params['record_type'],
                                                        node=module.params['node'])
            response['new_record'] = {'zone': module.params['zone'],
                                      'ttl': module.params['ttl'],
                                      'record_type': module.params['record_type'],
                                      'fqdn': module.params['node'] + "." + module.params['zone'],
                                      'rdata': module.params['rdata']}

        json_output[module.params['node']]['new_record'] = response['new_record']
        json_output[module.params['node']]['old_record'] = response['old_record']

        if response['old_record'] == {}:
            json_output[module.params['node']]['changed'] = changed = True
        elif response['old_record']['rdata'] != response['new_record']['rdata']:
            json_output[module.params['node']]['changed'] = changed = True
        elif response['old_record']['ttl'] != response['new_record']['ttl'] and response['new_record']['ttl'] != 0:
            json_output[module.params['node']]['changed'] = changed = True
        else:
            json_output[module.params['node']]['changed'] = changed = False
    else:
        if not module.check_mode:
            response = zone.recorddelete(record_type=module.params['record_type'],
                                         node=module.params['node'],
                                         rdata=module.params['rdata'])
            json_output[module.params['node']]['deleted'] = changed = response['deleted']
        else:
            response = zone.recordget(record_type=module.params['record_type'],
                                      node=module.params['node'],
                                      rdata=module.params['rdata'])
            if response != {}:
                changed = True
            json_output[module.params['node']]['deleted'] = True if response != {} else False

    if (module.params['state'] == "present" and json_output[module.params['node']]['changed']) or \
       (module.params['state'] == "absent" and json_output[module.params['node']]['deleted']):

        if not module.check_mode:
            zone.publish()
        json_output['published'] = True
    else:
        json_output['published'] = False

    zone.session.logout()
    module.exit_json(changed=changed, data=json_output)


if __name__ == '__main__':
    main()
