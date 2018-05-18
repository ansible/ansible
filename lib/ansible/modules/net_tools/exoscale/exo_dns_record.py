#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2016, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: exo_dns_record
short_description: Manages DNS records on Exoscale DNS.
description:
    - Create, update and delete records.
version_added: "2.2"
author: "René Moser (@resmo)"
options:
  name:
    description:
      - Name of the record.
    default: ""
  domain:
    description:
      - Domain the record is related to.
    required: true
  record_type:
    description:
      - Type of the record.
    default: A
    choices: [ A, ALIAS, CNAME, MX, SPF, URL, TXT, NS, SRV, NAPTR, PTR, AAAA, SSHFP, HINFO, POOL ]
    aliases: [ rtype, type ]
  content:
    description:
      - Content of the record.
      - Required if C(state=present) or C(multiple=yes).
    aliases: ['value', 'address']
  ttl:
    description:
      - TTL of the record in seconds.
    default: 3600
  prio:
    description:
      - Priority of the record.
    aliases: [ priority ]
  multiple:
    description:
      - Whether there are more than one records with similar C(name) and C(record_type).
      - Only allowed for a few record types, e.g. C(record_type=A), C(record_type=NS) or C(record_type=MX).
      - C(content) will not be updated, instead it is used as a key to find existing records.
    type: bool
    default: no
  state:
    description:
      - State of the record.
    default: present
    choices: [ present, absent ]
extends_documentation_fragment: exoscale
'''

EXAMPLES = '''
- name: Create or update an A record
  local_action:
    module: exo_dns_record
    name: web-vm-1
    domain: example.com
    content: 1.2.3.4

- name: Update an existing A record with a new IP
  local_action:
    module: exo_dns_record
    name: web-vm-1
    domain: example.com
    content: 1.2.3.5

- name: Create another A record with same name
  local_action:
    module: exo_dns_record
    name: web-vm-1
    domain: example.com
    content: 1.2.3.6
    multiple: yes

- name: Create or update a CNAME record
  local_action:
    module: exo_dns_record
    name: www
    domain: example.com
    record_type: CNAME
    content: web-vm-1

- name: Create another MX record
  local_action:
    module: exo_dns_record
    domain: example.com
    record_type: MX
    content: mx1.example.com
    prio: 10
    multiple: yes

- name: Delete one MX record out of multiple
  local_action:
    module: exo_dns_record
    domain: example.com
    record_type: MX
    content: mx1.example.com
    multiple: yes
    state: absent

- name: Remove a single A record
  local_action:
    module: exo_dns_record
    name: www
    domain: example.com
    state: absent
'''

RETURN = '''
---
exo_dns_record:
    description: API record results
    returned: success
    type: complex
    contains:
        content:
            description: value of the record
            returned: success
            type: string
            sample: 1.2.3.4
        created_at:
            description: When the record was created
            returned: success
            type: string
            sample: "2016-08-12T15:24:23.989Z"
        domain:
            description: Name of the domain
            returned: success
            type: string
            sample: example.com
        domain_id:
            description: ID of the domain
            returned: success
            type: int
            sample: 254324
        id:
            description: ID of the record
            returned: success
            type: int
            sample: 254324
        name:
            description: name of the record
            returned: success
            type: string
            sample: www
        parent_id:
            description: ID of the parent
            returned: success
            type: int
            sample: null
        prio:
            description: Priority of the record
            returned: success
            type: int
            sample: 10
        record_type:
            description: Priority of the record
            returned: success
            type: string
            sample: A
        system_record:
            description: Whether the record is a system record or not
            returned: success
            type: bool
            sample: false
        ttl:
            description: Time to live of the record
            returned: success
            type: int
            sample: 3600
        updated_at:
            description: When the record was updated
            returned: success
            type: string
            sample: "2016-08-12T15:24:23.989Z"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.exoscale import ExoDns, exo_dns_argument_spec, exo_dns_required_together


EXO_RECORD_TYPES = [
    'A',
    'ALIAS',
    'CNAME',
    'MX',
    'SPF',
    'URL',
    'TXT',
    'NS',
    'SRV',
    'NAPTR',
    'PTR',
    'AAAA',
    'SSHFP',
    'HINFO',
    'POOL'
]


class ExoDnsRecord(ExoDns):

    def __init__(self, module):
        super(ExoDnsRecord, self).__init__(module)

        self.domain = self.module.params.get('domain').lower()
        self.name = self.module.params.get('name').lower()
        if self.name == self.domain:
            self.name = ""

        self.multiple = self.module.params.get('multiple')
        self.record_type = self.module.params.get('record_type')
        self.content = self.module.params.get('content')

    def _create_record(self, record):
        self.result['changed'] = True
        data = {
            'record': {
                'name': self.name,
                'record_type': self.record_type,
                'content': self.content,
                'ttl': self.module.params.get('ttl'),
                'prio': self.module.params.get('prio'),
            }
        }
        self.result['diff']['after'] = data['record']
        if not self.module.check_mode:
            record = self.api_query("/domains/%s/records" % self.domain, "POST", data)
        return record

    def _update_record(self, record):
        data = {
            'record': {
                'name': self.name,
                'content': self.content,
                'ttl': self.module.params.get('ttl'),
                'prio': self.module.params.get('prio'),
            }
        }
        if self.has_changed(data['record'], record['record']):
            self.result['changed'] = True
            if not self.module.check_mode:
                record = self.api_query("/domains/%s/records/%s" % (self.domain, record['record']['id']), "PUT", data)
        return record

    def get_record(self):
        domain = self.module.params.get('domain')
        records = self.api_query("/domains/%s/records" % domain, "GET")

        result = {}
        for r in records:

            if r['record']['record_type'] != self.record_type:
                continue

            r_name = r['record']['name'].lower()
            r_content = r['record']['content']

            if r_name == self.name:
                if not self.multiple:
                    if result:
                        self.module.fail_json(msg="More than one record with record_type=%s and name=%s params. "
                                                  "Use multiple=yes for more than one record." % (self.record_type, self.name))
                    else:
                        result = r
                elif r_content == self.content:
                    return r

        return result

    def present_record(self):
        record = self.get_record()
        if not record:
            record = self._create_record(record)
        else:
            record = self._update_record(record)
        return record

    def absent_record(self):
        record = self.get_record()
        if record:
            self.result['diff']['before'] = record
            self.result['changed'] = True
            if not self.module.check_mode:
                self.api_query("/domains/%s/records/%s" % (self.domain, record['record']['id']), "DELETE")
        return record

    def get_result(self, resource):
        if resource:
            self.result['exo_dns_record'] = resource['record']
            self.result['exo_dns_record']['domain'] = self.domain
        return self.result


def main():
    argument_spec = exo_dns_argument_spec()
    argument_spec.update(dict(
        name=dict(default=""),
        record_type=dict(choices=EXO_RECORD_TYPES, aliases=['rtype', 'type'], default='A'),
        content=dict(aliases=['value', 'address']),
        multiple=(dict(type='bool', default=False)),
        ttl=dict(type='int', default=3600),
        prio=dict(type='int', aliases=['priority']),
        domain=dict(required=True),
        state=dict(choices=['present', 'absent'], default='present'),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=exo_dns_required_together(),
        required_if=[
            ('state', 'present', ['content']),
            ('multiple', True, ['content']),
        ],
        supports_check_mode=True,
    )

    exo_dns_record = ExoDnsRecord(module)
    if module.params.get('state') == "present":
        resource = exo_dns_record.present_record()
    else:
        resource = exo_dns_record.absent_record()

    result = exo_dns_record.get_result(resource)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
