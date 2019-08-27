#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018 Nicolai Buchwitz <nb@tipi-net.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: netcup_dns
notes: []
version_added: 2.7.0
short_description: manage Netcup DNS records
description:
  - "Manages DNS records via the Netcup API, see the docs U(https://ccp.netcup.net/run/webservice/servers/endpoint.php)"
options:
  api_key:
    description:
      - API key for authentification, must be obtained via the netcup CCP (U(https://ccp.netcup.net))
    required: True
  api_password:
    description:
      - API password for authentification, must be obtained via the netcup CCP (https://ccp.netcup.net)
    required: True
  customer_id:
    description:
      - Netcup customer id
    required: True
  domain:
    description:
      - Domainname the records should be added / removed
    required: True
  record:
    description:
      - Record to add or delete, supports wildcard (*). Default is C(@) (e.g. the zone name)
    default: "@"
    aliases: [ name ]
  type:
    description:
      - Record type
    choices: ['A', 'AAAA', 'MX', 'CNAME', 'CAA', 'SRV', 'TXT', 'TLSA', 'NS', 'DS']
    required: True
  value:
    description:
      - Record value
    required: true
  solo:
    type: bool
    default: False
    description:
      - Whether the record should be the only one for that record type and record name. Only use with C(state=present)
      - This will delete all other records with the same record name and type.
  priority:
    description:
      - Record priority. Required for C(type=MX)
    required: False
  state:
    description:
      - Whether the record should exist or not
    required: False
    default: present
    choices: [ 'present', 'absent' ]
requirements:
  - "nc-dnsapi >= 0.1.3"
author: "Nicolai Buchwitz (@nbuchwitz)"

'''

EXAMPLES = '''
- name: Create a record of type A
  netcup_dns:
    api_key: "..."
    api_password: "..."
    customer_id: "..."
    domain: "example.com"
    name: "mail"
    type: "A"
    value: "127.0.0.1"

- name: Delete that record
  netcup_dns:
    api_key: "..."
    api_password: "..."
    customer_id: "..."
    domain: "example.com"
    name: "mail"
    type: "A"
    value: "127.0.0.1"
    state: absent

- name: Create a wildcard record
  netcup_dns:
    api_key: "..."
    api_password: "..."
    customer_id: "..."
    domain: "example.com"
    name: "*"
    type: "A"
    value: "127.0.1.1"

- name: Set the MX record for example.com
  netcup_dns:
    api_key: "..."
    api_password: "..."
    customer_id: "..."
    domain: "example.com"
    type: "MX"
    value: "mail.example.com"

- name: Set a record and ensure that this is the only one
  netcup_dns:
    api_key: "..."
    api_password: "..."
    customer_id: "..."
    name: "demo"
    domain: "example.com"
    type: "AAAA"
    value: "::1"
    solo: true
'''

RETURN = '''
records:
    description: list containing all records
    returned: success
    type: complex
    contains:
        name:
            description: the record name
            returned: success
            type: str
            sample: fancy-hostname
        type:
            description: the record type
            returned: succcess
            type: str
            sample: A
        value:
            description: the record destination
            returned: success
            type: str
            sample: 127.0.0.1
        priority:
            description: the record priority (only relevant if type=MX)
            returned: success
            type: int
            sample: 0
        id:
            description: internal id of the record
            returned: success
            type: int
            sample: 12345
'''

import traceback

from ansible.module_utils.basic import AnsibleModule, missing_required_lib

NCDNSAPI_IMP_ERR = None
try:
    import nc_dnsapi
    from nc_dnsapi import DNSRecord

    HAS_NCDNSAPI = True
except ImportError:
    NCDNSAPI_IMP_ERR = traceback.format_exc()
    HAS_NCDNSAPI = False


def main():
    module = AnsibleModule(
        argument_spec=dict(
            api_key=dict(required=True, no_log=True),
            api_password=dict(required=True, no_log=True),
            customer_id=dict(required=True, type='int'),

            domain=dict(required=True),
            record=dict(required=False, default='@', aliases=['name']),
            type=dict(required=True, choices=['A', 'AAAA', 'MX', 'CNAME', 'CAA', 'SRV', 'TXT', 'TLSA', 'NS', 'DS']),
            value=dict(required=True),
            priority=dict(required=False, type='int'),
            solo=dict(required=False, type='bool', default=False),
            state=dict(required=False, choices=['present', 'absent'], default='present'),

        ),
        supports_check_mode=True
    )

    if not HAS_NCDNSAPI:
        module.fail_json(msg=missing_required_lib('nc-dnsapi'), exception=NCDNSAPI_IMP_ERR)

    api_key = module.params.get('api_key')
    api_password = module.params.get('api_password')
    customer_id = module.params.get('customer_id')
    domain = module.params.get('domain')
    record_type = module.params.get('type')
    record = module.params.get('record')
    value = module.params.get('value')
    priority = module.params.get('priority')
    solo = module.params.get('solo')
    state = module.params.get('state')

    if record_type == 'MX' and not priority:
        module.fail_json(msg="record type MX required the 'priority' argument")

    has_changed = False
    all_records = []
    try:
        with nc_dnsapi.Client(customer_id, api_key, api_password) as api:
            all_records = api.dns_records(domain)
            record = DNSRecord(record, record_type, value, priority=priority)

            # try to get existing record
            record_exists = False
            for r in all_records:
                if r == record:
                    record_exists = True
                    record = r

                    break

            if state == 'present':
                if solo:
                    obsolete_records = [r for r in all_records if
                                        r.hostname == record.hostname
                                        and r.type == record.type
                                        and not r.destination == record.destination]

                    if obsolete_records:
                        if not module.check_mode:
                            all_records = api.delete_dns_records(domain, obsolete_records)

                        has_changed = True

                if not record_exists:
                    if not module.check_mode:
                        all_records = api.add_dns_record(domain, record)

                    has_changed = True
            elif state == 'absent' and record_exists:
                if not module.check_mode:
                    all_records = api.delete_dns_record(domain, record)

                has_changed = True

    except Exception as ex:
        module.fail_json(msg=ex.message)

    module.exit_json(changed=has_changed, result={"records": [record_data(r) for r in all_records]})


def record_data(r):
    return {"name": r.hostname, "type": r.type, "value": r.destination, "priority": r.priority, "id": r.id}


if __name__ == '__main__':
    main()
