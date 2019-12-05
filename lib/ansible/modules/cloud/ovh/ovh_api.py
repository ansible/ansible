#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Francois Lallart (@fraff)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = '''
---
module: ovh_api
version_added: "2.10"
author: Francois Lallart (@fraff)
short_description: Minimalist wrapper around OVH api and ovh python module
description:
    - Minimalist wrapper around OVH api and ovh python module.
    - See U(https://api.ovh.com/console) for more informations.
notes:
    - This module is not idempotent and should only be used if no other module implement your will.
requirements: [ "ovh" ]
options:
    path:
        required: true
        type: str
        description:
            - https://api.ovh.com/console/{path} don't forget to replace / with '%2f'.
    method:
        type: str
        choices: ['GET', 'POST', 'PUT', 'DELETE']
        default: 'GET'
        aliases: ['action']
        description:
            - What method to use (case sensitive).
    body:
        type: dict
        default:
        aliases: ['data']
        description:
            - Use this body if required.
    skip_get:
        type: bool
        default: False
        description:
            - Do not perform GET before and after PUT or DELETE to detect changes.
    endpoint:
        type: str
        description:
            - The endpoint to use (for instance ovh-eu).
    application_key:
        type: str
        description:
            - The applicationKey to use.
    application_secret:
        type: str
        description:
            - The application secret to use.
    consumer_key:
        type: str
        description:
            - The consumer key to use.
'''

EXAMPLES = '''
# basic
- ovh_api:
    path: "/cloud/project"

# get info about yourself
- ovh_api:
    path: "/me"

# change reverse dns of ip y.y.y.y from block x.x.x.x/29
- ovh_api:
    path: "/ip/x.x.x.x%2f29/reverse"
    method: "POST"
    body: {'ipReverse': 'y.y.y.y', reverse: 'my.cool.reverse'}
'''

RETURN = '''
'''

import os
import sys
import traceback

try:
    import ovh
    import ovh.exceptions
    from ovh.exceptions import APIError
    HAS_OVH = True
except ImportError:
    HAS_OVH = False
    OVH_IMPORT_ERROR = traceback.format_exc()

from ansible.module_utils.basic import AnsibleModule


def ordered(obj):
    if isinstance(obj, dict):
        return sorted((k, ordered(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return sorted(ordered(x) for x in obj)
    else:
        return obj


def main():
    module = AnsibleModule(
        argument_spec=dict(
            path=dict(required=True),
            method=dict(required=False, default='GET', choices=['GET', 'POST', 'PUT', 'DELETE'], aliases=['action']),
            body=dict(required=False, default={}, type='dict', aliases=['data']),
            skip_get=dict(type='bool', required=False, default=False),
            endpoint=dict(required=False),
            application_key=dict(required=False, no_log=True),
            application_secret=dict(required=False, no_log=True),
            consumer_key=dict(required=False, no_log=True),
        ),
        supports_check_mode=False
    )

    if not HAS_OVH:
        module.fail_json(msg='python-ovh is required to run this module, see https://github.com/ovh/python-ovh')

    # Get parameters
    path = module.params.get('path')
    method = module.params.get('method').lower()
    body = module.params.get('body')
    skip_get = module.params.get('skip_get')
    endpoint = module.params.get('endpoint')
    application_key = module.params.get('application_key')
    application_secret = module.params.get('application_secret')
    consumer_key = module.params.get('consumer_key')
    additional_warn_msg = ''
    changed = False

    # Connect to OVH API
    client = ovh.Client(
        endpoint=endpoint,
        application_key=application_key,
        application_secret=application_secret,
        consumer_key=consumer_key
    )

    mydict = {
        'func': {'get': client.get, 'put': client.put, 'post': client.post, 'delete': client.delete},
        'changed': {'get': False, 'put': None, 'post': True, 'delete': None}
    }

    try:
        # OVH API does not always report change on PUT and DELETE
        if method in ['put', 'delete']:
            # Then we have to perform a GET before and after to detect some change
            # except if skip_get parameter is set to True
            if skip_get is False:
                old = mydict['func']['get'](path, **body)

            result = mydict['func'][method](path, **body)

            if skip_get is False:
                new = mydict['func']['get'](path, **body)
                changed = (ordered(old) != ordered(new))
                if result is None:
                    result = new

            module.exit_json(changed=changed, result=result)

        # GET always returns changed=False if no error, and POST always returns changed=True if no error.
        else:
            result = mydict['func'][method](path, **body)
            module.exit_json(changed=mydict['changed'][method], result=result)

    except APIError as apiError:
        if str(apiError).endswith("does not answer to the GET HTTP method"):
            additional_warn_msg = " (You can use 'skip_get' parameter to skip GET, this will always return change=False)"
        module.fail_json(changed=False, msg="OVH API Error: {0}{1}".format(apiError, additional_warn_msg))

    # We should never reach here
    module.fail_json(msg='Internal ovh_api module error')


if __name__ == "__main__":
    main()
