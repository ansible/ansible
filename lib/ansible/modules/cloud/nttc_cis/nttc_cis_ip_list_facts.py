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
module: nttc_cis_ip_list_facts
short_description: List and Get IP Address Lists
description:
    - List and Get IP Address Lists
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
            - The name of the IP Address List
        required: false
    network_domain:
        description:
            - The name of a Cloud Network Domain
        required: true
        default: None
    version:
        description:
            - The IP version for the IP Address List(s)
        required: false
        default: None
notes:
    - N/A
'''

EXAMPLES = '''
# List IP Address Lists
- nttc_cis_ip_list:
      region: na
      datacenter: NA9
      network_domain: "xxxx"
      version: IPV6
# Get a specific IP Address List
- nttc_cis_ip_list:
      region: na
      datacenter: NA9
      network_domain: "xxxx"
      name: "APITEST"
'''

RETURN = '''
count:
    description: The number of objects returned
    returned: success
    type: int
    sample: 1
port_list:
    description: a list of IP Address List objects or strs
    returned: success
    type: complex
    contains:
        id:
            description: IP Address List UUID
            type: str
            sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
        description:
            description: IP Address List description
            type: str
            sample: "My IP Address List description"
        name:
            description: IP Address List name
            type: str
            sample: "My IP Address List"
        createTime:
            description: The creation date of the image
            type: str
            sample: "2019-01-14T11:12:31.000Z"
        state:
            description: Status of the VLAN
            type: str
            sample: NORMAL
        ipVersion:
            description: The IP version for the IP Address List
            type: str
            sample: "IPV6"
        ipAddress:
            description: List of IP Addresses and/or IP Address Lists
            type: complex
            contains:
                begin:
                    description: The starting IP Address number for this IP Address or range (IPv4 or IPv6)
                    type: int
                    sample: x.x.x.x
                end:
                    description: The end IP Address number for this range. This is not present for single IP Addresses (IPv4 or IPv6)
                    type: int
                    sample: x.x.x.x
                prefixSize:
                    description: The prefix size for a given subnet
                    type: str
                    sample: "24"
        childIpAddressList:
            description: List of child IP Address Lists
            type: complex
            contains:
                id:
                    description: The ID of the IP Address List
                    type: str
                    sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
                name:
                    description: The name of the IP Address List
                    type: str
                    sample: "My Child IP Address List"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.nttc_cis.nttc_cis_utils import get_credentials, get_nttc_cis_regions, return_object
from ansible.module_utils.nttc_cis.nttc_cis_provider import NTTCCISClient, NTTCCISAPIException


def main():
    """
    Main function
    :returns: IP Address List Information
    """
    nttc_cis_regions = get_nttc_cis_regions()
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', choices=nttc_cis_regions),
            datacenter=dict(required=True, type='str'),
            name=dict(required=False, type='str'),
            version=dict(required=False, default=None, type='str', choices=['IPV4', 'IPV6']),
            network_domain=dict(required=True, type='str')
        ),
        supports_check_mode=True
    )
    credentials = get_credentials()
    name = module.params.get('name')
    network_domain_name = module.params.get('network_domain')
    datacenter = module.params.get('datacenter')
    version = module.params.get('version')
    return_data = return_object('ip_list')

    if credentials is False:
        module.fail_json(msg='Could not load the user credentials')

    client = NTTCCISClient((credentials[0], credentials[1]), module.params['region'])

    # Get the CND
    try:
        network = client.get_network_domain_by_name(name=network_domain_name, datacenter=datacenter)
        network_domain_id = network.get('id')
    except (KeyError, IndexError, NTTCCISAPIException):
        module.fail_json(msg='Could not find the Cloud Network Domain: {0}'.format(network_domain_name))

    try:
        if name:
            result = client.get_ip_list_by_name(network_domain_id, name, version)
            if result is None:
                module.fail_json(msg='Could not find the IP Address List {0}'.format(name))
            return_data['ip_list'].append(result)
        else:
            return_data['ip_list'] = client.list_ip_list(network_domain_id, version)
    except (KeyError, IndexError, NTTCCISAPIException) as e:
        module.fail_json(msg='Could not retrieve a list of the IP Address Lists - {0}'.format(e))

    return_data['count'] = len(return_data.get('ip_list'))
    module.exit_json(results=return_data)


if __name__ == '__main__':
    main()
