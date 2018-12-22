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
module: memset_memstore_user
author: "Simon Weald (@glitchcrab)"
version_added: "2.8"
short_description: Manage Memstore users.
notes:
  - Create/delete and manage the status of Memstore users.
  - An API key generated via the Memset customer control panel is needed with
    the following minimum scope - I(memset.user_list), I(memstore.user_info),
    I(memstore.user_enable), I(memstore.user_disable), I(memstore.user_delete),
    I(memstore.user_create).
description:
    - Create/delete and manage the status of Memstore users.
options:
    state:
        required: true
        default: present
        description:
            - Indicates desired state of resource.
        choices: [ absent, present ]
    api_key:
        required: true
        description:
            - The API key obtained from the Memset control panel.
    username:
        required: true
        description:
            - The name of the user to manage.
    memstore:
        required: true
        description:
            - The Memstore product the user belongs in.
    enabled:
        required: false
        default: false
        type: bool
        description:
            - Whether the user is enabled or disabled. Defaults to false for security.
    password:
        required: true
        description:
            - A password for the user.
'''

EXAMPLES = '''
# Create the 'test' and enable them.
- name: create memstore user
  memset_memstore_user:
    username: test
    memstore: mstestyaa1
    enabled: true
    state: present
    api_key: 5eb86c9196ab03919abcf03857163741
  delegate_to: localhost
'''

RETURN = '''
---
memset_api:
  description: Info from the Memset API
  returned: when changed or state == present
  type: complex
  contains:
    admin:
      description: Whether the user is an admin.
      returned: always
      type: bool
      sample: False
    enabled:
      description: Whether the user is enabled.
      returned: always
      type: bool
      sample: False
    username:
      description: The username.
      returned: always
      type: string
      sample: 'test'
'''

import re
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.memset import memset_api_call


def api_validation(args=None):
    '''
    Perform some validation which will be enforced by Memset's API (see:
    https://www.memset.com/apidocs/methods_memstore.user.html)
    '''
    username_re = r'^[a-z0-9-\_]{1}[a-z0-9-\.\_]{1,49}$'
    errors = dict()

    if not re.match(username_re, args['username'].lower()):
        errors['username'] = "Username can only contain numbers, letters, dots, dashes and underscores, and can't start with a dot. Must be 50 chars or less."

    if len(errors) > 0:
        module.fail_json(failed=True, msg=errors)


def create_user(args=None, user=None):
    '''
    Creates or updates a user.
    '''
    retvals, payload = dict(), dict()
    retvals['changed'], retvals['failed'] = False, False

    if not user:
        # user doesn't exist, create it.
        payload['name'], payload['username'], payload['password'], payload['enabled'] = \
            args['memstore'], args['username'], args['password'], args['enabled']
        if args['check_mode']:
            retvals['changed'] = True
            retvals['memset_api'] = payload
            return(retvals)
        # create the user
        api_method = 'memstore.user.create'
        retvals['failed'], msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method, payload=payload)

        if retvals['failed']:
            retvals['msg'] = msg
        else:
            retvals['changed'] = True
            retvals['memset_api'] = response.json()
    else:
        # User exists, update it. The only change possible is to enable/disable the user.
        if user['enabled'] != args['enabled']:
            if args['check_mode']:
                retvals['changed'] = True
                retvals['diff'] = "enabled: {0}" . format(args['enabled'])
                return(retvals)

            payload['name'], payload['username'] = args['memstore'], args['username']

            if args['enabled']:
                api_method = 'memstore.user.enable'
            else:
                api_method = 'memstore.user.disable'

            retvals['failed'], msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method, payload=payload)

            if retvals['failed']:
                retvals['msg'] = msg
            else:
                retvals['changed'] = True
                payload['enabled'] = args['enabled']
                retvals['memset_api'] = payload

    return(retvals)


def delete_user(args=None, user=None):
    '''
    Deletes a user.
    '''
    retvals, payload = dict(), dict()
    retvals['changed'], retvals['failed'] = False, False

    if user:
        if args['check_mode']:
            retvals['changed'] = True
            return(retvals)
        payload['name'] = args['memstore']
        payload['username'] = args['username']
        api_method = 'memstore.user.delete'
        retvals['failed'], msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method, payload=payload)

        if retvals['failed']:
            retvals['msg'] = msg
        else:
            retvals['changed'] = True

    return(retvals)


def create_or_delete_user(args=None):
    '''
    Performs initial auth validation and gets a list of
    existing services to provide to create/delete functions.
    '''
    retvals, payload = dict(), dict()
    retvals['changed'], retvals['failed'] = False, False

    payload['name'] = args['memstore']
    api_method = 'memstore.user.list'
    has_failed, msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method, payload=payload)

    if has_failed:
        # this is the first time the API is called; incorrect credentials will
        # manifest themselves at this point so we need to ensure the user is
        # informed of the reason.
        retvals['failed'] = has_failed
        retvals['msg'] = msg
        return(retvals)

    currentuser = None
    for user in response.json():
        if user['username'] == args['username']:
            currentuser = user
            break

    if args['state'] == 'present':
        retvals = create_user(args=args, user=currentuser)
    if args['state'] == 'absent':
        retvals = delete_user(args=args, user=currentuser)

    return(retvals)


def main():
    global module
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(required=False, default='present', choices=['present', 'absent'], type='str'),
            api_key=dict(required=True, type='str', no_log=True),
            username=dict(required=True, aliases=['username'], type='str'),
            password=dict(required=True, type='str', no_log=True),
            memstore=dict(required=True, type='str'),
            enabled=dict(required=False, default=False, type='bool')
        ),
        supports_check_mode=True
    )

    # populate the dict with the user-provided vars.
    args = dict()
    for key, arg in module.params.items():
        args[key] = arg
    args['check_mode'] = module.check_mode

    api_validation(args)

    retvals = create_or_delete_user(args)

    if retvals['failed']:
        module.fail_json(**retvals)
    else:
        module.exit_json(**retvals)


if __name__ == '__main__':
    main()
