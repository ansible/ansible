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
module: ntt_mcp_nat_info
short_description: List NAT entries
description:
    - List NAT entries
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
          - Valid values can be found in nttmcp.common.config.py under APIENDPOINTS
    datacenter:
        description:
            - The datacenter name
        required: true
        choices:
          - See NTT LTD Cloud Web UI
    network_domain:
        description:
            - The name of a Cloud Network Domain
        required: true
        default: None
    internal_ip:
        description:
            - The internal IP address of the NAT
        required: false
    external_ip:
        description:
            - The external IP address of the NAT
        required: false
    id:
        description:
            - The UUID of the NAT rule
        required: false
notes:
    - N/A
'''

EXAMPLES = '''
# List NAT rules
- ntt_mcp_nat_facts:
      region: na
      datacenter: NA9
      network_domain: "xxxx"
# Get a specific NAT rule
- ntt_mcp_nat_facts:
      region: na
      datacenter: NA9
      network_domain: "xxxx"
      id: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
# Get a specific NAT rule by IP address
- ntt_mcp_nat_facts:
      region: na
      datacenter: NA9
      internal_ip: "x.x.x.x"
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
        nat:
            description: a single or list of IP address objects or strings
            returned: success
            type: complex
            contains:
                id:
                    description: Network Domain ID
                    type: str
                    sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
                datacenterId:
                    description: Datacenter id/location
                    type: str
                    sample: NA3
                createTime:
                    description: The creation date of the image
                    type: str
                    sample: "2019-01-14T11:12:31.000Z"
                externalIp:
                    description: The public IPv4 address of the NAT
                    type: str
                    sample: x.x.x.x
                externalIpAddressability:
                    description: Internal Use
                    type: str
                    sample: PUBLIC_IP_BLOCK
                internalIp:
                    description: The internal IPv4 address of a host
                    type: str
                    sample: 10.0.0.10
                networkDomainId:
                    description: Network Domain ID
                    type: str
                    sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
                state:
                    state:
                    description: Status of the VLAN
                    type: str
                    sample: NORMAL
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ntt_mcp.ntt_mcp_utils import get_credentials, get_ntt_mcp_regions, return_object
from ansible.module_utils.ntt_mcp.ntt_mcp_provider import NTTMCPClient, NTTMCPAPIException


def list_nat_rule(module, client, network_domain_id):
    """
    Get a NAT rule by UUID

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg network_domain_id: The UUID of a network domain

    :returns: NAT object
    """
    return_data = return_object('nat')
    try:
        return_data['nat'] = client.list_nat_rule(network_domain_id)
    except NTTMCPAPIException as e:
        module.fail_json(msg='Could not retrieve a list of NAT(s) - {0}'.format(e.message))
    except KeyError:
        module.fail_json(msg='Network Domain is invalid')

    return_data['count'] = len(return_data.get('nat'))
    module.exit_json(changed=False, data=return_data)


def get_nat_rule(module, client, network_domain_id, nat_rule_id, internal_ip, external_ip):
    """
    Get a NAT rule by UUID

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg network_domain_id: The UUID of the CND
    :arg nat_rule_id: The UUID of the NAT rule to get
    :arg internal_ip: The internal IPv4 address of the NAT rule
    :arg external_ip: The external public IPv4 address of the NAT rule

    :returns: NAT object
    """
    return_data = return_object('nat')
    if nat_rule_id is None and internal_ip is None and external_ip is None:
        module.fail_json(msg='A value for is required for one of id, internal_ip or external_ip')
    try:
        if nat_rule_id:
            result = client.get_nat_rule(nat_rule_id)
        elif internal_ip:
            result = client.get_nat_by_private_ip(network_domain_id, internal_ip)
        elif external_ip:
            result = client.get_nat_by_public_ip(network_domain_id, external_ip)
        if result is None:
            module.exit_json(msg='Could not find a matching NAT rule', data=None)
        return_data['nat'].append(result)
    except NTTMCPAPIException as e:
        module.fail_json(msg='Could not get the NAT rule - {0}'.format(e.message))

    return_data['count'] = len(return_data.get('nat'))
    module.exit_json(changed=False, data=return_data)


def main():
    """
    Main function

    :returns: NAT Information
    """
    ntt_mcp_regions = get_ntt_mcp_regions()
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', choices=ntt_mcp_regions),
            datacenter=dict(required=True, type='str'),
            network_domain=dict(required=True, type='str'),
            internal_ip=dict(required=False, default=None, type='str'),
            external_ip=dict(required=False, default=None, type='str'),
            id=dict(default=None, type='str')
        ),
        supports_check_mode=True
    )
    credentials = get_credentials()
    network_domain_name = module.params.get('network_domain')
    datacenter = module.params.get('datacenter')
    object_id = module.params.get('id')
    internal_ip = module.params.get('internal_ip')
    external_ip = module.params.get('external_ip')

    if credentials is False:
        module.fail_json(msg='Could not load the user credentials')

    client = NTTMCPClient((credentials[0], credentials[1]), module.params.get('region'))

    # Get the CND
    try:
        network = client.get_network_domain_by_name(name=network_domain_name, datacenter=datacenter)
        network_domain_id = network.get('id')
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException):
        module.fail_json(msg='Could not find the Cloud Network Domain: {0}'.format(network_domain_name))

    if object_id or internal_ip or external_ip:
        get_nat_rule(module, client, network_domain_id, object_id, internal_ip, external_ip)
    else:
        list_nat_rule(module, client, network_domain_id)


if __name__ == '__main__':
    main()
