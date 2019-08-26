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
module: ntt_mcp_vip_node_info
short_description: List VIP Nodes
description:
    - List VIP Nodes
    - It is quicker to use the option "id" to locate the Node if the UUID is known rather than search by name or IP address
version_added: 2.9
author:
    - Ken Sinfield (@kensinfield)
options:
    region:
        description:
            - The geographical region
        required: false
        default: na
        type: str
    datacenter:
        description:
            - The datacenter name
        required: true
        type: str
    network_domain:
        description:
            - The name of a Cloud Network Domain
        required: true
        type: str
    id:
        description:
            - The UUID of the node
        required: false
        type: str
    name:
        description:
            - The name of the node
        required: false
        type: str
    ip_address:
        description:
            - The IPv4 or IPv6 address of the node
        required: false
        type: str
notes:
    - Requires NTT Ltd. MCP account/credentials
requirements:
    - requests>=2.21.0
'''

EXAMPLES = '''
- hosts: 127.0.0.1
  connection: local
  tasks:

  - name: List All Nodes
    ntt_mcp_vip_node_facts:
      region: na
      datacenter: NA9
      network_domain: myCND

  - name: Get a specific Node by name
    ntt_mcp_vip_node_facts:
      region: na
      datacenter: NA9
      network_domain: myCND
      name: myNode

  - name: Get a specific Node by IPv6 address
    ntt_mcp_vip_node_facts:
      region: na
      datacenter: NA9
      network_domain: myCND
      ip_address: ffff:ffff:ffff:ffff:ffff:ffff:ffff:0001

  - name: Get a specific Node by UUID
    ntt_mcp_vip_node_facts:
      region: na
      datacenter: NA9
      network_domain: myCND
      id: b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae
'''

RETURN = '''
data:
    description: Server objects
    returned: success
    type: complex
    contains:
        count:
            description: The number of objects returned
            returned: success
            type: int
            sample: 1
        node:
            description: List of VIP Node Objects
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
                            description:
                            type: str
                            sample: The UUID of the Health Monitor
                        name:
                            description: The Health Monitor display name
                            type: str
                            sample: CCDEFAULT.Icmp
                connectionLimit:
                    description: The maximum number of simultaneous connections permitted on the Node. Should be an integer between 1 and 100,000
                    type: int
                    sample: 100000
                createTime:
                    description: The creation date of the node
                    type: str
                    sample: "2019-01-14T11:12:31.000Z"
                name:
                    description: The node display name
                    type: str
                    sample: "my_node"
'''

try:
    from ipaddress import ip_address as IP
    HAS_IPADDRESS = True
except ImportError:
    HAS_IPADDRESS = False
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ntt_mcp.ntt_mcp_utils import get_credentials, get_ntt_mcp_regions, return_object
from ansible.module_utils.ntt_mcp.ntt_mcp_provider import NTTMCPClient, NTTMCPAPIException


def list_vip_node(module, client, network_domain_id, name, ip_address):
    """
    List the VIP Node for a network domain, filter by name if provided
    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg network_domain_id: The UUID of the VIP Node
    :arg name: Optional name of the VIP Node
    :arg ip_address: Optional IP address to filter on
    :returns: List of VIP Node objects
    """
    return_data = return_object('node')
    try:
        return_data['node'] = client.list_vip_node(network_domain_id, name, ip_address)
    except (KeyError, IndexError, NTTMCPAPIException) as exc:
        module.fail_json(msg='Could not retrieve a list of Nodes - {0}'.format(exc))

    return_data['count'] = len(return_data.get('node'))
    module.exit_json(data=return_data)


def get_vip_node(module, client, node_id):
    """
    Get a VIP Node by UUID
    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg pool_id: The UUID of the VIP Node
    :returns: VIP Node object
    """
    return_data = return_object('node')
    if node_id is None:
        module.fail_json(msg='A value for id is required')
    try:
        result = client.get_vip_node(node_id)
        if result is None:
            module.fail_json(msg='Could not find the Node for {0}'.format(node_id))
        return_data['node'].append(result)
    except NTTMCPAPIException as exc:
        module.fail_json(msg='Could not get the Node - {0}'.format(exc))

    return_data['count'] = len(return_data['node'])
    module.exit_json(data=return_data)


def main():
    """
    Main function
    :returns: VIP Node Information
    """
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', type='str'),
            datacenter=dict(required=True, type='str'),
            network_domain=dict(required=True, type='str'),
            id=dict(default=None, required=False, type='str'),
            name=dict(default=None, required=False, type='str'),
            ip_address=dict(default=None, required=False, type='str')
        ),
        supports_check_mode=True
    )
    try:
        credentials = get_credentials(module)
    except ImportError as e:
        module.fail_json(msg='{0}'.format(e))
    network_domain_name = module.params.get('network_domain')
    datacenter = module.params.get('datacenter')
    object_id = module.params.get('id')
    ip_address = module.params.get('ip_address')
    name = module.params.get('name')

    # Check Imports
    if not HAS_IPADDRESS:
        module.fail_json(msg='Missing Python module: ipaddress')

    # Check the region supplied is valid
    ntt_mcp_regions = get_ntt_mcp_regions()
    if module.params.get('region') not in ntt_mcp_regions:
        module.fail_json(msg='Invalid region. Regions must be one of {0}'.format(ntt_mcp_regions))

    if credentials is False:
        module.fail_json(msg='Could not load the user credentials')

    client = NTTMCPClient((credentials[0], credentials[1]), module.params.get('region'))

    # Get the CND
    try:
        network = client.get_network_domain_by_name(name=network_domain_name, datacenter=datacenter)
        network_domain_id = network.get('id')
    except (KeyError, IndexError, NTTMCPAPIException):
        module.fail_json(msg='Could not find the Cloud Network Domain: {0}'.format(network_domain_name))

    if object_id:
        get_vip_node(module, client, object_id)
    else:
        list_vip_node(module, client, network_domain_id, name, ip_address)


if __name__ == '__main__':
    main()
