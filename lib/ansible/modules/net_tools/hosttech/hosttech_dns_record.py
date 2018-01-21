#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2018 Felix Fontein
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: hosttech_dns_record

short_description: add or delete entries in Hosttech DNS service

version_added: "2.6"

description:
    - "Creates and deletes DNS records in Hosttech DNS service U(https://ns1.hosttech.eu/public/api?wsdl)."

options:
    state:
        description:
        - Specifies the state of the resource record.
        required: true
        choices: ['present', 'absent']
    zone:
        description:
        - The DNS zone to modify.
        required: true
    record:
        description:
        - The full DNS record to create or delete.
        required: true
    ttl:
        description:
        - The TTL to give the new record, in seconds.
        required: false
        default: 3600
    type:
        description:
        - The type of DNS record to create or delete.
        required: true
        choices: ['A', 'CNAME', 'MX', 'AAAA', 'TXT', 'PTR', 'SRV', 'SPF', 'NS', 'CAA']
    value:
        description:
        - The new value when creating a DNS record.
        - YAML lists or multiple comma-spaced values are allowed.
        - When deleting a record all values for the record must be specified or it will
          not be deleted.
        required: true
    overwrite:
        description:
        - Whether an existing record should be overwritten on create if values do not
          match.
        required: false
        default: false
        type: bool

author:
    - Felix Fontein (@felixfontein)

extends_documentation_fragment: hosttech
'''

EXAMPLES = '''
# Add new.foo.com as an A record with 3 IPs
- hosttech_dns_record:
      state: present
      zone: foo.com
      record: new.foo.com
      type: A
      ttl: 7200
      value: 1.1.1.1,2.2.2.2,3.3.3.3
      hosttech_username: foo
      hosttech_password: bar

# Update new.foo.com as an A record with a list of 3 IPs
- hosttech_dns_record:
      state: present
      zone: foo.com
      record: new.foo.com
      type: A
      ttl: 7200
      value:
        - 1.1.1.1
        - 2.2.2.2
        - 3.3.3.3
      hosttech_username: foo
      hosttech_password: bar

# Add an AAAA record.  Note that because there are colons in the value
# that the IPv6 address must be quoted.
- hosttech_dns_record:
      state: present
      zone: foo.com
      record: localhost.foo.com
      type: AAAA
      ttl: 7200
      value: "::1"
      hosttech_username: foo
      hosttech_password: bar

# Add a TXT record.
- hosttech_dns_record:
      state: present
      zone: foo.com
      record: localhost.foo.com
      type: TXT
      ttl: 7200
      value: 'bar'
      hosttech_username: foo
      hosttech_password: bar

# Remove the TXT record.
- hosttech_dns_record:
      state: absent
      zone: foo.com
      record: localhost.foo.com
      type: TXT
      ttl: 7200
      value: 'bar'
      hosttech_username: foo
      hosttech_password: bar

# Add a CAA record.
- hosttech_dns_record:
      state: present
      zone: foo.com
      record: foo.com
      type: CAA
      ttl: 3600
      value:
      - "128 issue letsencrypt.org"
      - "128 iodef mailto:webmaster@foo.com"
      hosttech_username: foo
      hosttech_password: bar

# Add an MX record.
- hosttech_dns_record:
      state: present
      zone: foo.com
      record: foo.com
      type: MX
      ttl: 3600
      value:
      - "10 mail.foo.com"
      hosttech_username: foo
      hosttech_password: bar

# Add a CNAME record.
- hosttech_dns_record:
      state: present
      zone: bla.foo.com
      record: foo.com
      type: CNAME
      ttl: 3600
      value:
      - foo.foo.com
      hosttech_username: foo
      hosttech_password: bar

# Add a PTR record.
- hosttech_dns_record:
      state: present
      zone: foo.foo.com
      record: foo.com
      type: PTR
      ttl: 3600
      value:
      - foo.foo.com
      hosttech_username: foo
      hosttech_password: bar

# Add an SPF record.
- hosttech_dns_record:
      state: present
      zone: foo.com
      record: foo.com
      type: SPF
      ttl: 3600
      value:
      - "v=spf1 a mx ~all"
      hosttech_username: foo
      hosttech_password: bar

# Add a PTR record.
- hosttech_dns_record:
      state: present
      zone: foo.com
      record: foo.com
      type: PTR
      ttl: 3600
      value:
      - "10 100 3333 service.foo.com"
      hosttech_username: foo
      hosttech_password: bar

'''

RETURN = '''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.hosttech import (
    HAS_LXML_ETREE, WSDLException, WSDLNetworkError,
    HostTechAPIError, HostTechAPIAuthError, HostTechAPI, DNSRecord,
)


def run_module():
    module_args = dict(
        state=dict(type='str', choices=['present', 'absent'], required=True),
        zone=dict(type='str', required=True),
        record=dict(type='str', required=True),
        ttl=dict(required=False, type='int', default=3600),
        type=dict(choices=['A', 'CNAME', 'MX', 'AAAA', 'TXT', 'PTR', 'SRV', 'SPF', 'NS', 'CAA'], required=True),
        value=dict(required=True, type='list'),
        overwrite=dict(required=False, default=False, type='bool'),
        hosttech_username=dict(type='str', required=True),
        hosttech_password=dict(type='str', required=True, no_log=True),
    )
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    if not HAS_LXML_ETREE:
        module.fail_json(msg='Needs lxml Python module (pip install lxml)')

    # Get zone and record.
    zone_in = module.params.get('zone').lower()
    record_in = module.params.get('record').lower()
    if zone_in[-1:] == '.':
        zone_in = zone_in[:-1]
    if record_in[-1:] == '.':
        record_in = record_in[:-1]

    # Convert record to prefix
    if not record_in.endswith('.' + zone_in) and record_in != zone_in:
        module.fail_json(msg='Record must be in zone')
    if record_in == zone_in:
        prefix = None
    else:
        prefix = record_in[:len(record_in) - len(zone_in) - 1]

    # Create API and get zone information
    api = HostTechAPI(module.params.get('hosttech_username'), module.params.get('hosttech_password'), debug=False)
    try:
        zone = api.get_zone(zone_in)
        if zone is None:
            module.fail_json(msg='Zone not found')
    except HostTechAPIAuthError as e:
        module.fail_json(msg='Cannot authenticate', error=e.message)
    except HostTechAPIError as e:
        module.fail_json(msg='Internal error (API level)', error=e.message)
    except WSDLException as e:
        module.fail_json(msg='Internal error (WSDL level)', error=e.message)

    # Find matching records
    type_in = module.params.get('type')
    records = []
    for record in zone.records:
        if record.prefix == prefix and record.type == type_in:
            records.append(record)

    # Parse records
    values = []
    value_in = module.params.get('value')
    for value in value_in:
        if type_in in ('PTR', 'MX'):
            priority, value = value.split(' ', 1)
            values.append((int(priority), value))
        else:
            values.append((None, value))

    # Compare records
    ttl_in = module.params.get('ttl')
    mismatch = False
    mismatch_records = []
    for record in records:
        if record.ttl != ttl_in:
            mismatch = True
            mismatch_records.append(record)
            continue
        val = (record.priority, record.target)
        if val in values:
            values.remove(val)
        else:
            mismatch = True
            mismatch_records.append(record)
            continue
    if values:
        mismatch = True

    # Determine what to do
    to_create = []
    to_delete = []
    to_change = []
    if module.params.get('state') == 'present':
        if records and mismatch:
            # Mismatch: user wants to overwrite?
            if module.params.get('overwrite'):
                to_delete.extend(mismatch_records)
            else:
                module.fail_json(msg="Record already exists with different value. Set 'overwrite' to replace it")
        for priority, target in values:
            if to_delete:
                # If there's a record to delete, change it to new record
                record = to_delete.pop()
                to_change.append(record)
            else:
                # Otherwise create new record
                record = DNSRecord()
                to_create.append(record)
            record.prefix = prefix
            record.type = type_in
            record.ttl = ttl_in
            record.priority = priority
            record.target = target
    if module.params.get('state') == 'absent':
        if not mismatch:
            to_delete.extend(records)

    # Is there nothing to change?
    if len(to_create) == 0 and len(to_delete) == 0 and len(to_change) == 0:
        module.exit_json(changed=False)

    # Actually do something
    if not module.check_mode:
        try:
            for record in to_delete:
                api.delete_record(record)
            for record in to_change:
                api.update_record(record)
            for record in to_create:
                api.add_record(zone_in, record)
        except HostTechAPIAuthError as e:
            module.fail_json(msg='Cannot authenticate', error=e.message)
        except HostTechAPIError as e:
            module.fail_json(msg='Internal error (API level)', error=e.message)
        except WSDLNetworkError as e:
            module.fail_json(msg='Network error: {0}'.format(e.message))
        except WSDLException as e:
            module.fail_json(msg='Internal error (WSDL level)', error=e.message)
    module.exit_json(changed=True)


def main():
    run_module()


if __name__ == '__main__':
    main()
