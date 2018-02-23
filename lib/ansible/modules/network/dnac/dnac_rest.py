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
module: dnac_rest

short_description: Direct access to the Cisco Software-Defined Access (SDA) controller, DNA Central

version_added: "2.6"

description:
    - Enables management of the Cisco Software-Defined Access controller, more commonly called DNA Center.
    - More information about the DNA Center API can be found at U(https://developer.cisco.com/site/dna-center-rest-api/).

options:
    username:
        description:
            - The username for use in HTTP basic authentication.
        required: yes
    password:
        description:
            - The password for use in HTTP basic authentication.
        required: yes
    host:
        description:
            - FQDN or IP address of DNA Central server.
        required: yes
    method:
        description:
            - The HTTP method of the request.
            - Using C(delete) is typically used for deleting objects.
            - Using C(get) is typically used for querying objects.
            - Using C(post) is typically used for modifying objects.
        required: yes
        choices: [ delete, get, post ]
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

author:
    - Kevin Breit (@kbreit)
'''

EXAMPLES = '''
# Query inventory
- name: Query network device inventory
  sda_rest:
    username: dnacuser
    password: dnaccpass
    host: dnac.yourorg.com
    method: get
    path: /api/v1/network-device
    use_ssl: yes
  delegate_to: localhost

'''

RETURN = '''
response:
    description: Data returned from controller.
    type: string
    returned: success
version:
    description: Version of returned data.
    type: string
    returned: info
'''


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url, open_url
from ansible.module_utils.basic import json
from ansible.module_utils._text import to_native


def main():

    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = dict(
        username=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
        host=dict(type='str', required=True),
        method=dict(type='str', choices=['delete', 'get', 'post'], required=True),
        path=dict(type='path', required=True),
        timeout=dict(type='int', default=30),
        use_proxy=dict(type='bool', default=False),
        use_ssl=dict(type='bool', default=True),
        validate_certs=dict(type='bool', default=True),
        content=dict(type='raw'),
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
    )

    path = module.params['path']
    content = module.params['content']
    payload = content

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifiupcations
    if module.check_mode:
        return result

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)
    protocol = None
    if module.params['use_ssl'] is not None and module.params['use_ssl'] is False:
        protocol = 'http'
    else:
        protocol = 'https'

    url = '{0}://{1}/{2}'.format(protocol, module.params['host'].rstrip('/'), module.params['path'].lstrip('/'))
    headers = {'Content-Type': 'application/json'}
    authheaders = {'Content-Type': 'application/json'}

    module.fail_json(msg=url)

    try:
        authurl = '{0}://{1}/api/system/v1/auth/login'.format(protocol, module.params['host'])
        authresp = open_url(authurl,
                            headers=authheaders,
                            method='GET',
                            use_proxy=module.params['use_proxy'],
                            timeout=module.params['timeout'],
                            validate_certs=module.params['validate_certs'],
                            url_username=module.params['username'],
                            url_password=module.params['password'],
                            force_basic_auth=True,
                            )

    except Exception as e:
        module.fail_json(msg=e)

    if to_native(authresp.read()) != "success":  # DNA Center returns success in body
        module.fail_json(msg="Authentication failed: {0}".format(authresp.read()))

    respheaders = authresp.getheaders()
    cookie = None
    for i in respheaders:
        if i[0] == 'Set-Cookie':
            cookie_split = i[1].split(';')
            cookie = cookie_split[0]

    if cookie is None:
        module.fail_json(msg="Cookie not assigned from DNA Central")

    headers['Cookie'] = cookie

    try:
        resp, info = fetch_url(module, url,
                               data=payload,
                               headers=headers,
                               method=module.params['method'].upper(),
                               use_proxy=module.params['use_proxy'],
                               force=True,
                               timeout=module.params['timeout'],)

    except Exception as e:
        module.fail_json(msg=e)

    if info['status'] != 200:
        module.fail_json(msg='{0}: {1} '.format(info['status'], info['body']))

    # use whatever logic you need to determine whether or not this module
    # made any modifications to your target
    if info['status'] == 200:
        result['changed'] = True
        try:
            result.update(json.loads(to_native(resp.read())))
        except:
            module.fail_json(msg="DNA Center did not return JSON compatible data")

    # during the execution of the module, if there is an exception or a
    # conditional state that effectively causes a failure, run
    # AnsibleModule.fail_json() to pass in the message and the result
    if info['status'] != 200:
        try:
            module.fail_json(msg="DNA Center error: {0} - {1}: ".format(info['status'], info['body']))
        except KeyError:
            module.fail_json(msg="Connection failed for {0}: ".format(url))

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)

if __name__ == '__main__':
    main()
