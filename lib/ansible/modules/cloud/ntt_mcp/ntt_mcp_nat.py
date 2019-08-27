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
module: ntt_mcp_nat
short_description: Add and Remove NAT entries
description:
    - Add and Remove NAT entries
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
    network_domain:
        description:
            - The name of a Cloud Network Domain
        required: true
        type: str
    internal_ip:
        description:
            - The internal IP address of the NAT
        required: false
        type: str
    external_ip:
        description:
            - The external IP address of the NAT
        required: false
        type: str
    id:
        description:
            - The UUID of the NAT rule
        required: false
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

  - name: Create a NAT rule
    ntt_mcp_nat:
      region: na
      datacenter: NA12
      network_domain: myCND
      internal_ip: 10.1.77.6
      external_ip: x.x.x.x
      state: present

  - name: Update a NAT rule
    ntt_mcp_nat:
      region: na
      datacenter: NA12
      network_domain: myCND
      internal_ip: 10.1.77.6
      external_ip: x.x.x.x
      state: present

  - name: Delete a NAT rule by internal_ip (can also use external_ip or id)
    ntt_mcp_nat:
      region: na
      datacenter: NA12
      network_domain: myCND
      internal_ip: 10.1.77.6
      state: absent
'''

RETURN = '''
data:
    description: Server objects
    returned: success
    type: complex
    contains:
        count:
            description: The number of objects returned
            returned: success
            type: int
            sample: 1
        nat:
            description: a single or list of IP address objects or strs
            returned: success
            type: complex
            contains:
                id:
                    description: The UUID of the NAT entry
                    type: str
                    returned: when state == present
                    sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
                datacenterId:
                    description: Datacenter id/location
                    type: str
                    returned: when state == present
                    sample: NA3
                createTime:
                    description: The creation date of the image
                    type: str
                    returned: when state == present
                    sample: "2019-01-14T11:12:31.000Z"
                externalIp:
                    description: The public IPv4 address of the NAT
                    type: str
                    returned: when state == present
                    sample: x.x.x.x
                externalIpAddressability:
                    description: Internal Use
                    type: str
                    returned: when state == present
                    sample: PUBLIC_IP_BLOCK
                internalIp:
                    description: The internal IPv4 address of a host
                    type: str
                    returned: when state == present
                    sample: 10.0.0.10
                networkDomainId:
                    description: Network Domain ID
                    type: str
                    returned: when state == present
                    sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
                state:
                    state:
                    description: Status of the VLAN
                    type: str
                    returned: when state == present
                    sample: NORMAL
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ntt_mcp.ntt_mcp_utils import get_credentials, get_ntt_mcp_regions, return_object
from ansible.module_utils.ntt_mcp.ntt_mcp_provider import NTTMCPClient, NTTMCPAPIException


def create_nat_rule(module, client, network_domain_id, internal_ip, external_ip):
    """
    Create a NAT rule

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg network_domain_id: The UUID of the network domain
    :arg internal_ip: The internal IPv4 address of the NAT rule
    :arg external_ip: The external public IPv4 address of the NAT rule
    :returns: The created NAT rule object
    """
    return_data = return_object('nat')
    if internal_ip is None or external_ip is None:
        module.fail_json(msg='Valid internal_ip and external_ip values are required')

    # Check if a NAT rule already exists for this private & public IP and delete it if it exists
    # Only a single NAT rule can exist for any given private IP address
    try:
        nat_rule = client.get_nat_by_private_ip(network_domain_id, internal_ip)
        nat_rule_public = client.get_nat_by_public_ip(network_domain_id, external_ip)
        if nat_rule:
            if nat_rule.get('internalIp') == internal_ip and nat_rule.get('externalIp') == external_ip:
                module.exit_json(data=nat_rule)
            # Check conflicts on the public IP
            return_data['nat'].append(nat_rule)
            if nat_rule_public:
                return_data['nat'].append(nat_rule_public)
            # Implement Check Mode
            if module.check_mode:
                module.exit_json(msg='The following NAT rule(s) will be affected', data=return_data.get('nat'))
            client.remove_nat_rule(nat_rule.get('id'))
        if nat_rule_public:
            return_data['nat'].append(nat_rule_public)
            # Implement Check Mode
            if module.check_mode:
                module.exit_json(msg='The following NAT rule(s) will be affected', data=return_data.get('nat'))
            client.remove_nat_rule(nat_rule_public.get('id'))
    except (KeyError, NTTMCPAPIException) as e:
        module.fail_json(msg='Could not create the NAT rule - {0}'.format(e))

    try:
        # Implement Check Mode
        if module.check_mode:
            module.exit_json(msg='The NAT rule with external IP {0} and internal IP {1}'
                             ' will be created'.format(external_ip, internal_ip))
        client.create_nat_rule(network_domain_id, internal_ip, external_ip)
        return_data['nat'] = client.get_nat_by_private_ip(network_domain_id, internal_ip)
    except (KeyError, NTTMCPAPIException) as e:
        module.fail_json(msg='Could not create the NAT rule - {0}'.format(e))

    module.exit_json(changed=True, data=return_data.get('nat'))


def delete_nat_rule(module, client, network_domain_id, internal_ip, external_ip):
    """
    Delete a NAT rule

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg nat_rule_id: The UUID of the existing NAT rule to delete
    :returns: A message
    """
    nat_rule_id = None
    try:
        nat_rule = client.get_nat_by_private_ip(network_domain_id, internal_ip)
        nat_rule_public = client.get_nat_by_public_ip(network_domain_id, external_ip)
        if nat_rule:
            nat_rule_id = nat_rule.get('id')
        elif nat_rule_public:
            nat_rule_id = nat_rule_public.get('id')
        else:
            module.exit_json(msg='Could not find a valid NAT rule')
        # Implement Check Mode
        if module.check_mode:
            module.exit_json(msg='NAT with ID {0} will be removed'.format(nat_rule_id))
        client.remove_nat_rule(nat_rule_id)
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException) as e:
        module.fail_json(msg='Could not delete the NAT rule - {0}'.format(e))

    module.exit_json(changed=True, msg='Successfully deleted the NAT rule')


def main():
    """
    Main function

    :returns: NAT rule Information
    """
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', type='str'),
            datacenter=dict(required=True, type='str'),
            network_domain=dict(required=True, type='str'),
            internal_ip=dict(required=False, default=None, type='str'),
            external_ip=dict(required=False, default=None, type='str'),
            id=dict(default=None, type='str'),
            state=dict(default='present', choices=['present', 'absent'])
        ),
        supports_check_mode=True
    )
    try:
        credentials = get_credentials(module)
    except ImportError as e:
        module.fail_json(msg='{0}'.format(e))
    network_domain_name = module.params.get('network_domain')
    datacenter = module.params.get('datacenter')
    state = module.params.get('state')
    internal_ip = module.params.get('internal_ip')
    external_ip = module.params.get('external_ip')

    # Check the region supplied is valid
    ntt_mcp_regions = get_ntt_mcp_regions()
    if module.params.get('region') not in ntt_mcp_regions:
        module.fail_json(msg='Invalid region. Regions must be one of {0}'.format(ntt_mcp_regions))

    if credentials is False:
        module.fail_json(msg='Error: Could not load the user credentials')

    client = NTTMCPClient((credentials[0], credentials[1]), module.params.get('region'))

    # Get a list of existing CNDs and check if the name already exists
    try:
        network = client.get_network_domain_by_name(name=network_domain_name, datacenter=datacenter)
        network_domain_id = network.get('id')
    except (KeyError, IndexError, AttributeError, NTTMCPAPIException) as e:
        module.fail_json(msg='Failed to get a list of Cloud Network Domains - {0}'.format(e))
    if not network:
        module.fail_json(msg='Failed to find the Cloud Network Domain Check the network_domain value')

    if state == 'present':
        create_nat_rule(module, client, network_domain_id, internal_ip, external_ip)
    elif state == 'absent':
        delete_nat_rule(module, client, network_domain_id, internal_ip, external_ip)


if __name__ == '__main__':
    main()
