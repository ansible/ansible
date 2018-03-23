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
module: cloudgenix_elements

short_description: "Modify or Describe CloudGenix Elements"

version_added: "2.6"

description:
    - "Modify or Describe a CloudGenix element object."

options:
    operation:
        description:
            - The operation you would like to perform on the element object
        choices: ['modify', 'describe']
        required: True

    id:
        description:
            - Globally unique ID of the object.
        required: True

    cluster_insertion_mode:
        description:
            - Set the insertion mode for the hub cluster.
        choices: ['auto', 'manual']

    cluster_member_id:
        description:
            - Existing hub cluster member id for this element to assume.

    name:
        description:
            - Name of the element.

    description:
        description:
            - Description of the element. Maximum 256 chars.

    site_id:
        description:
            - Site ID to bind this element to.

extends_documentation_fragment:
    - cloudgenix

author:
    - Aaron Edwards (@ebob9)
'''

EXAMPLES = '''
# Retrieve a element
- name: describe element
  cloudgenix_elements:
    auth_token: "<AUTH_TOKEN>"
    operation: "describe"
    id: "<ELEMENT_ID>"
  register: describe_results

# Assign an element to a DC site and give a description.
- name: assign element to dc
  cloudgenix_elements:
    auth_token: "<AUTH_TOKEN>"
    operation: "modify"
    id: "<ELEMENT_ID>"
    site_id: "<DC_SITE_ID>"
    cluster_insertion_mode: "auto"
    description: "Shiny happy description holding hands"
  register: modify_results

# Assign an element to a DC site and give a name.
- name: assign element to branch
  cloudgenix_elements:
    auth_token: "<AUTH_TOKEN>"
    operation: "modify"
    id: "<ELEMENT_ID>"
    site_id: "<BRANCH_SITE_ID>"
    name: "My little branch 01"
  register: modify_results

'''

RETURN = '''
operation:
    description: Operation that was executed
    type: string
    returned: always

role:
    description: Role of the element.
    type: string
    returned: always

state:
    description: State of the element.
    type: string
    returned: always

name:
    description: Name of the element
    type: string
    returned: always

id:
    description: Globally unique ID of the object. ID is REQUIRED for all element operations as there is no
                 'create' option for elements. (Elements are claimed Machines.)
    type: string
    returned: always

site_id:
    description: Site ID this element is bound to, if any.
    type: string
    returned: always

description:
    description: Description of the element.
    type: string
    returned: always

hw_id:
    description: Hardware ID of the Element.
    type: string
    returned: always

serial_number:
    description: Serial number of the Element.
    type: string
    returned: always

model_name:
    description: Model Name of the Element.
    type: string
    returned: always

allowed_roles:
    description: List of allowed roles this Element can assume.
    type: list
    returned: always

cluster_insertion_mode:
    description: Hub Cluster insertion mode.
    type: string
    returned: always

cluster_member_id:
    description: Hub Cluster member ID.
    type: string
    returned: always

connected:
    description: Currently connected status of this Element.
    type: bool
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

# Until fix of CGB-8998, element objects require cleanup.
VALID_ELEMENT_KEYS = [
    "_etag",
    "_schema",
    "cluster_insertion_mode",
    "cluster_member_id",
    "description",
    "id",
    "name",
    "site_id",
    "sw_obj"
]


def run_module():
    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = cloudgenix_common_arguments()
    module_args.update(dict(
        operation=dict(choices=['modify', 'describe'], required=True),
        id=dict(type='str', required=True),
        cluster_insertion_mode=dict(choices=['auto', 'manual'], required=False, default=None),
        cluster_member_id=dict(type='str', required=False, default=None),
        name=dict(type='str', required=False, default=None),
        description=dict(type='str', required=False, default=None),
        site_id=dict(type='str', required=False, default=None)
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
        role='',
        state='',
        name='',
        id='',
        site_id='',
        description='',
        hw_id='',
        serial_number='',
        model_name='',
        allowed_roles='',
        cluster_insertion_mode='',
        cluster_member_id='',
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
    cluster_insertion_mode = module.params.get('cluster_insertion_mode')
    cluster_member_id = module.params.get('cluster_member_id')
    name = module.params.get('name')
    description = module.params.get('description')
    site_id = module.params.get('site_id')

    # get CloudGenix API connection details
    auth_token, controller, tenant_id, cgx_session = setup_cloudgenix_connection(module)

    # start logic.

    # check if element is new, changing, or being deleted.
    if operation == 'describe':

        # Check for id as required for new element.
        if id is None:
            module.fail_json(msg='"id" is a required to describe an Element.', **result)

        # Get the object.
        elements_describe_response = cgx_session.get.elements(id)

        # Check for API failure
        if not elements_describe_response.cgx_status:
            result['meta'] = elements_describe_response.cgx_content
            module.fail_json(msg='Element ID {0} DESCRIBE failed.'.format(id), **result)

        updated_element_result = elements_describe_response.cgx_content

        # update result
        result = dict(
            changed=False,
            operation=operation,
            role=updated_element_result['role'],
            state=updated_element_result['state'],
            name=updated_element_result['name'],
            id=updated_element_result['id'],
            site_id=updated_element_result['site_id'],
            description=updated_element_result['description'],
            hw_id=updated_element_result['hw_id'],
            serial_number=updated_element_result['serial_number'],
            model_name=updated_element_result['model_name'],
            allowed_roles=updated_element_result['allowed_roles'],
            cluster_insertion_mode=updated_element_result['cluster_insertion_mode'],
            cluster_member_id=updated_element_result['cluster_member_id'],
            connected=updated_element_result['connected'],
            meta=elements_describe_response.cgx_content
        )

        # success
        module.exit_json(**result)

    elif operation == 'modify':

        # Check for id as required for new element.
        if id is None:
            module.fail_json(msg='"id" is a required value for element modification.', **result)

        # Get the object.
        elements_response = cgx_session.get.elements(id)

        # if element get fails, fail module.
        if not elements_response.cgx_status:
            result['meta'] = elements_response.cgx_content
            module.fail_json(msg='Element ID {0} retrieval failed.'.format(id), **result)
        # pull the element out of the Response
        updated_element = elements_response.cgx_content

        # modify the element
        if name is not None:
            updated_element['name'] = name
        if site_id is not None:
            updated_element['site_id'] = site_id
        if description is not None:
            updated_element['description'] = description
        if cluster_insertion_mode is not None:
            updated_element['cluster_insertion_mode'] = cluster_insertion_mode
        if cluster_member_id is not None:
            updated_element['cluster_member_id'] = cluster_member_id

        # Sanity check element object for invalid/unused fields
        remove_keys = []
        for key, value in updated_element.items():
            if key not in VALID_ELEMENT_KEYS:
                remove_keys.append(key)
        # Remove keys
        for key in remove_keys:
            updated_element.pop(key, None)
        # Add sw_obj
        updated_element['sw_obj'] = None

        # Attempt to modify element
        elements_update_response = cgx_session.put.elements(id, updated_element)

        if not elements_update_response.cgx_status:
            result['meta'] = elements_update_response.cgx_content
            module.fail_json(msg='Element ID {0} UPDATE failed.'.format(id), **result)

        updated_element_result = elements_update_response.cgx_content

        # update result
        result = dict(
            changed=True,
            operation=operation,
            role=updated_element_result['role'],
            state=updated_element_result['state'],
            name=updated_element_result['name'],
            id=updated_element_result['id'],
            site_id=updated_element_result['site_id'],
            description=updated_element_result['description'],
            hw_id=updated_element_result['hw_id'],
            serial_number=updated_element_result['serial_number'],
            model_name=updated_element_result['model_name'],
            allowed_roles=updated_element_result['allowed_roles'],
            cluster_insertion_mode=updated_element_result['cluster_insertion_mode'],
            cluster_member_id=updated_element_result['cluster_member_id'],
            connected=updated_element_result['connected'],
            meta=elements_update_response.cgx_content
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
