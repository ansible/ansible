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
module: nttc_cis_ipam_reserve
short_description: Reserve an IP Address in IP Address Management
description:
    - Reserve an IP Address in IP Address Management
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
        vlanId:
            description: UUID of the VLAN
            type: str
            returned: when state == present
            sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
        exclusive:
            description: Is this an explicity reservation
            type: bool
            returned: when state == present
        ipAddress:
            description: The IPv4/IPv6 IP address
            type: str
            returned: when state == present
            sample: 10.0.0.10
        datacenterId:
            description: UUID of the datacenter/MCP
            type: str
            returned: when state == present
            sample: N"b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
        id:
            description: UUID of the public IPv4 block if allocating public IPv4
            type: str
            returned: when state == present
            sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
'''

import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.nttc_cis.nttc_cis_utils import get_credentials, get_nttc_cis_regions, return_object
from ansible.module_utils.nttc_cis.nttc_cis_provider import NTTCCISClient, NTTCCISAPIException


def reserve_ip(module, client, vlan_id, ip_address, description, version):
    """
    Reserve an IPv4 or IPv6 address

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg vlan_id: The UUID of the VLAN for the reservation
    :arg ip_address: The IP address to reserve
    :arg description: The description associated with the IP address
    :arg version: The IP version
    :returns: The reserved IP address information
    """
    return_data = return_object('ipam')
    try:
        return_data['ipam'] = {'ipAddress': client.reserve_ip(vlan_id, ip_address, description, version)}
    except (KeyError, IndexError, NTTCCISAPIException) as e:
        module.fail_json(msg='Could not reserve the private IPv{0} address - {1}'.format(version, e), exception=traceback.format_exc())

    module.exit_json(changed=True, results=return_data.get('ipam'))


def unreserve_ip(module, client, vlan_id, ip_address, version):
    """
    Remove an IPv4 or IPv6 address reservation

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg ip_address: The IP address to reserve
    :arg version: The IP version
    :returns: A message
    """
    try:
        client.unreserve_ip(vlan_id, ip_address, version)
    except NTTCCISAPIException as e:
        module.fail_json(msg='Could not reserve the private IPv{0} address - {1}'.format(version, e))

    module.exit_json(changed=True, msg='Successfully unreserved the IP address')


def main():
    """
    Main function

    :returns: Public IP address reservation information
    """
    nttc_cis_regions = get_nttc_cis_regions()
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', choices=nttc_cis_regions),
            datacenter=dict(required=True, type='str'),
            description=dict(required=False, type='str'),
            network_domain=dict(required=True, type='str'),
            vlan=dict(required=False, default=None, type='str'),
            ip_address=dict(required=False, default=None, type='str'),
            version=dict(required=False, default=4, choices=[4, 6], type='int'),
            state=dict(default='present', choices=['present', 'absent'])
        )
    )
    vlan = {}
    credentials = get_credentials()
    network_domain_name = module.params['network_domain']
    vlan_name = module.params['vlan']
    datacenter = module.params['datacenter']
    description = module.params['description']
    state = module.params['state']
    ip_address = module.params['ip_address']
    version = module.params['version']

    if credentials is False:
        module.fail_json(msg='Error: Could not load the user credentials')

    client = NTTCCISClient((credentials[0], credentials[1]), module.params['region'])

    # Get the CND
    try:
        network = client.get_network_domain_by_name(name=network_domain_name, datacenter=datacenter)
        network_domain_id = network.get('id')
    except (KeyError, IndexError, NTTCCISAPIException):
        module.fail_json(msg='Could not find the Cloud Network Domain: {0}'.format(network_domain_name))

    # Get a list of existing VLANs and check if the new name already exists
    try:
        vlan = client.get_vlan_by_name(name=vlan_name, datacenter=datacenter, network_domain_id=network_domain_id)
        if not vlan:
            module.fail_json(msg='A valid VLAN is required')
    except NTTCCISAPIException as e:
        module.fail_json(msg='Failed to get a list of VLANs - {0}'.format(e))

    if state == 'present':
        reserve_ip(module, client, vlan.get('id'), ip_address, description, version)
    elif state == 'absent':
        unreserve_ip(module, client, vlan.get('id'), ip_address, version)


if __name__ == '__main__':
    main()
