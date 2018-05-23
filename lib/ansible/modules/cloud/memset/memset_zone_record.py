#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2018, Simon Weald <ansible@simonweald.com>
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
module: memset_zone_record
author: "Simon Weald (@analbeard)"
version_added: "2.6"
short_description: Create and delete records in Memset DNS zones.
notes:
  - Zones can be thought of as a logical group of domains, all of which share the
    same DNS records (i.e. they point to the same IP). An API key generated via the
    Memset customer control panel is needed with the following minimum scope -
    I(dns.zone_create), I(dns.zone_delete), I(dns.zone_list).
  - Currently this module can only create one DNS record at a time. Multiple records
    should be created using C(with_items).
description:
    - Manage DNS records in a Memset account.
options:
    state:
        default: present
        description:
            - Indicates desired state of resource.
        choices: [ absent, present ]
    api_key:
        required: true
        description:
            - The API key obtained from the Memset control panel.
    address:
        required: true
        description:
            - The address for this record (can be IP or text string depending on record type).
        aliases: [ ip, data ]
    priority:
        description:
            - C(SRV) and C(TXT) record priority, in the range 0 > 999 (inclusive).
    record:
        required: false
        description:
            - The subdomain to create.
    type:
        required: true
        description:
            - The type of DNS record to create.
        choices: [ A, AAAA, CNAME, MX, NS, SRV, TXT ]
    relative:
        type: bool
        description:
            - If set then the current domain is added onto the address field for C(CNAME), C(MX), C(NS)
              and C(SRV)record types.
    ttl:
        description:
            - The record's TTL in seconds (will inherit zone's TTL if not explicitly set). This must be a
              valid int from U(https://www.memset.com/apidocs/methods_dns.html#dns.zone_record_create).
        choices: [ 0, 300, 600, 900, 1800, 3600, 7200, 10800, 21600, 43200, 86400 ]
    zone:
        required: true
        description:
            - The name of the zone to which to add the record to.
'''

EXAMPLES = '''
# Create DNS record for www.domain.com
- name: create DNS record
  memset_zone_record:
    api_key: dcf089a2896940da9ffefb307ef49ccd
    state: present
    zone: domain.com
    type: A
    record: www
    address: 1.2.3.4
    ttl: 300
    relative: false
  delegate_to: localhost

# create an SPF record for domain.com
- name: create SPF record for domain.com
  memset_zone_record:
    api_key: dcf089a2896940da9ffefb307ef49ccd
    state: present
    zone: domain.com
    type: TXT
    address: "v=spf1 +a +mx +ip4:a1.2.3.4 ?all"
  delegate_to: localhost

# create multiple DNS records
- name: create multiple DNS records
  memset_zone_record:
    api_key: dcf089a2896940da9ffefb307ef49ccd
    zone: "{{ item.zone }}"
    type: "{{ item.type }}"
    record: "{{ item.record }}"
    address: "{{ item.address }}"
  delegate_to: localhost
  with_items:
    - { 'zone': 'domain1.com', 'type': 'A', 'record': 'www', 'address': '1.2.3.4' }
    - { 'zone': 'domain2.com', 'type': 'A', 'record': 'mail', 'address': '4.3.2.1' }
'''

RETURN = '''
memset_api:
  description: Record info from the Memset API.
  returned: when state == present
  type: complex
  contains:
    address:
      description: Record content (may be an IP, string or blank depending on record type).
      returned: always
      type: string
      sample: 1.1.1.1
    id:
      description: Record ID.
      returned: always
      type: string
      sample: "b0bb1ce851aeea6feeb2dc32fe83bf9c"
    priority:
      description: Priority for C(MX) and C(SRV) records.
      returned: always
      type: integer
      sample: 10
    record:
      description: Name of record.
      returned: always
      type: string
      sample: "www"
    relative:
      description: Adds the current domain onto the address field for C(CNAME), C(MX), C(NS) and C(SRV) types.
      returned: always
      type: boolean
      sample: False
    ttl:
      description: Record TTL.
      returned: always
      type: integer
      sample: 10
    type:
      description: Record type.
      returned: always
      type: string
      sample: AAAA
    zone_id:
      description: Zone ID.
      returned: always
      type: string
      sample: "b0bb1ce851aeea6feeb2dc32fe83bf9c"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.memset import get_zone_id
from ansible.module_utils.memset import memset_api_call
from ansible.module_utils.memset import get_zone_id


def api_validation(args=None):
    '''
    Perform some validation which will be enforced by Memset's API (see:
    https://www.memset.com/apidocs/methods_dns.html#dns.zone_record_create)
    '''
    failed_validation = False

    # priority can only be integer 0 > 999
    if not 0 <= args['priority'] <= 999:
        failed_validation = True
        error = 'Priority must be in the range 0 > 999 (inclusive).'
    # data value must be max 250 chars
    if len(args['address']) > 250:
        failed_validation = True
        error = "Address must be less than 250 characters in length."
    # record value must be max 250 chars
    if args['record']:
        if len(args['record']) > 63:
            failed_validation = True
            error = "Record must be less than 63 characters in length."
    # relative isn't used for all record types
    if args['relative']:
        if args['type'] not in ['CNAME', 'MX', 'NS', 'SRV']:
            failed_validation = True
            error = "Relative is only valid for CNAME, MX, NS and SRV record types."
    # if any of the above failed then fail early
    if failed_validation:
        module.fail_json(failed=True, msg=error)


def create_zone_record(args=None, zone_id=None, records=None, payload=None):
    '''
    Sanity checking has already occurred prior to this function being
    called, so we can go ahead and either create or update the record.
    As defaults are defined for all values in the argument_spec, this
    may cause some changes to occur as the defaults are enforced (if
    the user has only configured required variables).
    '''
    has_changed, has_failed = False, False
    msg, memset_api = None, None

    # assemble the new record.
    new_record = dict()
    new_record['zone_id'] = zone_id
    for arg in ['priority', 'address', 'relative', 'record', 'ttl', 'type']:
        new_record[arg] = args[arg]

    # if we have any matches, update them.
    if records:
        for zone_record in records:
            # record exists, add ID to payload.
            new_record['id'] = zone_record['id']
            if zone_record == new_record:
                # nothing to do; record is already correct so we populate
                # the return var with the existing record's details.
                memset_api = zone_record
                return(has_changed, has_failed, memset_api, msg)
            else:
                # merge dicts ensuring we change any updated values
                payload = zone_record.copy()
                payload.update(new_record)
                api_method = 'dns.zone_record_update'
                if args['check_mode']:
                    has_changed = True
                    # return the new record to the user in the returned var.
                    memset_api = new_record
                    return(has_changed, has_failed, memset_api, msg)
                has_failed, msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method, payload=payload)
                if not has_failed:
                    has_changed = True
                    memset_api = new_record
                    # empty msg as we don't want to return a boatload of json to the user.
                    msg = None
    else:
        # no record found, so we need to create it
        api_method = 'dns.zone_record_create'
        payload = new_record
        if args['check_mode']:
            has_changed = True
            # populate the return var with the new record's details.
            memset_api = new_record
            return(has_changed, has_failed, memset_api, msg)
        has_failed, msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method, payload=payload)
        if not has_failed:
            has_changed = True
            memset_api = new_record
            #  empty msg as we don't want to return a boatload of json to the user.
            msg = None

    return(has_changed, has_failed, memset_api, msg)


def delete_zone_record(args=None, records=None, payload=None):
    '''
    Matching records can be cleanly deleted without affecting other
    resource types, so this is pretty simple to achieve.
    '''
    has_changed, has_failed = False, False
    msg, memset_api = None, None

    # if we have any matches, delete them.
    if records:
        for zone_record in records:
            if args['check_mode']:
                has_changed = True
                return(has_changed, has_failed, memset_api, msg)
            payload['id'] = zone_record['id']
            api_method = 'dns.zone_record_delete'
            has_failed, msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method, payload=payload)
            if not has_failed:
                has_changed = True
                memset_api = zone_record
                #  empty msg as we don't want to return a boatload of json to the user.
                msg = None

    return(has_changed, has_failed, memset_api, msg)


def create_or_delete(args=None):
    '''
    We need to perform some initial sanity checking and also look
    up required info before handing it off to create or delete functions.
    Check mode is integrated into the create or delete functions.
    '''
    has_failed, has_changed = False, False
    msg, memset_api, stderr = None, None, None
    retvals, payload = dict(), dict()

    # get the zones and check if the relevant zone exists.
    api_method = 'dns.zone_list'
    _has_failed, msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method)

    if _has_failed:
        # this is the first time the API is called; incorrect credentials will
        # manifest themselves at this point so we need to ensure the user is
        # informed of the reason.
        retvals['failed'] = _has_failed
        retvals['msg'] = msg
        retvals['stderr'] = "API returned an error: {0}" . format(response.status_code)
        return(retvals)

    zone_exists, _msg, counter, zone_id = get_zone_id(zone_name=args['zone'], current_zones=response.json())

    if not zone_exists:
        has_failed = True
        if counter == 0:
            stderr = "DNS zone {0} does not exist." . format(args['zone'])
        elif counter > 1:
            stderr = "{0} matches multiple zones." . format(args['zone'])
        retvals['failed'] = has_failed
        retvals['msg'] = stderr
        retvals['stderr'] = stderr
        return(retvals)

    # get a list of all records ( as we can't limit records by zone)
    api_method = 'dns.zone_record_list'
    _has_failed, _msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method)

    # find any matching records
    records = [record for record in response.json() if record['zone_id'] == zone_id
               and record['record'] == args['record'] and record['type'] == args['type']]

    if args['state'] == 'present':
        has_changed, has_failed, memset_api, msg = create_zone_record(args=args, zone_id=zone_id, records=records, payload=payload)

    if args['state'] == 'absent':
        has_changed, has_failed, memset_api, msg = delete_zone_record(args=args, records=records, payload=payload)

    retvals['changed'] = has_changed
    retvals['failed'] = has_failed
    for val in ['msg', 'stderr', 'memset_api']:
        if val is not None:
            retvals[val] = eval(val)

    return(retvals)


def main():
    global module
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(required=False, default='present', choices=['present', 'absent'], type='str'),
            api_key=dict(required=True, type='str', no_log=True),
            zone=dict(required=True, type='str'),
            type=dict(required=True, choices=['A', 'AAAA', 'CNAME', 'MX', 'NS', 'SRV', 'TXT'], type='str'),
            address=dict(required=True, aliases=['ip', 'data'], type='str'),
            record=dict(required=False, default='', type='str'),
            ttl=dict(required=False, default=0, choices=[0, 300, 600, 900, 1800, 3600, 7200, 10800, 21600, 43200, 86400], type='int'),
            priority=dict(required=False, default=0, type='int'),
            relative=dict(required=False, default=False, type='bool')
        ),
        supports_check_mode=True
    )

    # populate the dict with the user-provided vars.
    args = dict()
    for key, arg in module.params.items():
        args[key] = arg
    args['check_mode'] = module.check_mode

    # perform some Memset API-specific validation
    api_validation(args=args)

    retvals = create_or_delete(args)

    if retvals['failed']:
        module.fail_json(**retvals)
    else:
        module.exit_json(**retvals)


if __name__ == '__main__':
    main()
