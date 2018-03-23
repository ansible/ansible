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
module: cloudgenix_vff_licenses

short_description: "Describe a CloudGenix VFF License"

version_added: "2.6"

description:
    - "Describe a CloudGenix Virtual Form Factor (VFF) License object."

options:
    operation:
        description:
            - The operation you would like to perform on the VFF License object
        choices: ['describe']
        required: True

    id:
        description:
            - Globally unique ID of the object. Required if operation set to "describe".

extends_documentation_fragment:
    - cloudgenix

author:
    - Aaron Edwards (@ebob9)
'''

EXAMPLES = '''
# Retrieve a vff_license
- name: describe vff_license
  cloudgenix_vff_licenses:
    auth_token: "<AUTH_TOKEN>"
    operation: "describe"
    id: "<VFF_LICENSE_ID>"
  register: describe_results

'''

RETURN = '''
operation:
    description: Operation that was executed
    type: string
    returned: always

allowed_ions:
    description: Number of allowed instantiated instances of this license.
    type: int
    returned: always

id:
    description: Globally unique ID of the object
    type: string
    returned: always

model:
    description: ION Model that this VFF License is for.
    type: string
    returned: always

deployed_ions:
    description: Currently deployed IONs counting against this license.
    type: int
    returned: if available, or None.

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
        operation=dict(choices=['describe'], required=True),
        id=dict(type='str', required=False, default=None),
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
        allowed_ions='',
        id='',
        model='',
        deployed_ions='',
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

    # check if vff_license is new, changing, or being deleted.
    if operation == 'describe':

        # Check for id as required for new vff_license.
        if id is None:
            module.fail_json(msg='"id" is a required to describe a VFF License.', **result)

        # Get the object.
        vff_licenses_describe_response = cgx_session.get.vfflicenses(id)

        # Check for API failure
        if not vff_licenses_describe_response.cgx_status:
            result['meta'] = vff_licenses_describe_response.cgx_content
            module.fail_json(msg='VFF License {0} DESCRIBE failed.'.format(id), **result)

        updated_vff_license_result = vff_licenses_describe_response.cgx_content

        # update result
        result = dict(
            changed=False,
            operation=operation,
            allowed_ions=updated_vff_license_result['allowed_ions'],
            id=updated_vff_license_result['id'],
            model=updated_vff_license_result['model'],
            meta=vff_licenses_describe_response.cgx_content
        )

        # attempt to grab VFF License Status API to populate the deployed_ions.
        vff_license_status_describe_response = cgx_session.get.vfflicense_status(id)
        if vff_license_status_describe_response.cgx_status:
            result['deployed_ions'] = vff_license_status_describe_response.cgx_content.get('deployed_ions', '')

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
