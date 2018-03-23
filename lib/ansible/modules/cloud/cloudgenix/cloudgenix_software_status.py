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
module: cloudgenix_software_status

short_description: "Describe or Modify CloudGenix ION Element Software Status."

version_added: "2.6"

description:
    - "Describe or Modify CloudGenix ION Element Software Status. Upgrade/Downgrade of ION system images."

options:
    operation:
        description:
            - The operation you would like to perform on the Element object
        choices: ['wait', 'describe']
        required: True

    id:
        description:
            - Globally unique ID of the Element to Describe / Modify.
        required: True

    wait_image_id:
        description:
            - If operation is "wait", this value is the image_id to wait for the element to have as the active image.

    wait_timeout:
        description:
            - If operation is "wait", this is the timeout in seconds to wait for the element to be running the active
              image id.
        default: 600

extends_documentation_fragment:
    - cloudgenix

author:
    - Aaron Edwards (@ebob9)
'''

EXAMPLES = '''
# Show software status of an element
  - name: current element software state
    cloudgenix_software_status:
      auth_token: "<AUTH_TOKEN>"
      operation: "wait"
      id: "<ELEMENT_ID>"
      wait_image_id: "<SOFTWARE_IMAGE_ID>"
    register: describe_results

# Wait for an upgrade to finish before continuing.
  - name: Wait for upgrade
    cloudgenix_software_status:
      auth_token: "<AUTH_TOKEN>"
      operation: "wait"
      id: "<ELEMENT_ID>"
      wait_image_id: "<SOFTWARE_IMAGE_ID>"
      wait_timeout: 900
    register: upgrade_results

'''

RETURN = '''
operation:
    description: Operation that was executed
    type: string
    returned: always

region:
    description: Region string where the device code is managed from.
    type: string
    returned: always

upgrade_image_id:
    description: The latest upgrade command the Element has received is the Image ID in this response.
    type: string
    returned: always

active_image_id:
    description: Currently running Image ID on this Element.
    type: string
    returned: always

previous_image_id:
    description: The previously running Image ID on this Element.
    type: string
    returned: always

upgrade_state:
    description: Upgrade state the Element is currently in.
    type: string
    returned: always

failure_info:
    description: If Element code version change has failed, details provided here.
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
        operation=dict(choices=['wait', 'describe'], required=True),
        id=dict(type='str', required=True),
        wait_image_id=dict(type='str', required=False, default=None),
        wait_timeout=dict(type='int', required=False, default=600)
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
        region='',
        upgrade_image_id='',
        active_image_id='',
        previous_image_id='',
        upgrade_state='',
        failure_info='',
        meta={},
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        return result

    # extract the params to shorter named vars.
    id = module.params.get('id')
    operation = module.params.get('operation')
    wait_image_id = module.params.get('wait_image_id')
    wait_timeout = module.params.get('wait_timeout')

    # get CloudGenix API connection details
    auth_token, controller, tenant_id, cgx_session = setup_cloudgenix_connection(module)

    # start logic.

    # check if Machine is new, changing, or being deleted.
    if operation == 'describe':

        # Get the object.
        software_status_describe_response = cgx_session.get.software_status(id)

        # Check for API failure
        if not software_status_describe_response.cgx_status:
            result['meta'] = software_status_describe_response.cgx_content
            module.fail_json(msg='Element Software Status DESCRIBE failed.', **result)

        updated_software_status_result = software_status_describe_response.cgx_content

        # update result
        result = dict(
            changed=False,
            operation=operation,
            region=updated_software_status_result['region'],
            upgrade_image_id=updated_software_status_result['upgrade_image_id'],
            active_image_id=updated_software_status_result['active_image_id'],
            previous_image_id=updated_software_status_result['previous_image_id'],
            upgrade_state=updated_software_status_result['upgrade_state'],
            failure_info=updated_software_status_result['failure_info'],
            meta=software_status_describe_response.cgx_content
        )

        # success
        module.exit_json(**result)

    elif operation == 'wait':

        # Check for missing modify required fields.
        if any(field is None for field in [wait_image_id]):
            module.fail_json(msg='"wait_mage_id" is required for '
                                 'Software Status waiting.', **result)

        # Get the object before the loop - to confirm that it exists.
        software_status_describe_response = cgx_session.get.software_status(id)

        # Check for API failure
        if not software_status_describe_response.cgx_status:
            result['meta'] = software_status_describe_response.cgx_content
            module.fail_json(msg='Element Software Status DESCRIBE failed.', **result)

        # start loop waiting for right image ID.
        upgraded = False
        time_elapsed = 0

        while not upgraded:
            # check  status
            if software_status_describe_response.cgx_status:
                active_image_id = software_status_describe_response.cgx_content.get('active_image_id',
                                                                                    'NOVALUE')
                if wait_image_id == active_image_id:
                    upgraded = True

            if time_elapsed > wait_timeout:
                result['meta'] = software_status_describe_response.cgx_content
                module.fail_json(msg='ION wait_timeout time exceeded', **result)

            if not upgraded:
                time.sleep(10)
                time_elapsed += 10
                # refresh here - this is due to the fact that we want an initial query before the loop starts.
                software_status_describe_response = cgx_session.get.software_status(id)

        # Got here, means ION at right image.

        updated_software_status_result = software_status_describe_response.cgx_content

        # update result
        result = dict(
            changed=False,
            operation=operation,
            region=updated_software_status_result['region'],
            upgrade_image_id=updated_software_status_result['upgrade_image_id'],
            active_image_id=updated_software_status_result['active_image_id'],
            previous_image_id=updated_software_status_result['previous_image_id'],
            upgrade_state=updated_software_status_result['upgrade_state'],
            failure_info=updated_software_status_result['failure_info'],
            meta=software_status_describe_response.cgx_content
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
