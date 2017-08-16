#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Stefan Midjich <swehack at gmail dot com>
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
module: xmlrpc_client

short_description: Run XMLRPC commands

version_added: "2.4"

description:
    - This module lets you establish an XMLRPC session and call any method
      by its xmlrpc path. On dry run this module will only establish API
      connection and check if your method exists in the method list but not
      call it.

options:
    url:
        description:
            - The API URL you connect to.
        required: true
    path:
        description:
            - The RPC path/method you are calling.
        required: true
    args:
        description:
            - A list of arguments for the RPC call. Placed first in any RPC call.
    kwargs:
        description:
            - A dictionary of arguments for the RPC call. Comes after the args list.

author:
    - Stefan Midjich (@stemid)
'''

EXAMPLES = '''
---

vars:
  api_url: https://api.localhost:9002

tasks:
  # Establish session
  - name: login to api
    xmlrpc_client:
      url: "{{api_url}}"
      path: login
      args:
        - admin
        - secret password.
    register: sid

  # Use session to execute privileged command. In this case server.group.add
  # returns a group ID from the API.
  - name: create new server group
    xmlrpc_client:
      url: "{{api_url}}"
      path: server.group.add
      args:
        - "{{sid.returned}}"
        - Dev environment web server group - Sweden, Malmoe
        - web
    register: server_group_id
    when: sid|changed

  # Use previous value in more API calls.
  - name: create new server
    xmlrpc_client:
      url: "{{api_url}}"
      path: server.add
      args:
        - "{{sid.returned}}"
        - vm-web01
        - 80
        - "{{server_group_id.returned}}"
    register: server_id
    when: server_group_id.returned
'''

RETURN = '''
returned:
  description: The output value that the RPC call returns
  type: string
  returned: success, changed
'''


try:
    from xmlrpc.client import ServerProxy
except ImportError:
    from xmlrpclib import ServerProxy

from ansible.module_utils.basic import AnsibleModule


def run_module():
    module_args = dict(
        url=dict(type='str', required=True),
        path=dict(type='str', required=True),
        args=dict(type='list', default=[]),
        kwargs=dict(type='dict', default={})
    )

    result = dict(
        changed=False,
        returned=None
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    try:
        server = ServerProxy(module.params['url'])
    except Exception as e:
        # Perhaps handle this with fail_json, that's why it's in a try block.
        raise

    # Only check if the RPC path exists in dry run
    if module.check_mode:
        if module.params['path'] in server.listMethods():
            result['returned'] = 'RPC call exists'
        else:
            result['returned'] = 'RPC call does not exist'
        return result

    try:
        returned_data = getattr(server, module.params['path'])(
            *module.params['args'],
            **module.params['kwargs']
        )
    except Exception as e:
        module.fail_json(
            msg='RPC call exception: {error}'.format(
                error=str(e)
            ),
            **result
        )

    result['returned'] = returned_data
    result['changed'] = True

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
