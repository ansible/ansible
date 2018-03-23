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
module: cloudgenix_edgeroutepeers

short_description: "Create, Modify, Describe, or Delete CloudGenix Edge Route Peers"

version_added: "2.6"

description:
    - "Create, Modify, Describe, or Delete a CloudGenix Edge Route Peering objects."

options:
    operation:
        description:
            - The operation you would like to perform on the edgeroutepeer object
        choices: ['create', 'modify', 'describe', 'delete']
        required: True

    site:
        description:
            - Site ID that this Edge Route Peer is configured in.
        required: True

    id:
        description:
            - Globally unique ID of the object. Required if operation set to "modify", "describe" or "delete".

    peer_config:
        description:
            - Complex object representing the the Edge Route Peer configuration.

extends_documentation_fragment:
    - cloudgenix

author:
    - Aaron Edwards (@ebob9)
'''

EXAMPLES = '''
# Create a Edge Route peer
- name: Create a Edge Route peer
  cloudgenix_edgeroutepeers:
    auth_token: "<AUTH_TOKEN>"
    operation: "create"
    site: "<SITE_ID>"
    peer_config:
      peer_ip: "6.6.6.9"
      protocol: "EBGP"
      bgp_config:
        hold_time:
        keepalive_time:
        local_as_num: 53366
        md5_secret:
        peer_retry_time:
        remote_as_num: 1010
  register:
      create_edge_route_peers

# Retrieve a Edge Route peer
- name: Describe a Edge Route peer
  cloudgenix_edgeroutepeers:
    auth_token: "<AUTH_TOKEN>"
    operation: "describe"
    site: "<SITE_ID>"
    id: "<EDGE_ROUTE_PEER_ID>"
  register:
      describe_edge_route_peers

# Modify a Edge Route peer
- name: Modify a Edge Route peer
  cloudgenix_edgeroutepeers:
    auth_token: "<AUTH_TOKEN>"
    operation: "describe"
    site: "<SITE_ID>"
    id: "{{ create_edge_route_peers.id }}"
    peer_config:
      peer_ip: "6.6.6.10"
      protocol: "EBGP"
      bgp_config:
        hold_time:
        keepalive_time:
        local_as_num: 53366
        md5_secret:
        peer_retry_time: 130
        remote_as_num: 1010
  register:
      modify_edge_route_peers

# Delete a Edge Route peer
- name: Delete Edge peer
  cloudgenix_edgeroutepeers:
    auth_token: "<AUTH_TOKEN>"
    operation: "delete"
    site: 15065345556770063
    id: "{{ create_edge_route_peers.id }}"
  register:
      delete_edge_route_peers
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

peer_config:
    description: Complex object representing the the Edge Route Peer configuration.
    type: dictionary
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
        operation=dict(choices=['create', 'modify', 'describe', 'delete'], required=True),
        site=dict(type='str', required=True),
        id=dict(type='str', required=False, default=None),
        peer_config=dict(type='dict', required=False, default=None),
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
        id='',
        peer_config='',
        meta={},
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        return result

    # extract the params to shorter named vars.
    operation = module.params.get('operation')
    site = module.params.get('site')
    id = module.params.get('id')
    peer_config = module.params.get('peer_config')

    # get CloudGenix API connection details
    auth_token, controller, tenant_id, cgx_session = setup_cloudgenix_connection(module)

    # start logic.

    # check if edgeroutepeer is new, changing, or being deleted.
    if operation == 'describe':

        # Check for id as required for new edgeroutepeer.
        if id is None:
            module.fail_json(msg='"id" is a required to describe a Edge Route Peer.', **result)

        # Get the object.
        edgeroutepeers_describe_response = cgx_session.get.edgeroutepeers(site, id)

        # Check for API failure
        if not edgeroutepeers_describe_response.cgx_status:
            result['meta'] = edgeroutepeers_describe_response.cgx_content
            module.fail_json(msg='Edge Route Peer ID {0} DESCRIBE failed.'.format(id), **result)

        updated_edgeroutepeer_result = edgeroutepeers_describe_response.cgx_content

        # update result
        result = dict(
            changed=False,
            operation=operation,
            id=updated_edgeroutepeer_result['id'],
            peer_config=updated_edgeroutepeer_result['peer_config'],
            meta=edgeroutepeers_describe_response.cgx_content
        )

        # success
        module.exit_json(**result)

    elif operation == 'create':
        # new edgeroutepeer request!

        # Check for name as required for new edgeroutepeer.
        if not isinstance(peer_config, dict):
            module.fail_json(msg='a valid "peer_config" dictionary is required for Edge Route Peer creation.', **result)

        # cgx edgeroutepeer template
        new_edgeroutepeer = dict()
        new_edgeroutepeer['peer_config'] = peer_config

        # Attempt to create edgeroutepeer
        edgeroutepeers_create_response = cgx_session.post.edgeroutepeers(site, new_edgeroutepeer)

        if not edgeroutepeers_create_response.cgx_status:
            result['meta'] = edgeroutepeers_create_response.cgx_content
            module.fail_json(msg='Edge Route Peer CREATE failed.', **result)

        updated_edgeroutepeer_result = edgeroutepeers_create_response.cgx_content

        # update result
        result = dict(
            changed=True,
            operation=operation,
            id=updated_edgeroutepeer_result['id'],
            peer_config=updated_edgeroutepeer_result['peer_config'],
            meta=edgeroutepeers_create_response.cgx_content
        )

        # success
        module.exit_json(**result)

    elif operation == 'modify':

        # Check for id as required for new edgeroutepeer.
        # Check for name as required for new edgeroutepeer.
        if not isinstance(peer_config, dict):
            module.fail_json(msg='a valid "peer_config" dictionary is required for Edge Route Peer modification.',
                             **result)

        if id is None:
            module.fail_json(msg='"id" is a required value for Edge Route Peer modification.', **result)

        # Get the object.
        edgeroutepeers_response = cgx_session.get.edgeroutepeers(site, id)

        # if edgeroutepeer get fails, fail module.
        if not edgeroutepeers_response.cgx_status:
            result['meta'] = edgeroutepeers_response.cgx_content
            module.fail_json(msg='Edge Route Peer ID {0} retrieval failed.'.format(id), **result)
        # pull the edgeroutepeer out of the Response
        updated_edgeroutepeer = edgeroutepeers_response.cgx_content

        updated_edgeroutepeer['peer_config'] = peer_config

        # Attempt to modify edgeroutepeer
        edgeroutepeers_update_response = cgx_session.put.edgeroutepeers(site, id, updated_edgeroutepeer)

        if not edgeroutepeers_update_response.cgx_status:
            result['meta'] = edgeroutepeers_update_response.cgx_content
            module.fail_json(msg='Edge Route Peer ID {0} UPDATE failed.'.format(id), **result)

        updated_edgeroutepeer_result = edgeroutepeers_update_response.cgx_content

        # update result
        result = dict(
            changed=True,
            operation=operation,
            id=updated_edgeroutepeer_result['id'],
            peer_config=updated_edgeroutepeer_result['peer_config'],
            meta=edgeroutepeers_update_response.cgx_content
        )

        # success
        module.exit_json(**result)

    elif operation == 'delete':
        # Delete edgeroutepeer request. Verify ID was passed.
        if id is None:
            module.fail_json(msg='Edge Route Peer ID not set and required for delete Edge Route Peer operation.')

        else:
            # Attempt to delete edgeroutepeer
            edgeroutepeers_delete_response = cgx_session.delete.edgeroutepeers(site, id)

            if not edgeroutepeers_delete_response.cgx_status:
                result['meta'] = edgeroutepeers_delete_response.cgx_content
                module.fail_json(msg='Edge Route Peer  DELETE failed.', **result)

            # update result
            result['changed'] = True
            result['meta'] = edgeroutepeers_delete_response.cgx_content

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
