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
module: cloudgenix_element_operations

short_description: "Reboot, Declaim, Restart DHCP server on an element."

version_added: "2.6"

description:
    - "Element Operations - Reboot, Declaim (revoke), or restart services such as DHCP server."

options:
    operation:
        description:
            - The operation you would like to perform on the Machine object
        choices: ['reboot', 'declaim', 'restart_dhcp']
        required: True

    id:
        description:
            - Globally unique ID of the Element that is to be modified.
        required: True


extends_documentation_fragment:
    - cloudgenix

author:
    - Aaron Edwards (@ebob9)
'''

EXAMPLES = '''
# Reboot an element
  - name: reboot it!
    cloudgenix_element_operations:
      auth_token: "<AUTH_TOKEN>"
      operation: "reboot"
      id: "<ELEMENT_ID>"
    register: reboot_results

# Restart DHCP on an element
  - name: restart dhcp
    cloudgenix_element_operations:
      auth_token: "<AUTH_TOKEN>"
      operation: "restart_dhcp"
      id: "<ELEMENT_ID>"
    register: dhcp_restart_results

# Declaim an element and return it to machine-only state
  - name: Declaim and return to machine state
    cloudgenix_element_operations:
      auth_token: "<AUTH_TOKEN>"
      operation: "declaim"
      id: "<ELEMENT_ID>"
    register: declaim_results

'''

RETURN = '''
operation:
    description: Operation that was executed
    type: string
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
    module_args.update(dict(
        operation=dict(choices=['reboot', 'declaim', 'restart_dhcp'], required=True),
        id=dict(type='str', required=True),
    ))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # check for Cloudgenix SDK (Required)
    if not HAS_CLOUDGENIX:
        module.fail_json(msg='The "cloudgenix" python module is required by this Ansible module.')

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        operation='',
        meta={},
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        return result

    # extract the params to shorter named vars.
    operation = module.params.get('operation')
    id = module.params.get('id')

    # get CloudGenix API connection details
    auth_token, controller, tenant_id, cgx_session = setup_cloudgenix_connection(module)

    # start logic.

    operation_text = None
    if operation == 'reboot':
        operation_text = 'reboot'
    elif operation == 'declaim':
        operation_text = 'declaim'
    elif operation == 'restart_dhcp':
        operation_text = 'restart_intf_dhcp_server'
    else:
        module.fail_json(msg='Invalid operation for module: {0}'.format(operation), **result)

    operation_data = {
        "action": operation_text,
        "parameters": None
    }

    # Attempt to submit element operation
    elements_operation_response = cgx_session.post.tenant_element_operations(id, operation_data)

    # Check for API failure
    if not elements_operation_response.cgx_status:
        result['meta'] = elements_operation_response.cgx_content
        module.fail_json(msg='Element Operation {0} failed.'.format(operation.upper()), **result)

    # update result
    result = dict(
        changed=True,
        operation=operation,
        meta=elements_operation_response.cgx_content
    )

    # success
    module.exit_json(**result)

    # avoid Pylint R1710
    return result


def main():
    run_module()


if __name__ == '__main__':
    main()
