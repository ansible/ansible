#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2019 Gregory Thiemonge <gregory.thiemonge@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: gandi_livedns
author:
- Gregory Thiemonge (@gthiemonge)
requirements:
- python >= 2.6
version_added: "2.9"
short_description: Manage Gandi LiveDNS records
description:
- "Manages dns records via the Gandi LiveDNS API, see the docs: U(https://doc.livedns.gandi.net/)"
options:
  api_key:
    description:
    - Account API token.
    type: str
    required: true
  record:
    description:
    - Record to add.
    - Default is C(@) (e.g. the zone name).
    type: str
    default: '@'
    required: true
    aliases: [ name ]
  state:
    description:
    - Whether the record(s) should exist or not.
    type: str
    choices: [ absent, present ]
    default: present
  ttl:
    description:
    - The TTL to give the new record.
    - Default is C(10800) when C(state=present).
    type: int
  type:
    description:
      - The type of DNS record to create.
    type: str
    required: true
    choices: [ A, AAAA, ALIAS, CAA, CDS, CNAME, DNAME, DS, KEY, LOC, MX, NS, PTR, SPF, SRV, SSHFP, TLSA, TXT, WKS ]
  values:
    description:
    - The record values.
    - Required for C(state=present).
    type: list
    aliases: [ content ]
  zone:
    description:
    - The name of the Zone to work with (e.g. "example.com").
    - The Zone must already exist.
    type: str
    required: true
  domain:
    description:
    - The name of the Domain to work with (e.g. "example.com").
    type: str
'''

EXAMPLES = r'''
- name: Create a test A record to point to 127.0.0.1 in the my.com zone.
  gandi_livedns:
    zone: my.com
    record: test
    type: A
    values:
    - 127.0.0.1
    api_key: dummyapitoken
  register: record

- name: Create a mail CNAME record to www.my.com domain
  gandi_livedns:
    domain: my.com
    type: CNAME
    record: mail
    values:
    - www
    api_key: dummyapitoken
    state: present

- name: Change its TTL
  gandi_livedns:
    domain: my.com
    type: CNAME
    values:
    - www
    ttl: 10800
    api_key: dummyapitoken
    state: present

- name: Delete the record
  gandi_livedns:
    domain: my.com
    type: CNAME
    record: mail
    api_key: dummyapitoken
    state: absent
'''

RETURN = r'''
record:
    description: A dictionary containing the record data.
    returned: success, except on record deletion
    type: complex
    contains:
        values:
            description: The record content (details depend on record type).
            returned: success
            type: list
            sample:
            - 192.0.2.91
            - 192.0.2.92
        name:
            description: The record name.
            returned: success
            type: str
            sample: www
        ttl:
            description: The time-to-live for the record.
            returned: success
            type: int
            sample: 300
        type:
            description: The record type.
            returned: success
            type: str
            sample: A
        domain:
            description: The domain associated with the record.
            returned: success
            type: str
            sample: my.com
        zone:
            description: The zone associated with the record.
            returned: success
            type: str
            sample: my.com
'''


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.gandi_livedns_api import GandiLiveDNSAPI


def main():
    module = AnsibleModule(
        argument_spec=dict(
            api_key=dict(type='str', required=True, no_log=True),
            record=dict(type='str', default='@', aliases=['name']),
            state=dict(type='str', default='present', choices=['absent', 'present']),
            ttl=dict(type='int', default=None),
            type=dict(type='str', choices=['A', 'AAAA', 'ALIAS', 'CAA', 'CDS', 'CNAME', 'DNAME', 'DS', 'KEY', 'LOC', 'MX', 'NS', 'PTR', 'SPF', 'SRV',
                                           'SSHFP', 'TLSA', 'TXT', 'WKS']),
            values=dict(type='list', aliases=['content']),
            zone=dict(type='str'),
            domain=dict(type='str'),
        ),
        supports_check_mode=True,
        required_if=[
            ('state', 'present', ['record', 'type', 'values']),
            ('state', 'absent', ['record', 'type']),
        ],
    )

    if not module.params['zone'] and not module.params['domain']:
        module.fail_json(msg="At least one of zone and domain parameters need to be defined.")
    if module.params['state'] == 'present' and module.params['ttl'] is None:
        module.params['ttl'] = 10800

    gandi_api = GandiLiveDNSAPI(module)

    if module.params['state'] == 'present':
        ret, changed = gandi_api.ensure_dns_record(module.params['record'],
                                                   module.params['type'],
                                                   module.params['ttl'],
                                                   module.params['values'],
                                                   module.params['zone'],
                                                   module.params['domain'])
    else:
        ret, changed = gandi_api.delete_dns_record(module.params['record'],
                                                   module.params['type'],
                                                   module.params['ttl'],
                                                   module.params['values'],
                                                   module.params['zone'],
                                                   module.params['domain'])

    result = dict(
        changed=changed,
    )
    if ret:
        result['record'] = gandi_api.build_result(ret,
                                                  module.params['zone'],
                                                  module.params['domain'])

    module.exit_json(**result)


if __name__ == '__main__':
    main()
