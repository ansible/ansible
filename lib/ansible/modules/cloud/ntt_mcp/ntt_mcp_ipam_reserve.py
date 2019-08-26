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
module: ntt_mcp_ipam_reserve
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
    vlan:
        description:
            - The name of a VLAN
        required: false
        type: str
    ip_address:
        description:
            - An IPv4 or IPv6 address
        required: True
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

  - name: Reserve and IPv4 address
    ntt_mcp_ipam_reserve:
      region: na
      datacenter: NA12
      network_domain: myCND
      vlan: myVLAN
      ip_address: 10.1.77.100
      state: present

  - name: Reserve and IPv6 address
    ntt_mcp_ipam_reserve:
      region: na
      datacenter: NA12
      network_domain: myCND
      vlan: myVLAN
      ip_address: ffff::1111
      state: present

  - name: Unreserve and IPv4 address
    ntt_mcp_ipam_reserve:
      region: na
      datacenter: NA12
      network_domain: myCND
      vlan: myVLAN
      ip_address: 10.1.77.100
      state: absent
'''

RETURN = '''
data:
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

try:
    from ipaddress import (ip_address as ip_addr, AddressValueError)
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


def reserve_ip(module, client, vlan_id, ip_address, description):
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
        return_data['ipam'] = {'ipAddress': client.reserve_ip(vlan_id, str(ip_address), description, ip_address.version)}
    except (KeyError, IndexError, NTTMCPAPIException) as e:
        module.fail_json(msg='Could not reserve the private IPv{0} address - {1}'.format(ip_address.version, e))

    module.exit_json(changed=True, data=return_data.get('ipam'))


def unreserve_ip(module, client, vlan_id, ip_address):
    """
    Remove an IPv4 or IPv6 address reservation

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg ip_address: The IP address to reserve
    :arg version: The IP version
    :returns: A message
    """
    try:
        client.unreserve_ip(vlan_id, str(ip_address), ip_address.version)
    except NTTMCPAPIException as e:
        module.fail_json(msg='Could not reserve the private IPv{0} address - {1}'.format(ip_address.version, e))

    module.exit_json(changed=True, msg='Successfully unreserved the IP address')


def get_reservation(module, client, vlan_id, ip_address):
    """
    Get the reservation status of an IP address

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg vlan_id: The UUID of the VLAN to check
    :arg ip_address: The IP address to check
    :returns: True/False on the reservation status of the IP address
    """

    try:
        reservations = client.list_reserved_ip(vlan_id=vlan_id, version=ip_address.version)
        for reserved_ip in reservations:
            if ip_addr(unicode(reserved_ip.get('ipAddress'))) == ip_address:
                return True
    except (AttributeError, NTTMCPAPIException) as e:
        module.fail_json(msg='Error getting existing reservations - {0}'.format(e))
    return False


def main():
    """
    Main function

    :returns: Public IP address reservation information
    """
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', type='str'),
            datacenter=dict(required=True, type='str'),
            description=dict(required=False, type='str'),
            network_domain=dict(required=True, type='str'),
            vlan=dict(required=True, type='str'),
            ip_address=dict(required=True, type='str'),
            state=dict(default='present', choices=['present', 'absent'])
        ),
        supports_check_mode=True
    )
    try:
        credentials = get_credentials(module)
    except ImportError as e:
        module.fail_json(msg='{0}'.format(e))
    vlan = {}
    network_domain_name = module.params.get('network_domain')
    vlan_name = module.params.get('vlan')
    datacenter = module.params.get('datacenter')
    description = module.params.get('description')
    state = module.params.get('state')
    ip_address = module.params.get('ip_address')

    # Check Imports
    if not HAS_IPADDRESS:
        module.fail_json(msg='Missing Python module: ipaddress')

    # Check the region supplied is valid
    ntt_mcp_regions = get_ntt_mcp_regions()
    if module.params.get('region') not in ntt_mcp_regions:
        module.fail_json(msg='Invalid region. Regions must be one of {0}'.format(ntt_mcp_regions))

    if credentials is False:
        module.fail_json(msg='Error: Could not load the user credentials')

    client = NTTMCPClient((credentials[0], credentials[1]), module.params.get('region'))

    # Check the IP address is valid
    try:
        ip_address_obj = ip_addr(unicode(ip_address))
    except AddressValueError:
        module.fail_json(msg='Invalid IPv4 or IPv6 address: {0}'.format(ip_address))

    # Get the CND
    try:
        network = client.get_network_domain_by_name(name=network_domain_name, datacenter=datacenter)
        network_domain_id = network.get('id')
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException):
        module.fail_json(msg='Could not find the Cloud Network Domain: {0}'.format(network_domain_name))

    # Get a list of existing VLANs and check if the new name already exists
    try:
        vlan = client.get_vlan_by_name(name=vlan_name, datacenter=datacenter, network_domain_id=network_domain_id)
        if not vlan:
            module.fail_json(msg='A valid VLAN is required')
    except NTTMCPAPIException as e:
        module.fail_json(msg='Failed to get a list of VLANs - {0}'.format(e))

    # Check if the IP address is already reserved
    is_reserved = get_reservation(module, client, vlan.get('id'), ip_address_obj)
    if not is_reserved and state == 'absent':
        module.exit_json(msg='No IPv{0} reservation found for {1}'.format(
            ip_address_obj.version,
            str(ip_address_obj)
        ))
    elif is_reserved and state == 'present':
        module.exit_json(msg='An existing IPv{0} reservation was found for {1}'.format(
            ip_address_obj.version,
            str(ip_address_obj)
        ))

    if state == 'present':
        # Implement Check Mode
        if module.check_mode:
            module.exit_json(msg='The IPv{0} address {1} will be reserved'.format(
                ip_address_obj.version,
                str(ip_address_obj),
            ))
        reserve_ip(module, client, vlan.get('id'), ip_address_obj, description)
    elif state == 'absent':
        # Implement Check Mode
        if module.check_mode:
            module.exit_json(msg='The IPv{0} address {1} will be unreserved'.format(
                ip_address_obj.version,
                str(ip_address_obj),
            ))
        unreserve_ip(module, client, vlan.get('id'), ip_address_obj)


if __name__ == '__main__':
    main()
