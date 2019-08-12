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
module: nttc_cis_network
short_description: Create, Update and Delete Cloud Network Domains (CND)
description:
    - Create, Update and Delete Cloud Network Domains (CND)
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
            - The name of the Cloud Network Domain
        required: true
    description:
        description:
            - The description of the Cloud Network Domain
        required: false
    network_type:
        description:
            - The type of Cloud Network Domain
        required: true
        default: ADVANCED
        choices:
          - [ADVANCED,ESSENTIALS,ENTERPRISE]
    new_name:
        description:
            - The new name of the Cloud Network Domain, used when updating
        required: true
    state:
        description:
            - The action to be performed
        required: true
        default: create
        choices: [create, delete, update, get]
    wait:
        description:
            - Should Ansible wait for the task to complete before continuing
        required: false
        default: false
        choices: [true, false]
    wait_time:
        description: The maximum time the Ansible should wait for the task
                     to complete in seconds
        required: false
        default: 600
    wait_poll_interval:
        description:
            - The time in between checking the status of the task in seconds
        required: false
        default: 10
notes:
    - N/A
'''

EXAMPLES = '''
# Create/Update a Cloud Network Domain
- nttc_cis_network:
      region: na
      location: NA9
      name: "xxxxx"
      network_type: "ESSENTIALS"
      description: "A test Network Domain"
      state: present
      wait: True
# Delete a Cloud Network Domain
- nttc_cis_network:
      region: na
      location: NA9
      name: "xxxxx"
      state: absent
      wait: True
'''

RETURN = '''
data:
    description: Dictionary of the network domain
    returned: success
    type: complex
    contains:
        id:
            description: Network Domain ID
            type: str
            returned: when state == present
            sample: "b2fbd7e6-ddbb-4eb6-a2dd-ad048bc5b9ae"
        name:
            description: Network Domain name
            type: str
            returned: when state == present and wait is True
            sample: "My network"
        description:
            description: Network Domain description
            type: str
            returned: when state == present and wait is True
            sample: "My network description"
        datacenterId:
            description: Datacenter id/location
            type: str
            returned: when state == present and wait is True
            sample: NA9
        state:
            description: Status of the Network Domain
            type: str
            returned: when state == present and wait is True
            sample: NORMAL
        createTime:
            description: The creation date of the image
            type: str
            returned: when state == present and wait is True
            sample: "2019-01-14T11:12:31.000Z"
        ipv4CpncGatewayAddress:
            description: The CPNC gateway address (mostly for internal use)
            type: str
            returned: when state == present and wait is True
            sample: "10.10.10.10"
        ipv4InternetGatewayAddress:
            description: The upstream gateway address
            type: str
            returned: when state == present and wait is True
            sample: "10.10.10.10"
        ipv6CpncGatewayAddress:
            description: The CPNC gateway address (mostly for internal use)
            type: str
            returned: when state == present and wait is True
            sample: "1111:1111:1111:1111:0:0:0:1"
        ipv6InternetGatewayAddress:
            description: The upstream gateway address
            type: str
            returned: when state == present and wait is True
            sample: "1111:1111:1111:1111:0:0:0:1"
        outsideTransitVlanIpv4Subnet:
            description:
            type: complex
            returned: when state == present and wait is True
            contains:
                address:
                    description: The upstream IPv4 transit network
                    type: str
                    sample: "10.10.10.0"
                prefixSize:
                    description: The upstream IPv4 transit network prefix
                    type: int
                    sample: 24
        outsideTransitVlanIpv6Subnet:
            description:
            type: complex
            returned: when state == present and wait is True
            contains:
                address:
                    description: The upstream IPv6 transit network
                    type: str
                    sample: "1111:1111:1111:1111:0:0:0:0"
                prefixSize:
                    description: The upstream IPv6 transit network prefix
                    type: int
                    sample: 64
        snatIpv4Address:
            description: The outgoing public IPv4 source address
            type: str
            returned: when state == present and wait is True
            sample: "1.1.1.1"
        type:
            description: The VLAN type
            type: str
            returned: when state == present and wait is True
            sample: "ADVANCED"
        baselineStaticRouteConfiguration:
            description: Internal use
            type: bool
            returned: when state == present and wait is True
'''

from time import sleep
from copy import deepcopy
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.nttc_cis.nttc_cis_utils import get_credentials, get_nttc_cis_regions, return_object, compare_json
from ansible.module_utils.nttc_cis.nttc_cis_provider import NTTCCISClient, NTTCCISAPIException


def create_network_domain(module, client):
    """
    Create a Cloud Network Domain

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :returns: The created Cloud Network Domain object
    """
    return_data = return_object('network')
    datacenter = module.params.get('datacenter')
    name = module.params.get('name')
    description = module.params.get('description')
    network_type = module.params.get('network_type')

    try:
        result = client.create_network_domain(datacenter, name, network_type, description)
        new_network_domain_id = result['info'][0].get('value')
    except (KeyError, IndexError, NTTCCISAPIException) as e:
        module.fail_json(msg='Could not create the Cloud Network Domain - {0}'.format(e))

    if module.params.get('wait'):
        wait_result = wait_for_network_domain(module, client, name, datacenter, 'NORMAL')
        if wait_result is None:
            module.fail_json(msg='Could not verify the Cloud Network Domain creation was successful. Check manually')
        return_data['network'].append(wait_result)
    else:
        return_data['network'].append({'id': new_network_domain_id})

    module.exit_json(changed=True, data=return_data.get('network'))


def update_network_domain(module, client, existing_network_domain):
    """
    Update a Cloud Network Domain

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg existing_network_domain: The existing Cloud Network Domain to be updated
    :returns: The updated Cloud Network Domain object
    """
    return_data = return_object('network')
    datacenter = module.params.get('datacenter')
    name = module.params.get('name')
    new_name = module.params.get('new_name')
    description = module.params.get('description')
    network_type = module.params.get('network_type')
    wait = module.params.get('wait')

    if new_name is not None:
        name = new_name

    try:
        client.update_network_domain(existing_network_domain.get('id'), name, network_type, description)
    except (KeyError, NTTCCISAPIException) as e:
        module.fail_json(msg='Could not update the Cloud Network Domain - {0}'.format(e))

    if wait:
        wait_result = wait_for_network_domain(module, client, name, datacenter, 'NORMAL')
        if wait_result is None:
            module.fail_json(msg='Could not verify the Cloud Network Domain update was successful. Check manually')
        return_data['network'] = wait_result
    else:
        return_data['network'] = {'id': existing_network_domain.get('id')}

    module.exit_json(changed=True, data=return_data.get('network'))

def compare_network_domain(module, network_domain):
    """
    Compare two Cloud Network Domains

    :arg module: The Ansible module instance
    :arg network_domain: The existingCloud Network Domain object
    :returns: Any differences between the two Cloud Network Domains
    """
    new_network_domain = deepcopy(network_domain)
    if module.params.get('name'):
        new_network_domain['name'] = module.params.get('name')
    if module.params.get('description'):
        new_network_domain['description'] = module.params.get('description')
    if module.params.get('network_type'):
        new_network_domain['type'] = module.params.get('network_type')

    return compare_json(new_network_domain, network_domain, None)


def delete_network_domain(module, client, network_domain):
    """
    Delete a Cloud Network Domain

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg network_domain: The Cloud Network Domain object
    :returns: A message
    """
    network_exists = True
    time = 0
    wait_time = module.params.get('wait_time')
    wait_poll_interval = module.params.get('wait_poll_interval')
    name = network_domain.get('name')
    datacenter = module.params.get('datacenter')

    try:
        client.delete_network_domain(network_domain.get('id'))
    except NTTCCISAPIException as e:
        module.fail_json(msg='Could not delete the Cloud Network Domain - {0}'.format(e))

    if module.params['wait']:
        while network_exists and time < wait_time:
            try:
                networks = client.list_network_domains(datacenter=datacenter)
                network_exists = [network for network in networks if network.get('id') == network_domain.get('id')]
            except (KeyError, NTTCCISAPIException) as e:
                pass
            sleep(wait_poll_interval)
            time = time + wait_poll_interval

        if network_exists and time >= wait_time:
            module.fail_json(msg='Timeout waiting for the Cloud Network Domain to be deleted')

    module.exit_json(changed=True, msg='Cloud Network Domain {0} has been successfully removed in {1}'.format(name, datacenter))


def wait_for_network_domain(module, client, name, datacenter, state):
    """
    Wait for an operation on a Cloud Network Domain. Polls based on wait_time and wait_poll_interval values.

    :arg module: The Ansible module instance
    :arg client: The CC API client instance
    :arg datacenter: The name of a MCP datacenter
    :arg state: The desired state to wait
    :returns: The Cloud Network Domain object
    """
    actual_state = ''
    wait_time = module.params.get('wait_time')
    time = 0

    while actual_state != state and time < wait_time:
        try:
            networks = client.list_network_domains(datacenter=datacenter)
            network_domain = [network for network in networks if network.get('name') == name]
        except NTTCCISAPIException as e:
            module.fail_json(msg='Failed to get a list of Cloud Network Domains - {0}'.format(e))
        try:
            actual_state = network_domain[0].get('state')
        except (KeyError, IndexError) as e:
            pass
        sleep(module.params.get('wait_poll_interval'))
        time = time + module.params.get('wait_poll_interval')

    if not network_domain and time >= wait_time:
        module.fail_json(msg='Timeout waiting for the Cloud Network Domain to be created')

    return network_domain[0]


def main():
    """
    Main function

    :returns: Cloud Network Domain Information
    """
    nttc_cis_regions = get_nttc_cis_regions()
    module = AnsibleModule(
        argument_spec=dict(
            region=dict(default='na', choices=nttc_cis_regions),
            datacenter=dict(required=True, type='str'),
            name=dict(required=True, type='str'),
            description=dict(required=False, type='str'),
            network_type=dict(default='ADVANCED', choices=['ADVANCED', 'ESSENTIALS', 'ENTERPRISE']),
            new_name=dict(required=False, default=None, type='str'),
            state=dict(default='present', choices=['present', 'absent']),
            wait=dict(required=False, default=True, type='bool'),
            wait_time=dict(required=False, default=600, type='int'),
            wait_poll_interval=dict(required=False, default=10, type='int')
        )
    )

    credentials = get_credentials()
    name = module.params['name']
    datacenter = module.params['datacenter']
    state = module.params['state']
    if credentials is False:
        module.fail_json(msg='Error: Could not load the user credentials')

    client = NTTCCISClient((credentials[0], credentials[1]), module.params['region'])

    # Get a list of existing CNDs and check if the name already exists
    try:
        network = client.get_network_domain_by_name(name=name, datacenter=datacenter)
    except NTTCCISAPIException as e:
        module.fail_json(msg='Failed to get a list of Cloud Network Domains - {0}'.format(e))

    # Create the Cloud Network Domain
    if state == 'present':
        # Handle case where CND name already exists
        if not network:
            create_network_domain(module, client)
        else:
            try:
                compare_result = compare_network_domain(module, network)
                if compare_result:
                    if compare_result.get('changes'):
                        update_network_domain(module, client, network)
                module.exit_json(changed=False, result=network)
            except (KeyError, NTTCCISAPIException) as e:
                module.fail_json(msg='Failed to update the Cloud Network Domain - {0}'.format(e))
    # Delete the Cloud Network Domain
    elif state == 'absent':
        if not network:
            module.exit_json(msg='Cloud Network Domain not found')
        delete_network_domain(module, client, network)


if __name__ == '__main__':
    main()
