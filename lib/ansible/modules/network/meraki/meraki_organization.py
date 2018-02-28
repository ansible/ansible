#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Kevin Breit (@kbreit) <kevin.breit@kevinbreit.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: meraki_organization
short_description: Manage organizations in the Meraki cloud
version_added: "2.6"
description:
- Allows for creation, management, and visibility into organizations within Meraki

notes:
- More information about the Meraki API can be found at U(https://dashboard.meraki.com/api_docs).
- Some of the options are likely only used for developers within Meraki

options:
    auth_key:
        description:
        - Authentication key provided by the dashboard. Required if environmental variable MERAKI_KEY is not set.
    name:
        description:
        - Organization ID of an organization
    host:
        description:
        - Hostname for Meraki dashboard
        - Only useful for internal Meraki developers
        type: string
        default: 'api.meraki.com'
    use_proxy:
        description:
        - If C(no), it will not use a proxy, even if one is defined in an environment variable on the target hosts.
        type: bool
    use_ssl:
        description:
        - If C(no), it will use HTTP. Otherwise it will use HTTPS.
        - Only useful for internal Meraki developers
        type: bool
        default: 'yes'
    output_level:
        description:
        - Set amount of debug output during module execution
        choices: ['normal', 'debug']

author:
    - Kevin Breit (@kbreit)
'''

EXAMPLES = '''
- name: Query information about all organizations
  meraki_organization:
    auth_key: abc12345
    status: query
  delegate_to: localhost

- name: Query information about a single organization named YourOrg
  meraki_organization:
    auth_key: abc12345
    name: YourOrg
    status: query
  delegate_to: localhost

- name: Create a new organization named YourOrg
  meraki_organization:
    auth_key: abc12345
    name: YourOrg
    status: present
  delegate_to: localhost
'''

RETURN = '''
response:
    description: Data returned from Meraki dashboard.
    type: dict
    state: query
    returned: info
'''

import os
from ansible.module_utils.basic import AnsibleModule, json, env_fallback
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_native

def find_org_id(data, name):
    ''' Find an organization's ID based on the provided name '''
    for i in data:
        if i['name'] == name:
            return i['id']

def meraki_request(module, result, url, method, headers, payload):
    try:
        resp, info = fetch_url(module, url,
                               data=json.dumps(payload),
                               headers=headers,
                               method=method,
                               use_proxy=module.params['use_proxy'],
                               force=False,
                               )
    except Exception as e:
        module.fail_json(msg=str(e), **debug_result)

    # module.fail_json(msg=info['status'])
    data = resp.read()
    if module.params['output_level'] == 'debug':
        debug_result['status'] = info['status']
        debug_result['resp_headers'] = resp.headers
        debug_result['response'] = data
    response = json.loads(to_native(data))

    if info['status'] >= 200 and info['status'] <= 299:
        try:
            result['message'] = response
            if method == 'POST' or method == 'PUT':
                if info['status'] == 201:
                    result['changed'] = True
        except:
            module.fail_json(msg="Meraki dashboard didn't return JSON compatible data")
    else:
        module.fail_json(msg='{0}: {1} '.format(info['status'], info['body']), **result)
    return response

def main():

    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = dict(auth_key=dict(type='str', no_log=True, fallback=(env_fallback, ['MERAKI_KEY'])),
                       host=dict(type='str', default='api.meraki.com'),
                       name=dict(type='str'),
                       username=dict(type='str'),
                       state=dict(type='str', choices=['present', 'absent', 'query'], required=True),
                       use_proxy=dict(type='bool', default=False),
                       use_ssl=dict(type='bool', default=True),
                       validate_certs=dict(type='bool', default=True),
                       output_level=dict(type='str', default='normal', choices=['normal', 'debug']),
                       )

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(argument_spec=module_args,
                           supports_check_mode=False,
                           )
    module.params['follow_redirects'] = 'all'

    module.required_if=[
                           ['state', 'present', ['name']],
                           ['state', 'absent', ['name']],
                       ]

    try:
        module.params['auth_key'] = os.environ['MERAKI_KEY']
    except KeyError:
        pass

    if module.params['auth_key'] is None:
        module.fail_json(msg='Meraki Dashboard API key not set')

    payload = None

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        return result

    # execute checks for argument completeness

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)
    protocol = 'https'
    if module.params['use_ssl'] is not None and module.params['use_ssl'] is False:
        protocol = 'http'
    host = 'api.meraki.com'

    url = '{0}://api.meraki.com/api/v0/organizations'.format(protocol)
    headers = {'Content-Type': 'application/json',
               'X-Cisco-Meraki-API-Key': module.params['auth_key'],
               }

    method = 'GET'

    if module.params['output_level'] == 'debug':
        debug_result=dict(url=url,
                          method=method,
                          headers=headers,
                          payload=payload,
                          )
        if module.params['state']:
            debug_result['state'] = module.params['state']

    try:
        resp, info = fetch_url(module, url,
                               data=payload,
                               headers=headers,
                               method=method,
                               use_proxy=module.params['use_proxy'],
                               force=False,
                               )

    except Exception as e:
        module.fail_json(msg=str(e), **debug_result)
    data = resp.read()
    if module.params['output_level'] == 'debug':
        debug_result['status'] = info['status']
        debug_result['resp_headers'] = resp.headers
        debug_result['response'] = data
    response = json.loads(to_native(data))

    if info['status'] >= 200 and info['status'] <= 299:
        try:
            result['changed'] = False
            result['message'] = response
        except:
            module.fail_json(msg="Meraki dashboard didn't return JSON compatible data for user lookup")
    else:
        module.fail_json(msg='{0}: {1} '.format(info['status'], info['body']), **result)

    response_items = None
    org_id = None

    if module.params['state'] == 'query' and module.params['name'] is None:  #Record all organizations, no matter what
        response_items = response
    elif module.params['state'] == 'query' and module.params['name']:
        module.warn('If there are multiple organizations with the same name, only the first matching result will be processed')
        for i in response:
            if i['name'] == module.params['name']:
                response_items = i
                break

    ''' Return the id for further processing. Some of these checks may not be necessary'''
    if module.params['state'] == 'present' or module.params['state'] == 'absent':
        if response_items:
            org_id = find_org_id(response_items, module.params['name'])
            # module.fail_json(msg=org_id)
            if module.params['state'] == 'present':
                module.fail_json(msg='Modifying an existing organization is not implemented')
            elif module.params['state'] == 'absent':
                module.fail_json(msg='Deleting an organization is not implemented')
        else:
            module.warn("Create module")
            url = '{0}://{1}/api/v0/organizations'.format(protocol, module.params['host'])
            payload = {'name': module.params['name']}
            r = meraki_request(module, result, url, 'POST', headers, payload)
    elif module.params['state'] == 'query':
        result['message'] = response_items

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


if __name__ == '__main__':
    main()
