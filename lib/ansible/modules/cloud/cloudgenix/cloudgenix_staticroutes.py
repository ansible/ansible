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
module: cloudgenix_staticroutes

short_description: "Create, Modify, Describe, or Delete a CloudGenix Element Static Route."

version_added: "2.6"

description:
    - "Create, Modify, Describe, or Delete a CloudGenix Element Static Route."

options:
    operation:
        description:
            - The operation you would like to perform on the Static Route object
        choices: ['create', 'modify', 'describe', 'delete']
        required: True

    site:
        description:
            - Site ID that the Element containing this Static Route is assigned to.
        required: True

    element:
        description:
            - Element ID that this Static Route is attached to.
        required: True
    id:
        description:
            - Globally unique ID of the object. Required if operation set to "modify", "describe" or "delete".

    network_context_id:
        description:
            - The Network Isolation Context ID, used to bind distinct isolation policy behavior to traffic from this network.

    scope:
        description:
            - Scope of the Static Route - Globaly reachable, or local only to this site.
        choices: ['global', 'local']

    destination_prefix:
        description:
            - Destination IP Prefix, in "A.B.C.D/E" format. Required if operation is set to "create".

    nexthops:
        description:
            - List of complex objects describing the next-hop configuration for this Static Route.

    description:
        description:
            - Description of the Static Route. Maximum 256 chars.

    tags:
        description:
            - List of strings to be used as identifying tags for this route.

extends_documentation_fragment:
    - cloudgenix

author:
    - Aaron Edwards (@ebob9)
'''

EXAMPLES = '''

# Create a Static Route
- name: create an static route
  cloudgenix_staticroutes:
    auth_token: "<AUTH_TOKEN>"
    operation: "create"
    site: "<SITE_ID>"
    element: "<ELEMENT_ID>"
    description: "Auto Created Route"
    destination_prefix: "4.5.6.7/32"
    scope: "global"
    nexthops:
      - admin_distance: 1
        nexthop_interface_id: "<SOURCE_INTERFACE_ID>"
        nexthop_ip: "10.200.2.5"
        self: False
  register: create_results

# Retrieve a Static Route
- name: describe modified static route
  cloudgenix_staticroutes:
    auth_token: "<AUTH_TOKEN>"
    operation: "describe"
    site: "<SITE_ID>"
    element: "<ELEMENT_ID>"
    id: "<STATIC_ROUTE_ID>"
  register: describe_results

# Modify a Static Route
- name: Modify an staticroute
  cloudgenix_staticroutes:
    auth_token: "<AUTH_TOKEN>"
    operation: "modify"
    site: "<SITE_ID>"
    element: "<ELEMENT_ID>"
    id: "<STATIC_ROUTE_ID>"
    description: "Change Static Route Description to this."
  register: modify_results

# Delete a Static Route
- name: Delete an staticroute
  cloudgenix_staticroutes:
    auth_token: "<AUTH_TOKEN>"
    operation: "delete"
    site: "<SITE_ID>"
    element: "<ELEMENT_ID>"
    id: "<STATIC_ROUTE_ID>"
'''

RETURN = '''
operation:
    description: Operation that was executed
    type: string
    returned: always

site:
    description: Site ID that the Element with this Static Route is located at.
    type: string
    returned: always

element:
    description: Element ID that this staticroute is bound with.
    type: string
    returned: always

id:
    description: Globally unique ID of the Static Route. Required if operation set to "modify", "describe" or "delete".
    type: string
    returned: always

network_context_id:
    description: Network Context ID bound to this LAN Network.
    type: string
    returned: always

scope:
    description: Global or Local scope of the LAN Network.
    type: string
    returned: always

destination_prefix:
    description: IP/Prefix of the Static Route destination, in "A.B.C.D/E" format.
    type: string
    returned: always

nexthops:
    description: List of complex objects describing the next-hop configuration for this Static Route.
    type: list
    returned: always

description:
    description: Description of the Static Route. Maximum 256 chars.
    type: string
    returned: always

tags:
    description: List of strings to be used as identifying tags for this route.
    type: list
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
        site=dict(type=str, required=True),
        element=dict(type=str, required=True),
        id=dict(type=str, required=False, default=None),
        network_context_id=dict(type='str', required=False, default=None),
        scope=dict(choices=['global', 'local'], required=False, default=None),
        destination_prefix=dict(type=str, required=False, default=None),
        nexthops=dict(type=list, required=False, default=None),
        description=dict(type=str, required=False, default=None),
        tags=dict(type=list, required=False, default=None)
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
        site='',
        element='',
        id='',
        network_context_id='',
        scope='',
        destination_prefix='',
        nexthops='',
        description='',
        tags='',
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
    element = module.params.get('element')
    id = module.params.get('id')
    network_context_id = module.params.get('network_context_id')
    scope = module.params.get('scope')
    destination_prefix = module.params.get('destination_prefix')
    nexthops = module.params.get('nexthops')
    description = module.params.get('description')
    tags = module.params.get('tags')

    # get CloudGenix API connection details
    auth_token, controller, tenant_id, cgx_session = setup_cloudgenix_connection(module)

    # start logic.

    # check if Static Route is new, changing, or being deleted.
    if operation == 'describe':

        # Check for id as required for describe Static Route.
        if any(field is None for field in [site, element, id]):
            module.fail_json(msg='"site", "element", and "id" are required to describe a Static Route.', **result)

        # Get the object.
        staticroutes_describe_response = cgx_session.get.staticroutes(site, element, id)

        # Check for API failure
        if not staticroutes_describe_response.cgx_status:
            result['meta'] = staticroutes_describe_response.cgx_content
            module.fail_json(msg='Static Route DESCRIBE failed.', **result)

        updated_staticroutes_result = staticroutes_describe_response.cgx_content

        # update result
        result = dict(
            changed=False,
            operation=operation,
            site=updated_staticroutes_result.get('site'),
            element=updated_staticroutes_result.get('element'),
            id=updated_staticroutes_result.get('id'),
            network_context_id=updated_staticroutes_result.get('network_context_id'),
            scope=updated_staticroutes_result.get('scope'),
            destination_prefix=updated_staticroutes_result.get('destination_prefix'),
            nexthops=updated_staticroutes_result.get('nexthops'),
            description=updated_staticroutes_result.get('description'),
            tags=updated_staticroutes_result.get('tags'),
            meta=staticroutes_describe_response.cgx_content
        )

        # success
        module.exit_json(**result)

    elif operation == 'create':
        # new Static Route request!

        # Check for new Static Route required fields.
        if any(field is None for field in [site, element, destination_prefix, nexthops, scope]):
            module.fail_json(msg='"site", "element", and "destination_prefix", "nexthops", and "scope" are required '
                                 'at a minimum for Static Route creation.', **result)

        # cgx Static Route template
        updated_staticroute = {
            "description": None,
            "destination_prefix": None,
            "network_context_id": None,
            "nexthops": [],
            "scope": None,
            "tags": []
        }

        if id is not None:
            updated_staticroute['id'] = id
        if network_context_id is not None:
            updated_staticroute['network_context_id'] = network_context_id
        if scope is not None:
            updated_staticroute['scope'] = scope
        if destination_prefix is not None:
            updated_staticroute['destination_prefix'] = destination_prefix
        if nexthops is not None:
            updated_staticroute['nexthops'] = nexthops
        if description is not None:
            updated_staticroute['description'] = description
        if tags is not None:
            updated_staticroute['tags'] = tags

        # Attempt to create Static Route
        staticroutes_create_response = cgx_session.post.staticroutes(site, element, updated_staticroute)

        if not staticroutes_create_response.cgx_status:
            result['meta'] = staticroutes_create_response.cgx_content
            module.fail_json(msg='Static Route CREATE failed.', **result)

        updated_staticroutes_result = staticroutes_create_response.cgx_content

        # update result
        result = dict(
            changed=True,
            operation=operation,
            site=updated_staticroutes_result.get('site'),
            element=updated_staticroutes_result.get('element'),
            id=updated_staticroutes_result.get('id'),
            network_context_id=updated_staticroutes_result.get('network_context_id'),
            scope=updated_staticroutes_result.get('scope'),
            destination_prefix=updated_staticroutes_result.get('destination_prefix'),
            nexthops=updated_staticroutes_result.get('nexthops'),
            description=updated_staticroutes_result.get('description'),
            tags=updated_staticroutes_result.get('tags'),
            meta=staticroutes_create_response.cgx_content
        )

        # success
        module.exit_json(**result)

    elif operation == 'modify':

        # Check for id as required for new Static Route.
        if any(field is None for field in [site, element, id]):
            module.fail_json(msg='"site", "element" and "id" are required values for Static Route modification.', **result)

        # Get the object.
        staticroutes_response = cgx_session.get.staticroutes(site, element, id)

        # if Static Route get fails, fail module.
        if not staticroutes_response.cgx_status:
            result['meta'] = staticroutes_response.cgx_content
            module.fail_json(msg='Static Route ID {0} retrieval failed.'.format(id), **result)
        # pull the Static Route out of the Response
        updated_staticroute = staticroutes_response.cgx_content

        # modify the Static Route
        if id is not None:
            updated_staticroute['id'] = id
        if network_context_id is not None:
            updated_staticroute['network_context_id'] = network_context_id
        if scope is not None:
            updated_staticroute['scope'] = scope
        if destination_prefix is not None:
            updated_staticroute['destination_prefix'] = destination_prefix
        if nexthops is not None:
            updated_staticroute['nexthops'] = nexthops
        if description is not None:
            updated_staticroute['description'] = description
        if tags is not None:
            updated_staticroute['tags'] = tags

        # Attempt to modify Static Route
        staticroutes_update_response = cgx_session.put.staticroutes(site, element, id, updated_staticroute)

        if not staticroutes_update_response.cgx_status:
            result['meta'] = staticroutes_update_response.cgx_content
            module.fail_json(msg='Static Route ID {0} UPDATE failed.'.format(id), **result)

        updated_staticroutes_result = staticroutes_update_response.cgx_content

        # update result
        result = dict(
            changed=True,
            operation=operation,
            site=updated_staticroutes_result.get('site'),
            element=updated_staticroutes_result.get('element'),
            id=updated_staticroutes_result.get('id'),
            network_context_id=updated_staticroutes_result.get('network_context_id'),
            scope=updated_staticroutes_result.get('scope'),
            destination_prefix=updated_staticroutes_result.get('destination_prefix'),
            nexthops=updated_staticroutes_result.get('nexthops'),
            description=updated_staticroutes_result.get('description'),
            tags=updated_staticroutes_result.get('tags'),
            meta=staticroutes_update_response.cgx_content
        )

        # success
        module.exit_json(**result)

    elif operation == 'delete':
        # Delete Static Route request. Verify ID was passed.
        if any(field is None for field in [site, element, id]):
            module.fail_json(msg='"site", "element" or "id" not set, all are required for delete '
                                 'Static Route operation.')

        else:
            # Attempt to delete Static Route
            staticroutes_delete_response = cgx_session.delete.staticroutes(site, element, id)

            if not staticroutes_delete_response.cgx_status:
                result['meta'] = staticroutes_delete_response.cgx_content
                module.fail_json(msg='Static Route DELETE failed.', **result)

            # update result
            result['changed'] = True
            result['meta'] = staticroutes_delete_response.cgx_content

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
