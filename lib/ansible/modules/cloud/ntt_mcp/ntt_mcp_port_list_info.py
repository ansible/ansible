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
module: ntt_mcp_port_list_info
short_description: List/Get Firewall Port Lists
description:
    - List/Get Firewall Port Lists
version_added: 2.9
author:
    - Ken Sinfield (@kensinfield)
options:
    region:
        description:
            - The geographical region
        required: false
        default: na
        type: str
    datacenter:
        description:
            - The datacenter name
        required: true
        type: str
    name:
        description:
            - The name of the Port List
        required: false
        type: str
    network_domain:
        description:
            - The name of a Cloud Network Domain
        required: true
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

  - name: List Port Lists
    ntt_mcp_port_list_info:
      region: na
      datacenter: NA9
      network_domain: xxxx

  - name: Get a specific Port List
    ntt_mcp_port_list_info:
      region: na
      datacenter: NA9
      network_domain: xxxx
      name: APITEST
'''

RETURN = '''
data:
    description: dict of returned Objects
    type: complex
    returned: success
    contains:
        count:
            description: The number of objects returned
            returned: success
            type: int
            sample: 1
        port_list:
            description: Array of Port List object
            returned: success
            type: complex
            contains:
                id:
                    description: Port List UUID
                    type: str
                    sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
                description:
                    description: Port List description
                    type: str
                    sample: "My Port List description"
                name:
                    description: Port List name
                    type: str
                    sample: "My Port List"
                createTime:
                    description: The creation date of the image
                    type: str
                    sample: "2019-01-14T11:12:31.000Z"
                state:
                    description: Status of the VLAN
                    type: str
                    sample: NORMAL
                port:
                    description: List of ports and/or port ranges
                    type: complex
                    contains:
                        begin:
                            description: The starting port number for this port or range
                            type: int
                            sample: 22
                        end:
                            description: The end port number for this range. This is not present for single ports
                            type: int
                            sample: 23
                childPortList:
                    description: List of child Port Lists
                    type: complex
                    contains:
                        id:
                            description: The ID of the Port List
                            type: str
                            sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
                        name:
                            description: The name of the Port List
                            type: str
                            sample: "My Child Port List"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ntt_mcp.ntt_mcp_utils import get_credentials, get_ntt_mcp_regions, return_object
from ansible.module_utils.ntt_mcp.ntt_mcp_provider import NTTMCPClient, NTTMCPAPIException


def main():
    """
    Main function
    :returns: Port List Information
    """
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', type='str'),
            datacenter=dict(required=True, type='str'),
            name=dict(required=False, type='str'),
            network_domain=dict(required=True, type='str')
        ),
        supports_check_mode=True
    )
    try:
        credentials = get_credentials(module)
    except ImportError as e:
        module.fail_json(msg='{0}'.format(e))
    name = module.params.get('name')
    network_domain_name = module.params.get('network_domain')
    datacenter = module.params.get('datacenter')
    return_data = return_object('port_list')

    # Check the region supplied is valid
    ntt_mcp_regions = get_ntt_mcp_regions()
    if module.params.get('region') not in ntt_mcp_regions:
        module.fail_json(msg='Invalid region. Regions must be one of {0}'.format(ntt_mcp_regions))

    if credentials is False:
        module.fail_json(msg='Error: Could not load the user credentials')

    client = NTTMCPClient((credentials[0], credentials[1]), module.params['region'])

    # Get a list of existing CNDs and check if the name already exists
    try:
        network = client.get_network_domain_by_name(name=network_domain_name, datacenter=datacenter)
        network_domain_id = network.get('id')
    except NTTMCPAPIException as e:
        module.fail_json(msg='Failed to get a list of Cloud Network Domains - {0}'.format(e))

    try:
        if name:
            result = client.get_port_list_by_name(network_domain_id, name)
            if result:
                return_data['port_list'].append(result)
        else:
            return_data['port_list'] = client.list_port_list(network_domain_id)
    except (KeyError, IndexError, NTTMCPAPIException) as e:
        module.fail_json(msg='Could not retrieve a list of the Port Lists - {0}'.format(e))

    return_data['count'] = len(return_data.get('port_list'))
    module.exit_json(data=return_data)


if __name__ == '__main__':
    main()
