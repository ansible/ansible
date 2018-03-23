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
module: cloudgenix_element_state

short_description: "Describe or Modify CloudGenix ION Element State."

version_added: "2.6"

description:
    - "Describe or Modify CloudGenix ION Element State. Upgrade/Downgrade of ION system images."

options:
    operation:
        description:
            - The operation you would like to perform on the Element object
        choices: ['modify', 'describe']
        required: True

    id:
        description:
            - Globally unique ID of the Element to Describe / Modify.
        required: True

    image_id:
        description:
            - Image ID to upgrade/downgrade the Element to.


extends_documentation_fragment:
    - cloudgenix

author:
    - Aaron Edwards (@ebob9)
'''

EXAMPLES = '''
# Upgrade an Element
  - name: upgrade it!
    cloudgenix_element_state:
      auth_token: "<AUTH_TOKEN>"
      operation: "modify"
      id: "<ELEMENT_ID>"
      image_id: "<SOFTWARE_IMAGE_ID>"
    register: modify_results

# View an Element assigned image
  - name: describe
    cloudgenix_element_state:
      auth_token: "<AUTH_TOKEN>"
      operation: "describe"
      id: "<ELEMENT_ID>"
    register: describe_results

'''

RETURN = '''
operation:
    description: Operation that was executed
    type: string
    returned: always

image_id:
    description: Globally unique ID of code release the system is running/will be upgraded/downgraded to.
    type: string
    returned: always

meta:
    description: Raw CloudGenix API response.
    type: dictionary
    returned: always

'''
import time
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
        operation=dict(choices=['modify', 'describe'], required=True),
        id=dict(type='str', required=True),
        image_id=dict(type='str', required=False, default=None),
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
        image_id='',
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
    image_id = module.params.get('image_id')

    # get CloudGenix API connection details
    auth_token, controller, tenant_id, cgx_session = setup_cloudgenix_connection(module)

    # start logic.

    # check if Machine is new, changing, or being deleted.
    if operation == 'describe':

        # Get the object.
        element_state_describe_response = cgx_session.get.state(id)

        # Check for API failure
        if not element_state_describe_response.cgx_status:
            result['meta'] = element_state_describe_response.cgx_content
            module.fail_json(msg='Element State DESCRIBE failed.', **result)

        updated_element_state_result = element_state_describe_response.cgx_content

        # update result
        result = dict(
            changed=False,
            operation=operation,
            image_id=updated_element_state_result['image_id'],
            meta=element_state_describe_response.cgx_content
        )

        # success
        module.exit_json(**result)

    elif operation == 'modify':

        # Check for missing modify required fields.
        if any(field is None for field in [image_id]):
            module.fail_json(msg='"image_id" is required for '
                                 'Element State Modification.', **result)

        # Get the object.
        element_state_describe_response = cgx_session.get.state(id)

        # Check for API failure
        if not element_state_describe_response.cgx_status:
            result['meta'] = element_state_describe_response.cgx_content
            module.fail_json(msg='Element State DESCRIBE failed.', **result)

        # Modify the result and put back
        element_state_change = element_state_describe_response.cgx_content
        element_state_change['image_id'] = image_id

        element_state_modify_response = cgx_session.put.state(id, element_state_change)

        if not element_state_modify_response.cgx_status:
            result['meta'] = element_state_modify_response.cgx_content
            module.fail_json(msg='Element State MODIFY failed.', **result)

        updated_element_state_result = element_state_modify_response.cgx_content

        # update result
        result = dict(
            changed=False,
            operation=operation,
            image_id=updated_element_state_result['image_id'],
            meta=element_state_describe_response.cgx_content
        )

        # success
        module.exit_json(**result)

    else:
        module.fail_json(msg='Invalid operation for module: {0}'.format(operation), **result)

    # avoid Pylint R1710
    return result


def main():
    run_module()


if __name__ == '__main__':
    main()
