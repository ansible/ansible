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
module: memset_memstore_info
author: "Simon Weald (@glitchcrab)"
version_added: "2.8"
short_description: Retrieve Memstore product usage information.
notes:
    - An API key generated via the Memset customer control panel is needed with the
      following minimum scope - I(memstore.usage).
description:
    - Retrieve Memstore product usage information.
    - This module was called C(memset_memstore_facts) before Ansible 2.9. The usage did not change.
options:
    api_key:
        required: true
        description:
            - The API key obtained from the Memset control panel.
    name:
        required: true
        description:
            - The Memstore product name (i.e. C(mstestyaa1)).
'''

EXAMPLES = '''
- name: get usage for mstestyaa1
  memset_memstore_info:
    name: mstestyaa1
    api_key: 5eb86c9896ab03919abcf03857163741
  delegate_to: localhost
'''

RETURN = '''
---
memset_api:
  description: Info from the Memset API
  returned: always
  type: complex
  contains:
    cdn_bandwidth:
      description: Dictionary of CDN bandwidth facts
      returned: always
      type: complex
      contains:
        bytes_out:
          description: Outbound CDN bandwidth for the last 24 hours in bytes
          returned: always
          type: int
          sample: 1000
        requests:
          description: Number of requests in the last 24 hours
          returned: always
          type: int
          sample: 10
        bytes_in:
          description: Inbound CDN bandwidth for the last 24 hours in bytes
          returned: always
          type: int
          sample: 1000
    containers:
      description: Number of containers
      returned: always
      type: int
      sample: 10
    bytes:
      description: Space used in bytes
      returned: always
      type: int
      sample: 3860997965
    objs:
      description: Number of objects
      returned: always
      type: int
      sample: 1000
    bandwidth:
      description: Dictionary of CDN bandwidth facts
      returned: always
      type: complex
      contains:
        bytes_out:
          description: Outbound bandwidth for the last 24 hours in bytes
          returned: always
          type: int
          sample: 1000
        requests:
          description: Number of requests in the last 24 hours
          returned: always
          type: int
          sample: 10
        bytes_in:
          description: Inbound bandwidth for the last 24 hours in bytes
          returned: always
          type: int
          sample: 1000
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.memset import memset_api_call


def get_facts(args=None):
    '''
    Performs a simple API call and returns a JSON blob.
    '''
    retvals, payload = dict(), dict()
    has_changed, has_failed = False, False
    msg, stderr, memset_api = None, None, None

    payload['name'] = args['name']

    api_method = 'memstore.usage'
    has_failed, msg, response = memset_api_call(api_key=args['api_key'], api_method=api_method, payload=payload)

    if has_failed:
        # this is the first time the API is called; incorrect credentials will
        # manifest themselves at this point so we need to ensure the user is
        # informed of the reason.
        retvals['failed'] = has_failed
        retvals['msg'] = msg
        retvals['stderr'] = "API returned an error: {0}" . format(response.status_code)
        return(retvals)

    # we don't want to return the same thing twice
    msg = None
    memset_api = response.json()

    retvals['changed'] = has_changed
    retvals['failed'] = has_failed
    for val in ['msg', 'memset_api']:
        if val is not None:
            retvals[val] = eval(val)

    return(retvals)


def main():
    global module
    module = AnsibleModule(
        argument_spec=dict(
            api_key=dict(required=True, type='str', no_log=True),
            name=dict(required=True, type='str')
        ),
        supports_check_mode=False
    )
    if module._name == 'memset_memstore_facts':
        module.deprecate("The 'memset_memstore_facts' module has been renamed to 'memset_memstore_info'", version='2.13')

    # populate the dict with the user-provided vars.
    args = dict()
    for key, arg in module.params.items():
        args[key] = arg

    retvals = get_facts(args)

    if retvals['failed']:
        module.fail_json(**retvals)
    else:
        module.exit_json(**retvals)


if __name__ == '__main__':
    main()
