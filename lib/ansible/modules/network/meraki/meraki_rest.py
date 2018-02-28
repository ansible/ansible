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
module: meraki_rest

short_description: Direct access to the Cisco Meraki management dashboard

version_added: "2.6"

description:
    - Enables management of Cisco's Meraki line of products through their cloud based dashboard.

notes:
    - Disabling HTTPS (C(use_ssl=no) will cause DELETE, POST and PUT methods to perform a GET (query).
    - Using C(host) and C(validate_certs=no) is only useful if you are a Cisco developer working with an in-house Meraki setup.
    - More information about the Meraki API is available from U(https://dashboard.meraki.com/api_docs).

options:
    auth_key:
        description:
            - Authentication key provided by the dashboard.
            - Required if environmental variable MERAKI_KEY is not set.
        default: MERAKI_KEY env var
    host:
        description:
            - FQDN or IP address of Meraki dashboard.
            - This is only useful if you are a Cisco developer working with an in-house Meraki setup.
        default: api.meraki.com
    method:
        description:
            - The HTTP method of the request.
            - Using C(delete) is typically used for deleting objects.
            - Using C(get) is typically used for querying objects.
            - Using C(post) and C(put) are typically used for modifying objects.
        choices: [ delete, get, post, put ]
        default: get
    path:
        description:
            - Directory path to the endpoint. Do not include FQDN specified in C(host).
        required: yes
    timeout:
        description:
            - HTTP timeout value.
        default: 30
    use_proxy:
        description:
            - If C(no), it will not use a proxy, even if one is defined in an environment variable on the target hosts.
        type: bool
        default: 'yes'
    use_ssl:
        description:
            - If C(no), it will use HTTP. Otherwise it will use HTTPS.
            - Disabling HTTPS will cause DELETE, POST and PUT methods to perform a GET (query).
        type: bool
        default: 'yes'
    validate_certs:
        description:
            - If C(no), HTTPS certificates will not be verified.
            - This is only useful if you are a Cisco developer working with an in-house Meraki setup.
        type: bool
        default: 'yes'
    content:
        description:
            - Raw content which should be fed in body.
            - Mutual exclusive with C(src).
    src:
        description:
            - Name of absolute path of the filename which contains content to be fed to Meraki Dashboard.
            - Must be in JSON format.
            - Mutual exclusive with C(content).
    output_level:
        description:
            - Set amount of debug output during module execution.
        choices: [ debug, normal ]
        default: normal

author:
    - Kevin Breit (@kbreit)
    - Dag Wieers (@dagwieers)
'''

EXAMPLES = '''
# Query inventory
- name: Query network device inventory
  meraki_rest:
    auth_key: abc12345
    method: get
    path: /api/v0/organizations
  delegate_to: localhost

- name: Create organization
  meraki_rest:
    auth_key: abc12345
    method: post
    path: /api/v0/organizations
    content: '{ "name": "My new organization" }'
  delegate_to: localhost

- name: Create network
  meraki_rest:
    auth_key: abc12345
    method: post
    path: /api/v0/organizations/133277/networks
    src: /home/username/network.json
  delegate_to: localhost
'''

RETURN = '''
data:
    description: Data returned from Meraki dashboard.
    type: dict
    returned: info
'''

import os
from ansible.module_utils.basic import AnsibleModule, json, env_fallback
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_native, to_text

# Optional, only used for YAML validation
try:
    import yaml
    HAS_YAML = True
except:
    HAS_YAML = False


def main():

    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = dict(
        auth_key=dict(type='str', no_log=True, fallback=(env_fallback, ['MERAKI_KEY'])),
        host=dict(type='str', default='api.meraki.com'),
        method=dict(type='str', default='get', choices=['delete', 'get', 'post', 'put']),
        path=dict(type='path', required=True),
        timeout=dict(type='int', default=30),
        use_proxy=dict(type='bool', default=True),
        use_ssl=dict(type='bool', default=True),
        validate_certs=dict(type='bool', default=True),
        content=dict(type='raw'),
        src=dict(type='path'),
        output_level=dict(type='str', default='normal', choices=['debug', 'normal']),
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
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False,
        mutually_exclusive=[['content', 'src']],
    )

    if module.params['auth_key'] is None:
        module.fail_json(msg='Meraki Dashboard API key not set')

    method = module.params['method']
    path = module.params['path']
    content = module.params['content']
    src = module.params['src']
    module.params['follow_redirects'] = 'all'

    # Report missing file
    file_exists = False
    if src:
        if os.path.isfile(src):
            file_exists = True
        else:
            module.fail_json(msg="Cannot find/access src '%s'" % src)

    # We include the payload as it may be templated
    payload = content
    if file_exists:
        with open(src, 'r') as config_object:
            # TODO: Would be nice to template this, requires action-plugin
            payload = config_object.read()

    json_payload = payload
    if content and isinstance(content, dict):
        # Validate inline YAML/JSON
        json_payload = json.dumps(payload)
    elif payload and isinstance(payload, str) and HAS_YAML:
        try:
            # Validate YAML/JSON string
            json_payload = json.dumps(yaml.safe_load(payload))
        except Exception as e:
            module.fail_json(msg='Failed to parse provided JSON/YAML payload: %s' % to_text(e), exception=to_text(e), payload=payload)

    if method in ('delete', 'get'):
        json_payload = None

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)
    protocol = 'https'
    if module.params['use_ssl'] is False:
        protocol = 'http'
        module.warn('Using HTTP (without SSL) every request becomes a query (GET) request')

    headers = {
        'Content-Type': 'application/json',
        'X-Cisco-Meraki-API-Key': module.params['auth_key'],
    }
    url = '{0}://{1}/{2}'.format(protocol, module.params['host'], module.params['path'].lstrip('/'))

    debug_result = dict(
        headers=headers,
        json_payload=json_payload,
        method=method.upper(),
        payload=payload,
        url=url,
    )

    try:
        resp, info = fetch_url(module, url,
                               data=json_payload,
                               headers=headers,
                               method=method.upper(),
                               use_proxy=module.params['use_proxy'],
                               force=False,
                               timeout=module.params['timeout'],
                               )
    except Exception as e:
        result.update(debug_result)
        module.fail_json(msg=to_native(e))

    if module.params['output_level'] == 'debug':
        debug_result['status'] = info['status']
        debug_result['response'] = info['msg']
        result.update(debug_result)

    # use whatever logic you need to determine whether or not this module
    # made any modifications to your target
    if 200 <= info['status'] <= 300 and resp is not None:
        try:
            result['data'] = json.loads(to_native(resp.read()))
        except KeyError:
            module.fail_json(msg="Meraki dashboard didn't return JSON compatible data", **result)
    elif 400 <= info['status'] < 500:
        try:
            data = json.loads(to_native(info['body']))
            module.fail_json(msg='Dashboard API Error: {0} '.format(';'.join(data['errors'])), **result)
        except (ValueError, KeyError) as e:
            result['data'] = to_native(info['body'])
            module.fail_json(msg=result['response'], **result)
    else:
        module.fail_json(msg='Unknown Error', info=info, **result)

    if method != 'get':
        result['changed'] = True

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(info=info, **result)


if __name__ == '__main__':
    main()
