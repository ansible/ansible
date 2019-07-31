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
module: nttc_cis_vip_pool_facts
short_description: List/Get VIP Pools
description:
    - List/Get VIP Pools
    - It is quicker to use the option "id" to locate the VIP Pool if the UUID is known rather than search by name
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
    id:
        description:
            - The UUID of the VIP Pool
        required: false
    name:
        description:
            - The name of the VIP Pool
        required: false
notes:
    - https://docs.mcp-services.net/x/5wMk
requirements:
    - NTTC CIS Provider (nttc_cis_provider)
    - NTTC CIS Utils (nttc_cis_utils)
'''

EXAMPLES = '''
# List All VIP Pools
- nttc_cis_vip_pool_facts:
      region: na
      datacenter: NA9
      network_domain: "my_network_domain"
# Get a specific VIP Pool by name
- nttc_cis_vip_node_facts:
      region: na
      datacenter: NA9
      network_domain: "my_network_domain"
      name: "my_pool"
# Get a specific VIP Pool by ID
- nttc_cis_vip_pool_facts:
      region: na
      datacenter: NA9
      network_domain: "my_network_domain"
      id: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
'''

RETURN = '''
count:
    description: The number of objects returned
    returned: success
    type: int
    sample: 1
pool:
    description: VIP Pool Object
    returned: success
    type: complex
    contains:
        networkDomainId:
            description: The UUID of the Cloud Network Domain
            type: str
            sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
        description:
            description: Node description
            type: str
            sample: "My Node"
        loadBalanceMethod:
            description: Defines how the Pool will handle load balancing
            type: str
            sample: "Round Robin"
        slowRampTime:
            description: This allows a Server to slowly ramp up connection
            type: int
            sample: 10
        createTime:
            description: The creation date of the VIP Pool
            type: str
            sample: "2019-01-14T11:12:31.000Z"
        datacenterId:
            description: The MCP ID
            type: str
            sample: NA9
        state:
            description: Operational state of the VIP Pool configuration
            type: str
            sample: NORMAL
        healthMonitor:
            description: The procedure that the load balancer uses to verify that the VIP Pool is considered “healthy” and available for load balancing
            type: complex
            suboptions:
                id:
                    description:
                    type: str
                    sample: The UUID of the Health Monitor
                name:
                    description: The Health Monitor display name
                    type: str
                    sample: CCDEFAULT.Tcp
        members:
            description: List of VIP Pool Members
            type: complex
            suboptions:
                createTime:
                    description: The creation date of the VIP Pool
                    type: str
                    sample: "2019-01-14T11:12:31.000Z"
                node:
                    description: The member node
                    type: complex
                    suboptions:
                        status:
                            description: The operational status of the node
                            type: str
                            sample: "ENABLED"
                        ipAddress:
                            description: The IPv4/IPv6 address of the Node
                            type: str
                            sample: "10.0.0.10"
                        id:
                            description: The UUID of the node
                            type: str
                            sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
                        name:
                            description: The name of the Node
                            type: str
                            sample: "my_node"
                status:
                    description: The operational status of the VIP Pool Member
                    type: str
                    sample: "DISABLED"
                port:
                    description: The TCP or UDP port for this VIP Pool Member
                    type: int
                    sample: 80
                id:
                    description: The UUID of the VIP Pool Member
                    type: str
                    sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
                state:
                    description: The state of the VIP Pool Member
                    type: str
                    sample: "NORMAL"
        serviceDownAction:
            description: When a Pool Member fails to respond to a Health Monitor, the system marks that Pool Member down and removes any persistence entries associated with the Pool Member
            type: str
            sample: "RESELECT"
        id:
            description:  The UUID of the VIP Pool
            type: str
            sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
        name:
            description: The VIP Pool display name
            type: str
            sample: "my_pool"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.nttc_cis.nttc_cis_utils import get_credentials, get_nttc_cis_regions, return_object
from ansible.module_utils.nttc_cis.nttc_cis_provider import NTTCCISClient, NTTCCISAPIException


def list_vip_pool(module, client, network_domain_id, name):
    """
    List the VIP Pools for a network domain, filter by name if provided
    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg network_domain_id: The UUID of the network domain
    :arg name: Optional name of the VIP Pool
    :returns: List of VIP Pool objects
    """
    return_data = return_object('vip_pool')
    try:
        return_data['vip_pool'] = client.list_vip_pool(network_domain_id, name)
        count = 0
        for pool in return_data['vip_pool']:
            return_data.get('vip_pool')[count]['members'] = client.list_vip_pool_members(pool.get('id'))
            # remove duplicated JSON attributes/objects from the inidiviual members
            member_count = 0
            for member in return_data.get('vip_pool')[count].get('members'):
                return_data.get('vip_pool')[count].get('members')[member_count].pop('pool')
                return_data.get('vip_pool')[count].get('members')[member_count].pop('datacenterId')
                return_data.get('vip_pool')[count].get('members')[member_count].pop('networkDomainId')
                member_count += 1
            count += 1
    except (KeyError, IndexError, NTTCCISAPIException) as exc:
        module.fail_json(msg='Could not retrieve a list of VIP Pools - {0}'.format(exc))

    return_data['count'] = len(return_data.get('vip_pool'))
    module.exit_json(results=return_data)


def get_vip_pool(module, client, pool_id):
    """
    Get a VIP Pool by UUID
    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg pool_id: The UUID of the VIP Pool
    :returns: VIP Pool object
    """
    return_data = return_object('vip_pool')
    if pool_id is None:
        module.fail_json(msg='A value for id is required')
    try:
        result = client.get_vip_pool(pool_id)
        if result is None:
            module.fail_json(msg='Could not find the VIP Pool for {0}'.format(pool_id))
        return_data['vip_pool'].append(result)
        return_data.get('vip_pool')[0]['members'] = client.list_vip_pool_members(return_data.get('vip_pool')[0].get('id'))
    except NTTCCISAPIException as exc:
        module.fail_json(msg='Could not get the VIP Pool - {0}'.format(exc))

    return_data['count'] = len(return_data['vip_pool'])
    module.exit_json(results=return_data)


def main():
    """
    Main function
    :returns: VIP Pool Information
    """
    nttc_cis_regions = get_nttc_cis_regions()
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', choices=nttc_cis_regions),
            datacenter=dict(required=True, type='str'),
            network_domain=dict(required=True, type='str'),
            id=dict(default=None, required=False, type='str'),
            name=dict(default=None, required=False, type='str'),
        ),
        supports_check_mode=True
    )
    credentials = get_credentials()
    network_domain_name = module.params.get('network_domain')
    datacenter = module.params.get('datacenter')
    object_id = module.params.get('id')
    name = module.params.get('name')

    if credentials is False:
        module.fail_json(msg='Could not load the user credentials')

    client = NTTCCISClient((credentials[0], credentials[1]), module.params.get('region'))

    # Get the CND
    try:
        network = client.get_network_domain_by_name(name=network_domain_name, datacenter=datacenter)
        network_domain_id = network.get('id')
    except (KeyError, IndexError, NTTCCISAPIException):
        module.fail_json(msg='Could not find the Cloud Network Domain: {0}'.format(network_domain_name))

    if object_id:
        get_vip_pool(module, client, object_id)
    else:
        list_vip_pool(module, client, network_domain_id, name)


if __name__ == '__main__':
    main()
