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

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: nttc_cis_static_route_facts
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
            - If a name and a network is provided but there is a conflict, name takes precendence
        required: false
    network:
        description:
            - The destination network address to search for e.g. 192.168.0.0
        required: false
    prefix:
        description:
            - The destination network prefix associated with the route as an integer e.g. 24
        required: false
    next_hop:
        description:
            - The next host destination for the route e.g. 10.0.0.10
        required: false
notes:
    - N/A
'''

EXAMPLES = '''
# List NAT rules
- nttc_cis_static_route_facts:
      region: na
      datacenter: NA9
      network_domain: "my_network_domain"
      next_hop: "172.16.0.77"
'''

RETURN = '''
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

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.nttc_cis.nttc_cis_utils import get_credentials, get_nttc_cis_regions, return_object
from ansible.module_utils.nttc_cis.nttc_cis_provider import NTTCCISClient, NTTCCISAPIException


def list_static_routes(module, client, network_domain_id):
    """
    List the Static Routes for a network domain, filter by name if provided
    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg network_domain_id: The UUID of the network domain
    :returns: List of Static Route objects
    """
    return_data = return_object('route')
    name = module.params.get('name')
    version = module.params.get('version')
    network = module.params.get('network')
    prefix = module.params.get('prefix')
    next_hop = module.params.get('next_hop')
    try:
        return_data['route'] = client.list_static_routes(network_domain_id, name, version, network, prefix, next_hop)
    except NTTCCISAPIException as exc:
        module.fail_json(msg='Could not retrieve a list of Static Routes - {0}'.format(exc))

    return_data['count'] = len(return_data['route'])
    module.exit_json(changed=False, results=return_data)


def main():
    """
    Main function
    :returns: Static Route Information
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
            network=dict(default=None, required=False, type='str'),
            prefix=dict(default=None, required=False, type='int'),
            next_hop=dict(default=None, required=False, type='str'),
            state=dict(default='present', choices=['present', 'absent', 'restore'])
        ),
        supports_check_mode=True
    )
    credentials = get_credentials()
    network_domain_name = module.params['network_domain']
    datacenter = module.params['datacenter']

    if credentials is False:
        module.fail_json(msg='Could not load the user credentials')

    client = NTTCCISClient((credentials[0], credentials[1]), module.params['region'])

    # Get the CND
    try:
        network = client.get_network_domain_by_name(name=network_domain_name, datacenter=datacenter)
        network_domain_id = network.get('id')
    except (KeyError, IndexError, NTTCCISAPIException):
        module.fail_json(msg='Could not find the Cloud Network Domain: {0}'.format(network_domain_name))

    list_static_routes(module, client, network_domain_id)


if __name__ == '__main__':
    main()
