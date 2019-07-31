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
module: nttc_cis_nat
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
    description:
        description:
            - The description of the Cloud Network Domain
        required: false
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
    state:
        description:
            - The action to be performed
        required: true
        default: create
        choices: [get_public_ipv4,add_public_ipv4,delete_public_ipv4,
                  list_reserved_ip,unreserve_ip,reserve_ip]
notes:
    - N/A
'''

EXAMPLES = '''
# Create a NAT rule
- nttc_cis_nat:
      region: na
      datacenter: NA9
      network_domain: "xxxx"
      internal_ip: "x.x.x.x"
      external_ip: "y.y.y.y"
      state: present
# Delete a NAT rule
- nttc_cis_nat:
      region: na
      datacenter: NA9
      network_domain: "xxxx"
      id: "ffffffff-fff-ffff-ffff-ffffffffffff"
      state: absent
'''

RETURN = '''
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

import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.nttc_cis.nttc_cis_utils import get_credentials, get_nttc_cis_regions, return_object
from ansible.module_utils.nttc_cis.nttc_cis_provider import NTTCCISClient, NTTCCISAPIException


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

    # Check if a NAT rule already exists for this private IP and delete it if it exists
    # Only a single NAT rule can exist for any given private IP address
    try:
        nat_rule = client.get_nat_by_private_ip(network_domain_id, internal_ip)
        if nat_rule is not None:
            client.remove_nat_rule(nat_rule.get('id'))
    except (KeyError, NTTCCISAPIException) as e:
        module.fail_json(msg='Could not create the NAT rule - {0}'.format(e.message), exception=traceback.format_exc())

    try:
        client.create_nat_rule(network_domain_id, internal_ip, external_ip)
        return_data['nat'] = client.get_nat_by_private_ip(network_domain_id, internal_ip)
    except (KeyError, NTTCCISAPIException) as e:
        module.fail_json(msg='Could not create the NAT rule - {0}'.format(e.message), exception=traceback.format_exc())

    module.exit_json(changed=True, results=return_data['nat'])


def delete_nat_rule(module, client, nat_rule_id):
    """
    Delete a NAT rule

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg nat_rule_id: The UUID of the existing NAT rule to delete
    :returns: A message
    """
    if nat_rule_id is None:
        module.fail_json(msg='A value for id is required')
    try:
        client.remove_nat_rule(nat_rule_id)
    except NTTCCISAPIException as e:
        module.fail_json(msg='Could not delete the NAT rule - {0}'.format(e.message), exception=traceback.format_exc())

    module.exit_json(changed=True, msg='Successfully deleted the NAT rule')


def main():
    """
    Main function

    :returns: NAT rule Information
    """
    nttc_cis_regions = get_nttc_cis_regions()
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', choices=nttc_cis_regions),
            datacenter=dict(required=True, type='str'),
            network_domain=dict(required=True, type='str'),
            internal_ip=dict(required=False, default=None, type='str'),
            external_ip=dict(required=False, default=None, type='str'),
            id=dict(default=None, type='str'),
            state=dict(default='present', choices=['present', 'absent'])
        )
    )
    credentials = get_credentials()
    object_id = module.params['id']
    network_domain_name = module.params['network_domain']
    datacenter = module.params['datacenter']
    state = module.params['state']
    internal_ip = module.params['internal_ip']
    external_ip = module.params['external_ip']

    if credentials is False:
        module.fail_json(msg='Error: Could not load the user credentials')

    client = NTTCCISClient((credentials[0], credentials[1]), module.params['region'])

    # Get a list of existing CNDs and check if the name already exists
    try:
        network = client.get_network_domain_by_name(name=network_domain_name, datacenter=datacenter)
        network_domain_id = network.get('id')
    except (KeyError, NTTCCISAPIException) as e:
        module.fail_json(msg='Failed to get a list of Cloud Network Domains - {0}'.format(e.message), exception=traceback.format_exc())
    if not network:
        module.fail_json(msg='Failed to find the Cloud Network Domain Check the network_domain value')

    if state == 'present':
        create_nat_rule(module, client, network_domain_id, internal_ip, external_ip)
    elif state == 'absent':
        delete_nat_rule(module, client, object_id)


if __name__ == '__main__':
    main()
