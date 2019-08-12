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

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: nttc_cis_static_route
short_description: Add and Remove static route entries for a Cloud Network Domain
description:
    - Add and Remove static route entries for a Cloud Network Domain
version_added: 2.9
author:
    - Ken Sinfield (@kensinfield)
options:
    region:
        description:
            - The geographical region
        required: true
        default: na
        choices:
          - Valid values can be found in nttcis.common.config.py under APIENDPOINTS
    datacenter:
        description:
            - The datacenter name
        required: true
        choices:
          - See NTTC CIS Cloud Web UI
    network_domain:
        description:
            - The name of a Cloud Network Domain
        required: true
        default: None
    name:
        description:
            - The name of the Static Route
        required: false
    cidr:
        description:
            - The IPv4 or IPv6 destination network address to modify in CIDR format for e.g. 192.168.0.0/24
        required: false
    next_hop:
        description:
            - The IPv4 or IPv6 address of the next host destination for the route e.g. 10.0.0.10
        required: false
    state:
        description:
            - The action to be performed
            - Restore will restore the static routes back to the MCP baseline defaults for the Cloud Network Domain
        required: true
        default: present
        choices: [present, absent, restore]
notes:
    - N/A
'''

EXAMPLES = '''
# Create/Update an IPv4 Static Route
- nttc_cis_static_route:
      region: na
      datacenter: NA9
      network_domain: "my_network_domain"
      name: "my_route"
      cidr: "192.168.1.0/24"
      next_hop: "10.0.0.10"
      state: present
# Delete a Static Route
- nttc_cis_static_route:
      region: na
      datacenter: NA9
      network_domain: "my_network_domain"
      name: "my_route"
      state: absent
# Restoring Static Routes to default
- nttc_cis_static_route:
      region: na
      datacenter: NA9
      network_domain: "my_network_domain"
      state: restore
'''

RETURN = '''
data:
    description: Array of Port List objects
    returned: success
    type: complex
    contains:
        count:
            description: The number of objects returned
            returned: success
            type: int
            sample: 1
        route:
            description: The Static Route objects or strings
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

from copy import deepcopy
from ipaddress import (ip_network as ip_net, AddressValueError)
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.nttc_cis.nttc_cis_utils import get_credentials, get_nttc_cis_regions, return_object, compare_json
from ansible.module_utils.nttc_cis.nttc_cis_provider import NTTCCISClient, NTTCCISAPIException


def create_static_route(module, client, network_domain_id, network_cidr):
    """
    Create a static route

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg network_domain_id: The UUID of the network domain
    :arg network_cidr: The network cidr object
    :returns: The created static route dict
    """
    return_data = return_object('route')
    name = module.params.get('name')
    description = module.params.get('description')
    version = 'IPv4' if network_cidr.version == 4 else 'IPV6'
    network = str(network_cidr.network_address)
    prefix = network_cidr.prefixlen
    next_hop = module.params.get('next_hop')

    if None in [network_domain_id, name, version, network, prefix, next_hop]:
        module.fail_json(msg='A valid value is required for network_domain, name and next_hop')
    try:
        client.create_static_route(network_domain_id, name, description, version, network, prefix, next_hop)
    except NTTCCISAPIException as e:
        module.fail_json(msg='Could not create the Static Route - {0}'.format(e))

    try:
        return_data['route'] = client.list_static_routes(network_domain_id=network_domain_id, name=name)[0]
    except (KeyError, IndexError, NTTCCISAPIException) as e:
        module.exit_json(changed=True, msg='Could not verify the static route was created - {0}'.format(e), results={})

    module.exit_json(changed=True, data=return_data.get('route'))


def delete_static_route(module, client, static_route_id):
    """
    Delete a static route

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg static_route_id: The UUID of the static route to be deleted
    :returns: A message
    """
    if static_route_id is None:
        module.exit_json(msg='No existing static route was matched for the name: {0}'.format(module.params.get('name')))
    try:
        client.remove_static_route(static_route_id)
    except NTTCCISAPIException as e:
        module.fail_json(msg='Could not delete the Static Route - {0}'.format(e))


def compare_static_route(module, network_cidr, route):
    """
    Compare two static routes

    :arg module: The Ansible module instance
    :arg network_cidr: The ip_network object
    :arg route: The dict containing the static route to compare to
    :returns: Any differences between the two static routes
    """
    new_route = deepcopy(route)
    if module.params.get('name'):
        new_route['name'] = module.params.get('name')
    if module.params.get('description'):
        new_route['description'] = module.params.get('description')
    if module.params.get('network'):
        new_route['destinationNetworkAddress'] = str(network_cidr.network_address)
    if module.params.get('prefix'):
        new_route['destinationPrefixSize'] = network_cidr.prefixlen
    if module.params.get('next_hop'):
        new_route['nextHopAddress'] = module.params.get('next_hop')

    compare_result = compare_json(new_route, route, None)
    # Implement Check Mode
    if module.check_mode:
        module.exit_json(data=compare_result)
    return compare_result.get('changes')


def main():
    """
    Main function

    :returns: Static route Information
    """
    nttc_cis_regions = get_nttc_cis_regions()
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', choices=nttc_cis_regions),
            datacenter=dict(required=True, type='str'),
            network_domain=dict(required=True, type='str'),
            name=dict(default=None, required=False, type='str'),
            version=dict(default='IPV4', required=False, choices=['IPV4', 'IPV6']),
            dsecription=dict(default=None, required=False, type='str'),
            cidr=dict(default=None, required=False, type='str'),
            next_hop=dict(default=None, required=False, type='str'),
            state=dict(default='present', choices=['present', 'absent', 'restore'])
        ),
        supports_check_mode=True
    )
    credentials = get_credentials()
    name = module.params.get('name')
    network_domain_name = module.params.get('network_domain')
    datacenter = module.params.get('datacenter')
    state = module.params.get('state')
    route = None
    routes = []

    if credentials is False:
        module.fail_json(msg='Error: Could not load the user credentials')

    client = NTTCCISClient((credentials[0], credentials[1]), module.params.get('region'))

    # Check to see the CIDR provided is valid
    if state == 'present':
        try:
            network_cidr = ip_net(unicode(module.params.get('cidr')))
        except (AddressValueError, ValueError) as e:
            module.fail_json(msg='Invalid network CIDR format {0}: {1}'.format(module.params.get('cidr'), e))

    # Get a list of existing CNDs and check if the name already exists
    try:
        network = client.get_network_domain_by_name(name=network_domain_name, datacenter=datacenter)
        network_domain_id = network.get('id')
    except (KeyError, IndexError, AttributeError, NTTCCISAPIException) as e:
        module.fail_json(msg='Failed to get a list of Cloud Network Domains - {0}'.format(e))

    # Check if a route already exists for this name
    try:
        if name:
            routes = client.list_static_routes(network_domain_id=network_domain_id, name=name)
        if not routes:
            # If no matching routes were found for the name check to see if the supplied
            # network parameters match a rule with a different name
            routes = client.list_static_routes(network_domain_id=network_domain_id,
                                               name=None,
                                               network=str(network_cidr.network_address),
                                               prefix=network_cidr.prefixlen,
                                               next_hop=module.params.get('next_hop')
                                              )
            if len(routes) == 1:
                route = routes[0]
        elif len(routes) == 1:
            route = routes[0]
    except (KeyError, IndexError, AttributeError, NTTCCISAPIException) as e:
        module.fail_json(msg='Failed to get a list of existing Static Routes - {0}'.format(e))

    try:
        if state == 'present':
            if not route:
                # Implement Check Mode
                if module.check_mode:
                    module.exit_json(msg='A new static route will be created for {0}'.format(str(network_cidr)))
                create_static_route(module, client, network_domain_id, network_cidr)
            else:
                # Static Routes cannot be updated. The old one must be removed and a new one created with the new parameters
                if compare_static_route(module, network_cidr, route):
                    delete_static_route(module, client, route.get('id'))
                    create_static_route(module, client, network_domain_id, network_cidr)
                module.exit_json(results=route)
        elif state == 'restore':
            # Implement Check Mode
            if module.check_mode:
                module.exit_json(msg='The routes for Network Domain {0} will be restored to defaults'.format(
                    module.params.get('network_domain')))
            client.restore_static_routes(network_domain_id)
            module.exit_json(changed=True, msg='Successfully restored the default Static Routes')
        elif state == 'absent':
            if route:
                # Implement Check Mode
                if module.check_mode:
                    module.exit_json(msg='An existing static route was found for {0} and will be removed'.format(
                        route.get('name')))
                delete_static_route(module, client, route.get('id'))
                module.exit_json(changed=True, msg='Successfully deleted the Static Route rule')
            else:
                module.exit_json(msg='No existing static route was matched')
    except (KeyError, IndexError, AttributeError, NTTCCISAPIException) as e:
        module.fail_json(msg='Could not update the static route - {0}'.format(e))


if __name__ == '__main__':
    main()
