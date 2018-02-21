#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: sda_rest

short_description: Direct access to the Cisco Software-Defined Access (SDA) controller

version_added: "2.6"

description:
    - Enables management of the Cisco Software-Defined Access controller, more commonly called DNA Center
    - More information about the DNA Center API can be found at U(https://developer.cisco.com/site/dna-center-rest-api/)

options:
    name:
        description:
            - This is the message to send to the sample module
        required: true
    new:
        description:
            - Control to demo if the result of this module is changed or not
        required: false

# extends_documentation_fragment:
#     - azure

author:
    - Kevin Breit (@kbreit)
'''

EXAMPLES = '''
# Pass in a message
- name: Test with a message
  my_new_test_module:
    name: hello world

# pass in a message and have changed true
- name: Test with a message and changed output
  my_new_test_module:
    name: hello world
    new: true

# fail the module
- name: Test failure of the module
  my_new_test_module:
    name: fail me
'''

RETURN = '''
original_message:
    description: The original name param that was passed in
    type: str
message:
    description: The output message that the sample module generates
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url, open_url
from ansible.module_utils.basic import json
from ansible.module_utils._text import to_bytes, to_native, to_text
# import json

def run_module():
    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = dict(
        username=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
        hostname=dict(type='str', required=True),
        method=dict(type='str', choices=['delete','get','post'], required=True),
        path=dict(type='path', required=True),
        timeout=dict(type='int', default=30, required=False),
        use_proxy=dict(type='bool', default=False, required=False),
        use_ssl=dict(type='bool', default=True, required=False),
        validate_certs=dict(type='bool', default=False, required=False),
        content=dict(type='raw', required=False)
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        message=''
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
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
        
    url = '{0}://{1}{2}'.format(protocol, module.params['hostname'], module.params['path'])
    headers = { 'Content-Type': 'application/json' }
    authheaders = { 'Content-Type': 'application/json' }

    try:
        authurl = '{0}://{1}/api/system/v1/auth/login'.format(protocol, module.params['hostname'])
        authresp = open_url(  authurl,
                            headers=authheaders,
                            method='GET',
                            use_proxy=module.params['use_proxy'],
                            timeout=module.params['timeout'],
                            validate_certs=module.params['validate_certs'],
                            url_username=module.params['username'],
                            url_password=module.params['password'],
                            force_basic_auth=True)

    except HTTPError as e:
        module.fail_json(msg=e.fp)

    if to_native(authresp.read()) != "success": # DNA Center returns success in body
        module.fail_json(msg="Authentication failed: {0}".format(authresp.read()))

    respheaders = authresp.getheaders()
    cookie = None
    for i in respheaders:
        if i[0] == 'Set-Cookie':
            cookie_split = i[1].split(';')
            cookie = cookie_split[0]

    # module.fail_json(msg=cookie)
    
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
                                timeout=module.params['timeout'])

    except HTTPError as e:
        module.fail_json(msg=e.fp)

    if info['status'] != 200:
        module.fail_json(msg='{0}: {1} '.format(info['status'], info['body']))
                      
    # use whatever logic you need to determine whether or not this module
    # made any modifications to your target
    if info['status'] == 200:
        result['changed'] = True
        # result['message']=json.loads(resp.read())
        try:
            result['message']=json.loads(resp.read())
        except:
            module.fail_json(msg="DNA Center didn't return JSON compatible data")

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

def main():
    run_module()

if __name__ == '__main__':
    main()