#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 NTT Communications Cloud Infrastructure Services
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ntt_mcp_vip_node
short_description: Create, Update and Delete VIP Nodes
description:
    - Create, Update and Delete VIP Nodes
version_added: 2.9
author:
    - Ken Sinfield (@kensinfield)
options:
    region:
        description:
            - The geographical region
        required: false
        type: str
        default: na
    datacenter:
        description:
            - The datacenter name
        required: true
        type: str
    description:
        description:
            - The description of the Cloud Network Domain
        required: false
        type: str
    network_domain:
        description:
            - The name of a Cloud Network Domain
        required: true
        type: str
    name:
        description:
            - The name of the VIP Node
        required: false
        type: str
    ip_address:
        description:
            - The IPv4 or IPv6 address of the VIP node
        required: false
        type: str
    status:
        description:
            - The status of the node
        required: false
        type: str
        default: ENABLED
        choices:
            - ENABLED
            - DISABLED
            - FORCED_OFFLINE
    connection_limit:
        description:
            - The maximum number of simultaneous connections permitted on the Node. Should be an integer between 1 and 100,000
        required: false
        type: int
        default: 100000
    connection_rate_limit:
        description:
            - The amount of new connections permitted every second. Should be an integer between 1 and 4,000.
        required: false
        type: int
        default: 4000
    health_monitor:
        description:
            - The procedure that the load balancer uses to verify that the Node is considered healthy and available for load balancing
            - https://docs.mcp-services.net/x/RgIu
        required: false
        type: str
        default: null
    no_health_monitor:
        description:
            - Remove a health monitor from a VIP pool
        required: false
        default: false
        type: bool
    id:
        description:
            - The UUID of the node
        required: false
        type: str
    state:
        description:
            - The action to be performed
        required: true
        type: str
        default: present
        choices:
            - present
            - absent
notes:
    - Requires NTT Ltd. MCP account/credentials
requirements:
    - requests>=2.21.0
'''

EXAMPLES = '''
- hosts: 127.0.0.1
  connection: local
  tasks:

  - name: Create a VIP Node
    ntt_mcp_vip_node:
      region: na
      datacenter: NA9
      network_domain: "my_network_domain"
      name: "My_Node"
      description: "My Node"
      ip_address: "10.0.0.10"
      health_monitor: "CCDEFAULT.Icmp"
      connection_limit: 50000
      connection_rate_limit: 2000
      state: present

  - name: Update a VIP Node - Disable the node and remove all health monitoring profiles
    ntt_mcp_vip_node:
      region: na
      datacenter: NA9
      network_domain: "my_network_domain"
      name: "My_Node"
      description: "My Node"
      no_health_monitor: True
      status: DISABLED
      state: present

  - name: Delete a VIP Node
    ntt_mcp_vip_node:
      region: na
      datacenter: NA9
      network_domain: "my_network_domain"
      name: "My_Node"
      state: absent
'''

RETURN = '''
data:
    description: Server objects
    returned: success
    type: complex
    contains:
        status:
            description: The status of the node
            type: str
            sample: ENABLED
        datacenterId:
            description: The MCP ID
            type: str
            sample: NA9
        networkDomainId:
            description: The UUID of the Cloud Network Domain
            type: str
            sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
        description:
            description: Node description
            type: str
            sample: "My Node"
        ipv6Address:
            description: The IPv6 address of the Node
            type: str
            returned: When the node has been created as an IPv6 node
            sample: "ffff:ffff:ffff:ffff:ffff:ffff:ffff:0001"
        ipv4Address:
            description: The IPv4 address of the Node
            type: str
            returned: When the node has been created as an IPv4 node
            sample: "10.0.0.10"
        id:
            description:  The UUID of the node
            type: str
            sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
        connectionRateLimit:
            description: The amount of new connections permitted every second. Should be an integer between 1 and 4,000.
            type: int
            sample: 4000
        state:
            description: Operational state of the node configuration
            type: str
            sample: NORMAL
        healthMonitor:
            description: The procedure that the load balancer uses to verify that the Node is considered healthy and available for load balancing
            type: complex
            contains:
                id:
                    description: The UUID of the Health Monitor
                    type: str
                    sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
                name:
                    description: The Health Monitor display name
                    type: str
                    sample: CCDEFAULT.Icmp
        connectionLimit:
            description: The maximum number of simultaneous connections permitted on the Node. Should be an integer between 1 and 100,000
            type: int
            sample: 100000
        createTime:
            description: The creation date of the image
            type: str
            sample: "2019-01-14T11:12:31.000Z"
        name:
            description: The node display name
            type: str
            sample: "my_node"
msg:
    description: A useful message
    type: str
    returned: when state == absent
'''

from copy import deepcopy
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ntt_mcp.ntt_mcp_utils import get_credentials, get_ntt_mcp_regions, return_object, compare_json
from ansible.module_utils.ntt_mcp.ntt_mcp_provider import NTTMCPClient, NTTMCPAPIException
from ansible.module_utils.ntt_mcp.ntt_mcp_config import VIP_NODE_STATES


def create_vip_node(module, client, network_domain_id):
    """
    Create a VIP node

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg network_domain_id: The UUID of the network domain
    :returns: The created VIP node dict
    """
    return_data = return_object('node')

    if not all([module.params.get('name'), module.params.get('ip_address')]):
        module.fail_json(msg='Valid values for name and ip_address are required')

    try:
        result = client.create_vip_node(network_domain_id, module.params.get('name'), module.params.get('description'),
                                        module.params.get('ip_address'), module.params.get('status'),
                                        module.params.get('health_monitor'), module.params.get('connection_limit'),
                                        module.params.get('connection_rate_limit'))
        return_data['node'] = client.get_vip_node(result)
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException) as e:
        module.fail_json(msg='Could not create the VIP Node - {0}'.format(e))

    module.exit_json(changed=True, data=return_data['node'])


def update_vip_node(module, client, node):
    """
    Update a VIP node

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg port_list: The dict containing the existing VIP node to be updated
    :returns: The updated VIP node dict
    """
    return_data = return_object('node')

    try:
        client.update_vip_node(node.get('id'), module.params.get('description'), module.params.get('status'),
                               module.params.get('health_monitor'), module.params.get('no_health_monitor'),
                               module.params.get('connection_limit'), module.params.get('connection_rate_limit'))
        return_data['node'] = client.get_vip_node(node.get('id'))
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException) as e:
        module.fail_json(msg='Could not update the VIP Node - {0}'.format(e))

    module.exit_json(changed=True, data=return_data['node'])


def delete_vip_node(module, client, node_id):
    """
    Delete a VIP node

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg node_id: The UUID of the VIP node to be deleted
    :returns: A message
    """
    if node_id is None:
        module.fail_json(msg='A value for id is required')
    try:
        client.remove_vip_node(node_id)
    except NTTMCPAPIException as e:
        module.fail_json(msg='Could not delete the VIP Node - {0}'.format(e))

    module.exit_json(changed=True, msg='Successfully deleted the VIP Node')


def compare_vip_node(module, node):
    """
    Compare two VIP nodes

    :arg module: The Ansible module instance
    :arg node: The dict containing the VIP node to compare to
    :returns: Any differences between the two VIP nodes
    """
    new_node = deepcopy(node)
    if module.params.get('name'):
        new_node['status'] = module.params.get('status')
    if module.params.get('connection_limit'):
        new_node['connectionLimit'] = module.params.get('connection_limit')
    if module.params.get('connection_rate_limit'):
        new_node['connectionRateLimit'] = module.params.get('connection_rate_limit')
    if module.params.get('health_monitor'):
        if not new_node.get('healthMonitor'):
            new_node['healthMonitor'] = {}
        new_node['healthMonitor']['id'] = module.params.get('health_monitor')

    compare_result = compare_json(new_node, node, None)
    # Implement Check Mode
    if module.check_mode:
        module.exit_json(data=compare_result)
    return compare_result['changes']


def main():
    """
    Main function

    :returns: Updated VIP node Information
    """
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', type='str'),
            datacenter=dict(required=True, type='str'),
            network_domain=dict(required=True, type='str'),
            id=dict(required=False, default=None, type='str'),
            name=dict(required=False, default=None, type='str'),
            description=dict(required=False, default=None, type='str'),
            ip_address=dict(required=False, default=None, type='str'),
            status=dict(required=False, default='ENABLED', choices=VIP_NODE_STATES),
            connection_limit=dict(required=False, default=100000, type='int'),
            connection_rate_limit=dict(required=False, default=4000, type='int'),
            health_monitor=dict(required=False, default=None, type='str'),
            no_health_monitor=dict(required=False, default=False, type='bool'),
            state=dict(default='present', choices=['present', 'absent'])
        ),
        supports_check_mode=True
    )
    try:
        credentials = get_credentials(module)
    except ImportError as e:
        module.fail_json(msg='{0}'.format(e))
    network_domain_name = module.params.get('network_domain')
    datacenter = module.params.get('datacenter')
    state = module.params.get('state')
    node = None

    # Check the region supplied is valid
    ntt_mcp_regions = get_ntt_mcp_regions()
    if module.params.get('region') not in ntt_mcp_regions:
        module.fail_json(msg='Invalid region. Regions must be one of {0}'.format(ntt_mcp_regions))

    # Check connection input values
    if module.params.get('connection_limit') not in range(1, 100001):
        module.fail_json(msg='connection_limit must be between 1 and 100000')
    if module.params.get('connection_rate_limit') not in range(1, 4001):
        module.fail_json(msg='connection_rate_limit must be between 1 and 4000')

    if credentials is False:
        module.fail_json(msg='Error: Could not load the user credentials')

    client = NTTMCPClient((credentials[0], credentials[1]), module.params.get('region'))

    # Get the CND
    try:
        network = client.get_network_domain_by_name(name=network_domain_name, datacenter=datacenter)
        network_domain_id = network.get('id')
    except NTTMCPAPIException as e:
        module.fail_json(msg='Could not find the Cloud Network Domain: {0}'.format(network_domain_name))

    # Check if the Node already exists
    try:
        if module.params.get('id'):
            node = client.get_vip_node(module.params.get('id'))
        else:
            nodes = client.list_vip_node(network_domain_id=network_domain_id,
                                         name=module.params.get('name'),
                                         ip_address=module.params.get('ip_address'))
            if len(nodes) == 1:
                node = nodes[0]
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException) as e:
        module.fail_json(msg='Could not get a list of existing nodes to check against - {0}'.format(e))

    # Check if a Health Monitoring profile was provided and update module.params with the UUID instead of the name
    # Since list_vip_health_monitor returns both Node and Pool profiles, we need to check that the name provided is node compatible
    try:
        health_monitors = client.list_vip_health_monitor(network_domain_id=network_domain_id)
        for profile in health_monitors:
            if module.params.get('health_monitor') == profile.get('name') and profile.get('nodeCompatible'):
                module.params['health_monitor'] = profile.get('id')
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException) as e:
        module.fail_json(msg='Could not get a list of existing Health Monitoring profiles to check against - {0}'.format(e))

    if state == 'present':
        if not node:
            # Implement Check Mode
            if module.check_mode:
                module.exit_json(msg='The VIP Node will be created')
            create_vip_node(module, client, network_domain_id)
        else:
            if compare_vip_node(module, node):
                update_vip_node(module, client, node)
            module.exit_json(result=node)
    elif state == 'absent':
        if not node:
            module.exit_json(msg='No VIP node not found. Nothing to remove.')
        # Implement Check Mode
        if module.check_mode:
            module.exit_json(msg='The VIP Node with ID {0} will be deleted'.format(node.get('id')))
        delete_vip_node(module, client, node.get('id'))


if __name__ == '__main__':
    main()
