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
module: ntt_mcp_firewall_info
short_description: List/Get Firewall rules
description:
    - List/Get Firewall rules
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
        required: False
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

  - name: List all firewall rules within a Cloud Network Domain
    ntt_mcp_firewall_info:
      region: na
      datacenter: NA12
      network_domain: myCND

  - name: Get a specific firewall rule
    ntt_mcp_firewall_info:
      region: na
      datacenter: NA12
      network_domain: myCND
      name: CCDEFAULT.BlockOutboundMailIPv6
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
        acl:
            description: Dictonary of the firewall rule(s)
            returned: success
            type: complex
            contains:
                ipVersion:
                    description: IP Version
                    type: str
                    sample: IPV6
                networkDomainId:
                    description: The UUID of the Cloud Network Domain
                    type: str
                    sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
                protocol:
                    description: The protocol for the firewall rule
                    type: str
                    sample: TCP
                name:
                    description: The name of the firewall rule
                    type: str
                    sample: my_firewall_rule
                destination:
                    description: The destination object for the rule, can be a single IP address or IP address list
                    type: complex
                    contains:
                        ip:
                            description: The destination IP address object
                            type: complex
                            contains:
                                address:
                                    description: The destination IP address
                                    type: str
                                    sample: "10.0.0.1"
                        port:
                            description: The destination port object
                            type: complex
                            contains:
                                begin:
                                    description: The starting port number
                                    type: int
                                    sample: 443
                                end:
                                    description: The ending port number
                                    type: int
                                    sample: 444
                        ipAddressList:
                            description: The IP address list object
                            type: complex
                            contains:
                                id:
                                    description: the UUID of the IP address list
                                    type: str
                                    sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
                                name:
                                    description: The name of the IP address list
                                    type: str
                                    sample: my_ip_list
                        portList:
                            description: The destination port list
                            type: complex
                            contains:
                                id:
                                    description: The UUID of the port list
                                    type: str
                                    sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
                                name:
                                    description: The name of the port list
                                    type: str
                                    sample: my port list
                enabled:
                    description: The status of the firewall rule
                    type: bool
                ruleType:
                    description: Internal Use - is the rule internally or client created
                    type: str
                    sample: CLIENT_RULE
                datacenterId:
                    description: Datacenter id/location
                    type: str
                    sample: NA9
                source:
                    description: The source object for the rule, can be a single IP address or IP address list
                    type: complex
                    contains:
                        ip:
                            description: The source IP address object
                            type: complex
                            contains:
                                address:
                                    description: The source IP address
                                    type: str
                                    sample: "10.0.0.1"
                        port:
                            description: The source port object
                            type: complex
                            contains:
                                begin:
                                    description: The starting port number
                                    type: int
                                    sample: 443
                                end:
                                    description: The ending port number
                                    type: int
                                    sample: 444
                        ipAddressList:
                            description: The IP address list object
                            type: complex
                            contains:
                                id:
                                    description: the UUID of the IP address list
                                    type: str
                                    sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
                                name:
                                    description: The name of the IP address list
                                    type: str
                                    sample: my_ip_list
                state:
                    description: Status of the VLAN
                    type: str
                    sample: NORMAL
                action:
                    description: The rule action
                    type: str
                    sample: ACCEPT_DECISIVELY
                id:
                    description: The UUID of the firewall rule
                    type: str
                    sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
'''

import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ntt_mcp.ntt_mcp_utils import get_credentials, get_ntt_mcp_regions, return_object
from ansible.module_utils.ntt_mcp.ntt_mcp_provider import NTTMCPClient, NTTMCPAPIException


def list_fw_rule(module, client, network_domain_id):
    """
    List all firewall rules for a given network domain

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg network_domain_id: The UUID of the network domain

    :returns: List of firewall rules
    """
    return_data = return_object('acl')
    try:
        return_data['acl'] = client.list_fw_rules(network_domain_id)
    except NTTMCPAPIException as e:
        module.fail_json(msg='Could not retrieve a list of firewall rules - {0}'.format(e), exception=traceback.format_exc())
    except KeyError:
        module.fail_json(msg='Network Domain is invalid')

    return_data['count'] = len(return_data.get('acl'))

    module.exit_json(changed=False, data=return_data)


def get_fw_rule(module, client, network_domain_id, name):
    """
    Gets a specific firewall rule by name

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg network_domain_id: The UUID of the network domain
    :arg name: The name of the firewall rule to search for

    :returns: a firewall rule
    """
    return_data = return_object('acl')
    try:
        result = client.get_fw_rule_by_name(network_domain_id, name)
        if result is None:
            module.exit_json(changed=False, msg='Could not find the ACL {0}'.format(name))
        return_data['acl'].append(result)
    except NTTMCPAPIException as e:
        module.exit_json(msg='Could not get the firewall rule - {0}'.format(e), exception=traceback.format_exc())
    except KeyError:
        module.fail_json(msg='Network Domain is invalid')

    return_data['count'] = len(return_data.get('acl'))

    module.exit_json(changed=False, data=return_data)


def main():
    """
    Main function

    :returns: Firewall Information
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

    # Check the region supplied is valid
    ntt_mcp_regions = get_ntt_mcp_regions()
    if module.params.get('region') not in ntt_mcp_regions:
        module.fail_json(msg='Invalid region. Regions must be one of {0}'.format(ntt_mcp_regions))

    if credentials is False:
        module.fail_json(msg='Error: Could not load the user credentials')

    client = NTTMCPClient((credentials[0], credentials[1]), module.params.get('region'))

    # Get the CND
    try:
        network = client.get_network_domain_by_name(name=network_domain_name, datacenter=datacenter)
        network_domain_id = network.get('id')
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException):
        module.fail_json(msg='Could not find the Cloud Network Domain: {0}'.format(network_domain_name))

    if name is not None:
        get_fw_rule(module, client, network_domain_id, name)
    else:
        list_fw_rule(module, client, network_domain_id)


if __name__ == '__main__':
    main()
