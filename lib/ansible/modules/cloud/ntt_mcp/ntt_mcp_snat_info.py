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
module: ntt_mcp_snat_info
short_description: List SNAT Exclusions
description:
    - List SNAT Exclusions
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
    id:
        description:
            - The UUID of the SNAT exclusion
            - If a id and a network is provided but there is a conflict, id takes precendence
        required: false
        type: str
    cidr:
        description:
            - The IPv4 or IPv6 destination network address to modify in CIDR format for e.g. 192.168.0.0/24
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

  - name: List SNAT exclusions
    ntt_mcp_snat_info:
      region: na
      datacenter: NA9
      network_domain: my_network_domain

  - name: Get a SNAT exclusion by cidr
    ntt_mcp_snat_info:
      region: na
      datacenter: NA9
      network_domain: my_network_domain
      cidr: "172.16.0.0/12"

  - name: Get a SNAT exclusion by id
    ntt_mcp_snat_info:
      region: na
      datacenter: NA9
      network_domain: my_network_domain
      id: b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae
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
        snat:
            description: List of SNAT exclusion objects
            returned: success
            type: complex
            contains:
                id:
                    description: The UUID of the SNAT exclusion
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
                description:
                    description: Optional description for the SNAT exclusion
                    type: str
                    sample: "something"
                networkDomainId:
                    description: Network Domain ID
                    type: str
                    sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
                state:
                    state:
                    description: Status of the static route
                    type: str
                    sample: NORMAL
                destinationPrefixSize:
                    description: The destination prefix for the static route
                    type: int
                    sample: 24
                destinationIpv4NetworkAddress:
                    description: The destination network address for the static route
                    type: str
                    sample: "192.168.0.0"
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


def list_snat_exclusion(module, client, network_domain_id):
    """
    List the SNAT for a network domain, filter by name if provided
    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg network_domain_id: The UUID of the network domain
    :returns: List of SNAT objects
    """
    return_data = return_object('snat')
    snat_id = module.params.get('id')
    network = module.params.get('network')
    prefix = module.params.get('prefix')
    try:
        return_data['snat'] = client.list_snat_exclusion(network_domain_id, snat_id, network, prefix)
    except NTTMCPAPIException as exc:
        module.fail_json(msg='Could not retrieve a list of SNAT Exclusions - {0}'.format(exc))

    return_data['count'] = len(return_data['snat'])
    module.exit_json(data=return_data)


def get_snat_exclusion(module, client, network_domain_id, snat_id, network_cidr):
    """
    Get a SNAT by UUID
    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg network_domain_id: The UUID of the network domain
    :arg snat_id: The UUID of the SNAT
    :arg network_cidr: The network CIDR for the SNAT exclusion
    :returns: SNAT object
    """
    return_data = return_object('snat')
    if snat_id is None and network_cidr is None:
        module.fail_json(msg='A value for id and cidr is required')
    try:
        if snat_id:
            result = client.get_snat_exclusion(snat_id)
        else:
            # If no matching routes were found for the name check to see if the supplied network parameters match a rule with a different name
            snats = client.list_snat_exclusion(network_domain_id=network_domain_id,
                                               network=str(network_cidr.network_address),
                                               prefix=network_cidr.prefixlen)
            if len(snats) == 1:
                result = snats[0]
        if result is None:
            module.fail_json(msg='Could not find the SNAT Exclusion for {0}'.format(snat_id if snat_id else str(network_cidr)))
        return_data['snat'].append(result)
    except NTTMCPAPIException as exc:
        module.fail_json(msg='Could not get the SNAT Exclusion - {0}'.format(exc))

    return_data['count'] = len(return_data['snat'])
    module.exit_json(data=return_data)


def main():
    """
    Main function
    :returns: SNAT Information
    """
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', type='str'),
            datacenter=dict(required=True, type='str'),
            network_domain=dict(required=True, type='str'),
            id=dict(default=None, required=False, type='str'),
            cidr=dict(default=None, required=False, type='str')
        ),
        supports_check_mode=True
    )
    try:
        credentials = get_credentials(module)
    except ImportError as e:
        module.fail_json(msg='{0}'.format(e))
    network_domain_name = module.params.get('network_domain')
    datacenter = module.params.get('datacenter')
    snat_id = module.params.get('id')
    network_cidr = None

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
        if network_cidr.version != 4:
            module.fail_json(msg='The cidr argument must be in valid IPv4 CIDR notation')

    # Get the CND
    try:
        network = client.get_network_domain_by_name(name=network_domain_name, datacenter=datacenter)
        network_domain_id = network.get('id')
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException):
        module.fail_json(msg='Could not find the Cloud Network Domain: {0}'.format(network_domain_name))

    if snat_id or network_cidr:
        get_snat_exclusion(module, client, network_domain_id, snat_id, network_cidr)
    else:
        list_snat_exclusion(module, client, network_domain_id)


if __name__ == '__main__':
    main()
