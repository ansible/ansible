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
module: memset_zone_domain
author: "Simon Weald (@glitchcrab)"
version_added: "2.6"
short_description: Create and delete domains in Memset DNS zones.
notes:
  - Zone domains can be thought of as a collection of domains, all of which share the
    same DNS records (i.e. they point to the same IP). An API key generated via the
    Memset customer control panel is needed with the following minimum scope -
    I(dns.zone_domain_create), I(dns.zone_domain_delete), I(dns.zone_domain_list).
  - Currently this module can only create one domain at a time. Multiple domains should
    be created using C(with_items).
description:
    - Manage DNS zone domains in a Memset account.
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
    domain:
        required: true
        description:
            - The zone domain name. Ensure this value has at most 250 characters.
        aliases: ['name']
    zone:
        required: true
        description:
            - The zone to add the domain to (this must already exist).
'''

EXAMPLES = '''
# Create the zone domain 'test.com'
- name: create zone domain
  memset_zone_domain:
    domain: test.com
    zone: testzone
    state: present
    api_key: 5eb86c9196ab03919abcf03857163741
  delegate_to: localhost
'''

RETURN = '''
memset_api:
  description: Domain info from the Memset API
  returned: when changed or state == present
  type: complex
  contains:
    domain:
      description: Domain name
      returned: always
      type: str
      sample: "example.com"
    id:
      description: Domain ID
      returned: always
      type: str
      sample: "b0bb1ce851aeea6feeb2dc32fe83bf9c"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.memset import get_zone_id
from ansible.module_utils.memset import check_zone_domain
from ansible.module_utils.memset import memset_api_call


def api_validation(args=None):
    '''
    Perform some validation which will be enforced by Memset's API (see:
    https://www.memset.com/apidocs/methods_dns.html#dns.zone_domain_create)
    '''
    # zone domain length must be less than 250 chars
    if len(args['domain']) > 250:
        stderr = 'Zone domain must be less than 250 characters in length.'
        module.fail_json(failed=True, msg=stderr)


def check(args=None):
    '''
    Support for running with check mode.
    '''
    retvals = dict()
    has_changed = False

    api_method = 'dns.zone_domain_list'
    has_failed, msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method)

    domain_exists = check_zone_domain(data=response, domain=args['domain'])

    # set changed to true if the operation would cause a change.
    has_changed = ((domain_exists and args['state'] == 'absent') or (not domain_exists and args['state'] == 'present'))

    retvals['changed'] = has_changed
    retvals['failed'] = has_failed

    return(retvals)


def create_zone_domain(args=None, zone_exists=None, zone_id=None, payload=None):
    '''
    At this point we already know whether the containing zone exists,
    so we just need to create the domain (or exit if it already exists).
    '''
    has_changed, has_failed = False, False
    msg = None

    api_method = 'dns.zone_domain_list'
    _has_failed, _msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method)

    for zone_domain in response.json():
        if zone_domain['domain'] == args['domain']:
            # zone domain already exists, nothing to change.
            has_changed = False
            break
    else:
        # we need to create the domain
        api_method = 'dns.zone_domain_create'
        payload['domain'] = args['domain']
        payload['zone_id'] = zone_id
        has_failed, msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method, payload=payload)
        if not has_failed:
            has_changed = True

    return(has_failed, has_changed, msg)


def delete_zone_domain(args=None, payload=None):
    '''
    Deletion is pretty simple, domains are always unique so we
    we don't need to do any sanity checking to avoid deleting the
    wrong thing.
    '''
    has_changed, has_failed = False, False
    msg, memset_api = None, None

    api_method = 'dns.zone_domain_list'
    _has_failed, _msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method)

    domain_exists = check_zone_domain(data=response, domain=args['domain'])

    if domain_exists:
        api_method = 'dns.zone_domain_delete'
        payload['domain'] = args['domain']
        has_failed, msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method, payload=payload)
        if not has_failed:
            has_changed = True
            memset_api = response.json()
            # unset msg as we don't want to return unnecessary info to the user.
            msg = None

    return(has_failed, has_changed, memset_api, msg)


def create_or_delete_domain(args=None):
    '''
    We need to perform some initial sanity checking and also look
    up required info before handing it off to create or delete.
    '''
    retvals, payload = dict(), dict()
    has_changed, has_failed = False, False
    msg, stderr, memset_api = None, None, None

    # get the zones and check if the relevant zone exists.
    api_method = 'dns.zone_list'
    has_failed, msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method)

    if has_failed:
        # this is the first time the API is called; incorrect credentials will
        # manifest themselves at this point so we need to ensure the user is
        # informed of the reason.
        retvals['failed'] = has_failed
        retvals['msg'] = msg
        retvals['stderr'] = "API returned an error: {0}" . format(response.status_code)
        return(retvals)

    zone_exists, msg, counter, zone_id = get_zone_id(zone_name=args['zone'], current_zones=response.json())

    if not zone_exists:
        # the zone needs to be unique - this isn't a requirement of Memset's API but it
        # makes sense in the context of this module.
        has_failed = True
        if counter == 0:
            stderr = "DNS zone '{0}' does not exist, cannot create domain." . format(args['zone'])
        elif counter > 1:
            stderr = "{0} matches multiple zones, cannot create domain." . format(args['zone'])

        retvals['failed'] = has_failed
        retvals['msg'] = stderr
        return(retvals)

    if args['state'] == 'present':
        has_failed, has_changed, msg = create_zone_domain(args=args, zone_exists=zone_exists, zone_id=zone_id, payload=payload)

    if args['state'] == 'absent':
        has_failed, has_changed, memset_api, msg = delete_zone_domain(args=args, payload=payload)

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
            state=dict(default='present', choices=['present', 'absent'], type='str'),
            api_key=dict(required=True, type='str', no_log=True),
            domain=dict(required=True, aliases=['name'], type='str'),
            zone=dict(required=True, type='str')
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
        retvals = create_or_delete_domain(args)

    # we would need to populate the return values with the API's response
    # in several places so it's easier to do it at the end instead.
    if not retvals['failed']:
        if args['state'] == 'present' and not module.check_mode:
            payload = dict()
            payload['domain'] = args['domain']
            api_method = 'dns.zone_domain_info'
            _has_failed, _msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method, payload=payload)
            retvals['memset_api'] = response.json()

    if retvals['failed']:
        module.fail_json(**retvals)
    else:
        module.exit_json(**retvals)


if __name__ == '__main__':
    main()
