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
module: nttc_cis_vlan_info
short_description: Get and List VLANs
description:
    - Get and List VLANs
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
            - The datacenter name e.g NA9
        required: true
    network_domain:
        description:
            - The name of the Cloud Network Domain
        required: true
    name:
        description:
            - The name of the VLAN. If a name is not provided the module will return all VLANs in the network_domain
        required: false
notes:
    - N/A
requirements:
    - NTTC CIS Provider (nttc_cis_provider)
    - NTTC CIS Utils (nttc_cis_utils)
'''

EXAMPLES = '''
# Get a specific VLAN
nttc_cis_vlan_facts:
  region: na
  datacenter: NA9
  network_domain: "my_network_domain"
  vlan: "my_vlan"
# List all VLANs in a Cloud Network Domain
nttc_cis_vlan_facts:
  region: na
  datacenter: NA9
  network_domain: "my_network_domain"
'''

RETURN = '''
data:
    description: dict of returned Objects
    returned: success
    type: complex
    contains:
        count:
            description: The number of objects returned
            returned: success
            type: int
            sample: 1
        vlan:
            description: Dictionary of the vlan
            returned: success
            type: complex
            contains:
                id:
                    description: VLAN ID
                    type: str
                    sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
                name:
                    description: VLAN name
                    type: str
                    sample: "My network"
                description:
                    description: VLAN description
                    type: str
                    sample: "My description"
                datacenterId:
                    description: Datacenter id/location
                    type: str
                    sample: NA9
                state:
                    description: Status of the VLAN
                    type: str
                    sample: NORMAL
                attached:
                    description: Whether or not the VLAN is a dettached VLAN
                    type: bool
                createTime:
                    description: The creation date of the image
                    type: str
                    sample: "2019-01-14T11:12:31.000Z"
                gatewayAddressing:
                    description: Use low (.1) or high (.254) addressing for the default gateway
                    type: str
                    sample: LOW
                ipv4GatewayAddress:
                    description: The IPv4 default gateway for this VLAN
                    type: str
                    sample: "10.0.0.1"
                ipv6GatewayAddress:
                    description: The IPv6 default gateway for this VLAN
                    type: str
                    sample: "1111:1111:1111:1111:0:0:0:1"
                ipv6Range:
                    description: The IPv6 address range
                    type: complex
                    contains:
                        address:
                            description: The base IPv6 network address
                            type: str
                            sample: "1111:1111:1111:1111:0:0:0:0"
                        prefixSize:
                            description: The IPv6 network prefix size
                            type: int
                            sample: 64
                networkDomain:
                    description: The Cloud Network Domain
                    type: complex
                    contains:
                        id:
                            description: The UUID of the Cloud Network Domain of the VLAN
                            type: str
                            sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
                        name:
                            description: The name of the Cloud Network Domain
                            type: str
                            sample: "my_network_domain"
                privateIpv4Range:
                    description: The IPv4 address range
                    type: complex
                    contains:
                        address:
                            description: The base IPv46 network address
                            type: str
                            sample: "10.0.0.0"
                        prefixSize:
                            description: The IPv6 network prefix size
                            type: int
                            sample: 24
                small:
                    description: Internal use
                    type: bool
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.nttc_cis.nttc_cis_utils import get_credentials, get_nttc_cis_regions, return_object
from ansible.module_utils.nttc_cis.nttc_cis_provider import NTTCCISClient, NTTCCISAPIException


def main():
    """
    Main function
    :returns: VLAN Information
    """
    return_data = return_object('vlan')
    nttc_cis_regions = get_nttc_cis_regions()
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', choices=nttc_cis_regions),
            datacenter=dict(required=True, type='str'),
            network_domain=dict(required=True, type='str'),
            name=dict(required=False, type='str')
        ),
        supports_check_mode=True
    )

    credentials = get_credentials()
    name = module.params['name']
    datacenter = module.params['datacenter']
    network_domain_name = module.params['network_domain']

    if credentials is False:
        module.fail_json(msg='Could not load the user credentials')

    client = NTTCCISClient((credentials[0], credentials[1]), module.params['region'])

    # Get the CND
    try:
        network = client.get_network_domain_by_name(name=network_domain_name, datacenter=datacenter)
        network_domain_id = network.get('id')
    except (KeyError, IndexError, AttributeError, NTTCCISAPIException):
        module.fail_json(msg='Could not find the Cloud Network Domain: {0}'.format(network_domain_name))

    # Get a list of existing VLANs and check if the new name already exists
    try:
        vlans = client.list_vlans(datacenter=datacenter, network_domain_id=network_domain_id)
    except NTTCCISAPIException as exc:
        module.fail_json(msg='Failed to get a list of VLANs - {0}'.format(exc))
    try:
        if name:
            return_data['vlan'] = [x for x in vlans if x['name'] == name]
        else:
            return_data['vlan'] = vlans
    except (KeyError, IndexError, NTTCCISAPIException):
        module.fail_json(msg='Could not find the VLAN - {0} in {1}'.format(name, datacenter))

    return_data['count'] = len(return_data['vlan'])

    module.exit_json(data=return_data)


if __name__ == '__main__':
    main()
