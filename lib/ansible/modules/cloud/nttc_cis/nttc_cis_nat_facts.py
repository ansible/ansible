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
module: nttc_cis_nat_facts
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
          - Valid values can be found in nttcis.common.config.py under APIENDPOINTS
    datacenter:
        description:
            - The datacenter name
        required: true
        choices:
          - See NTTC CIS Cloud Web UI
    network_domain:
        description:
            - The name of a Cloud Network Domain
        required: true
        default: None
    id:
        description:
            - The UUID of the NAT rule
        required: false
notes:
    - N/A
'''

EXAMPLES = '''
# List NAT rules
- nttc_cis_nat_facts:
      region: na
      datacenter: NA9
      network_domain: "xxxx"
# Get a specific NAT rule
- nttc_cis_nat_facts:
      region: na
      datacenter: NA9
      network_domain: "xxxx"
      id: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
'''

RETURN = '''
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

import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.nttc_cis.nttc_cis_utils import get_credentials, get_nttc_cis_regions, return_object
from ansible.module_utils.nttc_cis.nttc_cis_provider import NTTCCISClient, NTTCCISAPIException


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
    except NTTCCISAPIException as e:
        module.fail_json(msg='Could not retrieve a list of NAT(s) - {0}'.format(e.message), exception=traceback.format_exc())
    except KeyError:
        module.fail_json(msg='Network Domain is invalid')

    return_data['count'] = len(return_data['nat'])
    module.exit_json(changed=False, results=return_data)


def get_nat_rule(module, client, nat_rule_id):
    """
    Get a NAT rule by UUID

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg nat_rule_id: The UUID of the NAT rule to get

    :returns: NAT object
    """
    return_data = return_object('nat')
    if nat_rule_id is None:
        module.fail_json(msg='A value for id is required')
    try:
        result = client.get_nat_rule(nat_rule_id)
        if result is None:
            module.fail_json(msg='Could not find the NAT rule for {0}'.format(nat_rule_id))
        return_data['nat'].append(result)
    except NTTCCISAPIException as e:
        module.fail_json(msg='Could not get the NAT rule - {0}'.format(e.message), exception=traceback.format_exc())

    return_data['count'] = len(return_data['nat'])
    module.exit_json(changed=False, results=return_data)


def main():
    """
    Main function

    :returns: NAT Information
    """
    nttc_cis_regions = get_nttc_cis_regions()
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', choices=nttc_cis_regions),
            datacenter=dict(required=True, type='str'),
            network_domain=dict(required=True, type='str'),
            id=dict(default=None, type='str')
        ),
        supports_check_mode=True
    )
    credentials = get_credentials()
    network_domain_name = module.params['network_domain']
    datacenter = module.params['datacenter']
    object_id = module.params['id']

    if credentials is False:
        module.fail_json(msg='Could not load the user credentials')

    client = NTTCCISClient((credentials[0], credentials[1]), module.params['region'])

    # Get the CND
    try:
        network = client.get_network_domain_by_name(name=network_domain_name, datacenter=datacenter)
        network_domain_id = network.get('id')
    except (KeyError, IndexError, NTTCCISAPIException):
        module.fail_json(msg='Could not find the Cloud Network Domain: {0}'.format(network_domain_name))

    if object_id:
        get_nat_rule(module, client, object_id)
    else:
        list_nat_rule(module, client, network_domain_id)


if __name__ == '__main__':
    main()
