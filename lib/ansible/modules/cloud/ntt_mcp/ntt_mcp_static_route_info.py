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
module: ntt_mcp_static_route_info
short_description: List Static Routes
description:
    - List Static Routes
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
    network_domain:
        description:
            - The name of a Cloud Network Domain
        required: true
        type: str
    name:
        description:
            - The name of the Static Route
            - If a name and a network is provided but there is a conflict, name takes precendence
        required: false
        type: str
    cidr:
        description:
            - The IPv4 or IPv6 destination network address to modify in CIDR format for e.g. 192.168.0.0/24
        required: false
        type: str
    next_hop:
        description:
            - The next host destination for the route e.g. 10.0.0.10
        required: false
        type: str
    version:
        description:
            - The IP version. Used when searching (e.g. List all IPv6 routes)
        required: false
        type: int
        default: 4
        choices:
            - 4
            - 6
notes:
    - Requires NTT Ltd. MCP account/credentials
requirements:
    - requests>=2.21.0
'''

EXAMPLES = '''
- hosts: 127.0.0.1
  connection: local
  tasks:

  - name: List static routes
    ntt_mcp_static_route_info:
      region: na
      datacenter: NA9
      network_domain: my_network_domain

  - name: List static routes with a specific next hop IP address
    ntt_mcp_static_route_info:
      region: na
      datacenter: NA9
      network_domain: my_network_domain
      next_hop: "172.16.0.10"

  - name: Get a specific static route
    ntt_mcp_static_route_info:
      region: na
      datacenter: NA9
      network_domain: my_network_domain
      cidr: "10.0.0.0/24"
      next_hop: "172.16.0.10"
'''

RETURN = '''
data:
    description: dict of returned Objects
    type: complex
    returned: success
    contains:
        count:
            description: The number of objects returned
            returned: success
            type: int
            sample: 1
        route:
            description: a single or list of Static Route objects or strings
            returned: success
            type: complex
            contains:
                id:
                    description: Static Route ID
                    type: str
                    sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
                datacenterId:
                    description: Datacenter id/location
                    type: str
                    sample: NA3
                createTime:
                    description: The creation date of the image
                    type: str
                    sample: "2019-01-14T11:12:31.000Z"
                name:
                    description: The name of the Static Route
                    type: str
                    sample: "my_static_route"
                description:
                    description: Optional description for the static route
                    type: str
                    sample: "something"
                ipVersion:
                    description: The IP version of the static route
                    type: str
                    sample: IPV4
                networkDomainId:
                    description: Network Domain ID
                    type: str
                    sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
                state:
                    state:
                    description: Status of the static route
                    type: str
                    sample: NORMAL
                nextHopAddress:
                    description: The next hop destination for the route
                    type: str
                    sample: "10.0.0.10"
                destinationPrefixSize:
                    description: The destination prefix for the static route
                    type: int
                    sample: 24
                destinationNetworkAddress:
                    description: The destination network address for the static route
                    type: str
                    sample: "192.168.0.0"
                nextHopAddressVlanId:
                    description: The UUID of the VLAN for the next hop address
                    type: str
                    sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
                type:
                    description: The type of static route e.g. SYSTEM or CLIENT
                    type: str
                    sample: "CLIENT"
'''

try:
    from ipaddress import (ip_network as ip_net, AddressValueError)
    HAS_IPADDRESS = True
except ImportError:
    HAS_IPADDRESS = False
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ntt_mcp.ntt_mcp_utils import get_credentials, get_ntt_mcp_regions, return_object
from ansible.module_utils.ntt_mcp.ntt_mcp_provider import NTTMCPClient, NTTMCPAPIException

# Python3 workaround for unicode function so the same code can be used with ipaddress later
try:
    unicode('')
except NameError:
    unicode = str


def list_static_routes(module, client, network_domain_id, network_cidr):
    """
    List the Static Routes for a network domain, filter by name if provided

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg network_domain_id: The UUID of the network domain
    :arg network_cidr: The network cidr object
    :returns: List of Static Route objects
    """
    return_data = return_object('route')
    network = prefix = None
    name = module.params.get('name')
    version = 'IPv4' if module.params.get('version') == 4 else 'IPV6'
    if network_cidr:
        network = str(network_cidr.network_address)
        prefix = network_cidr.prefixlen
    next_hop = module.params.get('next_hop')
    try:
        return_data['route'] = client.list_static_routes(network_domain_id, name, version, network, prefix, next_hop)
    except NTTMCPAPIException as e:
        module.fail_json(msg='Could not retrieve a list of Static Routes - {0}'.format(e))

    return_data['count'] = len(return_data.get('route'))
    module.exit_json(data=return_data)


def main():
    """
    Main function
    :returns: Static Route Information
    """
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', type='str'),
            datacenter=dict(required=True, type='str'),
            network_domain=dict(required=True, type='str'),
            name=dict(default=None, required=False, type='str'),
            cidr=dict(default=None, required=False, type='str'),
            next_hop=dict(default=None, required=False, type='str'),
            version=dict(default=4, required=False, type='int', choices=[4, 6])
        ),
        supports_check_mode=True
    )
    try:
        credentials = get_credentials(module)
    except ImportError as e:
        module.fail_json(msg='{0}'.format(e))
    network_domain_name = module.params.get('network_domain')
    datacenter = module.params.get('datacenter')
    name = module.params.get('name')
    routes = []
    route = network_cidr = None

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

    # Check to see the CIDR provided is valid
    if module.params.get('cidr'):
        try:
            network_cidr = ip_net(unicode(module.params.get('cidr')))
        except (AddressValueError, ValueError) as e:
            module.fail_json(msg='Invalid network CIDR format {0}: {1}'.format(module.params.get('cidr'), e))

    # Get the CND
    try:
        network = client.get_network_domain_by_name(name=network_domain_name, datacenter=datacenter)
        network_domain_id = network.get('id')
    except (KeyError, IndexError, NTTMCPAPIException):
        module.fail_json(msg='Could not find the Cloud Network Domain: {0}'.format(network_domain_name))

    # Check if a route already exists for this name
    try:
        if name:
            routes = client.list_static_routes(network_domain_id=network_domain_id, name=name)
        if not routes and module.params.get('cidr'):
            # If no matching routes were found for the name check to see if the supplied
            # network parameters match a rule with a different name
            routes = client.list_static_routes(network_domain_id=network_domain_id,
                                               name=None,
                                               network=str(network_cidr.network_address),
                                               prefix=network_cidr.prefixlen,
                                               next_hop=module.params.get('next_hop'))
            if len(routes) == 1:
                route = routes[0]
        elif len(routes) == 1:
            route = routes[0]
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException) as e:
        module.fail_json(msg='Failed to get a list of existing Static Routes - {0}'.format(e))

    if route:
        return_data = return_object('route')
        return_data = return_object('route')
        return_data['count'] = len(return_data.get('route'))
        module.exit_json(data=route)
    list_static_routes(module, client, network_domain_id, network_cidr)


if __name__ == '__main__':
    main()
