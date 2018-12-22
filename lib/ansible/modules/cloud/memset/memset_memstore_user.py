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
        description:
            - Whether the user is enabled or disabled. Defaults to false for security.
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
        errors['username'] = "Username can only contain numbers, letters, dots, dashes and underscores, and can’t start with a dot. Must be 50 chars or less."

    if len(errors) > 0:
        module.fail_json(failed=True, msg=errors)


def create(args=None, payload=None):
    '''
    Creates or updates a user.
    '''
    retvals, payload = dict(), dict()
    retvals['changed'], retvals['failed'] = False, False

    return(retvals)


def delete(args=None, payload=None):
    '''
    Deletes a user.
    '''
    retvals, payload = dict(), dict()
    retvals['changed'], retvals['failed'] = False, False

    return(retvals)


def create_or_delete(args=None):
    '''
    Performs initial auth validation and gets a list of
    existing services to provide to create/delete functions.
    '''
    retvals, payload = dict(), dict()
    retvals['changed'], retvals['failed'] = False, False

    return(retvals)


def main():
    global module
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(required=False, default='present', choices=['present', 'absent'], type='str'),
            api_key=dict(required=True, type='str', no_log=True),
            username=dict(required=True, aliases=['name'], type='str'),
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

    create_or_delete()

    if failed:
        module.fail_json(**retvals)
    else:
        module.exit_json(**retvals)


if __name__ == '__main__':
    main()
