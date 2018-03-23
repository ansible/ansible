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
module: cloudgenix_lannetworks

short_description: "Create, Modify, Describe, or Delete CloudGenix LAN networks"

version_added: "2.6"

description:
    - "Create, Modify, Describe, or Delete a CloudGenix LAN networks."

options:
    operation:
        description:
            - The operation you would like to perform on the LAN Network object
        choices: ['create', 'modify', 'describe', 'delete']
        required: True

    site:
        description:
            - Site ID that this LAN Network is located at.
        required: True

    name:
        description:
            - Name of the LAN Network. Required if operation set to "create".

    id:
        description:
            - Globally unique ID of the object. Required if operation set to "modify", "describe" or "delete".

    scope:
        description:
            - Scope of the LAN Network - Globaly reachable, or local only to this site.
        choices: ['global', 'local']

    ipv4_config:
        description:
            - A dictionary describing the physical Ethernet hardware configuration for the interface.

    network_context_id:
        description:
            - The Network Isolation Context ID, used to bind distinct isolation policy behavior to traffic from this network.


extends_documentation_fragment:
    - cloudgenix

author:
    - Aaron Edwards (@ebob9)
'''

EXAMPLES = '''

# Create a LAN Network
- name: Create a lan network
  cloudgenix_lannetworks:
    operation: "create"
    auth_token: "<AUTH_TOKEN>"
    site: "<SITE_ID>"
    name: "Test_LAN_NETWORK1"
    ipv4_config:
      default_routers:
        - "10.4.100.1/24"
      prefixes:
      dhcp_relay:
      dhcp_server:
  register: create_lannetwork_results

# Modify a LAN Network
- name: Modify a lan network
  cloudgenix_lannetworks:
    operation: "modify"
    auth_token: "<AUTH_TOKEN>"
    site: "<SITE_ID>"
    id: "<LANNETWORK_ID>"
    name: "New LAN NETWORK Name"
  register: modify_lannetwork_results

# Retrieve a LAN Network
- name: Describe a lan network
  cloudgenix_lannetworks:
    operation: "describe"
    auth_token: "<AUTH_TOKEN>"
    site: "<SITE_ID>"
    id: "<LANNETWORK_ID>"
  register: describe_lannetwork_results

# Delete a LAN Network
- name: Delete a lan network
  cloudgenix_lannetworks:
    operation: "delete"
    auth_token: "<AUTH_TOKEN>"
    site: "<SITE_ID>"
    id: "<LANNETWORK_ID>"
  register: delete_lannetwork_results

'''

RETURN = '''
operation:
    description: Operation that was executed
    type: string
    returned: always

site:
    description: Site ID that this LAN Network is located at.
    type: string
    returned: always

name:
    description: Name of the LAN Network.
    type: string
    returned: always

id:
    description: Globally unique ID of the object
    type: string
    returned: always

scope:
    description: Global or Local scope of the LAN Network.
    type: string
    returned: always

ipv4_config:
    description: Complex object describing the IPv4 config of the LAN Network.
    type: dictionary
    returned: always

network_context_id:
    description: Network Context ID bound to this LAN Network.
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
        operation=dict(choices=['create', 'modify', 'describe', 'delete'], required=True),
        site=dict(type=str, required=True),
        name=dict(type='str', required=False, default=None),
        id=dict(type='str', required=False, default=None),
        scope=dict(choices=['global', 'local'], required=False, default=None),
        ipv4_config=dict(type='dict', required=False, default=None),
        network_context_id=dict(type='str', required=False, default=None)
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
        name='',
        id='',
        scope='',
        ipv4_config='',
        network_context_id='',
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
    name = module.params.get('name')
    id = module.params.get('id')
    scope = module.params.get('scope')
    ipv4_config = module.params.get('ipv4_config')
    network_context_id = module.params.get('network_context_id')

    # get CloudGenix API connection details
    auth_token, controller, tenant_id, cgx_session = setup_cloudgenix_connection(module)

    # start logic.

    # check if LAN Network is new, changing, or being deleted.
    if operation == 'describe':

        # Check for id as required for new LAN Network.
        if any(field is None for field in [site, id]):
            module.fail_json(msg='"site" and "id" are required to describe a LAN Network.', **result)

        # Get the object.
        lannetworks_describe_response = cgx_session.get.lannetworks(site, id)

        # Check for API failure
        if not lannetworks_describe_response.cgx_status:
            result['meta'] = lannetworks_describe_response.cgx_content
            module.fail_json(msg='WAN Network DESCRIBE failed.', **result)

        updated_lannetworks_result = lannetworks_describe_response.cgx_content

        # update result
        result = dict(
            changed=False,
            operation=operation,
            name=updated_lannetworks_result['name'],
            id=updated_lannetworks_result['id'],
            scope=updated_lannetworks_result['scope'],
            ipv4_config=updated_lannetworks_result['ipv4_config'],
            network_context_id=updated_lannetworks_result['network_context_id'],
            meta=lannetworks_describe_response.cgx_content
        )

        # success
        module.exit_json(**result)

    elif operation == 'create':
        # new LAN Network request!

        # Check for new LAN Network required fields.
        if any(field is None for field in [name, site]):
            module.fail_json(msg='"name", "site", are required for '
                                 'LAN Network creation.', **result)

        # cgx LAN Network template
        new_lannetwork = {
            "name": None,
            "scope": "global",
            "ipv4_config": None,
            "security_policy_set": None,
            "network_context_id": None
        }

        if name is not None:
            new_lannetwork['name'] = name
        if scope is not None:
            new_lannetwork['scope'] = scope
        if ipv4_config is not None:
            new_lannetwork['ipv4_config'] = ipv4_config
        if network_context_id is not None:
            new_lannetwork['network_context_id'] = network_context_id

        # Attempt to create LAN Network
        lannetworks_create_response = cgx_session.post.lannetworks(site, new_lannetwork)

        if not lannetworks_create_response.cgx_status:
            result['meta'] = lannetworks_create_response.cgx_content
            module.fail_json(msg='LAN Network CREATE failed.', **result)

        updated_lannetworks_result = lannetworks_create_response.cgx_content

        # update result
        result = dict(
            changed=True,
            operation=operation,
            name=updated_lannetworks_result['name'],
            id=updated_lannetworks_result['id'],
            scope=updated_lannetworks_result['scope'],
            ipv4_config=updated_lannetworks_result['ipv4_config'],
            network_context_id=updated_lannetworks_result['network_context_id'],
            meta=lannetworks_create_response.cgx_content
        )

        # success
        module.exit_json(**result)

    elif operation == 'modify':

        # Check for id as required for new LAN Network.
        if any(field is None for field in [site, id]):
            module.fail_json(msg='"site" and "id" is a required value for LAN Network modification.', **result)

        # Get the object.
        lannetworks_response = cgx_session.get.lannetworks(site, id)

        # if LAN Network get fails, fail module.
        if not lannetworks_response.cgx_status:
            result['meta'] = lannetworks_response.cgx_content
            module.fail_json(msg='LAN Network ID {0} retrieval failed.'.format(id), **result)
        # pull the LAN Network out of the Response
        updated_lannetwork = lannetworks_response.cgx_content

        # modify the LAN Network
        if name is not None:
            updated_lannetwork['name'] = name
        if scope is not None:
            updated_lannetwork['scope'] = scope
        if ipv4_config is not None:
            updated_lannetwork['ipv4_config'] = ipv4_config
        if network_context_id is not None:
            updated_lannetwork['network_context_id'] = network_context_id

        # Attempt to modify LAN Network
        lannetworks_update_response = cgx_session.put.lannetworks(site, id, updated_lannetwork)

        if not lannetworks_update_response.cgx_status:
            result['meta'] = lannetworks_update_response.cgx_content
            module.fail_json(msg='LAN Network ID {0} UPDATE failed.'.format(id), **result)

        updated_lannetworks_result = lannetworks_update_response.cgx_content

        # update result
        result = dict(
            changed=True,
            operation=operation,
            name=updated_lannetworks_result['name'],
            id=updated_lannetworks_result['id'],
            scope=updated_lannetworks_result['scope'],
            ipv4_config=updated_lannetworks_result['ipv4_config'],
            network_context_id=updated_lannetworks_result['network_context_id'],
            meta=lannetworks_update_response.cgx_content
        )

        # success
        module.exit_json(**result)

    elif operation == 'delete':
        # Delete LAN Network request. Verify ID was passed.
        if any(field is None for field in [site, id]):
            module.fail_json(msg='"site" or "id" not set, both are required for delete LAN Network operation.')

        else:
            # Attempt to delete LAN Network
            lannetworks_delete_response = cgx_session.delete.lannetworks(site, id)

            if not lannetworks_delete_response.cgx_status:
                result['meta'] = lannetworks_delete_response.cgx_content
                module.fail_json(msg='LAN Network DELETE failed.', **result)

            # update result
            result['changed'] = True
            result['meta'] = lannetworks_delete_response.cgx_content

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
