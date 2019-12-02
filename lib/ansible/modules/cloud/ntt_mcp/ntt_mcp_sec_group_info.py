#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019, Ken Sinfield <ken.sinfield@cis.ntt.com>
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
module: ntt_mcp_sec_group_info
short_description: Get and List Security Groups
description:
    - Get and List Security Groups
    - https://docs.mcp-services.net/x/NgMu
version_added: 2.10
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
            - The datacenter name e.g NA9
        required: true
        type: str
    network_domain:
        description:
            - The name of the Cloud Network Domain
        required: true
        type: str
    type:
        description:
            - The type of security group
        default: vlan
        choices:
            - vlan
            - server
        type: str
    name:
        description:
            - The name of the Security Group
            - A specific value for type should be used when searching by name
        required: false
        type: str
    id:
        description:
            - The UUID of the Security Group
        required: false
        type: str
    server:
        description:
            - The name of a server to search on
            - A specific value for type should be used when searching by server
        required: false
        type: str
    vlan:
        description:
            - The name of the vlan to search on
        required: false
        type: str
notes:
    - Requires NTT Ltd. MCP account/credentials
requirements:
    - requests>=2.21.0
    - configparser>=3.7.4
'''

EXAMPLES = '''
- hosts: 127.0.0.1
  connection: local
  tasks:

  - name: List all Server Security Groups in a Network Domain
    ntt_mcp_sec_group_info:
      region: na
      datacenter: NA9
      network_domain: my_cnd
      type: server

  - name: List all VLAN Security Groups in a Network Domain
    ntt_mcp_sec_group_info:
      region: na
      datacenter: NA9
      network_domain: my_cnd
      type: vlan

  - name: Get a specific VLAN Security Group by Security Group name
    ntt_mcp_sec_group_info:
      region: na
      datacenter: NA9
      network_domain: my_cnd
      type: vlan
      name: my_vlan_security_group

  - name: Get a specific Server Security Group by Security Group UUID
    ntt_mcp_sec_group_info:
      region: na
      datacenter: NA9
      network_domain: my_cnd
      type: server
      id: b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae

  - name: Get all Server Security Groups for a specific server
    ntt_mcp_sec_group_info:
      region: na
      datacenter: NA9
      network_domain: my_cnd
      type: server
      server: my_server
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
        security_group:
            description: List of Security Group objects
            contains:
                name:
                    description:
                    type: string
                    sample: my_vlan_security_group
                nics:
                    description:
                    returned: type == vlan and at least 1 NIC is configured in this group
                    type: complex
                    contains:
                        nic:
                            description: List of NICs in this Security Group
                            type: list
                            contains:
                                ipv4Address:
                                    description: The IPv4 address of the NIC
                                    type: string
                                    sample: 10.0.0.7
                                server:
                                    description: dict containing server information for this NIC
                                    type: complex
                                    contains:
                                        id:
                                            description: The UUID of the server
                                            type: string
                                            sample: b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae
                                        name:
                                            description: The name of the server
                                            type: string
                                            sample: myServer03
                                id:
                                    description: The UUID of the NIC
                                    type: string
                                    sample: 7b664273-05fa-467f-82c2-6dea32cdf233
                                ipv6Address:
                                    description: The IPv6 address of the NIC
                                    type: string
                                    sample: 1111:1111:1111:1111:0:0:0:1
                                primary:
                                    description: Is the NIC the primary NIC on the server
                                    type: bool
                        vlanId:
                            description: The UUID of the VLAN for the NICs
                            type: string
                            sample: b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae
                servers:
                    description: List of servers associated with the Security Group
                    returned: type == server and at least 1 server is configured in this group
                    type: complex
                    contains:
                        networkDomainId: The UUID of the Cloud Network Domain
                            description:
                            type: string
                            sample: b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae
                        server:
                            description: List of server objects
                            type: list
                            contains:
                                id:
                                    description: The UUID of the server
                                    type: string
                                    sample: b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae
                                name:
                                    description: The name of the server
                                    type: string
                                    sample: myServer01
                createTime:
                    description: The time (in zulu) that the Security Group was created
                    type: string
                    sample: 2019-11-26T19:29:52.000Z
                datacenterId:
                    description: The MCP/datacenter ID
                    type: string
                    sample: NA12
                state:
                    description: The operational state
                    type: string
                    sample: NORMAL
                type:
                    description: The Security Group type
                    type: string
                    sample: VLAN
                id:
                    description: The UUID of the Security Group
                    type: string
                    sample: b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae
                description:
                    description: Text description
                    type: string
                    sample: My VLAN security group
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ntt_mcp.ntt_mcp_utils import get_credentials, get_ntt_mcp_regions, return_object
from ansible.module_utils.ntt_mcp.ntt_mcp_provider import NTTMCPClient, NTTMCPAPIException


def main():
    """
    Main function
    :returns: Server Anti-Affinity Group information
    """
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', type='str'),
            datacenter=dict(required=True, type='str'),
            network_domain=dict(required=True, type='str'),
            type=dict(default='vlan', required=False, choices=['vlan', 'server']),
            name=dict(default=None, required=False, type='str'),
            id=dict(default=None, required=False, type='str'),
            server=dict(default=None, required=False, type='str'),
            vlan=dict(default=None, required=False, type='str')
        ),
        supports_check_mode=True
    )
    network_domain_name = module.params.get('network_domain')
    network_domain_id = None
    server = vlan = dict()
    datacenter = module.params.get('datacenter')
    return_data = return_object('security_group')
    try:
        credentials = get_credentials(module)
        if credentials is False:
            module.fail_json(msg='Could not load the user credentials')
    except ImportError as e:
        module.fail_json(msg='{0}'.format(e))

    # Check the region supplied is valid
    ntt_mcp_regions = get_ntt_mcp_regions()
    if module.params.get('region') not in ntt_mcp_regions:
        module.fail_json(msg='Invalid region. Regions must be one of {0}'.format(ntt_mcp_regions))

    try:
        client = NTTMCPClient(credentials, module.params.get('region'))
    except NTTMCPAPIException as e:
        module.fail_json(msg=e.msg)

    # Get the CND
    try:
        network = client.get_network_domain_by_name(network_domain_name, datacenter)
        network_domain_id = network.get('id')
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException):
        module.fail_json(msg='Could not find the Cloud Network Domain: {0}'.format(network_domain_name))

    # If a server name was provided get the server object
    if module.params.get('server'):
        try:
            server = client.get_server_by_name(datacenter=datacenter,
                                               network_domain_id=network_domain_id,
                                               name=module.params.get('server'))
            if not server:
                module.fail_json(msg='Could not find the server - {0} in {1}'.format(module.params.get('server'),
                                                                                     datacenter))
        except (KeyError, IndexError, AttributeError):
            module.fail_json(msg='Could not find the server - {0} in {1}'.format(module.params.get('server'),
                                                                                 datacenter))

    # If a vlan name was provided get the vlan object
    if module.params.get('vlan'):
        try:
            vlan = client.get_vlan_by_name(datacenter=datacenter,
                                           network_domain_id=network_domain_id,
                                           name=module.params.get('vlan'))
            if not vlan:
                module.fail_json(msg='Could not find the VLAN - {0} in {1}'.format(module.params.get('vlan'),
                                                                                   datacenter))
        except (KeyError, IndexError, AttributeError):
            module.fail_json(msg='Could not find the VLAN - {0} in {1}'.format(module.params.get('vlan'),
                                                                               datacenter))

    try:
        if module.params.get('id'):
            return_data['security_group'] = client.get_security_group_by_id(group_id=module.params.get('id'))
        else:
            return_data['security_group'] = client.list_security_groups(network_domain_id=network_domain_id,
                                                                        name=module.params.get('name'),
                                                                        group_type=module.params.get('type'),
                                                                        server_id=server.get('id', None),
                                                                        vlan_id=vlan.get('id', None))
        return_data['count'] = len(return_data['security_group'])
        module.exit_json(data=return_data)
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException) as e:
        module.fail_json(msg='Could not retrieve any Security Groups - {0}'.format(e))


if __name__ == '__main__':
    main()
