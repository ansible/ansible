#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 CallFire Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


################################################################################
# Documentation
################################################################################

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: gcdns_record
short_description: Creates or removes resource records in Google Cloud DNS
description:
    - Creates or removes resource records in Google Cloud DNS.
version_added: "2.2"
author: "William Albert (@walbert947)"
requirements:
    - "python >= 2.6"
    - "apache-libcloud >= 0.19.0"
options:
    state:
        description:
            - Whether the given resource record should or should not be present.
        required: false
        choices: ["present", "absent"]
        default: "present"
    record:
        description:
            - The fully-qualified domain name of the resource record.
        required: true
        aliases: ['name']
    zone:
        description:
            - The DNS domain name of the zone (e.g., example.com).
            - One of either I(zone) or I(zone_id) must be specified as an
              option, or the module will fail.
            - If both I(zone) and I(zone_id) are specified, I(zone_id) will be
              used.
        required: false
    zone_id:
        description:
            - The Google Cloud ID of the zone (e.g., example-com).
            - One of either I(zone) or I(zone_id) must be specified as an
              option, or the module will fail.
            - These usually take the form of domain names with the dots replaced
              with dashes. A zone ID will never have any dots in it.
            - I(zone_id) can be faster than I(zone) in projects with a large
              number of zones.
            - If both I(zone) and I(zone_id) are specified, I(zone_id) will be
              used.
        required: false
    type:
        description:
            - The type of resource record to add.
        required: true
        choices: [ 'A', 'AAAA', 'CNAME', 'SRV', 'TXT', 'SOA', 'NS', 'MX', 'SPF', 'PTR' ]
    record_data:
        description:
            - The record_data to use for the resource record.
            - I(record_data) must be specified if I(state) is C(present) or
              I(overwrite) is C(True), or the module will fail.
            - Valid record_data vary based on the record's I(type). In addition,
              resource records that contain a DNS domain name in the value
              field (e.g., CNAME, PTR, SRV, .etc) MUST include a trailing dot
              in the value.
            - Individual string record_data for TXT records must be enclosed in
              double quotes.
            - For resource records that have the same name but different
              record_data (e.g., multiple A records), they must be defined as
              multiple list entries in a single record.
        required: false
        aliases: ['value']
    ttl:
        description:
            - The amount of time in seconds that a resource record will remain
              cached by a caching resolver.
        required: false
        default: 300
    overwrite:
        description:
            - Whether an attempt to overwrite an existing record should succeed
              or fail. The behavior of this option depends on I(state).
            - If I(state) is C(present) and I(overwrite) is C(True), this
              module will replace an existing resource record of the same name
              with the provided I(record_data). If I(state) is C(present) and
              I(overwrite) is C(False), this module will fail if there is an
              existing resource record with the same name and type, but
              different resource data.
            - If I(state) is C(absent) and I(overwrite) is C(True), this
              module will remove the given resource record unconditionally.
              If I(state) is C(absent) and I(overwrite) is C(False), this
              module will fail if the provided record_data do not match exactly
              with the existing resource record's record_data.
        required: false
        choices: [True, False]
        default: False
    service_account_email:
        description:
            - The e-mail address for a service account with access to Google
              Cloud DNS.
        required: false
        default: null
    pem_file:
        description:
            - The path to the PEM file associated with the service account
              email.
            - This option is deprecated and may be removed in a future release.
              Use I(credentials_file) instead.
        required: false
        default: null
    credentials_file:
        description:
            - The path to the JSON file associated with the service account
              email.
        required: false
        default: null
    project_id:
        description:
            - The Google Cloud Platform project ID to use.
        required: false
        default: null
notes:
    - See also M(gcdns_zone).
    - This modules's underlying library does not support in-place updates for
      DNS resource records. Instead, resource records are quickly deleted and
      recreated.
    - SOA records are technically supported, but their functionality is limited
      to verifying that a zone's existing SOA record matches a pre-determined
      value. The SOA record cannot be updated.
    - Root NS records cannot be updated.
    - NAPTR records are not supported.
'''

EXAMPLES = '''
# Create an A record.
- gcdns_record:
    record: 'www1.example.com'
    zone: 'example.com'
    type: A
    value: '1.2.3.4'

# Update an existing record.
- gcdns_record:
    record: 'www1.example.com'
    zone: 'example.com'
    type: A
    overwrite: true
    value: '5.6.7.8'

# Remove an A record.
- gcdns_record:
    record: 'www1.example.com'
    zone_id: 'example-com'
    state: absent
    type: A
    value: '5.6.7.8'

# Create a CNAME record.
- gcdns_record:
    record: 'www.example.com'
    zone_id: 'example-com'
    type: CNAME
    value: 'www.example.com.'    # Note the trailing dot

# Create an MX record with a custom TTL.
- gcdns_record:
    record: 'example.com'
    zone: 'example.com'
    type: MX
    ttl: 3600
    value: '10 mail.example.com.'    # Note the trailing dot

# Create multiple A records with the same name.
- gcdns_record:
    record: 'api.example.com'
    zone_id: 'example-com'
    type: A
    record_data:
      - '192.0.2.23'
      - '10.4.5.6'
      - '198.51.100.5'
      - '203.0.113.10'

# Change the value of an existing record with multiple record_data.
- gcdns_record:
    record: 'api.example.com'
    zone: 'example.com'
    type: A
    overwrite: true
    record_data:           # WARNING: All values in a record will be replaced
      - '192.0.2.23'
      - '192.0.2.42'    # The changed record
      - '198.51.100.5'
      - '203.0.113.10'

# Safely remove a multi-line record.
- gcdns_record:
    record: 'api.example.com'
    zone_id: 'example-com'
    state: absent
    type: A
    record_data:           # NOTE: All of the values must match exactly
      - '192.0.2.23'
      - '192.0.2.42'
      - '198.51.100.5'
      - '203.0.113.10'

# Unconditionally remove a record.
- gcdns_record:
    record: 'api.example.com'
    zone_id: 'example-com'
    state: absent
    overwrite: true   # overwrite is true, so no values are needed
    type: A

# Create an AAAA record
- gcdns_record:
    record: 'www1.example.com'
    zone: 'example.com'
    type: AAAA
    value: 'fd00:db8::1'

# Create a PTR record
- gcdns_record:
    record: '10.5.168.192.in-addr.arpa'
    zone: '5.168.192.in-addr.arpa'
    type: PTR
    value: 'api.example.com.'    # Note the trailing dot.

# Create an NS record
- gcdns_record:
    record: 'subdomain.example.com'
    zone: 'example.com'
    type: NS
    ttl: 21600
    record_data:
      - 'ns-cloud-d1.googledomains.com.'    # Note the trailing dots on values
      - 'ns-cloud-d2.googledomains.com.'
      - 'ns-cloud-d3.googledomains.com.'
      - 'ns-cloud-d4.googledomains.com.'

# Create a TXT record
- gcdns_record:
    record: 'example.com'
    zone_id: 'example-com'
    type: TXT
    record_data:
      - '"v=spf1 include:_spf.google.com -all"'   # A single-string TXT value
      - '"hello " "world"'    # A multi-string TXT value
'''

RETURN = '''
overwrite:
    description: Whether to the module was allowed to overwrite the record
    returned: success
    type: boolean
    sample: True
record:
    description: Fully-qualified domain name of the resource record
    returned: success
    type: string
    sample: mail.example.com.
state:
    description: Whether the record is present or absent
    returned: success
    type: string
    sample: present
ttl:
    description: The time-to-live of the resource record
    returned: success
    type: int
    sample: 300
type:
    description: The type of the resource record
    returned: success
    type: string
    sample: A
record_data:
    description: The resource record values
    returned: success
    type: list
    sample: ['5.6.7.8', '9.10.11.12']
zone:
    description: The dns name of the zone
    returned: success
    type: string
    sample: example.com.
zone_id:
    description: The Google Cloud DNS ID of the zone
    returned: success
    type: string
    sample: example-com
'''


################################################################################
# Imports
################################################################################

import socket
from distutils.version import LooseVersion

try:
    from libcloud import __version__ as LIBCLOUD_VERSION
    from libcloud.common.google import InvalidRequestError
    from libcloud.common.types import LibcloudError
    from libcloud.dns.types import Provider
    from libcloud.dns.types import RecordDoesNotExistError
    from libcloud.dns.types import ZoneDoesNotExistError
    HAS_LIBCLOUD = True
except ImportError:
    HAS_LIBCLOUD = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.gcdns import gcdns_connect


################################################################################
# Constants
################################################################################

# Apache libcloud 0.19.0 was the first to contain the non-beta Google Cloud DNS
# v1 API. Earlier versions contained the beta v1 API, which has since been
# deprecated and decommissioned.
MINIMUM_LIBCLOUD_VERSION = '0.19.0'

# The libcloud Google Cloud DNS provider.
PROVIDER = Provider.GOOGLE

# The records that libcloud's Google Cloud DNS provider supports.
#
# Libcloud has a RECORD_TYPE_MAP dictionary in the provider that also contains
# this information and is the authoritative source on which records are
# supported, but accessing the dictionary requires creating a Google Cloud DNS
# driver object, which is done in a helper module.
#
# I'm hard-coding the supported record types here, because they (hopefully!)
# shouldn't change much, and it allows me to use it as a "choices" parameter
# in an AnsibleModule argument_spec.
SUPPORTED_RECORD_TYPES = ['A', 'AAAA', 'CNAME', 'SRV', 'TXT', 'SOA', 'NS', 'MX', 'SPF', 'PTR']


################################################################################
# Functions
################################################################################

def create_record(module, gcdns, zone, record):
    """Creates or overwrites a resource record."""

    overwrite = module.boolean(module.params['overwrite'])
    record_name = module.params['record']
    record_type = module.params['type']
    ttl = module.params['ttl']
    record_data = module.params['record_data']
    data = dict(ttl=ttl, rrdatas=record_data)

    # Google Cloud DNS wants the trailing dot on all DNS names.
    if record_name[-1] != '.':
        record_name = record_name + '.'

    # If we found a record, we need to check if the values match.
    if record is not None:
        # If the record matches, we obviously don't have to change anything.
        if _records_match(record.data['ttl'], record.data['rrdatas'], ttl, record_data):
            return False

        # The record doesn't match, so we need to check if we can overwrite it.
        if not overwrite:
            module.fail_json(
                msg='cannot overwrite existing record, overwrite protection enabled',
                changed=False
            )

    # The record either doesn't exist, or it exists and we can overwrite it.
    if record is None and not module.check_mode:
        # There's no existing record, so we'll just create it.
        try:
            gcdns.create_record(record_name, zone, record_type, data)
        except InvalidRequestError as error:
            if error.code == 'invalid':
                # The resource record name and type are valid by themselves, but
                # not when combined (e.g., an 'A' record with "www.example.com"
                # as its value).
                module.fail_json(
                    msg='value is invalid for the given type: ' +
                    "%s, got value: %s" % (record_type, record_data),
                    changed=False
                )

            elif error.code == 'cnameResourceRecordSetConflict':
                # We're attempting to create a CNAME resource record when we
                # already have another type of resource record with the name
                # domain name.
                module.fail_json(
                    msg="non-CNAME resource record already exists: %s" % record_name,
                    changed=False
                )

            else:
                # The error is something else that we don't know how to handle,
                # so we'll just re-raise the exception.
                raise

    elif record is not None and not module.check_mode:
        # The Google provider in libcloud doesn't support updating a record in
        # place, so if the record already exists, we need to delete it and
        # recreate it using the new information.
        gcdns.delete_record(record)

        try:
            gcdns.create_record(record_name, zone, record_type, data)
        except InvalidRequestError:
            # Something blew up when creating the record. This will usually be a
            # result of invalid value data in the new record. Unfortunately, we
            # already changed the state of the record by deleting the old one,
            # so we'll try to roll back before failing out.
            try:
                gcdns.create_record(record.name, record.zone, record.type, record.data)
                module.fail_json(
                    msg='error updating record, the original record was restored',
                    changed=False
                )
            except LibcloudError:
                # We deleted the old record, couldn't create the new record, and
                # couldn't roll back. That really sucks. We'll dump the original
                # record to the failure output so the user can resore it if
                # necessary.
                module.fail_json(
                    msg='error updating record, and could not restore original record, ' +
                    "original name: %s " % record.name +
                    "original zone: %s " % record.zone +
                    "original type: %s " % record.type +
                    "original data: %s" % record.data,
                    changed=True)

    return True


def remove_record(module, gcdns, record):
    """Remove a resource record."""

    overwrite = module.boolean(module.params['overwrite'])
    ttl = module.params['ttl']
    record_data = module.params['record_data']

    # If there is no record, we're obviously done.
    if record is None:
        return False

    # If there is an existing record, do our values match the values of the
    # existing record?
    if not overwrite:
        if not _records_match(record.data['ttl'], record.data['rrdatas'], ttl, record_data):
            module.fail_json(
                msg='cannot delete due to non-matching ttl or record_data: ' +
                "ttl: %d, record_data: %s " % (ttl, record_data) +
                "original ttl: %d, original record_data: %s" % (record.data['ttl'], record.data['rrdatas']),
                changed=False
            )

    # If we got to this point, we're okay to delete the record.
    if not module.check_mode:
        gcdns.delete_record(record)

    return True


def _get_record(gcdns, zone, record_type, record_name):
    """Gets the record object for a given FQDN."""

    # The record ID is a combination of its type and FQDN. For example, the
    # ID of an A record for www.example.com would be 'A:www.example.com.'
    record_id = "%s:%s" % (record_type, record_name)

    try:
        return gcdns.get_record(zone.id, record_id)
    except RecordDoesNotExistError:
        return None


def _get_zone(gcdns, zone_name, zone_id):
    """Gets the zone object for a given domain name."""

    if zone_id is not None:
        try:
            return gcdns.get_zone(zone_id)
        except ZoneDoesNotExistError:
            return None

    # To create a zone, we need to supply a domain name. However, to delete a
    # zone, we need to supply a zone ID. Zone ID's are often based on domain
    # names, but that's not guaranteed, so we'll iterate through the list of
    # zones to see if we can find a matching domain name.
    available_zones = gcdns.iterate_zones()
    found_zone = None

    for zone in available_zones:
        if zone.domain == zone_name:
            found_zone = zone
            break

    return found_zone


def _records_match(old_ttl, old_record_data, new_ttl, new_record_data):
    """Checks to see if original and new TTL and values match."""

    matches = True

    if old_ttl != new_ttl:
        matches = False
    if old_record_data != new_record_data:
        matches = False

    return matches


def _sanity_check(module):
    """Run sanity checks that don't depend on info from the zone/record."""

    overwrite = module.params['overwrite']
    record_name = module.params['record']
    record_type = module.params['type']
    state = module.params['state']
    ttl = module.params['ttl']
    record_data = module.params['record_data']

    # Apache libcloud needs to be installed and at least the minimum version.
    if not HAS_LIBCLOUD:
        module.fail_json(
            msg='This module requires Apache libcloud %s or greater' % MINIMUM_LIBCLOUD_VERSION,
            changed=False
        )
    elif LooseVersion(LIBCLOUD_VERSION) < MINIMUM_LIBCLOUD_VERSION:
        module.fail_json(
            msg='This module requires Apache libcloud %s or greater' % MINIMUM_LIBCLOUD_VERSION,
            changed=False
        )

    # A negative TTL is not permitted (how would they even work?!).
    if ttl < 0:
        module.fail_json(
            msg='TTL cannot be less than zero, got: %d' % ttl,
            changed=False
        )

    # Deleting SOA records is not permitted.
    if record_type == 'SOA' and state == 'absent':
        module.fail_json(msg='cannot delete SOA records', changed=False)

    # Updating SOA records is not permitted.
    if record_type == 'SOA' and state == 'present' and overwrite:
        module.fail_json(msg='cannot update SOA records', changed=False)

    # Some sanity checks depend on what value was supplied.
    if record_data is not None and (state == 'present' or not overwrite):
        # A records must contain valid IPv4 addresses.
        if record_type == 'A':
            for value in record_data:
                try:
                    socket.inet_aton(value)
                except socket.error:
                    module.fail_json(
                        msg='invalid A record value, got: %s' % value,
                        changed=False
                    )

        # AAAA records must contain valid IPv6 addresses.
        if record_type == 'AAAA':
            for value in record_data:
                try:
                    socket.inet_pton(socket.AF_INET6, value)
                except socket.error:
                    module.fail_json(
                        msg='invalid AAAA record value, got: %s' % value,
                        changed=False
                    )

        # CNAME and SOA records can't have multiple values.
        if record_type in ['CNAME', 'SOA'] and len(record_data) > 1:
            module.fail_json(
                msg='CNAME or SOA records cannot have more than one value, ' +
                "got: %s" % record_data,
                changed=False
            )

        # Google Cloud DNS does not support wildcard NS records.
        if record_type == 'NS' and record_name[0] == '*':
            module.fail_json(
                msg="wildcard NS records not allowed, got: %s" % record_name,
                changed=False
            )

        # Values for txt records must begin and end with a double quote.
        if record_type == 'TXT':
            for value in record_data:
                if value[0] != '"' and value[-1] != '"':
                    module.fail_json(
                        msg='TXT record_data must be enclosed in double quotes, ' +
                        'got: %s' % value,
                        changed=False
                    )


def _additional_sanity_checks(module, zone):
    """Run input sanity checks that depend on info from the zone/record."""

    overwrite = module.params['overwrite']
    record_name = module.params['record']
    record_type = module.params['type']
    state = module.params['state']

    # CNAME records are not allowed to have the same name as the root domain.
    if record_type == 'CNAME' and record_name == zone.domain:
        module.fail_json(
            msg='CNAME records cannot match the zone name',
            changed=False
        )

    # The root domain must always have an NS record.
    if record_type == 'NS' and record_name == zone.domain and state == 'absent':
        module.fail_json(
            msg='cannot delete root NS records',
            changed=False
        )

    # Updating NS records with the name as the root domain is not allowed
    # because libcloud does not support in-place updates and root domain NS
    # records cannot be removed.
    if record_type == 'NS' and record_name == zone.domain and overwrite:
        module.fail_json(
            msg='cannot update existing root NS records',
            changed=False
        )

    # SOA records with names that don't match the root domain are not permitted
    # (and wouldn't make sense anyway).
    if record_type == 'SOA' and record_name != zone.domain:
        module.fail_json(
            msg='non-root SOA records are not permitted, got: %s' % record_name,
            changed=False
        )


################################################################################
# Main
################################################################################

def main():
    """Main function"""

    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent'], type='str'),
            record=dict(required=True, aliases=['name'], type='str'),
            zone=dict(type='str'),
            zone_id=dict(type='str'),
            type=dict(required=True, choices=SUPPORTED_RECORD_TYPES, type='str'),
            record_data=dict(aliases=['value'], type='list'),
            ttl=dict(default=300, type='int'),
            overwrite=dict(default=False, type='bool'),
            service_account_email=dict(type='str'),
            pem_file=dict(type='path'),
            credentials_file=dict(type='path'),
            project_id=dict(type='str')
        ),
        required_if=[
            ('state', 'present', ['record_data']),
            ('overwrite', False, ['record_data'])
        ],
        required_one_of=[['zone', 'zone_id']],
        supports_check_mode=True
    )

    _sanity_check(module)

    record_name = module.params['record']
    record_type = module.params['type']
    state = module.params['state']
    ttl = module.params['ttl']
    zone_name = module.params['zone']
    zone_id = module.params['zone_id']

    json_output = dict(
        state=state,
        record=record_name,
        zone=zone_name,
        zone_id=zone_id,
        type=record_type,
        record_data=module.params['record_data'],
        ttl=ttl,
        overwrite=module.boolean(module.params['overwrite'])
    )

    # Google Cloud DNS wants the trailing dot on all DNS names.
    if zone_name is not None and zone_name[-1] != '.':
        zone_name = zone_name + '.'
    if record_name[-1] != '.':
        record_name = record_name + '.'

    # Build a connection object that we can use to connect with Google Cloud
    # DNS.
    gcdns = gcdns_connect(module, provider=PROVIDER)

    # We need to check that the zone we're creating a record for actually
    # exists.
    zone = _get_zone(gcdns, zone_name, zone_id)
    if zone is None and zone_name is not None:
        module.fail_json(
            msg='zone name was not found: %s' % zone_name,
            changed=False
        )
    elif zone is None and zone_id is not None:
        module.fail_json(
            msg='zone id was not found: %s' % zone_id,
            changed=False
        )

    # Populate the returns with the actual zone information.
    json_output['zone'] = zone.domain
    json_output['zone_id'] = zone.id

    # We also need to check if the record we want to create or remove actually
    # exists.
    try:
        record = _get_record(gcdns, zone, record_type, record_name)
    except InvalidRequestError:
        # We gave Google Cloud DNS an invalid DNS record name.
        module.fail_json(
            msg='record name is invalid: %s' % record_name,
            changed=False
        )

    _additional_sanity_checks(module, zone)

    diff = dict()

    # Build the 'before' diff
    if record is None:
        diff['before'] = ''
        diff['before_header'] = '<absent>'
    else:
        diff['before'] = dict(
            record=record.data['name'],
            type=record.data['type'],
            record_data=record.data['rrdatas'],
            ttl=record.data['ttl']
        )
        diff['before_header'] = "%s:%s" % (record_type, record_name)

    # Create, remove, or modify the record.
    if state == 'present':
        diff['after'] = dict(
            record=record_name,
            type=record_type,
            record_data=module.params['record_data'],
            ttl=ttl
        )
        diff['after_header'] = "%s:%s" % (record_type, record_name)

        changed = create_record(module, gcdns, zone, record)

    elif state == 'absent':
        diff['after'] = ''
        diff['after_header'] = '<absent>'

        changed = remove_record(module, gcdns, record)

    module.exit_json(changed=changed, diff=diff, **json_output)


if __name__ == '__main__':
    main()
