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
module: cloudgenix_interfaces

short_description: "Create, Modify, Describe, or Delete a CloudGenix Element Interface."

version_added: "2.6"

description:
    - "Create, Modify, Describe, or Delete a CloudGenix Element Interface."

options:
    operation:
        description:
            - The operation you would like to perform on the Interface object
        choices: ['create', 'modify', 'describe', 'delete']
        required: True

    site:
        description:
            - Site ID that the Element containing this interface is assigned to.
        required: True

    element:
        description:
            - Element ID that this Interface is attached to.
        required: True

    name:
        description:
            - Name of the Interface. Required if operation set to "create".

    description:
        description:
            - Description of the Interface. Maximum 256 chars.

    id:
        description:
            - Globally unique ID of the object. Required if operation set to "modify", "describe" or "delete".

    admin_up:
        description:
            - Administrative status of the interface (True = Enabled, False = Admin Down).

    attached_lan_networks:
        description:
            - "If interface is used_for: private, and part of a bypass_pair - list of attached LAN Networks."

    bound_interfaces:
        description:
            - Bound Interfaces, None unless part of a portchannel or virtual_interface.

    bypass_pair:
        description:
            - A dictionary describing the bypass pair to create or modify.

    dhcp_relay:
        description:
            - A dictionary describing the DHCP relay configuration for the interface.

    ethernet_port:
        description:
            - A dictionary describing the physical Ethernet hardware configuration for the interface.

    ipv4_config:
        description:
            - A dictionary describing the physical Ethernet hardware configuration for the interface.

    mac_address:
        description:
            - Specify a specific MAC address for the Interface, or None for default hardware MAC.

    mtu:
        description:
            - MTU for the interface.

    nat_address:
        description:
            - "If interface is used_for: public, External NAT address to receive inbound VPN traffic on."

    nat_port:
        description:
            - "If interface is used_for: public, External NAT UDP port that is re-mapped to 4500 on the physical interface."

    network_context_id:
        description:
            - ID of the WAN Network Context this interface belongs to, None for default.

    parent:
        description:
            - If this is a sub-interface, the ID of the parent interface it is attached to.

    pppoe_config:
        description:
            - A dictionary describing the PPPoE Configuration of this interface.

    site_wan_interface_ids:
        description:
            - "If interface is used_for: public, list of WAN Interfaces that are attached to this Interface."

    sub_interface:
        description:
            - A dictionary describing the sub-interface configuration for the interface.
    type:
        description:
            - A string designating type of interface. Used on creation.
        choices: ['port', 'loopback', 'bypasspair', 'virtual_interface', 'portchannel', 'subinterface']

    used_for:
        description:
            - A string stating use of this interface.
        choices: ['public', 'private_wan', 'lan', 'none']


extends_documentation_fragment:
    - cloudgenix

author:
    - Aaron Edwards (@ebob9)
'''

EXAMPLES = '''

# Retrieve a Interface
- name: Dump an interface
  cloudgenix_interfaces:
    auth_token: "<AUTH_TOKEN>"
    operation: "describe"
    site: 15059502911400245
    element: 15059505344360090
    id: 15059505688680064
  register: describe_results

# Create a Interface
- name: Create an interface
  cloudgenix_interfaces:
    auth_token: "<AUTH_TOKEN>"
    operation: "create"
    site: "<SITE_ID>"
    element: "<ELEMENT_ID>"
    parent: "<PARENT_INTERFACE_ID>"
    type: subinterface
    name: "Auto Created Subif"
    sub_interface:
      vlan_id: 3
  register: create_results

# Modify a Interface
- name: Modify an interface
  cloudgenix_interfaces:
    auth_token: "<AUTH_TOKEN>"
    operation: "modify"
    site: "<SITE_ID>"
    element: "<ELEMENT_ID>"
    id: "<INTERFACE_ID>"
    name: "Auto Created Subif renamed!"
    used_for: "lan"
  register: modify_results

# Delete a Interface
- name: Delete an interface
  cloudgenix_interfaces:
    auth_token: "<AUTH_TOKEN>"
    operation: "delete"
    site: "<SITE_ID>"
    element: "<ELEMENT_ID>"
    id: "<INTERFACE_ID>"

'''

RETURN = '''
operation:
    description: Operation that was executed
    type: string
    returned: always

site:
    description: Site ID that the Element with this Interface is located at.
    type: string
    returned: always

element:
    description: Element ID that this interface is bound with.
    type: string
    returned: always

name:
    description: Name of the Interface. Required if operation set to "create".
    type: string
    returned: always

description:
    description: Description of the Interface. Maximum 256 chars.
    type: string
    returned: always

id:
    description: Globally unique ID of the Interface. Required if operation set to "modify", "describe" or "delete".
    type: string
    returned: always

admin_up:
    description: Administrative status of the interface
    type: bool
    returned: always

attached_lan_networks:
    description: List of dictionaries describing Attached LAN Network IDs and VLANs.
    type: list
    returned: always

bound_interfaces:
    description: Bound Interfaces, None unless part of a portchannel or virtual_interface.
    type: string
    returned: always

bypass_pair:
    description: A dictionary describing the bypass pair
    type: dictionary
    returned: always

dhcp_relay:
    description: A dictionary describing the DHCP relay configuration for the interface.
    type: dictionary
    returned: always

ethernet_port:
    description: A dictionary describing the physical Ethernet hardware configuration for the interface.
    type: dictionary
    returned: always

ipv4_config:
    description: Complex object describing the IPv4 config of the LAN Network.
    type: dictionary
    returned: always

mac_address:
    description: Manually specified MAC address for the Interface, if present.
    type: string
    returned: always

mtu:
    description: MTU for the interface
    type: int
    returned: always

nat_address:
    description: External NAT address to receive inbound VPN traffic on.
    type: string
    returned: always

nat_port:
    description: External NAT UDP port that is re-mapped to 4500 on the physical interface.
    type: string
    returned: always

network_context_id:
    description: ID of the WAN Network Context this interface belongs to.
    type: string
    returned: always

parent:
    description: For a sub-interface, the ID of the parent interface it is attached to.
    type: string
    returned: always

pppoe_config:
    description: A dictionary describing the PPPoE Configuration of this interface.
    type: dictionary
    returned: always

site_wan_interface_ids:
    description: A list of WAN Interfaces that are attached to this Interface.
    type: list
    returned: always

sub_interface:
    description: A dictionary describing the sub-interface configuration for the interface.
    type: dictionary
    returned: always

type:
    description: A string designating type of interface.
    type: string
    returned: always

used_for:
    description: A string stating use of this interface.
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
        element=dict(type=str, required=True),
        name=dict(type=str, required=False, default=None),
        description=dict(type=str, required=False, default=None),
        id=dict(type=str, required=False, default=None),
        admin_up=dict(type=bool, required=False, default=None),
        attached_lan_networks=dict(type=list, required=False, default=None),
        bound_interfaces=dict(type=str, required=False, default=None),
        bypass_pair=dict(type=dict, required=False, default=None),
        dhcp_relay=dict(type=dict, required=False, default=None),
        ethernet_port=dict(type=dict, required=False, default=None),
        ipv4_config=dict(type=dict, required=False, default=None),
        mac_address=dict(type=str, required=False, default=None),
        mtu=dict(type=int, required=False, default=None),
        nat_address=dict(type=str, required=False, default=None),
        nat_port=dict(type=str, required=False, default=None),
        network_context_id=dict(type=str, required=False, default=None),
        parent=dict(type=str, required=False, default=None),
        pppoe_config=dict(type=dict, required=False, default=None),
        site_wan_interface_ids=dict(type=list, required=False, default=None),
        sub_interface=dict(type=dict, required=False, default=None),
        type=dict(choices=['port', 'loopback', 'bypasspair', 'virtual_interface', 'portchannel', 'subinterface'],
                  type=str, required=False, default=None),
        used_for=dict(choices=['public', 'private_wan', 'lan', 'none'], type=str, required=False, default=None)
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
        name='',
        description='',
        id='',
        admin_up='',
        attached_lan_networks='',
        bound_interfaces='',
        bypass_pair='',
        dhcp_relay='',
        ethernet_port='',
        ipv4_config='',
        mac_address='',
        mtu='',
        nat_address='',
        nat_port='',
        network_context_id='',
        parent='',
        pppoe_config='',
        site_wan_interface_ids='',
        sub_interface='',
        type='',
        used_for='',
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
    name = module.params.get('name')
    description = module.params.get('description')
    id = module.params.get('id')
    admin_up = module.params.get('admin_up')
    attached_lan_networks = module.params.get('attached_lan_networks')
    bound_interfaces = module.params.get('bound_interfaces')
    bypass_pair = module.params.get('bypass_pair')
    dhcp_relay = module.params.get('dhcp_relay')
    ethernet_port = module.params.get('ethernet_port')
    ipv4_config = module.params.get('ipv4_config')
    mac_address = module.params.get('mac_address')
    mtu = module.params.get('mtu')
    nat_address = module.params.get('nat_address')
    nat_port = module.params.get('nat_port')
    network_context_id = module.params.get('network_context_id')
    parent = module.params.get('parent')
    pppoe_config = module.params.get('pppoe_config')
    site_wan_interface_ids = module.params.get('site_wan_interface_ids ')
    sub_interface = module.params.get('sub_interface')
    type = module.params.get('type')
    used_for = module.params.get('used_for')

    # get CloudGenix API connection details
    auth_token, controller, tenant_id, cgx_session = setup_cloudgenix_connection(module)

    # start logic.

    # check if Interface is new, changing, or being deleted.
    if operation == 'describe':

        # Check for id as required for describe Interface.
        if any(field is None for field in [site, element, id]):
            module.fail_json(msg='"site", "element", and "id" are required to describe a Interface.', **result)

        # Get the object.
        interfaces_describe_response = cgx_session.get.interfaces(site, element, id)

        # Check for API failure
        if not interfaces_describe_response.cgx_status:
            result['meta'] = interfaces_describe_response.cgx_content
            module.fail_json(msg='Interface DESCRIBE failed.', **result)

        updated_interfaces_result = interfaces_describe_response.cgx_content

        # update result
        result = dict(
            changed=False,
            operation=operation,
            site=updated_interfaces_result.get('site'),
            element=updated_interfaces_result.get('element'),
            name=updated_interfaces_result.get('name'),
            description=updated_interfaces_result.get('description'),
            id=updated_interfaces_result.get('id'),
            admin_up=updated_interfaces_result.get('admin_up'),
            attached_lan_networks=updated_interfaces_result.get('attached_lan_networks'),
            bound_interfaces=updated_interfaces_result.get('bound_interfaces'),
            bypass_pair=updated_interfaces_result.get('bypass_pair'),
            dhcp_relay=updated_interfaces_result.get('dhcp_relay'),
            ethernet_port=updated_interfaces_result.get('ethernet_port'),
            ipv4_config=updated_interfaces_result.get('ipv4_config'),
            mac_address=updated_interfaces_result.get('mac_address'),
            mtu=updated_interfaces_result.get('mtu'),
            nat_address=updated_interfaces_result.get('nat_address'),
            nat_port=updated_interfaces_result.get('nat_port'),
            network_context_id=updated_interfaces_result.get('network_context_id'),
            parent=updated_interfaces_result.get('parent'),
            pppoe_config=updated_interfaces_result.get('pppoe_config'),
            site_wan_interface_ids=updated_interfaces_result.get('site_wan_interface_ids '),
            sub_interface=updated_interfaces_result.get('sub_interface'),
            type=updated_interfaces_result.get('type'),
            used_for=updated_interfaces_result.get('used_for'),
            meta=interfaces_describe_response.cgx_content
        )

        # success
        module.exit_json(**result)

    elif operation == 'create':
        # new Interface request!

        # Check for new Interface required fields.
        if any(field is None for field in [name, site, element, type]):
            module.fail_json(msg='"name", "site", "element", and "type" are required at a minimum for '
                                 'Interface creation.', **result)

        # cgx Interface template
        new_interface = {
            "admin_up": None,
            "attached_lan_networks": None,
            "bound_interfaces": None,
            "bypass_pair": None,
            "description": None,
            "dhcp_relay": None,
            "ethernet_port": {
                "full_duplex": False,
                "speed": 0
            },
            "ipv4_config": None,
            "mac_address": None,
            "mtu": 0,
            "name": None,
            "nat_address": None,
            "nat_port": 0,
            "network_context_id": None,
            "parent": None,
            "pppoe_config": None,
            "site_wan_interface_ids": None,
            "sub_interface": None,
            "type": None,
            "used_for": "none"
        }

        if admin_up is not None:
            new_interface['admin_up'] = admin_up
        if attached_lan_networks is not None:
            new_interface['attached_lan_networks'] = attached_lan_networks
        if bound_interfaces is not None:
            new_interface['bound_interfaces'] = bound_interfaces
        if bypass_pair is not None:
            new_interface['bypass_pair'] = bypass_pair
        if description is not None:
            new_interface['description'] = description
        if dhcp_relay is not None:
            new_interface['dhcp_relay'] = dhcp_relay
        if ethernet_port is not None:
            new_interface['ethernet_port'] = ethernet_port
        if ipv4_config is not None:
            new_interface['ipv4_config'] = ipv4_config
        if mac_address is not None:
            new_interface['mac_address'] = mac_address
        if mtu is not None:
            new_interface['mtu'] = mtu
        if name is not None:
            new_interface['name'] = name
        if nat_address is not None:
            new_interface['nat_address'] = nat_address
        if nat_port is not None:
            new_interface['nat_port'] = nat_port
        if network_context_id is not None:
            new_interface['network_context_id'] = network_context_id
        if parent is not None:
            new_interface['parent'] = parent
        if pppoe_config is not None:
            new_interface['pppoe_config'] = pppoe_config
        if site_wan_interface_ids is not None:
            new_interface['site_wan_interface_ids'] = site_wan_interface_ids
        if sub_interface is not None:
            new_interface['sub_interface'] = sub_interface
        if type is not None:
            new_interface['type'] = type
        if used_for is not None:
            new_interface['used_for'] = used_for

        # Attempt to create Interface
        interfaces_create_response = cgx_session.post.interfaces(site, element, new_interface)

        if not interfaces_create_response.cgx_status:
            result['meta'] = interfaces_create_response.cgx_content
            module.fail_json(msg='Interface CREATE failed.', **result)

        updated_interfaces_result = interfaces_create_response.cgx_content

        # update result
        result = dict(
            changed=True,
            operation=operation,
            site=updated_interfaces_result.get('site'),
            element=updated_interfaces_result.get('element'),
            name=updated_interfaces_result.get('name'),
            description=updated_interfaces_result.get('description'),
            id=updated_interfaces_result.get('id'),
            admin_up=updated_interfaces_result.get('admin_up'),
            attached_lan_networks=updated_interfaces_result.get('attached_lan_networks'),
            bound_interfaces=updated_interfaces_result.get('bound_interfaces'),
            bypass_pair=updated_interfaces_result.get('bypass_pair'),
            dhcp_relay=updated_interfaces_result.get('dhcp_relay'),
            ethernet_port=updated_interfaces_result.get('ethernet_port'),
            ipv4_config=updated_interfaces_result.get('ipv4_config'),
            mac_address=updated_interfaces_result.get('mac_address'),
            mtu=updated_interfaces_result.get('mtu'),
            nat_address=updated_interfaces_result.get('nat_address'),
            nat_port=updated_interfaces_result.get('nat_port'),
            network_context_id=updated_interfaces_result.get('network_context_id'),
            parent=updated_interfaces_result.get('parent'),
            pppoe_config=updated_interfaces_result.get('pppoe_config'),
            site_wan_interface_ids=updated_interfaces_result.get('site_wan_interface_ids '),
            sub_interface=updated_interfaces_result.get('sub_interface'),
            type=updated_interfaces_result.get('type'),
            used_for=updated_interfaces_result.get('used_for'),
            meta=interfaces_create_response.cgx_content
        )

        # success
        module.exit_json(**result)

    elif operation == 'modify':

        # Check for id as required for new Interface.
        if any(field is None for field in [site, element, id]):
            module.fail_json(msg='"site", "element" and "id" is a required value for Interface modification.', **result)

        # Get the object.
        interfaces_response = cgx_session.get.interfaces(site, element, id)

        # if Interface get fails, fail module.
        if not interfaces_response.cgx_status:
            result['meta'] = interfaces_response.cgx_content
            module.fail_json(msg='Interface ID {0} retrieval failed.'.format(id), **result)
        # pull the Interface out of the Response
        updated_interface = interfaces_response.cgx_content

        # modify the Interface
        if admin_up is not None:
            updated_interface['admin_up'] = admin_up
        if attached_lan_networks is not None:
            updated_interface['attached_lan_networks'] = attached_lan_networks
        if bound_interfaces is not None:
            updated_interface['bound_interfaces'] = bound_interfaces
        if bypass_pair is not None:
            updated_interface['bypass_pair'] = bypass_pair
        if description is not None:
            updated_interface['description'] = description
        if dhcp_relay is not None:
            updated_interface['dhcp_relay'] = dhcp_relay
        if ethernet_port is not None:
            updated_interface['ethernet_port'] = ethernet_port
        if ipv4_config is not None:
            updated_interface['ipv4_config'] = ipv4_config
        if mac_address is not None:
            updated_interface['mac_address'] = mac_address
        if mtu is not None:
            updated_interface['mtu'] = mtu
        if name is not None:
            updated_interface['name'] = name
        if nat_address is not None:
            updated_interface['nat_address'] = nat_address
        if nat_port is not None:
            updated_interface['nat_port'] = nat_port
        if network_context_id is not None:
            updated_interface['network_context_id'] = network_context_id
        if parent is not None:
            updated_interface['parent'] = parent
        if pppoe_config is not None:
            updated_interface['pppoe_config'] = pppoe_config
        if site_wan_interface_ids is not None:
            updated_interface['site_wan_interface_ids'] = site_wan_interface_ids
        if sub_interface is not None:
            updated_interface['sub_interface'] = sub_interface
        if type is not None:
            updated_interface['type'] = type
        if used_for is not None:
            updated_interface['used_for'] = used_for

        # Attempt to modify Interface
        interfaces_update_response = cgx_session.put.interfaces(site, element, id, updated_interface)

        if not interfaces_update_response.cgx_status:
            result['meta'] = interfaces_update_response.cgx_content
            module.fail_json(msg='Interface ID {0} UPDATE failed.'.format(id), **result)

        updated_interfaces_result = interfaces_update_response.cgx_content

        # update result
        result = dict(
            changed=True,
            operation=operation,
            site=updated_interfaces_result.get('site'),
            element=updated_interfaces_result.get('element'),
            name=updated_interfaces_result.get('name'),
            description=updated_interfaces_result.get('description'),
            id=updated_interfaces_result.get('id'),
            admin_up=updated_interfaces_result.get('admin_up'),
            attached_lan_networks=updated_interfaces_result.get('attached_lan_networks'),
            bound_interfaces=updated_interfaces_result.get('bound_interfaces'),
            bypass_pair=updated_interfaces_result.get('bypass_pair'),
            dhcp_relay=updated_interfaces_result.get('dhcp_relay'),
            ethernet_port=updated_interfaces_result.get('ethernet_port'),
            ipv4_config=updated_interfaces_result.get('ipv4_config'),
            mac_address=updated_interfaces_result.get('mac_address'),
            mtu=updated_interfaces_result.get('mtu'),
            nat_address=updated_interfaces_result.get('nat_address'),
            nat_port=updated_interfaces_result.get('nat_port'),
            network_context_id=updated_interfaces_result.get('network_context_id'),
            parent=updated_interfaces_result.get('parent'),
            pppoe_config=updated_interfaces_result.get('pppoe_config'),
            site_wan_interface_ids=updated_interfaces_result.get('site_wan_interface_ids '),
            sub_interface=updated_interfaces_result.get('sub_interface'),
            type=updated_interfaces_result.get('type'),
            used_for=updated_interfaces_result.get('used_for'),
            meta=interfaces_update_response.cgx_content
        )

        # success
        module.exit_json(**result)

    elif operation == 'delete':
        # Delete Interface request. Verify ID was passed.
        if any(field is None for field in [site, element, id]):
            module.fail_json(msg='"site", "element" or "id" not set, both are required for delete Interface operation.')

        else:
            # Attempt to delete Interface
            interfaces_delete_response = cgx_session.delete.interfaces(site, element, id)

            if not interfaces_delete_response.cgx_status:
                result['meta'] = interfaces_delete_response.cgx_content
                module.fail_json(msg='Interface DELETE failed.', **result)

            # update result
            result['changed'] = True
            result['meta'] = interfaces_delete_response.cgx_content

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
