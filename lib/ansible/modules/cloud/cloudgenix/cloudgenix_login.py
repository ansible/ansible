#!/usr/bin/python
# Copyright (c) 2018 CloudGenix Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: cloudgenix_login

short_description: "Login to the CloudGenix API endpoint"

version_added: "2.6"

description:
    - "Login to the CloudGenix API endpoint, to obtain an AUTH_TOKEN for use in later calls"

options:
    email:
        description:
            - This is the email of the account to login with
        required: true
    password:
        description:
            - This is the password of the account to login with
        required: true
    controller:
        description:
            - Base URI of controller to use
        required: false
        default: "https://api.elcapitan.cloudgenix.com"
    ssl_verify:
        description:
            - Boolean of whether to validate SSL connections
        required: false
        default: True
        type: bool
    ignore_region:
        description:
            - Boolean of whether to disregard region recommendations sent by the controller.
        required: false
        default: False
        type: bool

notes:
  - For more information on using Ansible to manage the CloudGenix App Fabric, see U(https://support.cloudgenix.com)
    or U(https://developers.cloudgenix.com).
  - Requires the C(cloudgenix) python module on the host. Typically, this is done with C(pip install cloudgenix).

requirements:
  - cloudgenix >= 4.6.1b1

author:
    - Aaron Edwards (@ebob9)
'''

EXAMPLES = '''
# Login to standard controller
- name: Log in to CloudGenix
  cloudgenix_login:
    email: "test@test.com"
    password: "Secethax0rpass"

# Login to a testing controller
- name: Log in to test CloudGenix
  cloudgenix_login:
    email: "test@test.com"
    password: "Secethax0rpass"
    controller: "https://api-45.hood.cloudgenix.com"
    ssl_verify: False

'''

RETURN = '''
auth_token:
    description: The AUTH_TOKEN for use in later operations
    type: str
    returned: always

tenant_id:
    description: The unique tenant ID for the logged in account.
    type: str
    returned: always

region:
    description: The auto-detected region to use provided by the controller.
    type: str
    returned: always

controller:
    description: The final URL to be used by subsequent modules.
    type: str
    returned: always

meta:
    description: Raw CloudGenix API response.
    type: dictionary
    returned: on failure
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudgenix_util import HAS_CLOUDGENIX

try:
    import cloudgenix
except ImportError:
    pass  # caught by imported HAS_CLOUDGENIX


def run_module():
    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = dict(
        email=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
        controller=dict(type='str', required=False),
        ssl_verify=dict(type='bool', required=False, default=True),
        ignore_region=dict(type='bool', required=False, default=False),
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        auth_token='',
        tenant_id='',
        controller='',
        region='',
        meta=''
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # check for Cloudgenix SDK (Required)
    if not HAS_CLOUDGENIX:
        module.fail_json(msg='The "cloudgenix" python module is required by this Ansible module.')

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        return result

    # setup CloudGenix API session
    cgx_session = cloudgenix.API(controller=module.params['controller'],
                                 ssl_verify=module.params['ssl_verify'])

    cgx_session.ignore_region = module.params['ignore_region']

    # issue login request
    login_response = cgx_session.post.login({
        "email": module.params['email'],
        "password": module.params['password']
    })

    # check for login failure
    if not login_response.cgx_status:
        # if login fails, fail module
        result['meta'] = login_response.cgx_content
        module.fail_json(msg='login failure', **result)

    auth_token = login_response.cgx_content.get('x_auth_token')
    # Check for no AUTH_TOKEN, this means a SAML or MSP/ESP user, which is not supported in this version.
    if not auth_token:
        result['meta'] = login_response.cgx_content
        module.fail_json(msg='The "email" specified was a SAML2.0 user or ESP/MSP user. '
                             'These are not yet supported via the CloudGenix Ansible module',
                         **result)

    # login success, mark changed True, as session is established even if somethin below fails.
    result['changed'] = True

    # token in the original login (not saml) means region parsing has not been done.
    # do now, and recheck if cookie needs set.
    auth_region = cgx_session.parse_region(login_response)
    cgx_session.update_region_to_controller(auth_region)
    cgx_session.reparse_login_cookie_after_region_update(login_response)

    # everything but tenant_id, update result
    result['auth_token'] = auth_token
    result['region'] = cgx_session.controller_region
    result['controller'] = cgx_session.controller

    # get tenant id
    profile_response = cgx_session.get.profile()

    if not profile_response.cgx_status:
        # profile get failure, fail module
        result['meta'] = profile_response.cgx_content
        module.fail_json(msg='GET profile failure', **result)

    cgx_session.tenant_id = profile_response.cgx_content.get('tenant_id')
    cgx_session.email = profile_response.cgx_content.get('email')

    if not cgx_session.tenant_id:
        # tenant ID not in profile, fail.
        result['meta'] = profile_response.cgx_content
        module.fail_json(msg='GET profile had no tenant_id value.', **result)

    result['tenant_id'] = cgx_session.tenant_id

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)

    # avoid Pylint R1710
    return result


def main():
    run_module()


if __name__ == '__main__':
    main()
