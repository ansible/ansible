#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2017, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: vr_dns_record
short_description: Manages DNS records on Vultr.
description:
  - Create, update and remove DNS records.
version_added: "2.5"
author: "René Moser (@resmo)"
options:
  name:
    description:
      - The record name (subrecord).
    required: true
    aliases: [ subrecord ]
  domain:
    description:
      - The domain the record is related to.
    required: true
  record_type:
    description:
      - Type of the record.
    default: A
    choices:
    - A
    - AAAA
    - CNAME
    - MX
    - SRV
    - ALIAS
    - SPF
    - TXT
    - NS
    aliases: [ type ]
  data:
    description:
      - Data of the record.
      - Required if C(state=present).
  ttl:
    description:
      - TTL of the record.
  multiple:
    description:
      - Whether to use more than one record with similar C(name).
      - Only allowed for a few record types, e.g. C(record_type=A).
      - C(data) will not be updated, it is used as a key to find existing records.
  priority:
    description:
      - Priority of the record.
      - Required for types MX and SRV if C(state=present)
  state:
    description:
      - State of the DNS record.
    default: present
    choices: [ present, absent ]
extends_documentation_fragment: vultr
'''

EXAMPLES = '''
- name: ensure an A record exists
  local_action:
    module: vr_dns_record
    name: www
    domain: example.com
    data: 10.10.10.10

- name: ensure a CNAME record exists
  local_action:
    module: vr_dns_record
    name: web
    record_type: CNAME
    domain: example.com
    data: www.example.com.

- name: ensure a record is absent
  local_action:
    module: vr_dns_record
    name: www
    domain: example.com
    state: absent
'''

RETURN = '''
---
vultr_api:
  description: Response from Vultr API with a few additions/modification
  returned: success
  type: complex
  contains:
    api_account:
      description: Account used in the ini file to select the key
      returned: success
      type: string
      sample: default
    api_timeout:
      description: Timeout used for the API requests
      returned: success
      type: int
      sample: 60
vultr_dns_record:
  description: Response from Vultr API
  returned: success
  type: complex
  contains:
    id:
      description: The ID of the DNS record.
      returned: success
      type: int
      sample: 1265277
    name:
      description: The name of the DNS record.
      returned: success
      type: string
      sample: web
    record_type:
      description: The name of the DNS record.
      returned: success
      type: string
      sample: web
    data:
      description: Data of the DNS record.
      returned: success
      type: string
      sample: 10.10.10.10
    domain:
      description: Domain the DNS record is related to.
      returned: success
      type: string
      sample: example.com
    priority:
      description: Priority of the DNS record.
      returned: success
      type: int
      sample: 10
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vultr import (
    Vultr,
    vultr_argument_spec,
)

RECORD_TYPES = [
    'A',
    'AAAA',
    'CNAME',
    'MX',
    'TXT',
    'NS',
    'SRV',
    'CAA',
    'SSHFP'
]


class AnsibleVultrDnsRecord(Vultr):

    def __init__(self, module):
        super(AnsibleVultrDnsRecord, self).__init__(module, "vultr_dns_record")

        self.returns = {
            'RECORDID': dict(key='id'),
            'name': dict(),
            'record': dict(),
            'priority': dict(),
            'data': dict(),
            'type': dict(key='record_type')
        }

    def get_record(self):
        records = self.api_query(path="/v1/dns/records?domain=%s" % self.module.params.get('domain'))

        for record in records or []:
            if record.get('type') != self.module.params.get('record_type'):
                continue

            if record.get('name') == self.module.params.get('name'):
                if not self.module.params.get('multiple'):
                    return record
                elif record.get('data') == self.module.params.get('data'):
                    return record
        return {}

    def present_record(self):
        record = self.get_record()
        if not record:
            record = self._create_record(record)
        else:
            record = self._update_record(record)
        return record

    def _create_record(self, record):
        self.result['changed'] = True
        data = {
            'name': self.module.params.get('name'),
            'domain': self.module.params.get('domain'),
            'data': self.module.params.get('data'),
            'type': self.module.params.get('record_type'),
            'priority': self.module.params.get('priority'),
        }
        self.result['diff']['before'] = {}
        self.result['diff']['after'] = data

        if not self.module.check_mode:
            self.api_query(
                path="/v1/dns/create_record",
                method="POST",
                data=data
            )
            record = self.get_record()
        return record

    def _update_record(self, record):
        data = {
            'RECORDID': record['RECORDID'],
            'name': self.module.params.get('name'),
            'domain': self.module.params.get('domain'),
            'data': self.module.params.get('data'),
            'type': self.module.params.get('record_type'),
            'priority': self.module.params.get('priority'),
        }
        has_changed = [k for k in data if k in record and data[k] != record[k]]
        if has_changed:
            self.result['changed'] = True

            self.result['diff']['before'] = record
            self.result['diff']['after'] = record.copy()
            self.result['diff']['after'].update(data)

            if not self.module.check_mode:
                self.api_query(
                    path="/v1/dns/update_record",
                    method="POST",
                    data=data
                )
                record = self.get_record()
        return record

    def absent_record(self):
        record = self.get_record()
        if record:
            self.result['changed'] = True

            data = {
                'RECORDID': record['RECORDID'],
                'domain': self.module.params.get('domain'),
            }

            self.result['diff']['before'] = record
            self.result['diff']['after'] = {}

            if not self.module.check_mode:
                self.api_query(
                    path="/v1/dns/delete_record",
                    method="POST",
                    data=data
                )
        return record


def main():
    argument_spec = vultr_argument_spec()
    argument_spec.update(dict(
        domain=dict(required=True),
        name=dict(required=True, aliases=['subrecord']),
        state=dict(choices=['present', 'absent'], default='present'),
        ttl=dict(type='int', default=300),
        record_type=dict(choices=RECORD_TYPES, default='A', aliases=['type']),
        multiple=dict(type='bool', default=False),
        priority=dict(type='int', default=0),
        data=dict()
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=[
            ('state', 'present', ['data']),
        ],
        supports_check_mode=True,
    )

    vr_record = AnsibleVultrDnsRecord(module)
    if module.params.get('state') == "absent":
        record = vr_record.absent_record()
    else:
        record = vr_record.present_record()

    result = vr_record.get_result(record)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
