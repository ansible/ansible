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
module: cloudgenix_logout

short_description: "Logout of the CloudGenix API endpoint"

version_added: "2.6"

description:
    - "Logout to the CloudGenix API endpoint, invalidates AUTH_TOKEN credentials"

extends_documentation_fragment:
    - cloudgenix

author:
    - Aaron Edwards (@ebob9)
'''

EXAMPLES = '''
# Logout to standard controller
- name: Log out of CloudGenix
  cloudgenix_logout:
    auth_token: "<AUTH_TOKEN>"

# Logout to a testing controller
- name: Log out of CloudGenix
  cloudgenix_logout:
    auth_token: "<AUTH_TOKEN>"
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
    description: The autodetected region to use provided by the controller.
    type: str
    returned: always

controller:
    description: the final URL to be used by future modules.
    type: str
    returned: always

meta:
    description: Raw CloudGenix API response.
    type: dictionary
    returned: always

'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudgenix_util import (HAS_CLOUDGENIX, cloudgenix_common_arguments,
                                                  setup_cloudgenix_connection)

try:
    import cloudgenix
except ImportError:
    pass  # caught by imported HAS_CLOUDGENIX


def run_module():
    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = cloudgenix_common_arguments()

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

    # get CloudGenix API connection details
    auth_token, controller, tenant_id, cgx_session = setup_cloudgenix_connection(module)

    # Attempt to create site
    logout_response = cgx_session.get.logout()

    if not logout_response.cgx_status:
        result['meta'] = logout_response.cgx_content
        module.fail_json(msg='Logout failed.', **result)

    result['changed'] = True
    result['tenant_id'] = tenant_id
    result['controller'] = controller
    result['meta'] = logout_response.cgx_content

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)

    # avoid Pylint R1710
    return result


def main():
    run_module()


if __name__ == '__main__':
    main()
