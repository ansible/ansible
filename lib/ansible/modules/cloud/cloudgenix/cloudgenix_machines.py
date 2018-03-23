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
module: cloudgenix_machines

short_description: "Describe, Claim or Return or Retire CloudGenix ION Machines."

version_added: "2.6"

description:
    - "Describe, Claim, Return (Physical), or Retire (Virtual) CloudGenix ION Machines."

options:
    operation:
        description:
            - The operation you would like to perform on the Machine object
        choices: ['claim', 'return', 'retire', 'describe']
        required: True

    id:
        description:
            - Globally unique ID of the Machine object to Claim/Declaim.
        required: True

    wait_if_offline:
        description:
            - Number of seconds to wait if the ION is offline when attempting CLAIM. Will fail after this timeframe.
              '0' will cause immediate failure if ION is offline.
        default: 300

    verify_success:
        description:
            - Wait for operation to complete, and verify successful Claim. If False, immediately exit with
              success without waiting for operation to complete.
        default: True
        type: bool

    wait_verify_success:
        description:
            - Number of seconds to wait for Claim / Declaim operation to succeed. Will fail after this timeframe.
        default: 600


extends_documentation_fragment:
    - cloudgenix

author:
    - Aaron Edwards (@ebob9)
'''

EXAMPLES = '''
# Describe a Machine
- name: describe
  cloudgenix_machines:
    auth_token: "<AUTH_TOKEN>"
    operation: "describe"
    id: "<MACHINE_ID>"
  register: describe_machine_results

# Claim a Machine
- name: claim
  cloudgenix_machines:
    auth_token: "<AUTH_TOKEN>"
    operation: "claim"
    id: "<MACHINE_ID>"
  register: claim_machine_results

# Return a Machine
- name: return
  cloudgenix_machines:
    auth_token: "<AUTH_TOKEN>"
    operation: "return"
    id: "<MACHINE_ID>"
  register: return_machine_results

# Retire a Machine
- name: retire
  cloudgenix_machines:
    auth_token: "<AUTH_TOKEN>"
    operation: "retire"
    id: "<MACHINE_ID>"
  register: retire_machine_results

# Reuse a Machine
- name: reuse
  cloudgenix_machines:
    auth_token: "<AUTH_TOKEN>"
    operation: "reuse"
    id: "<MACHINE_ID>"
  register: reuse_machine_results

'''

RETURN = '''
operation:
    description: Operation that was executed
    type: string
    returned: always

id:
    description: Globally unique ID of the Machine.
    type: string
    returned: always

serial:
    description: Serial Number of the ION Machine.
    type: string
    returned: always

model_name:
    description: ION Model Name
    type: string
    returned: always

machine_state:
    description: Lifecycle state of the ION Machine
    type: string
    returned: always

image_version:
    description: ION Machine current image version.
    type: string
    returned: always

element_id:
    description: If machine_state is claimed, the assigned Element ID after claiming.
    type: string
    returned: always

connected:
    description: Current connection status of the machine. True = Online, False = Offline.
    type: bool
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
        operation=dict(choices=['claim', 'retire', 'return', 'describe'], required=True),
        id=dict(type='str', required=True),
        verify_success=dict(type='bool', required=False, default=True),
        wait_verify_success=dict(type='int', required=False, default=600),
        wait_if_offline=dict(type='int', required=False, default=300)
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
        serial='',
        model_name='',
        machine_state='',
        image_version='',
        element_id='',
        connected='',
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
    verify_success = module.params.get('verify_success')
    wait_verify_success = module.params.get('wait_verify_success')
    wait_if_offline = module.params.get('wait_if_offline')

    # get CloudGenix API connection details
    auth_token, controller, tenant_id, cgx_session = setup_cloudgenix_connection(module)

    # start logic.

    # check if Machine is new, changing, or being deleted.
    if operation == 'describe':

        # Get the object.
        machines_describe_response = cgx_session.get.machines(id)

        # Check for API failure
        if not machines_describe_response.cgx_status:
            result['meta'] = machines_describe_response.cgx_content
            module.fail_json(msg='Machines DESCRIBE failed.', **result)

        updated_machines_result = machines_describe_response.cgx_content

        # update result
        result = dict(
            changed=False,
            operation=operation,
            serial=updated_machines_result['sl_no'],
            model_name=updated_machines_result['model_name'],
            machine_state=updated_machines_result['machine_state'],
            image_version=updated_machines_result['image_version'],
            element_id=updated_machines_result.get('em_element_id', ''),
            connected=updated_machines_result['connected'],
            meta=machines_describe_response.cgx_content
        )

        # success
        module.exit_json(**result)

    elif operation == 'claim':
        # Claim the ION

        # verify ION is online
        connected = False
        time_elapsed = 0
        while not connected:
            # check online status
            machines_describe_response = cgx_session.get.machines(id)
            if machines_describe_response.cgx_status:
                connected = machines_describe_response.cgx_content.get('connected', False)

            if time_elapsed > wait_if_offline:
                result['meta'] = machines_describe_response.cgx_content
                module.fail_json(msg='ION wait_if_offline time exceeded', **result)

            if not connected:
                time.sleep(10)
                time_elapsed += 10

        # Got here, means ION is online.
        # cgx Machine template
        machines_claim = {
            "inventory_op": "claim"
        }

        # Attempt to claim Machine
        machines_claim_response = cgx_session.post.tenant_machine_operations(id, machines_claim)

        if not machines_claim_response.cgx_status:
            result['meta'] = machines_claim_response.cgx_content
            module.fail_json(msg='Machine CLAIM failed.', **result)

        updated_machines_result = machines_claim_response.cgx_content

        # update result
        result = dict(
            changed=True,
            operation=operation,
            serial=updated_machines_result['sl_no'],
            model_name=updated_machines_result['model_name'],
            machine_state=updated_machines_result['machine_state'],
            image_version=updated_machines_result['image_version'],
            element_id=updated_machines_result.get('em_element_id', ''),
            connected=updated_machines_result['connected'],
            meta=machines_claim_response.cgx_content
        )

        if verify_success:
            # wait and make sure that the ION moves to "claimed" state.
            claimed = False
            time_elapsed = 0
            machine_state = updated_machines_result['machine_state']
            while not claimed:
                # check online status
                machines_describe_response = cgx_session.get.machines(id)
                if machines_describe_response.cgx_status:
                    machine_state = machines_describe_response.cgx_content.get('machine_state')
                    # update machine state to latest in result.
                    result['machine_state'] = machine_state
                    # Update claimed
                    if machine_state.lower() in ['claimed']:
                        claimed = True
                    else:
                        claimed = False

                if time_elapsed > wait_verify_success:
                    # failed waiting.
                    result['meta'] = machines_describe_response.cgx_content
                    module.fail_json(msg='ION wait_verify_success time exceeded.', **result)

                if not claimed:
                    time.sleep(10)
                    time_elapsed += 10

        # success
        module.exit_json(**result)

    elif operation in ['retire', 'return', 'reuse']:
        # Retire the ION

        # Got here, means ION is online.
        # cgx Machine template
        machines_op = {
            "inventory_op": operation
        }

        # Attempt to declaim Machine
        machines_declaim_response = cgx_session.post.tenant_machine_operations(id, machines_op)

        if not machines_declaim_response.cgx_status:
            result['meta'] = machines_declaim_response.cgx_content
            module.fail_json(msg='Machine {0} failed.'.format(operation.upper()), **result)

        # on declaim, machines API does not return machine info. Query that now.
        machines_describe_response = cgx_session.get.machines(id)

        if not machines_describe_response.cgx_status:
            result['meta'] = machines_declaim_response.cgx_content
            module.fail_json(msg='Machine DESCRIBE after {0} failed.'.format(operation.upper()), **result)

        updated_machines_result = machines_describe_response.cgx_content

        # update result
        result = dict(
            changed=True,
            operation=operation,
            serial=updated_machines_result['sl_no'],
            model_name=updated_machines_result['model_name'],
            machine_state=updated_machines_result['machine_state'],
            image_version=updated_machines_result['image_version'],
            element_id=updated_machines_result.get('em_element_id', ''),
            connected=updated_machines_result['connected'],
            meta=machines_declaim_response.cgx_content
        )

        if verify_success:
            # wait and make sure that the ION moves to correct state.
            status_resp = False
            time_elapsed = 0
            while not status_resp:
                # check online status
                machines_describe_response = cgx_session.get.machines(id)
                if machines_describe_response.cgx_status:
                    machine_state = machines_describe_response.cgx_content.get('machine_state')
                    # update machine state to latest in result.
                    result['machine_state'] = machine_state
                    # Update status_resp
                    if operation in ['retire'] and machine_state.lower() in ['retired']:
                        status_resp = True
                    elif operation in ['return'] and machine_state.lower() in ['to_be_returned']:
                        status_resp = True
                    elif operation in ['reuse'] and machine_state.lower() in ['allocated']:
                        status_resp = True
                    else:
                        status_resp = False

                if time_elapsed > wait_verify_success:
                    # failed waiting.
                    result['meta'] = machines_describe_response.cgx_content
                    module.fail_json(msg='ION wait_verify_success time exceeded.', **result)

                if not status_resp:
                    time.sleep(10)
                    time_elapsed += 10

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
