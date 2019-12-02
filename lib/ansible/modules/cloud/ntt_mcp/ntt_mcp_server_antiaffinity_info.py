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
module: ntt_mcp_server_antiaffinity_info
short_description: Get and List Server Anti-Affinity Groups
description:
    - Get and List Server Anti-Affinity Groups
    - Currently servers can only belong to a single Anti-Affinity Group
    - https://docs.mcp-services.net/x/YgIu
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
    servers:
        description:
            - List of server names to search for
        required: false
        type: list
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

  - name: List all Anti-Affinity Groups in a Network Domain
    ntt_mcp_server_antiaffinity_info:
      region: na
      datacenter: NA9
      network_domain: my_cnd

  - name: List all Anti-Affinity Groups for a specific server
    ntt_mcp_server_antiaffinity_info:
      region: na
      datacenter: NA9
      network_domain: my_cnd
      servers:
        - my_server_01

  - name: List all Anti-Affinity Groups for a specific server pair
    ntt_mcp_server_antiaffinity_info:
      region: na
      datacenter: NA9
      network_domain: my_cnd
      servers:
        - my_server_01
        - my_server_02
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
        antiaffinity:
            description: List of the Anti-Affinity Groups
            returned: success
            type: list
            contains:
                id:
                    description: Anti-Affinity Group ID
                    type: str
                    sample: b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae
                datacenterId:
                    description: Datacenter ID/location
                    type: str
                    sample: NA9
                createTime:
                    description: The creation date of the Anti-Affinity Group
                    type: str
                    sample: 2019-01-14T11:12:31.000Z
                state:
                    description: Status of the Anti-Affinity Group
                    type: str
                    sample: NORMAL
                server:
                    description: List of server objects in the Anti-Affinity Group
                    type: list
                    contains:
                        id:
                            description: Server ID
                            type: str
                            sample: b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae
                        name:
                            description: Server name
                            type: str
                            sample: my_server_01
                        networkInfo:
                            description: Server network information
                            type: complex
                            contains:
                                networkDomainId:
                                    description: The UUID of the Cloud Network Domain for this server
                                    type: str
                                    sample: b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae
                                networkDomainName:
                                    description: The name of the Cloud Network Domain for this server
                                    type: str:
                                    sample: my_cnd
                                primary_nic:
                                    description: Information in the primary NIC for this server
                                    type: complex
                                    contains:
                                        ipv6:
                                            description: The IPv6 address of the NIC
                                            type: str
                                            sample: fc00::100
                                        macAddress:
                                            description: The MAC address of the NIC
                                            type: str
                                            sample: aa:aa:aa:aa:aa:aa
                                        privateIpv4:
                                            description: The IPv4 address of the NIC
                                            type: str
                                            sample: 10.0.0.100
                                        vlanId:
                                            description: The UUID of the VLAN for the NIC
                                            type: str
                                            sample: b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae
                                        vlanName:
                                            description: The name of the VLAN for the NIC
                                            type: str
                                            sample: my_vlan
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
            network_domain=dict(default=None, type='str'),
            servers=dict(default=list(), type='list'),
        ),
        supports_check_mode=True
    )
    network_domain_name = module.params.get('network_domain')
    network_domain_id = None
    server_ids = list()
    datacenter = module.params.get('datacenter')
    return_data = return_object('antiaffinity_group')
    try:
        credentials = get_credentials(module)
    except ImportError as e:
        module.fail_json(msg='{0}'.format(e))

    # Check the region supplied is valid
    ntt_mcp_regions = get_ntt_mcp_regions()
    if module.params.get('region') not in ntt_mcp_regions:
        module.fail_json(msg='Invalid region. Regions must be one of {0}'.format(ntt_mcp_regions))

    if credentials is False:
        module.fail_json(msg='Could not load the user credentials')

    try:
        client = NTTMCPClient(credentials, module.params.get('region'))
    except NTTMCPAPIException as e:
        module.fail_json(msg=e.msg)

    # Get the CND
    if network_domain_name:
        try:
            network = client.get_network_domain_by_name(network_domain_name, datacenter)
            network_domain_id = network.get('id')
        except (KeyError, IndexError, AttributeError, NTTMCPAPIException):
            module.fail_json(msg='Could not find the Cloud Network Domain: {0}'.format(network_domain_name))

    # Get the servers
    for server in module.params.get('servers'):
        try:
            server = client.get_server_by_name(datacenter=datacenter,
                                               network_domain_id=network_domain_id,
                                               name=server)
            if server:
                server_ids.append(server.get('id'))
            else:
                module.warn(warning='Could not find the server - {0} in {1}'.format(server, datacenter))
        except (KeyError, IndexError, AttributeError):
            module.warn(warning='Could not find the server - {0} in {1}'.format(server, datacenter))

    try:
        if len(server_ids) == 0:
            return_data['antiaffinity_group'] = client.list_server_anti_affinity_groups(network_domain_id=network_domain_id)
        elif len(server_ids) == 1:
            return_data['antiaffinity_group'] = client.list_server_anti_affinity_groups(network_domain_id, server_ids[0])
        # Currently a server can belong to only a single antiaffinity group, while it doesn't do much more then the
        # case above today, this next section will handle any future situations were a server can belong to multiple
        # antiaffinity groups
        elif len(server_ids) == 2:
            return_data['antiaffinity_group'] = [client.get_anti_affinity_group_by_servers(server_ids[0], server_ids[1])]
        return_data['count'] = len(return_data['antiaffinity_group'])
        module.exit_json(data=return_data)
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException) as e:
        module.fail_json(msg='Could not retrieve any Server Anti Affinity Groups - {0}'.format(e))


if __name__ == '__main__':
    main()
