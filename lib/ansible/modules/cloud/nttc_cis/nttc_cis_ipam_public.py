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
module: nttc_cis_ipam_public
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
          - Valid values can be found in nttcis.common.config.py under
            APIENDPOINTS
    datacenter:
        description:
            - The datacenter name
        required: true
        choices:
          - See NTTC CIS Cloud Web UI
    name:
        description:
            - The name of the Cloud Network Domain
        required: true
    description:
        description:
            - The description of the Cloud Network Domain
        required: false
    network_domain:
        description:
            - The name of a Cloud Network Domain
        required: true
        default: None
    vlan:
        description:
            - The name of a VLAN
        required: false
    ip_address:
        description:
            - An IPv4 or IPv6 address
        required: false
    version:
        description:
            - The IP version
        required: false
        choices: [4, 6]
    state:
        description:
            - The action to be performed
        required: true
        default: create
        choices: [get_public_ipv4,add_public_ipv4,delete_public_ipv4,
                  list_reserved_ip,unreserve_ip,reserve_ip]
    verify_ssl_cert:
        description:
            - Enable/Disable SSL certificate verification
        required: false
        default: true
        choices: [true, false]
notes:
    - N/A
'''

EXAMPLES = '''
# Add a public IPv4 block
- nttc_cis_ipam:
      region: na
      datacenter: NA9
      network_domain: "xxxx"
      state: present
# Delete a public IPv4 block
- nttc_cis_ipam:
      region: na
      datacenter: NA9
      network_domain: "UCaaS RnD"
      id: "ffffffff-fff-ffff-ffff-ffffffffffff"
      state: absent
# Reserve an IP Address
- nttc_cis_ipam:
      region: na
      datacenter: NA9
      network_domain: "xxxx"
      vlan: "yyyy"
      ip_address: "xxxx::xxxx"
      version: 6
      reserved: True
      state: present
# Unreserve an IP Address
- nttc_cis_ipam:
      region: na
      datacenter: NA9
      network_domain: "xxxx"
      vlan: "yyyy"
      ip_address: "xxxx::xxxx"
      reserved: True
      version: 6
      state: absent
'''

RETURN = '''
results:
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

import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.nttc_cis.nttc_cis_utils import get_credentials, get_nttc_cis_regions, return_object, IP_TO_INT, INT_TO_IP
from ansible.module_utils.nttc_cis.nttc_cis_provider import NTTCCISClient, NTTCCISAPIException


def get_next_free_public_ipv4(module, client, network_domain_id):
    """
    Get the next available public IPv4 address. If no existing IPv4 blocks exist one will allocated as part of this process

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg network_domain_id: The UUID of the network domain
    :returns: The allocated public IPv4 address
    """
    return_data = return_object('ipam')
    return_data['ipam'] = {}
    try:
        result = client.get_next_public_ipv4(network_domain_id)
        return_data['ipam']['ipAddress'] = result['ipAddress']
    except NTTCCISAPIException as e:
        module.fail_json(msg='Could get the next free public IPv4 address - {0}'.format(e.message), exception=traceback.format_exc())

    module.exit_json(changed=result['changed'], results=return_data['ipam'])


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
        for i in range(public_block['size']):
            return_data['ipam']['ipAddress'].append(INT_TO_IP(IP_TO_INT(public_block['baseIp']) + i))
    except NTTCCISAPIException as e:
        module.fail_json(msg='Could not add a public IPv4 block - {0}'.format(e.message), exception=traceback.format_exc())
    except (KeyError, IndexError) as e:
        module.fail_json(msg='Network Domain is invalid or an API failure occurred - {0}'.format(e.message), exception=traceback.format_exc())

    module.exit_json(changed=True, results=return_data['ipam'])


def delete_public_ipv4(module, client, public_ipv4_block_id):
    """
    Delete a /31 public IP address block

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg public_ipv4_block_id: The UUID of the public IPv4 address block
    :returns: A message
    """
    if public_ipv4_block_id is None:
        module.fail_json(msg='A value for id is required')
    try:
        client.remove_public_ipv4(public_ipv4_block_id)
    except NTTCCISAPIException as e:
        module.fail_json(msg='Could not delete the public IPv4 block - {0}'.format(e.message), exception=traceback.format_exc())

    module.exit_json(changed=True, msg='Successfully deleted the public IPv4 block')


def main():
    """
    Main function

    :returns: Public IPv4 address information
    """
    nttc_cis_regions = get_nttc_cis_regions()
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', choices=nttc_cis_regions),
            datacenter=dict(required=True, type='str'),
            network_domain=dict(required=True, type='str'),
            next_free_public_ipv4=dict(required=False, default=True, type='bool'),
            id=dict(default=None, type='str'),
            state=dict(default='present', choices=['present', 'absent'])
        )
    )
    credentials = get_credentials()
    object_id = module.params['id']
    network_domain_name = module.params['network_domain']
    datacenter = module.params['datacenter']
    state = module.params['state']
    next_free_public_ipv4 = module.params['next_free_public_ipv4']

    if credentials is False:
        module.fail_json(msg='Error: Could not load the user credentials')

    client = NTTCCISClient((credentials[0], credentials[1]), module.params['region'])

    # Get the CND
    try:
        network = client.get_network_domain_by_name(name=network_domain_name, datacenter=datacenter)
        network_domain_id = network.get('id')
    except (KeyError, IndexError, NTTCCISAPIException):
        module.fail_json(msg='Could not find the Cloud Network Domain: {0}'.format(network_domain_name))

    if state == 'present' and next_free_public_ipv4:
        get_next_free_public_ipv4(module, client, network_domain_id)
    elif state == 'present' and not next_free_public_ipv4:
        add_public_ipv4(module, client, network_domain_id)
    elif state == 'absent':
        delete_public_ipv4(module, client, object_id)


if __name__ == '__main__':
    main()
