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
module: cloudgenix_vff_tokens

short_description: "Create, Revoke, or Describe CloudGenix VFF Tokens"

version_added: "2.6"

description:
    - "Create, Revoke, or Describe a CloudGenix Virtual Form Factor (VFF) authorization token object."

options:
    operation:
        description:
            - The operation you would like to perform on the VFF Token object
        choices: ['create', 'revoke', 'describe',]
        required: True

    id:
        description:
            - Globally unique ID of the object. Required if operation set to "describe" or "revoke".

    vff_license:
        description:
            - Globally unique ID of the VFF License this token exists under.
        required: True

    is_multiuse:
        description:
            - Is this token multi-use or single-use? Only applicable on 'create', can not be modified.
        choices: [True, False]
        default: True

extends_documentation_fragment:
    - cloudgenix

author:
    - Aaron Edwards (@ebob9)
'''

EXAMPLES = '''

# Revoke all currently valid VFF Token
- name: Revoke all currently valid tokens for a specific VFF License
  cloudgenix_vff_tokens:
    auth_token: "<AUTH_TOKEN>"
    operation: "revoke"
    vff_license: "<VFF_LICENSE_ID>"
    id: "{{ item.id }}"
  when:
    - item.is_expired == False
    - item.is_revoked == False
  with_cloudgenix:
    vff_tokens:
      vff_license: "<VFF_LICENSE_ID>"

# Create a VFF Token
- name: Create VFF Token
  cloudgenix_vff_tokens:
    auth_token: "<AUTH_TOKEN>"
    operation: "create"
    vff_license: "<VFF_LICENSE_ID>"
    is_multiuse: False
  register: create_token_results

# Describe a VFF Token
- name: Describe VFF Token
  cloudgenix_vff_tokens:
    auth_token: "<AUTH_TOKEN>"
    operation: "describe"
    id: "<VFF_TOKEN_ID>"
    vff_license: "<VFF_LICENSE_ID>"
  register: describe_token_results
'''

RETURN = '''
operation:
    description: Operation that was executed
    type: string
    returned: always

id:
    description: Globally unique ID of the object
    type: string
    returned: always

ion_key:
    description: ION Key string of the ION Key / Secret Key pair.
    type: string
    returned: always

secret_key:
    description: ION Key string of the ION Key / Secret Key pair.
    type: string
    returned: always

is_expired:
    description: Has this VFF Token expired?
    type: bool
    returned: always

is_multiuse:
    description: Is this VFF Token Multi-use?
    type: bool
    returned: always

is_revoked:
    description: Has this VFF Token been revoked?
    type: bool
    returned: always

is_used:
    description: Has this VFF Token been used?
    type: bool
    returned: always

valid_till_secs:
    description: UNIX timestamp when this token will expire
    type: int
    returned: always

vfflicense_id:
    description: Parent VFF License ID
    type: string
    returned: always

'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudgenix_util import (HAS_CLOUDGENIX, cloudgenix_common_arguments,
                                                  setup_cloudgenix_connection)

try:
    import cloudgenix
except ImportError:
    pass  # caught by imported HAS_CLOUDGENIX

# Until fix of CGB-8998, vfflicense_token objects require cleanup.
VALID_VFF_TOKEN_KEYS = [
    "_etag",
    "_schema",
    "is_revoked",
]


def run_module():
    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = cloudgenix_common_arguments()
    module_args.update(dict(
        operation=dict(choices=['create', 'revoke', 'describe'], required=True),
        id=dict(type='str', required=False, default=None),
        vff_license=dict(type='str', required=True),
        is_multiuse=dict(choices=[True, False], default=True),
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
        id='',
        ion_key='',
        secret_key='',
        is_expired='',
        is_multiuse='',
        is_revoked='',
        is_used='',
        valid_till_secs='',
        vfflicense_id='',
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
    vff_license = module.params.get('vff_license')
    is_multiuse = module.params.get('is_multiuse')

    # get CloudGenix API connection details
    auth_token, controller, tenant_id, cgx_session = setup_cloudgenix_connection(module)

    # start logic.

    # check if vff_token is new, changing, or being deleted.
    if operation == 'describe':

        # Check for id, vff_license as both are required for describe.
        if any(field is None for field in [id, vff_license]):
            module.fail_json(msg='"vff_license", and "id" are required to describe a VFF Token.', **result)

        # Get the object.
        vff_tokens_describe_response = cgx_session.get.vfflicense_tokens(vff_license, id)

        # Check for API failure
        if not vff_tokens_describe_response.cgx_status:
            result['meta'] = vff_tokens_describe_response.cgx_content
            module.fail_json(msg='VFF Token ID {0} DESCRIBE failed.'.format(id), **result)

        updated_vff_token_result = vff_tokens_describe_response.cgx_content

        # update result
        result = dict(
            changed=False,
            operation=operation,
            id=updated_vff_token_result['id'],
            ion_key=updated_vff_token_result['ion_key'],
            secret_key=updated_vff_token_result['secret_key'],
            is_expired=updated_vff_token_result['is_expired'],
            is_multiuse=updated_vff_token_result['is_multiuse'],
            is_revoked=updated_vff_token_result['is_revoked'],
            is_used=updated_vff_token_result['is_used'],
            valid_till_secs=updated_vff_token_result['valid_till_secs'],
            vfflicense_id=updated_vff_token_result['vfflicense_id'],
            meta=vff_tokens_describe_response.cgx_content
        )

        # success
        module.exit_json(**result)

    elif operation == 'create':
        # new vff_token request!

        # Check for id, vff_license and is_multiuse, as all are required for create.
        if any(field is None for field in [vff_license, is_multiuse]):
            module.fail_json(msg='"vff_license" is required to create a VFF Token.', **result)

        # cgx vff_token template
        new_vff_token = {
            "is_multiuse": is_multiuse
        }

        # Attempt to create vff_token
        vff_tokens_create_response = cgx_session.post.vfflicense_tokens(vff_license,
                                                                        new_vff_token)

        if not vff_tokens_create_response.cgx_status:
            result['meta'] = vff_tokens_create_response.cgx_content
            module.fail_json(msg='VFF Token CREATE failed.', **result)

        updated_vff_token_result = vff_tokens_create_response.cgx_content

        # update result
        result = dict(
            changed=True,
            operation=operation,
            id=updated_vff_token_result['id'],
            ion_key=updated_vff_token_result['ion_key'],
            secret_key=updated_vff_token_result['secret_key'],
            is_expired=updated_vff_token_result['is_expired'],
            is_multiuse=updated_vff_token_result['is_multiuse'],
            is_revoked=updated_vff_token_result['is_revoked'],
            is_used=updated_vff_token_result['is_used'],
            valid_till_secs=updated_vff_token_result['valid_till_secs'],
            vfflicense_id=updated_vff_token_result['vfflicense_id'],
            meta=vff_tokens_create_response.cgx_content
        )

        # success
        module.exit_json(**result)

    elif operation == 'revoke':

        # Check for id, vff_license as both are required for revoking a token.
        if any(field is None for field in [id, vff_license]):
            module.fail_json(msg='"vff_license", and "id" are required to revoke a VFF Token.', **result)

        # Get the object.
        vff_tokens_response = cgx_session.get.vfflicense_tokens(vff_license, id)

        # if vff_token get fails, fail module.
        if not vff_tokens_response.cgx_status:
            result['meta'] = vff_tokens_response.cgx_content
            module.fail_json(msg='VFF Token ID {0} DESCRIBE failed.'.format(id), **result)
        # pull the vff_token out of the Response
        updated_vff_token = vff_tokens_response.cgx_content

        updated_vff_token['is_revoked'] = True

        # Sanity check element object for invalid/unused fields
        remove_keys = []
        for key, value in updated_vff_token.items():
            if key not in VALID_VFF_TOKEN_KEYS:
                remove_keys.append(key)
        # Remove keys
        for key in remove_keys:
            updated_vff_token.pop(key, None)

        # Attempt to modify vff_token
        vff_tokens_update_response = cgx_session.put.vfflicense_tokens(vff_license, id, updated_vff_token)

        if not vff_tokens_update_response.cgx_status:
            result['meta'] = vff_tokens_update_response.cgx_content
            module.fail_json(msg='VFF Token ID {0} REVOKE failed.'.format(id), **result)

        updated_vff_token_result = vff_tokens_update_response.cgx_content

        # update result
        result = dict(
            changed=True,
            operation=operation,
            id=updated_vff_token_result['id'],
            ion_key=updated_vff_token_result['ion_key'],
            secret_key=updated_vff_token_result['secret_key'],
            is_expired=updated_vff_token_result['is_expired'],
            is_multiuse=updated_vff_token_result['is_multiuse'],
            is_revoked=updated_vff_token_result['is_revoked'],
            is_used=updated_vff_token_result['is_used'],
            valid_till_secs=updated_vff_token_result['valid_till_secs'],
            vfflicense_id=updated_vff_token_result['vfflicense_id'],
            meta=vff_tokens_update_response.cgx_content
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
