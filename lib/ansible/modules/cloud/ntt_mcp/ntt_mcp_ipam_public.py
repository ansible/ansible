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
module: ntt_mcp_ipam_public
short_description: IP Address Management
description:
    - IP Address Management
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
          - Valid values can be found in nttmcp.common.config.py under
            APIENDPOINTS
    datacenter:
        description:
            - The datacenter name
        required: true
        choices:
          - See NTT LTD Cloud Web UI
    network_domain:
        description:
            - The name of a Cloud Network Domain
        required: true
        default: None
    next_free_public_ipv4:
        description:
            - Return the next available public IPv4 address
            - If all existing /31 public IPv4 blocks are used, a new /31 will be provisioned
            - If a new /31 is required this should be set to false
        required: false
        default: true
    ip_address:
        description:
            - Any of the IPv4 addresses within the /31 public IPv4 block
            - Only used for deleting a /31 public IPv4 block
        required: false
    id:
        description:
            - The UUID of the /31 public IPv4 block
            - Only used for deleting a /31 public IPv4 block
        required: false
    state:
        description:
            - The action to be performed
        required: true
        default: create
        choices: [present, absent]
notes:
    - N/A
'''

EXAMPLES = '''
# Add a public IPv4 block
- ntt_mcp_ipam:
      region: na
      datacenter: NA9
      network_domain: xxxx
      state: present
# Delete a public IPv4 block by ID
- ntt_mcp_ipam:
      region: na
      datacenter: NA9
      network_domain: xxxx
      id: ffffffff-fff-ffff-ffff-ffffffffffff
      state: absent
# Delete a public IPv4 block by IPv4 address
- ntt_mcp_ipam:
      region: na
      datacenter: NA9
      network_domain: xxxx
      ip_address: x.x.x.x
      state: absent
'''

RETURN = '''
data:
    description: IP address object
    returned: success
    type: complex
    contains:
        ipAddress:
            description: The Public IPv4  address
            type: str
            returned: when next_free_public_ipv4 == True (Default)
            sample: 10.0.0.10
        ipAddress:
            description: List of Public IPv4 addresses within the new block
            type: complex
            returned: when next_free_public_ipv4 == False
            contains:
                type: str
                sample: 10.0.0.10
        id:
            description: UUID of the public IPv4 block if allocating public IPv4
            type: str
            returned: when next_free_public_ipv4 == False
            sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ntt_mcp.ntt_mcp_utils import get_credentials, get_ntt_mcp_regions, return_object, IP_TO_INT, INT_TO_IP
from ansible.module_utils.ntt_mcp.ntt_mcp_provider import NTTMCPClient, NTTMCPAPIException


def get_next_free_public_ipv4(module, client, network_domain_id):
    """
    Get the next available public IPv4 address.
    If no existing IPv4 blocks exist one will allocated as part of this process

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg network_domain_id: The UUID of the network domain
    :returns: The allocated public IPv4 address
    """
    return_data = return_object('ipam')
    return_data['ipam'] = {}
    try:
        result = client.get_next_public_ipv4(network_domain_id)
        return_data['ipam']['ipAddress'] = result.get('ipAddress')
    except NTTMCPAPIException as e:
        module.fail_json(msg='Could get the next free public IPv4 address - {0}'.format(e.message))

    module.exit_json(changed=result.get('changed'), data=return_data.get('ipam'))


def add_public_ipv4(module, client, network_domain_id):
    """
    Add a new /31 public IPv4 block to the cloud network domain

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg network_domain_id: The UUID of the network domain
    :returns: The allocated public IPv4 /31 address space
    """
    return_data = return_object('ipam')
    return_data['ipam'] = {}
    return_data['ipam']['ipAddress'] = []
    try:
        public_block_id = client.add_public_ipv4(network_domain_id)
        public_block = client.get_public_ipv4(public_block_id)
        return_data['ipam']['id'] = public_block_id
        for i in range(public_block.get('size')):
            return_data['ipam']['ipAddress'].append(INT_TO_IP(IP_TO_INT(public_block.get('baseIp')) + i))
    except NTTMCPAPIException as e:
        module.fail_json(msg='Could not add a public IPv4 block - {0}'.format(e.message))
    except (KeyError, IndexError) as e:
        module.fail_json(msg='Network Domain is invalid or an API failure occurred - {0}'.format(e.message))

    module.exit_json(changed=True, data=return_data['ipam'])


def delete_public_ipv4(module, client, network_domain_id):
    """
    Delete a /31 public IP address block

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg network_domain_id: The UUID of the network domain
    :returns: A message
    """
    ip_address = module.params.get('ip_address')
    public_ipv4_block_id = module.params.get('id')

    if public_ipv4_block_id is None and ip_address is None:
        module.fail_json(msg='A value for id or ip_address is required')
    try:
        if public_ipv4_block_id is None:
            public_ipv4_block = client.get_public_ipv4_by_ip(network_domain_id, ip_address)
            public_ipv4_block_id = public_ipv4_block.get('id')
        else:
            public_ipv4_block = client.get_public_ipv4(public_ipv4_block_id)
        # If the public IPv4 block can't be found then just exit - don't error that is just harsh
        # and not the behaviour we're after.
        if not public_ipv4_block:
            module.exit_json(msg='No matching public IPv4 block exists')
        # However if the public IPv4 block is being used by some NAT or VIP then error
        if client.check_public_block_in_use(network_domain_id, public_ipv4_block.get('baseIp')):
            module.fail_json(msg='The public IPv4 block with ID {0} is in use.'.format(public_ipv4_block_id))
        # Implement Check Mode
        if module.check_mode:
            module.exit_json(msg='The public IPv4 address block ID {0} with IPs '
                                 '{1} and {2} will be removed'.format(
                                     public_ipv4_block_id,
                                     public_ipv4_block.get('baseIp'),
                                     INT_TO_IP(IP_TO_INT(public_ipv4_block.get('baseIp')) + 1)
                                 ))
        client.remove_public_ipv4(public_ipv4_block_id)
    except NTTMCPAPIException as e:
        module.fail_json(msg='Could not delete the public IPv4 block - {0}'.format(e.message))

    module.exit_json(changed=True, msg='Successfully deleted the public IPv4 block')


def main():
    """
    Main function

    :returns: Public IPv4 address information
    """
    ntt_mcp_regions = get_ntt_mcp_regions()
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', choices=ntt_mcp_regions),
            datacenter=dict(required=True, type='str'),
            network_domain=dict(required=True, type='str'),
            next_free_public_ipv4=dict(required=False, default=True, type='bool'),
            ip_address=dict(required=False, default=None, type='str'),
            id=dict(default=None, type='str'),
            state=dict(default='present', choices=['present', 'absent'])
        ),
        supports_check_mode=True
    )
    credentials = get_credentials()
    network_domain_name = module.params.get('network_domain')
    datacenter = module.params.get('datacenter')
    state = module.params.get('state')
    next_free_public_ipv4 = module.params.get('next_free_public_ipv4')

    if credentials is False:
        module.fail_json(msg='Error: Could not load the user credentials')

    client = NTTMCPClient((credentials[0], credentials[1]), module.params.get('region'))

    # Get the CND
    try:
        network = client.get_network_domain_by_name(name=network_domain_name, datacenter=datacenter)
        network_domain_id = network.get('id')
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException):
        module.fail_json(msg='Could not find the Cloud Network Domain: {0}'.format(network_domain_name))

    if state == 'present' and next_free_public_ipv4:
        # Implement Check Mode
        if module.check_mode:
            module.exit_json(msg='A public IPv4 address will be consumed in '
                                 'the Network Domains with ID {0}'.format(network_domain_id))
        get_next_free_public_ipv4(module, client, network_domain_id)
    elif state == 'present' and not next_free_public_ipv4:
        # Implement Check Mode
        if module.check_mode:
            module.exit_json(msg='A new /31 public IPv4 block will be added to'
                                 ' the Network Domains with ID {0}'.format(network_domain_id))
        add_public_ipv4(module, client, network_domain_id)
    elif state == 'absent':
        delete_public_ipv4(module, client, network_domain_id)


if __name__ == '__main__':
    main()
