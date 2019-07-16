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
module: memset_zone
author: "Simon Weald (@glitchcrab)"
version_added: "2.6"
short_description: Creates and deletes Memset DNS zones.
notes:
  - Zones can be thought of as a logical group of domains, all of which share the
    same DNS records (i.e. they point to the same IP). An API key generated via the
    Memset customer control panel is needed with the following minimum scope -
    I(dns.zone_create), I(dns.zone_delete), I(dns.zone_list).
description:
    - Manage DNS zones in a Memset account.
options:
    state:
        required: true
        description:
            - Indicates desired state of resource.
        choices: [ absent, present ]
    api_key:
        required: true
        description:
            - The API key obtained from the Memset control panel.
    name:
        required: true
        description:
            - The zone nickname; usually the same as the main domain. Ensure this
              value has at most 250 characters.
        aliases: [ nickname ]
    ttl:
        description:
            - The default TTL for all records created in the zone. This must be a
              valid int from U(https://www.memset.com/apidocs/methods_dns.html#dns.zone_create).
        choices: [ 0, 300, 600, 900, 1800, 3600, 7200, 10800, 21600, 43200, 86400 ]
    force:
        required: false
        default: false
        type: bool
        description:
            - Forces deletion of a zone and all zone domains/zone records it contains.
'''

EXAMPLES = '''
# Create the zone 'test'
- name: create zone
  memset_zone:
    name: test
    state: present
    api_key: 5eb86c9196ab03919abcf03857163741
    ttl: 300
  delegate_to: localhost

# Force zone deletion
- name: force delete zone
  memset_zone:
    name: test
    state: absent
    api_key: 5eb86c9196ab03919abcf03857163741
    force: true
  delegate_to: localhost
'''

RETURN = '''
memset_api:
  description: Zone info from the Memset API
  returned: when state == present
  type: complex
  contains:
    domains:
      description: List of domains in this zone
      returned: always
      type: list
      sample: []
    id:
      description: Zone id
      returned: always
      type: str
      sample: "b0bb1ce851aeea6feeb2dc32fe83bf9c"
    nickname:
      description: Zone name
      returned: always
      type: str
      sample: "example.com"
    records:
      description: List of DNS records for domains in this zone
      returned: always
      type: list
      sample: []
    ttl:
      description: Default TTL for domains in this zone
      returned: always
      type: int
      sample: 300
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.memset import check_zone
from ansible.module_utils.memset import get_zone_id
from ansible.module_utils.memset import memset_api_call


def api_validation(args=None):
    '''
    Perform some validation which will be enforced by Memset's API (see:
    https://www.memset.com/apidocs/methods_dns.html#dns.zone_record_create)
    '''
    # zone domain length must be less than 250 chars.
    if len(args['name']) > 250:
        stderr = 'Zone name must be less than 250 characters in length.'
        module.fail_json(failed=True, msg=stderr, stderr=stderr)


def check(args=None):
    '''
    Support for running with check mode.
    '''
    retvals = dict()

    api_method = 'dns.zone_list'
    has_failed, _msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method)

    zone_exists, counter = check_zone(data=response, name=args['name'])

    # set changed to true if the operation would cause a change.
    has_changed = ((zone_exists and args['state'] == 'absent') or (not zone_exists and args['state'] == 'present'))

    retvals['changed'] = has_changed
    retvals['failed'] = has_failed

    return(retvals)


def create_zone(args=None, zone_exists=None, payload=None):
    '''
    At this point we already know whether the zone exists, so we
    just need to make the API reflect the desired state.
    '''
    has_changed, has_failed = False, False
    msg, memset_api = None, None

    if not zone_exists:
        payload['ttl'] = args['ttl']
        payload['nickname'] = args['name']
        api_method = 'dns.zone_create'
        has_failed, msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method, payload=payload)
        if not has_failed:
            has_changed = True
    else:
        api_method = 'dns.zone_list'
        _has_failed, _msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method)
        for zone in response.json():
            if zone['nickname'] == args['name']:
                break
        if zone['ttl'] != args['ttl']:
            # update the zone if the desired TTL is different.
            payload['id'] = zone['id']
            payload['ttl'] = args['ttl']
            api_method = 'dns.zone_update'
            has_failed, msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method, payload=payload)
            if not has_failed:
                has_changed = True

    # populate return var with zone info.
    api_method = 'dns.zone_list'
    _has_failed, _msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method)

    zone_exists, msg, counter, zone_id = get_zone_id(zone_name=args['name'], current_zones=response.json())

    if zone_exists:
        payload = dict()
        payload['id'] = zone_id
        api_method = 'dns.zone_info'
        _has_failed, _msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method, payload=payload)
        memset_api = response.json()

    return(has_failed, has_changed, memset_api, msg)


def delete_zone(args=None, zone_exists=None, payload=None):
    '''
    Deletion requires extra sanity checking as the zone cannot be
    deleted if it contains domains or records. Setting force=true
    will override this behaviour.
    '''
    has_changed, has_failed = False, False
    msg, memset_api = None, None

    if zone_exists:
        api_method = 'dns.zone_list'
        _has_failed, _msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method, payload=payload)
        counter = 0
        for zone in response.json():
            if zone['nickname'] == args['name']:
                counter += 1
        if counter == 1:
            for zone in response.json():
                if zone['nickname'] == args['name']:
                    zone_id = zone['id']
                    domain_count = len(zone['domains'])
                    record_count = len(zone['records'])
            if (domain_count > 0 or record_count > 0) and args['force'] is False:
                # we need to fail out if force was not explicitly set.
                stderr = 'Zone contains domains or records and force was not used.'
                has_failed = True
                has_changed = False
                module.fail_json(failed=has_failed, changed=has_changed, msg=msg, stderr=stderr, rc=1)
            api_method = 'dns.zone_delete'
            payload['id'] = zone_id
            has_failed, msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method, payload=payload)
            if not has_failed:
                has_changed = True
                # return raw JSON from API in named var and then unset msg var so we aren't returning the same thing twice.
                memset_api = msg
                msg = None
        else:
            # zone names are not unique, so we cannot safely delete the requested
            # zone at this time.
            has_failed = True
            has_changed = False
            msg = 'Unable to delete zone as multiple zones with the same name exist.'
    else:
        has_failed, has_changed = False, False

    return(has_failed, has_changed, memset_api, msg)


def create_or_delete(args=None):
    '''
    We need to perform some initial sanity checking and also look
    up required info before handing it off to create or delete.
    '''
    retvals, payload = dict(), dict()
    has_failed, has_changed = False, False
    msg, memset_api, stderr = None, None, None

    # get the zones and check if the relevant zone exists.
    api_method = 'dns.zone_list'
    _has_failed, _msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method)
    if _has_failed:
        # this is the first time the API is called; incorrect credentials will
        # manifest themselves at this point so we need to ensure the user is
        # informed of the reason.
        retvals['failed'] = _has_failed
        retvals['msg'] = _msg

        return(retvals)

    zone_exists, _msg, counter, _zone_id = get_zone_id(zone_name=args['name'], current_zones=response.json())

    if args['state'] == 'present':
        has_failed, has_changed, memset_api, msg = create_zone(args=args, zone_exists=zone_exists, payload=payload)

    elif args['state'] == 'absent':
        has_failed, has_changed, memset_api, msg = delete_zone(args=args, zone_exists=zone_exists, payload=payload)

    retvals['failed'] = has_failed
    retvals['changed'] = has_changed
    for val in ['msg', 'stderr', 'memset_api']:
        if val is not None:
            retvals[val] = eval(val)

    return(retvals)


def main():
    global module
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(required=True, choices=['present', 'absent'], type='str'),
            api_key=dict(required=True, type='str', no_log=True),
            name=dict(required=True, aliases=['nickname'], type='str'),
            ttl=dict(required=False, default=0, choices=[0, 300, 600, 900, 1800, 3600, 7200, 10800, 21600, 43200, 86400], type='int'),
            force=dict(required=False, default=False, type='bool')
        ),
        supports_check_mode=True
    )

    # populate the dict with the user-provided vars.
    args = dict()
    for key, arg in module.params.items():
        args[key] = arg
    args['check_mode'] = module.check_mode

    # validate some API-specific limitations.
    api_validation(args=args)

    if module.check_mode:
        retvals = check(args)
    else:
        retvals = create_or_delete(args)

    if retvals['failed']:
        module.fail_json(**retvals)
    else:
        module.exit_json(**retvals)


if __name__ == '__main__':
    main()
