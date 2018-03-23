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
module: cloudgenix_waninterfaces

short_description: "Create, Modify, Describe, or Delete CloudGenix WAN interfaces"

version_added: "2.6"

description:
    - "Create, Modify, Describe, or Delete a CloudGenix WAN interfaces."

options:
    operation:
        description:
            - The operation you would like to perform on the WAN Interface object
        choices: ['create', 'modify', 'describe', 'delete']
        required: True

    site:
        description:
            - Site ID that this WAN Interface is located at.
        required: True

    name:
        description:
            - Name of the WAN Interface. Required if operation set to "create".

    description:
        description:
            - Description of the WAN Interface. Maximum 256 chars.

    id:
        description:
            - Globally unique ID of the object. Required if operation set to "modify", "describe" or "delete".

    bandwidth_config:
        description:
            - Bandwidth speed configuration and bandwidth monitoring (bwm) testing. 'auto' always has bwm enabled.
        choices: ['manual', 'manual_bwm_disabled', 'auto']

    qos:
        description:
            - Enable or disable QoS enforcement on the link. Default 'True' on creation.
        type: bool

    bandwidth_down:
        description:
            - Amount of bandwidth on this circuit in the downstream direction, in Mbps.

    bandwidth_up:
        description:
            - Amount of bandwidth on this circuit in the upstream direction, in Mbps.

    link_quality_monitoring:
        description:
            - Enable or disable artificial link quality calculation. Default 'True' on creation.
        type: bool

    circuit_catagory:
        description:
            - Circuit Class/Catagory ID. Required if operation is "create".

    wan_network:
        description:
            - WAN Network ID. Required if operation is "create".

    bfd_mode:
        description:
            - Mode of BFD operation.
        choices: ['aggressive', 'non_aggressive']

extends_documentation_fragment:
    - cloudgenix

author:
    - Aaron Edwards (@ebob9)
'''

EXAMPLES = '''
# Create a WAN Interface
- name: create WAN Interface
  cloudgenix_waninterfaces:
    auth_token: "<AUTH_TOKEN>"
    operation: "create"
    name: "My Site Name"
  register: create_waninterfaces_results

# Retrieve a WAN Interface
- name: describe WAN Interface
  cloudgenix_waninterfaces:
    auth_token: "<AUTH_TOKEN>"
    operation: "describe"
    id: "<WANINTERFACES_ID>"
  register: describe_results

# Modify a WAN Interface
- name: modify WAN Interface
  cloudgenix_waninterfaces:
    auth_token: "<AUTH_TOKEN>"
    operation: "modify"
    id: "<WANINTERFACES_ID>"
    description: "Shiny happy description holding hands"
  register: modify_results

# Delete a WAN Interface
- name: delete WAN Interface
  cloudgenix_waninterfaces:
    auth_token: "<AUTH_TOKEN>"
    operation: "delete"
    id: "<WANINTERFACES_ID>"
  register: delete_results
'''

RETURN = '''
operation:
    description: Operation that was executed
    type: string
    returned: always

site:
    description: Site ID that this WAN Interface is located at.
    type: string
    returned: always

name:
    description: Name of the WAN Interface.
    type: string
    returned: always

description:
    description: Description of the WAN Interface.
    type: string
    returned: always

id:
    description: Globally unique ID of the object
    type: string
    returned: always

bandwidth_config:
    description: Bandwidth speed configuration mode.
    type: string
    returned: always

qos:
    description: QoS enforcement on the WAN Interface.
    type: bool
    returned: always

bandwidth_down:
    description: Amount of bandwidth on this circuit in the downstream direction, in Mbps.
    type: float
    returned: always

bandwidth_up:
    description: Amount of bandwidth on this circuit in the upstream direction, in Mbps.
    type: float
    returned: always

link_quality_monitoring:
    description: Enable or disable artificial link quality calculation.
    type: bool
    returned: always

circuit_catagory:
    description: Circuit Class/Catagory ID.
    type: string
    returned: always

wan_network:
    description: WAN Network ID.
    type: string
    returned: always

bfd_mode:
    description: Mode of BFD operation.
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
        description=dict(type='str', required=False, default=None),
        id=dict(type='str', required=False, default=None),
        bandwidth_config=dict(choices=['manual', 'manual_bwm_disabled', 'auto'], required=False, default=None),
        qos=dict(type='bool', required=False, default=None),
        bandwidth_down=dict(type='float', required=False, default=None),
        bandwidth_up=dict(type='float', required=False, default=None),
        link_quality_monitoring=dict(type='bool', required=False, default=None),
        circuit_catagory=dict(type='str', required=False, default=None),
        wan_network=dict(type='str', required=False, default=None),
        bfd_mode=dict(choices=['aggressive', 'non_aggressive'], required=False, default=None),
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
        description='',
        id='',
        bandwidth_config='',
        qos='',
        bandwidth_down='',
        bandwidth_up='',
        link_quality_monitoring='',
        circuit_catagory='',
        wan_network='',
        bfd_mode='',
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
    description = module.params.get('description')
    id = module.params.get('id')
    bandwidth_config = module.params.get('bandwidth_config')
    qos = module.params.get('qos')
    bandwidth_down = module.params.get('bandwidth_down')
    bandwidth_up = module.params.get('bandwidth_up')
    link_quality_monitoring = module.params.get('link_quality_monitoring')
    circuit_catagory = module.params.get('circuit_catagory')
    wan_network = module.params.get('wan_network')
    bfd_mode = module.params.get('bfd_mode')

    # get CloudGenix API connection details
    auth_token, controller, tenant_id, cgx_session = setup_cloudgenix_connection(module)

    # start logic.

    # check if WAN Interface is new, changing, or being deleted.
    if operation == 'describe':

        # Check for id as required for new WAN Interface.
        if any(field is None for field in [site, id]):
            module.fail_json(msg='"site" and "id" are required to describe a WAN Interface.', **result)

        # Get the object.
        waninterfaces_describe_response = cgx_session.get.waninterfaces(site, id)

        # Check for API failure
        if not waninterfaces_describe_response.cgx_status:
            result['meta'] = waninterfaces_describe_response.cgx_content
            module.fail_json(msg='WAN Network DESCRIBE failed.', **result)

        updated_waninterfaces_result = waninterfaces_describe_response.cgx_content

        # update result
        result = dict(
            changed=False,
            operation=operation,
            name=updated_waninterfaces_result['name'],
            description=updated_waninterfaces_result['description'],
            id=updated_waninterfaces_result['id'],
            bandwidth_config=updated_waninterfaces_result['bw_config_mode'],
            qos=updated_waninterfaces_result['bwc_enabled'],
            bandwidth_down=updated_waninterfaces_result['link_bw_down'],
            bandwidth_up=updated_waninterfaces_result['link_bw_up'],
            link_quality_monitoring=updated_waninterfaces_result['lqm_enabled'],
            circuit_catagory=updated_waninterfaces_result['label_id'],
            wan_network=updated_waninterfaces_result['network_id'],
            bfd_mode=updated_waninterfaces_result['bfd_mode'],
            meta=waninterfaces_describe_response.cgx_content
        )

        # success
        module.exit_json(**result)

    elif operation == 'create':
        # new WAN Interface request!

        # Check for new WAN Interface required fields.
        if any(field is None for field in [name, site, circuit_catagory, wan_network]):
            module.fail_json(msg='"name", "site", "circuit_catagory", and "wan_network" are required for '
                                 'WAN Interface creation.', **result)

        # cgx WAN Interface template
        new_waninterface = {
            "bfd_mode": "aggressive",
            "bw_config_mode": "manual",
            "bwc_enabled": True,
            "description": None,
            "label_id": None,
            "link_bw_down": 30,
            "link_bw_up": 10,
            "lqm_enabled": True,
            "name": None,
            "network_id": None,
        }

        if name is not None:
            new_waninterface['name'] = name
        if description is not None:
            new_waninterface['description'] = description
        if bandwidth_config is not None:
            new_waninterface['bw_config_mode'] = bandwidth_config
        if qos is not None:
            new_waninterface['bwc_enabled'] = qos
        if bandwidth_down is not None:
            new_waninterface['link_bw_down'] = bandwidth_down
        if bandwidth_up is not None:
            new_waninterface['link_bw_up'] = bandwidth_up
        if link_quality_monitoring is not None:
            new_waninterface['lqm_enabled'] = link_quality_monitoring
        if circuit_catagory is not None:
            new_waninterface['label_id'] = circuit_catagory
        if wan_network is not None:
            new_waninterface['network_id'] = wan_network
        if bfd_mode is not None:
            new_waninterface['bfd_mode'] = bfd_mode

        # Attempt to create WAN Interface
        waninterfaces_create_response = cgx_session.post.waninterfaces(site, new_waninterface)

        if not waninterfaces_create_response.cgx_status:
            result['meta'] = waninterfaces_create_response.cgx_content
            module.fail_json(msg='WAN Network CREATE failed.', **result)

        updated_waninterfaces_result = waninterfaces_create_response.cgx_content

        # update result
        result = dict(
            changed=True,
            operation=operation,
            name=updated_waninterfaces_result['name'],
            description=updated_waninterfaces_result['description'],
            id=updated_waninterfaces_result['id'],
            bandwidth_config=updated_waninterfaces_result['bw_config_mode'],
            qos=updated_waninterfaces_result['bwc_enabled'],
            bandwidth_down=updated_waninterfaces_result['link_bw_down'],
            bandwidth_up=updated_waninterfaces_result['link_bw_up'],
            link_quality_monitoring=updated_waninterfaces_result['lqm_enabled'],
            circuit_catagory=updated_waninterfaces_result['label_id'],
            wan_network=updated_waninterfaces_result['network_id'],
            bfd_mode=updated_waninterfaces_result['bfd_mode'],
            meta=waninterfaces_create_response.cgx_content
        )

        # success
        module.exit_json(**result)

    elif operation == 'modify':

        # Check for id as required for new WAN Interface.
        if any(field is None for field in [site, id]):
            module.fail_json(msg='"site" and "id" is a required value for WAN Interface modification.', **result)

        # Get the object.
        waninterfaces_response = cgx_session.get.waninterfaces(site, id)

        # if WAN Interface get fails, fail module.
        if not waninterfaces_response.cgx_status:
            result['meta'] = waninterfaces_response.cgx_content
            module.fail_json(msg='WAN Network ID {0} retrieval failed.'.format(id), **result)
        # pull the WAN Interface out of the Response
        updated_waninterface = waninterfaces_response.cgx_content

        # modify the WAN Interface
        if name is not None:
            updated_waninterface['name'] = name
        if description is not None:
            updated_waninterface['description'] = description
        if bandwidth_config is not None:
            updated_waninterface['bw_config_mode'] = bandwidth_config
        if qos is not None:
            updated_waninterface['bwc_enabled'] = qos
        if bandwidth_down is not None:
            updated_waninterface['link_bw_down'] = bandwidth_down
        if bandwidth_up is not None:
            updated_waninterface['link_bw_up'] = bandwidth_up
        if link_quality_monitoring is not None:
            updated_waninterface['lqm_enabled'] = link_quality_monitoring
        if circuit_catagory is not None:
            updated_waninterface['label_id'] = circuit_catagory
        if wan_network is not None:
            updated_waninterface['network_id'] = wan_network
        if bfd_mode is not None:
            updated_waninterface['bfd_mode'] = bfd_mode

        # Attempt to modify WAN Interface
        waninterfaces_update_response = cgx_session.put.waninterfaces(site, id, updated_waninterface)

        if not waninterfaces_update_response.cgx_status:
            result['meta'] = waninterfaces_update_response.cgx_content
            module.fail_json(msg='WAN Interface ID {0} UPDATE failed.'.format(id), **result)

        updated_waninterfaces_result = waninterfaces_update_response.cgx_content

        # update result
        result = dict(
            changed=True,
            operation=operation,
            name=updated_waninterfaces_result['name'],
            description=updated_waninterfaces_result['description'],
            id=updated_waninterfaces_result['id'],
            bandwidth_config=updated_waninterfaces_result['bw_config_mode'],
            qos=updated_waninterfaces_result['bwc_enabled'],
            bandwidth_down=updated_waninterfaces_result['link_bw_down'],
            bandwidth_up=updated_waninterfaces_result['link_bw_up'],
            link_quality_monitoring=updated_waninterfaces_result['lqm_enabled'],
            circuit_catagory=updated_waninterfaces_result['label_id'],
            wan_network=updated_waninterfaces_result['network_id'],
            bfd_mode=updated_waninterfaces_result['bfd_mode'],
            meta=waninterfaces_update_response.cgx_content
        )

        # success
        module.exit_json(**result)

    elif operation == 'delete':
        # Delete WAN Interface request. Verify ID was passed.
        if any(field is None for field in [site, id]):
            module.fail_json(msg='"site" or "id" not set, both are required for delete WAN Interface operation.')

        else:
            # Attempt to delete WAN Interface
            waninterfaces_delete_response = cgx_session.delete.waninterfaces(site, id)

            if not waninterfaces_delete_response.cgx_status:
                result['meta'] = waninterfaces_delete_response.cgx_content
                module.fail_json(msg='WAN Interface DELETE failed.', **result)

            # update result
            result['changed'] = True
            result['meta'] = waninterfaces_delete_response.cgx_content

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
