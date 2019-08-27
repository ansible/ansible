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
module: ntt_mcp_ipam_info
short_description: IP Address Management Facts
description:
    - IP Address Management Facts
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
    name:
        description:
            - The name of the Cloud Network Domain
        required: true
        type: str
    id:
        description:
            - The UUID of the IP address entity to search for
        required: false
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
    version:
        description:
            - The IP version
        required: false
        type: int
        default: 4
        choices:
            - 4
            - 6
    public_ip_address:
        description:
            - Any of the IPv4 addresses within the /31 public IPv4 block
        required: false
        type: str
    reserved:
        description:
            - Is the IP address entity to search for an reserved IP address
        required: false
        type: bool
        default: false
notes:
    - Requires NTT Ltd. MCP account/credentials
requirements:
    - requests>=2.21.0
'''

EXAMPLES = '''
- hosts: 127.0.0.1
  connection: local
  tasks:

  - name: List all reserved private IPv4 addresses for a VLAN
    ntt_mcp_ipam_info:
      region: na
      datacenter: NA12
      network_domain: myCND
      vlan: myVLAN
      reserved: True
      version: 4

  - name: List all reserved private IPv4 addresses for a CND
    ntt_mcp_ipam_info:
      region: na
      datacenter: NA12
      network_domain: myCND
      reserved: True
      version: 4

  - name: List all reserved IPv6 addresses for a VLAN
    ntt_mcp_ipam_info:
      region: na
      datacenter: NA12
      network_domain: myCND
      vlan: myVLAN
      reserved: True
      version: 6

  - name: List all public IPv4 blocks for a CND
    ntt_mcp_ipam_info:
      region: na
      datacenter: NA12
      network_domain: myCND

  - name: Get a public IPv4 block by IP address
    ntt_mcp_ipam_info:
      region: na
      datacenter: NA12
      network_domain: myCND
      public_ip_address: x.x.x.x

  - name: Get a public IPv4 block by UUID
    ntt_mcp_ipam_info:
      region: na
      datacenter: NA12
      network_domain: myCND
      id: ffffffff-ffff-ffff-ffff-ffffffffffff
'''

RETURN = '''
data:
    description: The returned data
    returned: success
    type: complex
    contains:
        count:
            description: The number of objects returned
            returned: success
            type: int
            sample: 1
        ipam:
            description: List of of IP address objects
            returned: success
            type: complex
            contains:
                vlanId:
                    description: UUID of the VLAN
                    type: str
                    sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
                exclusive:
                    description: Is this an explicity reservation
                    type: bool
                ipAddress:
                    description: The IPv4/IPv6 IP address
                    type: str
                    sample: 10.0.0.10
                datacenterId:
                    description: UUID of the datacenter/MCP
                    type: str
                    sample: N"b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"

'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ntt_mcp.ntt_mcp_utils import get_credentials, get_ntt_mcp_regions, return_object
from ansible.module_utils.ntt_mcp.ntt_mcp_provider import NTTMCPClient, NTTMCPAPIException


def list_public_ipv4(module, client, network_domain_id):
    """
    List the public IPv4 blocks for the specified network domain
    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg network_domain_id: The UUID of the network domain
    :returns: List of public IPv4 block objects
    """
    return_data = return_object('ipam')
    try:
        return_data['ipam'] = client.list_public_ipv4(network_domain_id)
    except NTTMCPAPIException as exc:
        module.fail_json(msg='Could not list the public IPv4 blocks - {0}'.format(exc))
    except KeyError:
        module.fail_json(msg='Network Domain is invalid')

    return_data['count'] = len(return_data.get('ipam'))

    module.exit_json(changed=False, data=return_data)


def get_public_ipv4(module, client, network_domain_id, public_ipv4_block_id, public_ipv4_address):
    """
    Get a specific public IPv4 block
    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg network_domain_id: The UUID of the CND
    :arg public_ipv4_block_id: UUID of the public IPv4 block
    :arg public_ipv4_address: A public IPv4 address
    :returns: Public IPv4 block object
    """
    return_data = return_object('ipam')
    if public_ipv4_block_id is None and public_ipv4_address is None:
        module.fail_json(msg='A value for id or public_ip_address is required')

    try:
        if public_ipv4_block_id:
            result = client.get_public_ipv4(public_ipv4_block_id)
        else:
            result = client.get_public_ipv4_by_ip(network_domain_id, public_ipv4_address)
            public_ipv4_block_id = result.get('id')
        # If the public IPv4 block can't be found then just exit - don't error, that is just harsh
        # and not the behaviour we're after.
        if not result:
            module.exit_json(msg='No matching public IPv4 block exists')
        return_data['ipam'] = result
    except (AttributeError, NTTMCPAPIException) as exc:
        module.fail_json(msg='Could not list the public IPv4 blocks - {0}'.format(exc))

    return_data['count'] = len(return_data.get('ipam'))

    module.exit_json(changed=False, data=return_data)


def list_reserved_ip(module, client, datacenter, vlan, version):
    """
    List the reserved IPs, filtered by optional VLAN and version
    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg vlan: Optional VLAN object
    :arg name: Optional IP version
    :returns: List of reserved IP objects
    """
    return_data = return_object('ipam')
    try:
        vlan_id = vlan['id']
    except KeyError:
        vlan_id = None

    try:
        return_data['ipam'] = client.list_reserved_ip(vlan_id, datacenter, version)
    except NTTMCPAPIException as exc:
        module.fail_json(msg='Could not list the private IPv{0} reservations - {1}'.format(version, exc))

    return_data['count'] = len(return_data.get('ipam'))

    module.exit_json(changed=False, data=return_data)


def main():
    """
    Main function
    :returns: IP Address Management Information
    """
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', type='str'),
            datacenter=dict(required=True, type='str'),
            name=dict(required=False, type='str'),
            description=dict(required=False, type='str'),
            network_domain=dict(required=True, type='str'),
            vlan=dict(required=False, default=None, type='str'),
            version=dict(required=False, default=4, choices=[4, 6], type='int'),
            reserved=dict(required=False, default=False, type='bool'),
            id=dict(default=None, type='str'),
            public_ip_address=dict(required=False, default=None, type='str')
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
    object_id = module.params.get('id')
    version = module.params.get('version')
    reserved = module.params.get('reserved')
    public_ip_address = module.params.get('public_ip_address')

    # Check the region supplied is valid
    ntt_mcp_regions = get_ntt_mcp_regions()
    if module.params.get('region') not in ntt_mcp_regions:
        module.fail_json(msg='Invalid region. Regions must be one of {0}'.format(ntt_mcp_regions))

    if not credentials:
        module.fail_json(msg='Error: Could not load the user credentials')

    client = NTTMCPClient((credentials[0], credentials[1]), module.params.get('region'))

    # Get the CND
    try:
        network = client.get_network_domain_by_name(name=network_domain_name, datacenter=datacenter)
        network_domain_id = network.get('id')
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException):
        module.fail_json(msg='Could not find the Cloud Network Domain: {0}'.format(network_domain_name))

    # find the provided VLAN
    if vlan_name:
        try:
            vlan = client.get_vlan_by_name(datacenter=datacenter, network_domain_id=network_domain_id, name=vlan_name)
        except NTTMCPAPIException:
            pass
        except KeyError:
            module.fail_json(msg='A valid VLAN is required')
        except IndexError:
            pass

    if version == 4 and not object_id and not reserved:
        list_public_ipv4(module, client, network_domain_id)
    elif (version == 4 and object_id and not reserved) or public_ip_address:
        get_public_ipv4(module, client, network_domain_id, object_id, public_ip_address)
    elif reserved:
        list_reserved_ip(module, client, datacenter, vlan, version)
    else:
        module.fail_json(msg='Ambiguous arguments supplied')


if __name__ == '__main__':
    main()
