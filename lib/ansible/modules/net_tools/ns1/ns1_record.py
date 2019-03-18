#!/usr/bin/python

# Copyright: (c) 2019, Matthew Burtless <mburtless@ns1.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community',
}

DOCUMENTATION = '''
---
module: ns1_record

short_description: Create, modify and delete NS1 hosted DNS records.

version_added: "2.8"

description:
  - Create, modify and delete record objects within an existing zone.

options:
  state:
    description:
      - Whether the record should be present or not.  Use C(present) to create
        or update and C(absent) to delete.
    default: present
    choices:
      - absent
      - present
  name:
    description:
      - The subdomain of the record. For apex records, this should match the
        value of I(zone).
    required: true
  zone:
    description:
      - Name of the existing DNS zone in which to manage the record.
    required: true
  answers:
    description:
      - An array of answers for this record (order matters). This can take
        many forms depending on record type and desired effect. See
        U(https://ns1.com/api) for more details.
    required: true
    suboptions:
      answer:
        description:
          - An array of RDATA values for this answer
        type: list
        required: false
      meta:
        description:
          - Answer level metadata
        type: dict
        required: false
  ignore_missing_zone:
    description:
      - Attempting to delete a record from a zone that is not present will
        normally result in an error. This error can be ignored by setting this
        flag to C(True). This module will then count any record without a valid
        zone as absent.  This is useful for ensuring a record is absent,
        regardless of the status of its zone.
    required: false
    default: false
  record_mode:
    description:
      - Whether existing I(answers) or I(filters) values unspecified in the module
        should be purged
    default: purge
    choices:
      - append
      - purge
  type:
    description:
      - The type of the record to create, modify or delete.
    required: true
    choices:
      - A
      - AAAA
      - ALIAS
      - AFSDB
      - CNAME
      - DNAME
      - HINFO
      - MX
      - NAPTR
      - NS
      - PTR
      - RP
      - SPF
      - SRV
      - TXT
  use_client_subnet:
    description:
      - Whether record should be EDNS-Client-Subnet enabled
    required: false
  meta:
    description:
      - Record level metadata.
    required: false
  link:
    description:
      - The target of a linked record.
    required: false
  filters:
    description:
      - An array of filters for the record, for use in configuring dynamic
        records (order matters)
    required: false
    suboptions:
      filter:
        description:
          - The type of filter.
        required: false
      config:
        description:
          - The filters' configuration
        type: dict
        required: false
  ttl:
    description:
      - The TTL of the record.
    required: false
    default: 3600
  regions:
    description:
      - The regions object for the record set.
    required: false

extends_documentation_fragment:
  - ns1

author:
  - 'Matthew Burtless (@mburtless)'
'''

EXAMPLES = '''
- name: Ensure an A record with two answers, metadata and filter chain
  ns1_record:
    apiKey: qACMD09OJXBxT7XOuRs8
    name: www
    zone: test.com
    state: present
    type: A
    answers:
        - answer:
            - 192.168.1.0
          meta:
            up: True
        - answer:
            - 192.168.1.1
          meta:
            up: True
    filters:
        - filter: up
          config: {}

- name: Ensure an A record, appending new answer to existing
  ns1_record:
    apiKey: qACMD09OJXBxT7XOuRs8
    name: www
    zone: test.com
    record_mode: append
    state: present
    type: A
    answers:
        - answer:
            - 192.168.1.3
          meta:
            up: True

- name: Delete an A record
  ns1_record:
    apiKey: qACMD09OJXBxT7XOuRs8
    name: www
    zone: test.com
    state: absent
    type: A
    answers: []

- name: Ensure an MX record at apex of zone with a single answer
  ns1_record:
    apiKey: qACMD09OJXBxT7XOuRs8
    name: test.com
    zone: test.com
    state: present
    type: MX
    answers:
      - answer:
          - 5
          - mail1.example.com
'''

RETURN = '''
'''

import copy

from ansible.module_utils.ns1 import NS1ModuleBase, HAS_NS1

try:
    from ns1 import NS1, Config
    from ns1.rest.errors import ResourceException
except ImportError:
    # This is handled in NS1 module_utils
    pass

RECORD_KEYS_MAP = dict(
    use_client_subnet=dict(appendable=False),
    answers=dict(appendable=True),
    meta=dict(appendable=False),
    link=dict(appendable=False),
    filters=dict(appendable=True),
    ttl=dict(appendable=False),
    regions=dict(appendable=False),
)

RECORD_TYPES = [
    'A',
    'AAAA',
    'ALIAS',
    'AFSDB',
    'CNAME',
    'DNAME',
    'HINFO',
    'MX',
    'NAPTR',
    'NS',
    'PTR',
    'RP',
    'SPF',
    'SRV',
    'TXT',
]


class NS1Record(NS1ModuleBase):
    def __init__(self):
        self.module_arg_spec = dict(
            name=dict(required=True, type='str'),
            zone=dict(required=True, type='str'),
            answers=dict(
                required=True,
                type='list',
                elements='dict',
                options=dict(
                    answer=dict(type='list', default=None),
                    meta=dict(type='dict', default=None),
                ),
            ),
            ignore_missing_zone=dict(required=False, type='bool', default=False),
            type=dict(required=True, type='str', choices=RECORD_TYPES),
            use_client_subnet=dict(required=False, type='bool', default=None),
            meta=dict(required=False, type='dict', default=None),
            link=dict(required=False, type='str', default=None),
            filters=dict(
                required=False,
                type='list',
                elements='dict',
                default=None,
                options=dict(
                    filter=dict(type='str', default=None),
                    config=dict(type='dict', default=None),
                ),
            ),
            ttl=dict(required=False, type='int', default=3600),
            regions=dict(required=False, type='dict', default=None),
            state=dict(
                required=False,
                type='str',
                default='present',
                choices=['present', 'absent'],
            ),
            record_mode=dict(
                required=False, type='str', default='purge', choices=['append', 'purge']
            ),
        )

        NS1ModuleBase.__init__(self, self.module_arg_spec, supports_check_mode=True)
        self.exec_module()

    def filter_empty_subparams(self, param_name):
        param = self.module.params.get(param_name)
        filtered = []
        if isinstance(param, list):
            for subparam in param:
                if isinstance(subparam, dict):
                    filtered.append(
                        dict(
                            (key, value)
                            for key, value in subparam.items()
                            if value is not None
                        )
                    )
        else:
            filtered = param
        return filtered

    def api_params(self):
        params = dict(
            (key, self.module.params.get(key))
            for key, value in RECORD_KEYS_MAP.items()
            if key != "answers" and self.module.params.get(key) is not None
        )
        return params

    def remove_id(self, d):
        if isinstance(d, dict):
            if 'id' in d:
                del d['id']
            for key, val in d.items():
                if isinstance(val, (dict, list)):
                    self.remove_id(val)
        if isinstance(d, list):
            for i in d:
                if isinstance(i, (dict, list)):
                    self.remove_id(i)
        return d

    def get_zone(self):
        to_return = None
        try:
            to_return = self.ns1.loadZone(self.module.params.get('zone'))
        except ResourceException as re:
            if re.response.code == 404:
                if (
                    self.module.params.get('ignore_missing_zone')
                    and self.module.params.get('state') == "absent"
                ):
                    # zone not found but we are in the absent state
                    # and the user doesn't care that the zone doesn't exist
                    # nothing to do and no change
                    self.module.exit_json(changed=False)
            else:
                # generic error or user cares about missing zone
                self.module.fail_json(
                    msg="error code %s - %s " % (re.response.code, re.message)
                )

        return to_return

    def get_record(self, zone):
        to_return = None
        try:
            to_return = zone.loadRecord(
                self.module.params.get('name'), self.module.params.get('type').upper()
            )
        except ResourceException as re:
            if re.response.code != 404:
                self.module.fail_json(
                    msg="error code %s - %s " % (re.response.code, re.message)
                )
                to_return = None
        return to_return

    def update(self, zone, record):
        # Clean copy of record to preserve IDs for response if no update required
        record_data = self.remove_id(copy.deepcopy(record.data))
        changed = False
        args = {}

        for key in RECORD_KEYS_MAP:
            input_data = self.filter_empty_subparams(key)

            if input_data is not None:
                if (
                    RECORD_KEYS_MAP[key]['appendable']
                    and self.module.params.get('record_mode') == 'append'
                ):
                    # Create union of input and existing record data, preserving existing order
                    input_data = record_data[key] + [
                        input_obj
                        for input_obj in input_data
                        if input_obj not in record_data[key]
                    ]

                if input_data != record_data[key]:
                    changed = True
                    args[key] = input_data

        if self.module.check_mode:
            # check mode short circuit before update
            self.module.exit_json(changed=changed)

        if changed:
            # update only if some changed data
            record = record.update(errback=self.errback_generator(), **args)

        self.module.exit_json(changed=changed, id=record['id'], data=record.data)

    def exec_module(self):
        state = self.module.params.get('state')
        zone = self.get_zone()
        record = self.get_record(zone)

        # record found
        if record:
            if state == "absent":
                if self.module.check_mode:
                    # short circut in check mode
                    self.module.exit_json(changed=True)

                record.delete(errback=self.errback_generator())
                self.module.exit_json(changed=True)
            else:
                self.update(zone, record)
        else:
            if state == "absent":
                self.module.exit_json(changed=False)
            else:
                if self.module.check_mode:
                    # short circuit in check mode
                    self.module.exit_json(changed=True)

                method_to_call = getattr(
                    zone, 'add_%s' % (self.module.params.get('type').upper())
                )

                record = method_to_call(
                    self.module.params.get('name'),
                    self.filter_empty_subparams('answers'),
                    errback=self.errback_generator(),
                    **self.api_params()
                )
                self.module.exit_json(changed=True, id=record['id'], data=record.data)


def main():
    NS1Record()


if __name__ == '__main__':
    main()
