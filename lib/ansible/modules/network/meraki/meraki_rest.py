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
    - More information about the Meraki API can be found at U(https://dashboard.meraki.com/api_docs).

options:
    auth_key:
        description:
            - Authentication key provided by the dashboard. Required if environmental variable MERAKI_KEY is not set.
        required: no
    host:
        description:
            - FQDN or IP address of Meraki dashboard.
        required: yes
    method:
        description:
            - The HTTP method of the request.
            - Using C(delete) is typically used for deleting objects.
            - Using C(get) is typically used for querying objects.
            - Using C(put) is typically used for modifying objects.
            - Using C(post) is typically used for modifying objects.
        required: yes
        choices: [ delete, get, post, put ]
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
        default: no
    use_ssl:
        description:
            - If C(no), it will use HTTP. Otherwise it will use HTTPS.
        type: bool
        default: yes
    validate_certs:
        description:
            - If C(no), HTTPS certificates will not be verified.
        type: bool
        default: yes
    content:
        description:
            - Raw content which should be fed in body.
    src:
        description:
            - Name of absolute path of the filename which contains content to be fed to Meraki Dashboard. Must be in JSON format.

author:
    - Kevin Breit (@kbreit)
'''

EXAMPLES = '''
# Query inventory
- name: Query network device inventory
  sda_rest:
    auth_key: abc12345
    host: dashboard.meraki.com
    method: get
    path: /api/v0/organizations
    use_ssl: yes
  delegate_to: localhost

- name: Create network
  sda_rest:
    auth_key: abc12345
    host: dashboard.meraki.com
    method: post
    path: /api/v0/organizations/133277/networks
    src: /home/username/network.json
    use_ssl: yes
  delegate_to: localhost

'''

RETURN = '''
response:
    description: Data returned from Meraki dashboard.
    type: dict
    returned: info
'''

import os
from ansible.module_utils.basic import AnsibleModule, json
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_native


def main():

    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = dict(auth_key=dict(type='str', no_log=True),
                       host=dict(type='str', required=True),
                       method=dict(type='str', choices=['delete', 'get', 'post', 'put'], required=True),
                       path=dict(type='path', required=True),
                       timeout=dict(type='int', default=30),
                       use_proxy=dict(type='bool', default=False),
                       use_ssl=dict(type='bool', default=True),
                       validate_certs=dict(type='bool', default=True),
                       content=dict(type='raw'),
                       src=dict(type='path'),
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
    module.params['follow_redirects'] = 'urllib2'
        
    try:
        module.params['auth_key'] = os.environ['MERAKI_KEY']
    except KeyError:
        pass
    
    if module.params['auth_key'] is None:
        module.fail_json(msg='Meraki Dashboard API key not set')

    path = module.params['path']
    payload = None
    
    if module.params['content']:
        payload = module.params['content']
        payload = json.dumps(payload)
    elif module.params['src']:
        src = module.params['src']
        file_exists = False
        if os.path.isfile(src):
            file_exists = True
            with open(src, 'r') as config_object:
                payload = config_object.read()
        else:
            module.fail_json(msg="File does not exist")

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        return result

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)
    protocol = None
    if module.params['use_ssl'] is not None and module.params['use_ssl'] is False:
        protocol = 'http'
    else:
        protocol = 'https'

    url = '{0}://{1}/{2}'.format(protocol, module.params['host'], module.params['path'].lstrip('/'))
    headers = {'Content-Type': 'application/json',
               'X-Cisco-Meraki-API-Key': module.params['auth_key'],
              }

    # result['url'] = url
    # result['method'] = module.params['method']
    # result['headers'] = headers
    # result['payload'] = payload

    try:
        resp, info = fetch_url(module, url,
                               data=payload,
                               headers=headers,
                               method=module.params['method'].upper(),
                               use_proxy=module.params['use_proxy'],
                               force=False,
                               timeout=module.params['timeout'],
                               # use_ssl=module.params['use_ssl'],
                               )
        # result['headers'] = str(dir(resp))
        result['headers'] = str(resp.headers)

    except Exception as e:
        module.fail_json(msg=e)

    if info['status'] >= 300:
        module.fail_json(msg='{0}: {1} '.format(info['status'], info['body']), **result)

    module.warn(to_native(info['status']))

    # use whatever logic you need to determine whether or not this module
    # made any modifications to your target
    if info['status'] >= 200 and info['status'] <= 299:
        result['changed'] = True
        try:
            result['message'] = json.loads(to_native(resp.read()))
        except:
            module.fail_json(msg="Meraki dashboard didn't return JSON compatible data")

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


if __name__ == '__main__':
    main()
