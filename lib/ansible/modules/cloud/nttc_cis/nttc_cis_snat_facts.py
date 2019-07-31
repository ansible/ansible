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
module: nttc_cis_snat_facts
short_description: List SNAT Exclusions
description:
    - List SNAT Exclusions
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
            - The UUID of the SNAT exclusion
            - If a id and a network is provided but there is a conflict, id takes precendence
        required: false
    network:
        description:
            - The destination network address to search for e.g. 192.168.0.0
        required: false
    prefix:
        description:
            - The destination network prefix associated with the SNAT exclusion as an integer e.g. 24
        required: false
notes:
    - N/A
requirements:
    - NTTC CIS Provider (nttc_cis_provider)
    - NTTC CIS Utils (nttc_cis_utils)
'''

EXAMPLES = '''
# List NAT rules
- nttc_cis_static_route_facts:
      region: na
      datacenter: NA9
      network_domain: "my_network_domain"
      next_hop: "172.16.0.77"
'''

RETURN = '''
count:
    description: The number of objects returned
    returned: success
    type: int
    sample: 1
snat:
    description: List of SNAT exclusion objects
    returned: success
    type: complex
    contains:
        id:
            description: The UUID of the SNAT exclusion
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
        description:
            description: Optional description for the SNAT exclusion
            type: str
            sample: "something"
        networkDomainId:
            description: Network Domain ID
            type: str
            sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
        state:
            state:
            description: Status of the static route
            type: str
            sample: NORMAL
        destinationPrefixSize:
            description: The destination prefix for the static route
            type: int
            sample: 24
        destinationIpv4NetworkAddress:
            description: The destination network address for the static route
            type: str
            sample: "192.168.0.0"
        type:
            description: The type of static route e.g. SYSTEM or CLIENT
            type: str
            sample: "CLIENT"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.nttc_cis.nttc_cis_utils import get_credentials, get_nttc_cis_regions, return_object
from ansible.module_utils.nttc_cis.nttc_cis_provider import NTTCCISClient, NTTCCISAPIException


def list_snat_exclusion(module, client, network_domain_id):
    """
    List the SNAT for a network domain, filter by name if provided
    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg network_domain_id: The UUID of the network domain
    :returns: List of SNAT objects
    """
    return_data = return_object('snat')
    snat_id = module.params.get('id')
    network = module.params.get('network')
    prefix = module.params.get('prefix')
    try:
        return_data['snat'] = client.list_snat_exclusion(network_domain_id, snat_id, network, prefix)
    except NTTCCISAPIException as exc:
        module.fail_json(msg='Could not retrieve a list of SNAT Exclusions - {0}'.format(exc))

    return_data['count'] = len(return_data['snat'])
    module.exit_json(changed=False, results=return_data)


def get_snat_exclusion(module, client, snat_id):
    """
    Get a SNAT by UUID
    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg pool_id: The UUID of the SNAT
    :returns: SNAT object
    """
    return_data = return_object('snat')
    if snat_id is None:
        module.fail_json(msg='A value for id is required')
    try:
        result = client.get_snat_exclusion(snat_id)
        if result is None:
            module.fail_json(msg='Could not find the SNAT Exclusion for {0}'.format(snat_id))
        return_data['snat'].append(result)
    except NTTCCISAPIException as exc:
        module.fail_json(msg='Could not get the SNAT Exclusion - {0}'.format(exc))

    return_data['count'] = len(return_data['snat'])
    module.exit_json(results=return_data)


def main():
    """
    Main function
    :returns: SNAT Information
    """
    nttc_cis_regions = get_nttc_cis_regions()
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', choices=nttc_cis_regions),
            datacenter=dict(required=True, type='str'),
            network_domain=dict(required=True, type='str'),
            id=dict(default=None, required=False, type='str'),
            network=dict(default=None, required=False, type='str'),
            prefix=dict(default=None, required=False, type='int'),
        ),
        supports_check_mode=True
    )
    credentials = get_credentials()
    network_domain_name = module.params.get('network_domain')
    datacenter = module.params.get('datacenter')
    object_id = module.params.get('id')

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
        get_snat_exclusion(module, client, object_id)
    else:
        list_snat_exclusion(module, client, network_domain_id)


if __name__ == '__main__':
    main()
